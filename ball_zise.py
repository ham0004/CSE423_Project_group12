from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time
import math

# Game Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
GRID_LENGTH = 600

# Size Platform Constants
MIN_PLATFORM_RADIUS = 20
MAX_PLATFORM_RADIUS = 50
MIN_BALL_RADIUS = 10
MAX_BALL_RADIUS = 40
SIZE_CHANGE_AMOUNT = 5

# Game States
START_SCREEN = 0
GAME_RUNNING = 1
GAME_PAUSED = 2
LEVEL_COMPLETE = 3
GAME_OVER = 4
game_state = START_SCREEN

# Player Ball
main_ball_pos = [0, 0, 4]  # x, y, z
main_ball_radius = 20
main_ball_target_x = 0
main_ball_y = 0
main_ball_rot_angle = 0
main_ball_color = [1.0, 0.4, 0.0]  # Orange
jumping = False
falling = False
jumping_height = 0

CAMERA_THIRD_PERSON = 0    # Default third-person view
CAMERA_FIRST_PERSON = 1    # First-person view from ball
CAMERA_SIDE_VIEW = 2       # Side view of the track
current_camera = CAMERA_THIRD_PERSON  # Make sure this line exists

max_jump_height = 75

# Player Lives System
lives = 3
invincible = False
invincible_time = 0
invincible_duration = 2  # Seconds of invincibility after respawn
respawn_pos = [0, 0, 4]  # Position where player respawns


# Camera settings
camera_pos = (0, 120, 200)
fovY = 60
camera_positions = {
    CAMERA_THIRD_PERSON: (0, 120, 200),    # Default third-person view
    CAMERA_FIRST_PERSON: (0, 30, 30),      # First-person view (relative to ball)
    CAMERA_SIDE_VIEW: (200, 50, 0)         # Side view
}

# Add these variables right after the camera_positions declaration:
camera_height_offset = 0  # For up/down movement
camera_rotation_angle = 0  # For left/right rotation (in degrees)

# Road and background
road_offset = 0
stars_positions = []
for _ in range(100):
    x = random.uniform(-2, 2)
    y = random.uniform(-3, 3)
    stars_positions.append((x, y))

# Game parameters
score = 0
level = 1
last_update_time = 0
game_speed = 40  # milliseconds between updates
direction = "STOP"

speed_multiplier = 1.0
base_game_speed = 40  # Store the original game speed
speed_increase_threshold = 10  # Increase speed every 10 points

# Colors available in the game (R, G, B)
colors = [
    [1.0, 0.4, 0.0],  # Orange
    [1.0, 0.0, 0.8],  # Pink
    [0.3, 0.4, 1.0]   # Blue
]

# Color Barriers
class ColorBarrier:
    def __init__(self, z_pos, color):
        self.x = 0
        self.y = 0
        self.z = z_pos
        self.color = color
        self.active = True
        self.width = 240
        self.height = 40
        self.depth = 20

    def draw(self):
        if self.active:
            glPushMatrix()
            glColor3f(self.color[0], self.color[1], self.color[2])
            glTranslatef(self.x, self.y, self.z)
            glScalef(self.width/40, self.height/40, self.depth/40)
            glutSolidCube(40)
            glPopMatrix()

# List of color barriers
color_barriers = []

# Wall
wall_pos_z = -400
show_wall = False
wall_color = colors[2]  # Initial wall color (blue)

# Finish line
finish_line_z = -2500
level_up = False

# Balls
class Ball:
    def __init__(self, x, y, z, radius, color):
        self.x = x
        self.y = y
        self.z = z
        self.radius = radius
        self.color = color

    def draw(self):
        glPushMatrix()
        glColor3f(self.color[0], self.color[1], self.color[2])
        glTranslatef(self.x, self.y, self.z)
        # Replace glutSolidSphere with gluSphere
        gluSphere(gluNewQuadric(), self.radius, 20, 15)
        glPopMatrix()

# Speed Cube class for speed modification
class SpeedCube:
    def __init__(self, x, z, cube_type):
        self.x = x
        self.y = -30  # Position on the floor
        self.z = z
        self.width = 20
        self.height = 5
        self.depth = 20
        self.cube_type = cube_type  # 'speed_up' or 'speed_down'
        self.color = [1.0, 0.0, 0.0] if cube_type == 'speed_up' else [0.0, 0.0, 1.0]  # Red for speed up, Blue for speed down
        self.active = True

    def draw(self):
        if self.active:
            glPushMatrix()
            glColor3f(self.color[0], self.color[1], self.color[2])
            glTranslatef(self.x, self.y, self.z)
            glScalef(self.width/40, self.height/40, self.depth/40)
            glutSolidCube(40)
            glPopMatrix()

# Initialize speed cubes list
speed_cubes = []

# Initialize moving balls list
balls = []
initial_ball = Ball(0, 0, -600, 20, colors[0])
balls.append(initial_ball)

# Size Platform class for size modification
class SizePlatform:
    def __init__(self, x, z, platform_type):
        self.x = x
        self.y = -30  # Position on the floor
        self.z = z
        self.platform_type = platform_type  # 'increase' or 'decrease'
        self.radius = MAX_PLATFORM_RADIUS if platform_type == 'increase' else MIN_PLATFORM_RADIUS
        self.color = [0.0, 1.0, 0.0] if platform_type == 'increase' else [1.0, 0.0, 0.0]  # Green for increase, Red for decrease
        self.active = True

    def draw(self):
        if self.active:
            glPushMatrix()
            glColor3f(self.color[0], self.color[1], self.color[2])
            glTranslatef(self.x, self.y, self.z)
            # Draw a flat circle using GL_TRIANGLE_FAN
            glBegin(GL_TRIANGLE_FAN)
            glVertex3f(0, 1, 0)  # Center point
            for i in range(21):  # 20 segments for smooth circle
                angle = 2.0 * 3.14159 * i / 20
                glVertex3f(self.radius * math.cos(angle), 1, self.radius * math.sin(angle))
            glEnd()
            glPopMatrix()

