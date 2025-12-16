import arcade
import fastf1 as f1
from datetime import timedelta
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
        self.lap_data = []
        self.current_lap = 0
        self.progress = 0  # 0 to 1 representing position on current lap
        self.x = TRACK_X
        self.y = TRACK_Y + position * 30
        
    def update_position(self, time_elapsed):
        """Update car position based on elapsed time."""
        if self.current_lap >= len(self.lap_data):
            return
        
        lap_time = self.lap_data[self.current_lap]
        self.progress = time_elapsed / lap_time.total_seconds()
        
        if self.progress >= 1.0:
            self.progress = 0
            self.current_lap += 1
            
        # Move car around the track (simplified oval)
        angle = self.progress * 2 * math.pi
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
        self.speed_multiplier = 100  # Speed up animation
        
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
        
        # Create cars for top drivers
        results = self.race_data['results']
        num_laps = self.race_data.get('race_data', {}).get('total_laps', 50)
        if not num_laps or num_laps == 0:
            num_laps = 50
        
        for idx, result in enumerate(results[:10]):
            team = result.get('team', 'Unknown')
            color = self.team_colors.get(team, arcade.color.WHITE)
            
            car = Car(
                driver_name=result['driver'],
                team_color=color,
                position=idx
            )
            
            # Generate realistic lap times based on position
            # Faster cars (lower position) have faster lap times
            base_time = 85 + idx * 1.5  # Base lap time in seconds
            for lap in range(int(num_laps)):
                # Add some variation to lap times
                variation = (lap % 5) * 0.5 - 1
                lap_time = timedelta(seconds=base_time + variation)
                car.lap_data.append(lap_time)
            
            self.cars.append(car)
    
    def on_draw(self):
        """Render the screen."""
        self.clear()
        
        # Draw track (outer boundary) using lines
        track_center_x = TRACK_X + TRACK_WIDTH / 2
        track_center_y = TRACK_Y + TRACK_HEIGHT / 2
        
        # Draw outer track oval
        points = []
        for i in range(100):
            angle = (i / 100) * 2 * math.pi
            x = track_center_x + (TRACK_WIDTH / 2) * math.cos(angle)
            y = track_center_y + (TRACK_HEIGHT / 2) * math.sin(angle)
            points.append((x, y))
        points.append(points[0])  # Close the loop
        
        arcade.draw_line_strip(points, arcade.color.WHITE, 5)
        
        # Draw inner track line
        inner_points = []
        for i in range(100):
            angle = (i / 100) * 2 * math.pi
            x = track_center_x + (TRACK_WIDTH / 2 - 50) * math.cos(angle)
            y = track_center_y + (TRACK_HEIGHT / 2 - 50) * math.sin(angle)
            inner_points.append((x, y))
        inner_points.append(inner_points[0])
        
        arcade.draw_line_strip(inner_points, arcade.color.DARK_GRAY, 3)
        
        # Draw cars
        for car in self.cars:
            # Draw car as a circle instead
            arcade.draw_circle_filled(
                car.x, car.y,
                15,
                car.team_color
            )
            
            # Draw driver abbreviation
            arcade.draw_text(
                car.driver_name,
                car.x - 15, car.y - 5,
                arcade.color.WHITE,
                10,
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
            "SPACE: Pause/Resume | ESC: Exit",
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
        
        sorted_cars = sorted(self.cars, key=lambda c: (c.current_lap, c.progress), reverse=True)
        for idx, car in enumerate(sorted_cars):
            arcade.draw_text(
                f"{idx + 1}. {car.driver_name} - Lap {car.current_lap}",
                list_x, list_y - 25 - (idx * 20),
                car.team_color,
                10
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
        
        # Reset timer for each lap
        if self.cars and self.cars[0].progress < 0.01 and self.time_elapsed > 1:
            self.time_elapsed = 0
    
    def on_key_press(self, key, modifiers):
        """Handle key presses."""
        if key == arcade.key.SPACE:
            self.is_paused = not self.is_paused
        elif key == arcade.key.ESCAPE:
            arcade.close_window()
        elif key == arcade.key.UP:
            self.speed_multiplier = min(1000, self.speed_multiplier + 10)
        elif key == arcade.key.DOWN:
            self.speed_multiplier = max(10, self.speed_multiplier - 10)


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
    
    print("✅ Race data loaded successfully!")
    print(f"🏁 {race_data['event_info']['event_name']}")
    print(f"   {len(race_data['results'])} drivers")
    print("\n🎮 Starting race animation...")
    print("\nControls:")
    print("  SPACE       - Pause/Resume")
    print("  UP/DOWN     - Adjust speed (10x-1000x)")
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
