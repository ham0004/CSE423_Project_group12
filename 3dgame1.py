from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time

# Game Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
GRID_LENGTH = 600

# Game States
START_SCREEN = 0
GAME_RUNNING = 1
GAME_PAUSED = 2
LEVEL_COMPLETE = 3
GAME_OVER = 4
game_state = START_SCREEN

# Player Ball
main_ball_pos = [0, 0, 4]  # x, y, z
main_ball_radius = 30
main_ball_target_x = 0
main_ball_y = 0
main_ball_rot_angle = 0
main_ball_color = [1.0, 0.4, 0.0]  # Orange
jumping = False
falling = False
jumping_height = 0
max_jump_height = 75

# Camera settings
camera_pos = (0, 120, 200)
fovY = 60

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

# Colors available in the game (R, G, B)
colors = [
    [1.0, 0.4, 0.0],  # Orange
    [1.0, 0.0, 0.8],  # Pink
    [0.3, 0.4, 1.0]   # Blue
]

# Wall
wall_pos_z = -400
show_wall = False
wall_color = colors[2]  # Initial wall color (blue)

# Finish line
finish_line_z = -1200
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
        glutSolidSphere(self.radius, 20, 15)
        glPopMatrix()

# Initialize moving balls list
balls = []
initial_ball = Ball(0, 0, -300, 30, colors[0])
balls.append(initial_ball)

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

def draw_wall():
    """Draw the color-changing wall"""
    if show_wall:
        glPushMatrix()
        glColor3f(wall_color[0], wall_color[1], wall_color[2])
        glTranslatef(0, 0, wall_pos_z)
        glScalef(6, 1, 0.5)
        glutSolidCube(40)
        glPopMatrix()

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
    draw_text(20, 100, "Controls:", GLUT_BITMAP_HELVETICA_18)
    draw_text(20, 80, "Left/Right Arrows: Move", GLUT_BITMAP_HELVETICA_12)
    draw_text(20, 60, "Up Arrow: Jump", GLUT_BITMAP_HELVETICA_12)
    draw_text(20, 40, "C: Start/Continue", GLUT_BITMAP_HELVETICA_12)
    draw_text(20, 20, "P: Pause", GLUT_BITMAP_HELVETICA_12)

def draw_pause_screen():
    """Draw pause screen overlay"""
    # Semi-transparent overlay
    glColor4f(0.0, 0.0, 0.0, 0.7)
    draw_rectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    
    # Pause symbol
    glColor3f(1.0, 1.0, 1.0)
    draw_rectangle(WINDOW_WIDTH/2-50, WINDOW_HEIGHT/2-60, WINDOW_WIDTH/2-20, WINDOW_HEIGHT/2+60)
    draw_rectangle(WINDOW_WIDTH/2+20, WINDOW_HEIGHT/2-60, WINDOW_WIDTH/2+50, WINDOW_HEIGHT/2+60)
    
    # Text
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2+100, "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24)
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2-100, "Press C to CONTINUE", GLUT_BITMAP_HELVETICA_18)

def draw_level_complete_screen():
    """Draw level complete screen"""
    # Semi-transparent overlay
    glColor4f(0.0, 0.0, 0.0, 0.7)
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
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2-70, "Press C to continue", GLUT_BITMAP_HELVETICA_12)

def draw_game_over_screen():
    """Draw game over screen"""
    # Semi-transparent overlay
    glColor4f(0.0, 0.0, 0.0, 0.7)
    draw_rectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    
    # Game over text
    glColor3f(1.0, 0.2, 0.2)
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2+100, "GAME OVER!", GLUT_BITMAP_TIMES_ROMAN_24)
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2+50, f"Score: {score}", GLUT_BITMAP_HELVETICA_18)
    
    # Restart button
    glColor3f(0.9, 0.3, 0.3)
    draw_rectangle(WINDOW_WIDTH/2-100, WINDOW_HEIGHT/2-40, WINDOW_WIDTH/2+100, WINDOW_HEIGHT/2+40)
    
    glColor3f(0.7, 0.0, 0.0)
    draw_rectangle(WINDOW_WIDTH/2-95, WINDOW_HEIGHT/2-35, WINDOW_WIDTH/2+95, WINDOW_HEIGHT/2+35)
    
    glColor3f(1.0, 1.0, 1.0)
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2, "RESTART", GLUT_BITMAP_HELVETICA_18)
    draw_text_center(WINDOW_WIDTH/2, WINDOW_HEIGHT/2-70, "Press C to restart", GLUT_BITMAP_HELVETICA_12)

def draw_hud():
    """Draw heads-up display with game info"""
    draw_text(10, WINDOW_HEIGHT-30, f"Score: {score}", GLUT_BITMAP_HELVETICA_18)
    draw_text(10, WINDOW_HEIGHT-60, f"Level: {level}", GLUT_BITMAP_HELVETICA_18)
    
    # Control reminders
    draw_text(WINDOW_WIDTH-200, WINDOW_HEIGHT-30, "C: Continue", GLUT_BITMAP_HELVETICA_12)
    draw_text(WINDOW_WIDTH-200, WINDOW_HEIGHT-50, "P: Pause", GLUT_BITMAP_HELVETICA_12)

