"""
Simple Flask-based Teams Bot
Nincs szükség Azure Functions CLI-re, pure Python HTTP server
"""

from flask import Flask, request, jsonify
import logging
import os
import requests
import time
import json

app = Flask(__name__)

# Load local.settings.json if it exists (MUST BE BEFORE reading config values)
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
settings_file = os.path.join(script_dir, 'local.settings.json')

try:
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            settings = json.load(f)
            # Load ALL values from local.settings.json, overwriting if needed
            for key, value in settings.get('Values', {}).items():
                if value:  # Only set if value is not empty
                    os.environ[key] = str(value)
except Exception as e:
    pass  # If loading fails, continue with existing env vars

# Configuration from environment or defaults
APP_ID = os.environ.get("MicrosoftAppId", "19c6dc8f-ba5d-4f10-8df2-af473d5515f0")
APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

# LLM Provider selection (NOW reads from environment after local.settings.json was loaded)
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "llama3").lower()

# Azure OpenAI config
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")

# Llama3 config
LLAMA3_API_URL = os.environ.get("LLAMA3_API_URL", "http://localhost:11434")
LLAMA3_MODEL = os.environ.get("LLAMA3_MODEL", "llama3")

# No pre-initialization of clients - they will be created dynamically when needed
# This allows hot-switching between different LLM providers without restart

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info(f"🤖 Teams Bot initialized")
logger.info(f"📌 LLM_PROVIDER: {LLM_PROVIDER}")
if LLM_PROVIDER == "azure":
    logger.info(f"☁️  Azure OpenAI: {AZURE_OPENAI_ENDPOINT}")
else:
    logger.info(f"🦙 Llama3 API: {LLAMA3_API_URL}")

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
    
    logger.info(f"🔑 Requesting token from: {token_url}")
    logger.info(f"   Client ID: {APP_ID}")
    logger.info(f"   Has password: {bool(APP_PASSWORD)}")
    
    try:
        response = requests.post(token_url, data=data, timeout=10)
        logger.info(f"   Response status: {response.status_code}")
        response.raise_for_status()
        token_data = response.json()
        
        _token_cache["token"] = token_data["access_token"]
        _token_cache["expires_at"] = now + 3300
        
        logger.info("✅ Bot access token refreshed successfully")
        return _token_cache["token"]
    except Exception as e:
        logger.error(f"❌ Failed to get access token: {e}")
        if 'response' in locals():
            logger.error(f"   Response text: {response.text}")
        return None

def send_activity_to_conversation(service_url, conversation_id, activity):
    """Send Activity to Teams conversation via Bot Framework REST API"""
    token = get_bot_access_token()
    if not token:
        logger.error("❌ No access token available - cannot send response")
        return False
    
    api_url = f"{service_url}v3/conversations/{conversation_id}/activities"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    logger.info(f"📤 Sending activity to Teams:")
    logger.info(f"   URL: {api_url}")
    logger.info(f"   Message: {activity.get('text', '')[:100]}")
    
    try:
        response = requests.post(api_url, json=activity, headers=headers, timeout=10)
        logger.info(f"   Response status: {response.status_code}")
        response.raise_for_status()
        logger.info(f"✅ Activity sent successfully to {conversation_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send activity: {e}")
        if 'response' in locals():
            logger.error(f"   Response text: {response.text}")
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
    """Get response from Llama3 - reads config dynamically"""
    try:
        # Always read current config from environment
        llama3_url = os.environ.get("LLAMA3_API_URL", "http://localhost:11434")
        llama3_model = os.environ.get("LLAMA3_MODEL", "llama3")
        
        logger.info(f"Sending to Llama3 at {llama3_url}: {user_message}")
        
        messages = [
            {"role": "system", "content": "Te egy barátságos Teams bot vagy. Válaszolj röviden és segítőkészen magyarul."}
        ]
        
        history = get_conversation_history(conversation_id)
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        
        payload = {
            "model": llama3_model,
            "messages": messages,
            "stream": False
        }
        
        response = requests.post(
            f"{llama3_url}/api/chat",
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        ai_reply = data.get("message", {}).get("content", "")
        
        if not ai_reply:
            logger.warning("Empty response from Llama3")
            return "Sajnálom, üres válasz érkezett"
        
        logger.info(f"✅ Llama3 response: {ai_reply[:100]}...")
        
        add_to_conversation_history(conversation_id, "user", user_message)
        add_to_conversation_history(conversation_id, "assistant", ai_reply)
        
        return ai_reply
        
    except requests.exceptions.Timeout:
        logger.error("❌ Llama3 request timeout")
        return "Sajnálom, az AI szerver nem válaszol időben"
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Cannot connect to Llama3 at {os.environ.get('LLAMA3_API_URL')}: {e}")
        return f"Sajnálom, nem tudom elérni az AI szervert"
    except Exception as e:
        logger.error(f"❌ Llama3 error: {e}")
        return "Sajnálom, hiba történt az AI válasz generálása során"

def get_azure_openai_response(user_message, conversation_id):
    """Get response from Azure OpenAI - reads config dynamically"""
    try:
        # Always read current config from environment
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
        api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
        deployment = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")
        
        if not endpoint or not api_key:
            logger.warning("❌ Azure OpenAI not configured (missing endpoint or API key)")
            return "Azure OpenAI nincs konfigurálva"
        
        # Create client dynamically
        from openai import AzureOpenAI
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-12-01-preview"
        )
        
        logger.info(f"📤 Sending to Azure OpenAI ({deployment}): {user_message}")
        
        messages = [
            {"role": "system", "content": "Te egy barátságos Teams bot vagy. Válaszolj röviden és segítőkészen magyarul."}
        ]
        
        history = get_conversation_history(conversation_id)
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        
        response = client.chat.completions.create(
            model=deployment,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        ai_reply = response.choices[0].message.content
        logger.info(f"✅ Azure OpenAI response: {ai_reply[:100]}...")
        
        add_to_conversation_history(conversation_id, "user", user_message)
        add_to_conversation_history(conversation_id, "assistant", ai_reply)
        
        return ai_reply
        
    except Exception as e:
        logger.error(f"❌ Azure OpenAI error: {e}")
        return "Sajnálom, hiba történt az Azure OpenAI válasz generálása során"

def get_ai_response(user_message, conversation_id):
    """Route to appropriate AI provider based on current config"""
    # Always read the current LLM_PROVIDER from environment (which loads from local.settings.json)
    current_provider = os.environ.get("LLM_PROVIDER", "llama3").lower()
    
    logger.info(f"Using LLM provider: {current_provider}")
    
    if current_provider == "llama3":
        return get_llama3_response(user_message, conversation_id)
    elif current_provider == "azure":
        return get_azure_openai_response(user_message, conversation_id)
    else:
        logger.warning(f"Unknown LLM provider: {current_provider}, falling back to echo")
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
