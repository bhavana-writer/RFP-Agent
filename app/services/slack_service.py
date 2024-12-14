import os
import requests
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from app.config import settings
from app.services.google_trends_service import GoogleTrendsService
from writerai import Writer
import logging
import json
import asyncio
import time

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

# Initialize Writer Client
writer_client = Writer(api_key=settings.WRITER_API_KEY)

# Define tools (Google Trends Service methods as tools)
tools = [
    {
        "type": "function",
        "function": {
            "name": "interest_over_time",
            "description": "Fetches the interest over time for a query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The keyword or topic to search (e.g., 'coffee')."
                    },
                    "date_range": {
                        "type": "string",
                        "description": "Time range for the data (e.g., 'today 12-m'). Default is past 12 months.",
                        "default": "today 12-m"
                    },
                    "geo": {
                        "type": "string",
                        "description": "Geographical location (e.g., 'US' for the United States). Default is worldwide.",
                        "default": ""
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "related_queries",
            "description": "Fetches related queries for a query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The keyword or topic to search (e.g., 'coffee')."
                    },
                    "date_range": {
                        "type": "string",
                        "description": "Time range for the data (e.g., 'today 12-m'). Default is past 12 months.",
                        "default": "today 12-m"
                    },
                    "geo": {
                        "type": "string",
                        "description": "Geographical location (e.g., 'US' for the United States). Default is worldwide.",
                        "default": ""
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# Define Google Trends functions
async def interest_over_time(query: str, date_range: str = "today 12-m", geo: str = ""):
    return GoogleTrendsService.interest_over_time(query=query, date_range=date_range, geo=geo)

async def related_queries(query: str, date_range: str = "today 12-m", geo: str = ""):
    return GoogleTrendsService.related_queries(query=query, date_range=date_range, geo=geo)

@slack_app.event("message")
def handle_message_events(body, say):
    """
    Handles incoming Slack message events, processes tools via Writer's API, and returns responses.
    """
    logger.info(f"Received message event: {body}")

    # Extract the message text
    message_text = body.get("event", {}).get("text", "")

    # Define the initial message payload
    messages = [{"role": "user", "content": message_text}]

    try:
        # Call Writer's Chat Completion API with tools
        response = writer_client.chat.chat(
            model="palmyra-x-004",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            stream=False,
        )

        # Process tool calls if any
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            # Match the tool and call the corresponding function
            if tool_name == "interest_over_time":
                result = asyncio.run(interest_over_time(**arguments))
            elif tool_name == "related_queries":
                result = asyncio.run(related_queries(**arguments))
            else:
                result = {"error": f"Unknown tool called: {tool_name}"}

            # Append the result back to the conversation
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": tool_name,
                    "content": json.dumps(result),
                }
            )

            # Call the model again to process the tool response
            second_response = writer_client.chat.chat(
                model="palmyra-x-004",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                stream=False,
            )
            final_response = second_response.choices[0].message.content
        else:
            # No tool calls found
            final_response = response.choices[0].message.content

        # Respond back to Slack
        say(final_response)

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        say(f"Error processing your message: {e}")

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
