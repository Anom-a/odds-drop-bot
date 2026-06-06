import hashlib

def calculate_drop(old_odds: float, new_odds: float) -> float:
    """
    Calculate the drop percentage from old_odds to new_odds.
    Returns drop percentage rounded to 2 decimal places.
    Returns 0.0 if new_odds >= old_odds.
    """
    if new_odds >= old_odds or old_odds == 0:
        return 0.0
    
    drop_pct = ((old_odds - new_odds) / old_odds) * 100
    return round(drop_pct, 2)

def make_alert_hash(match_id: str, market: str, outcome: str, new_odds: float) -> str:
    """
    Generate a SHA256 hash of the alert details.
    Used to prevent duplicate alerts for the same match/market/outcome/odds.
    """
    raw = f"{match_id}|{market}|{outcome}|{new_odds}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def check_for_drops(odds_list: list[dict], db, threshold: float) -> list[dict]:
    """
    Check a list of odds for significant drops compared to the DB.
    Returns a list of alert dictionaries.
    """
    alerts = []
    matches_cache = {}
    
    def get_match_info(m_id):
        if m_id not in matches_cache:
            with db.get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT home_team, away_team, kickoff_time FROM matches WHERE id=?", (m_id,))
                row = c.fetchone()
                if row:
                    matches_cache[m_id] = {
                        'home_team': row[0],
                        'away_team': row[1],
                        'kickoff_time': row[2]
                    }
                else:
                    matches_cache[m_id] = {
                        'home_team': 'Unknown',
                        'away_team': 'Unknown',
                        'kickoff_time': 'Unknown'
                    }
        return matches_cache[m_id]

    for entry in odds_list:
        match_id = entry['match_id']
        market = entry['market']
        outcome = entry['outcome']
        new_odds = entry['odds']
        
        old_odds = db.get_latest_odds(match_id, market, outcome)
        
        if old_odds is not None:
            drop_pct = calculate_drop(old_odds, new_odds)
            
            if drop_pct >= threshold:
                alert_hash = make_alert_hash(match_id, market, outcome, new_odds)
                
                if not db.alert_already_sent(alert_hash):
                    match_info = get_match_info(match_id)
                    alerts.append({
                        'match_id': match_id,
                        'home_team': match_info['home_team'],
                        'away_team': match_info['away_team'],
                        'market': market,
                        'outcome': outcome,
                        'old_odds': old_odds,
                        'new_odds': new_odds,
                        'drop_pct': drop_pct,
                        'kickoff_time': match_info['kickoff_time'],
                        'alert_hash': alert_hash
                    })
        
        # Store new odds in DB regardless
        db.store_odds(match_id, market, outcome, new_odds)
        
    return alerts

if __name__ == "__main__":
    print("Running unit tests for comparator.py...")
    
    # Test calculate_drop
    assert calculate_drop(2.0, 2.0) == 0.0, "Equal odds should return 0.0"
    assert calculate_drop(2.0, 2.1) == 0.0, "Rising odds should return 0.0"
    assert calculate_drop(2.0, 1.6) == 20.0, "20% drop from 2.0 to 1.6"
    assert calculate_drop(2.5, 2.00025) == 19.99, "19.99% drop calculation"
    
    # Test make_alert_hash
    hash1 = make_alert_hash("match_1", "h2h", "Home", 1.5)
    hash2 = make_alert_hash("match_1", "h2h", "Home", 1.5)
    hash3 = make_alert_hash("match_1", "h2h", "Home", 1.4)
    
    assert hash1 == hash2, "Same inputs should produce same hash"
    assert hash1 != hash3, "Different odds should produce different hash"
    assert len(hash1) == 64, "SHA256 hash should be 64 chars long"
    
    print("All tests passed successfully.")
