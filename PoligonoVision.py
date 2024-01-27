#Programa que grafica el polígono de visión de un robot en movimiento
#Autor: José Frrancisco Ambriz Gutiérrez
import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import pygame
import numpy as np
import math


# Variables para la posición inicial
robot_x = 0  #Coordenadas de -500 a 500
robot_y = -100
robot_speed = 10 #Es el paso en pixeles que dará el robot
sensor_radius = 1000 #Podemos reducirlo para tener mayor rendimiento, pero el polígono será limitado al tamaño del alcance del sensor
# Tamaño de la ventana
width = 1000
height = 1000  
# Lista para almacenar la trayectoria
trajectory = []
# Lista de obstáculos (coordenadas x, coordenadas y, ancho, alto)
obstacles = [(-490,-490,980,50),
             (-490,-490,50,900),
             (-490,380,980,50),
             (440,-490,50,880),
             (140, 100, 100, 70),
             (-300, -400, 300, 100),
             (200, -250, 180, 310),
             (-350, 201, 350, 180),
             (-400, -200, 250, 200),
             (-50,-50,100,100),
             (100, 250, 235, 95)]

# Variable para controlar el estado de la simuación
iniciar = False
#COLORES
green=(0.0, 1.0, 0.0,1)
red=(1.0, 0.0, 0.0, 1.0)
blue=(0.0, 0.0, 1.0,1)
obstacle_color=(0.0,0.0,0.0,1)
polygon_color=(1,0,0,0.3)
# Función para manejar la entrada de teclado
def key_callback(window, key, scancode, action, mods):
    global iniciar,ystate
    if key == glfw.KEY_SPACE and action == glfw.PRESS:
        # Cambia el estado de iniciar al presionar la barra espaciadora
        iniciar = not iniciar

# Función para dibujar un círculo con color personalizado
def draw_circle(x, y, radius, segments=30, color=(0.0, 0.0, 0.0, 1.0)):
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(*color)  # Utiliza el color proporcionado
    glVertex2f(x, y)  # Centro del círculo
    for i in range(segments + 1):
        angle = 2.0 * np.pi * float(i) / segments
        # La ventana es cuadrada así que jalan los circulos redonditos
        glVertex2f(x + radius * np.cos(angle), y + radius * np.sin(angle))
    glEnd()
#Función para un obstáculo cuadrado
def draw_obstacle(x, y, width, height, obstacle_color):
    glColor4f(*obstacle_color)  # Color gris para los obstáculos
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()
#Función que une todos los puntos dados con una lineae
def draw_polygon(points, color=(0.0, 0.0, 0.0, 1.0)):
    glBegin(GL_TRIANGLES)
    glColor4f(*color)  # Utiliza el color proporcionado
    for i in range(len(points)-1):
        glVertex2f(robot_x, robot_y)
        glVertex2f(points[i][0], points[i][1])
        glVertex2f(points[i+1][0], points[i+1][1])
    glEnd()
#Función para dibujar un rectangulo con esquinas redondeadas, basado en dos rectángulos y circulos
def draw_rounded_rectangle(x, y, width, height, corner_radius, color=obstacle_color):
    draw_obstacle(x, y, width, height, color)
    draw_obstacle(x-corner_radius,y+corner_radius,width+2*corner_radius,height-2*corner_radius,color)
    delta=0
    draw_circle(x-delta,y+corner_radius-delta,corner_radius,color=color,segments=51)
    draw_circle(x+width+delta,y+corner_radius-delta,corner_radius,color=color,segments=51)
    draw_circle(x-delta,y+height-corner_radius+delta,corner_radius,color=color,segments=51)
    draw_circle(x+width+delta,y+height-corner_radius+delta,corner_radius,color=color,segments=51)
# Función para dibujar el mapa de obstáculos
cr=0
def draw_obstacle_map():
    for obstacle in obstacles:
        x, y, width, height = obstacle
        draw_rounded_rectangle(x, y, width, height,cr)
    #Dibuja un circulo centrado en xy con radio r y color obstacle_color
    draw_circle(50,50,100,segments=51,color=obstacle_color)
    #Dibuja un triángulo en x y
    glBegin(GL_TRIANGLES)
    glColor4f(*obstacle_color)  # Utiliza el color proporcionado
    glVertex2f(200, -200)
    glVertex2f(400, -400)
    glVertex2f(150, -300)
    glEnd()
