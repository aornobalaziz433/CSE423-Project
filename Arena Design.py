from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import random
import math
import time

WINDOW_W, WINDOW_H = 1280, 800
GRID_LENGTH = 5000

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

def draw_shapes():
    draw_ground()
    draw_boulders()
    draw_coins()

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(90, WINDOW_W / WINDOW_H, 0.1, 2 * GRID_LENGTH)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(0, -800, 600, 0, 0, 0, 0, 0, 1)

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    glViewport(0, 0, WINDOW_W, WINDOW_H)
    setupCamera()
    draw_shapes()
    glutSwapBuffers()

def idle():
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
    glutCreateWindow(b"Doomsday Journey - Step 1: The World")
    initialize_world()
    glutDisplayFunc(showScreen)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()