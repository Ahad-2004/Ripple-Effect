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

# Bird's Eye View Toggle
BIRD_EYE_VIEW = False

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
# Simulation Parameters (3D water surface, bird's eye view)
# ======================
GRID_SIZE = 120  # Number of grid points per side (adjust for performance/quality, lowered for better FPS)
water_y = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)  # displacement (height)
water_v = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)  # velocity
water_a = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)  # acceleration

# Physics parameters
spring_k = 0.04  # spring constant
damping = 0.985  # damping factor (viscosity)
spread = 0.15    # how much neighboring points affect each other
gravity = 0.5
drop_mass = 1.0
drop_radius = 18.0
default_drop_radius = 18.0
drop_height = 200.0
drop_fall_speed = 8.0
drop_y = drop_height
drop_x = WIDTH // 3
drop_vy = 0.0
drop_angle = 45.0
proximity_threshold = 50.0
splash_particle_variation = 1.5
splash_particle_speed = 3.5
splash_particle_count = 30

# Scaling factor for kinetic energy transfer to water (tune for visible ripples)
RIPPLE_ENERGY_SCALE = 0.2

# UI/UX parameters
SLIDER_COLOR = (120, 180, 255)
SLIDER_BG = (40, 40, 60)
SLIDER_KNOB = (200, 220, 255)
SLIDER_WIDTH = 180
SLIDER_HEIGHT = 8
SLIDER_KNOB_RADIUS = 10

# =====================


# UI Elements and State
# =====================
BTTN_X = 1020 + 30  # inside panel, with padding
BTTN_Y0 = 520        # below data fields
BTTN_SPACING = 50
BUTTON_WIDTH, BUTTON_HEIGHT = 320, 38
toggle_view_button = pygame.Rect(BTTN_X, BTTN_Y0 + 0*BTTN_SPACING, BUTTON_WIDTH, BUTTON_HEIGHT)
start_button = pygame.Rect(BTTN_X, BTTN_Y0 + 1*BTTN_SPACING, BUTTON_WIDTH, BUTTON_HEIGHT)
reset_button = pygame.Rect(BTTN_X, BTTN_Y0 + 2*BTTN_SPACING, BUTTON_WIDTH, BUTTON_HEIGHT)
restart_button = pygame.Rect(BTTN_X, BTTN_Y0 + 3*BTTN_SPACING, BUTTON_WIDTH, BUTTON_HEIGHT)
pause_button = pygame.Rect(BTTN_X, BTTN_Y0 + 4*BTTN_SPACING, BUTTON_WIDTH, BUTTON_HEIGHT)
unpause_button = pygame.Rect(BTTN_X, BTTN_Y0 + 5*BTTN_SPACING, BUTTON_WIDTH, BUTTON_HEIGHT)
BIRD_EYE_VIEW = True  # Start in top view

# Minimize state for info panel
panel_minimized = False
# Minimize button (top-right of panel)
panel_min_btn_rect = pygame.Rect(380-36, 28, 28, 28)

INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT = 80, 30
angle_input_box = pygame.Rect(1120, 100, INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT)
size_input_box = pygame.Rect(1120, 140, INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT)
active_input_box = None
angle_input_text = ""
size_input_text = ""

simulation_started = False
simulation_paused = False
drop_hit_water = False

# 3D drop position (x, z, y)
drop_x = GRID_SIZE // 2
drop_z = GRID_SIZE // 2
drop_y = drop_height
drop_angle = 45.0
ripple_time = 0.0
initial_drop_x_ripple_origin = drop_x

splash_particles = []

# For bird's eye view ripples (now handled by 2D grid)
circle_ripples = []

# ============
# Helper Functions
# ============
def reset_simulation():
    global drop_hit_water, drop_y, drop_vy, drop_fall_speed, water_y, water_v, water_a, drop_x, drop_z, drop_radius, splash_particles, angle_input_text, size_input_text
    drop_hit_water = False
    drop_y = drop_height
    drop_vy = 0.0
    drop_fall_speed = 8.0
    water_y.fill(0.0)
    water_v.fill(0.0)
    water_a.fill(0.0)
    drop_x = GRID_SIZE // 2
    drop_z = GRID_SIZE // 2
    # Do not reset drop_radius here; keep user-set value
    splash_particles = []
    angle_input_text = ""
    size_input_text = ""

