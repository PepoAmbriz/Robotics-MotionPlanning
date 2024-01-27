#RRT kinodinámico para un Dron con controles discretos.
#Integrantes:
# José Francisco Ambriz Gutiérrez
# Lamberto Vázquez Soqui

import glfw
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective, gluLookAt, gluNewQuadric, gluSphere
import pygame
import numpy as np
import math
import random
import time


width = 800
height = 800
ancho = 500   #Cambiar y por z
drone_width=50   #50 px son 20
drone_height=25
drone_depht=50
rotate=100
zone=40
robot = (-300, -350, 0)
goal = (300, 300, 0)
epsilon = 20  # Incremento en cada paso


# Lista de obstáculos rectangulares con 2 puntos opuestos por obstáculo
obstacles = [
    [(-350, 60, -300), (-100, 250, 300)],
    [(100, 100, -300), (330, 200, 300)],
    [(-280, -140, -300), (-10, -10, 300)],
    [(80, -300, -300), (350, 30, 300)],
]

iniciar = False
green = (0.0, 1.0, 0.0, 1)
red = (1.0, 0.0, 0.0, 1.0)
blue = (0.0, 0.0, 1.0, 1)
obstacle_color = (0.2, 0.5, 0.7, 1)

light_position = (800, 800, 800)
light_diffuse = (1.0, 1.0, 1.0, 1.0)
light_ambient = (0.2, 0.2, 0.2, 1.0)
light_specular = (1.0, 1.0, 1.0, 1.0)

material_ambient = (0.7, 0.7, 0.7, 1.0)
material_diffuse = (0.7, 0.2, 0.7, 1.0)
material_specular = (0.2, 1.0, 1.0, 1.0)
material_shininess = 40.0

def myInit():
    if not glfw.init():
        raise Exception("No se pudo inicializar GLFW")
    window = glfw.create_window(width + 100, height + 100, "RRT 3D para un robot con volumen", None, None)
    if not window:
        glfw.terminate()
        raise Exception("No se pudo crear la ventana")
    glfw.make_context_current(window)
    glEnable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
    glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
    glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)
    glMaterialfv(GL_FRONT, GL_DIFFUSE, material_diffuse)
    glMaterialfv(GL_FRONT, GL_SPECULAR, material_specular)
    glMaterialfv(GL_FRONT, GL_SHININESS, material_shininess)
    glMaterialfv(GL_FRONT, GL_AMBIENT, material_ambient)
    glClearColor(1.0, 1.0, 1.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(39, (width / height), 1, 10000)
    glMatrixMode(GL_MODELVIEW)
    
    #funcion para ver en perspectiva el modelo
    gluLookAt(-rotate, 0, 1400, 0, 0, 0, 0, 1, 0)



def key_callback(window, key, scancode, action, mods):
    global iniciar
    if key == glfw.KEY_SPACE and action == glfw.PRESS:
        iniciar = not iniciar
 


def draw_sphere(x, y, z, radius, segments=30, color=(0.0, 0.0, 0.0, 1.0)):
    glPushMatrix()
    glTranslatef(x, y, z)

    # propiedades del material
    glMaterialfv(GL_FRONT, GL_DIFFUSE, color)
    glMaterialfv(GL_FRONT, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))
    glMaterialfv(GL_FRONT, GL_SHININESS, 50.0)

    glColor4f(*color)
    gluSphere(gluNewQuadric(), radius, segments, segments)

    glPopMatrix()

