# 🐺 WHITE_WOLF FINAL BOT - Text 100% + Voice TTS

**FINAL VERSION - Last try:**

✅ **Text Notification 100% Render e kaj korbe** - Kew join/leave korle text channel e bolbe
✅ **Voice TTS o thakbe** - `!join` diye VC te anle voice e bolbe (local e 100%, Render e voice support korle)

---

## 🚀 Render Deploy (100% Working)

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
python bot.py
```

**Env Variables:**

**For 2 servers (Recommended):**
- Key: `NOTIFICATION_CHANNELS`
- Value (JSON):
```json
{"123456789012345678": 987654321098765432, "234567890123456789": 876543210987654321}
```
First = Server ID, Second = Text Channel ID

**Or simple format:**
```
123456789012345678:987654321098765432,234567890123456789:876543210987654321
```

**For 1 server (Old way):**
- Key: `NOTIFICATION_CHANNEL_ID`
- Value: `987654321098765432`

**Always needed:**
- `DISCORD_TOKEN` = bot token

---

## 💬 Commands

- `!test` - Text notification test (100% works)
- `!join` - VC te join (voice TTS er jonno)
- `!say <text>` - Voice e bolao
- `!leave` - VC theke leave
- `!debug` - Debug info
- `!ping` - Ping
- `!help` - Help

**Auto:**
- Text: Join/Leave/Move auto text channel e bolbe (100% Render)
- Voice: Bot VC te thakle join/leave te voice e bolbe (local 100%)

---

## 📁 Files
- `bot.py` - Final bot (text 100% + voice)
- `requirements.txt` - No apt-get needed, imageio-ffmpeg pip diye FFmpeg
- `render.yaml` - Render config

---

Made for WHITE_WOLF GLOBAL 🐺 - FINAL VERSION
