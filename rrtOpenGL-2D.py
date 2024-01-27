import glfw
from OpenGL.GL import *
import pygame
import numpy as np
import math
import random
import time

width = 800
height = 800

robot = (-300, -250)
goal = (300, 300)
epsilon = 10


# Lista de obstáculos rectangulares con 2 puntos opuestos por obstáculo
obstacles = [[(-350, 60), (-100, 250)],
             [(100, 100), (330, 200)],
             [(-280, -140), (-10, -10)],
             [(80, -300), (350, 30)]]

iniciar = False
green = (0.0, 1.0, 0.0, 1)
red = (1.0, 0.0, 0.0, 1.0)
blue = (0.0, 0.0, 1.0, 1)
obstacle_color = (0.0, 0.0, 0.0, 1)
polygon_color = (1, 0, 0, 0.3)


def myInit():
    if not glfw.init():
        raise Exception("No se pudo inicializar GLFW")
    window = glfw.create_window(width, height, "RRT", None, None)
    if not window:
        glfw.terminate()
        raise Exception("No se pudo crear la ventana")
    glfw.make_context_current(window)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(1.0, 1.0, 1.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-width / 2, width / 2, -height / 2, height / 2, -1, 1)
    glMatrixMode(GL_MODELVIEW)


def key_callback(window, key, scancode, action, mods):
    global iniciar
    if key == glfw.KEY_SPACE and action == glfw.PRESS:
        iniciar = not iniciar


def draw_circle(x, y, radius, segments=30, color=(0.0, 0.0, 0.0, 1.0)):
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(*color)
    glVertex2f(x, y)
    for i in range(segments + 1):
        angle = 2.0 * np.pi * float(i) / segments
        glVertex2f(x + radius * np.cos(angle), y + radius * np.sin(angle))
    glEnd()

def draw_obstacle(obstacle, obstacle_color):
    x1, y1, x2, y2 = obstacle[0][0], obstacle[0][1], obstacle[1][0], obstacle[1][1]
    glColor4f(*obstacle_color)
    glBegin(GL_QUADS)
    glVertex2f(x1, y1)
    glVertex2f(x2, y1)
    glVertex2f(x2, y2)
    glVertex2f(x1, y2)
    glEnd()


def draw_line(point1, point2, color=(0.0, 0.0, 0.0, 1.0), thickness=1):
    glColor4f(*color)
    glLineWidth(thickness)
    glBegin(GL_LINES)
    glVertex2f(point1[0], point1[1])
    glVertex2f(point2[0], point2[1])
    glEnd()


def draw_obstacle_map():
    for obstacle in obstacles:
        draw_obstacle(obstacle, obstacle_color)


def world_to_pixel(x, y, window_width, window_height):
    pixel_x = int(x + (window_width * 0.5))
    pixel_y = int(y + (window_height * 0.5))
    return pixel_x, pixel_y

def is_inside_obstacle(x, y):
    for obstacle in obstacles:
        x1, y1, x2, y2 = obstacle[0][0], obstacle[0][1], obstacle[1][0], obstacle[1][1]
        if x1 <= x <= x2 and y1 <= y <= y2:
            return True
    return False


def distance(point1, point2):
    return math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)


def step_from_to(p1, p2,epsilon=10):
    if p1 is None or p2 is None:
        return None
    
    if distance(p1, p2) < 10:
        return p2
    else:
        theta = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        return p1[0] + epsilon * math.cos(theta), p1[1] + epsilon * math.sin(theta)


def encontrar_nodo_mas_cercano(padres, punto):
    if not padres:
        return None, float('inf')

    nodo_cercano = None
    distancia_minima = float('inf')

    for padre in padres:
        dist = distance(padre, punto)
        if dist < distancia_minima:
            distancia_minima = dist
            nodo_cercano = padre

    return nodo_cercano, distancia_minima


def main():
    global iniciar, robot, goal, obstacles

    myInit()
    glfw.set_key_callback(glfw.get_current_context(), key_callback)
    pygame.init()
    font = pygame.font.Font(None, 36)

    # Listas de padres e hijos
    padres = [robot]
    hijos = []

    while not glfw.window_should_close(glfw.get_current_context()):
        glClear(GL_COLOR_BUFFER_BIT)
        draw_obstacle_map()

        if iniciar:
            # Generamos un punto aleatorio de manera uniforme en el mapa y lo graficamos
            punto = (random.uniform(-width / 2, width / 2), random.uniform(-height / 2, height / 2))
            draw_circle(punto[0], punto[1], 3, color=blue)

            # Calculamos el nodo más cercano al punto aleatorio generado
            nodo_cercano, _ = encontrar_nodo_mas_cercano(padres, punto)
            # Calculamos el nuevo nodo con el paso
            nuevo_nodo = step_from_to(nodo_cercano, punto, epsilon)

            # Si el nuevo nodo no está dentro de un obstáculo, lo agregamos al árbol
            if not is_inside_obstacle(nuevo_nodo[0], nuevo_nodo[1]):
                padres.append(nuevo_nodo)
                hijos.append(nodo_cercano)
                # Dibujamos la línea entre el nodo cercano y el nuevo nodo en color azul
                draw_line(nodo_cercano, nuevo_nodo, blue)
                # Si el nuevo nodo está a una distancia menor a 10 del goal, terminamos
                if distance(nuevo_nodo, goal) < 15:
                    iniciar = False

        # Dibujamos el árbol
        for padre, hijo in zip(hijos, padres[1:]):
            draw_line(padre, hijo, blue)

        # Dibujamos el robot
        draw_circle(robot[0], robot[1], 5, color=green)
        # Dibujamos el goal
        draw_circle(goal[0], goal[1], 5, color=red)

        # Si el árbol ha terminado, trazamos la ruta desde el último nodo hasta el nodo inicial
        if not iniciar:
            # Empezamos desde el último nodo
            nodo_actual = padres[-1]
            # Mientras no lleguemos al nodo inicial
            while nodo_actual != robot:
                # Buscamos el padre del nodo actual
                padre = hijos[padres.index(nodo_actual) - 1]
                # Dibujamos la línea entre el nodo actual y su padre en color rojo
                draw_line(padre, nodo_actual, red,thickness=3)
                # El nuevo nodo actual es el padre del nodo actual
                nodo_actual = padre
            

        glfw.swap_buffers(glfw.get_current_context())
        glfw.poll_events()

    glfw.terminate()

# ...

if __name__ == "__main__":
    main()