#Función que dibuja un prisma rectangular centrado en el punto dado y dado su ancho, alto y profundidad
def draw_prism(x, y, z, width, height, depth, color=(0.0, 0.0, 0.0, 1.0)):
    x1 = x - width / 2
    x2 = x + width / 2
    y1 = y - height / 2
    y2 = y + height / 2
    z1 = z - depth / 2
    z2 = z + depth / 2

    # Configurar el material específico para los obstáculos
    glMaterialfv(GL_FRONT, GL_DIFFUSE, color)
    glMaterialfv(GL_FRONT, GL_SPECULAR, color)
    glMaterialfv(GL_FRONT, GL_SHININESS, 1.0)

    # Dibuja la base del prisma
    glBegin(GL_QUADS)
    glVertex3f(x1, y1, z1)
    glVertex3f(x2, y1, z1)
    glVertex3f(x2, y2, z1)
    glVertex3f(x1, y2, z1)

    # Dibuja la tapa superior del prisma
    glVertex3f(x1, y1, z2)
    glVertex3f(x2, y1, z2)
    glVertex3f(x2, y2, z2)
    glVertex3f(x1, y2, z2)

    # Dibuja las caras laterales del prisma
    glVertex3f(x1, y1, z1)
    glVertex3f(x2, y1, z1)
    glVertex3f(x2, y1, z2)
    glVertex3f(x1, y1, z2)

    glVertex3f(x1, y2, z1)
    glVertex3f(x2, y2, z1)
    glVertex3f(x2, y2, z2)
    glVertex3f(x1, y2, z2)

    glVertex3f(x1, y1, z1)
    glVertex3f(x1, y2, z1)
    glVertex3f(x1, y2, z2)
    glVertex3f(x1, y1, z2)

    glVertex3f(x2, y1, z1)
    glVertex3f(x2, y2, z1)
    glVertex3f(x2, y2, z2)
    glVertex3f(x2, y1, z2)
    glEnd()
    # Restaurar el material predeterminado
    glMaterialfv(GL_FRONT, GL_DIFFUSE, material_diffuse)
    glMaterialfv(GL_FRONT, GL_SPECULAR, material_specular)
    glMaterialfv(GL_FRONT, GL_SHININESS, material_shininess)




def draw_line(point1, point2, color=(0.0, 0.0, 0.0, 1.0), thickness=1):
    glColor4f(*color)
    glLineWidth(thickness)
    #desactivar iluminacion
    glDisable(GL_LIGHTING)
    glBegin(GL_LINES)
    glVertex3f(point1[0], point1[1], point1[2])
    glVertex3f(point2[0], point2[1], point2[2])
    glEnd()
    #reactivar iluminacion
    glEnable(GL_LIGHTING)

def draw_obstacle(obstacle, obstacle_color):
    x1, y1, z1, x2, y2, z2 = (
        obstacle[0][0],
        obstacle[0][1],
        obstacle[0][2],
        obstacle[1][0],
        obstacle[1][1],
        obstacle[1][2],
    )

    # Configurar el material específico para los obstáculos
    glMaterialfv(GL_FRONT, GL_DIFFUSE, obstacle_color)
    glMaterialfv(GL_FRONT, GL_SPECULAR, obstacle_color)
    glMaterialfv(GL_FRONT, GL_SHININESS, 1.0)


    # Dibuja la base del prisma
    glBegin(GL_QUADS)
    glVertex3f(x1, y1, z1)
    glVertex3f(x2, y1, z1)
    glVertex3f(x2, y2, z1)
    glVertex3f(x1, y2, z1)

    # Dibuja la tapa superior del prisma
    glVertex3f(x1, y1, z2)
    glVertex3f(x2, y1, z2)
    glVertex3f(x2, y2, z2)
    glVertex3f(x1, y2, z2)

    # Dibuja las caras laterales del prisma
    glVertex3f(x1, y1, z1)
    glVertex3f(x2, y1, z1)
    glVertex3f(x2, y1, z2)
    glVertex3f(x1, y1, z2)

    glVertex3f(x1, y2, z1)
    glVertex3f(x2, y2, z1)
    glVertex3f(x2, y2, z2)
    glVertex3f(x1, y2, z2)

    glVertex3f(x1, y1, z1)
    glVertex3f(x1, y2, z1)
    glVertex3f(x1, y2, z2)
    glVertex3f(x1, y1, z2)

    glVertex3f(x2, y1, z1)
    glVertex3f(x2, y2, z1)
    glVertex3f(x2, y2, z2)
    glVertex3f(x2, y1, z2)

    glEnd()


    # Restaurar el material predeterminado
    glMaterialfv(GL_FRONT, GL_DIFFUSE, material_diffuse)
    glMaterialfv(GL_FRONT, GL_SPECULAR, material_specular)
    glMaterialfv(GL_FRONT, GL_SHININESS, material_shininess)



def draw_obstacle_map():
    for obstacle in obstacles:
        draw_obstacle(obstacle, obstacle_color)


def world_to_pixel(x, y, z, window_width, window_height,ancho):
    pixel_x = int(x + (window_width * 0.5))
    pixel_y = int(y + (window_height * 0.5))
    pixel_z = int(z + (ancho * 0.5))
    return pixel_x, pixel_y



