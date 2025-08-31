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
SCORE = 0
COIN_COUNT = 0
KILL_COUNT = 0
game_over = False

CAR_SPEED_F = 11.0
CAR_SPEED_B = 5.5
CAR_TURN_SPEED = 3.0

last_w_time = 0.0
last_s_time = 0.0
KEY_HOLD_WINDOW = 0.16

boulders = []
coins = []
zombies = []

ZOMBIE_TYPES = {
    'small':  {'size': 20, 'speed': 0.65, 'health': 120, 'color': (0.1, 0.8, 0.2), 'damage': 1},
    'huge':   {'size': 60, 'speed': 0.90, 'health': 360, 'color': (1.0, 0.0, 0.0), 'damage': 3},
    'flying': {'size': 40, 'speed': 0.8, 'health': 960, 'color': (1.0, 0.4, 0.7), 'damage': 999},
}
MAX_SMALL_CONCURRENT = 10
MAX_HUGE_CONCURRENT  = 3
MAX_FLYING_CONCURRENT = 1
SPAWN_CHECK_COOLDOWN = 0.35
last_spawn_check = 0.0

clone_active = False
clone_pos = [0.0, 0.0, 20.0]
clone_angle = 0.0
clone_hits = 0

explosion_active = False
explosion_center = [0.0, 0.0, 0.0]
explosion_radius = 0.0
explosion_particles = []

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1.0, 1.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

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

def random_edge_spawn():
    side = random.choice(['left', 'right', 'top', 'bottom'])
    m = GRID_LENGTH - 50
    if side == 'left':
        return [-m, random.uniform(-m, m)]
    if side == 'right':
        return [ m, random.uniform(-m, m)]
    if side == 'top':
        return [random.uniform(-m, m),  m]
    return [random.uniform(-m, m), -m]