def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, True, color)
    surface.blit(text_obj, (x, y))

def display_data_panel(screen):
    # Draw panel background, border, and shadow (move to left)
    global panel_minimized
    panel_rect = (20, 20, 380, 760)
    shadow_rect = (panel_rect[0]+6, panel_rect[1]+8, panel_rect[2], panel_rect[3])
    pygame.draw.rect(screen, (30,30,40,120), shadow_rect, border_radius=18)
    pygame.draw.rect(screen, PANEL_BG_COLOR, panel_rect, border_radius=16)
    pygame.draw.rect(screen, PANEL_BORDER_COLOR, panel_rect, 2, border_radius=16)
    draw_text("Simulation Data", FONT_TITLE, TEXT_COLOR, screen, 40, 30)
    # Draw minimize/collapse button (top-right)
    btn_rect = pygame.Rect(panel_rect[0]+panel_rect[2]-36, panel_rect[1]+8, 28, 28)
    pygame.draw.rect(screen, (80,80,100), btn_rect, border_radius=8)
    # Draw icon: '-' if open, '+' if minimized
    icon = '-' if not panel_minimized else '+'
    icon_color = (220,220,220)
    icon_font = pygame.font.SysFont("Arial", 28, bold=True)
    icon_surf = icon_font.render(icon, True, icon_color)
    icon_rect = icon_surf.get_rect(center=btn_rect.center)
    screen.blit(icon_surf, icon_rect)
    # If minimized, return early (no controls/data)
    if panel_minimized:
        return 20+40  # Just enough for spacing below the button

    # Input boxes and labels
    draw_text("Drop Angle:", DATA_LABEL_FONT, TEXT_COLOR, screen, 40, 105)
    draw_text("Drop Size:", DATA_LABEL_FONT, TEXT_COLOR, screen, 40, 145)
    draw_text("(With reference to x-axis)", DATA_LABEL_FONT, TEXT_COLOR, screen, 230, 105)
    draw_text("(Range 0 to 100)", DATA_LABEL_FONT, TEXT_COLOR, screen, 230, 145)
    # Move input boxes to left
    angle_box_left = 140
    size_box_left = 140
    angle_input_box.x = angle_box_left
    size_input_box.x = size_box_left
    # Draw input boxes with placeholder if empty
    if active_input_box == angle_input_box:
        pygame.draw.rect(screen, INPUT_BOX_ACTIVE_COLOR, angle_input_box, 2, border_radius=4)
    else:
        pygame.draw.rect(screen, INPUT_BOX_COLOR, angle_input_box, 2, border_radius=4)
    if active_input_box == size_input_box:
        pygame.draw.rect(screen, INPUT_BOX_ACTIVE_COLOR, size_input_box, 2, border_radius=4)
    else:
        pygame.draw.rect(screen, INPUT_BOX_COLOR, size_input_box, 2, border_radius=4)
    # Show placeholder if empty
    if angle_input_text:
        angle_surface = INPUT_FONT.render(angle_input_text, True, TEXT_COLOR)
    else:
        angle_surface = INPUT_FONT.render("0-90", True, (150,150,150))
    if size_input_text:
        size_surface = INPUT_FONT.render(size_input_text, True, TEXT_COLOR)
    else:
        size_surface = INPUT_FONT.render("5-100", True, (150,150,150))
    screen.blit(angle_surface, (angle_input_box.x + 5, angle_input_box.y + 5))
    screen.blit(size_surface, (size_input_box.x + 5, size_input_box.y + 5))

    # Data grouping for display
    data_groups = [
        ("Droplet", [
            ("Drop Y", f"{drop_y:.2f}", "px"),
            ("Drop X", f"{drop_x:.2f}", "px"),
            ("Radius", f"{drop_radius:.2f}", "px"),
            ("Angle", f"{drop_angle:.2f}", "degrees"),
            ("Velocity Y", f"{drop_vy:.2f}", "px/frame"),
        ]),
        ("Water Surface", [
            ("Grid Size", f"{GRID_SIZE}x{GRID_SIZE}", ""),
            ("Spring k", f"{spring_k:.3f}", ""),
            ("Damping", f"{damping:.3f}", ""),
            ("Spread", f"{spread:.3f}", ""),
            ("Gravity", f"{gravity:.2f}", ""),
        ]),
        ("Splash", [
            ("Particle Speed", f"{splash_particle_speed:.2f}", "px/s"),
            ("Particle Variation", f"{splash_particle_variation:.2f}", ""),
            ("Particle Count", f"{splash_particle_count}", ""),
        ]),
    ]

    y_offset = 180
    for group_name, items in data_groups:
        draw_text(group_name, FONT_TITLE, TEXT_COLOR, screen, 40, y_offset)
        y_offset += 28
        for label, value, unit in items:
            draw_text(f"{label}:", DATA_LABEL_FONT, TEXT_COLOR, screen, 50, y_offset)
            draw_text(value, DATA_VALUE_FONT, TEXT_COLOR, screen, 220, y_offset)
            draw_text(unit, DATA_UNIT_FONT, TEXT_COLOR, screen, 320, y_offset)
            y_offset += 22
        y_offset += 10
        pygame.draw.line(screen, PANEL_BORDER_COLOR, (30, y_offset - 8), (380, y_offset - 8), 1)
    # Add compact space after data fields for controls
    y_offset += 18
    return y_offset

