import os
import requests
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from app.config import settings
from app.services.google_trends_service import GoogleTrendsService
from pydantic import BaseModel, Field
from app.services.salesforce_service import SalesforceService
from langchain_community.chat_models.writer import ChatWriter
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from writerai import Writer
import logging
import json
import asyncio
import time
from typing import Literal

# Initialize logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.info("Logger initialized!")

# Initialize the Slack Bolt app
slack_app = App(
    token=settings.SLACK_BOT_TOKEN,
    signing_secret=settings.SLACK_SIGNING_SECRET,
    logger=logger
)

slack_handler = SlackRequestHandler(slack_app)
sf_service = SalesforceService()


# Initialize Writer Client
writer_client = Writer(api_key=settings.WRITER_API_KEY)



# Tool to search accounts
@tool
def search_and_get_account_data(query: str) -> str:
    """
    Search for Salesforce accounts by name or partial name and retrieve data for the first result.
    """
    accounts = sf_service.search_accounts(query)
    if not accounts:
        return "No matching accounts found."
    
    # Get the first account's ID
    first_account = accounts[0]
    account_id = first_account["Id"]
    account_name = first_account["Name"]

    # Retrieve account data
    account_data = sf_service.get_account_data(account_id)
    return f"Account: {account_name}\n\n{account_data}"


@tool
def create_salesforce_task(account_id: str, subject: str) -> str:
    """Create a task for a specific Salesforce account."""
    result = sf_service.create_task_for_account(account_id, subject)
    if not result:
        return "Failed to create the task."
    return f"Task created successfully: {result}"
# Tool to get total pipeline value
@tool
def get_total_pipeline_value() -> str:
    """
    Get the total pipeline value (sum of Amount for open opportunities).
    """
    total_value = sf_service.total_pipeline_value()
    return f"Total Pipeline Value: ${total_value:,.2f}"

# Tool to get weighted pipeline value
@tool
def get_weighted_pipeline_value() -> str:
    """
    Get the weighted pipeline value (Amount * Probability for open opportunities).
    """
    weighted_value = sf_service.weighted_pipeline_value()
    return f"Weighted Pipeline Value: ${weighted_value:,.2f}"

# Tool to get stage-wise pipeline breakdown
@tool
def get_stage_wise_pipeline_breakdown() -> str:
    """
    Get the pipeline value grouped by stage.
    """
    breakdown = sf_service.stage_wise_pipeline_breakdown()
    breakdown_str = "\n".join([f"{stage}: ${value:,.2f}" for stage, value in breakdown.items()])
    return f"Stage-Wise Pipeline Breakdown:\n{breakdown_str}"

# Tool to calculate pipeline velocity
@tool
def calculate_pipeline_velocity(average_deal_size: float, win_rate: float, sales_cycle_length: int) -> str:
    """
    Calculate the pipeline velocity.
    """
    velocity = sf_service.pipeline_velocity(average_deal_size, win_rate, sales_cycle_length)
    return f"Pipeline Velocity: ${velocity:,.2f} per day"

# Tool to get sales cycle length
@tool
def get_sales_cycle_length() -> str:
    """
    Get the average sales cycle length (in days).
    """
    cycle_length = sf_service.sales_cycle_length()
    return f"Average Sales Cycle Length: {cycle_length:.2f} days"

# Tool to get win rate
@tool
def get_win_rate() -> str:
    """
    Get the win rate (percentage of closed-won opportunities).
    """
    win_rate = sf_service.win_rate()
    return f"Win Rate: {win_rate:.2f}%"

# Tool to get forecasted revenue by close date
@tool
def get_forecast_by_close_date() -> str:
    """
    Get the forecasted revenue grouped by CloseDate for open opportunities.
    """
    forecast = sf_service.forecast_by_close_date()
    forecast_str = "\n".join([f"{date}: ${value:,.2f}" for date, value in forecast.items()])
    return f"Forecasted Revenue by Close Date:\n{forecast_str}"

# Tool for pipeline gap analysis
@tool
def perform_pipeline_gap_analysis(target_revenue: float) -> str:
    """
    Perform a pipeline gap analysis based on target revenue.
    """
    gap = sf_service.pipeline_gap_analysis(target_revenue)
    status = "surplus" if gap < 0 else "deficit"
    return f"Pipeline Gap: ${abs(gap):,.2f} ({status})"

# Tool to get conversion rates by stage
@tool
def get_conversion_rates_by_stage() -> str:
    """
    Get the conversion rates by stage.
    """
    conversion_rates = sf_service.conversion_rates_by_stage()
    rates_str = "\n".join([f"{stage}: {rate:.2f}%" for stage, rate in conversion_rates.items()])
    return f"Conversion Rates by Stage:\n{rates_str}"

