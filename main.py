import config
import sys
import logging
import db
import commands
from telegram.ext import ApplicationBuilder, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import poller
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("odds_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

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
    
    # Add the polling job using the interval from config
    scheduler.add_job(
        poller.poll_once, 
        'interval', 
        seconds=config.POLL_INTERVAL_SECONDS, 
        args=[application.bot, db, config]
    )
    
    scheduler.start()
    
    # Record initial poll time logic in bot_data if needed
    application.bot_data['last_poll_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logger.info(f"APScheduler started. Polling every {config.POLL_INTERVAL_SECONDS}s.")

async def post_stop(application):
    """Graceful shutdown hook for the scheduler."""
    scheduler = application.bot_data.get('scheduler')
    if scheduler:
        scheduler.shutdown()
        logger.info("APScheduler stopped.")

def main():
    logger.info("Starting Odds Drop Bot...")
    logger.info("Configuration:")
    logger.info(f"ODDS_API_KEY: {mask_key(config.ODDS_API_KEY)}")
    logger.info(f"TELEGRAM_BOT_TOKEN: {mask_key(config.TELEGRAM_BOT_TOKEN)}")
    logger.info(f"TELEGRAM_CHAT_ID: {config.TELEGRAM_CHAT_ID}")
    logger.info(f"DROP_THRESHOLD: {config.DROP_THRESHOLD}%")
    logger.info(f"POLL_INTERVAL_SECONDS: {config.POLL_INTERVAL_SECONDS}s")
    
    # 1. Init DB
    db.init_db()

    # 2. Start Builder
    if not config.TELEGRAM_BOT_TOKEN or config.TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        logger.error("Valid TELEGRAM_BOT_TOKEN is required to start the bot.")
        sys.exit(1)

    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).post_init(post_init).post_stop(post_stop).build()
    
    # 3. Register Commands
    app.add_handler(CommandHandler("setthreshold", commands.set_threshold_handler))
    app.add_handler(CommandHandler("status", commands.status_handler))
    
    logger.info("Initialization complete. Starting bot polling...")
    
    # 4. Start Blocking Run (handles SIGTERM and SIGINT gracefully)
    app.run_polling()

if __name__ == "__main__":
    main()
