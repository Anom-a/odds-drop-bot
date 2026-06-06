from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
import db
import datetime

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start"""
    chat_id = str(update.effective_chat.id)
    db.add_subscriber(chat_id)
    
    welcome_text = (
        "👋 Welcome to the *Soccer Pre-Match Odds Drop Bot*!\n\n"
        "I monitor The Odds API continuously and will instantly notify you of significant pre-match odds drops.\n\n"
        "📖 *Available Commands:*\n"
        "📊 `/status` — View the bot's current status and daily alert stats\n"
        "⚙️ `/setthreshold <value>` — Change the drop percentage required to trigger an alert\n\n"
        "You can use the menu below for quick access!"
    )
    
    # Create a custom keyboard
    keyboard = [
        [KeyboardButton("/status")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def set_threshold_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /setthreshold <value>"""
    if not context.args:
        await update.message.reply_text("ℹ️ *Usage:* `/setthreshold <value>`\n_Example:_ `/setthreshold 15`", parse_mode='Markdown')
        return
        
    try:
        value = float(context.args[0])
        if not (1 <= value <= 50):
            await update.message.reply_text("❌ *Error:* Threshold must be a float between 1 and 50.", parse_mode='Markdown')
            return
            
        chat_id = str(update.effective_chat.id)
        db.set_threshold(chat_id, value)
        await update.message.reply_text(f"✅ *Success!* Threshold updated to *{value}%*", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("❌ *Error:* Invalid number provided. Must be a float.", parse_mode='Markdown')

async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /status"""
    chat_id = str(update.effective_chat.id)
    threshold = db.get_threshold(chat_id)
    
    with db.get_connection() as conn:
        c = conn.cursor()
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        c.execute("SELECT COUNT(*) FROM sent_alerts WHERE sent_at LIKE ?", (today + "%",))
        total_alerts_today = c.fetchone()[0]
        
    last_poll_time = context.bot_data.get('last_poll_time', 'Not polled yet')
    
    reply_text = (
        "🤖 *Bot Status Dashboard*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📉 *Current Threshold:* `{threshold}%`\n"
        f"⏱️ *Last Poll Time:* `{last_poll_time}`\n"
        f"🔔 *Alerts Sent Today:* `{total_alerts_today}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "_Monitoring in progress..._"
    )
    await update.message.reply_text(reply_text, parse_mode='Markdown')
