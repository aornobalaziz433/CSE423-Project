from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import random
import math
import time

WINDOW_W, WINDOW_H = 1280, 800
fovY = 90
ASPECT = WINDOW_W / WINDOW_H
GRID_LENGTH = 5000

camera_modes = ['chase', 'top_down', 'first_person']
current_camera_mode = 0
camera_distance = 260
camera_height = 140

car_pos = [0.0, 0.0, 20.0]
car_angle = 0.0
car_speed = 0.0

SLOW_SPEED = 0.0
CAR_SPEED_F = 11.0
CAR_SPEED_B = 5.5
CAR_TURN_SPEED = 3.0

LIVES = 9
SCORE = 0
COIN_COUNT = 0
KILL_COUNT = 0
game_over = False

last_w_time = 0.0
last_s_time = 0.0
KEY_HOLD_WINDOW = 0.16

dual_fire_active = False

boulders = []
coins = []
projectiles = []
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

def clamp_to_arena(pos_xy, radius=0):
    x, y = pos_xy
    limit = GRID_LENGTH - radius
    x = max(-limit, min(limit, x))
    y = max(-limit, min(limit, y))
    return [x, y]

def dist2d(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

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
            glVertex3f(x,       y,       0)
            glVertex3f(x+tile,  y,       0)
            glVertex3f(x+tile,  y+tile,  0)
            glVertex3f(x,       y+tile,  0)
            glEnd()

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

def draw_clone():
    if not clone_active:
        return
    glPushMatrix()
    glTranslatef(clone_pos[0], clone_pos[1], clone_pos[2])
    glRotatef(clone_angle, 0, 0, 1)
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

def draw_boulders():
    glColor3f(0.45, 0.45, 0.5)
    for (x, y) in boulders:
        glPushMatrix()
        glTranslatef(x, y, 25)
        gluSphere(gluNewQuadric(), 35, 12, 12)
        glPopMatrix()

def draw_coins():
    glColor3f(1.0, 0.84, 0.0)
    for (x, y) in coins:
        glPushMatrix()
        glTranslatef(x, y, 20)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 12, 12, 10, 15, 5)
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
        if z['type'] == 'small':
            draw_small_zombie(z)
        elif z['type'] == 'flying':
            draw_flying_zombie(z)
        else:
            draw_huge_zombie(z)

def draw_projectiles():
    glColor3f(1.0, 0.25, 0.0)
    for p in projectiles:
        glPushMatrix()
        glTranslatef(p['pos'][0], p['pos'][1], p['pos'][2])
        gluSphere(gluNewQuadric(), 6, 8, 8)
        glPopMatrix()

def draw_explosion():
    if not explosion_active:
        return
    glColor3f(1.0, 0.6, 0.1)
    for p in explosion_particles:
        glPushMatrix()
        glTranslatef(p['pos'][0], p['pos'][1], p['pos'][2])
        gluSphere(gluNewQuadric(), 4, 6, 6)
        glPopMatrix()

# def draw_minimap_border(x, y, size):
#     glMatrixMode(GL_PROJECTION)
#     glPushMatrix()
#     glLoadIdentity()
#     gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
#     glMatrixMode(GL_MODELVIEW)
#     glPushMatrix()
#     glLoadIdentity()
#     glColor3f(0.8, 0.8, 0.8)
#     glBegin(GL_LINE_LOOP)
#     radius = size / 2.0
#     center_x = x + radius
#     center_y = y + radius
#     for i in range(100):
#         angle = 2 * math.pi * i / 100
#         glVertex3f(center_x + radius * math.cos(angle), center_y + radius * math.sin(angle), 0)
#     glEnd()
#     glPopMatrix()
#     glMatrixMode(GL_PROJECTION)
#     glPopMatrix()
#     glMatrixMode(GL_MODELVIEW)

