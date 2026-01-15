"""
Simple Flask-based Teams Bot
Nincs szükség Azure Functions CLI-re, pure Python HTTP server
"""

from flask import Flask, request, jsonify
import logging
import os
import requests
import time

app = Flask(__name__)

# Configuration from environment or defaults
APP_ID = os.environ.get("MicrosoftAppId", "19c6dc8f-ba5d-4f10-8df2-af473d5515f0")
APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

# LLM Provider selection
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "llama3").lower()

# Azure OpenAI config
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")

# Llama3 config
LLAMA3_API_URL = os.environ.get("LLAMA3_API_URL", "http://localhost:11434")
LLAMA3_MODEL = os.environ.get("LLAMA3_MODEL", "llama3")

# Initialize Azure OpenAI client if needed
openai_client = None
if LLM_PROVIDER == "azure" and AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY:
    from openai import AzureOpenAI
    openai_client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION
    )

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Token cache
_token_cache = {"token": None, "expires_at": 0}

# Conversation history
_conversation_history = {}

logger.info(f"Teams Bot started with LLM_PROVIDER: {LLM_PROVIDER}")

def get_bot_access_token():
    """Get Microsoft Bot Framework access token"""
    now = time.time()
    
    if _token_cache["token"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]
    
    tenant_id = os.environ.get("MicrosoftAppTenantId", "5363c28c-cdab-42ce-86c6-1b35f030504b")
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    data = {
        "grant_type": "client_credentials",
        "client_id": APP_ID,
        "client_secret": APP_PASSWORD,
        "scope": "https://api.botframework.com/.default"
    }
    
    try:
        response = requests.post(token_url, data=data, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        
        _token_cache["token"] = token_data["access_token"]
        _token_cache["expires_at"] = now + 3300
        
        logger.info("Bot access token refreshed")
        return _token_cache["token"]
    except Exception as e:
        logger.error(f"Failed to get access token: {e}")
        return None

def send_activity_to_conversation(service_url, conversation_id, activity):
    """Send Activity to Teams conversation via Bot Framework REST API"""
    token = get_bot_access_token()
    if not token:
        logger.error("No access token available")
        return False
    
    api_url = f"{service_url}v3/conversations/{conversation_id}/activities"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(api_url, json=activity, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"Activity sent successfully to {conversation_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send activity: {e}")
        return False

def get_conversation_history(conversation_id):
    """Get conversation history"""
    return _conversation_history.get(conversation_id, [])

def add_to_conversation_history(conversation_id, role, message):
    """Add message to history (keep last 10 messages)"""
    if conversation_id not in _conversation_history:
        _conversation_history[conversation_id] = []
    
    _conversation_history[conversation_id].append({
        "role": role,
        "content": message
    })
    
    if len(_conversation_history[conversation_id]) > 10:
        _conversation_history[conversation_id] = _conversation_history[conversation_id][-10:]
    
    logger.debug(f"Conversation history length: {len(_conversation_history[conversation_id])}")

def get_llama3_response(user_message, conversation_id):
    """Get response from Llama3"""
    try:
        logger.info(f"Sending to Llama3: {user_message}")
        
        messages = [
            {"role": "system", "content": "Te egy barátságos Teams bot vagy. Válaszolj röviden és segítőkészen magyarul."}
        ]
        
        history = get_conversation_history(conversation_id)
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        
        payload = {
            "model": LLAMA3_MODEL,
            "messages": messages,
            "stream": False
        }
        
        response = requests.post(
            f"{LLAMA3_API_URL}/api/chat",
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        ai_reply = data.get("message", {}).get("content", "")
        
        if not ai_reply:
            logger.warning("Empty response from Llama3")
            return "Sajnálom, üres válasz érkezett"
        
        logger.info(f"Llama3 response: {ai_reply[:100]}...")
        
        add_to_conversation_history(conversation_id, "user", user_message)
        add_to_conversation_history(conversation_id, "assistant", ai_reply)
        
        return ai_reply
        
    except requests.exceptions.Timeout:
        logger.error("Llama3 request timeout")
        return "Sajnálom, az AI szerver nem válaszol időben"
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to Llama3 at {LLAMA3_API_URL}")
        return f"Sajnálom, nem tudom elérni az AI szervert"
    except Exception as e:
        logger.error(f"Llama3 error: {e}")
        return "Sajnálom, hiba történt az AI válasz generálása során"

def get_azure_openai_response(user_message, conversation_id):
    """Get response from Azure OpenAI"""
    if not openai_client:
        logger.warning("Azure OpenAI client not initialized")
        return "Azure OpenAI nincs konfigurálva"
    
    try:
        logger.info(f"Sending to Azure OpenAI: {user_message}")
        
        messages = [
            {"role": "system", "content": "Te egy barátságos Teams bot vagy. Válaszolj röviden és segítőkészen magyarul."}
        ]
        
        history = get_conversation_history(conversation_id)
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        
        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_CHAT_DEPLOYMENT,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        ai_reply = response.choices[0].message.content
        logger.info(f"Azure OpenAI response: {ai_reply[:100]}...")
        
        add_to_conversation_history(conversation_id, "user", user_message)
        add_to_conversation_history(conversation_id, "assistant", ai_reply)
        
        return ai_reply
        
    except Exception as e:
        logger.error(f"Azure OpenAI error: {e}")
        return "Sajnálom, hiba történt az AI válasz generálása során"

def get_ai_response(user_message, conversation_id):
    """Route to appropriate AI provider"""
    if LLM_PROVIDER == "llama3":
        return get_llama3_response(user_message, conversation_id)
    elif LLM_PROVIDER == "azure":
        return get_azure_openai_response(user_message, conversation_id)
    else:
        logger.warning(f"Unknown LLM provider: {LLM_PROVIDER}")
        return f"Echo: {user_message}"

@app.route('/api/messages', methods=['POST'])
def messages():
    """Bot Framework endpoint for Microsoft Teams"""
    logger.info('=== Bot message received from Teams ===')
    
    try:
        body = request.get_json()
        activity_type = body.get("type", "")
        
        logger.info(f'Activity type: {activity_type}')
        
        # Handle message activities
        if activity_type == "message":
            user_message = body.get("text", "")
            conversation = body.get("conversation", {})
            conversation_id = conversation.get("id", "")
            from_user = body.get("from", {})
            service_url = body.get("serviceUrl", "")
            
            user_name = from_user.get("name", "Unknown")
            
            logger.info(f'User: {user_name}, Message: "{user_message}"')
            
            # Get response from AI
            bot_reply = get_ai_response(user_message, conversation_id)
            
            # Create response activity
            response_activity = {
                "type": "message",
                "text": bot_reply,
                "from": {
                    "id": APP_ID,
                    "name": "Fresh Bot"
                }
            }
            
            logger.info(f'Sending response: "{bot_reply}"')
            
            # Send response
            success = send_activity_to_conversation(service_url, conversation_id, response_activity)
            
            if success:
                logger.info("Response sent successfully")
            else:
                logger.error("Failed to send response")
            
            return "", 200
        
        # Handle conversationUpdate
        elif activity_type == "conversationUpdate":
            members_added = body.get("membersAdded", [])
            logger.info(f'Conversation update - Members added: {len(members_added)}')
            
            for member in members_added:
                if member.get("id") == APP_ID:
                    logger.info('Bot was added to conversation')
                    welcome_message = "Szia! Én vagyok a Fresh Bot! 👋 Írj bármit és segíteni fogok!"
                    
                    response_activity = {
                        "type": "message",
                        "text": welcome_message,
                        "from": {"id": APP_ID, "name": "Fresh Bot"}
                    }
                    
                    service_url = body.get("serviceUrl", "")
                    conversation_id = body.get("conversation", {}).get("id", "")
                    
                    send_activity_to_conversation(service_url, conversation_id, response_activity)
            
            return "", 200
        
        # Handle other activity types
        else:
            logger.info(f'Unhandled activity type: {activity_type}')
            return "", 200
    
    except Exception as e:
        logger.error(f'Error processing message: {str(e)}', exc_info=True)
        return "", 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Fresh Teams Bot',
        'llm_provider': LLM_PROVIDER
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7071))
    logger.info(f"Starting server on 0.0.0.0:{port}")
    try:
        logger.info("About to start Flask app...")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Error starting Flask app: {e}", exc_info=True)
        raise
