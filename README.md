# Azure Bot Framework - Python Backend
Teams-hez integrált Azure Bot

## Projekt Szerkezete

```
Fresh_Teams_Connector/
├── app.py              # Flask/aiohttp alkalmazás
├── bot.py              # Bot logika
├── config.py           # Konfiguráció
├── requirements.txt    # Python függőségek
├── .env                # Környezeti változók (titkos adatok)
├── .gitignore          # Git figyelmen kívül hagyott fájlok
├── web.config          # Azure App Service konfiguráció
└── README.md           # Ez a fájl
```

## Telepítés (Lokális fejlesztéshez)

### 1. Python környezet beállítása

```bash
# Virtual environment létrehozása
python -m venv venv

# Aktiválás (Windows)
venv\Scripts\activate

# Aktiválás (Linux/Mac)
source venv/bin/activate
```

### 2. Függőségek telepítése

```bash
pip install -r requirements.txt
```

### 3. Azure Bot adatai

- Nyisd meg a `.env` fájlt
- Töltsd ki a `MicrosoftAppId` és `MicrosoftAppPassword` értékeket
- Az értékeket az Azure Portal Bot Settings oldaláról kapod meg

### 4. Bot elindítása (lokálisan)

```bash
python app.py
```

A bot a `http://localhost:3978/api/messages` címen fog futni.

## Azure Deployment Lépésről Lépésre

### Lépés 1: Azure Bot Regisztrálása

