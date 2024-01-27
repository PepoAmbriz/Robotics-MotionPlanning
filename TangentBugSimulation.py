#TANGENTBUG SIMULATION
# Autor: José Francisco Ambriz Gutiérrez

import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import pygame
import numpy as np
import math
import time
# Variables para la posición del robot y del objetivo
robot_x = -400  #Coordenadas de -500 a 500
robot_y = -400
goal_x = 310
goal_y = 430 
robot_speed = 6 #Es el paso en pixeles que dará el robot
sensor_radius = 40
# Tamaño de la ventana
width = 1000
height = 1000  
# Lista para almacenar la trayectoria
trajectory = []

# Lista de obstáculos (coordenadas x, coordenadas y, ancho, alto)
obstacles = [(140, 100, 100, 70),
             (-300, -400, 300, 100),
             (200, -250, 210, 310),
             (-350, 200, 350, 200),
             (-400, -200, 250, 200),
             (100, 250, 235, 95)]
k=5

obstacles1 = [(140-k, 100-k, 100+2*k, 70+2*k),
             (-300-k, -400-k, 300+2*k, 100+2*k),
             (200-k, -250-k, 210+2*k, 310+2*k),
             (-350-k, 200-k, 350+2*k, 200+2*k),
             (-400-k, -200-k, 250+2*k, 200+2*k),
             (100-k, 250-k, 235+2*k, 95+2*k)]

# Variable para controlar el estado de la simuación
iniciar = False
RFlag = True
#Para cambiar estado de seguir frontera
following_border = False
# para almacenar la primer posición del borde para cuando lo rodeas todo
border_touched = None
#COLORES
green=(0.0, 1.0, 0.0,1)
red=(1.0, 0.0, 0.0,1)
blue=(0.0, 0.0, 1.0,1)
obstacle_color=(0.2,0.2,0.2,1)
obstacle_color1=(0.2,0.2,0.2,0.009)
goal_color =(0.7,0.2,1,1)

# Función para manejar la entrada de teclado
def key_callback(window, key, scancode, action, mods):
    global iniciar, RFlag
    if key == glfw.KEY_SPACE and action == glfw.PRESS:
        # Cambia el estado de iniciar al presionar la barra espaciadora
        iniciar = not iniciar
    if key == glfw.KEY_ENTER and action == glfw.PRESS:
        # Cambia el estado de RFlag al presionar enter
        RFlag = not RFlag

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

# Función para dibujar la trayectoria en rojo con una línea más gruesa
def draw_trajectory(line_width=4.0):
    glLineWidth(line_width)  # Establece el grosor de la línea
    glBegin(GL_LINE_STRIP)
    glColor4f(1.0, 0.0, 0.0,1)  # Color rojo
    for point in trajectory:
        glVertex2f(point[0], point[1])
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
cr=1
def draw_obstacle_map():
    for obstacle in obstacles:
        x, y, width, height = obstacle
        draw_rounded_rectangle(x, y, width, height,cr)
    draw_circle(10,-50,70,color=obstacle_color,segments=51)

def draw_obstacle_map1():
    for obstacle in obstacles1:
        x, y, width, height = obstacle
        draw_rounded_rectangle(x, y, width, height,cr,color=obstacle_color1)
    draw_circle(10,-50,70+k,color=obstacle_color1,segments=51)

# Función para dibujar la circunferencia de detección del sensor
def draw_sensor_circle(x, y, radius, segments=50, color=(0.0, 0.0, 0.0, 1.0), line_width=1.0):
    glLineWidth(line_width)  # Establece el grosor de la línea
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)  # Configura el modo de dibujo a líneas
    glBegin(GL_LINE_LOOP)
    glColor4f(*color)  # Utiliza el color proporcionado
    for i in range(segments):
        angle = 2.0 * np.pi * float(i) / segments
        glVertex2f(x + radius * np.cos(angle), y + radius * np.sin(angle))
    glEnd()
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)  # Restaura el modo de dibujo a relleno

# Función para calcular la distancia euclidiana entre dos puntos
def euclidean_distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

