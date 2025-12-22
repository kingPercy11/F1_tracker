import arcade
import fastf1 as f1
from datetime import timedelta
from pathlib import Path
import math

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
SCREEN_TITLE = "F1 Race Animation"
TRACK_WIDTH = 900
TRACK_HEIGHT = 600
TRACK_X = 150
TRACK_Y = 100
CAR_WIDTH = 30
CAR_HEIGHT = 15


class Car:
    """Represents a racing car in the animation."""
    
    def __init__(self, driver_name, team_color, position):
        self.driver_name = driver_name
        self.team_color = team_color
        self.position = position
        self.lap_data = []  # List of lap times
        self.position_data = []  # List of (x, y) coordinates for each lap
        self.current_lap = 0
        self.lap_start_time = 0  # When current lap started
        self.x = TRACK_X
        self.y = TRACK_Y + position * 30
        
    def update_position(self, time_elapsed):
        """Update car position based on elapsed time."""
        if self.current_lap >= len(self.lap_data):
            return
        
        # Get current lap time
        lap_time = self.lap_data[self.current_lap]
        time_in_lap = time_elapsed - self.lap_start_time
        
        # Check if we need to advance to next lap
        if time_in_lap >= lap_time.total_seconds():
            self.current_lap += 1
            self.lap_start_time = time_elapsed
            
            if self.current_lap >= len(self.lap_data):
                return
            
            lap_time = self.lap_data[self.current_lap]
            time_in_lap = 0
        
        # Calculate progress through current lap (0 to 1)
        progress = time_in_lap / lap_time.total_seconds() if lap_time.total_seconds() > 0 else 0
        
        # Get position data for current lap
        if self.current_lap < len(self.position_data) and len(self.position_data[self.current_lap]) > 0:
            positions = self.position_data[self.current_lap]
            # Interpolate position based on progress
            idx = int(progress * (len(positions) - 1))
            idx = min(idx, len(positions) - 1)
            self.x, self.y = positions[idx]
        else:
            # Fallback to oval if no position data
            angle = progress * 2 * math.pi
            center_x = TRACK_X + TRACK_WIDTH / 2
            center_y = TRACK_Y + TRACK_HEIGHT / 2
            radius_x = TRACK_WIDTH / 2 - 50
            radius_y = TRACK_HEIGHT / 2 - 50
            
            self.x = center_x + radius_x * math.cos(angle)
            self.y = center_y + radius_y * math.sin(angle)


