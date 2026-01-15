import azure.functions as func
import json
import logging
import os
import requests
import time

app = func.FunctionApp()

# Bot credentials from environment variables
APP_ID = os.environ.get("MicrosoftAppId", "")
APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

# LLM Provider selection
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "azure").lower()

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")

# Llama3 configuration
LLAMA3_API_URL = os.environ.get("LLAMA3_API_URL", "http://172.30.12.144:11434")
LLAMA3_MODEL = os.environ.get("LLAMA3_MODEL", "llama3")

# Initialize clients
openai_client = None
if LLM_PROVIDER == "azure":
    if AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY:
        from openai import AzureOpenAI
        openai_client = AzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION
        )
        logging.info(f"Azure OpenAI initialized with deployment: {AZURE_OPENAI_CHAT_DEPLOYMENT}")
    else:
        logging.warning("Azure OpenAI not configured")
elif LLM_PROVIDER == "llama3":
    logging.info(f"Llama3 configured: {LLAMA3_API_URL} (model: {LLAMA3_MODEL})")

# Cache for access token
_token_cache = {"token": None, "expires_at": 0}

# Conversation history cache (in-memory)
_conversation_history = {}

logging.info(f'Fresh Bot initialized with App ID: {APP_ID[:8] if APP_ID else "MISSING"}...')
logging.info(f'LLM Provider: {LLM_PROVIDER}')

def get_bot_access_token():
    """Get Microsoft Bot Framework access token (with caching)"""
    now = time.time()
    
    # Return cached token if still valid
    if _token_cache["token"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]
    
    # Request new token (for SingleTenant bot, use specific tenant ID)
    tenant_id = os.environ.get("MicrosoftAppTenantId", "5363c28c-cdab-42ce-86c6-1b35f030504b")
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": APP_ID,
        "client_secret": APP_PASSWORD,
        "scope": "https://api.botframework.com/.default"
    }
    
    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        
        # Cache token (expires in 3600s, refresh after 55 min)
        _token_cache["token"] = token_data["access_token"]
        _token_cache["expires_at"] = now + 3300  # 55 minutes
        
        logging.info("Bot access token refreshed")
        return _token_cache["token"]
    except Exception as e:
        logging.error(f"Failed to get access token: {e}")
        return None

