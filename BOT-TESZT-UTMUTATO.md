# Teams Bot Tesztelés - Lokális Fejlesztés

## ✅ Jelenlegi Állapot

- ✅ Bot sikeresen feltöltve Teams-be
- ✅ Azure Functions fut lokálisan: `http://localhost:7071`
- ✅ Bot endpoint elérhető: `http://localhost:7071/api/messages`
- ⏳ **Következő lépés**: Public URL létrehozása és Bot Service frissítése

## 🔧 Lépés 1: Public Tunnel Létrehozása

### Módszer A: VS Code Port Forwarding (Legegyszerűbb)

1. **Nyisd meg a PORTS panel-t**:
   - `View` → `Terminal`
   - Alsó panel: **PORTS** tab
   - Vagy: `Ctrl+Shift+P` → "Forward a Port"

2. **Add hozzá a port-ot**:
   - Kattints: **Forward a Port**
   - Írd be: `7071`
   - Enter

3. **Állítsd Public-ra**:
   - Jobb klikk a port-on
   - **Port Visibility** → **Public**

4. **Másold ki az URL-t**:
   - Valami ilyesmi lesz: `https://xyz123-7071.use-azp.devtunnels.ms`
   - **Mentsd el ezt az URL-t!**

### Módszer B: Azure Dev Tunnel (Parancssori)

```powershell
# Telepítés (ha nincs még)
winget install Microsoft.devtunnel

# Bejelentkezés
devtunnel user login

# Tunnel létrehozása
devtunnel create --allow-anonymous

# Tunnel indítása
devtunnel port create 7071 --port-number 7071 --protocol https

# URL kiírása
devtunnel show
```

## 🔄 Lépés 2: Bot Service Endpoint Frissítése

Miután megvan a public URL (pl. `https://xyz123-7071.use-azp.devtunnels.ms`):

### Parancssorból (Azure CLI):

```powershell
# Helyettesítsd be a te tunnel URL-edet!
$TUNNEL_URL = "https://xyz123-7071.use-azp.devtunnels.ms"

az bot update `
  --name fresh-teams-bot `
  --resource-group AgreementDemo `
  --endpoint "$TUNNEL_URL/api/messages"
```

### Azure Portal-ból:

1. Nyisd meg: https://portal.azure.com
2. Keress rá: `fresh-teams-bot`
3. Menj: **Configuration** (bal oldali menü)
4. **Messaging endpoint**: 
   - Régi: `https://fresh-teams-bot-func.azurewebsites.net/api/chat`
   - Új: `https://xyz123-7071.use-azp.devtunnels.ms/api/messages`
5. **Save**

## 🧪 Lépés 3: Tesztelés

1. **Nyisd meg a Teams-et**
2. Kattints a **Fresh Bot**-ra a bal oldali menüben
3. Írj egy üzenetet: `"Hello"`
4. **Várd meg a választ!** 

Sikeres válasz:
```
Echo: Hello (Szia! Ez a Fresh Teams Bot!)
```

## 📊 Monitoring és Debug

### Functions Logs Nézése:

A Functions terminal-ban láthatod a beérkező kéréseket:
```
[INFO] Received message from Teams: Hello
[INFO] Sending reply: Echo: Hello (Szia! Ez a Fresh Teams Bot!)
```

### Bot Service Logs (Azure Portal):

1. Azure Portal → `fresh-teams-bot`
2. **Monitoring** → **Logs**
3. Nézd a beérkező kéréseket és válaszokat

### VS Code Debug:

Ha hibát látsz:
- Nézd meg a Functions terminal output-ját
- Ellenőrizd hogy a port forwarding aktív-e
- Teszteld a URL-t böngészőből: `https://your-tunnel.devtunnels.ms/api/health`

## ⚠️ Gyakori Problémák

### "A bot nem válaszol"

**Ellenőrzés**:
1. Functions fut? → Terminálban látszik: "Host lock lease acquired"
2. Port forwarding aktív? → PORTS panelben látszik a 7071
3. Bot Service endpoint frissítve? → Azure Portal: Configuration

### "401 Unauthorized"

**Megoldás**: App Password hibás
- Ellenőrizd a `.env` és `local.settings.json` fájlokban
- App Password helyesen kell beállítani

### "Functions hiba"

**Megoldás**: Python csomagok hiányoznak
```powershell
pip install botbuilder-core botbuilder-schema python-dotenv
```

## 🚀 Éles Deployment (Később)

Amikor készen állsz éles használatra:

1. **Deploy to Azure Functions**:
   ```powershell
   func azure functionapp publish fresh-teams-bot-func
   ```

2. **Bot Service endpoint visszaállítása**:
   ```
   https://fresh-teams-bot-func.azurewebsites.net/api/messages
   ```

3. **Environment változók beállítása** az Azure Functions-ben

## 📝 Hasznos Parancsok

```powershell
# Functions újraindítása
Get-Process -Name func | Stop-Process -Force
func start --port 7071

# Functions státusz
Get-Process -Name func

# Bot Service info
az bot show --name fresh-teams-bot --resource-group AgreementDemo

# Endpoint ellenőrzése
az bot show --name fresh-teams-bot --resource-group AgreementDemo --query "properties.endpoint"
```

## 🆘 Segítség

Ha bármi nem működik:
1. Ellenőrizd a Functions logs-ot
2. Teszteld a `/api/health` endpoint-ot
3. Nézd meg a Bot Service logs-ot Azure Portal-on
4. Ellenőrizd hogy a MicrosoftAppId és MicrosoftAppPassword helyesek
