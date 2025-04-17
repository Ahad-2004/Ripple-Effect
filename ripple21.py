import pygame
import numpy as np
import math
import random

pygame.init()

# Screen dimensions and setup
WIDTH, HEIGHT = 1400, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Liquid Droplet Impact Simulation")

# --- Colors ---
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
TOGGLE_COLOR = (100, 100, 100)
TOGGLE_HOVER_COLOR = (120, 120, 120)

# --- Fonts ---
FONT_DEFAULT = pygame.font.SysFont("Arial", 20)
FONT_SCALE = pygame.font.SysFont("Arial", 14)
FONT_TITLE = pygame.font.SysFont("Arial", 24, bold=True)
DATA_LABEL_FONT = pygame.font.SysFont("Arial", 18)
DATA_VALUE_FONT = pygame.font.SysFont("Arial", 18, bold=True)
DATA_UNIT_FONT = pygame.font.SysFont("Arial", 16)
INPUT_FONT = pygame.font.SysFont("Arial", 20)

# --- Simulation parameters ---
water_surface = np.zeros(WIDTH)
wave_speed = 150.0
drop_height = 200.0
drop_y = drop_height
drop_fall_speed = 8.0
ripple_time = 0.0
ripple_decay = 0.008
drop_radius = 18.0
ripple_amplitude = drop_radius * 3.5
wave_frequency = 1.8
surface_tension = 0.002
proximity_threshold = 50.0
pre_impact_amplitude_factor = 0.5
viscosity = 0.005
droplet_deformation_rate = 0.05
splash_particle_variation = 1.5
ripple_damping_factor = 0.001
wavelength_variation = 0.2
splash_particle_speed = 3.5
splash_particle_count = 30
wave_layers = 5  # Number of wave lines to draw in side view
circle_count = 10 # Number of concentric circles to create
start_radius_increment = 5 # Spacing/gap between initial circles

# --- Buttons ---
BUTTON_WIDTH, BUTTON_HEIGHT = 120, 40
pause_button = pygame.Rect(1020, 660, BUTTON_WIDTH, BUTTON_HEIGHT)
unpause_button = pygame.Rect(1150, 660, BUTTON_WIDTH, BUTTON_HEIGHT)
start_button = pygame.Rect(1020, 720, BUTTON_WIDTH, BUTTON_HEIGHT)
reset_button = pygame.Rect(1150, 720, BUTTON_WIDTH, BUTTON_HEIGHT)
restart_button = pygame.Rect(1280, 720, BUTTON_WIDTH, BUTTON_HEIGHT)
toggle_view_button = pygame.Rect(1280, 660, BUTTON_WIDTH, BUTTON_HEIGHT)

# --- Input Boxes ---
INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT = 80, 30
angle_input_box = pygame.Rect(1120, 100, INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT)
size_input_box = pygame.Rect(1120, 140, INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT)
active_input_box = None
angle_input_text = ""
size_input_text = ""

# --- Simulation states ---
simulation_started = False
simulation_paused = False
drop_hit_water = False
drop_x_initial = WIDTH // 3
drop_x = drop_x_initial
drop_angle = 45.0
initial_drop_x_ripple_origin = drop_x_initial
splash_particles = []
circle_radii = []
bird_eye_view = False  # Initially side view

# Modified wave object structure
class Wave:
    def __init__(self, x, y, radius, velocity, amplitude, start_time):
        self.x = x
        self.y = y
        self.radius = radius
        self.velocity = velocity
        self.amplitude = amplitude
        self.start_time = start_time

def reset_simulation():
    global drop_hit_water, drop_y, ripple_time, water_surface, drop_x, ripple_amplitude, drop_radius, circle_radii, splash_particles, drop_x_initial, drop_x, initial_drop_x_ripple_origin, angle_input_text, size_input_text
    drop_hit_water = False
    drop_y = drop_height
    ripple_time = 0.0
    water_surface[:] = 0.0
    drop_x = drop_x_initial
    ripple_amplitude = drop_radius * 3.5
    drop_radius = 18.0
    circle_radii = []
    splash_particles = []
    initial_drop_x_ripple_origin = drop_x_initial
    angle_input_text = ""
    size_input_text = ""