# Initialize size platforms list
size_platforms = []

def spawn_color_barrier():
    """Spawn a new color barrier with random color"""
    global color_barriers

    # Choose a color different from main ball's current color
    available_colors = [c for c in colors if c != main_ball_color]
    barrier_color = random.choice(available_colors)

    # Create new barrier
    new_barrier = ColorBarrier(-800, barrier_color)
    color_barriers.append(new_barrier)

def spawn_speed_cube():
    """Spawn a new speed cube with random type"""
    global speed_cubes
    
    # Randomly choose cube type (speed up or speed down)
    cube_type = random.choice(['speed_up', 'speed_down'])
    
    # Random x position (-80, 0, or 80)
    x_pos = random.choice([-80, 0, 80])
    
    # Create new speed cube
    new_cube = SpeedCube(x_pos, -800, cube_type)
    speed_cubes.append(new_cube)

def change_wall_color():
    """Change wall color to a random color different from the main ball"""
    global wall_color, colors, main_ball_color
    available_colors = [c for c in colors if c != main_ball_color]
    wall_color = random.choice(available_colors)

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    """Draw text on screen using bitmap characters"""
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    # Set up an orthographic projection for 2D text
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Draw text at specified position
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    # Restore original matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_text_center(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    """Draw centered text on screen"""
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    # Set up an orthographic projection for 2D text
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Calculate text width for centering
    text_width = 0
    for ch in text:
        text_width += glutBitmapWidth(font, ord(ch))

    # Draw centered text
    glRasterPos2f(x - text_width/2, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    # Restore original matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_rectangle(x1, y1, x2, y2):
    """Draw a 2D rectangle from (x1,y1) to (x2,y2)"""
    glBegin(GL_QUADS)
    glVertex2f(x1, y1)
    glVertex2f(x2, y1)
    glVertex2f(x2, y2)
    glVertex2f(x1, y2)
    glEnd()

def draw_road():
    """Draw the road"""
    glPushMatrix()
    glColor3f(0.5, 0.5, 0.5)  # Gray road
    glTranslatef(0, -30, 0)

    # Draw road segments with lines
    glBegin(GL_QUADS)
    glVertex3f(-120, 0, -1200)
    glVertex3f(120, 0, -1200)
    glVertex3f(120, 0, 100)
    glVertex3f(-120, 0, 100)
    glEnd()

    # Road markings
    glColor3f(1.0, 1.0, 1.0)  # White markings
    for z in range(-1200, 100, 100):
        z_pos = z + road_offset % 100
        glBegin(GL_QUADS)
        glVertex3f(-5, 1, z_pos)
        glVertex3f(5, 1, z_pos)
        glVertex3f(5, 1, z_pos+30)
        glVertex3f(-5, 1, z_pos+30)
        glEnd()

    glPopMatrix()

def switch_camera():
    """Switch to the next camera preset"""
    global current_camera
    current_camera = (current_camera + 1) % len(camera_positions)

def draw_wall():
    """Draw the color-changing wall"""
    if show_wall:
        glPushMatrix()
        glColor3f(wall_color[0], wall_color[1], wall_color[2])
        glTranslatef(0, 0, wall_pos_z)
        glScalef(6, 1, 0.5)
        glutSolidCube(40)
        glPopMatrix()

def draw_color_barriers():
    """Draw all active color barriers"""
    for barrier in color_barriers:
        barrier.draw()

def draw_finish_line():
    """Draw the finish line (checkered pattern)"""
    glPushMatrix()
    glTranslatef(0, -29, finish_line_z)

    # Create checkered pattern
    checker_size = 20
    for i in range(-3, 4):
        for j in range(0, 5):
            if (i + j) % 2 == 0:
                glColor3f(1, 1, 1)  # White
            else:
                glColor3f(0, 0, 0)  # Black

            glBegin(GL_QUADS)
            glVertex3f(i*checker_size, 0, j*checker_size)
            glVertex3f((i+1)*checker_size, 0, j*checker_size)
            glVertex3f((i+1)*checker_size, 0, (j+1)*checker_size)
            glVertex3f(i*checker_size, 0, (j+1)*checker_size)
            glEnd()

    glPopMatrix()

def draw_stars():
    """Draw stars in the background"""
    glPushMatrix()
    glColor3f(1, 1, 1)
    glPointSize(2)
    glBegin(GL_POINTS)
    for x, y in stars_positions:
        # Convert to screen coordinates
        glVertex3f(x*200, y*100 + 100, -500)
    glEnd()
    glPopMatrix()

def draw_sky():
    """Draw sky background"""
    glPushMatrix()
    # Draw gradient sky
    glBegin(GL_QUADS)
    glColor3f(0.0, 0.0, 0.2)  # Dark blue at top
    glVertex3f(-500, 200, -500)
    glVertex3f(500, 200, -500)
    glColor3f(0.2, 0.0, 0.4)  # Purple at bottom
    glVertex3f(500, -30, -500)
    glVertex3f(-500, -30, -500)
    glEnd()
    glPopMatrix()

def draw_lives():
    """Draw player lives indicator"""
    glPushMatrix()
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Draw text
    glColor3f(1.0, 1.0, 1.0)
    draw_text(WINDOW_WIDTH-120, WINDOW_HEIGHT-80, f"Lives: {lives}")

    # Draw life indicators (small spheres)
    for i in range(lives):
        glPushMatrix()
        glTranslatef(WINDOW_WIDTH-80 + i*25, WINDOW_HEIGHT-85, 0)
        glColor3f(1.0, 0.4, 0.0)  # Orange life indicators

        # If player is invincible, make the life indicators blink
        if invincible and int(time.time() * 2) % 2 == 0:
            glColor3f(1.0, 1.0, 1.0)  # White when blinking

        # Draw circle for each life
        glBegin(GL_POLYGON)
        num_segments = 12
        for j in range(num_segments):
            theta = 2.0 * 3.1415926 * j / num_segments
            glVertex2f(8 * math.cos(theta), 8 * math.sin(theta))
        glEnd()
        glPopMatrix()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

def cos(angle):
    """Helper function for cos calculations"""
    return math.cos(angle)

def sin(angle):
    """Helper function for sin calculations"""
    return math.sin(angle)

def draw_start_screen():
    """Draw the game start screen"""
    # Draw title
    glColor3f(1.0, 0.7, 0.2)
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT-200, "ROCKET ROAD", GLUT_BITMAP_TIMES_ROMAN_24)

    # Draw play button
    glColor3f(0.3, 0.8, 0.3)
    draw_rectangle(WINDOW_WIDTH/2-100, WINDOW_HEIGHT/2-40, WINDOW_WIDTH/2+100, WINDOW_HEIGHT/2+40)

    glColor3f(0.0, 0.0, 0.0)
    draw_rectangle(WINDOW_WIDTH/2-95, WINDOW_HEIGHT/2-35, WINDOW_WIDTH/2+95, WINDOW_HEIGHT/2+35)

    glColor3f(1.0, 1.0, 1.0)
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2, "PLAY", GLUT_BITMAP_TIMES_ROMAN_24)

    # Draw instructions
    glColor3f(1.0, 1.0, 1.0)
    draw_text(20, 120, "Controls:", GLUT_BITMAP_HELVETICA_18)
    draw_text(20, 100, "Left/Right Arrows: Move", GLUT_BITMAP_HELVETICA_12)
    draw_text(20, 80, "Up Arrow: Jump", GLUT_BITMAP_HELVETICA_12)
    draw_text(20, 60, "P: Start/Continue", GLUT_BITMAP_HELVETICA_12)
    draw_text(20, 40, "C: Pause", GLUT_BITMAP_HELVETICA_12)
    draw_text(20, 20, "Lives: 3", GLUT_BITMAP_HELVETICA_12)

