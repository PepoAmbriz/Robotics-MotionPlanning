#Grafo de visibilidad de un robot en ambiente poligonal
#Autor José Francisco Ambriz Gutiérrez
import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import pygame
import numpy as np
import math

width = 800
height = 800
#Posición inicial del robot y del goal
robot=(-300,-150)
goal =(300,300)
z=50
#Lista de obstáculos
obstacles = [[(-350+z, 60), (-200+z, 200), (-60+z, 180), (-100+z, 80)],
             [(100+z, 100), (80+z, 200), (170+z, 190), (100+z, 50)],
             [(-280+z, -140), (-200+z, -100), (-120+z, -90), (-10+z, -220)],
             [(80+z, -100), (50+z, 30), (220+z, 0), (100+z, -280)],]


iniciar = False

green = (0.0, 1.0, 0.0, 1)
red = (1.0, 0.0, 0.0, 1.0)
blue = (0.0, 0.0, 1.0, 1)
obstacle_color = (0.0, 0.0, 0.0, 1)
polygon_color = (1, 0, 0, 0.3)

#Función que inicializa la ventana
def myInit():
    if not glfw.init():
        raise Exception("No se pudo inicializar GLFW")
    window = glfw.create_window(width, height, "Vision Polygon Simulation", None, None)
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

#Función que revisa si se presionó la barra espaciadora
def key_callback(window, key, scancode, action, mods):
    global iniciar
    if key == glfw.KEY_SPACE and action == glfw.PRESS:
        iniciar = not iniciar

#Función que dibuja un círculo
def draw_circle(x, y, radius, segments=30, color=(0.0, 0.0, 0.0, 1.0)):
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(*color)
    glVertex2f(x, y)
    for i in range(segments + 1):
        angle = 2.0 * np.pi * float(i) / segments
        glVertex2f(x + radius * np.cos(angle), y + radius * np.sin(angle))
    glEnd()

#Función que dibuja un obstáculo con un color dado
def draw_obstacle(x, y, width, height, obstacle_color):
    glColor4f(*obstacle_color)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

#Función que dibuja un polígono con un color dado
def draw_polygon(points, color):
    glColor4f(*color)
    glBegin(GL_POLYGON)
    for x, y in points:
        glVertex2f(x, y)
    glEnd()

#Función que dibuja una línea con un color y grosor dado
def draw_line(point1, point2, color=(0.0, 0.0, 0.0, 1.0), thickness=1):
    glColor4f(*color)
    glLineWidth(thickness)
    glBegin(GL_LINES)
    glVertex2f(point1[0], point1[1])
    glVertex2f(point2[0], point2[1])
    glEnd()

#Función que dibuja el mapa de obstáculos
def draw_obstacle_map():
    for obstacle in obstacles:
        draw_polygon(obstacle, obstacle_color)

