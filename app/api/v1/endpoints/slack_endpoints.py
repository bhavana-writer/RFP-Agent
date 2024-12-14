from fastapi import APIRouter, Request, HTTPException
from app.services.slack_service import slack_handler, post_slack_message, create_canvas, post_canvas_message, send_account_followup_message
from app.services.slack_service import logger
import json

router = APIRouter()


@router.post("/events")
async def slack_events(request: Request):
    """
    Handles Slack events sent to the endpoint.
    """
    try:
        # Log raw request body for debugging
        raw_body = await request.body()
        logger.info(f"Raw request body: {raw_body.decode('utf-8')}")

        # Parse request body based on content type
        if request.headers.get("content-type") == "application/json":
            body = await request.json()
        elif request.headers.get("content-type") == "application/x-www-form-urlencoded":
            form_data = await request.form()
            payload = form_data.get("payload")
            body = json.loads(payload) if payload else {}
        else:
            raise HTTPException(
                status_code=415, detail="Unsupported Media Type"
            )

        logger.info(f"Slack event received: {body}")
        return await slack_handler.handle(request)
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/canvas/create")
async def create_canvas_endpoint(title: str, content: str):
    """
    API endpoint to create a new Slack Canvas document.
    """
    try:
        response = create_canvas(title, content)
        if not response.get("ok"):
            raise HTTPException(status_code=500, detail=f"Error creating canvas: {response.get('error', 'Unknown error')}")
        return {"status": "success", "canvas_id": response.get("canvas_id")}
    except Exception as e:
        logger.error(f"Error in /canvas/create: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/canvas/share")
async def share_canvas_endpoint(canvas_url: str, channel: str, message_text: str = "Here is the canvas you requested!"):
    """
    API endpoint to share a Canvas document by posting its URL to a specified Slack channel.
    """
    try:
        response = post_canvas_message(canvas_url=canvas_url, channel_id=channel, message_text=message_text)
        if response.get("error"):
            raise HTTPException(status_code=500, detail=f"Error sharing canvas: {response['error']}")
        return {"status": "success", "message": f"Canvas shared successfully to channel {channel}"}
    except Exception as e:
        logger.error(f"Error in /canvas/share: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/message/send")
async def send_message_endpoint(channel_id: str, text: str):
    """
    API endpoint to send a message to a Slack channel.
    """
    try:
        response = post_slack_message(channel_id, text)
        if not response.get("ok"):
            raise HTTPException(status_code=500, detail=f"Error sending message: {response.get('error', 'Unknown error')}")
        return {"status": "success", "message": "Message sent successfully"}
    except Exception as e:
        logger.error(f"Error in /message/send: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/message/account-followup")
async def send_account_followup(channel_id: str, message: str):
    """
    API endpoint to send an account follow-up message with Block Kit buttons.

    :param channel_id: The Slack channel ID where the message will be sent.
    :param message: Markdown-supported text for the follow-up message.
    :return: API response or error message.
    """
    try:
        response = send_account_followup_message(channel_id, message)
        if response.get("error"):
            raise HTTPException(
                status_code=500,
                detail=f"Error sending follow-up message: {response['error']}",
            )
        return {
            "status": "success",
            "message": f"Follow-up message sent successfully to channel {channel_id}",
        }
    except Exception as e:
        logger.error(f"Error in /message/account-followup: {e}")
        raise HTTPException(status_code=500, detail=str(e))