def draw_pause_screen():
    """Draw pause screen overlay"""
    # Semi-transparent overlay (simpler version without alpha blending)
    glColor3f(0.0, 0.0, 0.0)
    draw_rectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)

    # Pause symbol
    glColor3f(1.0, 1.0, 1.0)
    draw_rectangle(WINDOW_WIDTH/2-50, WINDOW_HEIGHT/2-60, WINDOW_WIDTH/2-20, WINDOW_HEIGHT/2+60)
    draw_rectangle(WINDOW_WIDTH/2+20, WINDOW_HEIGHT/2-60, WINDOW_WIDTH/2+50, WINDOW_HEIGHT/2+60)

    # Text
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2+100, "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24)
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2-100, "P to CONTINUE", GLUT_BITMAP_HELVETICA_18)

def draw_level_complete_screen():
    """Draw level complete screen"""
    # Semi-transparent overlay
    glColor3f(0.0, 0.0, 0.0)  # Simple black background instead of transparent
    draw_rectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)

    # Level complete text
    glColor3f(0.5, 1.0, 0.5)
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2+100, f"LEVEL {level-1} COMPLETE!", GLUT_BITMAP_TIMES_ROMAN_24)
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2+50, f"UP TO LEVEL {level}", GLUT_BITMAP_HELVETICA_18)

    # Continue button
    glColor3f(0.7, 0.2, 0.7)
    draw_rectangle(WINDOW_WIDTH/2-100, WINDOW_HEIGHT/2-40, WINDOW_WIDTH/2+100, WINDOW_HEIGHT/2+40)

    glColor3f(0.8, 0.6, 0.8)
    draw_rectangle(WINDOW_WIDTH/2-95, WINDOW_HEIGHT/2-35, WINDOW_WIDTH/2+95, WINDOW_HEIGHT/2+35)

    glColor3f(1.0, 1.0, 1.0)
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2, "CONTINUE", GLUT_BITMAP_HELVETICA_18)
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2-70, "P to continue", GLUT_BITMAP_HELVETICA_12)

def draw_game_over_screen():
    """Draw game over screen"""
    # Semi-transparent overlay
    glColor3f(0.0, 0.0, 0.0)  # Simple black background instead of transparent
    draw_rectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)

    # Game over text
    glColor3f(1.0, 0.2, 0.2)
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2+100, "GAME OVER!", GLUT_BITMAP_TIMES_ROMAN_24)
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2+50, f"Score: {score}", GLUT_BITMAP_HELVETICA_18)
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2+20, f"Level: {level}", GLUT_BITMAP_HELVETICA_18)

    # Restart button
    glColor3f(0.9, 0.3, 0.3)
    draw_rectangle(WINDOW_WIDTH/2-100, WINDOW_HEIGHT/2-40, WINDOW_WIDTH/2+100, WINDOW_HEIGHT/2+40)

    glColor3f(0.7, 0.0, 0.0)
    draw_rectangle(WINDOW_WIDTH/2-95, WINDOW_HEIGHT/2-35, WINDOW_WIDTH/2+95, WINDOW_HEIGHT/2+35)

    glColor3f(1.0, 1.0, 1.0)
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2, "RESTART", GLUT_BITMAP_HELVETICA_18)
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2-70, "P to restart", GLUT_BITMAP_HELVETICA_12)

