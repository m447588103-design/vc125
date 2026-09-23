# 🐺 WHITE_WOLF Voice Bot - Render Ready V2 (100% Working)

**New Design:** Flask + threading bad diye ekhon **aiohttp + asyncio** diye banano — Render e `No open ports detected` error 100% fix!

Voice channel e kew join/leave/move korle auto embed notification pathabe.

---

## ✅ V2 te ki fix kora hoise?

**V1 Problem:**
- Flask thread use korsilam, Render port detect korte parto na
- `No open ports detected` -> Render bot ke kill kore dito
- Tai voice log kaj korto na

**V2 Solution:**
- `aiohttp` web server, same asyncio loop e Discord bot er sathe chole
- Render er port 60s er moddhe instant bind hoy
- No threading, no Flask — 100% stable

---

## 🚀 Render e Deploy (Bangla Guide)

### 1. GitHub e Push
Ei repo ta GitHub e push koro.

### 2. Render e Service Banao
- https://dashboard.render.com > **New + > Web Service**
- GitHub repo connect koro `vc125`
- **Name:** `white-wolf-voice-bot`
- **Region:** `Singapore` (BD er jonno fast)
- **Branch:** `main` ba tomar branch
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python bot.py`
- **Plan:** `Free`

### 3. Environment Variables (Most Important!)
**Environment** tab e 2 ta add koro:

| Key | Value | Kothay paba |
|-----|-------|-------------|
| `DISCORD_TOKEN` | `MTM...` | Discord Developer Portal > Bot > Token |
| `NOTIFICATION_CHANNEL_ID` | `1234567890` | Discord channel e Right Click > Copy ID |
| `PORT` | `10000` | Auto thakbe |

> ⚠️ Token kokhono GitHub e dio na!

### 4. Discord Developer Portal Setup (Must!)
https://discord.com/developers/applications > Tomar App > **Bot** tab:

**Privileged Gateway Intents:**
- ✅ **SERVER MEMBERS INTENT** = ON
- ✅ **MESSAGE CONTENT INTENT** = ON
- ✅ **PRESENCE INTENT** = OFF (lagbe na)

Save koro.

**Bot Invite Link:**
OAuth2 > URL Generator:
- Scopes: `bot`
- Permissions: `View Channel`, `Send Messages`, `Embed Links`, `Read Message History`, `Connect`, `View Voice Channel`

### 5. Deploy!
**Manual Deploy > Deploy latest commit** click koro.

**Logs e dekhba:**
```
✅ WEB SERVER started on 0.0.0.0:10000
🐺 WHITE_WOLF Voice Bot Online!
✅ Startup message sent!
```
Jodi `No open ports detected` na ase, mane success!

Discord e bot message pathabe: `🟢 WHITE_WOLF Bot Online!`

---

## 🧪 Test Commands

Discord e giye:

- `!ping` - Bot alive kina
- `!test` - Notification channel e test message
- `!debug` - Sob info dekhabe
- `!help` - Command list

Voice channel e join/leave kore test koro, instant embed asbe.

---

## 🔁 24/7 Online (Free Plan Trick)

Free plan e 15 min inactive thakle sleep hoy. Tai UptimeRobot use koro:

1. https://uptimerobot.com e free account
2. New Monitor > HTTP(s)
3. URL: `https://tomar-bot-name.onrender.com/health`
4. Interval: 5 min

Ete bot kokhono sleep hobe na!

---

## 📁 Files

```
bot.py              # Main bot + aiohttp server (Render 100% compatible)
requirements.txt    # discord.py + aiohttp + dotenv
render.yaml         # Blueprint - auto deploy
runtime.txt         # Python 3.11
.env.example        # Local test er jonno example
.gitignore
README.md
```

## 🖥️ Local Test

```bash
cp .env.example .env
# .env e token boshao
pip install -r requirements.txt
python bot.py
# Browser: http://localhost:10000
# Health: http://localhost:10000/health
```

---

## ❓ Common Problems

**1. Bot online but voice log ase na?**
- Portal e SERVER MEMBERS INTENT ON korso?
- `!debug` e channel found dekhay?
- Bot ke voice channel dekhte permission ase?

**2. Startup message ase na?**
- NOTIFICATION_CHANNEL_ID vul
- Bot er Send Messages permission nai

**3. Render e No open ports?**
- V2 te fix kora, ar asbe na. Asle `PORT` env check koro.

---

Made with ❤️ for **WHITE_WOLF GLOBAL** 🐺
