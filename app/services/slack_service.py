from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from app.config import settings
import logging

logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more verbosity
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.info("Logger initialized!")  # Verify logger initialization


# Initialize the Slack Bolt app
slack_app = App(
    token=settings.SLACK_BOT_TOKEN,
    signing_secret=settings.SLACK_SIGNING_SECRET,
    logger=logger  # Attach the logger
)

slack_handler = SlackRequestHandler(slack_app)

# Define Slack event handlers
@slack_app.event("message")
#if event is im then log it
def handle_message_events(body, say):
    logger.info(f"Received message event: {body}")
    say("Message received!")