def send_activity_to_conversation(service_url, conversation_id, activity):
    """Send Activity to Teams conversation via Bot Framework REST API"""
    token = get_bot_access_token()
    if not token:
        logging.error("No access token available")
        return False
    
    # Bot Framework API endpoint
    api_url = f"{service_url}v3/conversations/{conversation_id}/activities"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(api_url, json=activity, headers=headers)
        response.raise_for_status()
        logging.info(f"Activity sent successfully to {conversation_id}")
        return True
    except Exception as e:
        logging.error(f"Failed to send activity: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"Response: {e.response.text}")
        return False

def get_conversation_history(conversation_id):
    """Get conversation history for a conversation"""
    return _conversation_history.get(conversation_id, [])

def add_to_conversation_history(conversation_id, role, message):
    """Add message to conversation history (keep last 10 messages)"""
    if conversation_id not in _conversation_history:
        _conversation_history[conversation_id] = []
    
    _conversation_history[conversation_id].append({
        "role": role,
        "content": message
    })
    
    # Keep only last 10 messages (5 user-bot turns)
    if len(_conversation_history[conversation_id]) > 10:
        _conversation_history[conversation_id] = _conversation_history[conversation_id][-10:]
    
    logging.info(f"Conversation history length: {len(_conversation_history[conversation_id])} messages")

def get_ai_response(user_message, conversation_id):
    """Get response from configured AI provider"""
    
    if LLM_PROVIDER == "azure":
        return get_azure_openai_response(user_message, conversation_id)
    elif LLM_PROVIDER == "llama3":
        return get_llama3_response(user_message, conversation_id)
    else:
        logging.warning(f"Unknown LLM provider: {LLM_PROVIDER}")
        return f"Echo: {user_message}"

def get_azure_openai_response(user_message, conversation_id):
    """Get response from Azure OpenAI"""
    if not openai_client:
        logging.warning("OpenAI client not initialized")
        return f"Echo: {user_message}"
    
    try:
        logging.info(f"Sending to Azure OpenAI: {user_message}")
        
        # Build messages array with conversation history
        messages = [
            {"role": "system", "content": "Te egy barátságos Teams bot vagy. Válaszolj röviden és segítőkészen magyarul."}
        ]
        
        # Add conversation history
        history = get_conversation_history(conversation_id)
        messages.extend(history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_CHAT_DEPLOYMENT,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        ai_reply = response.choices[0].message.content
        logging.info(f"Azure OpenAI response: {ai_reply[:100]}...")
        
        # Save to history
        add_to_conversation_history(conversation_id, "user", user_message)
        add_to_conversation_history(conversation_id, "assistant", ai_reply)
        
        return ai_reply
        
    except Exception as e:
        logging.error(f"Azure OpenAI error: {e}")
        return f"Sajnálom, hiba történt az AI válasz generálása során"

def get_llama3_response(user_message, conversation_id):
    """Get response from Llama3 via Ollama API"""
    
    try:
        logging.info(f"Sending to Llama3: {user_message}")
        
        # Build messages array with conversation history
        messages = [
            {"role": "system", "content": "Te egy barátságos Teams bot vagy. Válaszolj röviden és segítőkészen magyarul."}
        ]
        
        # Add conversation history
        history = get_conversation_history(conversation_id)
        messages.extend(history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Call Ollama API
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
            logging.warning("Empty response from Llama3")
            return "Sajnálom, üres válasz érkezett az AI-tól"
        
        logging.info(f"Llama3 response: {ai_reply[:100]}...")
        
        # Save to history
        add_to_conversation_history(conversation_id, "user", user_message)
        add_to_conversation_history(conversation_id, "assistant", ai_reply)
        
        return ai_reply
        
    except requests.exceptions.Timeout:
        logging.error("Llama3 request timeout")
        return "Sajnálom, az AI szerver nem válaszol időben"
    except requests.exceptions.ConnectionError:
        logging.error(f"Cannot connect to Llama3 at {LLAMA3_API_URL}")
        return f"Sajnálom, nem tudom elérni az AI szervert ({LLAMA3_API_URL})"
    except Exception as e:
        logging.error(f"Llama3 error: {e}")
        return f"Sajnálom, hiba történt az AI válasz generálása során"

@app.route(route='messages', auth_level=func.AuthLevel.ANONYMOUS, methods=['POST'])
async def messages(req: func.HttpRequest) -> func.HttpResponse:
    """
    Bot Framework endpoint for Microsoft Teams
    Receives Bot Framework Activity objects and sends responses
    """
    logging.info('=== Bot message received from Teams ===')
    
    try:
        # Parse incoming Bot Framework Activity
        if "application/json" not in req.headers.get("Content-Type", ""):
            logging.warning('Invalid content type')
            return func.HttpResponse(status_code=415)
        
        body = req.get_json()
        activity_type = body.get("type", "")
        
        logging.info(f'Activity type: {activity_type}')
        
        # Handle message activities
        if activity_type == "message":
            user_message = body.get("text", "")
            conversation = body.get("conversation", {})
            conversation_id = conversation.get("id", "")
            from_user = body.get("from", {})
            service_url = body.get("serviceUrl", "")
            channel_data = body.get("channelData", {})
            
            # Extract user information
            user_id = from_user.get("id", "N/A")
            user_name = from_user.get("name", "Unknown")
            aad_object_id = from_user.get("aadObjectId", None)
            
            # Extract tenant and Teams-specific info
            tenant_id = channel_data.get("tenant", {}).get("id", None)
            teams_user_info = channel_data.get("teamsUser", {})
            user_principal_name = teams_user_info.get("userPrincipalName", None)
            teams_tenant_id = teams_user_info.get("tenantId", None)
            
            # Log all user information
            logging.info(f'User message: "{user_message}"')
            logging.info(f'User Name: {user_name}')
            logging.info(f'Teams User ID: {user_id}')
            logging.info(f'AAD Object ID: {aad_object_id}')
            logging.info(f'User Principal Name (UPN/Email): {user_principal_name}')
            logging.info(f'Tenant ID: {tenant_id or teams_tenant_id}')
            logging.info(f'Conversation ID: {conversation_id}')
            logging.info(f'Service URL: {service_url}')
            
            # Extract domain from UPN
            domain = None
            if user_principal_name and '@' in user_principal_name:
                domain = user_principal_name.split('@')[1]
                logging.info(f'User Domain: {domain}')
            
            # Check if user is from Grepton tenant
            grepton_tenant_id = "5363c28c-cdab-42ce-86c6-1b35f030504b"
            is_grepton_user = (tenant_id == grepton_tenant_id) or (teams_tenant_id == grepton_tenant_id)
            
            if is_grepton_user:
                logging.info("User is from Grepton domain")
            else:
                logging.info(f"User is from external tenant: {tenant_id or teams_tenant_id}")
            
            # Get response from AI provider
            bot_reply = get_ai_response(user_message, conversation_id)
            
            # Create Bot Framework response activity
            response_activity = {
                "type": "message",
                "text": bot_reply,
                "from": {
                    "id": APP_ID,
                    "name": "Fresh Bot"
                }
            }
            
            logging.info(f'Sending response: "{bot_reply}"')
            
            # Send response via Bot Framework REST API
            success = send_activity_to_conversation(service_url, conversation_id, response_activity)
            
            if success:
                logging.info("Response sent successfully via Bot Framework API")
            else:
                logging.error("Failed to send response via Bot Framework API")
            
            # Return 200 OK to acknowledge receipt
            return func.HttpResponse(status_code=200)
        
        # Handle conversationUpdate (bot added to chat)
        elif activity_type == "conversationUpdate":
            members_added = body.get("membersAdded", [])
            logging.info(f'Conversation update - Members added: {len(members_added)}')
            
            # Check if bot was added
            for member in members_added:
                if member.get("id") == APP_ID:
                    logging.info('Bot was added to conversation - sending welcome message')
                    
                    welcome_message = "Szia! Én vagyok a Fresh Bot! 👋 Írj bármit és visszhangozom!"
                    
                    response_activity = {
                        "type": "message",
                        "text": welcome_message,
                        "from": {"id": APP_ID, "name": "Fresh Bot"},
                        "conversation": body.get("conversation", {}),
                        "serviceUrl": body.get("serviceUrl", "")
                    }
                    
                    return func.HttpResponse(
                        json.dumps(response_activity),
                        status_code=200,
                        mimetype="application/json"
                    )
            
            return func.HttpResponse(status_code=200)
        
        # Handle other activity types
        else:
            logging.info(f'Unhandled activity type: {activity_type}')
            return func.HttpResponse(status_code=200)
    
    except Exception as e:
        logging.error(f'Error processing Teams message: {str(e)}', exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route='chat', auth_level=func.AuthLevel.ANONYMOUS, methods=['POST'])
def chat(req: func.HttpRequest) -> func.HttpResponse:
    """Legacy chat API - for direct HTTP testing"""

    logging.info('Chat request received')

    try:
        req_body = req.get_json()
        user_message = req_body.get('message', '')

        logging.info(f'User message: {user_message}')

        # Get response from AI
        bot_reply = get_ai_response(user_message, "test-conversation")

        response_data = {
            'success': True,
            'message': user_message,
            'reply': bot_reply,
            'timestamp': str(__import__('datetime').datetime.now())
        }

        return func.HttpResponse(
            json.dumps(response_data),
            status_code=200,
            mimetype='application/json'
        )

    except ValueError as e:
        return func.HttpResponse(
            json.dumps({'error': 'Invalid JSON', 'details': str(e)}),
            status_code=400
        )
    except Exception as e:
        logging.error(f'Error: {str(e)}')
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500
        )

@app.route(route='health', auth_level=func.AuthLevel.ANONYMOUS, methods=['GET'])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    return func.HttpResponse(
        json.dumps({'status': 'healthy', 'service': 'Fresh Teams Bot', 'llm_provider': LLM_PROVIDER}),
        status_code=200,
        mimetype='application/json'
    )