#Función que dibuja texto
def draw_text(text, x, y, font, color=(1.0, 1.0, 1.0)):
    text_surface = font.render(text, True, pygame.Color(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255))
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    text_width, text_height = text_surface.get_width(), text_surface.get_height()
    glRasterPos2i(x, y)
    glDrawPixels(text_width, text_height, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

#Función que convierte de coordenadas del mundo a coordenadas de pixeles
def world_to_pixel(x, y, window_width, window_height):
    pixel_x = int(x + (window_width * 0.5))
    pixel_y = int(y + (window_height * 0.5))
    return pixel_x, pixel_y

#Función que lee el color de un pixel
def read_pixel_color(x1, y1):
    x, y = world_to_pixel(x1, y1, width, height)
    glFlush()
    data = glReadPixels(x, y, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE)
    red = data[0] / 255.0
    green = data[1] / 255.0
    blue = data[2] / 255.0
    alpha = data[3] / 255.0
    return red, green, blue, alpha

#Función que revisa si un punto está dentro de un obstáculo
def is_inside_obstacle(x, y):
    pixel_color = read_pixel_color(x, y)
    return pixel_color != (1, 1, 1, 1) and pixel_color != (0, 0, 1, 1)

#Función que calcula la distancia entre dos puntos
def distance(point1,point2):
    return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

#Función que revisa si hay un obstáculo entre dos puntos
def laser(point1,point2,step=3):
    #Calcula la distancia entre los puntos
    dis = distance(point1,point2)
    #Calcula el número de pasos
    steps = int(dis/step)
    #Calcula el incremento en x y el incremento en y 
    dx =(point2[0]-point1[0])/steps
    dy =(point2[1]-point1[1])/steps
    #Para todos los pasos vamos avanzando y revisando si está e el obstáculo
    for i in range(steps+10):
        x = point1[0] + dx*i
        y = point1[1] + dy*i
        if is_inside_obstacle(x,y):
            return False
    return True

    #Función que retorna new_y y new_x que es la nueva posición del robot usando las flechas del teclado, y usa is inside obstacle para no dejarlo pasar
def update_robot_position(robot_x,robot_y,robot_speed=1):
    new_x = robot_x
    new_y = robot_y
    if glfw.get_key(glfw.get_current_context(), glfw.KEY_UP) == glfw.PRESS:
        new_y += robot_speed
        if is_inside_obstacle(new_x, new_y):
            new_y -= robot_speed
    if glfw.get_key(glfw.get_current_context(), glfw.KEY_DOWN) == glfw.PRESS:
        new_y -= robot_speed
        if is_inside_obstacle(new_x, new_y):
            new_y += robot_speed
    if glfw.get_key(glfw.get_current_context(), glfw.KEY_LEFT) == glfw.PRESS:
        new_x -= robot_speed
        if is_inside_obstacle(new_x, new_y):
            new_x += robot_speed
    if glfw.get_key(glfw.get_current_context(), glfw.KEY_RIGHT) == glfw.PRESS:
        new_x += robot_speed
        if is_inside_obstacle(new_x, new_y):
            new_x -= robot_speed
    return new_x, new_y
#Función principal
def main():
    global iniciar, robot, goal, obstacles

    myInit()
    glfw.set_key_callback(glfw.get_current_context(), key_callback)
    pygame.init()
    font = pygame.font.Font(None, 36)

    
    while not glfw.window_should_close(glfw.get_current_context()):
        glClear(GL_COLOR_BUFFER_BIT)
        draw_obstacle_map()
        draw_text("Presiona espacio para iniciar o terminar", -390, 355, font, color=(0.0, 0.0, 1.0, 1))
        draw_text("Mueve el robot a sus cordenadas iniciales", -390, 325, font, color=(0.0, 0.0, 1.0, 1))
        new_x,new_y=update_robot_position(robot[0],robot[1])
        robot=(new_x,new_y)
        pairs = []
        vertex =[]
        if iniciar:
            
            #Convertimos obstacles a un vector de puntos llamado vertex
            for obstacle in obstacles:
                for point in obstacle:
                    vertex.append(point)
            vertex.append(robot)
            vertex.append(goal)
        #Revisamos los puntos por pares 
            for i in range(len(vertex)):
                for j in range(i+1,len(vertex)):
                    #Si no hay obstáculo entre los puntos los agregamos a pairs
                    if laser(vertex[i],vertex[j]):
                        if laser(vertex[j],vertex[i]):
                            pairs.append((vertex[i],vertex[j]))
                
            for obstacle in obstacles:
                for i in range(len(obstacle)):
                    pairs.append((obstacle[i], obstacle[(i + 1) % len(obstacle)]))
           
            #Podriamos correr un algoritmo para encontrar la ruta mas corta por el grafo
            #Unimos los puntos de pares con una recta azul
        if pairs:
            for pair in pairs:
                draw_line(pair[0], pair[1], color=blue, thickness=2)
            

        #Graficamos el robot en morado y el goal en verde
        draw_circle(robot[0],robot[1],5,color=(0.8,0,1,1))
        draw_circle(goal[0],goal[1],5,color=(0,0.5,0.2,1))          
        glfw.swap_buffers(glfw.get_current_context())
        glfw.poll_events()


if __name__ == "__main__":
    main()