def dist2d(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

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
        (25, 25, 0), (-25, 25, 0),
        (25, -40, 0), (-25, -40, 0)
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

def draw_clone():
    if not clone_active:
        return
    glPushMatrix()
    glTranslatef(clone_pos[0], clone_pos[1], clone_pos[2])
    glRotatef(clone_angle, 0, 0, 1)
    glColor3f(0.30, 0.32, 0.40)
    glPushMatrix(); glTranslatef(0, -5, -5); glScalef(50, 70, 15); glutSolidCube(1); glPopMatrix()
    glColor3f(0.4, 0.42, 0.5)
    glPushMatrix(); glTranslatef(0, 10, 10); glScalef(40, 45, 25); glutSolidCube(1); glPopMatrix()
    glColor3f(0.18, 0.18, 0.2)
    glPushMatrix(); glTranslatef(0, 0, 24); glScalef(22, 22, 6); glutSolidCube(1); glPopMatrix()
    glColor3f(0.1, 0.1, 0.1)
    glPushMatrix(); glTranslatef(0, 25, 25); glScalef(5, 50, 5); glutSolidCube(1); glPopMatrix()
    glColor3f(0.05, 0.05, 0.05)
    q = gluNewQuadric()
    wheel_positions = [(25, 25, 0), (-25, 25, 0), (25, -40, 0), (-25, -40, 0)]
    for x, y, z in wheel_positions:
        glPushMatrix(); glTranslatef(x, y, z); glRotatef(90, 0, 1, 0)
        gluCylinder(q, 12, 12, 10, 15, 5); gluCylinder(q, 12, 0, 0.1, 15, 1); glTranslatef(0,0,10)
        gluCylinder(q, 12, 0, 0.1, 15, 1); glPopMatrix()
    glPopMatrix()

def draw_small_zombie(z):
    glPushMatrix()
    glTranslatef(z['pos'][0], z['pos'][1], ZOMBIE_TYPES['small']['size'])
    scale = 1.0 + 0.15 * math.sin(time.time() * 5.0)
    glScalef(scale, scale, scale)
    glColor3f(*ZOMBIE_TYPES['small']['color'])
    gluSphere(gluNewQuadric(), ZOMBIE_TYPES['small']['size'], 15, 15)
    glTranslatef(0, 0, ZOMBIE_TYPES['small']['size'])
    gluSphere(gluNewQuadric(), ZOMBIE_TYPES['small']['size'] * 0.6, 12, 12)
    glPopMatrix()

def draw_huge_zombie(z):
    glPushMatrix()
    glTranslatef(z['pos'][0], z['pos'][1], ZOMBIE_TYPES['huge']['size'])
    scale = 1.0 + 0.15 * math.sin(time.time() * 5.0)
    glScalef(scale, scale, scale)
    glColor3f(*ZOMBIE_TYPES['huge']['color'])
    gluSphere(gluNewQuadric(), ZOMBIE_TYPES['huge']['size'], 15, 15)
    glTranslatef(0, 0, ZOMBIE_TYPES['huge']['size'])
    gluSphere(gluNewQuadric(), ZOMBIE_TYPES['huge']['size'] * 0.6, 12, 12)
    glPopMatrix()

def draw_flying_zombie(z):
    glPushMatrix()
    glTranslatef(z['pos'][0], z['pos'][1], 300)
    scale = 1.0 + 0.15 * math.sin(time.time() * 5.0)
    glScalef(scale, scale, scale)
    glRotatef(time.time() * 150, 0, 0, 1)
    glColor3f(*ZOMBIE_TYPES['flying']['color'])
    gluSphere(gluNewQuadric(), ZOMBIE_TYPES['flying']['size'], 15, 15)
    glPopMatrix()

def draw_zombies():
    for z in zombies:
        if z['type'] == 'small': draw_small_zombie(z)
        elif z['type'] == 'huge': draw_huge_zombie(z)
        elif z['type'] == 'flying': draw_flying_zombie(z)

def draw_explosion():
    if not explosion_active:
        return
    glColor3f(1.0, 0.6, 0.1)
    for p in explosion_particles:
        glPushMatrix()
        glTranslatef(p['pos'][0], p['pos'][1], p['pos'][2])
        gluSphere(gluNewQuadric(), 4, 6, 6)
        glPopMatrix()

def draw_shapes():
    draw_ground()
    draw_boulders()
    draw_coins()
    draw_zombies()
    if not explosion_active:
        draw_car()
        draw_clone()
    draw_explosion()

def setupCamera():
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(fovY, ASPECT, 0.1, 2 * GRID_LENGTH + 800)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
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

def setupMiniMapCamera():
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(120, 1.0, 0.1, 2 * GRID_LENGTH + 1000)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    gluLookAt(car_pos[0], car_pos[1], GRID_LENGTH * 0.25, car_pos[0], car_pos[1], 0, 0, 1, 0)

def maintain_enemy_caps():
    small_count = sum(1 for z in zombies if z['type'] == 'small')
    huge_count = sum(1 for z in zombies if z['type'] == 'huge')
    flying_count = sum(1 for z in zombies if z['type'] == 'flying')
    if small_count < MAX_SMALL_CONCURRENT:
        for _ in range(MAX_SMALL_CONCURRENT - small_count):
            zombies.append({'type': 'small', 'pos': random_edge_spawn(), 'health': ZOMBIE_TYPES['small']['health']})
    if huge_count < MAX_HUGE_CONCURRENT:
        for _ in range(MAX_HUGE_CONCURRENT - huge_count):
            zombies.append({'type': 'huge', 'pos': random_edge_spawn(), 'health': ZOMBIE_TYPES['huge']['health']})
    if flying_count < MAX_FLYING_CONCURRENT:
        for _ in range(MAX_FLYING_CONCURRENT - flying_count):
            zombies.append({'type': 'flying', 'pos': random_edge_spawn(), 'health': ZOMBIE_TYPES['flying']['health']})

def update_game_state():
    global car_pos, car_speed, LIVES, game_over, last_spawn_check, SCORE, COIN_COUNT, clone_active, clone_hits, explosion_active, explosion_radius

    if game_over:
        return

    now = time.time()
    if explosion_active:
        explosion_radius += 22.0
        for p in explosion_particles:
            p['pos'][0] += p['dir'][0]; p['pos'][1] += p['dir'][1]; p['pos'][2] += p['dir'][2]
            p['dir'][2] -= 0.45
        victims = [z for z in zombies if dist2d(z['pos'], explosion_center) < explosion_radius]
        if victims:
            for z in victims:
                if z in zombies:
                    zombies.remove(z)
        if explosion_radius > 1500:
            explosion_active = False
            game_over = True
        return

    if now - last_w_time <= KEY_HOLD_WINDOW: car_speed = CAR_SPEED_F
    elif now - last_s_time <= KEY_HOLD_WINDOW: car_speed = -CAR_SPEED_B
    else: car_speed = 0.0

    ang = math.radians(car_angle)
    next_x = car_pos[0] - car_speed * math.sin(ang)
    next_y = car_pos[1] + car_speed * math.cos(ang)

    colliding = False
    for (bx, by) in boulders:
        if math.hypot(next_x - bx, next_y - by) < 65:
            car_speed *= -0.4; LIVES -= 1; colliding = True; break
    if not colliding: car_pos[0], car_pos[1] = next_x, next_y
    car_pos[0], car_pos[1] = clamp_to_arena([car_pos[0], car_pos[1]], radius=60)

    new_coins = []
    for (cx, cy) in coins:
        if dist2d(car_pos, [cx, cy]) < 40: SCORE += 10; COIN_COUNT += 1
        else: new_coins.append((cx, cy))
    coins[:] = new_coins

    if now - last_spawn_check > SPAWN_CHECK_COOLDOWN:
        maintain_enemy_caps(); last_spawn_check = now

    zombies_to_remove = []
    for z in zombies:
        props = ZOMBIE_TYPES[z['type']]
        target_pos = car_pos
        if clone_active:
            if dist2d(z['pos'], clone_pos) < dist2d(z['pos'], car_pos):
                target_pos = clone_pos
        dx = target_pos[0] - z['pos'][0]; dy = target_pos[1] - z['pos'][1]
        dist = math.hypot(dx, dy)
        if dist > 0: z['pos'][0] += (dx / dist) * props['speed']; z['pos'][1] += (dy / dist) * props['speed']
        if dist2d(z['pos'], car_pos) < (25 + props['size']):
            LIVES -= props['damage']; zombies_to_remove.append(z)
        if clone_active and dist2d(z['pos'], clone_pos) < (25 + props['size']):
            zombies_to_remove.append(z); clone_hits += 1
            if clone_hits >= 2: clone_active = False

    for z in zombies_to_remove:
        if z in zombies: zombies.remove(z)

    if LIVES <= 0: LIVES = 0; game_over = True

def keyboardListener(key, x, y):
    global car_angle, last_w_time, last_s_time, current_camera_mode, clone_active, LIVES, clone_hits, explosion_active, explosion_center, explosion_particles

    if key == b'w': last_w_time = time.time()
    elif key == b's': last_s_time = time.time()
    elif key == b'a': car_angle += CAR_TURN_SPEED
    elif key == b'd': car_angle -= CAR_TURN_SPEED
    elif key == b'c': current_camera_mode = (current_camera_mode + 1) % len(camera_modes)
    elif key == b'v':
        if not clone_active and LIVES > 3:
            LIVES -= 3; clone_active = True; clone_hits = 0
            clone_pos[:] = [car_pos[0] + 60, car_pos[1] - 60, car_pos[2]]
            clone_angle = car_angle
    elif key == b'g':
        if not explosion_active:
            explosion_active = True
            explosion_center[:] = car_pos
            explosion_particles.clear()
            for _ in range(200):
                ang = random.uniform(0, 2 * math.pi)
                pitch = random.uniform(-math.pi/2, math.pi/2)
                speed = random.uniform(8, 20)
                dx = speed * math.cos(ang) * math.cos(pitch)
                dy = speed * math.sin(ang) * math.cos(pitch)
                dz = speed * math.sin(pitch)
                explosion_particles.append({'pos': list(explosion_center), 'dir': [dx, dy, dz]})

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    glViewport(0, 0, WINDOW_W, WINDOW_H)
    setupCamera()
    draw_shapes()
    MAP_SIZE = 200; MAP_X = 20; MAP_Y = WINDOW_H - MAP_SIZE - 20
    glViewport(MAP_X, MAP_Y, MAP_SIZE, MAP_SIZE)
    glClear(GL_DEPTH_BUFFER_BIT)
    setupMiniMapCamera()
    draw_ground()
    draw_boulders()
    draw_zombies()
    if not explosion_active:
        draw_car()
        if clone_active:
            draw_clone()
    glViewport(0, 0, WINDOW_W, WINDOW_H)
    draw_text(10, WINDOW_H - 30, f"Lives: {LIVES}")
    draw_text(10, WINDOW_H - 60, f"Score: {SCORE}")
    draw_text(10, WINDOW_H - 90, f"Coins: {COIN_COUNT}")
    if game_over:
        draw_text(WINDOW_W/2 - 50, WINDOW_H/2, "GAME OVER")
    glutSwapBuffers()

def idle():
    update_game_state()
    glutPostRedisplay()

def initialize_world():
    global boulders, coins, last_spawn_check, LIVES, SCORE, COIN_COUNT, game_over
    global clone_active, clone_hits, explosion_active, explosion_radius
    LIVES = 9; SCORE = 0; COIN_COUNT = 0; game_over = False
    clone_active = False; clone_hits = 0
    explosion_active = False; explosion_radius = 0.0
    boulders[:] = try_place_points(60, min_r=180, spread=GRID_LENGTH - 140)
    coins[:] = try_place_points(220, min_r=120, spread=GRID_LENGTH - 160)
    zombies[:] = []
    maintain_enemy_caps()
    last_spawn_check = time.time()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Doomsday Journey - Step 6: Advanced Mechanics")
    glClearColor(0.18, 0.176, 0.27, 1.0)
    initialize_world()
    glutDisplayFunc(showScreen)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboardListener)
    glutMainLoop()

if __name__ == "__main__":
    main()

