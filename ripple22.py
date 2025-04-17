import pygame
import numpy as np
import math
import random

pygame.init()

# =======================
# Configuration Constants
# =======================
WIDTH, HEIGHT = 1400, 800
BG_COLOR = (20, 20, 30)
WATER_COLOR_DEEP = (10, 30, 70)
WATER_COLOR_SURFACE = (30, 60, 120)
DROP_COLOR = (0, 180, 230)
PANEL_BG_COLOR = (50, 50, 60)
PANEL_BORDER_COLOR = (80, 80, 90)
TEXT_COLOR = (220, 220, 220)
BUTTON_COLOR = (60, 80, 150)
BUTTON_HOVER_COLOR = (80, 100, 180)
RESET_COLOR = (160, 60, 60)
RESET_HOVER_COLOR = (180, 80, 80)
RESTART_COLOR = (80, 150, 80)
RESTART_HOVER_COLOR = (100, 180, 100)
PAUSE_COLOR = (150, 80, 60)
PAUSE_HOVER_COLOR = (180, 100, 80)
UNPAUSE_COLOR = (80, 150, 60)
UNPAUSE_HOVER_COLOR = (100, 180, 80)
INPUT_BOX_COLOR = (70, 70, 80)
INPUT_BOX_ACTIVE_COLOR = (90, 90, 120)

# Set to False to disable droplet deformation during descent
ENABLE_DEFORMATION = False

# -----------------------
# Fonts and Screen Setup
# -----------------------
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Liquid Droplet Impact Simulation")
FONT_DEFAULT = pygame.font.SysFont("Arial", 20)
FONT_SCALE = pygame.font.SysFont("Arial", 14)
FONT_TITLE = pygame.font.SysFont("Arial", 24, bold=True)
DATA_LABEL_FONT = pygame.font.SysFont("Arial", 18)
DATA_VALUE_FONT = pygame.font.SysFont("Arial", 18, bold=True)
DATA_UNIT_FONT = pygame.font.SysFont("Arial", 16)
INPUT_FONT = pygame.font.SysFont("Arial", 20)

# ======================
# Simulation Parameters
# ======================
water_surface = np.zeros(WIDTH)
wave_speed = 150.0
drop_height = 200.0
drop_fall_speed = 8.0
ripple_decay = 0.008
default_drop_radius = 18.0
drop_radius = default_drop_radius
ripple_amplitude = drop_radius * 3.5
wave_frequency = 1.8
surface_tension = 0.002
proximity_threshold = 50.0
pre_impact_amplitude_factor = 0.5
viscosity = 0.005
# droplet_deformation_rate is still defined in case you want to adjust deformation
droplet_deformation_rate = 0.05
splash_particle_variation = 1.5
ripple_damping_factor = 0.001
wavelength_variation = 0.2
splash_particle_speed = 3.5
splash_particle_count = 30

# =====================
# UI Elements and State
# =====================
BUTTON_WIDTH, BUTTON_HEIGHT = 120, 40
pause_button = pygame.Rect(1020, 660, BUTTON_WIDTH, BUTTON_HEIGHT)
unpause_button = pygame.Rect(1150, 660, BUTTON_WIDTH, BUTTON_HEIGHT)
start_button = pygame.Rect(1020, 720, BUTTON_WIDTH, BUTTON_HEIGHT)
reset_button = pygame.Rect(1150, 720, BUTTON_WIDTH, BUTTON_HEIGHT)
restart_button = pygame.Rect(1280, 720, BUTTON_WIDTH, BUTTON_HEIGHT)

INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT = 80, 30
angle_input_box = pygame.Rect(1120, 100, INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT)
size_input_box = pygame.Rect(1120, 140, INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT)
active_input_box = None
angle_input_text = ""
size_input_text = ""

simulation_started = False
simulation_paused = False
drop_hit_water = False
drop_x_initial = WIDTH // 3
drop_x = drop_x_initial
drop_y = drop_height
drop_angle = 45.0
ripple_time = 0.0
initial_drop_x_ripple_origin = drop_x_initial

splash_particles = []
# (circle_radii removed as it is no longer used)

# ============
# Helper Functions
# ============
def reset_simulation():
    global drop_hit_water, drop_y, ripple_time, water_surface, drop_x, ripple_amplitude, drop_radius, splash_particles, initial_drop_x_ripple_origin, angle_input_text, size_input_text
    drop_hit_water = False
    drop_y = drop_height
    ripple_time = 0.0
    water_surface[:] = 0.0
    drop_x = drop_x_initial
    drop_radius = default_drop_radius
    ripple_amplitude = drop_radius * 3.5
    splash_particles = []
    initial_drop_x_ripple_origin = drop_x_initial
    angle_input_text = ""
    size_input_text = ""