def draw_hud():
    """Draw heads-up display with game info"""
    draw_text(10, WINDOW_HEIGHT-30, f"Score: {score}", GLUT_BITMAP_HELVETICA_18)
    draw_text(10, WINDOW_HEIGHT-60, f"Level: {level}", GLUT_BITMAP_HELVETICA_18)

    # Draw lives
    draw_lives()

    # Control reminders
    draw_text(WINDOW_WIDTH-200, WINDOW_HEIGHT-30, "P: Continue", GLUT_BITMAP_HELVETICA_12)
    draw_text(WINDOW_WIDTH-200, WINDOW_HEIGHT-50, "C: Pause", GLUT_BITMAP_HELVETICA_12)

def respawn_player():
    """Respawn the player after losing a life"""
    global main_ball_pos, main_ball_target_x, main_ball_y, invincible, invincible_time
    global jumping, falling, jumping_height

    # Reset player position to last respawn point
    main_ball_pos = respawn_pos.copy()
    main_ball_target_x = respawn_pos[0]
    main_ball_y = 0

    # Reset jump state
    jumping = False
    falling = False
    jumping_height = 0

    # Make player temporarily invincible
    invincible = True
    invincible_time = time.time()

def reset_game():
    """Reset game parameters to start a new game"""
    global main_ball_pos, main_ball_target_x, main_ball_y, main_ball_color
    global jumping, falling, jumping_height, road_offset, score, level
    global wall_pos_z, show_wall, finish_line_z, game_state, direction
    global main_ball_rot_angle, color_barriers, lives, invincible, respawn_pos
    global speed_multiplier, game_speed, base_game_speed 

    # Reset player
    main_ball_pos = [0, 0, 4]
    main_ball_target_x = 0
    main_ball_y = 0
    main_ball_rot_angle = 0
    main_ball_color = colors[0]
    respawn_pos = [0, 0, 4]

    # Reset game state
    jumping = False
    falling = False
    jumping_height = 0
    road_offset = 0
    score = 0
    level = 1
    lives = 3
    invincible = False

    # Reset environment
    wall_pos_z = -400
    show_wall = False
    finish_line_z = -2500
    game_state = GAME_RUNNING
    direction = "STOP"

    # Reset barriers
    color_barriers.clear()

    # Reset balls
    balls.clear()
    balls.append(Ball(0, 0, -300, 20, colors[0]))

def setup_next_level():
    """Setup game for the next level"""
    global wall_pos_z, show_wall, finish_line_z, game_state
    global road_offset, main_ball_rot_angle, color_barriers, respawn_pos

    # Reset positions but keep score and level
    wall_pos_z = -400
    show_wall = False
    finish_line_z = -2500-(level * 300)
    road_offset = 0
    main_ball_rot_angle = 0
    game_state = GAME_RUNNING
    color_barriers.clear()

    # Update respawn position for the new level
    respawn_pos = [0, 0, 4]

    # Add a new ball with random color for increased difficulty
    random_x = random.choice([-80, 0, 80])
    random_color = random.choice(colors)
    balls.append(Ball(random_x, 0, -600, 20, random_color))

def spawn_size_platform():
    """Spawn a new size platform with random type"""
    global size_platforms
    
    # Randomly choose platform type (increase or decrease)
    platform_type = random.choice(['increase', 'decrease'])
    
    # Random x position (-80, 0, or 80)
    x_pos = random.choice([-80, 0, 80])
    
    # Create new size platform
    new_platform = SizePlatform(x_pos, -800, platform_type)
    size_platforms.append(new_platform)

