import fastf1 as f1
from race.detail import get_race_details, get_current_season_races
from datetime import datetime

def select_year():
    """Allow user to select a year for F1 season."""
    current_year = datetime.now().year
    print("\n" + "="*60)
    print("F1 RACE TRACKER - Year Selection")
    print("="*60)
    
    while True:
        try:
            print(f"\nEnter a year (1950-{current_year}) or press Enter for current year ({current_year}): ")
            year_input = input().strip()
            
            if year_input == "":
                return current_year
            
            year = int(year_input)
            if 1950 <= year <= current_year:
                return year
            else:
                print(f"Invalid year. Please enter a year between 1950 and {current_year}.")
        except ValueError:
            print("Invalid input. Please enter a valid year.")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            return None

def display_race_menu(year):
    """Display a menu of races for user to select from."""
    print("\n" + "="*60)
    print(f"F1 RACE TRACKER - {year} Season")
    print("="*60)
    
    # Get all races for selected year
    races = get_current_season_races(year)
    
    if 'error' in races:
        print(f"Error: {races['error']}")
        return
    
    # Display races
    print("\nSelect a race to view details:\n")
    for i, race in enumerate(races, 1):
        format_badge = f" [{race.get('format', 'conventional').upper()}]" if race.get('format') != 'conventional' else ""
        print(f"{i:2d}. Round {race['round']:2d} - {race['event_name']} ({race['country']}){format_badge} - {race['date']}")
    
    print(f"\n0. Back to year selection")
    
    # Get user input
    while True:
        try:
            choice = int(input(f"\nEnter your choice (0-{len(races)}): "))
            if 1 <= choice <= len(races):
                return races[choice - 1]
            elif choice == 0:
                return None
            else:
                print(f"Invalid choice. Please enter a number between 0 and {len(races)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            return None

def display_race_details(race_info, year):
    """Display detailed information about the selected race."""
    print("\n" + "="*60)
    print(f"RACE DETAILS")
    print("="*60)
    
    details = get_race_details(year, race_info['round'])
    
    if 'error' in details:
        print(f"\nError: {details['error']}")
        return
    
    # Display event information
    event = details['event_info']
    print(f"\nRace: {event['event_name']}")
    print(f"Location: {event['location']}, {event['country']}")
    print(f"Round: {event['round']}")
    print(f"Date: {event['event_date']}")
    print(f"Status: {details['session_status'].upper()}")
    
    # Display race results if available
    if details['results']:
        print("\n" + "-"*60)
        print("RACE RESULTS")
        print("-"*60)
        print(f"{'Pos':<5} {'Driver':<20} {'Team':<25} {'Time':<15} {'Pts':<5}")
        print("-"*60)
        
        for result in details['results'][:10]:  # Show top 10
            pos = result['position'] if result['position'] else 'DNF'
            print(f"{pos:<5} {result['full_name']:<20} {result['team']:<25} {result['time']:<15} {result['points']:<5}")
        
        if len(details['results']) > 10:
            print(f"\n... and {len(details['results']) - 10} more drivers")
    
    elif details['session_status'] == 'upcoming':
        print("\n⏳ This race hasn't taken place yet.")
    
    elif details['session_status'] == 'data_unavailable':
        print("\n⚠️  Race data is not yet available.")
        if 'error' in event:
            print(f"   {event['error']}")
    
    print("\n" + "="*60)

def main():
    """Main program loop."""
    while True:
        # Select year
        year = select_year()
        
        if year is None:
            break
        
        # Select and view races for the chosen year
        while True:
            selected_race = display_race_menu(year)
            
            if selected_race is None:
                break
            
            display_race_details(selected_race, year)
            
            # Ask if user wants to animate the race
            print("\n")
            animate_choice = input("Animate this race? (y/n): ").lower()
            if animate_choice == 'y':
                try:
                    from race.animation import animate_race
                    animate_race(year, selected_race['round'])
                except ImportError:
                    print("⚠️  Arcade library not installed. Install with: pip install arcade")
                except Exception as e:
                    print(f"⚠️  Animation error: {e}")
            
            # Ask if user wants to see another race
            print("\n")
            continue_choice = input("View another race? (y/n): ").lower()
            if continue_choice != 'y':
                break
        
        # Ask if user wants to select a different year
        print("\n")
        year_choice = input("Select a different year? (y/n): ").lower()
        if year_choice != 'y':
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()
