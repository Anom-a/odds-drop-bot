import logging
import odds_client
import comparator
import alerts
import datetime

logger = logging.getLogger(__name__)

async def poll_once(bot, db_module, config_module):
    """
    Polling job executed periodically by APScheduler.
    """
    logger.info("Starting polling cycle...")
    
    try:
        # 1. Fetch upcoming matches
        matches = odds_client.fetch_upcoming_matches()
        matches_scanned = len(matches)
        alerts_sent_count = 0
        
        all_odds = []
        
        # 2. For each match: upsert into matches table and parse odds
        for match in matches:
            db_module.upsert_match(match)
            parsed_odds = odds_client.parse_odds(match)
            all_odds.extend(parsed_odds)
            
        # 3. Get the dynamic threshold
        current_threshold = db_module.get_threshold()
        
        # 4. Run check_for_drops
        drops = comparator.check_for_drops(all_odds, db_module, current_threshold)
        
        # 5. For each alert: send_alert
        for alert in drops:
            if not db_module.alert_already_sent(alert['alert_hash']):
                try:
                    # Update context with last poll time so /status can show it
                    # But we don't have access to context here, so we skip that for now.
                    
                    if config_module.TELEGRAM_CHAT_ID and config_module.TELEGRAM_CHAT_ID != "your_telegram_chat_id_here":
                        await alerts.send_alert(bot, config_module.TELEGRAM_CHAT_ID, alert)
                        alerts_sent_count += 1
                        logger.info(f"Alert sent for match {alert['match_id']} ({alert['outcome']} dropped {alert['drop_pct']}%)")
                    else:
                        logger.warning(f"Simulated alert (CHAT_ID missing) for match {alert['match_id']}")
                        # We simulate marking it as sent anyway so we don't spam the DB
                        db_module.mark_alert_sent(alert['alert_hash'])
                        
                except Exception as e:
                    logger.error(f"Failed to send alert for {alert['alert_hash']}: {e}")
                    
        # 6. Log completion details
        req_rem = getattr(odds_client, 'requests_remaining', 'Unknown')
        logger.info(f"Poll complete. Matches scanned: {matches_scanned}, Alerts sent: {alerts_sent_count}, API requests remaining: {req_rem}")
        
    except Exception as e:
        logger.error(f"Error during poll_once: {e}", exc_info=True)
