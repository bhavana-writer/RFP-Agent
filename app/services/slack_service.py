import os
import requests
import asyncio
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
from app.services.wordpress_service import WordPressService
from threading import Thread
import markdown
import textwrap
from simple_salesforce import Salesforce
from datetime import datetime
from slack_sdk.errors import SlackApiError




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

wordpress_service = WordPressService()

# Initialize Salesforce connection
sf = Salesforce(
    username=os.environ.get("SALESFORCE_USERNAME"),
    password=os.environ.get("SALESFORCE_PASSWORD"),
    security_token=os.environ.get("SALESFORCE_SECURITY_TOKEN")
)

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

#handle message that iincldes a file share - Primt the output of the file
@slack_app.event("message")
def handle_file_share_event(body, logger):
    """
    Handles the 'file_share' subtype of the 'message' event from Slack.
    """
    event = body.get("event", {})
    subtype = event.get("subtype")

    # Check if the message subtype is 'file_share'
    if subtype == "file_share":
        logger.info("Handling file_share event")
        
        # Extract file information
        files = event.get("files", [])
        user_id = event.get("user")
        channel_id = event.get("channel")

        # Print out the extracted data
        for file in files:
            file_id = file.get("id")
            file_name = file.get("name")
            file_url = file.get("url_private_download")
            
            print(f"File ID: {file_id}")
            print(f"File Name: {file_name}")
            print(f"File URL: {file_url}")

        print(f"User ID: {user_id}")
        print(f"Channel ID: {channel_id}")

    else:
        logger.info("Received a non-file_share message event")


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

@slack_app.shortcut("generate_blog_article")
def handle_generate_blog_article_shortcut(ack, body, client):
    """
    Handles the 'generate_blog_article' shortcut and opens a modal.
    """
    ack()  # Acknowledge the shortcut invocation

    # Define the modal view payload
    modal_view = {
    "type": "modal",
    "callback_id": "generate_blog_article",
    "title": {
        "type": "plain_text",
        "text": "SEO Blog Article",
        "emoji": True
    },
    "submit": {
        "type": "plain_text",
        "text": ":writer: Generate",
        "emoji": True
    },
    "close": {
        "type": "plain_text",
        "text": "Cancel",
        "emoji": True
    },
    "blocks": [
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Provide details of the Blog you want to write below"
            }
        },
        {
            "type": "input",
            "block_id": "blog_title_block",
            "element": {
                "type": "plain_text_input",
                "action_id": "blog_title_input"
            },
            "label": {
                "type": "plain_text",
                "text": "Blog Title",
                "emoji": True
            }
        },
        {
            "type": "input",
            "block_id": "objectives_block",
            "element": {
                "type": "plain_text_input",
                "multiline": True,
                "action_id": "objectives_input"
            },
            "label": {
                "type": "plain_text",
                "text": "Objectives",
                "emoji": True
            }
        },
        {
            "type": "input",
            "block_id": "sources_block",
            "element": {
                "type": "plain_text_input",
                "multiline": True,
                "action_id": "sources_input"
            },
            "label": {
                "type": "plain_text",
                "text": "Sources",
                "emoji": True
            }
        },
        {
            "type": "input",
            "block_id": "keywords_block",
            "element": {
                "type": "plain_text_input",
                "action_id": "keywords_input"
            },
            "label": {
                "type": "plain_text",
                "text": "Primary Keywords",
                "emoji": True
            }
        }
    ]
}


    # Open the modal
    client.views_open(
        trigger_id=body["trigger_id"],
        view=modal_view
    )
