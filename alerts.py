import db

def format_alert(alert: dict) -> str:
    return f"""🚨 ODDS DROP ALERT

Match: {alert['home_team']} vs {alert['away_team']}
Market: {alert['market']} — {alert['outcome']}

Old Odds: {alert['old_odds']}
New Odds: {alert['new_odds']}
Drop: {alert['drop_pct']}%

Kickoff: {alert['kickoff_time']}"""

async def send_alert(bot, chat_id: str, alert: dict):
    text = format_alert(alert)
    await bot.send_message(chat_id=chat_id, text=text)

if __name__ == "__main__":
    import asyncio
    import config
    from telegram import Bot
    
    async def test():
        print("Running alerts test...")
        if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID or config.TELEGRAM_CHAT_ID == "your_telegram_chat_id_here":
            print("Warning: Please set a valid TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env to test the alert.")
            
            # Print format check
            dummy_alert = {
                'home_team': 'Test Home',
                'away_team': 'Test Away',
                'market': 'h2h',
                'outcome': 'Home',
                'old_odds': 2.0,
                'new_odds': 1.6,
                'drop_pct': 20.0,
                'kickoff_time': '2023-12-01T15:00:00Z',
                'alert_hash': 'dummy_hash_123'
            }
            print("\nFormat check (not sent):")
            print(format_alert(dummy_alert))
            return
            
        bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        dummy_alert = {
            'home_team': 'Test Home',
            'away_team': 'Test Away',
            'market': 'h2h',
            'outcome': 'Home',
            'old_odds': 2.0,
            'new_odds': 1.6,
            'drop_pct': 20.0,
            'kickoff_time': '2023-12-01T15:00:00Z',
            'alert_hash': 'dummy_hash_123'
        }
        print(f"Sending test alert to {config.TELEGRAM_CHAT_ID}...")
        await send_alert(bot, config.TELEGRAM_CHAT_ID, dummy_alert)
        print("Test alert sent successfully!")
        
    asyncio.run(test())
