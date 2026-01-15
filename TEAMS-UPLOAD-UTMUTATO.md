# Teams Bot Feltöltési Útmutató

## ✅ Elkészült: fresh-teams-bot.zip

A ZIP fájl helyes struktúrájú:
```
fresh-teams-bot.zip
├── manifest.json
├── color.png (192x192)
└── outline.png (32x32)
```

## 📋 Lépések a feltöltéshez

### 1. Custom App Upload Engedélyezése (Admin szükséges)

**Ha Te vagy a Teams admin**, ellenőrizd:

1. Nyisd meg: https://admin.teams.microsoft.com
2. Menj: **Teams apps** → **Setup policies**
3. Kattints a **Global (Org-wide default)** policy-ra
4. Ellenőrizd hogy **"Upload custom apps"** = **ON**
5. Ha módosítottad, várj 1-2 órát a változások érvényesüléséig

**Alternatíva**: Kérj hozzáférést a Teams admin-tól

### 2. Bot Feltöltése Teams-be

#### Módszer A: Microsoft Teams Admin Center (Javasolt)
1. Nyisd meg: https://admin.teams.microsoft.com
2. Menj: **Teams apps** → **Manage apps**
3. Kattints: **Upload** (jobb felső sarok)
4. Válaszd ki: `fresh-teams-bot.zip`
5. Kattints: **Upload**

#### Módszer B: Teams Alkalmazás (Végfelhasználói)
1. Nyisd meg a **Microsoft Teams** alkalmazást
2. Bal oldali menü: **Apps** (vagy **Alkalmazások**)
3. Jobb alsó sarok: **Manage your apps** (vagy **Alkalmazások kezelése**)
4. Jobb felső sarok: **Upload a custom app** (vagy **Egyéni alkalmazás feltöltése**)
5. Válaszd ki: `fresh-teams-bot.zip`
6. Kattints: **Add** vagy **Hozzáadás**

#### Módszer C: Developer Portal (Fejlesztői)
1. Nyisd meg: https://dev.teams.microsoft.com/apps
2. Kattints: **Import app**
3. Válaszd ki: `fresh-teams-bot.zip`
4. A betöltés után: **Preview in Teams**

## ⚠️ Lehetséges Hibák és Megoldások

### "Nem sikerült feltölteni az alkalmazást"

**1. Custom app upload nincs engedélyezve**
- **Megoldás**: Lásd "1. Custom App Upload Engedélyezése" fenti
- **Vagy**: Kérj segítséget a Teams admin-tól

**2. Manifest érvényesítési hiba**
- **Ellenőrizd**: Bot App ID helyes-e: `19c6dc8f-ba5d-4f10-8df2-af473d5515f0`
- **Ellenőrizd**: Icon fájlok léteznek és megfelelő méretűek
- **Tipp**: Használd a Developer Portal-t validáláshoz

**3. ZIP struktúra hibás**
- **Probléma**: A fájlok almappában vannak
- **Megoldás**: Futtasd újra a ZIP létrehozó parancsot

**4. Bot Service nem elérhető**
- **Ellenőrizd**: Bot Service fut-e az Azure-ban
- **URL**: https://portal.azure.com → fresh-teams-bot
- **Endpoint**: Messaging endpoint beállítva kell legyen

## 🔍 Bot Konfiguráció Ellenőrzése

### Azure Bot Service Beállítások
```
Resource Group: AgreementDemo
Bot Name: fresh-teams-bot
App ID: 19c6dc8f-ba5d-4f10-8df2-af473d5515f0
Tenant ID: 5363c28c-cdab-42ce-86c6-1b35f030504b
Messaging Endpoint: https://fresh-teams-bot-func.azurewebsites.net/api/messages
```

### Ellenőrzési Lépések
1. Azure Portal: https://portal.azure.com
2. Keress rá: `fresh-teams-bot`
3. Menj: **Channels** → Ellenőrizd **Microsoft Teams** channel aktív
4. Menj: **Configuration** → Ellenőrizd **Messaging endpoint** helyesen van beállítva

## 📝 Manifest Adatok

**App ID**: `64b3a3a2-548a-43b1-9d83-d989ac60e4c6`  
**Bot ID**: `19c6dc8f-ba5d-4f10-8df2-af473d5515f0`  
**Version**: `1.0.0`  
**Manifest Version**: `1.19`

## 🚀 Következő Lépések (Feltöltés után)

1. **Tesztelés**:
   - Nyisd meg a bot-ot Teams-ben
   - Küldj egy üzenetet: "Hello"
   - Várd meg a választ

2. **Endpoint Frissítés** (Ha lokális teszteléshez):
   - Bot Service endpoint: Módosítsd lokális URL-re
   - Példa: `https://YOUR-NGROK-URL.ngrok-free.app/api/messages`

3. **Deployment** (Éles használathoz):
   - Deploy function_app.py → Azure Functions
   - Frissítsd Bot Service endpoint → Azure Functions URL

## 📚 Hasznos Linkek

- **Teams Admin Center**: https://admin.teams.microsoft.com
- **Developer Portal**: https://dev.teams.microsoft.com
- **Azure Portal**: https://portal.azure.com
- **Bot Registration**: https://dev.botframework.com/bots

## 🆘 Segítség Kérése

Ha továbbra sem működik:
1. Próbáld meg a **Developer Portal**-on keresztül feltölteni
2. Ellenőrizd a **manifest.json** validációját itt: https://dev.teams.microsoft.com/validation
3. Nézd meg a Bot Service **logs**-okat az Azure Portal-on
4. Kérd meg a Teams admin-t, hogy ellenőrizze a **tenant policies**-t