@slack_app.view("generate_blog_article")
def handle_generate_blog_article_submission(ack, body, client, logger):
    """
    Handles the submission of the 'generate_blog_article' modal.
    """
    ack()  # Acknowledge the submission immediately

    try:
        # Extract state values using explicit block_ids
        state_values = body["view"]["state"]["values"]
        
        blog_title = state_values["blog_title_block"]["blog_title_input"]["value"]
        objectives = state_values["objectives_block"]["objectives_input"]["value"]
        sources = state_values["sources_block"]["sources_input"]["value"]
        keywords = state_values["keywords_block"]["keywords_input"]["value"]

        # Prepare inputs for text generation
        text_gen_inputs = [
            {
                "id": "Blog Title",
                "value": [blog_title]
            },
            {
                "id": "Objective",
                "value": [objectives]
            },
            {
                "id": "Sources",
                "value": [source.strip() for source in sources.split('\n') if source.strip()]
            },
            {
                "id": "Primary Keyword",
                "value": [keywords]
            }
        ]

        # Simulate loading process with sequential messages
        channel_id = "C08476AM146"
        initial_message = client.chat_postMessage(
            channel=channel_id,
            text=":hourglass_flowing_sand: Generating Blog Article...",
        )
        message_ts = initial_message["ts"]

        # Update message to show progress
        time.sleep(2)
        client.chat_update(
            channel=channel_id,
            ts=message_ts,
            text=(
                ":hourglass_flowing_sand: Generating Blog Article...\n"
                ":hourglass_flowing_sand: Gathering inputs and preparing content..."
            ),
        )

        time.sleep(2)
        client.chat_update(
            channel=channel_id,
            ts=message_ts,
            text=(
                ":hourglass_flowing_sand: Generating Blog Article...\n"
                ":white_check_mark: Gathering inputs and preparing content...\n"
                ":hourglass_flowing_sand: Finalizing the article..."
            ),
        )

        time.sleep(2)
        client.chat_update(
            channel=channel_id,
            ts=message_ts,
            text=(
                ":white_check_mark: Generating Blog Article...\n"
                ":white_check_mark: Gathering inputs and preparing content...\n"
                ":white_check_mark: Finalizing the article...\n"
                ":hourglass_flowing_sand: Almost done..."
            ),
        )

        time.sleep(2)
        client.chat_update(
            channel=channel_id,
            ts=message_ts,
            text=(
                ":white_check_mark: Generating Blog Article...\n"
                ":white_check_mark: Gathering inputs and preparing content...\n"
                ":white_check_mark: Finalizing the article...\n"
                ":white_check_mark: Almost done...\n"
                "Blog article is ready for review!"
            ),
        )

        # Use the existing Canvas link
        canvas_url = "https://writerai.slack.com/docs/T02AJRK99/F0882E6N0P5"

        # Send the existing Canvas URL to the specified channel with approval buttons
        client.chat_postMessage(
            channel=channel_id,
            text=":white_check_mark: Blog article is ready for review!",
            blocks=[
                {
                    "type": "section",
                    "block_id": "review_section",
                    "text": {"type": "mrkdwn", "text": f"*Your Blog Article is Ready for Review* ✨\nClick here to review the blog article: <{canvas_url}|View Blog Article Canvas>"}
                },
                {
                    "type": "section",
                    "block_id": "instruction_section",
                    "text": {"type": "mrkdwn", "text": "Please review the document and approve or request changes."}
                },
                {
                    "type": "actions",
                    "block_id": "action_buttons",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": ":white_check_mark: Approve"},
                            "action_id": "approve_blog_article",
                            "value": "approve",
                            "style": "primary"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": ":x: Request Changes"},
                            "action_id": "request_changes_blog_article",
                            "value": "request_changes"
                        }
                    ]
                }
            ]
        )

    except Exception as e:
        logger.error(f"Error handling blog article submission: {e}")
        client.chat_postMessage(
            channel=body["user"]["id"],
            text=f":warning: There was an error processing your request: {str(e)}"
        )


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
    ack()
    thread_ts = body["message"]["ts"]

    # Update the modal view to include a callback_id
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
                                "text": {"type": "plain_text", "text": "May's Voice"},
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
    ack()
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

# Add a catch-all view submission handler
@slack_app.view("")
def handle_view_submission_events(ack, body, logger):
    """
    Generic handler for any unhandled view submissions
    """
    ack()
    logger.info(f"Caught unhandled view submission: {body}")
