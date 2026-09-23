# 🐺 WHITE_WOLF Voice TTS Bot - VC te Ese Bolbe!

**KITT Style Voice Bot:** Kew voice channel e join korle bot **nije VC te join hoye mukhe bolbe** "X join korse", leave nile "X leave nise" — text e na, **voice e bolbe!**

---

## 🎙️ Ki kore?

- **Join:** `Joy` VC te join korlo → Bot VC te join hoye bolbe: **"Joy voice e join korse"**
- **Leave:** `Joy` leave nilo → Bot bolbe: **"Joy voice theke leave nise"**
- **Move:** Channel change korle bolbe

100% Render Free Tier compatible!

---

## 🚀 Render e Deploy

### Build & Start Command:
- **Build:** `apt-get update && apt-get install -y ffmpeg && pip install -r requirements.txt`
- **Start:** `python bot.py`

Render Dashboard e auto set ache `render.yaml` theke.

### Environment Variables:
| Key | Value | Kothay paba |
|-----|-------|-------------|
| `DISCORD_TOKEN` | Bot token | Discord Dev Portal > Bot > Token |
| `VOICE_LANG` | `bn` (Bangla) ba `en` (English) | Optional, default `en` |
| `PORT` | `10000` | Auto |

### Discord Portal Setup (Must!):
1. https://discord.com/developers/applications > Bot
2. **Privileged Intents:**
   - ✅ SERVER MEMBERS INTENT = ON
   - ✅ MESSAGE CONTENT INTENT = ON
3. **Bot Permissions:** 
   - `View Channel`, `Send Messages`, `Connect`, `Speak`, `Use Voice Activity`

### Invite Link:
OAuth2 > URL Generator > Scopes: `bot` + `applications.commands`
Permissions: `Connect`, `Speak`, `View Channel`, `Send Messages`

---

## 💬 Commands

- `!join` - Bot ke tomar VC te anbe (age VC te join koro)
- `!leave` - Bot VC theke ber hobe
- `!say <text>` - Bot ke diye kichu bolao, ex: `!say Hello guys`
- `!testvoice` - Voice TTS test
- `!ping` - Ping check
- `!help` - Help

**Auto:** `!join` diye ekbar VC te anle, tarpor kew join/leave korle bot auto bolbe!

---

## 🔧 Local Test

```bash
# FFmpeg install koro (must)
# Windows: https://ffmpeg.org/download.html
# Linux: sudo apt install ffmpeg

pip install -r requirements.txt
python bot.py
```

---

## ❓ Common Issues

**1. Bot VC te join hoy na?**
- `!join` command e age VC te thako
- Bot er `Connect` + `Speak` permission ache?

**2. Voice e kotha bole na?**
- Render log e `FFmpeg error` ase? Build command e `ffmpeg` install ache?
- `!testvoice` diye test koro

**3. No open ports error?**
- Ekhon fix kora, http.server use kora hoise

---

Made for **WHITE_WOLF GLOBAL** 🐺 - KITT Style Voice TTS
