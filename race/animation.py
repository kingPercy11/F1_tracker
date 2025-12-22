import arcade
import fastf1 as f1
from datetime import timedelta
from pathlib import Path
import math

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
    """Racing car in animation"""
    
    def __init__(self, driver_name, team_color, position):
        self.driver_name = driver_name
        self.team_color = team_color
        self.position = position
        self.lap_data = []
        self.position_data = []
        self.tyre_compounds = []
        self.current_lap = 0
        self.lap_start_time = 0
        self.x = TRACK_X
        self.y = TRACK_Y + position * 30
        
    def update_position(self, time_elapsed):
        """Update car position"""
        if self.current_lap >= len(self.lap_data):
            return
        
        lap_time = self.lap_data[self.current_lap]
        time_in_lap = time_elapsed - self.lap_start_time
        
        if time_in_lap >= lap_time.total_seconds():
            self.current_lap += 1
            self.lap_start_time = time_elapsed
            
            if self.current_lap >= len(self.lap_data):
                return
            
            lap_time = self.lap_data[self.current_lap]
            time_in_lap = 0
        
        progress = time_in_lap / lap_time.total_seconds() if lap_time.total_seconds() > 0 else 0
        
        if self.current_lap < len(self.position_data) and len(self.position_data[self.current_lap]) > 0:
            positions = self.position_data[self.current_lap]
            idx = int(progress * (len(positions) - 1))
            idx = min(idx, len(positions) - 1)
            self.x, self.y = positions[idx]
        else:
            angle = progress * 2 * math.pi
            center_x = TRACK_X + TRACK_WIDTH / 2
            center_y = TRACK_Y + TRACK_HEIGHT / 2
            radius_x = TRACK_WIDTH / 2 - 50
            radius_y = TRACK_HEIGHT / 2 - 50
            
            self.x = center_x + radius_x * math.cos(angle)
            self.y = center_y + radius_y * math.sin(angle)