article_content = textwrap.dedent("""

## Introduction

Imagine this: 95% of SMBs are effectively using generative AI, according to Salesforce's SMB research. This statistic is a powerful testament to the potential of AI in small businesses. Small businesses can successfully adopt AI to unlock growth, productivity, and innovation. In this blog, we'll explore why AI is a game-changer for small businesses, showcase real-world examples of AI success, address common challenges, and highlight Salesforce's AI tools that can help you get started.

## Why AI is a Game-Changer for Small Businesses

AI offers a multitude of benefits for small businesses, making it a valuable investment. From increasing efficiency to improving customer service and enhancing decision-making, the advantages are manifold.

### Increased Efficiency

AI can automate routine tasks, such as data entry, customer inquiries, and even content creation. This not only saves time but also reduces the risk of errors, allowing your team to focus on more strategic and creative work. According to Gartner, AI can help SMBs increase revenue by 10% and reduce costs by 15%.

### Improved Customer Service

Customer satisfaction is crucial for small businesses. AI-powered chatbots and virtual assistants can provide 24/7 support, answering common questions and handling basic tasks. This ensures that your customers receive prompt and accurate assistance, enhancing their overall experience.

### Enhanced Decision-Making

AI can analyze vast amounts of data to provide actionable insights. For instance, predictive analytics can help you anticipate market trends, customer behavior, and potential issues. This allows you to make informed decisions that can drive your business forward.

### Assessing Readiness with the AI Maturity Assessment Tool

Salesforce's AI Maturity Assessment Tool is a valuable resource for SMBs. It helps you evaluate your current AI capabilities and identify areas for improvement. By using this tool, you can gain a clear understanding of where you stand and what steps you need to take to fully leverage AI.

## Real-World Examples of AI Success

Let's dive into some case studies of small businesses that have successfully adopted AI using Salesforce tools.

### Case Study 1: BACA Systems

BACA Systems, a leading provider of IT solutions, used Einstein Activity Capture to streamline their sales processes. They noticed a significant improvement in customer lifetime value. As one of their executives put it, "We use Einstein Activity Capture to streamline our sales processes and boost customer lifetime value."

### Case Study 2: Crexi

Crexi, a commercial real estate platform, leveraged Agentic AI to optimize their sales priorities. The results were impressive. "Agentic AI has helped us to optimize our sales priorities and improve our bottom line," said their CEO.

### Case Study 3: Bombardier

Bombardier, a global leader in transportation, used AI to break down data silos and integrate predictive analytics into their sales process. "AI has helped us to break down data silos and integrate predictive analytics into our sales process," noted one of their technologists.

## Overcoming Common AI Challenges

While the benefits of AI are clear, small businesses often face challenges such as limited resources and technical expertise. However, these challenges can be overcome with the right approach.

### Limited Resources

One of the primary concerns for SMBs is the cost and resources required to implement AI. However, third-party research shows that the return on investment (ROI) is substantial. For instance, SMBs that adopt AI are twice as likely to be profitable as those that don't, according to Forrester. This makes AI a cost-effective solution in the long run.

### Technical Expertise

Many small businesses may feel they lack the technical expertise to implement AI. However, Salesforce's pre-built AI solutions are designed to be user-friendly and require minimal technical knowledge. Additionally, there are numerous resources and training programs available to help you get started.

### Data Silos

Data silos can hinder the effectiveness of AI. To address this, ensure that all your data is harmonized and integrated. This means having a single, consistent format for all your data, which can be used to fine-tune AI models. Salesforce's Data Cloud can help you achieve this by providing a unified view of your customer data.

## Salesforce's AI Tools for Small Businesses

Salesforce offers a range of AI tools specifically designed for small businesses. These tools are user-friendly and can help you adopt AI with ease.

### Einstein AI Tools

Einstein AI is a suite of AI tools that can help you with various aspects of your business. Here are some of the key capabilities:

- **Predictive Analytics**: Use AI to forecast sales, customer behavior, and market trends. This can help you make data-driven decisions and stay ahead of the competition.
- **Generative AI for Content**: Create personalized marketing materials, product descriptions, and customer communications with AI. This can save you time and ensure that your content is relevant and engaging.
- **Workflow Automation**: Automate repetitive tasks to improve productivity and reduce errors. This can help you streamline your operations and focus on more strategic initiatives.

### AI Use Case Library

Salesforce's AI Use Case Library is a valuable resource for small businesses. It provides a wide range of practical applications of AI, from sales and marketing to customer service and operations. By exploring these use cases, you can gain inspiration and insights on how to apply AI in your business.

## Competitive Benchmarking

When it comes to AI adoption, small businesses often face challenges that differ from those of large enterprises. However, SMBs have unique advantages that can help them succeed.

### Agility and Speed to Market

One of the biggest advantages of small businesses is their agility. Unlike large enterprises, SMBs can quickly implement new technologies and adapt to changes in the market. This agility allows you to capitalize on AI's benefits faster and more efficiently.

### Cost, Time, and Resource Savings

Developing in-house AI solutions can be expensive and time-consuming. Salesforce's pre-built AI solutions offer a cost-effective and time-saving alternative. These solutions are tailored to the needs of SMBs and can be implemented quickly, without the need for extensive development resources.

## Broader Economic Impact

AI has the potential to level the playing field for small businesses competing against larger enterprises. By providing access to cutting-edge technologies, AI can help SMBs grow and create jobs.

### Economic Contribution of SMBs

Small businesses are the backbone of the economy, contributing significantly to job creation and economic growth. According to Statistics Canada, small businesses account for a substantial portion of the country's GDP and employment. By adopting AI, you can enhance your business's performance and contribute to the broader economic landscape.

### Leveling the Playing Field

AI can help small businesses level the playing field against larger enterprises. With access to the same advanced technologies, you can compete more effectively and deliver exceptional customer experiences. As Marc Benioff, CEO of Salesforce, noted, "AI is the future of business, and SMBs that don't adopt it will be left behind."

## Conclusion

In summary, AI is a powerful tool that can help small businesses unlock growth, productivity, and innovation. By understanding the benefits, learning from real-world examples, and overcoming common challenges, you can successfully adopt AI and stay ahead of the curve. We encourage you to explore Salesforce's AI tools and discover how they can help your small business thrive.
""")


        
@slack_app.action("approve_blog_article")
def handle_approve_blog_article(ack, body, client, logger):
    """
    Handles the 'Approve' button click for the blog article.
    """
    # Acknowledge the button click immediately
    ack()

    # Run the heavy operation in a separate thread
    def process_approval():
        try:
            # Log the body for debugging
            logger.info(f"Slack event body: {body}")

            # Extract channel ID and thread_ts from the message
            channel_id = body["channel"]["id"]
            thread_ts = body.get("message", {}).get("ts")

            # Notify the user that the article is being sent to WordPress
            client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=":hourglass_flowing_sand: Sending the article to WordPress..."
            )

            # Convert markdown to HTML first
            html_content = markdown.markdown(article_content)
            print(html_content)
            
            # Then use it in the create_article call
            async def create_article_async():
                return await wordpress_service.create_article(
                    title="Why Small Businesses Should Embrace AI: Unlocking Growth, Productivity, and Innovation",
                    content=html_content,  # Use the converted HTML content
                    status="draft",
                    format="standard"
                )

            # Run the async function and get the result
            result = asyncio.run(create_article_async())

            # Log the result for debugging
            logger.info(f"WordPress article creation result: {result}")

            # Construct the draft link
            post_id = result.get("id")
            wordpress_site_url = "https://wordpress-p30c.onrender.com"
            draft_link = f"{wordpress_site_url}/wp-admin/post.php?post={post_id}&action=edit"

            # Notify the user of success
            client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=f":white_check_mark: Article successfully sent to WordPress as a draft! <{draft_link}|View Draft>"
            )

        except Exception as e:
            logger.error(f"Error handling approve button: {e}")
            client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=f":warning: An error occurred while sending the article to WordPress: {str(e)}"
            )

    # Start the long-running task in a separate thread
    Thread(target=process_approval).start()

