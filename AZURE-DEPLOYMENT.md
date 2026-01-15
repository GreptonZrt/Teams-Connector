# Azure Functions - Bot Framework Adapter Deployment

## Probléma
Az Azure-ban lévő `fresh-teams-bot-func` Functions app még a régi HTTP trigger kódot futtatja, nem a Bot Framework compatible verziót.

## Megoldás Opciók

### Opció 1: Azure Portal Code Editor (Legegyszerűbb)

1. **Nyisd meg**: https://portal.azure.com
2. **Keress rá**: `fresh-teams-bot-func`
3. **Menj**: **Functions** → **chat** function
4. **Code + Test** (bal menü)
5. **Cseréld le** a `__init__.py` vagy `function_app.py` tartalmát az alábbi Bot Framework compatible kódra:

```python
import azure.functions as func
import json
import logging
import os
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext
from botbuilder.schema import Activity

# Bot Framework Adapter Settings
APP_ID = os.environ.get("MicrosoftAppId", "")
APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)

async def on_message_activity(turn_context: TurnContext):
    """Handle incoming messages from Teams"""
    user_message = turn_context.activity.text
    logging.info(f'Received message from Teams: {user_message}')
    
    # Echo bot logic
    reply = f'Echo: {user_message} (Szia! Ez a Fresh Teams Bot!)'
    await turn_context.send_activity(reply)

async def main(req: func.HttpRequest) -> func.HttpResponse:
    """Bot Framework messages endpoint for Teams"""
    
    logging.info('Bot message received from Teams')
    
    if "application/json" in req.headers.get("Content-Type", ""):
        body = req.get_json()
    else:
        return func.HttpResponse(status_code=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    try:
        response = await ADAPTER.process_activity(activity, auth_header, on_message_activity)
        if response:
            return func.HttpResponse(json.dumps(response.body), status_code=response.status)
        return func.HttpResponse(status_code=201)
    except Exception as e:
        logging.error(f'Error processing activity: {str(e)}')
        return func.HttpResponse(json.dumps({'error': str(e)}), status_code=500)
```

6. **Save**
7. **Restart** the function app

### Opció 2: Új Function Létrehozása (messages)

1. Azure Portal → `fresh-teams-bot-func`
2. **Functions** → **Create**
3. **Template**: HTTP trigger
4. **Name**: `messages`
5. **Authorization level**: Anonymous
6. Másold be a fenti Bot Framework kódot

### Opció 3: Environment Variables Beállítása

Az Azure Functions-nek szüksége van a Bot credentials-ekre:

1. Azure Portal → `fresh-teams-bot-func`
2. **Configuration** (bal menü)
3. **Application settings** → **New application setting**
4. Adj hozzá:
   - `MicrosoftAppId` = [a te Bot App ID-d]
   - `MicrosoftAppPassword` = [a te Bot App Password-d]
5. **Save** → **Restart**

### Opció 4: Requirements.txt Frissítése

Az Azure Functions-nek szüksége van a Bot Framework csomagokra:

1. Azure Portal → `fresh-teams-bot-func`
2. **App Files** (felső menü)
3. Select: `requirements.txt`
4. Add hozzá:
```
botbuilder-core>=4.14.0
botbuilder-schema>=4.14.0
```
5. **Save**
6. **Restart** the app

## Bot Service Endpoint Frissítése

Miután az Azure Functions kész:

```powershell
# Ha új "messages" function-t hoztál létre:
az bot update --name fresh-teams-bot --resource-group AgreementDemo --endpoint "https://fresh-teams-bot-func.azurewebsites.net/api/messages"

# Ha a "chat" function-t módosítottad:
az bot update --name fresh-teams-bot --resource-group AgreementDemo --endpoint "https://fresh-teams-bot-func.azurewebsites.net/api/chat"
```

Vagy Azure Portal-ból:
1. https://portal.azure.com → `fresh-teams-bot`
2. **Configuration** → **Messaging endpoint**
3. Set: `https://fresh-teams-bot-func.azurewebsites.net/api/messages`
4. **Save**

## Tesztelés

1. Nyisd meg Teams-et
2. Írj a Fresh Bot-nak
3. Várd meg a választ!

## Debug

Ha nem működik:
1. Azure Portal → `fresh-teams-bot-func`
2. **Monitor** → **Logs**
3. Nézd meg a hibákat