def display_data_panel(screen, font, drop_y, drop_x, ripple_amplitude, ripple_time):
    pygame.draw.rect(screen, PANEL_BG_COLOR, (1000, 20, 380, 760), border_radius=12) # Increased panel height to contain buttons visually
    pygame.draw.rect(screen, PANEL_BORDER_COLOR, (1000, 20, 380, 760), 2, border_radius=12) # Increased panel height to contain buttons visually
    draw_text("Simulation Data", FONT_TITLE, TEXT_COLOR, screen, 1020, 30)

    # --- View Label ---
    view_text = "View: Top" if bird_eye_view else "View: Side"
    draw_text(view_text, DATA_LABEL_FONT, TEXT_COLOR, screen, 1020, 70) # Added view label

    # --- Input Boxes and Labels ---
    draw_text("Drop Angle:", DATA_LABEL_FONT, TEXT_COLOR, screen, 1020, 105) # Label for Angle input
    draw_text("Drop Size:", DATA_LABEL_FONT, TEXT_COLOR, screen, 1020, 145)  # Label for Size input
    draw_text("(With reference to x-axis)", DATA_UNIT_FONT, TEXT_COLOR, screen, 1210, 105) # Label for Angle input - smaller font, corrected argument order
    draw_text("(Range 0 to 100)", DATA_UNIT_FONT, TEXT_COLOR, screen, 1210, 145)  # Label for Size input - smaller font, corrected argument order
    pygame.draw.rect(screen, INPUT_BOX_ACTIVE_COLOR if active_input_box == angle_input_box else INPUT_BOX_COLOR, angle_input_box, 2, border_radius=4)
    pygame.draw.rect(screen, INPUT_BOX_ACTIVE_COLOR if active_input_box == size_input_box else INPUT_BOX_COLOR, size_input_box, 2, border_radius=4)
    angle_surface = INPUT_FONT.render(angle_input_text, True, TEXT_COLOR)
    size_surface = INPUT_FONT.render(size_input_text, True, TEXT_COLOR)
    screen.blit(angle_surface, (angle_input_box.x + 5, angle_input_box.y + 5))
    screen.blit(size_surface, (size_input_box.x + 5, size_input_box.y + 5))

    data_groups = [
        ("Drop Properties", [
            ("Height", f"{drop_y:.2f}", "px"),
            ("Radius", f"{drop_radius:.2f}", "px"),
            ("Angle", f"{drop_angle:.2f}", "°"),
        ]),
        ("Ripple Properties", [
            ("Amplitude", f"{ripple_amplitude:.2f}", "px"),
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
    for group_name, data_items in data_groups:
        draw_text(group_name, FONT_TITLE, TEXT_COLOR, screen, 1020, y_offset)
        y_offset += 30
        for label, value, unit in data_items:
            draw_text(f"{label}:", DATA_LABEL_FONT, TEXT_COLOR, screen, 1030, y_offset)
            draw_text(value, DATA_VALUE_FONT, TEXT_COLOR, screen, 1220, y_offset)
            draw_text(unit, DATA_UNIT_FONT, TEXT_COLOR, screen, 1300, y_offset)
            y_offset += 25
        y_offset += 15
        pygame.draw.line(screen, PANEL_BORDER_COLOR,(1010, y_offset - 10),(1370, y_offset - 10), 1)

def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, True, color)
    surface.blit(text_obj, (x, y))

def generate_ripple_effect(drop_x, drop_y, ripple_time, ripple_amplitude, pre_impact=False, ripple_width=None):
    if pre_impact:
        pre_amp = ripple_amplitude * pre_impact_amplitude_factor
    else:
        pre_amp = ripple_amplitude
    for x in range(WIDTH):
        if ripple_width is not None:
            if abs(x - drop_x) > ripple_width:
                continue
        distance = np.sqrt((x - drop_x) ** 2 + (HEIGHT // 2 - drop_y) ** 2)
        if distance == 0:
            continue
        height = (
            pre_amp
            * np.exp(-distance / 120.0)
            * np.exp(-(ripple_decay + viscosity) * ripple_time)
            * np.sin((distance / wave_speed * (wave_frequency + random.uniform(-wavelength_variation, wavelength_variation))) - ripple_time * 2 * np.pi)
            * np.exp(-distance * ripple_damping_factor)
        )
        water_surface[x] = height


def update_circles():
    global circle_radii
    new_circles = []
    for wave in circle_radii:
        wave.radius += wave.velocity * 0.02
        wave.amplitude *= math.exp(-ripple_decay * 0.02)
        if wave.amplitude > 0.005: # Further reduced amplitude threshold for longer fading

            # --- Wave Boundary Reflection ---
            if wave.x - wave.radius < 0:
                wave.velocity *= -1
                wave.x = wave.radius # Keep wave within bounds
            if wave.x + wave.radius > WIDTH:
                wave.velocity *= -1
                wave.x = WIDTH - wave.radius # Keep wave within bounds
            if wave.y - wave.radius < 0:
                wave.velocity *= -1 # Reflect vertically as well
                wave.y = wave.radius # Keep wave within bounds
            if wave.y + wave.radius > HEIGHT:
                wave.velocity *= -1 # Reflect vertically
                wave.y = HEIGHT - wave.radius # Keep wave within bounds

            # Wave interaction (crude - just amplitude reduction upon overlap)
            for other_wave in circle_radii:
                if wave != other_wave:
                    distance = math.sqrt((wave.x - other_wave.x)**2 + (wave.y - other_wave.y)**2)
                    if distance < wave.radius + other_wave.radius:
                        overlap = (wave.radius + other_wave.radius - distance)
                        wave.amplitude -= overlap * 0.005  # reduce amplitude slightly upon overlap
                        other_wave.amplitude -= overlap * 0.005

            new_circles.append(wave)
    circle_radii = new_circles

def draw_scale():
    for i in range(1, 11):
        y_pos = HEIGHT - (i * (HEIGHT // 10))
        pygame.draw.line(screen, TEXT_COLOR, (50, y_pos), (70, y_pos), 2)
        scale_text = FONT_SCALE.render(f"{i}", True, TEXT_COLOR)
        screen.blit(scale_text, (20, y_pos - 8))

def create_splash(drop_x, drop_y, num_particles=splash_particle_count):
    for _ in range(num_particles):
        angle = np.random.uniform(0, 2 * np.pi)
        speed = np.random.uniform(splash_particle_speed * 0.7 * splash_particle_variation, splash_particle_speed * 1.3 * splash_particle_variation)
        lifetime = np.random.uniform(0.6, 1.6)
        size = np.random.uniform(2, 6)
        particle = {
            "x": drop_x + np.random.uniform(-drop_radius / 2, drop_radius / 2),
            "y": drop_y + np.random.uniform(-drop_radius / 2, drop_radius / 2),
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
    if bird_eye_view:
        screen.fill(WATER_COLOR_DEEP)
        if  drop_hit_water and not circle_radii: # Create circles only once upon impact in top view
            for i in range(circle_count): # Create multiple initial circles for concentric effect
                start_radius = i * start_radius_increment # Initial radius offset for each circle
                circle_radii.append(Wave(drop_x, HEIGHT // 2, start_radius, wave_speed + random.uniform(-20, 20), ripple_amplitude * random.uniform(0.8, 1.2), ripple_time))
        for wave in circle_radii:
            if wave.amplitude > 0.005: # Further reduced amplitude threshold for longer fading and visibility
                alpha_val = max(0, min(255, int(255 * (wave.amplitude / (drop_radius * 3.5))))) # Forcefully clamp alpha to 0-255
                # --- Visual Fading: Alpha based on amplitude ---
                alpha_val = max(0, min(255, int(alpha_val * (wave.amplitude / (ripple_amplitude/2))))) # Further reduce alpha as amplitude fades


                color = (DROP_COLOR[0], DROP_COLOR[1], DROP_COLOR[2], alpha_val)

                if not isinstance(color, pygame.Color): # Ensure color is pygame.Color object
                    try:
                        color = pygame.Color(color)
                    except ValueError as e:
                        print(f"Color creation error: {e}, Color value: {color}")
                        continue # Skip drawing if color is invalid

                pygame.draw.circle(screen, color, (int(wave.x), int(wave.y)), int(wave.radius), 2) # Draw circles for top view
    else: # Side view - modified to draw multiple lines for wave effect
        y_base = HEIGHT // 2
        layer_spacing = 4 # Spacing between wave layers
        for layer in range(wave_layers):
            y_offset = layer * layer_spacing - (wave_layers - 1) * layer_spacing / 2 # Center layers around y_base
            y_level = y_base + y_offset
            color_intensity = int(WATER_COLOR_SURFACE[2] + y_offset * 5) # Adjust color intensity for depth
            color_intensity = max(0, min(255, color_intensity))
            wave_color = (WATER_COLOR_SURFACE[0], WATER_COLOR_SURFACE[1], color_intensity)

            for x in range(0, WIDTH, 5): # Draw short line segments, step of 5 for performance
                height = int(y_level + water_surface[x])
                pygame.draw.line(screen, wave_color, (x, height), (x + 5, height)) # Short horizontal lines


def draw_drop():
    if simulation_started and not drop_hit_water:
        if bird_eye_view:
            pygame.draw.circle(screen, DROP_COLOR, (int(drop_x), int(drop_y)), int(drop_radius))
        else:
            deform = 1 + ((HEIGHT // 2) - drop_y) / (proximity_threshold * 2)
            pygame.draw.ellipse(screen, DROP_COLOR, (int(drop_x - drop_radius), int(drop_y - drop_radius * deform), int(drop_radius * 2), int(drop_radius * 2 * deform)))

def draw_lighting():
    light_pos = (WIDTH // 4, HEIGHT // 4)
    light_intensity_max = 20 # Reduced for softer lighting
    for x in range(WIDTH):
        distance = np.sqrt((x - light_pos[0]) ** 2 + (HEIGHT // 2 - light_pos[1]) ** 2)
        light_intensity = max(0, min(light_intensity_max, int(200 / (distance + 100))))
        pygame.draw.line(screen, (light_intensity, light_intensity, light_intensity), (x, HEIGHT // 2), (x, HEIGHT))

running = True
clock = pygame.time.Clock()

while running:
    screen.fill(BG_COLOR)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if start_button.collidepoint(mouse_pos):
                try:
                    drop_angle = float(angle_input_text) if angle_input_text else drop_angle
                    drop_radius = float(size_input_text) if size_input_text else drop_radius
                    ripple_amplitude = drop_radius * 3.5
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
            elif toggle_view_button.collidepoint(mouse_pos):
                bird_eye_view = not bird_eye_view
            else:
                active_input_box = None
        if event.type == pygame.KEYDOWN:
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

    for y in range(HEIGHT):
        intensity = int(WATER_COLOR_DEEP[2] + (WATER_COLOR_SURFACE[2] - WATER_COLOR_DEEP[2]) * (y / HEIGHT))
        pygame.draw.line(screen, (WATER_COLOR_DEEP[0], WATER_COLOR_DEEP[1], intensity), (0, y), (WIDTH, y))

    if simulation_started and not drop_hit_water:
        if drop_y >= (HEIGHT // 2) - proximity_threshold:
            drop_radius += droplet_deformation_rate

    if simulation_started and not drop_hit_water:
        if drop_y >= (HEIGHT // 2) - (proximity_threshold / 2):
            generate_ripple_effect(initial_drop_x_ripple_origin, drop_y, ripple_time, ripple_amplitude * (1 - ((HEIGHT // 2) - drop_y) / proximity_threshold), pre_impact=True, ripple_width=200)
        else:
            water_surface[:] = 0

    draw_lighting()

    if drop_hit_water:
        if bird_eye_view and not circle_radii: # Create circles only once upon impact in top view
            for i in range(circle_count): # Create multiple initial circles for concentric effect
                start_radius = i * start_radius_increment # Initial radius offset for each circle
                circle_radii.append(Wave(drop_x, HEIGHT // 2, start_radius, wave_speed + random.uniform(-20, 20), ripple_amplitude * random.uniform(0.8, 1.2), ripple_time))
        if bird_eye_view:
            update_circles()
        else:
            generate_ripple_effect(drop_x, HEIGHT // 2, ripple_time, ripple_amplitude)

    draw_water_surface()
    draw_drop()
    draw_scale()

    display_data_panel(screen, FONT_DEFAULT, drop_y, drop_x, ripple_amplitude, ripple_time) # Data panel drawn FIRST now

    # --- Button Drawing (Buttons drawn AFTER data panel) ---
    pygame.draw.rect(screen, BUTTON_HOVER_COLOR if start_button.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR, start_button, border_radius=8)
    pygame.draw.rect(screen, RESET_HOVER_COLOR if reset_button.collidepoint(pygame.mouse.get_pos()) else RESET_COLOR, reset_button, border_radius=8)
    pygame.draw.rect(screen, RESTART_HOVER_COLOR if restart_button.collidepoint(pygame.mouse.get_pos()) else RESTART_COLOR, restart_button, border_radius=8)
    pygame.draw.rect(screen, PAUSE_HOVER_COLOR if pause_button.collidepoint(pygame.mouse.get_pos()) else PAUSE_COLOR, pause_button, border_radius=8)
    pygame.draw.rect(screen, UNPAUSE_HOVER_COLOR if unpause_button.collidepoint(pygame.mouse.get_pos()) else UNPAUSE_COLOR, unpause_button, border_radius=8)
    pygame.draw.rect(screen, TOGGLE_HOVER_COLOR if toggle_view_button.collidepoint(pygame.mouse.get_pos()) else TOGGLE_COLOR, toggle_view_button, border_radius=8)

    draw_text("Start", FONT_DEFAULT, TEXT_COLOR, screen, start_button.x + 35, start_button.y + 10)
    draw_text("Reset", FONT_DEFAULT, TEXT_COLOR, screen, reset_button.x + 35, reset_button.y + 10)
    draw_text("Restart", FONT_DEFAULT, TEXT_COLOR, screen, restart_button.x + 25, restart_button.y + 10)
    draw_text("Pause", FONT_DEFAULT, TEXT_COLOR, screen, pause_button.x + 35, pause_button.y + 10)
    draw_text("Unpause", FONT_DEFAULT, TEXT_COLOR, screen, unpause_button.x + 25, unpause_button.y + 10)
    draw_text("View", FONT_DEFAULT, TEXT_COLOR, screen, toggle_view_button.x + 35, toggle_view_button.y + 10)


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
            if bird_eye_view and ripple_amplitude < 0.005: # Reset in top view when ripples are very faint
                reset_simulation()
                simulation_started = False
            elif ripple_amplitude < 0.01 and not bird_eye_view: # Keep circles for top view longer, reduced amplitude threshold
                reset_simulation()
                simulation_started = False


    update_splash_particles()
    draw_splash_particles()

    pygame.display.update()
    clock.tick(60)

pygame.quit()