def is_inside_obstacle(x, y, z, prism_width=drone_width, prism_height=drone_height, prism_depth=drone_depht):
    for obstacle in obstacles:
        x1, y1, z1, x2, y2, z2 = (
            obstacle[0][0],
            obstacle[0][1],
            obstacle[0][2],
            obstacle[1][0],
            obstacle[1][1],
            obstacle[1][2],
        )

        # Calcular los límites del obstáculo
        obstacle_x_min = x1
        obstacle_x_max = x2
        obstacle_y_min = y1
        obstacle_y_max = y2
        obstacle_z_min = z1
        obstacle_z_max = z2

        # Calcular los límites del prisma rectangular centrado en el punto dado
        prism_x_min = x - prism_width / 2
        prism_x_max = x + prism_width / 2
        prism_y_min = y - prism_height / 2
        prism_y_max = y + prism_height / 2
        prism_z_min = z - prism_depth / 2
        prism_z_max = z + prism_depth / 2

        # Verificar si hay intersección entre el prisma y el obstáculo en cada dimensión
        if (
            prism_x_min <= obstacle_x_max and prism_x_max >= obstacle_x_min
            and prism_y_min <= obstacle_y_max and prism_y_max >= obstacle_y_min
            and prism_z_min <= obstacle_z_max and prism_z_max >= obstacle_z_min
        ):
            return True

    return False


def distance(point1, point2):
    return math.sqrt(
        (point2[0] - point1[0]) ** 2
        + (point2[1] - point1[1]) ** 2
        + (point2[2] - point1[2]) ** 2
    )


def step_from_to(p1, p2, epsilon=10):
    if p1 is None or p2 is None:
        return None

    if distance(p1, p2) < epsilon:
        return p2
    else:
        direction = np.array(p2) - np.array(p1)
        direction /= np.linalg.norm(direction)
        return tuple(np.array(p1) + epsilon * direction)


def encontrar_nodo_mas_cercano(padres, punto):
    if not padres:
        return None, float("inf")

    nodo_cercano = None
    distancia_minima = float("inf")

    for padre in padres:
        dist = distance(padre, punto)
        if dist < distancia_minima:
            distancia_minima = dist
            nodo_cercano = padre

    return nodo_cercano, distancia_minima

#Función Principal
def main():
    global iniciar, robot, goal, obstacles

    myInit()
    glfw.set_key_callback(glfw.get_current_context(), key_callback)
    pygame.init()
    font = pygame.font.Font(None, 36)

    # El primer padre es el nodo donde está el robot
    padres = [robot]
    hijos = []

    while not glfw.window_should_close(glfw.get_current_context()):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        draw_obstacle_map()
        # Flag para iniciar con el teclado
        if iniciar:
            #Punto aleatorio con distribución uniforme en el espacio.
            punto = (
                random.uniform(-width / 2, width / 2),
                random.uniform(-height / 2, height / 2),
                random.uniform(-ancho/2, ancho/2),
            )
            #Ponemos el punto para ver la construcción.
            draw_sphere(punto[0], punto[1], punto[2], 5, color=blue)
            #Calcular el nearest neighbor
            nodo_cercano, _ = encontrar_nodo_mas_cercano(padres, punto)
            #Buscar el control que lo conecte

            nuevo_nodo = step_from_to(nodo_cercano, punto, epsilon)
            if not is_inside_obstacle(*nuevo_nodo):
                #Si todo bien,k agregamos el nodo
                padres.append(nuevo_nodo)
                hijos.append(nodo_cercano)
                #Dibujamos el arbol
                #draw_line(nodo_cercano, nuevo_nodo, blue)
                #Si estamos en la región acabamos
                if distance(nuevo_nodo, goal) < zone:
                    iniciar = False

        
        for padre, hijo in zip(hijos, padres[1:]):
            draw_line(padre, hijo, blue)

        # Dibujamos el robot y el goal 
        draw_prism(robot[0], robot[1], robot[2], drone_width, drone_height, drone_depht)
        draw_sphere(robot[0], robot[1], robot[2], 20, color=green)
        draw_sphere(goal[0], goal[1], goal[2], 10, color=red)
        
        #Dibujar la ruta
        if not iniciar:
            nodo_actual = padres[-1]
            while nodo_actual != robot:
                padre = hijos[padres.index(nodo_actual) - 1]
                draw_line(padre, nodo_actual, red, thickness=3)
                nodo_actual = padre

        glfw.swap_buffers(glfw.get_current_context())
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()