def update_game_state():
    """Update game state based on current time"""
    global last_update_time, road_offset, wall_pos_z, show_wall
    global finish_line_z, main_ball_pos, main_ball_target_x, direction
    global jumping, falling, jumping_height, main_ball_y, main_ball_rot_angle
    global main_ball_color, score, level, game_state, color_barriers
    global lives, invincible, invincible_time, respawn_pos
    global speed_multiplier, game_speed, base_game_speed, speed_cubes
    global main_ball_radius, size_platforms

    current_time = time.time()
    if current_time - last_update_time < game_speed / 1000.0:
        return

    last_update_time = current_time

    if game_state != GAME_RUNNING:
        return

    # Check if invincibility should end
    if invincible and current_time - invincible_time > invincible_duration:
        invincible = False

    # Update main ball position based on direction
    if direction == "LEFT":
        main_ball_pos[0] = max(main_ball_pos[0] - 5, main_ball_target_x)
    elif direction == "RIGHT":
        main_ball_pos[0] = min(main_ball_pos[0] + 5, main_ball_target_x)

    # Update respawn position (checkpoint) every 200 units of forward progress
    if abs(finish_line_z - (-1200)) > 200 and abs(finish_line_z - (-1200)) % 200 < 10:
        respawn_pos = main_ball_pos.copy()

    # Handle jumping
    if jumping and not falling:
        jumping_height += 5
        main_ball_y = jumping_height
        if jumping_height >= max_jump_height:
            falling = True
    elif falling:
        jumping_height -= 5
        main_ball_y = jumping_height
        if jumping_height <= 0:
            jumping = False
            falling = False
            jumping_height = 0
            main_ball_y = 0

    # Update road and world elements
    road_offset += 5
    if show_wall:
        wall_pos_z += 10
    finish_line_z += 5
    main_ball_rot_angle += 5

    # Randomly spawn size platforms (about every 5 seconds)
    if random.random() < 0.02 and len(size_platforms) < 2:
        spawn_size_platform()

    # Update size platforms
    platforms_to_remove = []
    for i, platform in enumerate(size_platforms):
        platform.z += 10

        # Check for collision with size platform
        if abs(platform.x - main_ball_pos[0]) < 30 and \
           abs(platform.z - main_ball_pos[2]) < 30 and \
           platform.active:
            
            # Apply size change
            if platform.platform_type == 'increase':
                main_ball_radius = min(main_ball_radius + SIZE_CHANGE_AMOUNT, MAX_BALL_RADIUS)
            else:  # decrease
                main_ball_radius = max(main_ball_radius - SIZE_CHANGE_AMOUNT, MIN_BALL_RADIUS)
            
            # Deactivate the platform
            platform.active = False
            platforms_to_remove.append(i)

        # Remove platforms that go off-screen
        if platform.z > 50:
            platforms_to_remove.append(i)

    # Remove inactive platforms (in reverse order to avoid index issues)
    for i in sorted(platforms_to_remove, reverse=True):
        if i < len(size_platforms):
            size_platforms.pop(i)

    # Randomly spawn speed cubes (about every 5 seconds)
    if random.random() < 0.02 and len(speed_cubes) < 2:
        spawn_speed_cube()

    # Update speed cubes
    cubes_to_remove = []
    for i, cube in enumerate(speed_cubes):
        cube.z += 10

        # Check for collision with speed cube
        if abs(cube.x - main_ball_pos[0]) < 30 and \
           abs(cube.z - main_ball_pos[2]) < 30 and \
           cube.active:
            
            # Apply speed effect
            if cube.cube_type == 'speed_up':
                speed_multiplier = min(speed_multiplier + 0.2, 2.0)  # Increase speed up to 2x
            else:  # speed_down
                speed_multiplier = max(speed_multiplier - 0.2, 0.5)  # Decrease speed down to 0.5x
            
            # Update game speed based on multiplier
            game_speed = base_game_speed / speed_multiplier
            
            # Deactivate the cube
            cube.active = False
            cubes_to_remove.append(i)

        # Remove cubes that go off-screen
        if cube.z > 50:
            cubes_to_remove.append(i)

    # Remove inactive cubes (in reverse order to avoid index issues)
    for i in sorted(cubes_to_remove, reverse=True):
        if i < len(speed_cubes):
            speed_cubes.pop(i)

    # Handle wall collision
    if wall_pos_z >= 0 and show_wall:
        main_ball_color = wall_color.copy()
        wall_pos_z = -400
        show_wall = False
        change_wall_color()

    # Check if we should show a wall
    if score > 0 and score % 15 == 0 and not show_wall and wall_pos_z <= -390:
        show_wall = True

    # Randomly spawn color barriers (about every 10 seconds)
    if random.random() < 0.01 and len(color_barriers) < 3:
        spawn_color_barrier()

    # Update color barriers
    barriers_to_remove = []
    for i, barrier in enumerate(color_barriers):
        barrier.z += 10

        # Check for collision with barrier
        if abs(barrier.z - main_ball_pos[2]) < 30 and barrier.active:
            main_ball_color = barrier.color.copy()
            barrier.active = False
            barriers_to_remove.append(i)

        # Remove barriers that go off-screen
        if barrier.z > 50:
            barriers_to_remove.append(i)

    # Remove inactive barriers (in reverse order to avoid index issues)
    for i in sorted(barriers_to_remove, reverse=True):
        if i < len(color_barriers):
            color_barriers.pop(i)

    # Handle finish line
    if finish_line_z >= 0:
        game_state = LEVEL_COMPLETE
        level += 1

    # Process balls
    for ball in balls:
        # Move balls forward
        ball.z += 10

        # Check for collision with main ball
        if abs(ball.x - main_ball_pos[0]) < 40 and \
           abs(ball.z - main_ball_pos[2]) < 40 and \
           abs(ball.y - main_ball_y) < 40:

            if ball.color == main_ball_color:
                # Same color - collect point

                # Check if we should increase speed
                if score > 0 and score % speed_increase_threshold == 0:
                    speed_multiplier += 0.1  # Increase by 10% each time
                    game_speed = base_game_speed / speed_multiplier  # Lower value means faster updates


                score += 1
                ball.x = random.choice([-80, 0, 80])
                ball.z = -600 
                ball.color = random.choice(colors)
            elif not invincible:
                # Different color and not invincible - lose a life
                lives -= 1

                if lives <= 0:
                    # Game over when no lives left
                    game_state = GAME_OVER
                else:
                    # Respawn with one less life
                    respawn_player()

                # Reset the ball that caused the collision
                ball.x = random.choice([-80, 0, 80])
                ball.z = -600
                ball.color = random.choice(colors)

        # Reset balls that go off-screen
        if ball.z > 50:
            ball.x = random.choice([-80, 0, 80])
            ball.z = -600
            ball.color = random.choice(colors)

def switch_camera():
    """Switch to the next camera preset"""
    global current_camera
    current_camera = (current_camera + 1) % len(camera_positions)

