import azure.functions as func
import json
import logging
import os
import requests

# Bot credentials
APP_ID = os.environ.get("MicrosoftAppId", "")
APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Bot Framework Adapter - converts Teams Activity to simple JSON
    and forwards to the /api/chat endpoint
    """
    logging.info('Bot message received from Teams via /api/messages')
    
    try:
        # Parse Bot Framework Activity
        body = req.get_json()
        activity_type = body.get("type", "")
        
        # Handle message activity
        if activity_type == "message":
            user_message = body.get("text", "")
            from_id = body.get("from", {}).get("id", "")
            
            logging.info(f'User message: {user_message}')
            
            # Call the existing /api/chat endpoint
            chat_response = requests.post(
                "https://fresh-teams-bot-func.azurewebsites.net/api/chat",
                json={"message": user_message},
                timeout=10
            )
            
            if chat_response.status_code == 200:
                chat_data = chat_response.json()
                reply_text = chat_data.get("reply", "Echo response")
                
                # Return Bot Framework response
                response_activity = {
                    "type": "message",
                    "text": reply_text,
                    "from": {"id": APP_ID},
                    "recipient": {"id": from_id}
                }
                
                return func.HttpResponse(
                    json.dumps(response_activity),
                    status_code=200,
                    mimetype="application/json"
                )
            else:
                logging.error(f'Chat endpoint error: {chat_response.status_code}')
                return func.HttpResponse(
                    json.dumps({"error": "Chat endpoint failed"}),
                    status_code=500
                )
        
        # Handle other activity types (conversationUpdate, etc.)
        elif activity_type == "conversationUpdate":
            # Bot added to conversation
            logging.info('Bot added to conversation')
            return func.HttpResponse(status_code=200)
        
        else:
            # Unknown activity type
            logging.info(f'Unhandled activity type: {activity_type}')
            return func.HttpResponse(status_code=200)
            
    except Exception as e:
        logging.error(f'Error processing Bot message: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500
        )