@slack_app.event("file_shared")
def handle_file_shared_event(body, logger):
    """
    Handles the 'file_shared' event from Slack, extracts email information, creates a Salesforce record, and sends a message to Slack.
    """
    try:
        # Log the entire event body for debugging
        logger.info("Received file_shared event")
        logger.info(body)

        # Extract relevant data from the event
        event_data = body.get("event", {})
        files = event_data.get("files", [])
        user_id = event_data.get("user")
        channel_id = event_data.get("channel")

        # Set the claim details
        claim_amount = "7800.00"
        claim_status = "New"
        claim_type = "Critical Illness"
        date_of_claim = datetime.today().strftime('%Y-%m-%d')
        healthcare_provider = "City General Hospital"

        # Create a Salesforce record
        sf.Insurance_Claim__c.create({
            'Claim_Amount__c': claim_amount,
            'Claim_Status__c': claim_status,
            'Claim_Type__c': claim_type,
            'Date_of_Claim__c': date_of_claim,
            'Healthcare_Provider__c': healthcare_provider,
            'Contact__c': '003aj00000Ek20LAAR'
        })


            # Send claim details to Slack channel with interactive buttons
        slack_app.client.chat_postMessage(
            channel="C089BMNHYQJ",
            text=(
                f"New Insurance Claim Received:\n"
                f"Claim Amount: $$7,800\n"
                f"Claim Status: {claim_status}\n"
                f"Claim Type: {claim_type}\n"
                f"Date of Claim: {date_of_claim}\n"
                f"Healthcare Provider: {healthcare_provider}\n"
                f"Priority: High :exclamation: \n"
                f"Sentiment: Negative :red_circle: \n" 
                "Salesforce Record: "
            ),
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*New Insurance Claim Received:*\n"
                            f"*Claim Amount:* $7,800\n"
                            f"*Claim Status:* {claim_status}\n"
                            f"*Claim Type:* {claim_type}\n"
                            f"*Date of Claim:* {date_of_claim}\n"
                            f"*Healthcare Provider:* {healthcare_provider}\n"
                            f"*Priority:* High :exclamation:\n"
                            f"*Sentiment:* Negative :red_circle:\n"
                            f"*Salesforce Record:* <https://writer6-dev-ed.develop.lightning.force.com/lightning/r/Insurance_Claim__c/a00aj00000cNlbSAAS/view|View Record>"
                        )
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                         {
                            "type": "button",
                            "text": {"type": "plain_text", "text": ":writer-icon: Analyze Claim"},
                            "action_id": "review_policy_coverage"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View Claim"},
                            "action_id": "verify_medical_records", 
                            "url": "https://writer6-dev-ed.develop.lightning.force.com/lightning/r/Insurance_Claim__c/a00aj00000cNlbSAAS/view"
                        },

                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Run Fraud Check"},
                            "action_id": "run_fraud_check"
                        },
                       
                    ]
                }
            ]
        )

    except Exception as e:
        logger.error(f"Error handling file_shared event: {e}")