1. Nyisd meg az [Azure Portal](https://portal.azure.com)
2. Kattints a **+ Create a resource** gombra
3. Keress az **"Azure Bot"** kifejezésre
4. Kattints **Create**

#### Töltsd ki az alábbi adatokat:

- **Bot handle**: pl. `fresh-teams-bot` (egyedi név)
- **Subscription**: válassz ki egy subscription-t
- **Resource Group**: létrehozd az újat: `fresh-teams-rg`
- **Pricing tier**: `F0` (ingyenes) vagy `S1` (production)
- **App Service plan**: automatikus (hagyj meg)

5. Kattints **Create** és várj, amíg elkészül (2-3 perc)

### Lépés 2: Microsoft App ID és Jelszó Lekérése

1. Az Azure Portal-on nyisd meg az imént létrehozott **Azure Bot** resource-ot
2. Bal oldali menüben kattints: **Configuration**
3. Jegyezd fel az **App ID**-t (ez a `MicrosoftAppId`)
4. Kattints **Manage** a jelszó mellett
5. Kattints **+ New client secret**
6. **Description**: pl. `Teams Bot Secret`
7. **Expires**: `Never`
8. Kattints **Add**
9. **Másold le az értéket** és mentsd el biztonságosan! (később nem látod meg)

### Lépés 3: Azure App Service Létrehozása (a bot hostingához)

1. Az Azure Portal-on kattints **+ Create a resource**
2. Keress: **"App Service"**
3. Kattints **Create**

#### Töltsd ki:

- **Resource Group**: válaszd ki az előzőt: `fresh-teams-rg`
- **Name**: pl. `fresh-teams-app` (egyedi, ezt az Azure ellenőrzi)
- **Runtime stack**: `Python 3.11` vagy `3.10`
- **Operating System**: `Linux`
- **Region**: válaszd azt, amely közel van hozzád
- **App Service Plan**: `Free F1` vagy `Basic B1`

4. Kattints **Review + create**
5. Kattints **Create** és várj (2-3 perc)

### Lépés 4: Messaging Endpoint Beállítása

1. Nyisd meg az Azure Bot resource-ot
2. Bal oldali menüben: **Configuration**
3. **Messaging endpoint**: 
   - Formátum: `https://<your-app-name>.azurewebsites.net/api/messages`
   - Helyettesítsd be: `<your-app-name>` az App Service nevével (pl. `fresh-teams-app`)
4. Kattints **Apply**

### Lépés 5: Kód Deploy-olása az Azure App Service-re

#### Opció A: Git Deployment (ajánlott)

1. Az App Service-ben: **Deployment Center** > **Source**: `Local Git`
2. Kattints **Save**
3. Lekérsz egy Git URL-t, megjegyzezd

```bash
# Nyisd meg a parancssorban a projekt mappáját és:
git init
git add .
git commit -m "Initial commit"
git remote add azure <git-url-from-azure>
git push azure master
```

#### Opció B: ZIP Deploy

1. Hozz létre egy ZIP fájlt a projekt fájljaiból
2. Az App Service-ben: **Deployment Center** > Upload a ZIP file
3. Válaszd ki a ZIP-et és deploy-old

#### Opció C: VS Code Azure Tools (legegyszerűbb)

1. Telepítsd a VS Code-ba: **Azure App Service** extension
2. Nyisd meg a VS Code parancspalettáját (Ctrl+Shift+P)
3. Írj: `Azure App Service: Deploy to Web App`
4. Válaszd ki a mappádat és az App Service-ed
5. Végez a deployment

### Lépés 6: Teams Channel Engedélyezése

1. Az Azure Bot resource-ban: **Channels**
2. Keress: **Microsoft Teams**
3. Kattints **Configure**
4. Fogadd el a feltételeket
5. Kattints **Apply**

### Lépés 7: Bot Hozzáadása Teams-hez

1. Nyisd meg a [Teams Developer Portal](https://dev.teams.microsoft.com/apps)
2. Kattints **+ New app**
3. **App name**: pl. `Fresh Teams Bot`
4. **Configure**: `Bots` szekció
5. Kattints **+ Create new bot**
6. **Bot name**: `Fresh Teams Bot`
7. **Owner ID**: (meghagyhatod üresen)
8. **Scopes**: pipáld be: `personal`, `team`, `groupChat`
9. Kattints **Create bot**

#### Bot App ID:
1. Kopírozd az **App ID**-t az Azure Bot resource-ből
2. Illeszd be ide

10. **Messages**: töltsd ki az **Messaging endpoint URL**-t:
    ```
    https://<your-app-name>.azurewebsites.net/api/messages
    ```

11. Kattints **Save**
12. Kattints **Download app package** (ZIP fájl)

### Lépés 8: Bot Hozzáadása a Teams-hez

1. Nyisd meg a Microsoft Teams asztali alkalmazást
2. **Apps** > **Manage your apps**
3. Kattints **Upload a custom app**
4. Válaszd ki a letöltött ZIP fájlt
5. A bot megjelenik az alkalmazások között
6. Kattints a bot-on > **Add**

### Lépés 9: Tesztelés

1. Nyisd meg az Azure Bot-ban a **Test in Web Chat** opciót
2. Írj egy üzenetet, pl. "Szia!"
3. A bot válaszolni fog: "Szia! 👋 Ezt a botot Azure-on futtatjuk, és Teams-ben elérhető lesz."

## Hibaelhárítás

### Az Application Insights naplók megtekintése:
1. Azure Portal > App Service > **Log Stream**
2. Itt láthatod az összes hiba és debug üzeneteket

### Messaging Endpoint nem működik:
1. Ellenőrizd, hogy a **Deploy status** `Success`
2. Ellenőrizd az URL-t: `https://<app-name>.azurewebsites.net/api/messages`
3. Nézd meg az App Service logs-ot

### Bot nem válaszol Teams-ben:
1. Ellenőrizd az Azure Bot > **Channels** > Teams beállításait
2. Nézd meg az Application Insights naplókat
3. Tesztelj az "Test in Web Chat" opcióval

## Következő Lépések

- RAG (Retrieval-Augmented Generation) logika integrálása
- Valódi AI model csatlakoztatása
- Hibakezelés és logging fejlesztése
- Authentikáció és engedélyek beállítása
