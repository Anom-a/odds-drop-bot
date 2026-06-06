# Soccer Pre-Match Odds Drop Bot

A Telegram bot that continuously monitors The Odds API for significant pre-match odds drops in Soccer and alerts you directly via Telegram.

## Setup Instructions (Ubuntu Azure VM)

1. Clone or upload this repository to your Ubuntu VM.
2. Make sure your `.env` file is populated with your live API keys:
   ```ini
   ODDS_API_KEY=your_key_here
   TELEGRAM_BOT_TOKEN=your_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   DROP_THRESHOLD=20.0
   POLL_INTERVAL_SECONDS=60
   ```
3. Run the automated deployment script with `sudo` to set up system dependencies, the virtual environment, permissions, and log directories:
   ```bash
   sudo bash deploy.sh
   ```
4. Copy the systemd unit file into the system services directory:
   ```bash
   sudo cp odds-bot.service /etc/systemd/system/
   ```

## Enable and Start the Service
Run the following exact commands to reload the system daemon, enable the bot to start automatically on system boot, and launch it immediately:

```bash
sudo systemctl daemon-reload
sudo systemctl enable odds-bot
sudo systemctl start odds-bot
```

Confirm the service is running perfectly with:
```bash
sudo systemctl status odds-bot
```

---

## Bot Features & Commands

Once running, you can manage the bot dynamically from within Telegram:
- **How to update threshold:** Send `/setthreshold 15` (updates the drop threshold on the fly without needing a restart).
- **Check bot status:** Send `/status` to see daily alert counts, current threshold, and last poll timestamp.

---

## Server Management

**How to check logs:**
You can follow the systemd journal logs live using:
```bash
journalctl -u odds-bot -f
```
*(You can also inspect the raw text logs directly at `/var/log/odds-bot/bot.log` and `/var/log/odds-bot/error.log`)*

**How to restart:**
If the bot gets stuck or you make manual changes to the python files:
```bash
sudo systemctl restart odds-bot
```

**How to swap to paid API:**
1. Open the `.env` file located in the `/opt/odds-drop-bot/` installation directory:
   ```bash
   sudo nano /opt/odds-drop-bot/.env
   ```
2. Change `ODDS_API_KEY` to your new paid key.
3. Save the file and restart the bot to apply the changes:
   ```bash
   sudo systemctl restart odds-bot
   ```
