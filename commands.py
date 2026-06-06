from telegram import Update
from telegram.ext import ContextTypes
import db
import datetime

async def set_threshold_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /setthreshold <value>"""
    if not context.args:
        await update.message.reply_text("Usage: /setthreshold <value>")
        return
        
    try:
        value = float(context.args[0])
        if not (1 <= value <= 50):
            await update.message.reply_text("Error: Threshold must be a float between 1 and 50.")
            return
            
        db.set_threshold(value)
        await update.message.reply_text(f"Threshold updated to {value}%")
    except ValueError:
        await update.message.reply_text("Error: Invalid number provided. Must be a float.")

async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /status"""
    threshold = db.get_threshold()
    
    with db.get_connection() as conn:
        c = conn.cursor()
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        c.execute("SELECT COUNT(*) FROM sent_alerts WHERE sent_at LIKE ?", (today + "%",))
        total_alerts_today = c.fetchone()[0]
        
    last_poll_time = context.bot_data.get('last_poll_time', 'Not polled yet')
    
    reply_text = (
        f"📊 Bot Status\n\n"
        f"Current Threshold: {threshold}%\n"
        f"Last Poll Time: {last_poll_time}\n"
        f"Total Alerts Today: {total_alerts_today}"
    )
    await update.message.reply_text(reply_text)