class RaceAnimation(arcade.Window):
    """Main race animation window"""
    
    def __init__(self, race_data):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.BLACK)
        
        self.race_data = race_data
        self.cars = []
        self.time_elapsed = 0
        self.is_paused = False
        self.speed_multiplier = 1
        self.track_map = []
        self.zoom_level = 1.0
        self.camera_x = 0
        self.camera_y = 0
        self.track_scale_params = None
        
        self.team_colors = {
            'Red Bull Racing': arcade.color.BLUE,
            'Mercedes': arcade.color.CYAN,
            'Ferrari': arcade.color.RED,
            'McLaren': arcade.color.ORANGE,
            'Alpine': arcade.color.PINK,
            'Aston Martin': arcade.color.GREEN,
            'Williams': arcade.color.LIGHT_BLUE,
            'AlphaTauri': arcade.color.DARK_GREEN,
            'Alfa Romeo': arcade.color.DARK_RED,
            'Haas F1 Team': arcade.color.WHITE,
        }
        
        self.setup_race()
    
    def setup_race(self):
        """Initialize race cars data"""
        if not self.race_data or 'results' not in self.race_data or not self.race_data['results']:
            print("No race data available for animation")
            return
        
        try:
            year = self.race_data.get('year')
            round_num = self.race_data.get('round')
            race_format = self.race_data.get('format', 'conventional')
            
            if year and round_num:
                cache_dir = Path(__file__).parent.parent / 'cache' / str(year)
                if cache_dir.exists():
                    print(f"✓ Found cache directory for {year}")
                
                session_type = 'S' if 'sprint' in race_format.lower() else 'R'
                session_name = 'Sprint' if 'sprint' in race_format.lower() else 'Race'
                print(f"Loading position data for {year} Round {round_num} ({session_name})...")
                session = f1.get_session(year, round_num, session_type)
                
                try:
                    session.load(telemetry=True, laps=True, weather=False)
                    print(f"✓ Session data loaded successfully")
                except Exception as load_error:
                    print(f"⚠ Could not load session data: {load_error}")
                    raise
                
                try:
                    first_driver = session.laps.pick_driver(session.results['Abbreviation'].iloc[0])
                    if first_driver is not None and len(first_driver) > 0:
                        sample_lap = first_driver.pick_fastest()
                        if sample_lap is not None:
                            telemetry = sample_lap.get_telemetry()
                            if telemetry is not None and 'X' in telemetry and 'Y' in telemetry:
                                x_coords = telemetry['X'].values
                                y_coords = telemetry['Y'].values
                                
                                x_min, x_max = x_coords.min(), x_coords.max()
                                y_min, y_max = y_coords.min(), y_coords.max()
                                
                                x_range = x_max - x_min
                                y_range = y_max - y_min
                                
                                scale = min(TRACK_WIDTH / x_range, TRACK_HEIGHT / y_range) * 0.9
                                
                                self.track_scale_params = {
                                    'x_min': x_min, 'x_max': x_max,
                                    'y_min': y_min, 'y_max': y_max,
                                    'x_range': x_range, 'y_range': y_range,
                                    'scale': scale
                                }
                                
                                for i in range(len(x_coords)):
                                    x = TRACK_X + TRACK_WIDTH / 2 + (x_coords[i] - x_min - x_range / 2) * scale
                                    y = TRACK_Y + TRACK_HEIGHT / 2 + (y_coords[i] - y_min - y_range / 2) * scale
                                    self.track_map.append((x, y))
                                
                                print(f"✓ Track map loaded: {len(self.track_map)} points")
                except Exception as e:
                    print(f"⚠ Could not load track map: {e}")
                    self.track_map = []
                
                results = self.race_data['results']
                for idx, result in enumerate(results):
                    team = result.get('team', 'Unknown')
                    color = self.team_colors.get(team, arcade.color.WHITE)
                    
                    car = Car(
                        driver_name=result['driver'],
                        team_color=color,
                        position=idx
                    )
                    
                    driver_abbr = result['driver']
                    driver_laps = session.laps.pick_driver(driver_abbr)
                    
                    if driver_laps is not None and len(driver_laps) > 0:
                        for lap_num in range(len(driver_laps)):
                            lap = driver_laps.iloc[lap_num]
                            lap_time = lap['LapTime']
                            
                            # Handle formation lap (NaT time) - use estimated time
                            if lap_time is None or str(lap_time) in ['NaT', 'nan']:
                                # Use average lap time or default for formation lap
                                estimated_time = timedelta(seconds=100 + idx * 0.5)
                                car.lap_data.append(estimated_time)
                            else:
                                car.lap_data.append(lap_time)
                            
                            compound = lap.get('Compound', None)
                            if compound and str(compound) != 'nan':
                                car.tyre_compounds.append(str(compound))
                            else:
                                car.tyre_compounds.append('UNKNOWN')
                            
                            try:
                                telemetry = lap.get_telemetry()
                                if telemetry is not None and 'X' in telemetry and 'Y' in telemetry and self.track_scale_params:
                                    lap_positions = []
                                    x_coords = telemetry['X'].values
                                    y_coords = telemetry['Y'].values
                                    
                                    params = self.track_scale_params
                                    
                                    for i in range(len(x_coords)):
                                        x = TRACK_X + TRACK_WIDTH / 2 + (x_coords[i] - params['x_min'] - params['x_range'] / 2) * params['scale']
                                        y = TRACK_Y + TRACK_HEIGHT / 2 + (y_coords[i] - params['y_min'] - params['y_range'] / 2) * params['scale']
                                        lap_positions.append((x, y))
                                    
                                    car.position_data.append(lap_positions)
                                else:
                                    car.position_data.append([])
                            except:
                                car.position_data.append([])
                        
                        print(f"✓ Loaded {len(car.lap_data)} laps for {driver_abbr}")
                    else:
                        num_laps = self.race_data.get('race_data', {}).get('total_laps', 50)
                        base_time = 85 + idx * 1.5
                        for lap in range(int(num_laps)):
                            variation = (lap % 5) * 0.5 - 1
                            lap_time = timedelta(seconds=base_time + variation)
                            car.lap_data.append(lap_time)
                            car.position_data.append([])
                            car.tyre_compounds.append('UNKNOWN')
                            car.tyre_compounds.append('UNKNOWN')
                    
                    self.cars.append(car)
                
        except Exception as e:
            print(f"⚠ Error loading session data: {e}")
            print("Using fallback data...")
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
                    car.tyre_compounds.append('UNKNOWN')
                
                self.cars.append(car)
    
    def on_draw(self):
        """Render screen"""
        self.clear()
        
        center_x = SCREEN_WIDTH / 2
        center_y = SCREEN_HEIGHT / 2
        
        if len(self.track_map) > 0:
            scaled_points = []
            for x, y in self.track_map:
                scaled_x = center_x + (x - center_x) * self.zoom_level
                scaled_y = center_y + (y - center_y) * self.zoom_level
                scaled_points.append((scaled_x, scaled_y))
            scaled_points.append(scaled_points[0])
            arcade.draw_line_strip(scaled_points, arcade.color.WHITE, 5)
            
            if len(scaled_points) > 10:
                start_x, start_y = scaled_points[0]
                end_x, end_y = scaled_points[5]
                
                dx = end_x - start_x
                dy = end_y - start_y
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:
                    perp_x = -dy / length * 40 * self.zoom_level
                    perp_y = dx / length * 40 * self.zoom_level
                    
                    # Draw checkered flag pattern
                    square_size = 8 * self.zoom_level
                    rows = 5
                    cols = 2
                    
                    # Calculate direction along the perpendicular
                    norm_perp_x = perp_x / (40 * self.zoom_level)
                    norm_perp_y = perp_y / (40 * self.zoom_level)
                    
                    for row in range(rows):
                        for col in range(cols):
                            # Alternate colors in checkered pattern
                            is_white = (row + col) % 2 == 0
                            color = arcade.color.WHITE if is_white else arcade.color.BLACK
                            
                            # Calculate position for this square
                            offset_perp = (row - rows/2) * square_size
                            offset_parallel = (col - cols/2) * square_size
                            
                            # Position along perpendicular line
                            center_x = start_x + norm_perp_x * offset_perp
                            center_y = start_y + norm_perp_y * offset_perp
                            
                            # Offset parallel to perpendicular (slight depth)
                            parallel_x = -norm_perp_y * offset_parallel
                            parallel_y = norm_perp_x * offset_parallel
                            
                            center_x += parallel_x
                            center_y += parallel_y
                            
                            arcade.draw_lbwh_rectangle_filled(
                                center_x - square_size / 2,
                                center_y - square_size / 2,
                                square_size, square_size,
                                color
                            )
        else:
            track_center_x = TRACK_X + TRACK_WIDTH / 2
            track_center_y = TRACK_Y + TRACK_HEIGHT / 2
            
            points = []
            for i in range(100):
                angle = (i / 100) * 2 * math.pi
                x = track_center_x + (TRACK_WIDTH / 2) * math.cos(angle)
                y = track_center_y + (TRACK_HEIGHT / 2) * math.sin(angle)
                scaled_x = center_x + (x - center_x) * self.zoom_level
                scaled_y = center_y + (y - center_y) * self.zoom_level
                points.append((scaled_x, scaled_y))
            points.append(points[0])
            
            arcade.draw_line_strip(points, arcade.color.WHITE, 5)
            
            inner_points = []
            for i in range(100):
                angle = (i / 100) * 2 * math.pi
                x = track_center_x + (TRACK_WIDTH / 2 - 50) * math.cos(angle)
                y = track_center_y + (TRACK_HEIGHT / 2 - 50) * math.sin(angle)
                scaled_x = center_x + (x - center_x) * self.zoom_level
                scaled_y = center_y + (y - center_y) * self.zoom_level
                inner_points.append((scaled_x, scaled_y))
            inner_points.append(inner_points[0])
            
            arcade.draw_line_strip(inner_points, arcade.color.DARK_GRAY, 3)
        
        for car in self.cars:
            scaled_x = center_x + (car.x - center_x) * self.zoom_level
            scaled_y = center_y + (car.y - center_y) * self.zoom_level
            car_size = 15 * self.zoom_level
            
            arcade.draw_circle_filled(
                scaled_x, scaled_y,
                car_size,
                car.team_color
            )
            
            text_size = max(8, int(10 * self.zoom_level))
            arcade.draw_text(
                car.driver_name,
                scaled_x - 15 * self.zoom_level, scaled_y - 5 * self.zoom_level,
                arcade.color.WHITE,
                text_size,
                bold=True
            )
        
        arcade.draw_text(
            f"Race: {self.race_data.get('event_info', {}).get('event_name', 'Unknown')}",
            10, SCREEN_HEIGHT - 30,
            arcade.color.WHITE,
            14,
            bold=True
        )
        
        if self.cars:
            arcade.draw_text(
                f"Lap: {self.cars[0].current_lap + 1}",
                10, SCREEN_HEIGHT - 60,
                arcade.color.WHITE,
                14
            )
        
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
        
        list_x = SCREEN_WIDTH - 200
        list_y = SCREEN_HEIGHT - 50
        arcade.draw_text(
            "Position",
            list_x, list_y,
            arcade.color.YELLOW,
            12,
            bold=True
        )
        
        def get_car_position(car):
            if car.current_lap >= len(car.lap_data):
                return (car.current_lap, 1.0)
            lap_time = car.lap_data[car.current_lap]
            time_in_lap = self.time_elapsed - car.lap_start_time
            progress = time_in_lap / lap_time.total_seconds() if lap_time.total_seconds() > 0 else 0
            return (car.current_lap, progress)
        
        sorted_cars = sorted(self.cars, key=get_car_position, reverse=True)
        for idx, car in enumerate(sorted_cars):
            y_pos = list_y - 25 - (idx * 20)
            arcade.draw_text(
                f"{idx + 1}. {car.driver_name} - Lap {car.current_lap + 1}",
                list_x, y_pos,
                car.team_color,
                10
            )
            
            if car.current_lap < len(car.tyre_compounds):
                compound = car.tyre_compounds[car.current_lap]
                tyre_colors = {
                    'SOFT': arcade.color.RED,
                    'MEDIUM': arcade.color.YELLOW,
                    'HARD': arcade.color.WHITE,
                    'INTERMEDIATE': arcade.color.GREEN,
                    'WET': arcade.color.BLUE,
                    'UNKNOWN': arcade.color.GRAY
                }
                tyre_color = tyre_colors.get(compound, arcade.color.GRAY)
                tyre_text = compound[0] if compound != 'UNKNOWN' else '?'
                
                arcade.draw_circle_outline(
                    list_x + 145, y_pos + 5,
                    11,
                    tyre_color,
                    3,
                    num_segments=32
                )
                arcade.draw_text(
                    tyre_text,
                    list_x + 140, y_pos + 1,
                    tyre_color,
                    10,
                    bold=True
                )
        
        arcade.draw_text(
            f"Zoom: {self.zoom_level:.1f}x (+/- or Mouse Wheel)",
            10, 50,
            arcade.color.WHITE,
            12
        )
        
        legend_x = SCREEN_WIDTH - 200
        legend_y = 240
        arcade.draw_text(
            "Team Colors",
            legend_x, legend_y,
            arcade.color.YELLOW,
            12,
            bold=True
        )
        
        teams_in_race = set()
        for car in self.cars:
            for result in self.race_data['results']:
                if result['driver'] == car.driver_name:
                    teams_in_race.add(result.get('team', 'Unknown'))
                    break
        
        y_offset = legend_y - 20
        for team in sorted(teams_in_race):
            color = self.team_colors.get(team, arcade.color.WHITE)
            arcade.draw_circle_filled(legend_x + 10, y_offset, 5, color)
            arcade.draw_text(
                team[:15],
                legend_x + 20, y_offset - 5,
                arcade.color.WHITE,
                9
            )
            y_offset -= 18
    
    def on_update(self, delta_time):
        """Update game logic"""
        if self.is_paused:
            return
        
        self.time_elapsed += delta_time * self.speed_multiplier
        
        for car in self.cars:
            car.update_position(self.time_elapsed)
    
    def restart_race(self):
        """Restart race"""
        self.time_elapsed = 0
        self.is_paused = False
        
        for car in self.cars:
            car.current_lap = 0
            car.lap_start_time = 0
            car.x = TRACK_X
            car.y = TRACK_Y + car.position * 30
    
    def on_key_press(self, key, modifiers):
        """Handle key presses"""
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
        """Handle mouse scroll"""
        if scroll_y > 0:
            self.zoom_level = min(5.0, self.zoom_level + 0.1)
        elif scroll_y < 0:
            self.zoom_level = max(0.5, self.zoom_level - 0.1)


def animate_race(year, race_round, race_format='conventional'):
    """Create and run race animation"""
    from race.detail import get_race_details
    
    print(f"\n🏎️  Loading race data for {year} Round {race_round}...")
    race_data = get_race_details(year, race_round, race_format)
    
    if 'error' in race_data:
        print(f"❌ Error loading race: {race_data['error']}")
        return
    
    if not race_data.get('results'):
        print("❌ No race results available for animation. Race may not have been completed yet.")
        return
    
    race_data['year'] = year
    race_data['round'] = race_round
    race_data['format'] = race_format
    
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
    animate_race(2024, 1)