def generate_ripple_effect(*args, **kwargs):
    # No-op: replaced by 2D grid physics
    pass

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
    # Center the simulation horizontally, allow for info panel width if visible
    global panel_minimized
    sim_width = 700
    sim_height = 700
    # Shift simulation left by 80 pixels for better centering
    shift_left = 80
    if panel_minimized:
        offset_x = max(0, (WIDTH - sim_width) // 2 - shift_left)
    else:
        offset_x = 20 + 380 + max(0, ((WIDTH - (20 + 380) - sim_width) // 2) - shift_left)
    offset_y = 80
    if BIRD_EYE_VIEW:
        # 3D: Render as a shaded height map (bird's eye view) with specular highlight
        cell_size = sim_width // GRID_SIZE
        light_pos = (GRID_SIZE // 2, GRID_SIZE // 2)
        for i in range(GRID_SIZE - 1):
            for j in range(GRID_SIZE - 1):
                h = water_y[i, j]
                # Color by height (blue for low, white for high)
                base = 80 + int(80 * (h / 30.0))
                base = max(0, min(255, base))
                color = [base, base, 200 + base // 4]
                # Fake specular highlight (bright spot follows highest slope facing 'light')
                if 1 <= i < GRID_SIZE-2 and 1 <= j < GRID_SIZE-2:
                    dx = (water_y[i+1, j] - water_y[i-1, j]) * 0.5
                    dz = (water_y[i, j+1] - water_y[i, j-1]) * 0.5
                    # Light direction from above
                    dot = max(0, min(1, 0.5 - 0.5 * (dx + dz)))
                    spec = int(80 * dot)
                    color[0] = min(255, color[0] + spec)
                    color[1] = min(255, color[1] + spec)
                    color[2] = min(255, color[2] + spec)
                x = offset_x + i * cell_size
                y = offset_y + j * cell_size
                pygame.draw.rect(screen, color, (x, y, cell_size, cell_size))

        # Draw animated impact ring if recent impact
        if drop_hit_water and ripple_time < 20:
            impact_x = offset_x + int(drop_x * sim_width / GRID_SIZE)
            impact_y = offset_y + int(drop_z * sim_width / GRID_SIZE)
            ring_radius = int(drop_radius * 1.2 + ripple_time * 3)
            alpha = max(0, 180 - ripple_time * 8)
            ring_surface = pygame.Surface((ring_radius*2, ring_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(ring_surface, (255,255,255,alpha), (ring_radius, ring_radius), ring_radius, 4)
            screen.blit(ring_surface, (impact_x - ring_radius, impact_y - ring_radius))
    else:
        # Side view: show a horizontal slice through the grid at the drop's Z position, or average a band for smoother ripples
        band = 2
        slice_j = int(drop_z)
        points = []
        for i in range(GRID_SIZE):
            # Average over a small band for smoother ripples
            avg_h = np.mean(water_y[i, max(0, slice_j-band):min(GRID_SIZE, slice_j+band+1)])
            x = offset_x + int(i * sim_width / GRID_SIZE)
            y = 500 + int(avg_h)
            points.append((x, y))
        # Draw filled water
        water_poly = points + [(offset_x + sim_width, 800), (offset_x, 800)]
        pygame.draw.polygon(screen, WATER_COLOR_SURFACE, water_poly)
        # Draw the surface line
        pygame.draw.aalines(screen, (180, 220, 255), False, points, 2)

def draw_drop():
    if simulation_started and not drop_hit_water:
        drop_color = (0, 180, 230)
        # Use same centering logic as draw_water_surface
        global panel_minimized
        sim_width = 700
        if panel_minimized:
            offset_x = (WIDTH - sim_width) // 2
        else:
            offset_x = 20 + 380 + ((WIDTH - (20 + 380) - sim_width) // 2)
        offset_y = 80
        if BIRD_EYE_VIEW:
            x = offset_x + int(drop_x * sim_width / GRID_SIZE)
            z = offset_y + int(drop_z * sim_width / GRID_SIZE)
            pygame.draw.circle(screen, drop_color, (x, z), int(drop_radius))
            # Optional: draw shadow on water
            pygame.draw.circle(screen, (100, 120, 180, 80), (x, z), int(drop_radius * 1.1), 1)
        else:
            # Side view: show drop as a circle above the current cross-section
            x = offset_x + int(drop_x * sim_width / GRID_SIZE)
            y = 500 + int(drop_y - drop_height)
            pygame.draw.circle(screen, drop_color, (x, y), int(drop_radius))

def draw_lighting():
    light_pos = (WIDTH // 4, HEIGHT // 4)
    for x in range(WIDTH):
        distance = np.sqrt((x - light_pos[0]) ** 2 + (HEIGHT // 2 - light_pos[1]) ** 2)
        light_intensity = max(0, min(20, int(200 / (distance + 100))))
        pygame.draw.line(screen, (light_intensity, light_intensity, light_intensity, 30), (x, HEIGHT // 2), (x, HEIGHT))

# ====================
# Main Simulation Loop
# ====================
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
            # Minimize/collapse info panel
            if 20 <= mouse_pos[0] <= 20+380 and 20 <= mouse_pos[1] <= 20+40:
                btn_rect = pygame.Rect(20+380-36, 20+8, 28, 28)
                if btn_rect.collidepoint(mouse_pos):
                    panel_minimized = not panel_minimized
                    continue
            if start_button.collidepoint(mouse_pos):
                try:
                    # Input validation
                    if angle_input_text:
                        val = float(angle_input_text)
                        drop_angle = max(0, min(90, val))
                    if size_input_text:
                        val = float(size_input_text)
                        drop_radius = max(5, min(100, val))
                    # Calculate initial drop_x, drop_z based on angle and size
                    # Angle 0 = center, 90 = right edge
                    r = (GRID_SIZE // 2) - int((drop_radius / 100) * (GRID_SIZE // 2 - 5))
                    drop_x = int((GRID_SIZE // 2) + r * math.cos(math.radians(drop_angle)))
                    drop_z = int((GRID_SIZE // 2) + r * math.sin(math.radians(drop_angle)))
                    reset_simulation()
                    simulation_started = True
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
            elif toggle_view_button.collidepoint(mouse_pos):
                BIRD_EYE_VIEW = not BIRD_EYE_VIEW
            elif not panel_minimized and angle_input_box.collidepoint(mouse_pos):
                active_input_box = angle_input_box
            elif not panel_minimized and size_input_box.collidepoint(mouse_pos):
                active_input_box = size_input_box
            else:
                active_input_box = None

        elif event.type == pygame.KEYDOWN:
            # Keyboard shortcuts
            if event.key == pygame.K_SPACE:
                simulation_started = not simulation_started
            elif event.key == pygame.K_r:
                reset_simulation()
                simulation_started = False
            elif event.key == pygame.K_p:
                simulation_paused = not simulation_paused
            elif event.key == pygame.K_v:
                BIRD_EYE_VIEW = not BIRD_EYE_VIEW

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


    # --- Droplet physics (3D) ---
    if simulation_started and not drop_hit_water:
        drop_vy = drop_fall_speed
        drop_y += drop_vy
        # Drop falls straight down (for simplicity)
        if drop_y >= 40:  # Impact height (tune for grid scale)
            drop_hit_water = True
            # Energy transfer: amplitude proportional to drop's kinetic energy (no normalization)
            drop_mass_physical = (drop_radius / default_drop_radius) ** 3 * drop_mass
            drop_kinetic_energy = 0.5 * drop_mass_physical * drop_vy ** 2
            # Add energy to a circular region on the grid
            for i in range(GRID_SIZE):
                for j in range(GRID_SIZE):
                    dx = i - drop_x
                    dz = j - drop_z
                    dist = math.sqrt(dx * dx + dz * dz)
                    if dist <= drop_radius:
                        water_v[i, j] += (1 - dist / (drop_radius + 1)) * drop_kinetic_energy * RIPPLE_ENERGY_SCALE
            # Visual splash at impact location (use same offset_x, sim_width as draw_water_surface)
            sim_width = 700
            if panel_minimized:
                offset_x = (WIDTH - sim_width) // 2
            else:
                offset_x = 20 + 380 + ((WIDTH - (20 + 380) - sim_width) // 2)
            offset_y = 80
            splash_x = offset_x + int(drop_x * sim_width / GRID_SIZE)
            splash_y = offset_y + int(drop_z * sim_width / GRID_SIZE)
            create_splash(splash_x, splash_y)
    # --- FPS Counter ---
    fps = int(clock.get_fps())
    fps_surf = FONT_DEFAULT.render(f"FPS: {fps}", True, (255,255,0))
    screen.blit(fps_surf, (WIDTH-120, 20))

    # --- 3D Water Surface Physics (spring-mass grid) ---
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            center = water_y[i, j]
            neighbors = 0
            total = 0.0
            for di, dj in [(-1,0),(1,0),(0,-1),(0,1)]:
                ni, nj = i+di, j+dj
                if 0 <= ni < GRID_SIZE and 0 <= nj < GRID_SIZE:
                    total += water_y[ni, nj]
                    neighbors += 1
            force = spring_k * (-center) + spread * (total - neighbors * center)
            water_a[i, j] = force
    water_v += water_a
    water_v *= damping
    water_y += water_v


    draw_lighting()
    draw_water_surface()
    draw_drop()
    draw_scale()


    # Draw data panel first and get y_offset for placing controls
    controls_y = display_data_panel(screen)

    # --- Modern UI Panel with Sliders ---
    def draw_slider(x, y, value, minv, maxv, label):
        # Draw a modern slider with shadow and rounded corners
        slider_rect = pygame.Rect(x, y, SLIDER_WIDTH, SLIDER_HEIGHT)
        shadow = pygame.Surface((SLIDER_WIDTH+8, SLIDER_HEIGHT+8), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0,0,0,60), (4,4,SLIDER_WIDTH,SLIDER_HEIGHT), border_radius=8)
        screen.blit(shadow, (x-4, y-4))
        pygame.draw.rect(screen, SLIDER_BG, slider_rect, border_radius=8)
        pos = int((value - minv) / (maxv - minv) * SLIDER_WIDTH)
        pygame.draw.rect(screen, SLIDER_COLOR, (x, y, pos, SLIDER_HEIGHT), border_radius=8)
        knob_x = x + pos
        pygame.draw.circle(screen, SLIDER_KNOB, (knob_x, y + SLIDER_HEIGHT // 2), SLIDER_KNOB_RADIUS)
        draw_text(f"{label}: {value:.3f}", FONT_DEFAULT, TEXT_COLOR, screen, x, y - 25)

    # Place sliders and buttons immediately after the data fields
    if not panel_minimized:
        slider_x = 40
        slider_y0 = controls_y + 10  # Add a little more space after data fields
        slider_gap = 38
        draw_slider(slider_x, slider_y0, gravity, 0.1, 2.0, "Gravity")
        draw_slider(slider_x, slider_y0 + slider_gap, damping, 0.90, 0.999, "Damping")
        draw_slider(slider_x, slider_y0 + 2*slider_gap, drop_radius, 5, 100, "Drop Size")

    # --- Buttons on the right ---
    button_list = [
        (toggle_view_button, "Top/Side View"),
        (start_button, "Start"),
        (reset_button, "Reset"),
        (restart_button, "Restart"),
        (pause_button, "Pause"),
        (unpause_button, "Unpause")
    ]
    button_x = WIDTH - BUTTON_WIDTH - 40
    button_y0 = 80
    button_gap = 18
    for idx, (btn, label) in enumerate(button_list):
        btn.x = button_x
        btn.y = button_y0 + idx * (BUTTON_HEIGHT + button_gap)
        if btn == reset_button:
            color = RESET_COLOR if not btn.collidepoint(pygame.mouse.get_pos()) else RESET_HOVER_COLOR
        elif btn == restart_button:
            color = RESTART_COLOR if not btn.collidepoint(pygame.mouse.get_pos()) else RESTART_HOVER_COLOR
        elif btn == pause_button:
            color = PAUSE_COLOR if not btn.collidepoint(pygame.mouse.get_pos()) else PAUSE_HOVER_COLOR
        elif btn == unpause_button:
            color = UNPAUSE_COLOR if not btn.collidepoint(pygame.mouse.get_pos()) else UNPAUSE_HOVER_COLOR
        else:
            color = BUTTON_COLOR if not btn.collidepoint(pygame.mouse.get_pos()) else BUTTON_HOVER_COLOR
        # Draw button with shadow and rounded corners
        shadow = pygame.Surface((BUTTON_WIDTH+8, BUTTON_HEIGHT+8), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0,0,0,60), (4,4,BUTTON_WIDTH,BUTTON_HEIGHT), border_radius=12)
        screen.blit(shadow, (btn.x-4, btn.y-4))
        pygame.draw.rect(screen, color, btn, border_radius=12)
        # Center label
        text_surf = FONT_DEFAULT.render(label, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=btn.center)
        screen.blit(text_surf, text_rect)

    # --- End of frame ---
    update_splash_particles()
    draw_splash_particles()
    if drop_hit_water:
        ripple_time += 1
    else:
        ripple_time = 0

    # --- Handle slider interaction (mouse drag) ---
    if not panel_minimized and pygame.mouse.get_pressed()[0]:
        mx, my = pygame.mouse.get_pos()
        # Match slider positions to left panel
        slider_x = 40
        slider_y0 = controls_y + 10
        slider_gap = 38
        # Gravity slider
        if slider_x <= mx <= slider_x + SLIDER_WIDTH and slider_y0 <= my <= slider_y0 + SLIDER_HEIGHT:
            gravity = 0.1 + (mx - slider_x) / SLIDER_WIDTH * (2.0 - 0.1)
        # Viscosity slider (inverted: left = high viscosity, right = low viscosity)
        if slider_x <= mx <= slider_x + SLIDER_WIDTH and slider_y0 + slider_gap <= my <= slider_y0 + slider_gap + SLIDER_HEIGHT:
            damping = 0.999 - (mx - slider_x) / SLIDER_WIDTH * (0.999 - 0.90)
        # Drop size slider
        if slider_x <= mx <= slider_x + SLIDER_WIDTH and slider_y0 + 2*slider_gap <= my <= slider_y0 + 2*slider_gap + SLIDER_HEIGHT:
            drop_radius = 5 + (mx - slider_x) / SLIDER_WIDTH * (100 - 5)

    pygame.display.update()
    clock.tick(120)

pygame.quit()
