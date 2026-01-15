# Disclaimer

Ez a dokumentáció egy laikus megközelítés a Teams Bot Framework-höz. Bár igyekeztem legjobb tudásom szerint összeszedni és rendszerezni az összes szükséges lépést és koncepciót, ez a guide nem egy hivatalos Microsoft dokumentáció, szóval úgy kezeljétek. 

**Javasolt forrás:** A Microsoft hivatalos dokumentációja az alábbi linkeken: https://learn.microsoft.com/en-us/azure/bot-service/ és https://learn.microsoft.com/en-us/microsoftteams/platform/

---

#  Pro Tip: VS Code Azure Tools

Nem kell az Azure webes labirintusában böngészni, VS Code-ban vannak beépített Azure bővítmények, amelyek segítségével a terminálból lehet konfigurálni mindent.

## Ajánlott Extensions

1. **Azure Tools** - Alap Azure integráció
2. **Azure Resources** - Azure erőforrások kezelése
3. **Azure Developer CLI** - `azd` CLI eszköz projektek inicializálásához és deploymentjéhez
4. **Azure Functions** - Azure Functions deployment és management


# Teams Bot – komponensek

1. Teams
Teams kliens és Teams cloud service.

2. Azure Bot Service (Bot Channels Registration)
Bot resource Azure-ban. Messaging endpoint + Teams channel beállítása.

3. Microsoft Entra App Registration
Bot identitása. App ID, secret, OAuth2.

4. Azure Functions (Python)
Bot backend. POST /api/messages endpoint.

5. Bot Framework Activity
JSON formátum Teams és bot között.

6. Connector API
REST: POST {serviceUrl}v3/conversations/{conversationId}/activities

7. Bearer Token (OAuth2)
Token a Connector API hívásokhoz.

8. Dev Tunnel
Lokál backend publikus HTTPS URL-ként.

9. Teams App Manifest
Bot app definíció (JSON + ZIP).

Lépések:

1. Entra App Registration
   1.1. Azure Portal -> Microsoft Entra ID -> App registrations -> New registration
   1.2. Name: "My Bot"
   1.3. Supported account types: "Accounts in this organizational directory only"
   1.4. Register
   1.5. Certificates & secrets -> New client secret
   1.6. Description: "Bot token", Expires: 24 months
   1.7. Add
   1.8. Másold: Client ID, Client secret value, Directory ID (Tenant ID)
   1.9. Ezek az értékek: MicrosoftAppId, MicrosoftAppPassword, MicrosoftAppTenantId

2. Bot Channels Registration
   2.1. Azure Portal -> Create a resource
   2.2. Keresés: "Bot Channels Registration"
   2.3. Create
   2.4. Resource group: válassz vagy újat
   2.5. Bot handle: pl. "my-bot"
   2.6. Pricing tier: "Free"
   2.7. Create
   2.8. Kész: Bot resource URL-je
   2.9. App ID beállítása: az Entra-ból másolt Client ID

3. Dev Tunnel
   3.1. VS Code: Terminal -> New Terminal
   3.2. devtunnel create --allow-anonymous
   3.3. Másold: tunnel ID és URL
   3.4. devtunnel host
   3.5. A lokál port 7071 -> publikus HTTPS URL

4. Bot Messaging Endpoint
   4.1. Azure Portal -> Bot resource
   4.2. Configuration
   4.3. Messaging endpoint: {backend-host-url}/api/messages
   4.4. Save
   4.5. Messaging endpoint template: https://{backend-host}/api/messages

5. Local Settings
   5.1. local.settings.json -> Values
   5.2. MicrosoftAppId: Entra Client ID
   5.3. MicrosoftAppPassword: Entra Client secret
   5.4. MicrosoftAppTenantId: Entra Tenant ID
   5.5. Mentsd el