# Add all tools to the tools list
tools = [
    search_and_get_account_data,
    create_salesforce_task,
    get_total_pipeline_value,
    get_weighted_pipeline_value,
    get_stage_wise_pipeline_breakdown,
    calculate_pipeline_velocity,
    get_sales_cycle_length,
    get_win_rate,
    get_forecast_by_close_date,
    perform_pipeline_gap_analysis,
    get_conversion_rates_by_stage,
]



tool_node = ToolNode(tools)

llm = ChatWriter(
    model="palmyra-x-004",
    temperature=0.7,
).bind_tools(tools)

def should_continue(state: MessagesState) -> Literal["tools", END]:
    messages = state["messages"]
    last_message = messages[-1]
    # If the LLM makes a tool call, route to the tools node
    if last_message.tool_calls:
        return "tools"
    # Otherwise, end the workflow
    return END

def call_model(state: MessagesState):
    messages = state["messages"]
    response = llm.invoke(messages)
    # Return the response as part of the message state
    return {"messages": [response]}

# Initialize the StateGraph
workflow = StateGraph(MessagesState)

# Add agent and tools nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

# Set the entry point and transitions
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

# Add memory for persistent state
checkpointer = MemorySaver()

# Compile the graph into a runnable
app = workflow.compile(checkpointer=checkpointer)



@slack_app.message("")
def handle_message_events(message, say, client):
    """
    Handles incoming Slack messages and processes them using the Salesforce tool chain.
    """
    channel_id = message["channel"]
    thread_ts = message["ts"]  # Use this as the thread_id
    user_query = message.get("text", "").strip()

    if not user_query:
        client.chat_postMessage(
            channel=channel_id,
            text=":warning: I couldn't understand your message. Please try again.",
            thread_ts=thread_ts,
        )
        return

    # Add reminder and examples to the query for LLM
    query = (
        f"{user_query}\n\n"
        "Please return the response formatted in clean Slack markdown (`mrkdwn`) with clear headers, bullet points, and proper indentation. "
        "Use the following format as a guide:\n\n"
        "* Example Output Format:\n"
        "- *Key*: Value\n"
        "- *Link*: <https://example.com|example>\n"
        "  - Nested Item 1\n"
        "  - Nested Item 2\n"
        "- *Key with List*:\n"
        "  - Item 1\n"
        "  - Item 2\n"
        "- *Contacts*:\n"
        "  - *Name*: John Doe, *Email*: john.doe@example.com\n"
        "- *Activities*:\n"
        "  - *Subject*: Task 1, *Status*: Completed, *Date*: 2024-12-01\n\n"
        "Ensure consistent indentation and bullet point alignment for readability."
    )

    # Post an initial processing message
    result = client.chat_postMessage(channel=channel_id, text=":mag: Processing...", thread_ts=thread_ts)
    thread_ts = result["ts"]

    try:
        # Invoke the workflow with the query and config
        state = app.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config={"configurable": {"thread_id": thread_ts}}
        )

        # Safely extract the last message content
        response_messages = state["messages"]
        if response_messages:
            response_text = response_messages[-1].content.strip()
        else:
            response_text = "Sorry, I couldn't process your request."

        # Post-process response to ensure proper Slack markdown formatting
        response_text = format_to_slack_mrkdwn(response_text)

    except Exception as e:
        response_text = f":warning: An error occurred while processing your request: {e}"
        logger.error(f"Error processing query: {query}. Exception: {e}")

    # Update the Slack thread with the response
    client.chat_update(
        channel=channel_id,
        ts=thread_ts,
        text=response_text,
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": response_text,
                },
            }
        ],
    )

def format_to_slack_mrkdwn(text: str) -> str:
    """
    Ensures the text is formatted properly for Slack's mrkdwn syntax.
    - Converts inconsistent bullet points to `-`.
    - Adds indentation for nested items.
    """
    lines = text.split("\n")
    formatted_lines = []
    for line in lines:
        # Adjust bullet points and indentation
        if line.startswith("- "):
            formatted_lines.append(line)
        elif line.startswith("  - "):  # Nested item
            formatted_lines.append(f"    {line.strip()}")
        elif line.strip():  # Regular content
            formatted_lines.append(line)
    return "\n".join(formatted_lines)




