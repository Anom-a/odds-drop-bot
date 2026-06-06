import config
import sys
import db
import commands
from telegram.ext import ApplicationBuilder, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

def mask_key(key):
    if not key:
        return "Not Set"
    if len(key) <= 4:
        return "****"
    return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}" if len(key) >= 8 else f"{key[:2]}****"

async def post_init(application):
    """Hook to start the APScheduler securely inside the asyncio loop of the bot."""
    scheduler = AsyncIOScheduler()
    application.bot_data['scheduler'] = scheduler
    
    # Ready to add the polling job later using the interval from config
    # scheduler.add_job(poller.run_polling_cycle, 'interval', seconds=config.POLL_INTERVAL_SECONDS, args=[application])
    
    scheduler.start()
    print("APScheduler started alongside the bot.")

def main():
    print("Starting Odds Drop Bot...")
    print("Configuration:")
    print(f"ODDS_API_KEY: {mask_key(config.ODDS_API_KEY)}")
    print(f"TELEGRAM_BOT_TOKEN: {mask_key(config.TELEGRAM_BOT_TOKEN)}")
    print(f"TELEGRAM_CHAT_ID: {config.TELEGRAM_CHAT_ID}")
    print(f"DROP_THRESHOLD: {config.DROP_THRESHOLD}%")
    print(f"POLL_INTERVAL_SECONDS: {config.POLL_INTERVAL_SECONDS}s")
    
    db.init_db()

    if not config.TELEGRAM_BOT_TOKEN or config.TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        print("Error: Valid TELEGRAM_BOT_TOKEN is required to start the bot.")
        sys.exit(1)

    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("setthreshold", commands.set_threshold_handler))
    app.add_handler(CommandHandler("status", commands.status_handler))
    
    print("Initialization complete. Starting polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
