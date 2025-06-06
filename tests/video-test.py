import os
import pygame
import psutil
import time
import math

pygame.init()
pygame.mouse.set_visible(False)  # Nasconde il cursore del mouse

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
width, height = screen.get_size()
font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()

def draw_grid(surface, spacing=50, color=(50, 50, 50)):
    for x in range(0, width, spacing):
        pygame.draw.line(surface, color, (x, 0), (x, height))
    for y in range(0, height, spacing):
        pygame.draw.line(surface, color, (0, y), (width, y))

# Funzione per disegnare una sinusoide animata con effetto glow
def draw_sinusoid(surface, time_offset, color=(0, 255, 0), amplitude=50, frequency=0.01):
    # Calcola i punti della sinusoide
    points = []
    for x in range(0, width, 2):
        y = int(height / 2 + amplitude * math.sin(frequency * x + time_offset))
        points.append((x, y))
    
    if len(points) > 1:
        # Metodo alternativo per creare il glow: disegna linee più spesse con opacità minore
        # Strato 4 (il più esterno)
        pygame.draw.lines(surface, (0, 40, 0), False, points, 10)
        # Strato 3
        pygame.draw.lines(surface, (0, 80, 0), False, points, 8)
        # Strato 2
        pygame.draw.lines(surface, (0, 120, 0), False, points, 6)
        # Strato 1
        pygame.draw.lines(surface, (0, 160, 0), False, points, 4)
        # Linea principale
        pygame.draw.lines(surface, color, False, points, 2)

# Funzione per disegnare le informazioni di sistema
def draw_system_info(surface, cpu_values, mem_values, cpu_index, mem_index, fps, width, height):
    # Leggi i valori correnti
    current_cpu = psutil.cpu_percent()
    current_mem = psutil.virtual_memory().percent
    
    # Aggiorna le liste con i nuovi valori
    cpu_values[cpu_index] = current_cpu
    mem_values[mem_index] = current_mem
    
    # Aggiorna gli indici in modo circolare
    cpu_index = (cpu_index + 1) % len(cpu_values)
    mem_index = (mem_index + 1) % len(mem_values)
    
    # Calcola le medie
    avg_cpu = sum(cpu_values) / len(cpu_values)
    avg_mem = sum(mem_values) / len(mem_values)

    # Formatta i valori con un numero fisso di cifre decimali (1 decimale)
    cpu_formatted = f"{avg_cpu:.1f}".rjust(5)
    mem_formatted = f"{avg_mem:.1f}".rjust(5)
    
    # Visualizza tutte le informazioni di sistema su una singola linea in basso
    info_text = f"CPU: {cpu_formatted}% | MEM: {mem_formatted}% | FPS: {fps} | RES: {width}x{height}"
    info_surface = font.render(info_text, True, (255, 255, 255))
    
    # Posiziona il testo centrato nella parte inferiore dello schermo
    info_x = (width - info_surface.get_width()) // 2
    info_y = height - info_surface.get_height() - 20
    surface.blit(info_surface, (info_x, info_y))
    
    return cpu_index, mem_index

# Variabile per controllare la visibilità dell'overlay
show_overlay = True

# Variabile per animare la sinusoide
wave_offset = 0

# Variabili per il calcolo delle medie
cpu_values = [0] * 10  # Lista per memorizzare gli ultimi 10 valori di CPU
mem_values = [0] * 10  # Lista per memorizzare gli ultimi 10 valori di MEM
cpu_index = 0  # Indice corrente nella lista
mem_index = 0  # Indice corrente nella lista

running = True
# Variabile per il calcolo del framerate
frame_count = 0
fps = 0
last_time = time.time()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_F1:
                # Cambia lo stato dell'overlay quando F1 viene premuto
                show_overlay = not show_overlay

    screen.fill((0, 0, 0))

    # Griglia
    if show_overlay:
      draw_grid(screen)
    
    # Disegna la sinusoide animata
    draw_sinusoid(screen, wave_offset)
    wave_offset += 0.05  # Incrementa l'offset per animare la sinusoide

    # Calcolo del framerate
    frame_count += 1
    current_time = time.time()
    if current_time - last_time > 1.0:
        fps = frame_count
        frame_count = 0
        last_time = current_time

    # Mostra le informazioni di sistema solo se l'overlay è attivo
    if show_overlay:
        cpu_index, mem_index = draw_system_info(screen, cpu_values, mem_values, cpu_index, mem_index, fps, width, height)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