def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, True, color)
    surface.blit(text_obj, (x, y))

def display_data_panel(screen):
    # Draw panel background and border
    panel_rect = (1000, 20, 380, 680)
    pygame.draw.rect(screen, PANEL_BG_COLOR, panel_rect, border_radius=12)
    pygame.draw.rect(screen, PANEL_BORDER_COLOR, panel_rect, 2, border_radius=12)
    draw_text("Simulation Data", FONT_TITLE, TEXT_COLOR, screen, 1020, 30)
    
    # Input boxes and labels
    draw_text("Drop Angle:", DATA_LABEL_FONT, TEXT_COLOR, screen, 1020, 105)
    draw_text("Drop Size:", DATA_LABEL_FONT, TEXT_COLOR, screen, 1020, 145)
    draw_text("(With reference to x-axis)", DATA_LABEL_FONT, TEXT_COLOR, screen, 1210, 105)
    draw_text("(Range 0 to 100)", DATA_LABEL_FONT, TEXT_COLOR, screen, 1210, 145)
    pygame.draw.rect(screen, INPUT_BOX_ACTIVE_COLOR if active_input_box == angle_input_box else INPUT_BOX_COLOR, angle_input_box, 2, border_radius=4)
    pygame.draw.rect(screen, INPUT_BOX_ACTIVE_COLOR if active_input_box == size_input_box else INPUT_BOX_COLOR, size_input_box, 2, border_radius=4)
    
    angle_surface = INPUT_FONT.render(angle_input_text, True, TEXT_COLOR)
    size_surface = INPUT_FONT.render(size_input_text, True, TEXT_COLOR)
    screen.blit(angle_surface, (angle_input_box.x + 5, angle_input_box.y + 5))
    screen.blit(size_surface, (size_input_box.x + 5, size_input_box.y + 5))
    
    # Data grouping for display
    data_groups = [
        ("Droplet", [
            ("Drop Y", f"{drop_y:.2f}", "px"),
            ("Drop X", f"{drop_x:.2f}", "px"),
            ("Radius", f"{drop_radius:.2f}", "px"),
            ("Angle", f"{drop_angle:.2f}", "degrees"),
        ]),
        ("Ripple", [
            ("Amplitude", f"{ripple_amplitude:.2f}", "px"),
            ("Time", f"{ripple_time:.2f}", "s"),
            ("Speed", f"{wave_speed:.2f}", "px/s"),
            ("Decay", f"{ripple_decay:.4f}", ""),
            ("Frequency", f"{wave_frequency:.2f}", ""),
            ("Viscosity", f"{viscosity:.4f}", ""),
            ("Damping", f"{ripple_damping_factor:.4f}", ""),
            ("Wavelength Var", f"{wavelength_variation:.2f}", ""),
        ]),
        ("Splash", [
            ("Particle Speed", f"{splash_particle_speed:.2f}", "px/s"),
            ("Particle Variation", f"{splash_particle_variation:.2f}", ""),
            ("Particle Count", f"{splash_particle_count}", ""),
        ]),
    ]
    
    y_offset = 180
    for group_name, items in data_groups:
        draw_text(group_name, FONT_TITLE, TEXT_COLOR, screen, 1020, y_offset)
        y_offset += 30
        for label, value, unit in items:
            draw_text(f"{label}:", DATA_LABEL_FONT, TEXT_COLOR, screen, 1030, y_offset)
            draw_text(value, DATA_VALUE_FONT, TEXT_COLOR, screen, 1220, y_offset)
            draw_text(unit, DATA_UNIT_FONT, TEXT_COLOR, screen, 1300, y_offset)
            y_offset += 25
        y_offset += 15
        pygame.draw.line(screen, PANEL_BORDER_COLOR, (1010, y_offset - 10), (1370, y_offset - 10), 1)