# Función para encontrar el punto de tangencia que minimiza la distancia heurística
def closest_tangent(robot_x, robot_y, tangent_points, goal_x, goal_y):
    if not tangent_points:
        return None  # No hay puntos tangenciales
    min_distance = float('inf')
    closest_point = None

    for point in tangent_points:
        distance_to_robot = euclidean_distance(robot_x, robot_y, point[0], point[1])
        distance_to_goal = euclidean_distance(point[0], point[1], goal_x, goal_y)
        total_distance = distance_to_robot + distance_to_goal

        if total_distance < min_distance:
            min_distance = total_distance
            closest_point = point
    #print(closest_point)
    return closest_point

# Función para renderizar y dibujar texto en OpenGL
def draw_text(text, x, y, font, color=(1.0, 1.0, 1.0,1)):
    text_surface = font.render(text, True, pygame.Color(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255))
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    text_width, text_height = text_surface.get_width(), text_surface.get_height()
    glRasterPos2i(x, y)
    glDrawPixels(text_width, text_height, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

# Para moverse al goal
def move_towards_goal(robot_x, robot_y, goal_x, goal_y, speed):
    global border_touched,cp,previous_direction,dx,dy
    
    # Calcula la dirección hacia el objetivo
    dx = goal_x - robot_x
    dy = goal_y - robot_y
    length = np.sqrt(dx ** 2 + dy ** 2)
    
    if length != 0:
        dx /= length
        dy /= length      #Normalizamos para mantener velocidad constate
    if 0.07 > dx > -0.07:
        dx=0
    if 0.07 > dy > -0.07:
        dy=0
    # Intenta moverse en la dirección original (x e y)
    new_x = robot_x + speed * dx
    new_y = robot_y + speed * dy

    #Si está muy cerca de cp, guerda robot_x y robot_y en border_touched
    if cp is not None and border_touched is None:
        if euclidean_distance(robot_x, robot_y, cp[0], cp[1]) < robot_speed-1:
            border_touched = (robot_x, robot_y)
    
    previous_direction = (dx, dy)

    return new_x, new_y

#Función que toma los puntos tangenciales y devuelve los puntos que den un dx y dy diferentes de -1
def points_in_direction(tangent_points):
    filter=[]
    for point in tangent_points:
        dx=point[0] - robot_x
        dy=point[1] - robot_y
        length = np.sqrt(dx ** 2 + dy ** 2)
        if length != 0:
            dx /= length
            dy /= length      #Normalizamos para mantener velocidad constate
        if 0.07 > dx > -0.07:
            dx=0
        if 0.07 > dy > -0.07:
            dy=0
        if dx*(previous_direction[0])>= 0:
            if dy*previous_direction[1]>= 0:
                filter.append(point) 
    return filter

#Función para convertir coordenadas de ventana a pixeles 
def world_to_pixel(x, y, window_width, window_height):
    # Ajusta las coordenadas del mundo a coordenadas de pixeles
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
        if (read_pixel_color(x,y) != (1,1,1,1) and read_pixel_color(x,y) != goal_color and read_pixel_color(x,y) != (0,0,0,0) and read_pixel_color(x,y) != blue):
            return True
        else:
            return False

# Laser para detectar
def laser(x, y, angle, max_distance,step=3,offset=robot_speed*2):
    # Inicializa las coordenadas del punto actual
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
    angle_increment = 8.0
    # Itera a través de los rayos
    num_rays=int((360)/angle_increment)
    for i in range(num_rays):
        # Calcula el ángulo para este rayo en radianes
        current_angle = math.radians((i) * angle_increment)
        detected_x, detected_y = laser(x,y, current_angle, R)
        points_on_circle.append((detected_x, detected_y))
    # Filtra los puntos que tienen al menos un vecino igual a (None, None) y current_point no es (None, None)
    filtered_points = []
    for i in range(len(points_on_circle)):
        current_point = points_on_circle[i]
        prev_index = (i - 1) % len(points_on_circle)  # Índice del punto anterior (considerando el ciclo)
        next_index = (i + 1) % len(points_on_circle)  # Índice del siguiente punto (considerando el ciclo)
        prev_point = points_on_circle[prev_index]
        next_point = points_on_circle[next_index]
        #De todo el arreglo de puntos, verifica el punto que minimiza la distancia euclidiana a x_robot y y_robot y lo guarda en cp
        if current_point != (None, None):
            if cp is None:
                cp = current_point
            else:
                if euclidean_distance(x, y, current_point[0], current_point[1]) < euclidean_distance(x, y, cp[0], cp[1]):
                    cp = current_point
        # Verifica si al menos uno de los vecinos es igual a (None, None) y current_point no es (None, None)
        if (current_point != (None, None)) and ((prev_point == (None, None)) or (next_point == (None, None))):
            filtered_points.append(current_point)
            #print(filtered_points)
    return filtered_points

# Función para verificar si el robot ha alcanzado el objetivo
def has_reached_goal(robot_x, robot_y, goal_x, goal_y, threshold=2):
    distance = euclidean_distance(robot_x, robot_y, goal_x, goal_y)
    return distance < threshold

#Funcion para ver si nos despegamos o no
def leave_border(robot_x, robot_y, goal_x, goal_y, sensor_radius):
    # Llama a la función 'laser' para lanzar un rayo desde el robot hacia el goal
    d=sensor_radius
    a=euclidean_distance(robot_x, robot_y, goal_x, goal_y)
    if a < sensor_radius:
        d=a
    x, y = laser(robot_x, robot_y, math.atan2(goal_y - robot_y, goal_x - robot_x), d,step=1,offset=6)
    # Verifica si 'laser' detectó un obstáculo en la dirección del goal
    if x is None and y is None:
        return True  #Despegarse
    else:
        return False  #Seguir borde porque hay algo

#Funcion de inicialización
def myInit():
    # Inicializar GLFW
    if not glfw.init():
        raise Exception("No se pudo inicializar GLFW")
    # Crear una ventana
    window = glfw.create_window(width, height, "Tangent Bug Simulation", None, None)
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
#Funciones para mover al robot y al goal con las flechas del teclado
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
#lo mismo para el goal pero sin restricción
#Función que retorna new_y y new_x que es la nueva posición del goal usando las flechas del teclado
def update_goal_position(robot_x,robot_y,robot_speed=robot_speed):
    new_x = robot_x
    new_y = robot_y
    if glfw.get_key(glfw.get_current_context(), glfw.KEY_UP) == glfw.PRESS:
        new_y += robot_speed
    if glfw.get_key(glfw.get_current_context(), glfw.KEY_DOWN) == glfw.PRESS:
        new_y -= robot_speed
    if glfw.get_key(glfw.get_current_context(), glfw.KEY_LEFT) == glfw.PRESS:
        new_x -= robot_speed
    if glfw.get_key(glfw.get_current_context(), glfw.KEY_RIGHT) == glfw.PRESS:
        new_x += robot_speed
    return new_x, new_y
############################################################################################################################################
############################################################################################################################################
#Función principal
def main():
    global robot_x, robot_y, goal_x, goal_y, following_border, iniciar,RFlag, last_tangent_point, previous_direction,border_touched, cp, goal_reached, not_possible,sep, closest_border, closest_border1
    tangent_points = []  # Inicializa la lista de puntos de tangencia
    filter_points = []
    last_tangent_point = None  # Variable para almacenar el último punto tangencial seguido
    previous_direction = None  # Variable para almacenar la dirección anterior del robot
    border_touched = None  # Variable para almacenar el punto tangencial más cercano
    cp = None
    goal_reached = False
    not_possible = False 
    closest_border1=None
    closest_border=None
    despegarse = True
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
        draw_obstacle_map1()
        draw_text("Mover goal o robot con flechas (cambia el objeto con enter) ",-495,470,font, color=blue)
        draw_text("luego presiona espacio para iniciar o detener la simulación",-495,446,font, color=blue)
        draw_obstacle(-500,440,1000,60,(0.5,0.5,0.5,0.5))
        draw_obstacle(-505,435,1010,70,obstacle_color1)

        if iniciar:
            # Llama a la función 'sensor' para obtener los puntos de tangencia
            despegarse = leave_border(robot_x, robot_y, goal_x, goal_y, sensor_radius)
            tangent_points = sensor(robot_x, robot_y , sensor_radius)
            

            if despegarse:
                # El robot debe moverse hacia el goal
                robot_x, robot_y = move_towards_goal(robot_x, robot_y, goal_x, goal_y, robot_speed)
                last_tangent_point = None  # Reinicia el último punto tangencial seguido
                # Reinicia el punto de referencia de la frontera
                border_touched=None
                filter_points=[None]
                cp=None
            else:
                # El robot debe seguir el punto más cercano
                if not following_border:

                    following_border = True

                if last_tangent_point is not None:
                    #primero toma los puntos en esa dirección
                    filter_points=points_in_direction(tangent_points=tangent_points)
                    #Sigue el punto tangencial que minimiza dos veces la euclidiana
                    closest_border = closest_tangent(robot_x, robot_y, filter_points, last_tangent_point[0], last_tangent_point[1])
                    
                else:
                    # Sigue el punto tangencial que minimiza la distancia heurística al principio
                    if len(tangent_points) >= 2 :
                        closest_border = closest_tangent(robot_x, robot_y, tangent_points, goal_x, goal_y)
                        closest_border1=closest_border

                if closest_border is not None:
                    closest_border1 = closest_border
                    robot_x, robot_y = move_towards_goal(robot_x, robot_y, closest_border1[0], closest_border1[1], robot_speed)
                    
                # Verifica si ha vuelto al punto inicial del borde
                if border_touched is not None and has_reached_goal(robot_x, robot_y, border_touched[0], border_touched[1],threshold=robot_speed-1):
                    following_border = False
                    not_possible = True 
                    iniciar = False

                last_tangent_point = closest_border  # Actualiza el último punto tangencial seguido
            
            # Almacena la posición actual en la trayectoria
            trajectory.append((robot_x, robot_y))
            # Evalúa si llegamos al goal
            if has_reached_goal(robot_x, robot_y, goal_x, goal_y, threshold=4):
                iniciar = False
                goal_reached = True
        else:
            if RFlag:
                robot_x, robot_y = update_robot_position(robot_x,robot_y)
            else:
                goal_x, goal_y = update_goal_position(goal_x,goal_y)
        # Dibuja solo el contorno de la circunferencia de detección en verde si no hay colisiones
        # o en rojo si se deteta una colisión
        draw_sensor_circle(robot_x, robot_y, sensor_radius, color=(0.0, 1.0, 0.0,1) if not tangent_points else (1.0, 0.0, 0.0,1), line_width=2.0)

        # Dibuja los puntos tangenciales en color rojo
        glColor4f(1.0, 0.0, 0.0, 1)  # es rgb en escala de 0 a 1
        for point in tangent_points:
            if point is not None:
                draw_circle(point[0], point[1], 3, color=red)  # Asegura que los puntos sean rojos
        
        #Dibuja el punto tocado
        if border_touched is not None:
            draw_circle(border_touched[0], border_touched[1], 5, color=(0,1,1,1))

        # Dibuja el círculo del robot su trayectoria y goal
        draw_circle(robot_x, robot_y, 5, color=(0,0,1,1))
        draw_trajectory(line_width=3.0)
        draw_circle(goal_x, goal_y, 5, color=goal_color)

        if goal_reached:
            draw_text("Goal reached", -100, 0, font2, color=(0.0, 1.0, 0.0,1))
        if not_possible:
            draw_text("Not possible", -100, 0, font2, color=(1.0, 0.0, 0.0,1))

        glfw.swap_buffers(glfw.get_current_context())  # Se intercambian buffers para que aparezca lo dibujado
        glfw.poll_events()  # Manejar eventos de entrada como presionar espacio
        #time.sleep(0.01)
    glfw.terminate()


if __name__ == "__main__":
    main()