# Función para renderizar y dibujar texto en OpenGL
def draw_text(text, x, y, font, color=(1.0, 1.0, 1.0)):
    text_surface = font.render(text, True, pygame.Color(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255))
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    text_width, text_height = text_surface.get_width(), text_surface.get_height()
    glRasterPos2i(x, y)
    glDrawPixels(text_width, text_height, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
#Función para convertir coordenadas de ventana a pixeles 
def world_to_pixel(x, y, window_width, window_height):
    # Ajusta las coordenadas del mundo (-1 a 1) al tamaño de la ventana
    pixel_x = int(x + (window_width * 0.5))
    pixel_y = int(y + (window_height* 0.5))
    return pixel_x, pixel_y

#Funcion para leer un pixel
def read_pixel_color(x1, y1):
    x,y= world_to_pixel(x1, y1, width, height)
    glFlush()
    data = glReadPixels(x, y, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE)
    # Accede a los componentes de color directamente en el resultado de glReadPixels
    red = data[0] / 255.0
    green = data[1] / 255.0
    blue = data[2] /255.0
    alpha = data[3] / 255.0 
    #print(red, green, blue, alpha)
    return (red, green, blue, alpha)
     
# Función para verificar si un punto (x, y) está dentro de algún obstáculo
def is_inside_obstacle(x, y):
        if (read_pixel_color(x,y) != (1,1,1,1) and read_pixel_color(x,y) != (0,0,0,0) and read_pixel_color(x,y) != (1,0,0,0.3)):
            return True
        else:
            return False

# Laser para detectar
def laser(x, y, angle, max_distance,step=10):
    # Inicializa las coordenadas del punto actual
    offset= robot_speed*2
    current_x = x + offset * math.cos(angle)
    current_y = y + offset * math.sin(angle)
    # Calcula las coordenadas del punto final del láser
    end_x = x + max_distance * math.cos(angle )
    end_y = y + max_distance * math.sin(angle )
    # Define un paso pequeño para avanzar a lo largo de la línea
    while (
        (current_x <= end_x and step * math.cos(angle) >= 0) or
        (current_x >= end_x and step * math.cos(angle) <= 0)
    ) and (
        (current_y <= end_y and step * math.sin(angle) >= 0) or
        (current_y >= end_y and step * math.sin(angle) <= 0)
    ):
        # Verifica si el punto actual está dentro de algún obstáculo
        if is_inside_obstacle(current_x, current_y):
            # El punto está dentro de un obstáculo, por lo que lo retornamos
            return current_x, current_y
            
        # Avanza al siguiente punto a lo largo del láser
        current_x += step * math.cos(angle)
        current_y += step * math.sin(angle)
    return None, None

#Funcion sensor
def sensor(x, y, R):
    global cp
    # Lista para almacenar los puntos de la circunferencia
    points_on_circle = []
    # Calcula el incremento angular entre los rayos
    angle_increment = 2
    # Itera a través de los rayos
    num_rays=int((360)/angle_increment)
    for i in range(num_rays):
        # Calcula el ángulo para este rayo en radianes
        current_angle = math.radians((i) * angle_increment)
        detected_x, detected_y = laser(x,y, current_angle, R)
        points_on_circle.append((detected_x, detected_y))
    #Filtramos points on circle para quitar los none,none
    points_on_circle = [x for x in points_on_circle if x != (None, None)]
    points_on_circle.append(points_on_circle[0])
    return points_on_circle
#Función que retorna new_y y new_x que es la nueva posición del robot usando las flechas del teclado, y usa is inside obstacle para no dejarlo pasar
def update_robot_position(robot_x,robot_y,robot_speed=robot_speed):
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

#Funcion de inicialización
def myInit():
    # Inicializar GLFW
    if not glfw.init():
        raise Exception("No se pudo inicializar GLFW")
    # Crear una ventana
    window = glfw.create_window(width, height, "Vision Polygon Simulation", None, None)
    if not window:
        glfw.terminate()
        raise Exception("No se pudo crear la ventana")
    # Hacer que la ventana sea el contexto actual de OpenGL
    glfw.make_context_current(window)
    # Habilitar el uso de transparencia
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    # Configurar el color de fondo en blanco
    glClearColor(1.0, 1.0, 1.0, 1.0)
    # Configurar la matriz de proyección ortográfica
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-width / 2, width / 2, -height / 2, height / 2, -1, 1)
    glMatrixMode(GL_MODELVIEW)

############################################################################################################################################
############################################################################################################################################
#Función principal
def main():
    global iniciar, robot_x, robot_y
    tangent_points = []  # Inicializa la lista de puntos
    myInit()
    # Configura la función de callback para la entrada de teclado
    glfw.set_key_callback(glfw.get_current_context(), key_callback)
     # Carga la fuente y define su tamaño
    pygame.init()
    font = pygame.font.Font(None, 36)
    font2 = pygame.font.Font(None, 66)
    while not glfw.window_should_close(glfw.get_current_context()):
        # Borra el fondo con el color blanco
        glClear(GL_COLOR_BUFFER_BIT)
        # Dibuja el mapa de obstáculos
        draw_obstacle_map()
        draw_text("Presiona espacio para encender o apagar el sensor, apáguelo para mover el robot",-490,475,font,color=(0.0,0.0,1.0,1))
        draw_text("Mueva el punto con las flechas del teclado. (Puede ir lento con sensor encendido)",-490,447,font,color=(0.8,0,1.0,1))
        new_x,new_y=update_robot_position(robot_x,robot_y)
        if iniciar:
            # solo si no hay teclas presionadas Llama a la función 'sensor' para obtener los puntos
            tangent_points = sensor(robot_x, robot_y, sensor_radius)
            draw_polygon(tangent_points, polygon_color)

        #Actualiza la posición del robot
        robot_x=new_x
        robot_y=new_y
        # Dibuja el círculo del robot 
        draw_circle(robot_x, robot_y, 5, color=blue)
        draw_obstacle_map()
        glfw.swap_buffers(glfw.get_current_context())  # Se intercambian buffers para que aparezca lo dibujado
        glfw.poll_events()  # Manejar eventos de entrada como presionar espacio
        #time.sleep(0.01)
    glfw.terminate()


if __name__ == "__main__":
    main()