def setupCamera():
    """Configure the camera perspective based on current camera mode"""
    global camera_height_offset, camera_rotation_angle
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WINDOW_WIDTH/WINDOW_HEIGHT, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if current_camera == CAMERA_FIRST_PERSON:
        # First-person view follows the player
        cam_x = main_ball_pos[0]
        cam_y = main_ball_y + 30  # Slightly above the ball
        cam_z = main_ball_pos[2] + 30  # Slightly behind the ball
        
        # Look slightly ahead
        look_x = main_ball_pos[0]
        look_y = main_ball_y
        look_z = main_ball_pos[2] - 100
        
        gluLookAt(cam_x, cam_y, cam_z, look_x, look_y, look_z, 0, 1, 0)
    else:
        # Other camera positions
        x, y, z = camera_positions[current_camera]
        
        if current_camera == CAMERA_SIDE_VIEW:
            # Side view tracks player position along z-axis
            gluLookAt(x, y + camera_height_offset, main_ball_pos[2], 
                      main_ball_pos[0], main_ball_y, main_ball_pos[2], 0, 1, 0)
        else:
            # Apply rotation and height adjustment to third-person view
            # Convert angle to radians
            angle_rad = camera_rotation_angle * 3.14159 / 180.0
            
            # Calculate new camera position based on rotation angle
            rotated_x = x * math.cos(angle_rad) - z * math.sin(angle_rad)
            rotated_z = x * math.sin(angle_rad) + z * math.cos(angle_rad)
            
            # Apply the adjusted camera position
            gluLookAt(rotated_x, y + camera_height_offset, rotated_z, 
                      0, 0, 0, 0, 1, 0)

def keyboardListener(key, x, y):
    """Handle regular keyboard inputs"""
    global game_state, current_camera, camera_height_offset, camera_rotation_angle

    # Changed from F1 to P key for start/continue/restart
    if key == b'p' or key == b'P':
        if game_state == START_SCREEN:
            game_state = GAME_RUNNING
        elif game_state == GAME_PAUSED:
            game_state = GAME_RUNNING
        elif game_state == LEVEL_COMPLETE:
            setup_next_level()
        elif game_state == GAME_OVER:
            reset_game()

    # Changed from F2 to C key for pause
    elif key == b'c' or key == b'C':
        if game_state == GAME_RUNNING:
            game_state = GAME_PAUSED
    
    # New key 'V' to change camera view
    elif key == b'v' or key == b'V':
        if game_state == GAME_RUNNING:
            switch_camera()
            
    # Camera controls
    elif key == b'w' or key == b'W':
        camera_height_offset += 10  # Move camera up
    elif key == b's' or key == b'S':
        camera_height_offset -= 10  # Move camera down
    elif key == b'a' or key == b'A':
        camera_rotation_angle += 5  # Rotate camera left
    elif key == b'd' or key == b'D':
        camera_rotation_angle -= 5  # Rotate camera right

def specialKeyListener(key, x, y):
    """Handle special key inputs (arrow keys)"""
    global main_ball_target_x, direction, jumping

    if game_state != GAME_RUNNING:
        return

    # Left arrow key to move left
    if key == GLUT_KEY_LEFT:
        main_ball_target_x = max(main_ball_target_x - 40, -80)
        direction = "LEFT"

    # Right arrow key to move right
    elif key == GLUT_KEY_RIGHT:
        main_ball_target_x = min(main_ball_target_x + 40, 80)
        direction = "RIGHT"

    # Up arrow key to jump
    elif key == GLUT_KEY_UP and not jumping and not falling:
        jumping = True

def mouseListener(button, state, x, y):
    """Handle mouse inputs"""
    global game_state

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # Check if clicking on start button
        if game_state == START_SCREEN:
            # Check if click is within play button
            button_x1 = WINDOW_WIDTH/2 - 100
            button_x2 = WINDOW_WIDTH/2 + 100
            button_y1 = WINDOW_HEIGHT/2 - 40
            button_y2 = WINDOW_HEIGHT/2 + 40

            # Note: OpenGL Y coordinates are flipped compared to mouse coordinates
            y = WINDOW_HEIGHT - y

            if button_x1 <= x <= button_x2 and button_y1 <= y <= button_y2:
                game_state = GAME_RUNNING

def idle():
    """Idle function to continually update game state and trigger redisplays"""
    update_game_state()
    glutPostRedisplay()
