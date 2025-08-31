from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import random
import math
import time

WINDOW_W, WINDOW_H = 1280, 800
GRID_LENGTH = 5000
ASPECT = WINDOW_W / WINDOW_H
fovY = 90

camera_modes = ['chase', 'top_down', 'first_person']
current_camera_mode = 0
camera_distance = 260
camera_height = 140

car_pos = [0.0, 0.0, 20.0]
car_angle = 0.0
car_speed = 0.0
LIVES = 9

CAR_SPEED_F = 11.0
CAR_SPEED_B = 5.5
CAR_TURN_SPEED = 3.0

last_w_time = 0.0
last_s_time = 0.0
KEY_HOLD_WINDOW = 0.16

boulders = []
coins = []

def try_place_points(count, min_r, spread):
    pts = []
    attempts = 0
    while len(pts) < count and attempts < count * 80:
        attempts += 1
        p = (random.uniform(-spread, spread), random.uniform(-spread, spread))
        ok = True
        for q in pts:
            if math.hypot(p[0]-q[0], p[1]-q[1]) < min_r:
                ok = False
                break
        if ok:
            pts.append(p)
    return pts

def clamp_to_arena(pos_xy, radius=0):
    x, y = pos_xy
    limit = GRID_LENGTH - radius
    x = max(-limit, min(limit, x))
    y = max(-limit, min(limit, y))
    return [x, y]

def draw_ground():
    tile = 400
    half = GRID_LENGTH
    t = time.time()
    for x in range(-half, half, tile):
        for y in range(-half, half, tile):
            pulse = 0.06 * math.sin((x + y) * 0.001 + t * 0.6)
            r = 0.78 + pulse
            g = 0.28 + 0.5 * pulse
            b = 0.18 + 0.3 * pulse
            r = max(0, min(1, r)); g = max(0, min(1, g)); b = max(0, min(1, b))
            glColor3f(r, g, b)
            glBegin(GL_QUADS)
            glVertex3f(x, y, 0)
            glVertex3f(x + tile, y, 0)
            glVertex3f(x + tile, y + tile, 0)
            glVertex3f(x, y + tile, 0)
            glEnd()

def draw_boulders():
    glColor3f(0.45, 0.45, 0.5)
    for (x, y) in boulders:
        glPushMatrix()
        glTranslatef(x, y, 25)
        gluSphere(gluNewQuadric(), 35, 12, 12)
        glPopMatrix()

def draw_coins():
    glColor3f(1.0, 0.84, 0.0)
    q = gluNewQuadric()
    for (x, y) in coins:
        glPushMatrix()
        glTranslatef(x, y, 20)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(q, 12, 12, 1, 20, 1)
        glPopMatrix()

def draw_car():
    glPushMatrix()
    glTranslatef(car_pos[0], car_pos[1], car_pos[2])
    glRotatef(car_angle, 0, 0, 1)

    glColor3f(0.30, 0.32, 0.40)
    glPushMatrix()
    glTranslatef(0, -5, -5)
    glScalef(50, 70, 15)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.4, 0.42, 0.5)
    glPushMatrix()
    glTranslatef(0, 10, 10)
    glScalef(40, 45, 25)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.18, 0.18, 0.2)
    glPushMatrix()
    glTranslatef(0, 0, 24)
    glScalef(22, 22, 6)
    glutSolidCube(1)
    glPopMatrix()
    
    glColor3f(0.1, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(0, 25, 25)
    glScalef(5, 50, 5)
    glutSolidCube(1)
    glPopMatrix()
    
    glColor3f(0.05, 0.05, 0.05)
    q = gluNewQuadric()
    wheel_positions = [
        (25, 25, 0),
        (-25, 25, 0),
        (25, -40, 0),
        (-25, -40, 0)
    ]
    for x, y, z in wheel_positions:
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(90, 0, 1, 0)
        gluCylinder(q, 12, 12, 10, 15, 5)
        gluCylinder(q, 12, 0, 0.1, 15, 1)
        glTranslatef(0,0,10)
        gluCylinder(q, 12, 0, 0.1, 15, 1)
        glPopMatrix()

    glPopMatrix()

def draw_shapes():
    draw_ground()
    draw_boulders()
    draw_coins()
    draw_car()

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, ASPECT, 0.1, 2 * GRID_LENGTH + 800)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    mode = camera_modes[current_camera_mode]
    ang = math.radians(car_angle)

    if mode == 'chase':
        cam_x = car_pos[0] + camera_distance * math.sin(ang)
        cam_y = car_pos[1] - camera_distance * math.cos(ang)
        cam_z = car_pos[2] + camera_height
        gluLookAt(cam_x, cam_y, cam_z, car_pos[0], car_pos[1], car_pos[2] + 25, 0, 0, 1)
    elif mode == 'top_down':
        gluLookAt(car_pos[0], car_pos[1], GRID_LENGTH, car_pos[0], car_pos[1], 0, 0, 1, 0)
    else:
        eye_x = car_pos[0] - 10 * math.sin(ang)
        eye_y = car_pos[1] + 10 * math.cos(ang)
        look_x = car_pos[0] - 120 * math.sin(ang)
        look_y = car_pos[1] + 120 * math.cos(ang)
        gluLookAt(eye_x, eye_y, car_pos[2] + 30, look_x, look_y, car_pos[2] + 30, 0, 0, 1)


def update_game_state():
    global car_pos, car_speed, LIVES

    now = time.time()
    if now - last_w_time <= KEY_HOLD_WINDOW:
        car_speed = CAR_SPEED_F
    elif now - last_s_time <= KEY_HOLD_WINDOW:
        car_speed = -CAR_SPEED_B
    else:
        car_speed = 0.0

    ang = math.radians(car_angle)
    next_x = car_pos[0] - car_speed * math.sin(ang)
    next_y = car_pos[1] + car_speed * math.cos(ang)

    colliding = False
    for (bx, by) in boulders:
        if math.hypot(next_x - bx, next_y - by) < 65:
            car_speed *= -0.4
            LIVES -= 1
            colliding = True
            break
    
    if not colliding:
        car_pos[0], car_pos[1] = next_x, next_y
    
    car_pos[0], car_pos[1] = clamp_to_arena([car_pos[0], car_pos[1]], radius=60)
    
    if LIVES <= 0:
        print("Game Over! You ran out of lives.")
        
def keyboardListener(key, x, y):
    global car_angle, last_w_time, last_s_time, current_camera_mode

    if key == b'w':
        last_w_time = time.time()
    elif key == b's':
        last_s_time = time.time()
    elif key == b'a':
        car_angle += CAR_TURN_SPEED
    elif key == b'd':
        car_angle -= CAR_TURN_SPEED
    elif key == b'c':
        current_camera_mode = (current_camera_mode + 1) % len(camera_modes)

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    glViewport(0, 0, WINDOW_W, WINDOW_H)
    setupCamera()
    draw_shapes()
    glutSwapBuffers()

def idle():
    update_game_state()
    glutPostRedisplay()

def initialize_world():
    global boulders, coins
    boulders[:] = try_place_points(60, min_r=180, spread=GRID_LENGTH - 140)
    coins[:] = try_place_points(220, min_r=120, spread=GRID_LENGTH - 160)

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Doomsday Journey")
    
    initialize_world()

    glutDisplayFunc(showScreen)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboardListener)
    glutMainLoop()

if __name__ == "__main__":
    main()
