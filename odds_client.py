import requests
import datetime
import logging
import config
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

BASE_URL = "https://api.the-odds-api.com/v4"
requests_remaining = "Unknown"

def fetch_upcoming_matches() -> List[Dict[str, Any]]:
    """Fetch upcoming soccer matches from The Odds API."""
    global requests_remaining
    
    if not config.ODDS_API_KEY or config.ODDS_API_KEY == "your_odds_api_key_here":
        logger.error("ODDS_API_KEY is not set properly.")
        return []

    url = f"{BASE_URL}/sports/soccer/odds"
    params = {
        "apiKey": config.ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h,totals",
        "oddsFormat": "decimal"
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        
        if 'x-requests-remaining' in response.headers:
            requests_remaining = response.headers['x-requests-remaining']
            
        response.raise_for_status()
        data = response.json()
        
        normalized_matches = []
        now = datetime.datetime.now(datetime.timezone.utc)
        
        for match in data:
            commence_time_str = match.get('commence_time')
            if not commence_time_str:
                continue
                
            try:
                dt_str = commence_time_str.replace('Z', '+00:00')
                kickoff = datetime.datetime.fromisoformat(dt_str)
                if kickoff.tzinfo is None:
                    kickoff = kickoff.replace(tzinfo=datetime.timezone.utc)
            except ValueError:
                continue
                
            if kickoff < now:
                continue
                
            normalized_matches.append({
                'id': match.get('id'),
                'home_team': match.get('home_team'),
                'away_team': match.get('away_team'),
                'kickoff_time': commence_time_str,
                'bookmakers': match.get('bookmakers', [])
            })
            
        return normalized_matches
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching upcoming matches: {e}")
        return []

def parse_odds(match: dict) -> List[Dict[str, Any]]:
    """Extract and normalize odds from the first available bookmaker."""
    bookmakers = match.get('bookmakers', [])
    if not bookmakers:
        return []
        
    bookmaker = bookmakers[0]
    markets = bookmaker.get('markets', [])
    
    parsed_odds = []
    match_id = match.get('id')
    home_team = match.get('home_team')
    away_team = match.get('away_team')
    
    for market in markets:
        market_key = market.get('key')
        outcomes = market.get('outcomes', [])
        
        if market_key == 'h2h':
            for outcome in outcomes:
                outcome_name = outcome.get('name')
                price = outcome.get('price')
                
                if outcome_name == home_team:
                    norm_outcome = "Home"
                elif outcome_name == away_team:
                    norm_outcome = "Away"
                elif outcome_name == "Draw":
                    norm_outcome = "Draw"
                else:
                    norm_outcome = outcome_name 
                    
                parsed_odds.append({
                    'match_id': match_id,
                    'market': 'h2h',
                    'outcome': norm_outcome,
                    'odds': price
                })
                
        elif market_key == 'totals':
            for outcome in outcomes:
                outcome_name = outcome.get('name')
                price = outcome.get('price')
                point = outcome.get('point')
                
                if point == 2.5:
                    norm_outcome = f"{outcome_name} 2.5"
                    parsed_odds.append({
                        'match_id': match_id,
                        'market': 'totals',
                        'outcome': norm_outcome,
                        'odds': price
                    })
                    
    return parsed_odds