def draw_circle_mask(x, y, size):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glBegin(GL_TRIANGLE_FAN)
    radius = size / 2.0
    center_x = x + radius
    center_y = y + radius
    glVertex3f(center_x, center_y, 0)
    for i in range(101):
        angle = 2 * math.pi * i / 100
        glVertex3f(center_x + radius * math.cos(angle), center_y + radius * math.sin(angle), 0)
    glEnd()
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_shapes():
    draw_ground()
    draw_boulders()
    draw_coins()
    draw_zombies()
    if not explosion_active:
        draw_car()
        draw_clone()
    draw_projectiles()
    draw_explosion()

def setupMiniMapCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(120, 1.0, 0.1, 2 * GRID_LENGTH + 1000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(car_pos[0], car_pos[1], GRID_LENGTH * 0.125, car_pos[0], car_pos[1], 0, 0, 1, 0)

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

def keyboardListener(key, x, y):
    global car_angle, current_camera_mode
    global explosion_active, explosion_center, explosion_particles
    global clone_active, clone_pos, clone_angle, LIVES, game_over, clone_hits
    global last_w_time, last_s_time
    global dual_fire_active
    if game_over and key != b'r':
        return
    if key == b'w':
        last_w_time = time.time()
    elif key == b's':
        last_s_time = time.time()
    elif key == b'a':
        car_angle += CAR_TURN_SPEED
    elif key == b'd':
        car_angle -= CAR_TURN_SPEED
    elif key == b' ':
        pass
    elif key == b'e' or key == b'E':
        dual_fire_active = not dual_fire_active
    elif key == b'c':
        current_camera_mode = (current_camera_mode + 1) % len(camera_modes)
    elif key == b'g':
        if not explosion_active:
            explosion_active = True
            explosion_center[:] = [car_pos[0], car_pos[1], car_pos[2]]
            explosion_particles.clear()
            for _ in range(140):
                ang = random.uniform(0, 2 * math.pi)
                pitch = random.uniform(-math.pi / 2, math.pi / 2)
                sp = random.uniform(6, 16)
                dx = sp * math.cos(ang) * math.cos(pitch)
                dy = sp * math.sin(ang) * math.cos(pitch)
                dz = sp * math.sin(pitch)
                explosion_particles.append({'pos': [*explosion_center], 'dir': [dx, dy, dz]})
    elif key == b'v':
        if not clone_active and LIVES > 3:
            LIVES -= 3
            clone_active = True
            clone_hits = 0
            clone_pos[0], clone_pos[1], clone_pos[2] = car_pos[0] + 60, car_pos[1] - 60, 20
            clone_angle = car_angle
    elif key == b'r':
        reset_game()

def specialKeyListener(key, x, y):
    global camera_distance, camera_height
    if key == GLUT_KEY_LEFT:
        camera_distance = max(120, camera_distance - 10)
    if key == GLUT_KEY_RIGHT:
        camera_distance = min(420, camera_distance + 10)
    if key == GLUT_KEY_UP:
        camera_height = min(240, camera_height + 6)
    if key == GLUT_KEY_DOWN:
        camera_height = max(80, camera_height - 6)

def mouseListener(button, state, x, y):
    if state == GLUT_DOWN:
        if not game_over and not explosion_active:
            if button == GLUT_LEFT_BUTTON:
                fire_weapon('normal')
            elif button == GLUT_RIGHT_BUTTON:
                fire_weapon('horizontal')

def fire_weapon(mode):
    if dual_fire_active:
        fire_forward()
        fire_horizontally()
        if clone_active:
            fire_forward(from_clone=True)
            fire_horizontally(from_clone=True)
    elif mode == 'normal':
        fire_forward()
        if clone_active:
            fire_forward(from_clone=True)
    elif mode == 'horizontal':
        fire_horizontally()
        if clone_active:
            fire_horizontally(from_clone=True)

def fire_forward(from_clone=False):
    base_angle = clone_angle if from_clone else car_angle
    base_pos   = clone_pos if from_clone else car_pos
    ang = math.radians(base_angle)
    dir_x = -math.sin(ang)
    dir_y =  math.cos(ang)
    dir_z =  0.22
    ln = math.sqrt(dir_x*dir_x + dir_y*dir_y + dir_z*dir_z)
    d = [dir_x/ln, dir_y/ln, dir_z/ln]
    projectiles.append({'pos': [base_pos[0], base_pos[1], base_pos[2] + 18], 'dir': d, 'speed': 40.0})

def fire_upward(from_clone=False):
    base_pos = clone_pos if from_clone else car_pos
    d = [0, 0, 1]
    projectiles.append({'pos': [base_pos[0], base_pos[1], base_pos[2] + 18], 'dir': d, 'speed': 40.0})

def fire_horizontally(from_clone=False):
    base_angle = clone_angle if from_clone else car_angle
    base_pos   = clone_pos if from_clone else car_pos
    ang = math.radians(base_angle)
    dir_x = -math.sin(ang)
    dir_y =  math.cos(ang)
    dir_z =  0.0
    ln = math.hypot(dir_x, dir_y)
    if ln == 0: return
    d = [dir_x/ln, dir_y/ln, dir_z/ln]
    projectiles.append({'pos': [base_pos[0], base_pos[1], 20.0], 'dir': d, 'speed': 40.0})

def update_game_state():
    global car_pos, car_speed, LIVES, SCORE, game_over
    global last_spawn_check
    global clone_pos, clone_angle, clone_active, clone_hits
    global explosion_active, explosion_radius
    global COIN_COUNT, KILL_COUNT
    global dual_fire_active
    if game_over:
        return
    now = time.time()
    if now - last_w_time <= KEY_HOLD_WINDOW and not explosion_active:
        car_speed = CAR_SPEED_F
    elif now - last_s_time <= KEY_HOLD_WINDOW and not explosion_active:
        car_speed = -CAR_SPEED_B
    else:
        car_speed = 0.0
    if explosion_active:
        explosion_radius += 22.0
        for p in explosion_particles:
            p['pos'][0] += p['dir'][0]
            p['pos'][1] += p['dir'][1]
            p['pos'][2] += p['dir'][2]
            p['dir'][2] -= 0.45
        victims = []
        for z in zombies:
            if dist2d(z['pos'], explosion_center) < explosion_radius:
                victims.append(z)
        if victims:
            KILL_COUNT += len(victims)
        for z in victims:
            if z in zombies:
                zombies.remove(z)
                SCORE += 30
        if explosion_radius > 520:
            explosion_active = False
            game_over = True
        return
    ang = math.radians(car_angle)
    next_x = car_pos[0] - car_speed * math.sin(ang)
    next_y = car_pos[1] + car_speed * math.cos(ang)
    colliding = False
    for (bx, by) in boulders:
        if math.hypot(next_x - bx, next_y - by) < 65:
            car_speed *= -0.4
            LIVES -= 1
            dual_fire_active = False
            colliding = True
            break
    if not colliding:
        car_pos[0], car_pos[1] = next_x, next_y
        car_pos[0], car_pos[1] = clamp_to_arena([car_pos[0], car_pos[1]], radius=60)
    new_coins = []
    gained_score = 0
    coins_collected_this_frame = 0
    for (cx, cy) in coins:
        if math.hypot(car_pos[0] - cx, car_pos[1] - cy) < 40:
            gained_score += 10
            coins_collected_this_frame += 1
        else:
            new_coins.append((cx, cy))
    if gained_score:
        SCORE += gained_score
        COIN_COUNT += coins_collected_this_frame
    coins[:] = new_coins
    if clone_active:
        pass
    to_remove = []
    for p in projectiles:
        p['pos'][0] += p['dir'][0] * p['speed']
        p['pos'][1] += p['dir'][1] * p['speed']
        p['pos'][2] += p['dir'][2] * p['speed']
        if (abs(p['pos'][0]) > GRID_LENGTH or
            abs(p['pos'][1]) > GRID_LENGTH or
            p['pos'][2] < 0 or p['pos'][2] > GRID_LENGTH):
            to_remove.append(p)
    for r in to_remove:
        if r in projectiles:
            projectiles.remove(r)
    if now - last_spawn_check > SPAWN_CHECK_COOLDOWN:
        maintain_enemy_caps()
        last_spawn_check = now
    dead = []
    speed_multiplier = 1.0 + (SCORE / 2000.0)
    for z in zombies:
        t = z['type']
        props = ZOMBIE_TYPES[t]
        spd = props['speed'] * speed_multiplier
        target_pos = car_pos
        if clone_active:
            d_player = dist2d(z['pos'], car_pos)
            d_clone = dist2d(z['pos'], clone_pos)
            if d_clone < d_player:
                target_pos = clone_pos
        dx = target_pos[0] - z['pos'][0]
        dy = target_pos[1] - z['pos'][1]
        d_to_target = math.hypot(dx, dy)
        if d_to_target > 0:
            z['pos'][0] += (dx / d_to_target) * spd
            z['pos'][1] += (dy / d_to_target) * spd
        z['pos'] = clamp_to_arena(z['pos'])
        if dist2d(z['pos'], car_pos) < (25 + props['size']):
            LIVES -= props['damage']
            dual_fire_active = False
            dead.append(z)
            if LIVES <= 0:
                LIVES = 0
                game_over = True
        if clone_active:
            d_clone = dist2d(z['pos'], clone_pos)
            if d_clone < (25 + props['size']):
                dead.append(z)
                if t == 'small':
                    clone_hits += 1
                    if clone_hits >= 2:
                        clone_active = False
        hit_by = None
        zZ = 0
        if t == 'small':
            zZ = 20
        elif t == 'huge':
            zZ = 40
        elif t == 'flying':
            zZ = 300
        for p in projectiles:
            d3 = math.sqrt((p['pos'][0]-z['pos'][0])**2 +
                           (p['pos'][1]-z['pos'][1])**2 +
                           (p['pos'][2]-zZ)**2)
            if d3 < props['size'] * 0.9:
                hit_by = p
                break
        if hit_by:
            if hit_by in projectiles:
                projectiles.remove(hit_by)
            z['health'] -= 120
            if z['health'] <= 0:
                dead.append(z)
                KILL_COUNT += 1
                if t == 'small': SCORE += 50
                elif t == 'huge': SCORE += 200
                elif t == 'flying': SCORE += 500
    for z in dead:
        if z in zombies:
            zombies.remove(z)
    if dead:
        maintain_enemy_caps()

def maintain_enemy_caps():
    small = [z for z in zombies if z['type'] == 'small']
    huge  = [z for z in zombies if z['type'] == 'huge']
    flying = [z for z in zombies if z['type'] == 'flying']
    need_small = MAX_SMALL_CONCURRENT - len(small)
    need_huge  = MAX_HUGE_CONCURRENT - len(huge)
    need_flying = MAX_FLYING_CONCURRENT - len(flying)
    for _ in range(max(0, need_small)):
        pos = random_edge_spawn()
        zombies.append({'type': 'small',
                        'pos': pos,
                        'health': ZOMBIE_TYPES['small']['health']})
    for _ in range(max(0, need_huge)):
        pos = random_edge_spawn()
        zombies.append({'type': 'huge',
                        'pos': pos,
                        'health': ZOMBIE_TYPES['huge']['health']})
    for _ in range(max(0, need_flying)):
        pos = random_edge_spawn()
        zombies.append({'type': 'flying',
                        'pos': pos,
                        'health': ZOMBIE_TYPES['flying']['health']})

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    glViewport(0, 0, WINDOW_W, WINDOW_H)
    setupCamera()
    draw_shapes()
    MAP_SIZE = 200
    MAP_X = 20
    MAP_Y = WINDOW_H - MAP_SIZE - 20
    glViewport(MAP_X, MAP_Y, MAP_SIZE, MAP_SIZE)
    glClear(GL_DEPTH_BUFFER_BIT)
    setupMiniMapCamera()
    draw_ground()
    draw_boulders()
    draw_zombies()
    if not explosion_active:
        draw_car()
        draw_clone()
    glViewport(0, 0, WINDOW_W, WINDOW_H)
    glColor3f(0.8, 0.8, 0.8)
    
    draw_text(10, WINDOW_H - 30, f"Lives: {LIVES}")
    draw_text(10, WINDOW_H - 60, f"Score: {SCORE}")
    dual_fire_text = "DUAL FIRE: " + ("ON" if dual_fire_active else "OFF")
    draw_text(10, WINDOW_H - 90, dual_fire_text)
    draw_text(WINDOW_W - 150, WINDOW_H - 30, f"Kills: {KILL_COUNT}")
    draw_text(WINDOW_W - 150, WINDOW_H - 60, f"Coins: {COIN_COUNT}")
    draw_text(10, 40, "LMB: Shoot | RMB: H-Shoot | E: Dual-Fire")
    draw_text(10, 20, "A/D: Turn | W/S: Move | C: Camera | V: Clone(-3 L) | G: BOOM | R: Reset")
    if game_over:
        glColor3f(1.0, 0.4, 0.7)
        draw_text(WINDOW_W//2 - 100, WINDOW_H//2 + 10, "GAME OVER")
        glColor3f(1.0, 1.0, 1.0)
        draw_text(WINDOW_W//2 - 100, WINDOW_H//2 - 20, "Press 'R' to Restart")
        glColor3f(0.1, 0.8, 0.2)
        draw_text(WINDOW_W//2 - 180, WINDOW_H//2 - 50, "CSE423 Project by Aornob, Pritom and Anonto")
    glutSwapBuffers()

def idle():
    update_game_state()
    glutPostRedisplay()

def reset_game():
    global car_pos, car_angle, car_speed, LIVES, SCORE, game_over
    global boulders, coins, zombies, projectiles
    global last_spawn_check
    global clone_active, clone_pos, clone_angle, clone_hits
    global explosion_active, explosion_radius, explosion_particles
    global last_w_time, last_s_time
    global COIN_COUNT, KILL_COUNT
    global dual_fire_active
    car_pos[:] = [0.0, 0.0, 20.0]
    car_angle = 0.0
    car_speed = 0.0
    LIVES = 9
    SCORE = 0
    COIN_COUNT = 0
    KILL_COUNT = 0
    game_over = False
    dual_fire_active = False
    boulders[:] = try_place_points(60,  min_r=180, spread=GRID_LENGTH - 140)
    coins[:]    = try_place_points(220, min_r=120, spread=GRID_LENGTH - 160)
    zombies[:] = []
    for _ in range(MAX_SMALL_CONCURRENT):
        pos = random_edge_spawn()
        zombies.append({'type': 'small', 'pos': pos, 'health': ZOMBIE_TYPES['small']['health']})
    for _ in range(MAX_HUGE_CONCURRENT):
        pos = random_edge_spawn()
        zombies.append({'type': 'huge', 'pos': pos, 'health': ZOMBIE_TYPES['huge']['health']})
    for _ in range(MAX_FLYING_CONCURRENT):
        pos = random_edge_spawn()
        zombies.append({'type': 'flying', 'pos': pos, 'health': ZOMBIE_TYPES['flying']['health']})
    projectiles[:] = []
    last_spawn_check = time.time()
    clone_active = False
    clone_hits = 0
    clone_pos[:] = [60.0, -60.0, 20.0]
    clone_angle = 0.0
    explosion_active = False
    explosion_radius = 0.0
    explosion_particles[:] = []
    last_w_time = 0.0
    last_s_time = 0.0

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Doomsday Journey")
    reset_game()
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()

