import fastf1 as f1
from datetime import datetime
import warnings
import os
from pathlib import Path

# Suppress fastf1 warnings
warnings.filterwarnings('ignore')

# Create cache directory if it doesn't exist
CACHE_DIR = Path(__file__).parent.parent / 'cache'
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Enable cache globally
f1.Cache.enable_cache(str(CACHE_DIR))

def get_race_details(year, race_round):
    """
    Get race details for a specific race round.
    
    Parameters:
    -----------
    year : int
        The year of the F1 season
    race_round : int or str
        The race round number or race name
        
    Returns:
    --------
    dict : Dictionary containing race information including:
        - event_info: Basic event details (name, location, date)
        - session_status: Whether race is upcoming, ongoing, or completed
        - race_data: Race session data (if available)
        - results: Race results (if race is completed)
    """
    
    try:
        # Get the event schedule
        schedule = f1.get_event_schedule(year)
        
        # Get event by round number or name
        if isinstance(race_round, int):
            event = schedule[schedule['RoundNumber'] == race_round].iloc[0]
        else:
            event = schedule[schedule['EventName'].str.contains(race_round, case=False)].iloc[0]
        
        # Extract basic event information
        event_info = {
            'event_name': event['EventName'],
            'location': event['Location'],
            'country': event['Country'],
            'round': event['RoundNumber'],
            'event_date': event['EventDate'],
        }
        
        # Check session dates
        current_time = datetime.now()
        race_date = event['EventDate'].to_pydatetime().replace(tzinfo=None)
        
        # Determine race status
        if current_time < race_date:
            session_status = 'upcoming'
            race_data = None
            results = None
        else:
            session_status = 'completed'
            
            # Load race session
            try:
                race_session = f1.get_session(year, event['RoundNumber'], 'R')
                race_session.load()
                
                # Get race results
                results = race_session.results
                
                # Convert results to dictionary format
                results_list = []
                for idx, driver in results.iterrows():
                    results_list.append({
                        'position': driver['Position'],
                        'driver_number': driver['DriverNumber'],
                        'driver': driver['Abbreviation'],
                        'full_name': driver['FullName'],
                        'team': driver['TeamName'],
                        'time': str(driver['Time']) if 'Time' in driver and driver['Time'] is not None else 'N/A',
                        'status': driver['Status'],
                        'points': driver['Points']
                    })
                
                race_data = {
                    'total_laps': race_session.total_laps,
                    'track_status': race_session.track_status,
                    'session_start': str(race_session.session_start_time),
                }
                
                results = results_list
                
            except Exception as e:
                session_status = 'data_unavailable'
                race_data = None
                results = None
                event_info['error'] = f"Could not load race data: {str(e)}"
        
        return {
            'event_info': event_info,
            'session_status': session_status,
            'race_data': race_data,
            'results': results
        }
        
    except Exception as e:
        return {
            'error': f"Failed to retrieve race details: {str(e)}",
            'year': year,
            'race_round': race_round
        }


def get_current_season_races(year=None):
    """
    Get all races for a specific season.
    
    Parameters:
    -----------
    year : int, optional
        The year of the F1 season. Defaults to current year.
        
    Returns:
    --------
    list : List of race events with basic information
    """
    if year is None:
        year = datetime.now().year
    
    try:
        schedule = f1.get_event_schedule(year)
        races = []
        
        for idx, event in schedule.iterrows():
            # Include all events
            races.append({
                'round': event['RoundNumber'],
                'event_name': event['EventName'],
                'location': event['Location'],
                'country': event['Country'],
                'date': str(event['EventDate']),
                'format': event['EventFormat']
            })
        
        return races
    except Exception as e:
        return {'error': f"Failed to retrieve season schedule: {str(e)}"}