@slack_app.action("review_policy_coverage")
def handle_review_policy_coverage(ack, body, client):
    """
    Handles the 'Review Policy Coverage' button click and updates a Slack message sequentially with progress updates.
    """
    ack()  # Acknowledge the button press

    # Extract channel ID and thread_ts from the message
    channel_id = body["channel"]["id"]
    thread_ts = body.get("message", {}).get("ts")

    # Define sequential messages
    messages = [
        ":hourglass_flowing_sand: Retrieving policy holding file from :salesforce-logo: Salesforce...",
        (
            ":hourglass_flowing_sand: Retrieving policy holding file from :salesforce-logo: Salesforce...\n"
            ":hourglass_flowing_sand: Retrieving doctor report from :database: internal database..."
        ),
        (
            ":hourglass_flowing_sand: Retrieving policy holding file from :salesforce-logo: Salesforce...\n"
            ":hourglass_flowing_sand: Retrieving doctor report from :database: internal database...\n"
            ":hourglass_flowing_sand: Retrieving police report from :database: internal database..."
        ),
        (
            ":hourglass_flowing_sand: Retrieving policy holding file from :salesforce-logo: Salesforce...\n"
            ":hourglass_flowing_sand: Retrieving doctor report from :database: internal database...\n"
            ":hourglass_flowing_sand: Retrieving police report from :database: internal database...\n"
            ":hourglass_flowing_sand: Searching :writer: knowledge graph for policy details..."
        ),
        (
            ":white_check_mark: Policy coverage information retrieved.\n"
            "Sources:\n"
            "- Policyholding file from :salesforce-logo: Salesforce\n"
            "- Doctor report from :database: internal database\n"
            "- Police report from :database: internal database\n"
            "- :writer: Knowledge Graph\n\n"
            "Summary can be found here: <https://writerai.slack.com/docs/T02AJRK99/F088DBCSDJA|Canvas Link>"
        ),
    ]

    try:
        # Send the initial message
        initial_payload = {
            "channel": channel_id,
            "text": messages[0],
            "thread_ts": thread_ts,  # Ensure it is a threaded reply
        }
        response = client.chat_postMessage(**initial_payload)

        if not response["ok"]:
            logger.error(f"Error sending initial message: {response['error']}")
            return

        message_ts = response["ts"]  # Timestamp of the sent message

        # Sequentially update the message with progress
        for i in range(1, len(messages)):
            time.sleep(5)  # Delay between updates
            update_payload = {
                "channel": channel_id,
                "ts": message_ts,  # Reference the original message's timestamp
                "text": messages[i],
            }
            update_response = client.chat_update(**update_payload)

            if not update_response["ok"]:
                logger.error(f"Error updating message at step {i}: {update_response['error']}")
                break

        # Add buttons after the final message
        # Define the blocks for the message with buttons
        final_buttons_payload = {
            "channel": channel_id,
            "ts": message_ts,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Follow up with the customer with one of the following actions:"
                    }
                },
                {
                    "type": "actions",
                    "block_id": "policy_review_actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Approved"
                            },
                            "value": "approved",
                            "action_id": "approve"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Conditionally Approved"
                            },
                            "value": "conditionally_approved",
                            "action_id": "conditionally_approved"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Additional Investigation Required"
                            },
                            "value": "additional_investigation",
                            "action_id": "additional_investigation"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Rejected"
                            },
                            "value": "rejected",
                            "action_id": "reject"
                        }
                    ]
                }
            ]
        }
        final_buttons_payload["thread_ts"] = message_ts  # Ensure the message is threaded
        client.chat_postMessage(**final_buttons_payload)

    except Exception as e:
        logger.error(f"Error during message update sequence: {e}")