6. Azure Functions Handler
    6.1. function_app.py szerkesztése
        - Nyisd meg a `function_app.py` fájlt
        - Definiáld a route-ot: `@app.route(route="messages", methods=["POST"])`
        - Ez kezeli a `/api/messages` endpoint-ot
    
    6.2. Activity fogadása Teams-ből
        - A Teams minden interakcióra (üzenet, esemény) Activity JSON-t küld
        - Deserializáld a request body-t Activity objektummá
        - Példa Activity típusok:
          - `message`: felhasználó üzenete
          - `conversationUpdate`: bot hozzáadva/eltávolítva
          - `invoke`: interaktív kártya akció
    
    6.3. OAuth2 Bearer Token kérése
        - Endpoint: `https://login.microsoftonline.com/botframework.com/oauth2/v2.0/token`
        - Method: POST
        - Body (x-www-form-urlencoded):
          - `grant_type=client_credentials`
          - `client_id={MicrosoftAppId}`
          - `client_secret={MicrosoftAppPassword}`
          - `scope=https://api.botframework.com/.default`
        - Response: `access_token` (Bearer token)
        - Fontos: Cache-eld a tokent, 1 óráig érvényes
    
    6.4. Válasz küldése a Connector API-val
        - URL: `{activity.serviceUrl}/v3/conversations/{activity.conversation.id}/activities`
        - Method: POST
        - Headers:
          - `Authorization: Bearer {access_token}`
          - `Content-Type: application/json`
        - Body: új Activity JSON
          - `type: "message"`
          - `text: "Bot válasz szövege"`
          - `replyToId: {activity.id}` (ha válasz egy üzenetre)
    
    6.5. Activity feldolgozási folyamat
        - Fogadd be a POST request-et
        - Validáld az Activity-t (Bot Framework auth middleware)
        - Szerezz Bearer tokent (OAuth2 client_credentials)
        - Készítsd el a válasz Activity-t
        - Küld el a Connector API-nak
        - Return HTTP 200 OK a Teams felé
    
    6.6. Hibakezelés
        - 401 Unauthorized: ellenőrizd az App ID és secret-et
        - 429 Too Many Requests: retry-after logika
        - 500 Server Error: logold a diagnostics adatokat
        - Mindig return 200-at a Teams-nek, különben újrapróbálkozik

7. Teams App Manifest
    7.1. Manifest struktúra
          - Szükséges fájlok (mind a gyökérben):
             - `manifest.json` (bot definíció)
             - `color.png` (192x192 px, teljes színes ikon)
             - `outline.png` (32x32 px, áttetsző háttér, fehér kontúr)
    
    7.2. manifest.json alapbeállítások
          - `$schema`: Teams manifest schema URL
          - `manifestVersion`: "1.16" vagy újabb
          - `version`: Az app verziója (pl. "1.0.0")
          - `id`: **Entra App Registration Client ID** (UUID formátum)
          - `packageName`: Egyedi azonosító (pl. "com.company.mybot")
          - `developer`: name, websiteUrl, privacyUrl, termsOfUseUrl
    
    7.3. Bot konfiguráció
          - `bots` tömb:
             - `botId`: **Entra App Registration Client ID** (ugyanaz mint `id`)
             - `scopes`: `["personal", "team", "groupchat"]` (ahol használható)
             - `supportsFiles`: false (vagy true ha fájlkezelés kell)
             - `isNotificationOnly`: false
             - `commandLists`: bot parancsok listája (opcionális)
    
    7.4. Valid Domains beállítása
          - `validDomains` tömb:
             - Add hozzá a **dev tunnel domain-t** (pl. `"abc123.devtunnels.ms"`)
             - Add hozzá: `"token.botframework.com"` (OAuth flow-hoz)
             - Ne add hozzá a teljes URL-t, csak a domain nevet
             - Példa: `["abc123.devtunnels.ms", "token.botframework.com"]`
    
    7.5. Ikonok előkészítése
              - `color.png`: 192x192 px, teljes színes, PNG formátum
              - `outline.png`: 32x32 px, áttetsző háttér, fehér/világos kontúr
              - `icons` objektum a manifest-ben:
                 - `color`: "color.png"
                 - `outline`: "outline.png"
              - A Teams manifest validáció megköveteli mindkét ikont, különben a manifest érvénytelen lesz és az app nem telepíthető. Az ikonok jelennek meg a Teams app galériában és a bot profilképeként.
    
    7.6. Mentés és ellenőrzés
          - Mentsd el a `manifest.json` fájlt
          - Győződj meg róla, hogy mind a 3 fájl (`manifest.json`, `color.png`, `outline.png`) gyökérkönyvtárában van és ezekből készítsünk egy zip-et. 
          - Ez a zip kerül majd feltöltésre.

