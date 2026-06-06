# ⚽ Soccer Pre-Match Odds Drop Bot

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-Production_Ready-brightgreen)

A high-performance, async Telegram bot that continuously monitors [The Odds API](https://the-odds-api.com/) for significant pre-match odds drops in global soccer matches and broadcasts real-time alerts to subscribed users.

Designed for high availability, this bot runs as a background service, features a robust SQLite persistence layer, and supports multi-user subscription with dynamic, per-user configuration.

---

## ✨ Key Features

- **Real-Time Monitoring**: Automatically polls The Odds API to detect drastic pre-match odds fluctuations.
- **Multi-User Architecture**: Supports an unlimited number of Telegram users simultaneously. Users simply send `/start` to subscribe.
- **Per-User Customization**: Each user can set their own custom odds-drop sensitivity threshold (e.g., `15%` vs `25%`) using interactive bot commands.
- **Duplicate Alert Prevention**: Cryptographic hashing (`SHA-256`) of odds data ensures users are never spammed with duplicate alerts for the same market shift.
- **Zero-Downtime Resilience**: Built with `python-telegram-bot` and `APScheduler` wrapped in asynchronous event loops. Survives network interruptions and API rate limits gracefully.
- **Production Ready**: Includes automated deployment scripts and a native Linux `systemd` unit file for 24/7 background execution.

---

## 🛠️ Technology Stack

- **Language**: Python 3.10+
- **Database**: SQLite3 (Local, serverless, atomic)
- **APIs**: 
  - [The Odds API v4](https://the-odds-api.com/) (Data Ingestion)
  - [Telegram Bot API](https://core.telegram.org/bots/api) (Async User Interface)
- **Key Libraries**: `python-telegram-bot`, `apscheduler`, `requests`, `python-dotenv`

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher installed.
- A free API key from [The Odds API](https://the-odds-api.com/).
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather).

### 1. Local Installation

```bash
# Clone the repository
git clone https://github.com/Anom-a/odds-drop-bot.git
cd odds-drop-bot

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and inject your secure credentials:

```bash
cp .env.example .env
```

Edit the `.env` file:
```ini
ODDS_API_KEY=your_odds_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
DROP_THRESHOLD=20.0
POLL_INTERVAL_SECONDS=60
```

### 3. Run the Bot

```bash
python main.py
```

---

## 📱 Bot Commands (Telegram Interface)

Users can interact with the bot directly via Telegram to manage their personal subscriptions:

| Command | Description |
| :--- | :--- |
| `/start` | Subscribes the user to the broadcast list and opens the main menu. |
| `/status` | Displays a beautiful dashboard showing the user's personal threshold, last system poll time, and alerts dispatched today. |
| `/setthreshold <float>`| Updates the user's personal odds drop threshold (e.g., `/setthreshold 15.5` alerts only on drops ≥ 15.5%). |

---

## ☁️ Cloud Deployment (Ubuntu / Debian)

This project includes configuration files for seamless deployment to a virtual machine (e.g., Azure, AWS EC2, DigitalOcean).

1. Upload the repository to your remote server (e.g., `/opt/odds-drop-bot`).
2. Run the automated deployment script:
   ```bash
   sudo bash deploy.sh
   ```
3. Register the bot as a highly-available background service:
   ```bash
   sudo cp odds-bot.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now odds-bot
   ```

### Operational Commands
- **View Live Logs**: `sudo journalctl -u odds-bot -f`
- **Check Service Status**: `sudo systemctl status odds-bot`
- **Restart Bot**: `sudo systemctl restart odds-bot`

---

## 📄 License & Disclaimer

This project is licensed under the MIT License. 

*Disclaimer: This bot is strictly for informational and educational purposes. Betting markets are highly volatile, and odds data may be subject to API delays.*