@slack_app.action("verify_medical_records")
def handle_some_action(ack, body, logger):
    ack()
    logger.info(body)


# Handle Conditional Approval button click
@slack_app.action("conditionally_approved")
def handle_conditionally_approved(ack, body, logger):
    ack()
    logger.info(body)

    # Retrieve channel ID and message timestamp from the correct location in the payload
    channel_id = body.get("container", {}).get("channel_id")
    message_ts = body.get("container", {}).get("message_ts")

    # Log an error if channel ID or message timestamp is missing
    if not channel_id or not message_ts:
        logger.error("Missing channel ID or message timestamp in the request body.")
        return

    # Simulate updating Salesforce status to "Conditionally Approved"
    logger.info("Simulating update of Salesforce status to 'Conditionally Approved'")

    # Send initial message indicating conditional approval
    try:
        response = slack_app.client.chat_postMessage(
            channel=channel_id,
            text="Claim is conditionally approved in Salesforce",
            thread_ts=message_ts
        )
        logger.info(f"Initial conditional approval message sent: {response}")
    except Exception as e:
        logger.error(f"Failed to send initial conditional approval message: {e}")
        return

    # Wait for 5 seconds before sending the next message
    time.sleep(5)

    # Simulate updating Salesforce status to "Done"
    logger.info("Simulating update of Salesforce status to 'Done'")

    # Send a follow-up message with the suggested email canvas link
    try:
        response = slack_app.client.chat_postMessage(
            channel=channel_id,
            text="Here is a suggested email to send to the customer: <https://writerai.slack.com/docs/T02AJRK99/F088P7L690U|Canvas Link>",
            thread_ts=message_ts
        )
        logger.info(f"Follow-up message with canvas link sent: {response}")
    except Exception as e:
        logger.error(f"Failed to send follow-up message: {e}")


# Function to delete all messages in a channel
def delete_all_messages(channel_id):
    try:
        # Retrieve all messages in the channel
        response = slack_app.client.conversations_history(channel=channel_id)
        messages = response.get("messages", [])

        # Loop through and delete each message and its threaded replies
        for message in messages:
            ts = message.get("ts")
            if ts:
                # Retrieve threaded replies
                replies_response = slack_app.client.conversations_replies(channel=channel_id, ts=ts)
                replies = replies_response.get("messages", [])

                # Delete each threaded reply
                for reply in replies:
                    reply_ts = reply.get("ts")
                    if reply_ts:
                        slack_app.client.chat_delete(channel=channel_id, ts=reply_ts)
                        logger.info(f"Deleted threaded reply with timestamp: {reply_ts}")

                # Delete the original message
                slack_app.client.chat_delete(channel=channel_id, ts=ts)
                logger.info(f"Deleted message with timestamp: {ts}")
    except Exception as e:
        logger.error(f"Error deleting messages: {e}")

# Execute the function to delete all messages in a specific channel
#delete_all_messages("C08476AM146")

