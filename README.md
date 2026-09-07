# 🐺 WHITE_WOLF Voice Notification Bot

Render-ready Discord bot for voice join, leave, and move notifications.

## GitHub / Render
1. Upload these files to a GitHub repository.
2. On Render, create a Background Worker from the repository.
3. Add environment variables:
   - `DISCORD_TOKEN` = your Discord bot token
   - `NOTIFICATION_CHANNEL_ID` = the text-channel ID for notifications
4. Render uses `render.yaml` automatically when configured for Blueprint deployment.

## Discord permissions
Enable Server Members Intent in the Discord Developer Portal. The bot needs View Channel, Send Messages, and Embed Links in the notification channel.

## Security
Do NOT upload `.env` or your real Discord bot token to GitHub.
