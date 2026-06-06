import config
import sys

def mask_key(key):
    if not key:
        return "Not Set"
    if len(key) <= 4:
        return "****"
    return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}" if len(key) >= 8 else f"{key[:2]}****"

def main():
    print("Starting Odds Drop Bot...")
    print("Configuration:")
    print(f"ODDS_API_KEY: {mask_key(config.ODDS_API_KEY)}")
    print(f"TELEGRAM_BOT_TOKEN: {mask_key(config.TELEGRAM_BOT_TOKEN)}")
    print(f"TELEGRAM_CHAT_ID: {config.TELEGRAM_CHAT_ID}")
    print(f"DROP_THRESHOLD: {config.DROP_THRESHOLD}%")
    print(f"POLL_INTERVAL_SECONDS: {config.POLL_INTERVAL_SECONDS}s")
    
    print("Initialization complete. Exiting cleanly.")
    sys.exit(0)

if __name__ == "__main__":
    main()