# Functionality to send a message to Slack
def post_slack_message(channel_id: str, text: str):
    """
    Posts a message to a Slack channel.
    """
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"channel": channel_id, "text": text}
    response = requests.post(url, headers=headers, json=payload)
    if not response.ok:
        logger.error(f"Error sending message to Slack: {response.text}")
    return response.json()

# Functionality to create a new Canvas document
def create_canvas(title: str, content: str):
    """
    Creates a new Slack Canvas document.
    """
    url = "https://slack.com/api/canvas.create"
    headers = {
        "Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"title": title, "content": content}
    response = requests.post(url, headers=headers, json=payload)
    if not response.ok:
        logger.error(f"Error creating canvas: {response.text}")
    return response.json()

# Functionality to share a Canvas document
def post_canvas_message(canvas_url: str, channel_id: str, message_text: str = "Here is the canvas you requested!"):
    """
    Posts a message with the given canvas URL to a Slack channel.

    :param canvas_url: The URL of the Canvas to share.
    :param channel_id: The ID of the Slack channel to post the message in.
    :param message_text: The message text to include with the Canvas URL.
    :return: API response from Slack.
    """
    bot_token = settings.SLACK_BOT_TOKEN

    bot_headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json"
    }

    post_message_payload = {
        "channel": channel_id,
        "text": f"{message_text}\n{canvas_url}"
    }

    # Make the API call to Slack
    response = requests.post(
        url="https://slack.com/api/chat.postMessage",
        headers=bot_headers,
        json=post_message_payload
    )

    logger.info(f"Post Message Response (Raw): {response.text}")
    post_message_data = response.json()

    # Check for errors
    if not post_message_data.get("ok"):
        error_message = post_message_data.get("error", "Unknown error during message posting.")
        logger.error(f"Error posting message: {error_message}")
        return {"error": error_message}

    return {"status": "Message sent successfully"}

def send_account_followup_message(channel_id: str, message: str):
    """
    Sends a Block Kit message with follow-up options to a Slack channel.

    :param channel_id: Slack channel ID where the message will be posted.
    :param message: Markdown-supported text for the initial section message.
    :return: API response from Slack.
    """
    bot_token = settings.SLACK_BOT_TOKEN
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json",
    }

    # Block Kit message payload
    payload = {
        "channel": channel_id,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message,
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": ":writer: Create Follow-Up Email"},
                        "action_id": "create_followup_email",
                        "value": "followup_email",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": ":writer: Generate Account Summary"},
                        "action_id": "executive_summary",
                        "value": "executive_summary",
                    },
                ],
            },
        ],
    }

    # Send the message via Slack API
    response = requests.post(
        url="https://slack.com/api/chat.postMessage",
        headers=headers,
        json=payload,
    )

    logger.info(f"Send Account Follow-Up Response (Raw): {response.text}")
    response_data = response.json()

    # Check for errors
    if not response_data.get("ok"):
        error_message = response_data.get("error", "Unknown error during message posting.")
        logger.error(f"Error sending follow-up message: {error_message}")
        return {"error": error_message}

    return {"status": "Message sent successfully"}


@slack_app.action("create_followup_email")
def handle_create_followup_email(ack, body, client):
    """
    Handles the 'Create Follow-Up Email' button click and opens a modal.
    """
    ack()  # Acknowledge the action

    # Get the thread timestamp of the original message
    thread_ts = body["message"]["ts"]

    # Open a modal with a dropdown for tone of voice selection
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "followup_email_modal",
            "private_metadata": json.dumps({"thread_ts": thread_ts}),
            "title": {"type": "plain_text", "text": "Create Follow-Up Email"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "tone_of_voice",
                    "label": {"type": "plain_text", "text": "Select Tone of Voice"},
                    "element": {
                        "type": "static_select",
                        "action_id": "tone_select",
                        "placeholder": {"type": "plain_text", "text": "Choose a tone"},
                        "options": [
                            {
                                "text": {"type": "plain_text", "text": "Writer Default Voice"},
                                "value": "formal",
                            },
                            {
                                "text": {"type": "plain_text", "text": "May's Vouice"},
                                "value": "casual",
                            },
                            {
                                "text": {"type": "plain_text", "text": "Company Default Voice"},
                                "value": "professional",
                            },
                        ],
                    },
                }
            ],
            "submit": {"type": "plain_text", "text": "Submit"},
        },
    )