class RaceAnimation(arcade.Window):
    """Main application class for race animation."""
    
    def __init__(self, race_data):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.BLACK)
        
        self.race_data = race_data
        self.cars = []
        self.time_elapsed = 0
        self.is_paused = False
        self.speed_multiplier = 10  # Speed up animation
        self.track_map = []  # Store track coordinates
        self.zoom_level = 1.0  # Zoom level (1.0 = normal, >1 = zoomed in, <1 = zoomed out)
        self.camera_x = 0  # Camera offset X
        self.camera_y = 0  # Camera offset Y
        
        # Team colors (simplified)
        self.team_colors = {
            'Red Bull Racing': arcade.color.BLUE,
            'Mercedes': arcade.color.CYAN,
            'Ferrari': arcade.color.RED,
            'McLaren': arcade.color.ORANGE,
            'Alpine': arcade.color.PINK,
            'Aston Martin': arcade.color.GREEN,
            'Williams': arcade.color.LIGHT_BLUE,
            'AlphaTauri': arcade.color.NAVY_BLUE,
            'Alfa Romeo': arcade.color.DARK_RED,
            'Haas F1 Team': arcade.color.WHITE,
        }
        
        self.setup_race()
    
    def setup_race(self):
        """Initialize race cars with their lap data."""
        if not self.race_data or 'results' not in self.race_data or not self.race_data['results']:
            print("No race data available for animation")
            return
        
        # Load race session to get position data
        try:
            year = self.race_data.get('year')
            round_num = self.race_data.get('round')
            
            if year and round_num:
                # Check if data is available in cache
                cache_dir = Path(__file__).parent.parent / 'cache' / str(year)
                if cache_dir.exists():
                    print(f"✓ Found cache directory for {year}")
                
                print(f"Loading position data for {year} Round {round_num}...")
                session = f1.get_session(year, round_num, 'R')
                
                # Load with cache-first approach
                try:
                    session.load(telemetry=True, laps=True, weather=False)
                    print(f"✓ Session data loaded successfully")
                except Exception as load_error:
                    print(f"⚠ Could not load session data: {load_error}")
                    raise
                
                # Get track position data for map
                try:
                    # Get position data from any driver's lap
                    first_driver = session.laps.pick_driver(session.results['Abbreviation'].iloc[0])
                    if first_driver is not None and len(first_driver) > 0:
                        sample_lap = first_driver.pick_fastest()
                        if sample_lap is not None:
                            telemetry = sample_lap.get_telemetry()
                            if telemetry is not None and 'X' in telemetry and 'Y' in telemetry:
                                # Scale track coordinates to fit screen
                                x_coords = telemetry['X'].values
                                y_coords = telemetry['Y'].values
                                
                                # Scale to fit track area
                                x_min, x_max = x_coords.min(), x_coords.max()
                                y_min, y_max = y_coords.min(), y_coords.max()
                                
                                x_range = x_max - x_min
                                y_range = y_max - y_min
                                
                                scale = min(TRACK_WIDTH / x_range, TRACK_HEIGHT / y_range) * 0.9
                                
                                for i in range(len(x_coords)):
                                    x = TRACK_X + TRACK_WIDTH / 2 + (x_coords[i] - x_min - x_range / 2) * scale
                                    y = TRACK_Y + TRACK_HEIGHT / 2 + (y_coords[i] - y_min - y_range / 2) * scale
                                    self.track_map.append((x, y))
                                
                                print(f"✓ Track map loaded: {len(self.track_map)} points")
                except Exception as e:
                    print(f"⚠ Could not load track map: {e}")
                    self.track_map = []
                
                # Create cars with actual lap data
                results = self.race_data['results']
                for idx, result in enumerate(results):
                    team = result.get('team', 'Unknown')
                    color = self.team_colors.get(team, arcade.color.WHITE)
                    
                    car = Car(
                        driver_name=result['driver'],
                        team_color=color,
                        position=idx
                    )
                    
                    # Get driver's laps
                    driver_abbr = result['driver']
                    driver_laps = session.laps.pick_driver(driver_abbr)
                    
                    if driver_laps is not None and len(driver_laps) > 0:
                        for lap_num in range(len(driver_laps)):
                            lap = driver_laps.iloc[lap_num]
                            lap_time = lap['LapTime']
                            
                            if lap_time is not None:
                                car.lap_data.append(lap_time)
                                
                                # Get position data for this lap
                                try:
                                    telemetry = lap.get_telemetry()
                                    if telemetry is not None and 'X' in telemetry and 'Y' in telemetry:
                                        lap_positions = []
                                        x_coords = telemetry['X'].values
                                        y_coords = telemetry['Y'].values
                                        
                                        x_min, x_max = x_coords.min(), x_coords.max()
                                        y_min, y_max = y_coords.min(), y_coords.max()
                                        x_range = x_max - x_min if x_max - x_min > 0 else 1
                                        y_range = y_max - y_min if y_max - y_min > 0 else 1
                                        scale = min(TRACK_WIDTH / x_range, TRACK_HEIGHT / y_range) * 0.9
                                        
                                        for i in range(len(x_coords)):
                                            x = TRACK_X + TRACK_WIDTH / 2 + (x_coords[i] - x_min - x_range / 2) * scale
                                            y = TRACK_Y + TRACK_HEIGHT / 2 + (y_coords[i] - y_min - y_range / 2) * scale
                                            lap_positions.append((x, y))
                                        
                                        car.position_data.append(lap_positions)
                                    else:
                                        car.position_data.append([])
                                except:
                                    car.position_data.append([])
                            else:
                                # Fallback lap time if missing
                                base_time = 85 + idx * 1.5
                                car.lap_data.append(timedelta(seconds=base_time))
                                car.position_data.append([])
                        
                        print(f"✓ Loaded {len(car.lap_data)} laps for {driver_abbr}")
                    else:
                        # Fallback: generate estimated lap times
                        num_laps = self.race_data.get('race_data', {}).get('total_laps', 50)
                        base_time = 85 + idx * 1.5
                        for lap in range(int(num_laps)):
                            variation = (lap % 5) * 0.5 - 1
                            lap_time = timedelta(seconds=base_time + variation)
                            car.lap_data.append(lap_time)
                            car.position_data.append([])
                    
                    self.cars.append(car)
                
        except Exception as e:
            print(f"⚠ Error loading session data: {e}")
            print("Using fallback data...")
            # Fallback to original simple implementation
            results = self.race_data['results']
            num_laps = self.race_data.get('race_data', {}).get('total_laps', 50)
            if not num_laps or num_laps == 0:
                num_laps = 50
            
            for idx, result in enumerate(results):
                team = result.get('team', 'Unknown')
                color = self.team_colors.get(team, arcade.color.WHITE)
                
                car = Car(
                    driver_name=result['driver'],
                    team_color=color,
                    position=idx
                )
                
                base_time = 85 + idx * 1.5
                for lap in range(int(num_laps)):
                    variation = (lap % 5) * 0.5 - 1
                    lap_time = timedelta(seconds=base_time + variation)
                    car.lap_data.append(lap_time)
                    car.position_data.append([])
                
                self.cars.append(car)
    
    def on_draw(self):
        """Render the screen."""
        self.clear()
        
        # Apply zoom transformation by scaling around center
        center_x = SCREEN_WIDTH / 2
        center_y = SCREEN_HEIGHT / 2
        
        # Draw track using actual map data or fallback to oval
        if len(self.track_map) > 0:
            # Draw actual track with zoom
            scaled_points = []
            for x, y in self.track_map:
                # Scale around center
                scaled_x = center_x + (x - center_x) * self.zoom_level
                scaled_y = center_y + (y - center_y) * self.zoom_level
                scaled_points.append((scaled_x, scaled_y))
            scaled_points.append(scaled_points[0])  # Close the loop
            arcade.draw_line_strip(scaled_points, arcade.color.WHITE, 5)
        else:
            # Fallback to oval with zoom
            track_center_x = TRACK_X + TRACK_WIDTH / 2
            track_center_y = TRACK_Y + TRACK_HEIGHT / 2
            
            # Draw outer track oval
            points = []
            for i in range(100):
                angle = (i / 100) * 2 * math.pi
                x = track_center_x + (TRACK_WIDTH / 2) * math.cos(angle)
                y = track_center_y + (TRACK_HEIGHT / 2) * math.sin(angle)
                # Apply zoom
                scaled_x = center_x + (x - center_x) * self.zoom_level
                scaled_y = center_y + (y - center_y) * self.zoom_level
                points.append((scaled_x, scaled_y))
            points.append(points[0])  # Close the loop
            
            arcade.draw_line_strip(points, arcade.color.WHITE, 5)
            
            # Draw inner track line
            inner_points = []
            for i in range(100):
                angle = (i / 100) * 2 * math.pi
                x = track_center_x + (TRACK_WIDTH / 2 - 50) * math.cos(angle)
                y = track_center_y + (TRACK_HEIGHT / 2 - 50) * math.sin(angle)
                # Apply zoom
                scaled_x = center_x + (x - center_x) * self.zoom_level
                scaled_y = center_y + (y - center_y) * self.zoom_level
                inner_points.append((scaled_x, scaled_y))
            inner_points.append(inner_points[0])
            
            arcade.draw_line_strip(inner_points, arcade.color.DARK_GRAY, 3)
        
        # Draw cars
        for car in self.cars:
            # Apply zoom to car position
            scaled_x = center_x + (car.x - center_x) * self.zoom_level
            scaled_y = center_y + (car.y - center_y) * self.zoom_level
            car_size = 15 * self.zoom_level
            
            # Draw car as a circle
            arcade.draw_circle_filled(
                scaled_x, scaled_y,
                car_size,
                car.team_color
            )
            
            # Draw driver abbreviation
            text_size = max(8, int(10 * self.zoom_level))
            arcade.draw_text(
                car.driver_name,
                scaled_x - 15 * self.zoom_level, scaled_y - 5 * self.zoom_level,
                arcade.color.WHITE,
                text_size,
                bold=True
            )
        
        # Draw race info
        arcade.draw_text(
            f"Race: {self.race_data.get('event_info', {}).get('event_name', 'Unknown')}",
            10, SCREEN_HEIGHT - 30,
            arcade.color.WHITE,
            14,
            bold=True
        )
        
        # Draw lap info
        if self.cars:
            arcade.draw_text(
                f"Lap: {self.cars[0].current_lap + 1}",
                10, SCREEN_HEIGHT - 60,
                arcade.color.WHITE,
                14
            )
        
        # Draw speed control
        arcade.draw_text(
            f"Speed: {self.speed_multiplier}x (Arrow Up/Down to adjust)",
            10, 30,
            arcade.color.WHITE,
            12
        )
        
        arcade.draw_text(
            "SPACE: Pause/Resume | R: Restart | +/-: Zoom | ESC: Exit",
            10, 10,
            arcade.color.GRAY,
            10
        )
        
        # Draw position list
        list_x = SCREEN_WIDTH - 200
        list_y = SCREEN_HEIGHT - 50
        arcade.draw_text(
            "Position",
            list_x, list_y,
            arcade.color.YELLOW,
            12,
            bold=True
        )
        
        # Sort cars by lap and progress through current lap
        def get_car_position(car):
            if car.current_lap >= len(car.lap_data):
                return (car.current_lap, 1.0)
            lap_time = car.lap_data[car.current_lap]
            time_in_lap = self.time_elapsed - car.lap_start_time
            progress = time_in_lap / lap_time.total_seconds() if lap_time.total_seconds() > 0 else 0
            return (car.current_lap, progress)
        
        sorted_cars = sorted(self.cars, key=get_car_position, reverse=True)
        for idx, car in enumerate(sorted_cars):
            arcade.draw_text(
                f"{idx + 1}. {car.driver_name} - Lap {car.current_lap + 1}",
                list_x, list_y - 25 - (idx * 20),
                car.team_color,
                10
            )
        
        # Draw zoom level info
        arcade.draw_text(
            f"Zoom: {self.zoom_level:.1f}x (+/- or Mouse Wheel)",
            10, 50,
            arcade.color.WHITE,
            12
        )
    
    def on_update(self, delta_time):
        """Update game logic."""
        if self.is_paused:
            return
        
        # Update time with speed multiplier
        self.time_elapsed += delta_time * self.speed_multiplier
        
        # Update all cars
        for car in self.cars:
            car.update_position(self.time_elapsed)
    
    def restart_race(self):
        """Restart the race animation from the beginning."""
        self.time_elapsed = 0
        self.is_paused = False
        
        # Reset all cars
        for car in self.cars:
            car.current_lap = 0
            car.lap_start_time = 0
            car.x = TRACK_X
            car.y = TRACK_Y + car.position * 30
    
    def on_key_press(self, key, modifiers):
        """Handle key presses."""
        if key == arcade.key.SPACE:
            self.is_paused = not self.is_paused
        elif key == arcade.key.R:
            self.restart_race()
        elif key == arcade.key.ESCAPE:
            arcade.close_window()
        elif key == arcade.key.UP:
            self.speed_multiplier = min(1000, self.speed_multiplier + 10)
        elif key == arcade.key.DOWN:
            self.speed_multiplier = max(10, self.speed_multiplier - 10)
        elif key == arcade.key.PLUS or key == arcade.key.EQUAL:
            self.zoom_level = min(5.0, self.zoom_level + 0.2)
        elif key == arcade.key.MINUS:
            self.zoom_level = max(0.5, self.zoom_level - 0.2)
        elif key == arcade.key.NUM_0 or key == arcade.key.KEY_0:
            self.zoom_level = 1.0
            self.camera_x = 0
            self.camera_y = 0
    
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """Handle mouse wheel scrolling for zoom."""
        if scroll_y > 0:
            self.zoom_level = min(5.0, self.zoom_level + 0.1)
        elif scroll_y < 0:
            self.zoom_level = max(0.5, self.zoom_level - 0.1)


