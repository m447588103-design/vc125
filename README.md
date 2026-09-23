# 🐺 WHITE_WOLF Voice Notification Bot

Render e 24/7 host korar jonno fully ready Discord bot. Voice join / leave / move korle embed notification pathabe.

### ✅ Render er jonno ki ki add kora holo?
- **Flask Keep-Alive Server**: Render Web Service (Free) e bot sleep hoye jay, tai `/` & `/health` endpoint add kora hoise. UptimeRobot diye ping korle 24/7 online thakbe.
- **Improved `render.yaml`**: `type: web`, `plan: free`, `healthCheckPath: /health`, auto deploy on.
- **Error Handling**: Channel na pele crash korbe na, proper logging.
- **`.gitignore`, `runtime.txt`, `.env.example`, `Procfile`**: Production ready.

---

## 🚀 Render e Deploy (Step by Step - Bangla)

### 1. GitHub e Upload
Ei sob file GitHub repo te push koro.

### 2. Render e New Service
- https://dashboard.render.com e jao
- **New +** > **Blueprint** select koro (render.yaml auto detect korbe) **OR** **Web Service** select koro
- GitHub repo connect koro

### 3. Settings
- **Name**: `white-wolf-voice-bot`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python bot.py`
- **Plan**: `Free`

### 4. Environment Variables (Most Important)
Render Dashboard > **Environment** tab e 2 ta variable add koro:

| Key | Value |
|-----|-------|
| `DISCORD_TOKEN` | Tomar Discord Bot Token (Discord Developer Portal theke) |
| `NOTIFICATION_CHANNEL_ID` | Je text channel e notification jabe tar ID (Copy ID) |
| `PORT` | `10000` (auto thakbe) |

> ⚠️ `.env` file kokhono GitHub e upload korba na!

### 5. Discord Developer Portal Settings
- https://discord.com/developers/applications > Tomar Bot
- **Bot** tab > **Privileged Gateway Intents**:
  - ✅ `SERVER MEMBERS INTENT` ON
  - ✅ `MESSAGE CONTENT INTENT` (optional)
- **OAuth2 > URL Generator**:
  - Scopes: `bot`
  - Permissions: `View Channel`, `Send Messages`, `Embed Links`, `Read Message History`

### 6. 24/7 Online Rakhar Trick (Free Plan)
Free plan e 15 min inactive thakle service sleep hoye jay. Tai:
1. https://uptimerobot.com e free account kholo
2. **New Monitor** > **HTTP(s)** 
3. URL: Tomar Render er URL + `/health`  -> `https://white-wolf-voice-bot.onrender.com/health`
4. Interval: 5 minutes

Ete 5 min por por ping porbe ar bot kokhono sleep hobe na!

---

## 🖥️ Local e Test

```bash
# .env.example copy kore .env banao
cp .env.example .env
# .env edit kore token boshao

pip install -r requirements.txt
python bot.py
```

Browser e `http://localhost:10000` gele `Bot is Alive` dekhabe.

---

## 📁 File Structure
```
.
├── bot.py              # Main bot + Flask keep-alive
├── requirements.txt    # Dependencies
├── render.yaml         # Render Blueprint (auto deploy)
├── runtime.txt         # Python version
├── Procfile            # For Render/Heroku
├── .env.example        # Example env
├── .gitignore
└── README.md
```

## 🔒 Security
- Token kokhono public korba na
- `.env` gitignore e ache

Made with ❤️ for WHITE_WOLF GLOBAL 🐺
