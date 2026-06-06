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
                    subscribers = db_module.get_subscribers()
                    
                    if not subscribers:
                        logger.warning(f"No subscribers registered yet. Skipped sending alert for match {alert['match_id']}")
                        # Mark as sent anyway so we don't hold a backlog
                        db_module.mark_alert_sent(alert['alert_hash'])
                        continue
                        
                    for chat_id in subscribers:
                        try:
                            await alerts.send_alert(bot, chat_id, alert)
                            alerts_sent_count += 1
                        except Exception as e:
                            logger.error(f"Failed to send alert to {chat_id}: {e}")
                            
                    # Mark alert as sent after broadcasting
                    db_module.mark_alert_sent(alert['alert_hash'])
                    logger.info(f"Alert broadcasted for match {alert['match_id']} ({alert['outcome']} dropped {alert['drop_pct']}%)")
                        
                except Exception as e:
                    logger.error(f"Failed to process alert for {alert['alert_hash']}: {e}")
                    
        # 6. Log completion details
        req_rem = getattr(odds_client, 'requests_remaining', 'Unknown')
        logger.info(f"Poll complete. Matches scanned: {matches_scanned}, Alerts sent: {alerts_sent_count}, API requests remaining: {req_rem}")
        
    except Exception as e:
        logger.error(f"Error during poll_once: {e}", exc_info=True)
