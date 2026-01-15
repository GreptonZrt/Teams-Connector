# Lokális Fejlesztés - Azure Bot Service

## 1. VS Code Port Forwarding (Legegyszerűbb)

1. Indítsd el a Functions-t: `func start`
2. VS Code-ban nyisd meg a **PORTS** tabot (Terminal panel mellett)
3. Kattints a **Forward a Port** gombra
4. Add meg: `7071`
5. Jobb klikk a port-ra → **Port Visibility** → **Public**
6. Másold ki a generált HTTPS URL-t (pl: `https://xxxxx.devtunnels.ms`)
7. Azure Bot Configuration → Messaging endpoint:
   ```
   https://xxxxx.devtunnels.ms/api/chat
   ```

## 2. Alternatíva: ngrok

Ha nincs VS Code port forwarding:

```powershell
# Telepítsd az ngrok-ot: https://ngrok.com/download
ngrok http 7071
```

Ez ad egy HTTPS URL-t, pl: `https://abc123.ngrok.io`

Azure Bot Configuration-ba:
```
https://abc123.ngrok.io/api/chat
```

## 3. Azure Dev Tunnels (Microsoft megoldás)

```powershell
# Telepítés (ha nincs még)
winget install Microsoft.DevTunnels

# Tunnel létrehozása
devtunnel user login
devtunnel create fresh-teams-bot --allow-anonymous
devtunnel port create 7071 --protocol https
devtunnel host
```

## Fontos:
- A tunnel csak addig él, amíg fut a terminálban
- Minden újraindításkor új URL-t kapsz (kivéve ha fixált tunnel-t állítasz be)
- Az Azure Bot Config-ban frissítsd az URL-t az új tunnel URL-re
