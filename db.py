import sqlite3
import datetime
import config

DB_FILE = 'odds_bot.db'

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    """Create all tables if not exist and initialize settings."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY,
                home_team TEXT,
                away_team TEXT,
                kickoff_time TEXT,
                sport_key TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS odds_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT,
                market TEXT,
                outcome TEXT,
                odds REAL,
                recorded_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_hash TEXT UNIQUE,
                sent_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscribers (
                chat_id TEXT PRIMARY KEY,
                registered_at TEXT
            )
        ''')
        
        # Initialize default threshold if not set
        cursor.execute('SELECT value FROM settings WHERE key = ?', ('DROP_THRESHOLD',))
        if cursor.fetchone() is None:
            cursor.execute(
                'INSERT INTO settings (key, value) VALUES (?, ?)',
                ('DROP_THRESHOLD', str(config.DROP_THRESHOLD))
            )
            
        conn.commit()

def add_subscriber(chat_id: str):
    """Add a new subscriber if they don't already exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO subscribers (chat_id, registered_at)
            VALUES (?, ?)
        ''', (chat_id, datetime.datetime.now(datetime.timezone.utc).isoformat()))
        conn.commit()

def get_subscribers() -> list:
    """Return a list of all registered chat IDs."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT chat_id FROM subscribers')
        return [row[0] for row in cursor.fetchall()]

def upsert_match(match_dict):
    """Insert or update a match record."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO matches (id, home_team, away_team, kickoff_time, sport_key)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                home_team=excluded.home_team,
                away_team=excluded.away_team,
                kickoff_time=excluded.kickoff_time,
                sport_key=excluded.sport_key
        ''', (
            match_dict['id'],
            match_dict.get('home_team'),
            match_dict.get('away_team'),
            match_dict.get('kickoff_time'),
            match_dict.get('sport_key')
        ))
        conn.commit()

def store_odds(match_id, market, outcome, odds):
    """Store an odds entry."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO odds_history (match_id, market, outcome, odds, recorded_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (match_id, market, outcome, odds, datetime.datetime.now(datetime.timezone.utc).isoformat()))
        conn.commit()

def get_latest_odds(match_id, market, outcome):
    """Return the most recently recorded odds for a specific outcome, or None."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT odds FROM odds_history 
            WHERE match_id = ? AND market = ? AND outcome = ? 
            ORDER BY recorded_at DESC LIMIT 1
        ''', (match_id, market, outcome))
        row = cursor.fetchone()
        return row[0] if row else None

def alert_already_sent(alert_hash):
    """Check if an alert was already sent."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM sent_alerts WHERE alert_hash = ?', (alert_hash,))
        return cursor.fetchone() is not None

def mark_alert_sent(alert_hash):
    """Mark an alert as sent, ignoring if already marked."""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO sent_alerts (alert_hash, sent_at)
                VALUES (?, ?)
            ''', (alert_hash, datetime.datetime.now(datetime.timezone.utc).isoformat()))
            conn.commit()
        except sqlite3.IntegrityError:
            pass # alert_hash must be unique, so we ignore duplicates

def get_threshold() -> float:
    """Get the current drop threshold from settings, fallback to config."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', ('DROP_THRESHOLD',))
        row = cursor.fetchone()
        return float(row[0]) if row else float(config.DROP_THRESHOLD)

def set_threshold(value: float):
    """Update the drop threshold in settings."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
        ''', ('DROP_THRESHOLD', str(value)))
        conn.commit()

if __name__ == "__main__":
    import os
    import time
    
    # Use a test DB for assertions
    DB_FILE = 'test_odds_bot.db'
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        
    try:
        init_db()
        
        # Test: Threshold defaults to config value
        assert get_threshold() == float(config.DROP_THRESHOLD), "Default threshold mismatch"
        
        # Test: Setting new threshold
        set_threshold(15.5)
        assert get_threshold() == 15.5, "Failed to update threshold"
        
        # Test: Upsert match (Insert)
        m = {
            'id': 'match123',
            'home_team': 'Arsenal',
            'away_team': 'Chelsea',
            'kickoff_time': '2023-12-01T15:00:00Z',
            'sport_key': 'soccer_epl'
        }
        upsert_match(m)
        
        # Verify insert
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT home_team FROM matches WHERE id=?', ('match123',))
            row = c.fetchone()
            assert row is not None
            assert row[0] == 'Arsenal', "Match insert failed"
            
        # Test: Upsert match (Update)
        m['home_team'] = 'Arsenal FC'
        upsert_match(m)
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT home_team FROM matches WHERE id=?', ('match123',))
            row = c.fetchone()
            assert row[0] == 'Arsenal FC', "Match update failed"
            
        # Test: get_latest_odds for non-existent record
        assert get_latest_odds('match123', 'h2h', 'Arsenal') is None, "Should be None"
        
        # Test: store_odds & get_latest_odds
        store_odds('match123', 'h2h', 'Arsenal', 2.1)
        assert get_latest_odds('match123', 'h2h', 'Arsenal') == 2.1, "Odds store/retrieve failed"
        
        # Simulate new odds later to check ordering
        time.sleep(0.1) 
        store_odds('match123', 'h2h', 'Arsenal', 1.9)
        assert get_latest_odds('match123', 'h2h', 'Arsenal') == 1.9, "Odds ordering failed"
        
        # Test: alerts
        alert_hash = 'hash123'
        assert not alert_already_sent(alert_hash), "Alert should not exist yet"
        
        mark_alert_sent(alert_hash)
        assert alert_already_sent(alert_hash), "Alert should be marked as sent"
        
        # Marking again should not crash (IntegrityError caught)
        mark_alert_sent(alert_hash)
        assert alert_already_sent(alert_hash), "Alert marking duplication failed"
        
        print("All db.py tests passed successfully.")
        
    finally:
        # Cleanup
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
