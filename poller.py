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
            
        # 3. Get subscribers and calculate minimum threshold
        subscribers = db_module.get_subscribers()
        if not subscribers:
            min_threshold = float(config_module.DROP_THRESHOLD)
        else:
            min_threshold = min([sub['threshold'] for sub in subscribers])
            
        # 4. Run check_for_drops with the minimum threshold
        drops = comparator.check_for_drops(all_odds, db_module, min_threshold)
        
        # 5. For each alert: send_alert to subscribers who meet their threshold
        for alert in drops:
            if not db_module.alert_already_sent(alert['alert_hash']):
                try:
                    if not subscribers:
                        logger.warning(f"No subscribers registered yet. Skipped sending alert for match {alert['match_id']}")
                        # Mark as sent anyway so we don't hold a backlog
                        db_module.mark_alert_sent(alert['alert_hash'])
                        continue
                        
                    sent_to_anyone = False
                    for sub in subscribers:
                        if alert['drop_pct'] >= sub['threshold']:
                            try:
                                await alerts.send_alert(bot, sub['chat_id'], alert)
                                alerts_sent_count += 1
                                sent_to_anyone = True
                            except Exception as e:
                                logger.error(f"Failed to send alert to {sub['chat_id']}: {e}")
                            
                    # Mark alert as sent after broadcasting
                    if sent_to_anyone or len(subscribers) > 0:
                        db_module.mark_alert_sent(alert['alert_hash'])
                        if sent_to_anyone:
                            logger.info(f"Alert broadcasted for match {alert['match_id']} ({alert['outcome']} dropped {alert['drop_pct']}%)")
                        
                except Exception as e:
                    logger.error(f"Failed to process alert for {alert['alert_hash']}: {e}")
                    
        # 6. Log completion details
        req_rem = getattr(odds_client, 'requests_remaining', 'Unknown')
        logger.info(f"Poll complete. Matches scanned: {matches_scanned}, Alerts sent: {alerts_sent_count}, API requests remaining: {req_rem}")
        
    except Exception as e:
        logger.error(f"Error during poll_once: {e}", exc_info=True)