def showScreen():
    """Main display function"""
    # Clear buffers
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)

    setupCamera()

    # Draw sky background (simple rectangles instead of gradient)
    glPushMatrix()
    glBegin(GL_QUADS)
    glColor3f(0.0, 0.0, 0.2)  # Dark blue
    glVertex3f(-500, 200, -500)
    glVertex3f(500, 200, -500)
    glVertex3f(500, -30, -500)
    glVertex3f(-500, -30, -500)
    glEnd()
    glPopMatrix()

    # Draw stars
    glPushMatrix()
    glColor3f(1, 1, 1)
    glPointSize(2)
    glBegin(GL_POINTS)
    for x, y in stars_positions:
        glVertex3f(x*200, y*100 + 100, -500)
    glEnd()
    glPopMatrix()

    # Draw road
    glPushMatrix()
    glColor3f(0.5, 0.5, 0.5)  # Gray road
    glTranslatef(0, -30, 0)

    # Main road
    glBegin(GL_QUADS)
    glVertex3f(-120, 0, -1200)
    glVertex3f(120, 0, -1200)
    glVertex3f(120, 0, 100)
    glVertex3f(-120, 0, 100)
    glEnd()

    # Road markings
    glColor3f(1.0, 1.0, 1.0)  # White markings
    for z in range(-1200, 100, 100):
        z_pos = z + road_offset % 100
        glBegin(GL_QUADS)
        glVertex3f(-5, 1, z_pos)
        glVertex3f(5, 1, z_pos)
        glVertex3f(5, 1, z_pos+30)
        glVertex3f(-5, 1, z_pos+30)
        glEnd()
    glPopMatrix()

    # Draw size platforms
    for platform in size_platforms:
        platform.draw()

    # Draw finish line (checkered pattern)
    glPushMatrix()
    glTranslatef(0, -29, finish_line_z)
    checker_size = 20
    for i in range(-3, 4):
        for j in range(0, 5):
            if (i + j) % 2 == 0:
                glColor3f(1, 1, 1)  # White
            else:
                glColor3f(0, 0, 0)  # Black
            glBegin(GL_QUADS)
            glVertex3f(i*checker_size, 0, j*checker_size)
            glVertex3f((i+1)*checker_size, 0, j*checker_size)
            glVertex3f((i+1)*checker_size, 0, (j+1)*checker_size)
            glVertex3f(i*checker_size, 0, (j+1)*checker_size)
            glEnd()
    glPopMatrix()

    # Draw wall if active
    if show_wall:
        glPushMatrix()
        glColor3f(wall_color[0], wall_color[1], wall_color[2])
        glTranslatef(0, 0, wall_pos_z)
        glScalef(6, 1, 0.5)
        glutSolidCube(40)
        glPopMatrix()

    # Draw color barriers
    for barrier in color_barriers:
        if barrier.active:
            glPushMatrix()
            glColor3f(barrier.color[0], barrier.color[1], barrier.color[2])
            glTranslatef(barrier.x, barrier.y, barrier.z)
            glScalef(barrier.width/40, barrier.height/40, barrier.depth/40)
            glutSolidCube(40)
            glPopMatrix()

    # Draw speed cubes
    for cube in speed_cubes:
        cube.draw()

    # Draw main ball (player)
    glPushMatrix()
    glColor3f(main_ball_color[0], main_ball_color[1], main_ball_color[2])

    # If player is invincible, make it flash (simpler implementation)
    current_time = time.time()
    if invincible and int(current_time * 4) % 2 == 0:
        glColor3f(1.0, 1.0, 1.0)  # White when flashing

    glTranslatef(main_ball_pos[0], main_ball_y, main_ball_pos[2])
    glRotatef(main_ball_rot_angle, 1, 0, 0)  # Rotate around x-axis for rolling effect
    gluSphere(gluNewQuadric(), main_ball_radius, 20, 15)
    glPopMatrix()

    # Draw other balls
    for ball in balls:
        glPushMatrix()
        glColor3f(ball.color[0], ball.color[1], ball.color[2])
        glTranslatef(ball.x, ball.y, ball.z)
        gluSphere(gluNewQuadric(), ball.radius, 20, 15)
        glPopMatrix()

    # Draw HUD elements in ortho mode
    # Score and level display
    draw_text(10, WINDOW_HEIGHT-30, f"Score: {score}")
    draw_text(10, WINDOW_HEIGHT-60, f"Level: {level}")

    # Display current camera mode
    camera_names = ["Third Person", "First Person", "Side View"]
    draw_text(10, WINDOW_HEIGHT-90, f"Camera: {camera_names[current_camera]}")
    draw_text(WINDOW_WIDTH-200, WINDOW_HEIGHT-70, "V: Change View", GLUT_BITMAP_HELVETICA_12)
    # Lives display
    draw_text(WINDOW_WIDTH-120, WINDOW_HEIGHT-80, f"Lives: {lives}")

    # Draw life indicators as simple shapes
    for i in range(lives):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glColor3f(1.0, 0.4, 0.0)  # Orange life indicators

        # If player is invincible, make the life indicators blink
        if invincible and int(current_time * 2) % 2 == 0:
            glColor3f(1.0, 1.0, 1.0)  # White when blinking

        # Draw circles for lives using GL_POINTS with larger size
        glPointSize(16)
        glBegin(GL_POINTS)
        glVertex2f(WINDOW_WIDTH-80 + i*25, WINDOW_HEIGHT-85)
        glEnd()

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    # Draw game state overlays
    if game_state == START_SCREEN:
        # Draw start screen
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Title
        draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT-200, "ROCKET ROAD", GLUT_BITMAP_TIMES_ROMAN_24)

        # Play button (background)
        glColor3f(0.3, 0.8, 0.3)
        glBegin(GL_QUADS)
        glVertex2f(WINDOW_WIDTH/2-100, WINDOW_HEIGHT/2-40)
        glVertex2f(WINDOW_WIDTH/2+100, WINDOW_HEIGHT/2-40)
        glVertex2f(WINDOW_WIDTH/2+100, WINDOW_HEIGHT/2+40)
        glVertex2f(WINDOW_WIDTH/2-100, WINDOW_HEIGHT/2+40)
        glEnd()

        # Inner button (darker)
        glColor3f(0.0, 0.0, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(WINDOW_WIDTH/2-95, WINDOW_HEIGHT/2-35)
        glVertex2f(WINDOW_WIDTH/2+95, WINDOW_HEIGHT/2-35)
        glVertex2f(WINDOW_WIDTH/2+95, WINDOW_HEIGHT/2+35)
        glVertex2f(WINDOW_WIDTH/2-95, WINDOW_HEIGHT/2+35)
        glEnd()

        # Button text
        glColor3f(1.0, 1.0, 1.0)
        draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2, "PLAY", GLUT_BITMAP_TIMES_ROMAN_24)

        # Instructions
        glColor3f(1.0, 1.0, 1.0)
        draw_text(20, 60, "P: Start/Continue", GLUT_BITMAP_HELVETICA_12)
        draw_text(20, 40, "C: Pause", GLUT_BITMAP_HELVETICA_12)
        draw_text(20, 20, "V: Change Camera", GLUT_BITMAP_HELVETICA_12)
        draw_text(20, 120, "Controls:", GLUT_BITMAP_HELVETICA_18)
        draw_text(20, 100, "Left/Right Arrows: Move", GLUT_BITMAP_HELVETICA_12)
        draw_text(20, 80, "Up Arrow: Jump", GLUT_BITMAP_HELVETICA_12)
        draw_text(20, 60, "P: Start/Continue", GLUT_BITMAP_HELVETICA_12)
        draw_text(20, 40, "C: Pause", GLUT_BITMAP_HELVETICA_12)
        #draw_text(20, 20, "Lives: 3", GLUT_BITMAP_HELVETICA_12)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    elif game_state == GAME_PAUSED:
        # Draw pause screen
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Darkened background
        glColor3f(0.0, 0.0, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(WINDOW_WIDTH, 0)
        glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT)
        glVertex2f(0, WINDOW_HEIGHT)
        glEnd()

        # Pause symbol (two vertical bars)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glVertex2f(WINDOW_WIDTH/2-50, WINDOW_HEIGHT/2-60)
        glVertex2f(WINDOW_WIDTH/2-20, WINDOW_HEIGHT/2-60)
        glVertex2f(WINDOW_WIDTH/2-20, WINDOW_HEIGHT/2+60)
        glVertex2f(WINDOW_WIDTH/2-50, WINDOW_HEIGHT/2+60)
        glEnd()

        glBegin(GL_QUADS)
        glVertex2f(WINDOW_WIDTH/2+20, WINDOW_HEIGHT/2-60)
        glVertex2f(WINDOW_WIDTH/2+50, WINDOW_HEIGHT/2-60)
        glVertex2f(WINDOW_WIDTH/2+50, WINDOW_HEIGHT/2+60)
        glVertex2f(WINDOW_WIDTH/2+20, WINDOW_HEIGHT/2+60)
        glEnd()

        # Text
        draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2+100, "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2-100, "P to CONTINUE", GLUT_BITMAP_HELVETICA_18)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    elif game_state == LEVEL_COMPLETE:
        # Draw level complete screen
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Darkened background
        glColor3f(0.0, 0.0, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(WINDOW_WIDTH, 0)
        glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT)
        glVertex2f(0, WINDOW_HEIGHT)
        glEnd()

        # Level complete text
        glColor3f(0.5, 1.0, 0.5)
        draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2+100, f"LEVEL {level-1} COMPLETE!", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2+50, f"UP TO LEVEL {level}", GLUT_BITMAP_HELVETICA_18)

        # Continue button
        glColor3f(0.7, 0.2, 0.7)
        glBegin(GL_QUADS)
        glVertex2f(WINDOW_WIDTH/2-100, WINDOW_HEIGHT/2-40)
        glVertex2f(WINDOW_WIDTH/2+100, WINDOW_HEIGHT/2-40)
        glVertex2f(WINDOW_WIDTH/2+100, WINDOW_HEIGHT/2+40)
        glVertex2f(WINDOW_WIDTH/2-100, WINDOW_HEIGHT/2+40)
        glEnd()

        glColor3f(0.8, 0.6, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(WINDOW_WIDTH/2-95, WINDOW_HEIGHT/2-35)
        glVertex2f(WINDOW_WIDTH/2+95, WINDOW_HEIGHT/2-35)
        glVertex2f(WINDOW_WIDTH/2+95, WINDOW_HEIGHT/2+35)
        glVertex2f(WINDOW_WIDTH/2-95, WINDOW_HEIGHT/2+35)
        glEnd()

        glColor3f(1.0, 1.0, 1.0)
        draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2, "CONTINUE", GLUT_BITMAP_HELVETICA_18)
        draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2-70, "P to continue", GLUT_BITMAP_HELVETICA_12)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    elif game_state == GAME_OVER:
        # Draw game over screen
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Darkened background
        glColor3f(0.0, 0.0, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(WINDOW_WIDTH, 0)
        glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT)
        glVertex2f(0, WINDOW_HEIGHT)
        glEnd()

        # Game over text
        glColor3f(1.0, 0.2, 0.2)
        draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2+100, "GAME OVER!", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2+50, f"Score: {score}", GLUT_BITMAP_HELVETICA_18)
        draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2+20, f"Level: {level}", GLUT_BITMAP_HELVETICA_18)

        # Restart button
        glColor3f(0.9, 0.3, 0.3)
        glBegin(GL_QUADS)
        glVertex2f(WINDOW_WIDTH/2-100, WINDOW_HEIGHT/2-40)
        glVertex2f(WINDOW_WIDTH/2+100, WINDOW_HEIGHT/2-40)
        glVertex2f(WINDOW_WIDTH/2+100, WINDOW_HEIGHT/2+40)
        glVertex2f(WINDOW_WIDTH/2-100, WINDOW_HEIGHT/2+40)
        glEnd()

        glColor3f(0.7, 0.0, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(WINDOW_WIDTH/2-95, WINDOW_HEIGHT/2-35)
        glVertex2f(WINDOW_WIDTH/2+95, WINDOW_HEIGHT/2-35)
        glVertex2f(WINDOW_WIDTH/2+95, WINDOW_HEIGHT/2+35)
        glVertex2f(WINDOW_WIDTH/2-95, WINDOW_HEIGHT/2+35)
        glEnd()

        glColor3f(1.0, 1.0, 1.0)
        draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2, "RESTART", GLUT_BITMAP_HELVETICA_18)
        draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2-70, "P to restart", GLUT_BITMAP_HELVETICA_12)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    # Swap buffers
    glutSwapBuffers()

# Main function to initialize and start the game
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"Rocket Road")

    # Register callbacks
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    # Start game loop
    glutMainLoop()

if __name__ == "__main__":
    main()