def reset_game():
    """Reset game parameters to start a new game"""
    global main_ball_pos, main_ball_target_x, main_ball_y, main_ball_color
    global jumping, falling, jumping_height, road_offset, score, level
    global wall_pos_z, show_wall, finish_line_z, game_state, direction
    global main_ball_rot_angle
    
    # Reset player
    main_ball_pos = [0, 0, 4]
    main_ball_target_x = 0
    main_ball_y = 0
    main_ball_rot_angle = 0
    main_ball_color = colors[0]
    
    # Reset game state
    jumping = False
    falling = False
    jumping_height = 0
    road_offset = 0
    score = 0
    level = 1
    
    # Reset environment
    wall_pos_z = -400
    show_wall = False
    finish_line_z = -1200
    game_state = GAME_RUNNING
    direction = "STOP"
    
    # Reset balls
    balls.clear()
    balls.append(Ball(0, 0, -300, 30, colors[0]))

def setup_next_level():
    """Setup game for the next level"""
    global wall_pos_z, show_wall, finish_line_z, game_state
    global road_offset, main_ball_rot_angle
    
    # Reset positions but keep score and level
    wall_pos_z = -400
    show_wall = False
    finish_line_z = -1200
    road_offset = 0
    main_ball_rot_angle = 0
    game_state = GAME_RUNNING
    
    # Add a new ball with random color for increased difficulty
    random_x = random.choice([-80, 0, 80])
    random_color = random.choice(colors)
    balls.append(Ball(random_x, 0, -300, 30, random_color))

def update_game_state():
    """Update game state based on current time"""
    global last_update_time, road_offset, wall_pos_z, show_wall
    global finish_line_z, main_ball_pos, main_ball_target_x, direction
    global jumping, falling, jumping_height, main_ball_y, main_ball_rot_angle
    global main_ball_color, score, level, game_state
    
    current_time = time.time()
    if current_time - last_update_time < game_speed / 1000.0:
        return
    
    last_update_time = current_time
    
    if game_state != GAME_RUNNING:
        return
    
    # Update main ball position based on direction
    if direction == "LEFT":
        main_ball_pos[0] = max(main_ball_pos[0] - 5, main_ball_target_x)
    elif direction == "RIGHT":
        main_ball_pos[0] = min(main_ball_pos[0] + 5, main_ball_target_x)
    
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
    
    # Handle wall collision
    if wall_pos_z >= 0 and show_wall:
        main_ball_color = wall_color.copy()
        wall_pos_z = -400
        show_wall = False
        change_wall_color()
    
    # Check if we should show a wall
    if score > 0 and score % 15 == 0 and not show_wall and wall_pos_z <= -390:
        show_wall = True
    
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
                score += 1
                ball.x = random.choice([-80, 0, 80])
                ball.z = -300
                ball.color = random.choice(colors)
            else:
                # Different color - game over
                game_state = GAME_OVER
        
        # Reset balls that go off-screen
        if ball.z > 50:
            ball.x = random.choice([-80, 0, 80])
            ball.z = -300
            ball.color = random.choice(colors)

def setupCamera():
    """Configure the camera perspective"""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WINDOW_WIDTH/WINDOW_HEIGHT, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    x, y, z = camera_pos
    gluLookAt(x, y, z, 0, 0, 0, 0, 1, 0)

def keyboardListener(key, x, y):
    """Handle regular keyboard inputs"""
    global game_state
    
    # 'c' key for start/continue/restart (previously F1)
    if key == b'c' or key == b'C':
        if game_state == START_SCREEN:
            game_state = GAME_RUNNING
        elif game_state == GAME_PAUSED:
            game_state = GAME_RUNNING
        elif game_state == LEVEL_COMPLETE:
            setup_next_level()
        elif game_state == GAME_OVER:
            reset_game()

    # 'p' key for pause (previously F2)
    elif key == b'p' or key == b'P':
        if game_state == GAME_RUNNING:
            game_state = GAME_PAUSED

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
    # Clear screen
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Setup viewport and camera
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    setupCamera()
    
    # Draw background elements
    draw_sky()
    draw_stars()
    
    # Draw game elements
    if game_state != START_SCREEN:
        # Draw game world
        draw_road()
        draw_wall()
        draw_finish_line()
        
        # Draw main ball (player)
        glPushMatrix()
        glColor3f(main_ball_color[0], main_ball_color[1], main_ball_color[2])
        glTranslatef(main_ball_pos[0], main_ball_y, main_ball_pos[2])
        glRotatef(main_ball_rot_angle, 1, 0, 0)  # Rotate around X axis
        glutSolidSphere(main_ball_radius, 20, 15)
        glPopMatrix()
        
        # Draw moving balls
        for ball in balls:
            ball.draw()
        
        # Draw HUD
        draw_hud()
    
    # Draw appropriate state screen
    if game_state == START_SCREEN:
        draw_start_screen()
    elif game_state == GAME_PAUSED:
        draw_pause_screen()
    elif game_state == LEVEL_COMPLETE:
        draw_level_complete_screen()
    elif game_state == GAME_OVER:
        draw_game_over_screen()
    
    # Swap buffers
    glutSwapBuffers()

def main():
    """Main function to initialize and start the game"""
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Rocket Road")
    
    # Enable depth testing and blending for transparency
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Set up lighting
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    # Register callback functions
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    
    # Start the game loop
    glutMainLoop()

if __name__ == "__main__":
    main()