def generate_ripple_effect(drop_x_val, drop_y_val, current_time, amplitude, pre_impact=False, ripple_width=None):
    if pre_impact:
        effective_amp = amplitude * pre_impact_amplitude_factor
    else:
        effective_amp = amplitude
    for x in range(WIDTH):
        if ripple_width is not None and abs(x - drop_x_val) > ripple_width:
            continue
        distance = np.sqrt((x - drop_x_val) ** 2 + (HEIGHT // 2 - drop_y_val) ** 2)
        if distance == 0:
            continue
        water_surface[x] = (
            effective_amp *
            np.exp(-distance / 120.0) *
            np.exp(-(ripple_decay + viscosity) * current_time) *
            np.sin((distance / wave_speed * (wave_frequency + random.uniform(-wavelength_variation, wavelength_variation))) - current_time * 2 * np.pi) *
            np.exp(-distance * ripple_damping_factor)
        )

def draw_scale():
    for i in range(1, 11):
        y_pos = HEIGHT - (i * (HEIGHT // 10))
        pygame.draw.line(screen, TEXT_COLOR, (50, y_pos), (70, y_pos), 2)
        scale_text = FONT_SCALE.render(f"{i}", True, TEXT_COLOR)
        screen.blit(scale_text, (20, y_pos - 8))

def create_splash(drop_x_val, drop_y_val, num_particles=splash_particle_count):
    for _ in range(num_particles):
        angle = np.random.uniform(0, 2 * np.pi)
        speed = np.random.uniform(splash_particle_speed * 0.7 * splash_particle_variation,
                                  splash_particle_speed * 1.3 * splash_particle_variation)
        lifetime = np.random.uniform(0.6, 1.6)
        size = np.random.uniform(2, 6)
        particle = {
            "x": drop_x_val + np.random.uniform(-drop_radius / 2, drop_radius / 2),
            "y": drop_y_val + np.random.uniform(-drop_radius / 2, drop_radius / 2),
            "vx": speed * np.cos(angle),
            "vy": -speed * np.sin(angle),
            "life": lifetime,
            "size": size
        }
        splash_particles.append(particle)

def update_splash_particles():
    for particle in splash_particles[:]:
        particle["x"] += particle["vx"]
        particle["y"] += particle["vy"]
        particle["vy"] += 0.1
        if particle["y"] > HEIGHT // 2 and particle["vy"] > 0:
            particle["vy"] *= -0.4
        particle["life"] -= 0.04
        if particle["life"] <= 0:
            splash_particles.remove(particle)

def draw_splash_particles():
    for particle in splash_particles:
        alpha = max(0, int(255 * (particle["life"] / 1.6)))
        color = (DROP_COLOR[0], DROP_COLOR[1], DROP_COLOR[2], alpha)
        pygame.draw.circle(screen, color, (int(particle["x"]), int(particle["y"])), int(particle["size"]))

def draw_water_surface():
    for x in range(WIDTH):
        height_val = int(HEIGHT // 2 + water_surface[x])
        color_intensity = max(0, min(255, int(120 + water_surface[x] * 5)))
        pygame.draw.line(screen, (WATER_COLOR_SURFACE[0], WATER_COLOR_SURFACE[1], color_intensity), (x, height_val), (x, HEIGHT))

def draw_drop():
    # If deformation is enabled, compute a deformation factor; otherwise, use 1.0 for a perfect circle.
    if simulation_started and not drop_hit_water:
        deform = 1 + ((HEIGHT // 2) - drop_y) / (proximity_threshold * 2) if ENABLE_DEFORMATION else 1.0
        pygame.draw.ellipse(screen, DROP_COLOR, (
            int(drop_x - drop_radius),
            int(drop_y - drop_radius * deform),
            int(drop_radius * 2),
            int(drop_radius * 2 * deform)
        ))

def draw_lighting():
    light_pos = (WIDTH // 4, HEIGHT // 4)
    for x in range(WIDTH):
        distance = np.sqrt((x - light_pos[0]) ** 2 + (HEIGHT // 2 - light_pos[1]) ** 2)
        light_intensity = max(0, min(20, int(200 / (distance + 100))))
        pygame.draw.line(screen, (light_intensity, light_intensity, light_intensity, 30), (x, HEIGHT // 2), (x, HEIGHT))

# ====================
# Main Simulation Loop
# ====================
running = True
clock = pygame.time.Clock()

while running:
    screen.fill(BG_COLOR)

    # ------------------
    # Event Handling
    # ------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if start_button.collidepoint(mouse_pos):
                try:
                    drop_angle = float(angle_input_text) if angle_input_text else drop_angle
                    drop_radius = float(size_input_text) if size_input_text else drop_radius
                    ripple_amplitude = drop_radius * 3.5
                    reset_simulation()
                    simulation_started = True
                    initial_drop_x_ripple_origin = drop_x_initial
                except ValueError:
                    print("Invalid input. Please enter numbers for angle and size.")
            elif reset_button.collidepoint(mouse_pos):
                reset_simulation()
                simulation_started = False
            elif restart_button.collidepoint(mouse_pos):
                reset_simulation()
                simulation_started = True
            elif pause_button.collidepoint(mouse_pos):
                simulation_paused = True
            elif unpause_button.collidepoint(mouse_pos):
                simulation_paused = False
            elif angle_input_box.collidepoint(mouse_pos):
                active_input_box = angle_input_box
            elif size_input_box.collidepoint(mouse_pos):
                active_input_box = size_input_box
            else:
                active_input_box = None

        elif event.type == pygame.KEYDOWN:
            if active_input_box == angle_input_box:
                if event.key == pygame.K_BACKSPACE:
                    angle_input_text = angle_input_text[:-1]
                elif event.unicode.isdigit() or event.unicode == '.':
                    angle_input_text += event.unicode
            elif active_input_box == size_input_box:
                if event.key == pygame.K_BACKSPACE:
                    size_input_text = size_input_text[:-1]
                elif event.unicode.isdigit() or event.unicode == '.':
                    size_input_text += event.unicode

    # ------------------
    # Drawing Background
    # ------------------
    for y in range(HEIGHT):
        intensity = int(WATER_COLOR_DEEP[2] + (WATER_COLOR_SURFACE[2] - WATER_COLOR_DEEP[2]) * (y / HEIGHT))
        pygame.draw.line(screen, (WATER_COLOR_DEEP[0], WATER_COLOR_DEEP[1], intensity), (0, y), (WIDTH, y))

    # -----------------------
    # Droplet and Ripple Updates
    # -----------------------
    # Optional droplet deformation update
    if simulation_started and not drop_hit_water and ENABLE_DEFORMATION:
        if drop_y >= (HEIGHT // 2) - proximity_threshold:
            drop_radius += droplet_deformation_rate

    # Pre-impact ripple effect
    if simulation_started and not drop_hit_water:
        if drop_y >= (HEIGHT // 2) - (proximity_threshold / 2):
            generate_ripple_effect(initial_drop_x_ripple_origin, drop_y, ripple_time,
                                   ripple_amplitude * (1 - ((HEIGHT // 2) - drop_y) / proximity_threshold),
                                   pre_impact=True, ripple_width=200)
        else:
            water_surface[:] = 0

    draw_lighting()

    # Post-impact ripple generation
    if drop_hit_water:
        generate_ripple_effect(drop_x, HEIGHT // 2, ripple_time, ripple_amplitude)

    draw_water_surface()
    draw_drop()
    draw_scale()

    # -----------------
    # Draw UI Buttons
    # -----------------
    for btn, label, offset in [
        (start_button, "Start", 35),
        (reset_button, "Reset", 35),
        (restart_button, "Restart", 25),
        (pause_button, "Pause", 35),
        (unpause_button, "Unpause", 25)
    ]:
        color = BUTTON_HOVER_COLOR if btn.collidepoint(pygame.mouse.get_pos()) else (
            RESET_COLOR if btn == reset_button else 
            RESTART_COLOR if btn == restart_button else 
            PAUSE_COLOR if btn == pause_button else 
            UNPAUSE_COLOR if btn == unpause_button else 
            BUTTON_COLOR)
        pygame.draw.rect(screen, color, btn, border_radius=8)
        draw_text(label, FONT_DEFAULT, TEXT_COLOR, screen, btn.x + offset, btn.y + 10)

    # -----------------
    # Simulation Updates
    # -----------------
    if not simulation_paused:
        if simulation_started and not drop_hit_water:
            drop_y += drop_fall_speed * math.cos(math.radians(drop_angle))
            drop_x += drop_fall_speed * math.sin(math.radians(drop_angle))
            drop_x = max(0, min(WIDTH, drop_x))
            if drop_y >= HEIGHT // 2:
                drop_hit_water = True
                create_splash(drop_x, HEIGHT // 2)

        if drop_hit_water:
            ripple_time += 0.02
            ripple_amplitude *= math.exp(-(ripple_decay + viscosity))
            if ripple_amplitude < 0.1:
                reset_simulation()
                simulation_started = False

    update_splash_particles()
    draw_splash_particles()
    display_data_panel(screen)

    pygame.display.update()
    clock.tick(60)

pygame.quit()