8. Teams App Upload
   8.1. teams-app-package/ könyvtár
   8.2. manifest.json + 192x192.png + 32x32.png
   8.3. ZIP: manifest.json + ikonok 
   8.4. Teams: Apps -> Upload custom app -> ZIP fájl
   8.5. Install bot saját Teams-be




Bot Framework kommunikációs sablon vs. hagyományos HTTP

Alapvetően fontos megjegyezni: A Teams Bot Framework nem egyszerű HTTP kommunikáció. A Bot Framework egy protokoll és szabványosított kommunikációs sablon, amely alapvetően eltér a hagyományos REST API-któl.


1. Activity szerkezet kötelezően szükséges
   - A Teams nem tetszőleges JSON-t küld, hanem strukturált Activity objektumot
   - Az Activity-nek mindig meg kell felelnie a Bot Framework Activity schema-nak
   - Egyetlen egy helytelen mező, és a kommunikáció lebomlik

2. OAuth2 Bearer Token szükséges minden válaszhoz
   - A Connector API-val való kommunikáció mindössze Bearer tokent fogad
   - Nem működik az alapvető HTTP authentication vagy API key
   - A tokent dinamikusan ki kell szerezni OAuth2 client_credentials flow-val

3. Connector API alapú válaszküldés
   - A bot nem közvetlenül az eredeti HTTP válaszra küld vissza üzenetet
   - Helyette új HTTP POST kéréssel kell meghívni a Connector API-t
   - Az URL az Activity `serviceUrl` objektumból származik
   - Ez aszinkron kommunikációt jelent:
        1. Teams → Bot: POST request (Activity JSON)
        2. Bot → Teams: HTTP 200 OK válasz (azonnal, üres body-val)
        3. Bot → Connector API: POST request (új Activity JSON a válasszal)
        4. Connector API → Teams: Ez az üzenet jelenik meg a felhasználónál
      - A bot minden esetben 200 OK-t ad vissza a Teams-nek (2. lépés), még ha később hibázik is a Connector API hívás (3. lépés)
      - A válasz Activity-ben fontos a `replyToId` mező, hogy a Teams összekapcsolja az eredeti üzenettel

4. Activity típusok és kontextus
   - Nem minden Teams interakció "üzenet" típusú Activity
   - `conversationUpdate`: bot hozzáadva/eltávolítva
   - `invoke`: interaktív kártya gomb kattintás
   - `message`: sima üzenet
   - Mindegyikre másképp kell reagálni

5. Válaszazonosítás és konverzáció követés
   - A `replyToId` mező nélkül a válaszok nem kapcsolódnak az eredeti üzenethez
   - A `conversationId` és `threadId` mezők nélkül elvész a kontextus
   - A Connector API-val küldött válasz után a Bot Framework biztosítja az üzenetek összekapcsolódását

Lényeg

A Teams Bot Framework egy Microsoft által definiált, zárt protokoll. Ha az Activity XML sémáját, az OAuth2 flow-t vagy a Connector API-t kihagyjuk, a bot nem fog működni. Egy hagyományos webszerver ezekkel a szabványokkal nem tud kommunikálni.


Minimális Setup Lokális Hosting-hoz

- **function_app.py** - Bot endpoint-ok + messaging logika
- **local.settings.json** vagy **.env** - Credentials & config (MicrosoftAppId, MicrosoftAppPassword, Azure OpenAI paraméterek)
- **host.json** - Azure Functions runtime config (extensionBundle, logging)
- **requirements.txt** - Python dependencies (azure-functions, requests, openai)
- **.venv/** - Virtual environment

Futtatás:
```powershell
func start
```

Hasznos források:
Bot Framework SDK:
https://learn.microsoft.com/en-us/azure/bot-service/bot-service-overview?view=azure-bot-service-4.0

Developer Portal for Teams:
https://learn.microsoft.com/en-us/microsoftteams/platform/concepts/build-and-test/teams-developer-portal

App setup and install:
https://learn.microsoft.com/hu-hu/microsoftteams/teams-app-setup-policies#use-app-setup-policy-to-allow-independent-bots

Referencia kódok és setup-ok:
https://github.com/OfficeDev/Microsoft-Teams-Samples/tree/main