@slack_app.view("followup_email_modal")
def handle_followup_email_submission(ack, body, client):
    """
    Handles the submission of the follow-up email modal.
    Sends a threaded message with the Canvas link and action buttons.
    """
    ack()  # Acknowledge the submission

    # Extract the selected tone of voice
    state_values = body["view"]["state"]["values"]
    tone_of_voice = state_values["tone_of_voice"]["tone_select"]["selected_option"]["value"]

    # Retrieve the thread_ts from private_metadata
    private_metadata = json.loads(body["view"]["private_metadata"])
    thread_ts = private_metadata.get("thread_ts")

    # Define the Canvas link and the message
    canvas_url = "https://writerai.slack.com/docs/T02AJRK99/F084DF8CPN2"
    channel_id = "C08476AM146"
    message_text = f"Here is the draft generated by the :writer: sales follow-up text generation app: <{canvas_url}|draft>."

    # Block Kit message payload with buttons
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message_text,
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": ":white_check_mark: Approve"},
                    "action_id": "approve_followup",
                    "value": "approve",
                    "style": "primary",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": ":writer: Regenerate"},
                    "action_id": "regenerate_followup",
                    "value": "regenerate",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": ":writer: Check for Compliance"},
                    "action_id": "check_compliance",
                    "value": "check_compliance",
                },
            ],
        },
    ]

    # Send the threaded message
    payload = {
        "channel": channel_id,
        "blocks": blocks,
        "thread_ts": thread_ts,  # Ensure the message is threaded
    }

    bot_token = settings.SLACK_BOT_TOKEN
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        url="https://slack.com/api/chat.postMessage",
        headers=headers,
        json=payload,
    )

    if response.status_code != 200 or not response.json().get("ok"):
        logger.error(f"Error sending threaded message: {response.text}")



@slack_app.action("executive_summary")
def handle_executive_summary_action(ack, body, client):
    """
    Handles the "Executive Summary" action.
    Updates a Slack message sequentially with progress updates.
    """
    ack()  # Acknowledge the button press

    # Extract channel ID and thread_ts from the message
    channel_id = body["channel"]["id"]
    thread_ts = body.get("message", {}).get("ts")

    # Define sequential messages
    messages = [
        ":hourglass_flowing_sand: Gathering Account Data from :salesforce-logo:",
        (
            ":white_check_mark: Gathering Account Data from :salesforce-logo:\n"
            ":hourglass_flowing_sand: Gathering Gong Call Transcript from :gong-emoji:"
        ),
        (
            ":white_check_mark: Gathering Account Data from :salesforce-logo:\n"
            ":white_check_mark: Gathering Gong Call Transcript from :gong-emoji:\n"
            ":hourglass_flowing_sand: Gathering Web research about account using :writer: Research Assistant"
        ),
        (
            ":white_check_mark: Gathering Account Data from :salesforce-logo:\n"
            ":white_check_mark: Gathering Gong Call Transcript from :gong-emoji:\n"
            ":white_check_mark: Gathering Web research about account using :writer: Research Assistant\n"
            ":hourglass_flowing_sand: Generating summary using :writer: Account Executive Summary Text Generation App"
        ),
        (
            ":white_check_mark: Gathering Account Data from :salesforce-logo:\n"
            ":white_check_mark: Gathering Gong Call Transcript from :gong-emoji:\n"
            ":white_check_mark: Gathering Web research about account using :writer: Research Assistant\n"
            ":white_check_mark: Generating summary using :writer: Account Executive Summary Text Generation App\n\n"
            "Final Summary can be found here: <https://writerai.slack.com/docs/T02AJRK99/F084P646L6M|Executive Summary>"
        ),
    ]

    bot_token = settings.SLACK_BOT_TOKEN
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json",
    }

    try:
        # Send the initial message
        initial_payload = {
            "channel": channel_id,
            "text": messages[0],
            "thread_ts": thread_ts,  # Ensure it is a threaded reply
        }
        response = requests.post(
            url="https://slack.com/api/chat.postMessage",
            headers=headers,
            json=initial_payload,
        )

        if not response.ok or not response.json().get("ok"):
            logger.error(f"Error sending initial message: {response.text}")
            return

        message_ts = response.json().get("ts")  # Timestamp of the sent message

        # Sequentially update the message with progress
        for i in range(1, len(messages)):
            time.sleep(5)  # Delay between updates
            update_payload = {
                "channel": channel_id,
                "ts": message_ts,  # Reference the original message's timestamp
                "text": messages[i],
            }
            update_response = requests.post(
                url="https://slack.com/api/chat.update",
                headers=headers,
                json=update_payload,
            )

            if not update_response.ok or not update_response.json().get("ok"):
                logger.error(f"Error updating message at step {i}: {update_response.text}")
                break

    except Exception as e:
        logger.error(f"Error during message update sequence: {e}")





# Endpoint handler for Slack events
def get_slack_handler():
    return slack_handler