def animate_race(year, race_round):
    """
    Create and run an animated visualization of a race.
    
    Parameters:
    -----------
    year : int
        The year of the race
    race_round : int
        The round number of the race
    """
    from race.detail import get_race_details
    
    print(f"\n🏎️  Loading race data for {year} Round {race_round}...")
    race_data = get_race_details(year, race_round)
    
    if 'error' in race_data:
        print(f"❌ Error loading race: {race_data['error']}")
        return
    
    if not race_data.get('results'):
        print("❌ No race results available for animation. Race may not have been completed yet.")
        return
    
    # Add year and round to race_data for session loading
    race_data['year'] = year
    race_data['round'] = race_round
    
    print("✅ Race data loaded successfully!")
    print(f"🏁 {race_data['event_info']['event_name']}")
    print(f"   {len(race_data['results'])} drivers")
    print("\n🎮 Starting race animation...")
    print("\nControls:")
    print("  SPACE       - Pause/Resume")
    print("  R           - Restart race")
    print("  UP/DOWN     - Adjust speed (10x-1000x)")
    print("  +/-         - Zoom in/out")
    print("  Mouse Wheel - Zoom in/out")
    print("  0           - Reset zoom")
    print("  ESC         - Exit")
    print("\n👀 Check for the animation window - it may open behind other windows!")
    print("-" * 60)
    
    try:
        window = RaceAnimation(race_data)
        arcade.run()
    except Exception as e:
        print(f"\n❌ Animation error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Test animation with 2024 season
    animate_race(2024, 1)
