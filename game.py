import pgzrun
import pygame
import os
import random

os.environ['SDL_VIDEO_CENTERED'] = '1'
# Game Configuration
WIDTH = 1500
HEIGHT = 800
TITLE = "Open World City Map - Residential & Industrial"

# Camera zoom
CAMERA_ZOOM = 2.0

# Tile size
TILE_SIZE = 18

# Map dimensions in tiles 
MAP_TILES_WIDTH = 200
MAP_TILES_HEIGHT = 150

# Calculate pixel dimensions
MAP_WIDTH = MAP_TILES_WIDTH * TILE_SIZE
MAP_HEIGHT = MAP_TILES_HEIGHT * TILE_SIZE

# Camera offset
camera_x = 0
camera_y = 0

# Game state
game_state = {
    'alive': True,
    'death_timer': 0,
    'death_delay': 80
}

# Player setup
player = Actor('idle')
player.x = 500
player.y = 500
player_walk_speed = 1
player_run_speed = 2

# Weapon state
player_weapon = {
    'type': 'none',  # 'none', 'katana', or 'gun'
    'attacking': False,
    'attack_frame': 0,
    'attack_delay': 0,
    'shoot_animation_done': False  # Track if shoot animation finished
}

# Gun configuration - ADJUST THESE VALUES
GUN_CONFIG = {
    'scale': 0.8,           # Gun size multiplier - CHANGE THIS to adjust gun size
    'offset_x': 5,         # Horizontal offset from player center - CHANGE THIS
    'offset_y': 5,          # Vertical offset from player center - CHANGE THIS
    'image': None           # Will store loaded gun image
}

# Bullet system
bullets = []  # List of active bullets

# Bullet configuration - ADJUST THESE VALUES
BULLET_CONFIG = {
    'speed': 8,            # Bullet travel speed - CHANGE THIS (higher = faster)
    'scale': 1.0,          # Bullet size multiplier - CHANGE THIS
    'lifetime': 120        # Frames before bullet disappears - CHANGE THIS (higher = travels farther)
}

# NPC System
npcs = []  # List of all NPCs

# NPC Configuration - ADJUST POPULATION HERE
NPC_CONFIG = {
    'max_population': 200,        # CHANGE THIS: Total number of NPCs in the world
    'walk_speed': 1.0,            # NPC walking speed
    'run_speed': 2.0,             # NPC running speed (when scared)
    'animation_speed': 8,         # Animation frame delay
    'decision_interval': 300,     # Frames between behavior changes (3 seconds at 60fps)
    'sidewalk_preference': 0.9,   # 90% chance to stay on sidewalk
    'sit_duration': 240,          # How long NPCs sit (4 seconds)
}

# NPC spritesheets
NPC_SPRITESHEETS = {}

# NPC states
NPC_STATE_IDLE = 0
NPC_STATE_WALKING = 1
NPC_STATE_RUNNING = 2
NPC_STATE_SITTING = 3
NPC_STATE_HURT = 4

def load_npc_spritesheets():
    """Load all NPC spritesheets (npc1-9)"""
    try:
        for i in range(1, 10):
            NPC_SPRITESHEETS[f'npc{i}'] = {
                'idle': pygame.image.load(f'images/npc{i}idle.png'),
                'walk': pygame.image.load(f'images/npc{i}walk.png'),
                'run': pygame.image.load(f'images/npc{i}run.png'),
                'sit': pygame.image.load(f'images/npc{i}sit.png'),
                'hurt': pygame.image.load(f'images/npc{i}hurt.png')
            }
        print(f"Loaded {len(NPC_SPRITESHEETS)} NPC types successfully!")
    except Exception as e:
        print(f"Error loading NPC spritesheets: {e}")

# NPC frame counts (same as player)
NPC_FRAME_COUNTS = {
    'idle': 2,
    'walk': 9,
    'run': 8,
    'sit': 3,   
    'hurt': 6
}

def get_npc_frame(npc_type, state, direction, frame_index):
    """Extract NPC frame from spritesheet"""
    if npc_type not in NPC_SPRITESHEETS:
        return None
    
    state_map = {
        NPC_STATE_IDLE: 'idle',
        NPC_STATE_WALKING: 'walk',
        NPC_STATE_RUNNING: 'run',
        NPC_STATE_SITTING: 'sit',
        NPC_STATE_HURT: 'hurt'
    }
    
    state_name = state_map.get(state, 'idle')
    
    if state_name not in NPC_SPRITESHEETS[npc_type]:
        return None
    
    spritesheet = NPC_SPRITESHEETS[npc_type][state_name]
    
    # Row mapping (same as player)
    row = DIRECTION_ROWS.get(direction, 0)
    
    # Each frame is 64x64
    frame_x = frame_index * 64
    frame_y = row * 64
    
    try:
        frame = spritesheet.subsurface(pygame.Rect(frame_x, frame_y, 64, 64))
        return frame
    except:
        return None

def is_on_sidewalk(x, y):
    """Check if position is on sidewalk"""
    tile_x = int(x // TILE_SIZE)
    tile_y = int(y // TILE_SIZE)
    
    if 0 <= tile_x < MAP_TILES_WIDTH and 0 <= tile_y < MAP_TILES_HEIGHT:
        tile = map_grid[tile_y][tile_x]
        if 'sidewalk' in tile.lower():
            return True
    return False

def is_on_walkable_surface(x, y):
    """Check if NPC can walk here (sidewalk or crosswalk)"""
    tile_x = int(x // TILE_SIZE)
    tile_y = int(y // TILE_SIZE)
    
    if 0 <= tile_x < MAP_TILES_WIDTH and 0 <= tile_y < MAP_TILES_HEIGHT:
        tile = map_grid[tile_y][tile_x]
        tile_lower = tile.lower()
        if 'sidewalk' in tile_lower or 'crosswalk' in tile_lower:
            return True
    return False

def spawn_npc():
    """Spawn a single NPC on a random sidewalk"""
    # Try random positions until we find a sidewalk
    for attempt in range(50):
        x = random.randint(100, MAP_WIDTH - 100)
        y = random.randint(100, MAP_HEIGHT - 100)
        
        if is_on_sidewalk(x, y):
            # Choose random NPC type
            npc_type = f'npc{random.randint(1, 9)}'
            
            npcs.append({
                'type': npc_type,
                'x': float(x),
                'y': float(y),
                'direction': random.choice(['up', 'down', 'left', 'right']),
                'state': NPC_STATE_IDLE,
                'current_frame': 0,
                'frame_delay': 0,
                'decision_timer': 0,
                'sit_timer': 0,
                'target_x': None,
                'target_y': None,
                'alive': True
            })
            return True
    return False

def initialize_npcs():
    """Spawn initial NPC population"""
    npcs.clear()
    for i in range(NPC_CONFIG['max_population']):
        spawn_npc()
    print(f"Spawned {len(npcs)} NPCs")

def check_npc_player_collision(new_x, new_y):
    """Check if player would collide with any NPC"""
    player_radius = 8
    npc_radius = 10
    
    for npc in npcs:
        if not npc['alive']:
            continue
            
        dx = new_x - npc['x']
        dy = new_y - npc['y']
        distance = (dx * dx + dy * dy) ** 0.5
        
        if distance < (player_radius + npc_radius):
            return True  # Collision - block movement
    
    return False  # No collision

def check_npc_car_collision(npc):
    """Check if NPC collides with a car"""
    npc_radius = 12
    car_radius = 14
    
    for car in traffic_vehicles:
        dx = npc['x'] - car['x']
        dy = npc['y'] - car['y']
        distance = (dx * dx + dy * dy) ** 0.5
        
        if distance < (npc_radius + car_radius):
            return True
    return False

def update_npc(npc):
    """Update single NPC behavior"""
    if not npc['alive']:
        return
    
    # Update animation frame (but NOT for sitting - it should stay on last frame)
    if npc['state'] != NPC_STATE_SITTING:
        npc['frame_delay'] += 1
        if npc['frame_delay'] >= NPC_CONFIG['animation_speed']:
            npc['frame_delay'] = 0
            npc['current_frame'] += 1
            
            # Get max frames for current state
            state_map = {
                NPC_STATE_IDLE: 'idle',
                NPC_STATE_WALKING: 'walk',
                NPC_STATE_RUNNING: 'run',
                NPC_STATE_SITTING: 'sit',
                NPC_STATE_HURT: 'hurt'
            }
            state_name = state_map.get(npc['state'], 'idle')
            max_frames = NPC_FRAME_COUNTS.get(state_name, 2)
            
            if npc['current_frame'] >= max_frames:
                npc['current_frame'] = 0
    
    # Check collision with cars
    if check_npc_car_collision(npc):
        npc['state'] = NPC_STATE_HURT
        npc['alive'] = False
        npc['current_frame'] = 0
        # Spawn replacement
        spawn_npc()
        return
    
    # Behavior decision timer
    npc['decision_timer'] += 1
    
    if npc['decision_timer'] >= NPC_CONFIG['decision_interval']:
        npc['decision_timer'] = 0
        
        # Decide new behavior
        behavior_choice = random.random()
        
        if behavior_choice < 0.3:
            # 30% - Start walking
            npc['state'] = NPC_STATE_WALKING
            npc['direction'] = random.choice(['up', 'down', 'left', 'right'])
        elif behavior_choice < 0.5:
            # 20% - Sit down
            npc['state'] = NPC_STATE_SITTING
            npc['sit_timer'] = NPC_CONFIG['sit_duration']
            npc['current_frame'] = 0  # Start sit animation from beginning
        else:
            # 50% - Stay idle
            npc['state'] = NPC_STATE_IDLE
    
    # Handle sitting
    if npc['state'] == NPC_STATE_SITTING:
        npc['sit_timer'] -= 1
        # Keep on last frame of sit animation
        npc['current_frame'] = NPC_FRAME_COUNTS['sit'] - 1
        if npc['sit_timer'] <= 0:
            npc['state'] = NPC_STATE_IDLE
            npc['current_frame'] = 0  # Reset frame when standing up
    
    # Handle walking
    if npc['state'] == NPC_STATE_WALKING:
        speed = NPC_CONFIG['walk_speed']
        
        next_x = npc['x']
        next_y = npc['y']
        
        if npc['direction'] == 'up':
            next_y -= speed
        elif npc['direction'] == 'down':
            next_y += speed
        elif npc['direction'] == 'left':
            next_x -= speed
        elif npc['direction'] == 'right':
            next_x += speed
        
        # Check if next position is walkable
        if is_on_walkable_surface(next_x, next_y):
            npc['x'] = next_x
            npc['y'] = next_y
        else:
            # Hit obstacle, change direction
            npc['direction'] = random.choice(['up', 'down', 'left', 'right'])
            npc['decision_timer'] = NPC_CONFIG['decision_interval'] - 10

def update_npcs():
    """Update all NPCs"""
    for npc in npcs[:]:
        update_npc(npc)
        
        # Remove dead NPCs after hurt animation
        if not npc['alive'] and npc['state'] == NPC_STATE_HURT:
            # Check if hurt animation finished
            if npc['current_frame'] >= NPC_FRAME_COUNTS['hurt'] - 1:
                npcs.remove(npc)

# NEW Player animation system for spritesheets
player_animation = {
    'current_frame': 0,
    'frame_delay': 0,
    'animation_speed': 6,  # Lower = faster animation
    'direction': 'down',   # Start facing down
    'state': 'idle',       # idle, walk, or run
    'spritesheets': {},
    'current_frames': []
}

# Frame counts for each animation
FRAME_COUNTS = {
    'idle': 2,
    'walk': 9,
    'walk_katana': 9,
    'run': 8,
    'hurt': 6,
    'slash_katana': 6,
    'shoot': 13
}

# Frame sizes for each animation
FRAME_SIZES = {
    'idle': 64,
    'walk': 64,
    'walk_katana': 128,
    'run': 64,
    'hurt': 64,
    'slash_katana': 128,
    'shoot': 64
}

# Direction to row mapping
DIRECTION_ROWS = {
    'up': 0,
    'left': 1,
    'down': 2,
    'right': 3
}

def load_player_spritesheets():
    """Load all spritesheets"""
    try:
        player_animation['spritesheets']['idle'] = pygame.image.load('images/idle.png')
        player_animation['spritesheets']['walk'] = pygame.image.load('images/walk.png')
        player_animation['spritesheets']['walk_katana'] = pygame.image.load('images/walk_katana.png')
        player_animation['spritesheets']['run'] = pygame.image.load('images/run.png')
        player_animation['spritesheets']['hurt'] = pygame.image.load('images/hurt.png')
        player_animation['spritesheets']['slash_katana'] = pygame.image.load('images/slash_katana.png')
        player_animation['spritesheets']['shoot'] = pygame.image.load('images/shoot.png')
        
        # Load gun and bullet
        GUN_CONFIG['image'] = pygame.image.load('images/ak47.png')
        BULLET_CONFIG['image'] = pygame.image.load('images/rifleallosmall.png')
        
        print("Player spritesheets and weapons loaded successfully!")
    except Exception as e:
        print(f"Error loading spritesheets: {e}")
    
    # Load NPCs - ADD THIS
    load_npc_spritesheets()
    
    # Initialize NPC population - ADD THIS
    initialize_npcs()

def get_player_frame(state, direction, frame_index):
    """Extract a single frame from spritesheet"""
    if state not in player_animation['spritesheets']:
        return None
    
    spritesheet = player_animation['spritesheets'][state]
    
    # Get frame size for this animation
    frame_size = FRAME_SIZES.get(state, 64)
    
    # For hurt animation, use row 0 only (no direction)
    if state == 'hurt':
        row = 0
    else:
        row = DIRECTION_ROWS[direction]
    
    # Calculate frame position
    frame_x = frame_index * frame_size
    frame_y = row * frame_size
    
    # Extract the frame
    frame = spritesheet.subsurface(pygame.Rect(frame_x, frame_y, frame_size, frame_size))
    return frame

def get_rotated_gun(direction):
    """Get gun rotated based on direction"""
    if GUN_CONFIG['image'] is None:
        return None
    
    gun_img = GUN_CONFIG['image']
    
    # Rotate based on direction (gun default faces right)
    if direction == 'right':
        rotated_gun = gun_img
    elif direction == 'left':
        # Flip horizontally for left (not rotate 180)
        rotated_gun = pygame.transform.flip(gun_img, True, False)
    elif direction == 'up':
        rotated_gun = pygame.transform.rotate(gun_img, 90)
    elif direction == 'down':
        rotated_gun = pygame.transform.rotate(gun_img, -90)
    else:
        rotated_gun = gun_img
    
    return rotated_gun

def get_gun_offset(direction):
    """Get gun position offset based on direction - ADJUST EACH INDIVIDUALLY"""
    # Each direction has its own X and Y offset
    # Format: (horizontal_offset, vertical_offset)
    offsets = {
        'right': (4, 5),      # ADJUST: gun position when facing right (x, y)
        'left': (-4, 5),      # ADJUST: gun position when facing left (x, y)
        'up': (-1, -3),         # ADJUST: gun position when facing up (x, y)
        'down': (1, 5)         # ADJUST: gun position when facing down (x, y)
    }
    return offsets.get(direction, (0, 0))

def spawn_bullet():
    """Spawn a bullet from player position"""
    direction = player_animation['direction']
    
    # Starting position (player position with offset)
    start_x = player.x
    start_y = player.y
    
    # Offset bullet spawn point slightly in front of player
    if direction == 'right':
        start_x += 20
    elif direction == 'left':
        start_x -= 20
    elif direction == 'up':
        start_y -= 20
    elif direction == 'down':
        start_y += 20
    
    # Bullet velocity based on direction
    velocities = {
        'right': (BULLET_CONFIG['speed'], 0),
        'left': (-BULLET_CONFIG['speed'], 0),
        'up': (0, -BULLET_CONFIG['speed']),
        'down': (0, BULLET_CONFIG['speed'])
    }
    
    vel_x, vel_y = velocities.get(direction, (0, 0))
    
    # Rotation angle for bullet
    rotation_angles = {
        'right': 0,
        'left': 180,
        'up': -90,
        'down': 90
    }
    
    bullet = {
        'x': float(start_x),
        'y': float(start_y),
        'vel_x': vel_x,
        'vel_y': vel_y,
        'angle': rotation_angles.get(direction, 0),
        'lifetime': BULLET_CONFIG['lifetime']
    }
    
    bullets.append(bullet)
    print(f"BULLET SPAWNED! Position: ({start_x}, {start_y}), Direction: {direction}, Total: {len(bullets)}")

def update_bullets():
    """Update all bullets"""
    for bullet in bullets[:]:
        # Move bullet
        bullet['x'] += bullet['vel_x']
        bullet['y'] += bullet['vel_y']
        
        # Decrease lifetime
        bullet['lifetime'] -= 1
        
        # Remove if lifetime expired or off map
        if (bullet['lifetime'] <= 0 or 
            bullet['x'] < 0 or bullet['x'] > MAP_WIDTH or
            bullet['y'] < 0 or bullet['y'] > MAP_HEIGHT):
            bullets.remove(bullet)


def update_player_animation(state, direction):
    """Update animation based on state (idle/walk/run) and direction"""
    player_animation['state'] = state
    player_animation['direction'] = direction
    
    if state != 'idle':  # Walking or running
        player_animation['frame_delay'] += 1
        
        if player_animation['frame_delay'] >= player_animation['animation_speed']:
            player_animation['frame_delay'] = 0
            player_animation['current_frame'] += 1
            
            # Loop animation
            max_frames = FRAME_COUNTS[state]
            if player_animation['current_frame'] >= max_frames:
                player_animation['current_frame'] = 0
    else:  # Idle
        # Animate idle slowly
        player_animation['frame_delay'] += 1
        
        if player_animation['frame_delay'] >= player_animation['animation_speed'] * 3:  # Slower
            player_animation['frame_delay'] = 0
            player_animation['current_frame'] += 1
            
            if player_animation['current_frame'] >= FRAME_COUNTS['idle']:
                player_animation['current_frame'] = 0

# Map grid
map_grid = []

# Initialize empty map with grass
for y in range(MAP_TILES_HEIGHT):
    row = []
    for x in range(MAP_TILES_WIDTH):
        row.append('grassfieldmiddle') 
    map_grid.append(row)

# Objects layer
map_objects = []

# Traffic system
traffic_vehicles = []  

# Traffic configuration - REPLACE OLD ONE
TRAFFIC_CONFIG = {
    'max_cars': 80,         
    'spawn_interval': 15,        # Frames between spawns (45 = ~0.75 seconds)
    'car_speed': 3,   
    'car_max_speed': 5,           
    'despawn_distance': 2000,
    'stop_distance': 100,         # Distance to stop before another car
    'brake_distance': 120,
    'brake_force': 0.15,
    'intersection_wait': 30,     # Frames to wait at intersection if blocked
}

# Spawn timer
spawn_timer = 0

# COMPLETE intersection map with proper lane positions
INTERSECTIONS = [
    # Residential - Row 1 (y=30)
    {'x': 29 * TILE_SIZE, 'y': 30 * TILE_SIZE, 'type': 'T', 'directions': {
        'up': [(29 * TILE_SIZE, 28 * TILE_SIZE)],
        'down': [(29 * TILE_SIZE, 32 * TILE_SIZE)],
        'right': [(31 * TILE_SIZE, 30 * TILE_SIZE)],
    }},
    {'x': 54 * TILE_SIZE, 'y': 30 * TILE_SIZE, 'type': 'cross', 'directions': {
        'up': [(54 * TILE_SIZE, 28 * TILE_SIZE)],
        'down': [(54 * TILE_SIZE, 32 * TILE_SIZE)],
        'left': [(52 * TILE_SIZE, 30 * TILE_SIZE)],
        'right': [(56 * TILE_SIZE, 30 * TILE_SIZE)],
    }},
    {'x': 79 * TILE_SIZE, 'y': 30 * TILE_SIZE, 'type': 'cross', 'directions': {
        'up': [(79 * TILE_SIZE, 28 * TILE_SIZE)],
        'down': [(79 * TILE_SIZE, 32 * TILE_SIZE)],
        'left': [(77 * TILE_SIZE, 30 * TILE_SIZE)],
        'right': [(81 * TILE_SIZE, 30 * TILE_SIZE)],
    }},
    {'x': 106 * TILE_SIZE, 'y': 30 * TILE_SIZE, 'type': 'T', 'directions': {
        'up': [(106 * TILE_SIZE, 28 * TILE_SIZE)],
        'down': [(106 * TILE_SIZE, 32 * TILE_SIZE)],
        'left': [(104 * TILE_SIZE, 30 * TILE_SIZE)],
    }},
    
    # Residential - Row 2 (y=60)
    {'x': 29 * TILE_SIZE, 'y': 60 * TILE_SIZE, 'type': 'cross', 'directions': {
        'up': [(29 * TILE_SIZE, 58 * TILE_SIZE)],
        'down': [(29 * TILE_SIZE, 62 * TILE_SIZE)],
        'right': [(31 * TILE_SIZE, 60 * TILE_SIZE)],
    }},
    {'x': 54 * TILE_SIZE, 'y': 60 * TILE_SIZE, 'type': 'cross', 'directions': {
        'up': [(54 * TILE_SIZE, 58 * TILE_SIZE)],
        'down': [(54 * TILE_SIZE, 62 * TILE_SIZE)],
        'left': [(52 * TILE_SIZE, 60 * TILE_SIZE)],
        'right': [(56 * TILE_SIZE, 60 * TILE_SIZE)],
    }},
    {'x': 79 * TILE_SIZE, 'y': 60 * TILE_SIZE, 'type': 'cross', 'directions': {
        'up': [(79 * TILE_SIZE, 58 * TILE_SIZE)],
        'down': [(79 * TILE_SIZE, 62 * TILE_SIZE)],
        'left': [(77 * TILE_SIZE, 60 * TILE_SIZE)],
        'right': [(81 * TILE_SIZE, 60 * TILE_SIZE)],
    }},
    {'x': 106 * TILE_SIZE, 'y': 60 * TILE_SIZE, 'type': 'T', 'directions': {
        'up': [(106 * TILE_SIZE, 58 * TILE_SIZE)],
        'down': [(106 * TILE_SIZE, 62 * TILE_SIZE)],
        'left': [(104 * TILE_SIZE, 60 * TILE_SIZE)],
    }},
    
    # Residential - Row 3 (y=84)
    {'x': 29 * TILE_SIZE, 'y': 84 * TILE_SIZE, 'type': 'T', 'directions': {
        'up': [(29 * TILE_SIZE, 82 * TILE_SIZE)],
        'right': [(31 * TILE_SIZE, 84 * TILE_SIZE)],
    }},
    {'x': 54 * TILE_SIZE, 'y': 84 * TILE_SIZE, 'type': 'T', 'directions': {
        'up': [(54 * TILE_SIZE, 82 * TILE_SIZE)],
        'left': [(52 * TILE_SIZE, 84 * TILE_SIZE)],
        'right': [(56 * TILE_SIZE, 84 * TILE_SIZE)],
    }},
    {'x': 79 * TILE_SIZE, 'y': 84 * TILE_SIZE, 'type': 'T', 'directions': {
        'up': [(79 * TILE_SIZE, 82 * TILE_SIZE)],
        'left': [(77 * TILE_SIZE, 84 * TILE_SIZE)],
        'right': [(81 * TILE_SIZE, 84 * TILE_SIZE)],
    }},
    {'x': 106 * TILE_SIZE, 'y': 84 * TILE_SIZE, 'type': 'T', 'directions': {
        'up': [(106 * TILE_SIZE, 82 * TILE_SIZE)],
        'left': [(104 * TILE_SIZE, 84 * TILE_SIZE)],
    }},
    
    # Industrial intersections (add all industrial ones)
    {'x': 127 * TILE_SIZE, 'y': 30 * TILE_SIZE, 'type': 'cross', 'directions': {
        'up': [(127 * TILE_SIZE, 28 * TILE_SIZE)],
        'down': [(127 * TILE_SIZE, 32 * TILE_SIZE)],
        'left': [(125 * TILE_SIZE, 30 * TILE_SIZE)],
        'right': [(129 * TILE_SIZE, 30 * TILE_SIZE)],
    }},
    {'x': 152 * TILE_SIZE, 'y': 30 * TILE_SIZE, 'type': 'cross', 'directions': {
        'up': [(152 * TILE_SIZE, 28 * TILE_SIZE)],
        'down': [(152 * TILE_SIZE, 32 * TILE_SIZE)],
        'left': [(150 * TILE_SIZE, 30 * TILE_SIZE)],
        'right': [(154 * TILE_SIZE, 30 * TILE_SIZE)],
    }},
    {'x': 177 * TILE_SIZE, 'y': 30 * TILE_SIZE, 'type': 'cross', 'directions': {
        'up': [(177 * TILE_SIZE, 28 * TILE_SIZE)],
        'down': [(177 * TILE_SIZE, 32 * TILE_SIZE)],
        'left': [(175 * TILE_SIZE, 30 * TILE_SIZE)],
        'right': [(179 * TILE_SIZE, 30 * TILE_SIZE)],
    }},
    
    # Add remaining industrial intersections at y=52, 72, 92, 112, 130
    {'x': 127 * TILE_SIZE, 'y': 52 * TILE_SIZE, 'type': 'cross', 'directions': {
        'up': [(127 * TILE_SIZE, 50 * TILE_SIZE)],
        'down': [(127 * TILE_SIZE, 54 * TILE_SIZE)],
        'left': [(125 * TILE_SIZE, 52 * TILE_SIZE)],
        'right': [(129 * TILE_SIZE, 52 * TILE_SIZE)],
    }},
    {'x': 152 * TILE_SIZE, 'y': 52 * TILE_SIZE, 'type': 'cross', 'directions': {
        'up': [(152 * TILE_SIZE, 50 * TILE_SIZE)],
        'down': [(152 * TILE_SIZE, 54 * TILE_SIZE)],
        'left': [(150 * TILE_SIZE, 52 * TILE_SIZE)],
        'right': [(154 * TILE_SIZE, 52 * TILE_SIZE)],
    }},
    {'x': 177 * TILE_SIZE, 'y': 52 * TILE_SIZE, 'type': 'cross', 'directions': {
        'up': [(177 * TILE_SIZE, 50 * TILE_SIZE)],
        'down': [(177 * TILE_SIZE, 54 * TILE_SIZE)],
        'left': [(175 * TILE_SIZE, 52 * TILE_SIZE)],
        'right': [(179 * TILE_SIZE, 52 * TILE_SIZE)],
    }},
    
    
    # Continue pattern for y=72, 92, 112, 130...
]

#rotated images
rotated_images = {}

def get_rotated_image(image_name, angle):
    """Get a cached rotated image"""
    cache_key = f"{image_name}_{angle}"
    if cache_key not in rotated_images:
        try:
            img = pygame.image.load(f'images/{image_name}.png')
            if angle != 0:
                rotated_images[cache_key] = pygame.transform.rotate(img, angle)
            else:
                rotated_images[cache_key] = img
        except:
            rotated_images[cache_key] = None
    return rotated_images[cache_key]

def place_tile(tile_name, tile_x, tile_y, rotation=0):
    if 0 <= tile_x < MAP_TILES_WIDTH and 0 <= tile_y < MAP_TILES_HEIGHT:
        if rotation == 0:
            map_grid[tile_y][tile_x] = tile_name
        else:
            map_grid[tile_y][tile_x] = f"{tile_name}|rot{rotation}"

def place_object(obj_name, pixel_x, pixel_y):
    map_objects.append({'name': obj_name, 'x': pixel_x, 'y': pixel_y})

def place_horizontal_road_normal(start_x, start_y, length):
    for i in range(length):
        x = start_x + i
        place_tile('sidewalkmiddle', x, start_y - 2)
        place_tile('sidewalkmiddle', x, start_y - 1)
        place_tile('road', x, start_y)
        place_tile('road', x, start_y + 1)
        place_tile('roadhorizontal', x, start_y + 2, rotation=90)
        place_tile('road', x, start_y + 3)
        place_tile('road', x, start_y + 4)
        place_tile('sidewalkmiddle', x, start_y + 5)
        place_tile('sidewalkmiddle', x, start_y + 6)

def place_horizontal_road_main(start_x, start_y, length):
    for i in range(length):
        x = start_x + i
        place_tile('sidewalkmiddle', x, start_y - 2)
        place_tile('sidewalkmiddle', x, start_y - 1)
        place_tile('road', x, start_y)
        place_tile('road', x, start_y + 1)
        place_tile('road', x, start_y + 2)
        place_tile('road', x, start_y + 3)
        place_tile('roadhorizontaldoubleline', x, start_y + 4, rotation=90)
        place_tile('road', x, start_y + 5)
        place_tile('road', x, start_y + 6)
        place_tile('road', x, start_y + 7)
        place_tile('road', x, start_y + 8)
        place_tile('sidewalkmiddle', x, start_y + 9)
        place_tile('sidewalkmiddle', x, start_y + 10)

def place_vertical_road_normal(start_x, start_y, length):
    for i in range(length):
        y = start_y + i
        place_tile('sidewalkmiddle', start_x - 2, y, rotation=90)
        place_tile('sidewalkmiddle', start_x - 1, y, rotation=90)
        place_tile('road', start_x, y, rotation=90)
        place_tile('road', start_x + 1, y, rotation=90)
        place_tile('roadhorizontal', start_x + 2, y)
        place_tile('road', start_x + 3, y, rotation=90)
        place_tile('road', start_x + 4, y, rotation=90)
        place_tile('sidewalkmiddle', start_x + 5, y, rotation=90)
        place_tile('sidewalkmiddle', start_x + 6, y, rotation=90)

def place_vertical_road_main(start_x, start_y, length):
    for i in range(length):
        y = start_y + i
        place_tile('sidewalkmiddle', start_x - 2, y, rotation=90)
        place_tile('sidewalkmiddle', start_x - 1, y, rotation=90)
        place_tile('road', start_x, y, rotation=90)
        place_tile('road', start_x + 1, y, rotation=90)
        place_tile('road', start_x + 2, y, rotation=90)
        place_tile('road', start_x + 3, y, rotation=90)
        place_tile('roadhorizontaldoubleline', start_x + 4, y)
        place_tile('road', start_x + 5, y, rotation=90)
        place_tile('road', start_x + 6, y, rotation=90)
        place_tile('road', start_x + 7, y, rotation=90)
        place_tile('road', start_x + 8, y, rotation=90)
        place_tile('sidewalkmiddle', start_x + 9, y, rotation=90)
        place_tile('sidewalkmiddle', start_x + 10, y, rotation=90)

def place_crosswalk_horizontal(center_x, center_y, road_width):
    for offset in range(-3, road_width - 1):
        place_tile('crosswalk', center_x, center_y + offset, rotation=90)

def place_crosswalk_vertical(center_x, center_y, road_width):
    for offset in range(-3, road_width - 1):
        place_tile('crosswalk', center_x + offset, center_y)

def fill_grass_area(start_x, start_y, width, height):
    for dy in range(height):
        for dx in range(width):
            x = start_x + dx
            y = start_y + dy
            if dy == 0 and dx == 0:
                tile = 'grassfieldtopleftcorner'
            elif dy == 0 and dx == width - 1:
                tile = 'grassfieldtoprightcorner'
            elif dy == height - 1 and dx == 0:
                tile = 'grassfieldbottomleftcorner'
            elif dy == height - 1 and dx == width - 1:
                tile = 'grassfieldbottomrightcorner'
            elif dy == 0:
                tile = 'grassfieldtopmiddle'
            elif dy == height - 1:
                tile = 'grassfieldbottommiddle'
            elif dx == 0:
                tile = 'grassfieldleftmiddle'
            elif dx == width - 1:
                tile = 'grassfieldrightmiddle'
            else:
                tile = 'grassfieldmiddle'
            place_tile(tile, x, y)

# ============================================
# RESIDENTIAL ZONE
# ============================================

place_vertical_road_main(104, 5, 84)
place_horizontal_road_main(5, 28, 99)

place_horizontal_road_normal(5, 58, 99)
place_horizontal_road_normal(5, 82, 99)

place_vertical_road_normal(27, 5, 23)
place_vertical_road_normal(27, 37, 21)
place_vertical_road_normal(27, 63, 19)

place_vertical_road_normal(52, 5, 23)
place_vertical_road_normal(52, 37, 21)
place_vertical_road_normal(52, 63, 19)

place_vertical_road_normal(77, 5, 23)
place_vertical_road_normal(77, 37, 21)
place_vertical_road_normal(77, 63, 19)

# Crosswalks
place_crosswalk_vertical(30, 27, 3)
place_crosswalk_vertical(30, 26, 3)
place_crosswalk_vertical(55, 26, 3)
place_crosswalk_vertical(55, 27, 3)
place_crosswalk_vertical(80, 26, 3)
place_crosswalk_vertical(80, 27, 3)

place_crosswalk_vertical(30, 56, 3)
place_crosswalk_vertical(30, 57, 3)
place_crosswalk_vertical(55, 56, 3)
place_crosswalk_vertical(55, 57, 3)
place_crosswalk_vertical(80, 56, 3)
place_crosswalk_vertical(80, 57, 3)

place_crosswalk_vertical(30, 80, 3)
place_crosswalk_vertical(30, 81, 3)
place_crosswalk_vertical(55, 80, 3)
place_crosswalk_vertical(55, 81, 3)
place_crosswalk_vertical(80, 80, 3)
place_crosswalk_vertical(80, 81, 3)

place_crosswalk_horizontal(28, 58, 7)
place_crosswalk_horizontal(53, 58, 7)
place_crosswalk_horizontal(78, 58, 7)

place_crosswalk_horizontal(28, 82, 7)
place_crosswalk_horizontal(53, 82, 7)
place_crosswalk_horizontal(78, 82, 7)

# Residential grass areas
fill_grass_area(5, 5, 20, 20)
fill_grass_area(34, 5, 16, 20)
fill_grass_area(59, 5, 16, 20)
fill_grass_area(84, 5, 16, 20)

fill_grass_area(5, 43, 20, 12)
fill_grass_area(34, 43, 16, 12)
fill_grass_area(59, 43, 16, 12)
fill_grass_area(84, 43, 16, 12)

fill_grass_area(5, 67, 20, 12)
fill_grass_area(34, 67, 16, 12)
fill_grass_area(59, 67, 16, 12)
fill_grass_area(84, 67, 16, 12)

fill_grass_area(5, 90, 103, 7)

# Residential houses
x_positions = [7, 11, 15, 19, 23, 36, 40, 44, 48, 61, 65, 69, 73, 86, 90, 94, 98]
y_positions = [7, 9.67, 12.3, 15.01, 17.68, 20.35, 23]
for x in x_positions:
    for y in y_positions:
        place_object('smallhouse', x * TILE_SIZE, y * TILE_SIZE)

x_positions = [7, 11, 15, 19, 23, 36, 40, 44, 48, 61, 65, 69, 73, 86, 90, 94, 98]
y_positions = [45, 47.67, 50.34, 53.01]
for x in x_positions:
    for y in y_positions:
        place_object('smallhouse', x * TILE_SIZE, y * TILE_SIZE)

x_positions = [7, 11, 15, 19, 23, 36, 40, 44, 48, 61, 65, 69, 73, 86, 90, 94, 98]
y_positions = [69, 71.67, 74.34, 77.01]
for x in x_positions:
    for y in y_positions:
        place_object('smallhouse', x * TILE_SIZE, y * TILE_SIZE)

x_positions = []
x = 7
while x <= 103:
    x_positions.append(x)
    x += 4
y_positions = [92, 94.67]
for x in x_positions:
    for y in y_positions:
        place_object('smallhouse', x * TILE_SIZE, y * TILE_SIZE)

# Residential shops
place_object('shop1', 38 * TILE_SIZE, 26 * TILE_SIZE)
place_object('shop2', 70 * TILE_SIZE, 26 * TILE_SIZE)
place_object('shop3', 100 * TILE_SIZE, 26 * TILE_SIZE)
place_object('supermarket', 48 * TILE_SIZE, 94 * TILE_SIZE)

# Residential props
place_object('tree1', 7 * TILE_SIZE, 8 * TILE_SIZE)
place_object('tree2', 20 * TILE_SIZE, 10 * TILE_SIZE)
place_object('tree1', 51 * TILE_SIZE, 8 * TILE_SIZE)
place_object('tree2', 76 * TILE_SIZE, 9 * TILE_SIZE)
place_object('tree1', 7 * TILE_SIZE, 45 * TILE_SIZE)
place_object('tree2', 51 * TILE_SIZE, 46 * TILE_SIZE)
place_object('tree1', 76 * TILE_SIZE, 45 * TILE_SIZE)
place_object('tree1', 15 * TILE_SIZE, 95 * TILE_SIZE)
place_object('tree2', 70 * TILE_SIZE, 96 * TILE_SIZE)

place_object('bench', 23 * TILE_SIZE, 26 * TILE_SIZE)
place_object('bench', 62 * TILE_SIZE, 26 * TILE_SIZE)
place_object('parklight', 26 * TILE_SIZE, 24 * TILE_SIZE)
place_object('parklight', 33 * TILE_SIZE, 24 * TILE_SIZE)
place_object('parklight', 58 * TILE_SIZE, 24 * TILE_SIZE)
place_object('dustbin', 23 * TILE_SIZE, 38 * TILE_SIZE)
place_object('recyclebin', 61 * TILE_SIZE, 38 * TILE_SIZE)
place_object('mailboxblue', 26 * TILE_SIZE, 66 * TILE_SIZE)



# ============================================
# INDUSTRIAL ZONE
# ============================================

# Main industrial
place_horizontal_road_main(113, 28, 77)
place_horizontal_road_main(113, 7, 77)

# Horizontal industrial streets
place_horizontal_road_normal(113, 50, 77)
place_horizontal_road_normal(113, 70, 77)
place_horizontal_road_normal(113, 90, 77)
place_horizontal_road_normal(113, 110, 77)
place_horizontal_road_normal(113, 128, 77)


place_vertical_road_main(150, 16, 12)
place_vertical_road_main(150, 37, 13)
place_vertical_road_main(150, 55, 15)
place_vertical_road_main(150, 75, 15)
place_vertical_road_main(150, 95, 15)
place_vertical_road_main(150, 115, 13)
place_vertical_road_main(150, 133, 12)

# Vertical industrial streets
place_vertical_road_normal(125, 16, 12)
place_vertical_road_normal(125, 37, 12)
place_vertical_road_normal(125, 55, 14)
place_vertical_road_normal(125, 75, 14)
place_vertical_road_normal(125, 95, 14)
place_vertical_road_normal(125, 115, 13)
place_vertical_road_normal(125, 133, 12)

place_vertical_road_normal(175, 16, 12)
place_vertical_road_normal(175, 37, 13)
place_vertical_road_normal(175, 55, 14)
place_vertical_road_normal(175, 75, 14)
place_vertical_road_normal(175, 95, 14)
place_vertical_road_normal(175, 115, 13)
place_vertical_road_normal(175, 133, 12)

# Industrial crosswalks
place_crosswalk_vertical(128, 26, 3)
place_crosswalk_vertical(128, 27, 3)
place_crosswalk_vertical(153, 26, 3)
place_crosswalk_vertical(153, 27, 3)
place_crosswalk_vertical(157, 26, 3)
place_crosswalk_vertical(157, 27, 3)
place_crosswalk_vertical(178, 26, 3)
place_crosswalk_vertical(178, 27, 3)

place_crosswalk_vertical(128, 49, 3)
place_crosswalk_vertical(128, 50, 3)
place_crosswalk_vertical(153, 49, 3)
place_crosswalk_vertical(153, 50, 3)
place_crosswalk_vertical(157, 49, 3)
place_crosswalk_vertical(157, 50, 3)
place_crosswalk_vertical(178, 49, 3)
place_crosswalk_vertical(178, 50, 3)

place_crosswalk_vertical(128, 69, 3)
place_crosswalk_vertical(128, 70, 3)
place_crosswalk_vertical(153, 69, 3)
place_crosswalk_vertical(153, 70, 3)
place_crosswalk_vertical(157, 69, 3)
place_crosswalk_vertical(157, 70, 3)
place_crosswalk_vertical(178, 69, 3)
place_crosswalk_vertical(178, 70, 3)

place_crosswalk_vertical(128, 89, 3)
place_crosswalk_vertical(128, 90, 3)
place_crosswalk_vertical(153, 89, 3)
place_crosswalk_vertical(153, 90, 3)
place_crosswalk_vertical(157, 89, 3)
place_crosswalk_vertical(157, 90, 3)
place_crosswalk_vertical(178, 89, 3)
place_crosswalk_vertical(178, 90, 3)

place_crosswalk_vertical(128, 109, 3)
place_crosswalk_vertical(128, 110, 3)
place_crosswalk_vertical(153, 109, 3)
place_crosswalk_vertical(153, 110, 3)
place_crosswalk_vertical(157, 109, 3)
place_crosswalk_vertical(157, 110, 3)
place_crosswalk_vertical(178, 109, 3)
place_crosswalk_vertical(178, 110, 3)

place_crosswalk_vertical(128, 126, 3)
place_crosswalk_vertical(128, 127, 3)
place_crosswalk_vertical(153, 126, 3)
place_crosswalk_vertical(153, 127, 3)
place_crosswalk_vertical(157, 126, 3)
place_crosswalk_vertical(157, 127, 3)
place_crosswalk_vertical(178, 126, 3)
place_crosswalk_vertical(178, 127, 3)


# TOP SECTION
place_object('building1', 117 * TILE_SIZE, 19 * TILE_SIZE)
place_object('building2', 121 * TILE_SIZE, 19 * TILE_SIZE)
place_object('building4', 119 * TILE_SIZE, 23 * TILE_SIZE)

place_object('building1', 134 * TILE_SIZE, 19 * TILE_SIZE)
place_object('building3.5', 137.5 * TILE_SIZE, 19 * TILE_SIZE)
place_object('building4', 142 * TILE_SIZE, 19 * TILE_SIZE)
place_object('building3.5', 146 * TILE_SIZE, 19 * TILE_SIZE)
place_object('building2', 134 * TILE_SIZE, 23 * TILE_SIZE)
place_object('building4', 138 * TILE_SIZE, 23 * TILE_SIZE)
place_object('building3', 142 * TILE_SIZE, 23 * TILE_SIZE)
place_object('building3.5', 146 * TILE_SIZE, 23 * TILE_SIZE)


place_object('building1', 163 * TILE_SIZE, 19 * TILE_SIZE)
place_object('building3', 167 * TILE_SIZE, 19 * TILE_SIZE)
place_object('building2', 171 * TILE_SIZE, 19 * TILE_SIZE)
place_object('building3.5', 163 * TILE_SIZE, 23 * TILE_SIZE)
place_object('building4', 167 * TILE_SIZE, 23 * TILE_SIZE)
place_object('building3', 171 * TILE_SIZE, 23 * TILE_SIZE)

place_object('building1', 184 * TILE_SIZE, 19 * TILE_SIZE)
place_object('building3', 188 * TILE_SIZE, 19 * TILE_SIZE)
place_object('building2', 184 * TILE_SIZE, 23 * TILE_SIZE)
place_object('building3.5', 188 * TILE_SIZE, 23 * TILE_SIZE)



# BLOCK 1
place_object('building4', 119 * TILE_SIZE, 40 * TILE_SIZE)
place_object('building4', 119 * TILE_SIZE, 44 * TILE_SIZE)

place_object('building4', 135 * TILE_SIZE, 40 * TILE_SIZE)
place_object('building3', 139 * TILE_SIZE, 40 * TILE_SIZE)
place_object('building1', 142 * TILE_SIZE, 40 * TILE_SIZE)
place_object('building2', 146 * TILE_SIZE, 40 * TILE_SIZE)
place_object('building3.5', 134 * TILE_SIZE, 44 * TILE_SIZE)
place_object('building2', 137.5 * TILE_SIZE, 44 * TILE_SIZE)
place_object('building4', 142 * TILE_SIZE, 44 * TILE_SIZE)
place_object('building3', 146 * TILE_SIZE, 44 * TILE_SIZE)


place_object('building2', 163 * TILE_SIZE, 40 * TILE_SIZE)
place_object('building4', 167 * TILE_SIZE, 40 * TILE_SIZE)
place_object('building3.5', 171 * TILE_SIZE, 40 * TILE_SIZE)
place_object('building1', 163 * TILE_SIZE, 44 * TILE_SIZE)
place_object('building3', 166 * TILE_SIZE, 44 * TILE_SIZE)
place_object('building4', 170 * TILE_SIZE, 44 * TILE_SIZE)

place_object('building4', 184.5 * TILE_SIZE, 40 * TILE_SIZE)
place_object('building2', 188 * TILE_SIZE, 40 * TILE_SIZE)
place_object('building4', 184.5 * TILE_SIZE, 44 * TILE_SIZE)
place_object('building1', 188 * TILE_SIZE, 44 * TILE_SIZE)


# BLOCK 2
place_object('building4', 119 * TILE_SIZE, 58 * TILE_SIZE)
place_object('building1', 117 * TILE_SIZE, 64 * TILE_SIZE)
place_object('building2', 121 * TILE_SIZE, 64 * TILE_SIZE)


place_object('building3.5', 134 * TILE_SIZE, 58 * TILE_SIZE)
place_object('building2', 138 * TILE_SIZE, 58 * TILE_SIZE)
place_object('building3', 142 * TILE_SIZE, 58 * TILE_SIZE)
place_object('building1', 146 * TILE_SIZE, 58 * TILE_SIZE)
place_object('building3', 134 * TILE_SIZE, 64 * TILE_SIZE)
place_object('building1', 137.5 * TILE_SIZE, 64 * TILE_SIZE)
place_object('building2', 141.3 * TILE_SIZE, 64 * TILE_SIZE)
place_object('building4', 145.6 * TILE_SIZE, 64 * TILE_SIZE)


place_object('building3.5', 163 * TILE_SIZE, 58 * TILE_SIZE)
place_object('building3', 167 * TILE_SIZE, 58 * TILE_SIZE)
place_object('building2', 171 * TILE_SIZE, 58 * TILE_SIZE)
place_object('building1', 163 * TILE_SIZE, 64 * TILE_SIZE)
place_object('building4', 167 * TILE_SIZE, 64 * TILE_SIZE)
place_object('building3', 171 * TILE_SIZE, 64 * TILE_SIZE)

place_object('building2', 184.5 * TILE_SIZE, 58 * TILE_SIZE)
place_object('building1', 189 * TILE_SIZE, 58 * TILE_SIZE)
place_object('building3', 184.5 * TILE_SIZE, 64 * TILE_SIZE)
place_object('building3.5', 189 * TILE_SIZE, 64 * TILE_SIZE)

# BLOCK 3
place_object('building1', 117 * TILE_SIZE, 78 * TILE_SIZE)
place_object('building2', 121 * TILE_SIZE, 78 * TILE_SIZE)
place_object('building4', 119 * TILE_SIZE, 84 * TILE_SIZE)

place_object('building1', 134 * TILE_SIZE, 78 * TILE_SIZE)
place_object('building3.5', 137.5 * TILE_SIZE, 78 * TILE_SIZE)
place_object('building4', 142 * TILE_SIZE, 78 * TILE_SIZE)
place_object('building3.5', 146 * TILE_SIZE, 78 * TILE_SIZE)
place_object('building2', 134 * TILE_SIZE, 84 * TILE_SIZE)
place_object('building4', 138 * TILE_SIZE, 84 * TILE_SIZE)
place_object('building3', 142 * TILE_SIZE, 84 * TILE_SIZE)
place_object('building3.5', 146 * TILE_SIZE, 84 * TILE_SIZE)


place_object('building1', 163 * TILE_SIZE, 78 * TILE_SIZE)
place_object('building3', 167 * TILE_SIZE, 78 * TILE_SIZE)
place_object('building2', 171 * TILE_SIZE, 78 * TILE_SIZE)
place_object('building3.5', 163 * TILE_SIZE, 84 * TILE_SIZE)
place_object('building4', 167 * TILE_SIZE, 84 * TILE_SIZE)
place_object('building3', 171 * TILE_SIZE, 84 * TILE_SIZE)

place_object('building1', 184 * TILE_SIZE, 78 * TILE_SIZE)
place_object('building3', 188 * TILE_SIZE, 78 * TILE_SIZE)
place_object('building2', 184 * TILE_SIZE, 84 * TILE_SIZE)
place_object('building3.5', 188 * TILE_SIZE, 84 * TILE_SIZE)

# BLOCK 4
place_object('building4', 119 * TILE_SIZE, 98 * TILE_SIZE)
place_object('building4', 119 * TILE_SIZE, 104 * TILE_SIZE)

place_object('building4', 135 * TILE_SIZE, 98 * TILE_SIZE)
place_object('building3', 139 * TILE_SIZE, 98 * TILE_SIZE)
place_object('building1', 142 * TILE_SIZE, 98 * TILE_SIZE)
place_object('building2', 146 * TILE_SIZE, 98 * TILE_SIZE)
place_object('building3.5', 134 * TILE_SIZE, 104 * TILE_SIZE)
place_object('building2', 137.5 * TILE_SIZE, 104 * TILE_SIZE)
place_object('building4', 142 * TILE_SIZE, 104 * TILE_SIZE)
place_object('building3', 146 * TILE_SIZE, 104 * TILE_SIZE)


place_object('building2', 163 * TILE_SIZE, 98 * TILE_SIZE)
place_object('building4', 167 * TILE_SIZE, 98 * TILE_SIZE)
place_object('building3.5', 171 * TILE_SIZE, 98 * TILE_SIZE)
place_object('building1', 163 * TILE_SIZE, 104 * TILE_SIZE)
place_object('building3', 166 * TILE_SIZE, 104 * TILE_SIZE)
place_object('building4', 170 * TILE_SIZE, 104 * TILE_SIZE)

place_object('building4', 184.5 * TILE_SIZE, 98 * TILE_SIZE)
place_object('building2', 189 * TILE_SIZE, 98 * TILE_SIZE)
place_object('building4', 184.5 * TILE_SIZE, 104 * TILE_SIZE)
place_object('building1', 189 * TILE_SIZE,104 * TILE_SIZE)

# BLOCK 5
place_object('building4', 119 * TILE_SIZE, 118 * TILE_SIZE)
place_object('building1', 117 * TILE_SIZE, 122 * TILE_SIZE)
place_object('building2', 121 * TILE_SIZE, 122 * TILE_SIZE)


place_object('building3.5', 134 * TILE_SIZE, 118 * TILE_SIZE)
place_object('building2', 138 * TILE_SIZE, 118 * TILE_SIZE)
place_object('building3', 142 * TILE_SIZE, 118 * TILE_SIZE)
place_object('building1', 146 * TILE_SIZE, 118 * TILE_SIZE)
place_object('building3', 134 * TILE_SIZE, 122 * TILE_SIZE)
place_object('building1', 137.5 * TILE_SIZE, 122 * TILE_SIZE)
place_object('building2', 141.3 * TILE_SIZE, 122 * TILE_SIZE)
place_object('building4', 145.6 * TILE_SIZE, 122 * TILE_SIZE)


place_object('building3.5', 163 * TILE_SIZE, 118 * TILE_SIZE)
place_object('building3', 167 * TILE_SIZE, 118 * TILE_SIZE)
place_object('building2', 171 * TILE_SIZE, 118 * TILE_SIZE)
place_object('building1', 163 * TILE_SIZE, 122 * TILE_SIZE)
place_object('building4', 167 * TILE_SIZE, 122 * TILE_SIZE)
place_object('building3', 171 * TILE_SIZE, 122 * TILE_SIZE)

place_object('building2', 184.5 * TILE_SIZE, 118 * TILE_SIZE)
place_object('building1', 189 * TILE_SIZE, 118 * TILE_SIZE)
place_object('building3', 184.5 * TILE_SIZE, 122 * TILE_SIZE)
place_object('building3.5', 189 * TILE_SIZE, 122 * TILE_SIZE)

# BLOCK 6
place_object('building1', 117 * TILE_SIZE, 136 * TILE_SIZE)
place_object('building2', 121 * TILE_SIZE, 136 * TILE_SIZE)
place_object('building4', 119 * TILE_SIZE, 140 * TILE_SIZE)

place_object('building1', 134 * TILE_SIZE, 136 * TILE_SIZE)
place_object('building3.5', 137.5 * TILE_SIZE, 136 * TILE_SIZE)
place_object('building4', 142 * TILE_SIZE, 136 * TILE_SIZE)
place_object('building3.5', 146 * TILE_SIZE, 136 * TILE_SIZE)
place_object('building2', 134 * TILE_SIZE, 140 * TILE_SIZE)
place_object('building4', 138 * TILE_SIZE, 140 * TILE_SIZE)
place_object('building3', 142 * TILE_SIZE, 140 * TILE_SIZE)
place_object('building3.5', 146 * TILE_SIZE, 140 * TILE_SIZE)


place_object('building1', 163 * TILE_SIZE, 136 * TILE_SIZE)
place_object('building3', 167 * TILE_SIZE, 136 * TILE_SIZE)
place_object('building2', 171 * TILE_SIZE, 136 * TILE_SIZE)
place_object('building3.5', 163 * TILE_SIZE, 140 * TILE_SIZE)
place_object('building4', 167 * TILE_SIZE, 140 * TILE_SIZE)
place_object('building3', 171 * TILE_SIZE, 140 * TILE_SIZE)

place_object('building1', 184 * TILE_SIZE, 136 * TILE_SIZE)
place_object('building3', 188 * TILE_SIZE, 136 * TILE_SIZE)
place_object('building2', 184 * TILE_SIZE, 140 * TILE_SIZE)
place_object('building3.5', 188 * TILE_SIZE, 140 * TILE_SIZE)

# ============================================
# INDUSTRIAL PROPS
# ============================================

# Main boulevard props
place_object('parklight', 124 * TILE_SIZE, 19 * TILE_SIZE)
place_object('parklight', 124 * TILE_SIZE, 40 * TILE_SIZE)
place_object('parklight', 124 * TILE_SIZE, 60 * TILE_SIZE)
place_object('parklight', 124 * TILE_SIZE, 80 * TILE_SIZE)
place_object('parklight', 124 * TILE_SIZE, 100 * TILE_SIZE)
place_object('parklight', 124 * TILE_SIZE, 120 * TILE_SIZE)

place_object('parklight', 180 * TILE_SIZE, 15 * TILE_SIZE)
place_object('parklight', 180 * TILE_SIZE, 40 * TILE_SIZE)
place_object('parklight', 180 * TILE_SIZE, 60 * TILE_SIZE)
place_object('parklight', 180 * TILE_SIZE, 80 * TILE_SIZE)
place_object('parklight', 180 * TILE_SIZE, 100 * TILE_SIZE)
place_object('parklight', 180 * TILE_SIZE, 120 * TILE_SIZE)

# Utility props
place_object('dustbin', 149 * TILE_SIZE, 48 * TILE_SIZE)
place_object('recyclebin', 149 * TILE_SIZE, 88 * TILE_SIZE)
place_object('firehydrant', 149 * TILE_SIZE, 128 * TILE_SIZE)

# Small loading zones
place_object('box1', 190 * TILE_SIZE, 58 * TILE_SIZE)
place_object('box2', 191 * TILE_SIZE, 58 * TILE_SIZE)
place_object('box1', 190 * TILE_SIZE, 98 * TILE_SIZE)
place_object('box2', 191 * TILE_SIZE, 98 * TILE_SIZE)

# Facilities
place_object('toilet', 149 * TILE_SIZE, 138 * TILE_SIZE)
place_object('vendingmachine', 174 * TILE_SIZE, 138 * TILE_SIZE)

load_player_spritesheets()

# Sort objects
map_objects.sort(key=lambda obj: obj['y'])

# ============================================
# TRAFFIC SYSTEM
# ============================================

# Car state flags
CAR_STATE_DRIVING = 0
CAR_STATE_WAITING = 1
CAR_STATE_TURNING = 2
CAR_STATE_BRAKING = 3

def spawn_traffic_car():
    """Spawn with STRICT lane separation"""
    global spawn_timer
    
    if len(traffic_vehicles) >= TRAFFIC_CONFIG['max_cars']:
        return
    
    spawn_timer += 1
    if spawn_timer < TRAFFIC_CONFIG['spawn_interval']:
        return
    spawn_timer = 0
    
    # FIXED spawn points with PROPER lane separation
    spawn_points = [
        # Horizontal roads - RIGHT direction (upper lanes)
        {'x': 8 * TILE_SIZE, 'y': 30 * TILE_SIZE, 'direction': 'right'},
        {'x': 8 * TILE_SIZE, 'y': 60 * TILE_SIZE, 'direction': 'right'},
        {'x': 8 * TILE_SIZE, 'y': 84 * TILE_SIZE, 'direction': 'right'},
        
        # Horizontal roads - LEFT direction (lower lanes, +3 tiles offset)
        {'x': 100 * TILE_SIZE, 'y': (30 + 3) * TILE_SIZE, 'direction': 'left'},
        {'x': 100 * TILE_SIZE, 'y': (60 + 3) * TILE_SIZE, 'direction': 'left'},
        {'x': 100 * TILE_SIZE, 'y': (84 + 3) * TILE_SIZE, 'direction': 'left'},
        
        # Vertical roads - DOWN direction (left lanes)
        {'x': 29 * TILE_SIZE, 'y': 8 * TILE_SIZE, 'direction': 'down'},
        {'x': 54 * TILE_SIZE, 'y': 8 * TILE_SIZE, 'direction': 'down'},
        {'x': 79 * TILE_SIZE, 'y': 8 * TILE_SIZE, 'direction': 'down'},
        {'x': 106 * TILE_SIZE, 'y': 8 * TILE_SIZE, 'direction': 'down'},
        
        # Vertical roads - UP direction (right lanes, +3 tiles offset)
        {'x': (29 + 3) * TILE_SIZE, 'y': 95 * TILE_SIZE, 'direction': 'up'},
        {'x': (54 + 3) * TILE_SIZE, 'y': 95 * TILE_SIZE, 'direction': 'up'},
        {'x': (79 + 3) * TILE_SIZE, 'y': 95 * TILE_SIZE, 'direction': 'up'},
        {'x': (106 + 3) * TILE_SIZE, 'y': 95 * TILE_SIZE, 'direction': 'up'},
    ]
    
    for _ in range(5):
        spawn = random.choice(spawn_points)
        
        if not is_position_blocked(spawn['x'], spawn['y'], 100):
            car_type = random.choice(['ambulanceup', 'truckup', 'carup1'])
            
            traffic_vehicles.append({
                'name': car_type,
                'x': float(spawn['x']),
                'y': float(spawn['y']),
                'direction': spawn['direction'],
                'speed': TRAFFIC_CONFIG['car_speed'],
                'target_speed': TRAFFIC_CONFIG['car_max_speed'],
                'angle': get_angle_for_direction(spawn['direction']),
                'state': CAR_STATE_DRIVING,
                'wait_timer': 0,
                'target_lane': None,
                'last_intersection': None,
                'frames_since_turn': 999,
                'lane_y': spawn['y'] if spawn['direction'] in ['right', 'left'] else None,
                'lane_x': spawn['x'] if spawn['direction'] in ['up', 'down'] else None,
            })
            return

def is_position_blocked(x, y, min_dist):
    for car in traffic_vehicles:
        dx = abs(car['x'] - x)
        dy = abs(car['y'] - y)
        if (dx * dx + dy * dy) ** 0.5 < min_dist:
            return True
    return False

def get_angle_for_direction(direction):
    return {'up': 180, 'down': 0, 'left': 270, 'right': 90}.get(direction, 0)

def is_on_road(x, y):
    """Check if on road - INCLUDING CROSSWALKS"""
    tile_x = int(x // TILE_SIZE)
    tile_y = int(y // TILE_SIZE)
    
    if 0 <= tile_x < MAP_TILES_WIDTH and 0 <= tile_y < MAP_TILES_HEIGHT:
        tile = map_grid[tile_y][tile_x]
        tile_lower = tile.lower()
        
        if ('road' in tile_lower or 'crosswalk' in tile_lower) and 'sidewalk' not in tile_lower:
            return True
    return False

def is_at_intersection(x, y):
    """Check if at intersection"""
    threshold = 12
    
    for intersection in INTERSECTIONS:
        dx = abs(x - intersection['x'])
        dy = abs(y - intersection['y'])
        
        if dx < threshold and dy < threshold:
            return intersection
    return None

def get_opposite_direction(direction):
    return {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left'}.get(direction, direction)

def choose_new_direction(car, intersection):
    """Choose direction - 90% go straight"""
    current_dir = car['direction']
    opposite_dir = get_opposite_direction(current_dir)
    
    available_dirs = [d for d in intersection['directions'].keys() if d != opposite_dir]
    
    if not available_dirs:
        return current_dir, None
    
    # 90% go straight to reduce turns
    if current_dir in available_dirs and random.random() < 0.90:
        new_dir = current_dir
    else:
        new_dir = random.choice(available_dirs)
    
    # Get target lane
    target_positions = intersection['directions'][new_dir]
    target_lane = target_positions[0] if target_positions else None
    
    # Update lane tracking
    if new_dir in ['right', 'left']:
        car['lane_y'] = target_lane[1] if target_lane else car['y']
        car['lane_x'] = None
    else:
        car['lane_x'] = target_lane[0] if target_lane else car['x']
        car['lane_y'] = None
    
    return new_dir, target_lane

def check_obstacle_ahead(car, check_distance):
    """Check for cars AND PLAYER ahead"""
    min_distance = check_distance
    found_obstacle = False
    
    # Check other cars - STRICT lane checking
    for other_car in traffic_vehicles:
        if other_car == car:
            continue
        
        same_lane = False
        is_ahead = False
        dist = 0
        
        if car['direction'] == 'right':
            # STRICT: same lane means very close Y position
            same_lane = abs(car['y'] - other_car['y']) < 15
            if same_lane and other_car['x'] > car['x']:
                is_ahead = True
                dist = other_car['x'] - car['x']
                
        elif car['direction'] == 'left':
            same_lane = abs(car['y'] - other_car['y']) < 15
            if same_lane and other_car['x'] < car['x']:
                is_ahead = True
                dist = car['x'] - other_car['x']
                
        elif car['direction'] == 'down':
            same_lane = abs(car['x'] - other_car['x']) < 15
            if same_lane and other_car['y'] > car['y']:
                is_ahead = True
                dist = other_car['y'] - car['y']
                
        elif car['direction'] == 'up':
            same_lane = abs(car['x'] - other_car['x']) < 15
            if same_lane and other_car['y'] < car['y']:
                is_ahead = True
                dist = car['y'] - other_car['y']
        
        if is_ahead and 0 < dist < min_distance:
            min_distance = dist
            found_obstacle = True
    
    # Check player
    player_ahead = False
    player_dist = 0
    
    if car['direction'] == 'right':
        if abs(car['y'] - player.y) < 25 and player.x > car['x']:
            player_dist = player.x - car['x']
            player_ahead = True
    elif car['direction'] == 'left':
        if abs(car['y'] - player.y) < 25 and player.x < car['x']:
            player_dist = car['x'] - player.x
            player_ahead = True
    elif car['direction'] == 'down':
        if abs(car['x'] - player.x) < 25 and player.y > car['y']:
            player_dist = player.y - car['y']
            player_ahead = True
    elif car['direction'] == 'up':
        if abs(car['x'] - player.x) < 25 and player.y < car['y']:
            player_dist = car['y'] - player.y
            player_ahead = True
    
    if player_ahead and player_dist < min_distance:
        min_distance = player_dist
        found_obstacle = True
    
    return found_obstacle, min_distance

def update_traffic():
    """Traffic update with STRICT lane keeping"""
    spawn_traffic_car()
    
    for car in traffic_vehicles[:]:
        if 'frames_since_turn' not in car:
            car['frames_since_turn'] = 999
        car['frames_since_turn'] += 1
        
        # STRICT lane keeping - cars MUST stay in their lane
        if car['state'] == CAR_STATE_DRIVING and car['frames_since_turn'] > 30:
            if car['direction'] in ['right', 'left'] and car['lane_y'] is not None:
                # Keep Y position fixed to lane
                if abs(car['y'] - car['lane_y']) > 3:
                    car['y'] += (car['lane_y'] - car['y']) * 0.15
            elif car['direction'] in ['up', 'down'] and car['lane_x'] is not None:
                # Keep X position fixed to lane
                if abs(car['x'] - car['lane_x']) > 3:
                    car['x'] += (car['lane_x'] - car['x']) * 0.15
        
        # Check obstacles
        has_obstacle, obstacle_dist = check_obstacle_ahead(car, TRAFFIC_CONFIG['brake_distance'])
        
        # Braking system
        if has_obstacle:
            if obstacle_dist < TRAFFIC_CONFIG['stop_distance']:
                car['state'] = CAR_STATE_WAITING
                car['speed'] = max(0, car['speed'] - TRAFFIC_CONFIG['brake_force'] * 3)
                car['wait_timer'] += 1
                
                if car['wait_timer'] > 500:
                    traffic_vehicles.remove(car)
                continue
            elif obstacle_dist < TRAFFIC_CONFIG['brake_distance']:
                car['state'] = CAR_STATE_BRAKING
                car['speed'] = max(1.0, car['speed'] - TRAFFIC_CONFIG['brake_force'])
            else:
                car['state'] = CAR_STATE_DRIVING
                car['speed'] = min(car['target_speed'], car['speed'] + 0.06)
        else:
            car['state'] = CAR_STATE_DRIVING
            car['speed'] = min(car['target_speed'], car['speed'] + 0.06)
            car['wait_timer'] = 0
        
        # Intersection handling
        intersection = None
        if car['frames_since_turn'] > 30:
            intersection = is_at_intersection(car['x'], car['y'])
        
        if intersection and car['state'] in [CAR_STATE_DRIVING, CAR_STATE_BRAKING]:
            if car.get('last_intersection') != intersection:
                new_direction, target_lane = choose_new_direction(car, intersection)
                
                if new_direction != car['direction']:
                    car['direction'] = new_direction
                    car['angle'] = get_angle_for_direction(new_direction)
                    car['target_lane'] = target_lane
                    car['state'] = CAR_STATE_TURNING
                    car['frames_since_turn'] = 0
                    
                    car['x'] = float(intersection['x'])
                    car['y'] = float(intersection['y'])
                
                car['last_intersection'] = intersection
        
        # Turn completion
        if car['state'] == CAR_STATE_TURNING and car['target_lane']:
            target_x, target_y = car['target_lane']
            
            dx = target_x - car['x']
            dy = target_y - car['y']
            dist = (dx * dx + dy * dy) ** 0.5
            
            if dist < 10:
                car['state'] = CAR_STATE_DRIVING
                car['target_lane'] = None
            else:
                car['x'] += dx * 0.15
                car['y'] += dy * 0.15
        
        # Movement
        if car['state'] in [CAR_STATE_DRIVING, CAR_STATE_BRAKING]:
            next_x, next_y = car['x'], car['y']
            
            if car['direction'] == 'right':
                next_x += car['speed']
            elif car['direction'] == 'left':
                next_x -= car['speed']
            elif car['direction'] == 'down':
                next_y += car['speed']
            elif car['direction'] == 'up':
                next_y -= car['speed']
            
            if is_on_road(next_x, next_y):
                car['x'], car['y'] = next_x, next_y
                
                if intersection is None:
                    car['last_intersection'] = None
            else:
                traffic_vehicles.remove(car)
                continue
        
        # Despawn
        dist = ((car['x'] - player.x)**2 + (car['y'] - player.y)**2)**0.5
        if dist > TRAFFIC_CONFIG['despawn_distance']:
            traffic_vehicles.remove(car)


# ============================================
# REPLACE check_collision_with_cars function
# ============================================
def play_hurt_animation():
    """Play hurt animation once"""
    player_animation['state'] = 'hurt'
    player_animation['current_frame'] = 0
    player_animation['frame_delay'] = 0

def get_car_hitbox(car):
    """Get rectangular hitbox for car based on direction and type"""
    # Determine car size
    if car['name'] in ['truckup']:
        width, height = 32, 51  # Larger vehicles
    else:
        width, height = 27, 46  # Regular cars
    
    # Rotate hitbox based on direction
    if car['direction'] in ['up', 'down']:
        # Vertical: use width/height as-is
        half_w = width / 2
        half_h = height / 2
    else:  # left, right
        # Horizontal: swap width and height
        half_w = height / 2
        half_h = width / 2
    
    return {
        'left': car['x'] - half_w,
        'right': car['x'] + half_w,
        'top': car['y'] - half_h,
        'bottom': car['y'] + half_h
    }

def check_rect_collision(x, y, hitbox, padding=0):
    """Check if point (x, y) collides with rectangular hitbox"""
    player_size = 6 + padding  # Player collision size
    
    return (x + player_size > hitbox['left'] and 
            x - player_size < hitbox['right'] and
            y + player_size > hitbox['top'] and 
            y - player_size < hitbox['bottom'])

def check_player_car_collision(new_x, new_y):
    """Check if player would collide with ANY car at new position - RECTANGULAR"""
    for car in traffic_vehicles:
        hitbox = get_car_hitbox(car)
        
        if check_rect_collision(new_x, new_y, hitbox, padding=5):
            return True  # Collision - block movement
    
    return False  # No collision - allow movement

def check_collision_with_cars():
    """Death collision - only fast moving cars from front/side - RECTANGULAR"""
    for car in traffic_vehicles:
        hitbox = get_car_hitbox(car)
        
        # Check if player is inside car hitbox
        if check_rect_collision(player.x, player.y, hitbox, padding=0):
            # Car must be moving fast enough to kill
            if car['speed'] < 1.8:
                continue  # Stopped/slow car won't kill
            
            # Check impact direction (player position relative to car center)
            dx = player.x - car['x']
            dy = player.y - car['y']
            
            # Front/side collision only (not rear-end)
            if car['direction'] == 'right':
                if dx > -20:  # Player not behind car
                    play_hurt_animation()  # Play hurt animation
                    return True
            elif car['direction'] == 'left':
                if dx < 20:
                    play_hurt_animation()  # Play hurt animation
                    return True
            elif car['direction'] == 'down':
                if dy > -20:
                    play_hurt_animation()  # Play hurt animation
                    return True
            elif car['direction'] == 'up':
                if dy < 20:
                    play_hurt_animation()  # Play hurt animation
                    return True
    
    return False

def restart_game():
    """Restart the game - reset player and game state"""
    global player, traffic_vehicles, game_state, bullets  # Add bullets here
    
    # Reset player position
    player.x = 500
    player.y = 500
    player_animation['direction'] = 'down'
    player_animation['current_frame'] = 0
    
    # Clear all traffic
    traffic_vehicles.clear()
    
    # Clear all bullets - ADD THIS LINE
    bullets.clear()
    
    # Reset game state
    game_state['alive'] = True
    game_state['death_timer'] = 0

# ============================================
# MAIN GAME LOOP
# ============================================

def draw():
    screen.clear()
    
    global camera_x, camera_y
    
    view_width = WIDTH / CAMERA_ZOOM
    view_height = HEIGHT / CAMERA_ZOOM
    
    camera_x = player.x - view_width / 2
    camera_y = player.y - view_height / 2
    
    camera_x = max(0, min(camera_x, MAP_WIDTH - view_width))
    camera_y = max(0, min(camera_y, MAP_HEIGHT - view_height))
    
    start_tile_x = max(0, int(camera_x // TILE_SIZE) - 1)
    end_tile_x = min(MAP_TILES_WIDTH, int((camera_x + view_width) // TILE_SIZE) + 2)
    start_tile_y = max(0, int(camera_y // TILE_SIZE) - 1)
    end_tile_y = min(MAP_TILES_HEIGHT, int((camera_y + view_height) // TILE_SIZE) + 2)
    
    # Draw tiles
    for tile_y in range(start_tile_y, end_tile_y):
        for tile_x in range(start_tile_x, end_tile_x):
            tile_data = map_grid[tile_y][tile_x]
            
            world_x = tile_x * TILE_SIZE
            world_y = tile_y * TILE_SIZE
            screen_x = (world_x - camera_x) * CAMERA_ZOOM
            screen_y = (world_y - camera_y) * CAMERA_ZOOM
            
            if '|rot' in tile_data:
                parts = tile_data.split('|rot')
                tile_name = parts[0]
                rotation = int(parts[1])
            else:
                tile_name = tile_data
                rotation = 0
            
            try:
                img = get_rotated_image(tile_name, rotation)
                if img:
                    scaled_img = pygame.transform.scale(img, 
                        (int(img.get_width() * CAMERA_ZOOM) + 1, int(img.get_height() * CAMERA_ZOOM) + 1))
                    screen.blit(scaled_img, (int(screen_x), int(screen_y)))
            except:
                if 'road' in tile_name:
                    screen.draw.filled_rect(Rect(int(screen_x), int(screen_y), int(TILE_SIZE * CAMERA_ZOOM) + 1, int(TILE_SIZE * CAMERA_ZOOM) + 1), (60, 60, 60))
                elif 'sidewalk' in tile_name:
                    screen.draw.filled_rect(Rect(int(screen_x), int(screen_y), int(TILE_SIZE * CAMERA_ZOOM) + 1, int(TILE_SIZE * CAMERA_ZOOM) + 1), (100, 100, 110))
                elif 'grass' in tile_name:
                    screen.draw.filled_rect(Rect(int(screen_x), int(screen_y), int(TILE_SIZE * CAMERA_ZOOM) + 1, int(TILE_SIZE * CAMERA_ZOOM) + 1), (60, 140, 60))
    
    # Draw objects
    for obj in map_objects:
        world_x = obj['x']
        world_y = obj['y']
        screen_x = (world_x - camera_x) * CAMERA_ZOOM
        screen_y = (world_y - camera_y) * CAMERA_ZOOM
        
        if -200 < screen_x < WIDTH + 200 and -200 < screen_y < HEIGHT + 200:
            try:
                img = pygame.image.load(f'images/{obj["name"]}.png')
                scaled_img = pygame.transform.scale(img,
                    (int(img.get_width() * CAMERA_ZOOM), int(img.get_height() * CAMERA_ZOOM)))
                screen.blit(scaled_img, (screen_x - scaled_img.get_width()//2, screen_y - scaled_img.get_height()//2))
            except:
                if 'building' in obj['name'] or 'house' in obj['name'] or 'shop' in obj['name']:
                    screen.draw.filled_rect(Rect(screen_x-25*CAMERA_ZOOM, screen_y-40*CAMERA_ZOOM, 50*CAMERA_ZOOM, 80*CAMERA_ZOOM), (120, 100, 100))
                elif 'tree' in obj['name']:
                    screen.draw.filled_circle((int(screen_x), int(screen_y)), int(8*CAMERA_ZOOM), (50, 150, 50))
                else:
                    screen.draw.filled_rect(Rect(screen_x-5*CAMERA_ZOOM, screen_y-5*CAMERA_ZOOM, 10*CAMERA_ZOOM, 10*CAMERA_ZOOM), (150, 150, 150))
    
    # Draw traffic cars
    for car in traffic_vehicles:
        world_x = car['x']
        world_y = car['y']
        screen_x = (world_x - camera_x) * CAMERA_ZOOM
        screen_y = (world_y - camera_y) * CAMERA_ZOOM
        
        if -200 < screen_x < WIDTH + 200 and -200 < screen_y < HEIGHT + 200:
            try:
                img = pygame.image.load(f'images/{car["name"]}.png')
                scaled_img = pygame.transform.scale(img,
                    (int(img.get_width() * CAMERA_ZOOM), int(img.get_height() * CAMERA_ZOOM)))
                rotated_car = pygame.transform.rotate(scaled_img, car['angle'])
                car_rect = rotated_car.get_rect(center=(int(screen_x), int(screen_y)))
                screen.blit(rotated_car, car_rect)
            except:
                 screen.draw.filled_rect(Rect(screen_x-10*CAMERA_ZOOM, screen_y-10*CAMERA_ZOOM, 20*CAMERA_ZOOM, 20*CAMERA_ZOOM), (200, 50, 50))

    # Draw player
    try:
        state = player_animation['state']
        direction = player_animation['direction']
        frame = player_animation['current_frame']
        
        player_img = get_player_frame(state, direction, frame)
        
        if player_img:
            # Get frame size and scale based on animation type
            frame_size = FRAME_SIZES.get(state, 64)

            player_scale = 0.6
            
            scaled_player = pygame.transform.scale(player_img,
                (int(frame_size * CAMERA_ZOOM * player_scale), int(frame_size * CAMERA_ZOOM * player_scale)))
            player_rect = scaled_player.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(scaled_player, player_rect)
        else:
            screen.draw.filled_circle((WIDTH // 2, HEIGHT // 2), int(10*CAMERA_ZOOM), (255, 255, 0))
    except Exception as e:
        screen.draw.filled_circle((WIDTH // 2, HEIGHT // 2), int(10*CAMERA_ZOOM), (255, 255, 0))
    
    # Draw gun if equipped - ADD THIS NEW SECTION
    if player_weapon['type'] == 'gun' and GUN_CONFIG['image']:
        try:
            direction = player_animation['direction']
            gun_img = get_rotated_gun(direction)
            
            if gun_img:
                # Scale gun
                gun_width = int(gun_img.get_width() * CAMERA_ZOOM * GUN_CONFIG['scale'])
                gun_height = int(gun_img.get_height() * CAMERA_ZOOM * GUN_CONFIG['scale'])
                scaled_gun = pygame.transform.scale(gun_img, (gun_width, gun_height))
                
                # Get offset position
                offset_x, offset_y = get_gun_offset(direction)
                
                # Calculate gun position (centered on player + offset)
                gun_x = WIDTH // 2 + (offset_x * CAMERA_ZOOM)
                gun_y = HEIGHT // 2 + (offset_y * CAMERA_ZOOM)
                
                gun_rect = scaled_gun.get_rect(center=(gun_x, gun_y))
                screen.blit(scaled_gun, gun_rect)
        except Exception as e:
            pass

    # Draw bullets - ALWAYS DRAW YELLOW CIRCLES
    for bullet in bullets:
        world_x = bullet['x']
        world_y = bullet['y']
        screen_x = (world_x - camera_x) * CAMERA_ZOOM
        screen_y = (world_y - camera_y) * CAMERA_ZOOM
        
        # Only draw if on screen
        if -100 < screen_x < WIDTH + 100 and -100 < screen_y < HEIGHT + 100:
            # Draw bright yellow circle - ALWAYS VISIBLE
            screen.draw.filled_circle((int(screen_x), int(screen_y)), 8, (255, 255, 0))


    # Draw NPCs - ADD THIS NEW SECTION (before drawing player)
    for npc in npcs:
        world_x = npc['x']
        world_y = npc['y']
        screen_x = (world_x - camera_x) * CAMERA_ZOOM
        screen_y = (world_y - camera_y) * CAMERA_ZOOM
        
        # Only draw if on screen
        if -200 < screen_x < WIDTH + 200 and -200 < screen_y < HEIGHT + 200:
            try:
                npc_img = get_npc_frame(npc['type'], npc['state'], npc['direction'], npc['current_frame'])
                
                if npc_img:
                    npc_scale = 0.5  # NPCs slightly smaller than player
                    scaled_npc = pygame.transform.scale(npc_img,
                        (int(64 * CAMERA_ZOOM * npc_scale), int(64 * CAMERA_ZOOM * npc_scale)))
                    npc_rect = scaled_npc.get_rect(center=(int(screen_x), int(screen_y)))
                    screen.blit(scaled_npc, npc_rect)
            except:
                # Fallback - draw circle
                screen.draw.filled_circle((int(screen_x), int(screen_y)), int(8*CAMERA_ZOOM), (100, 200, 100))
    
    # UI
    screen.draw.text(f"Position: ({int(player.x)}, {int(player.y)})", (10, 10), color="white", fontsize=24)
    screen.draw.text(f"Tile: ({int(player.x//TILE_SIZE)}, {int(player.y//TILE_SIZE)})", (10, 35), color="white", fontsize=24)
    screen.draw.text(f"Traffic: {len(traffic_vehicles)}/{TRAFFIC_CONFIG['max_cars']}", (10, 60), color="cyan", fontsize=20)
    screen.draw.text(f"NPCs: {len(npcs)}/{NPC_CONFIG['max_population']}", (10, 85), color="green", fontsize=20)
    screen.draw.text(f"BULLETS: {len(bullets)}", (10, 110), color="yellow", fontsize=24)
    screen.draw.text(f"WEAPON: {player_weapon['type']}", (10, 135), color="orange", fontsize=24)
    screen.draw.text("Press 3 = GUN | CLICK = SHOOT", (10, HEIGHT - 30), color="yellow", fontsize=20)

    # Death screen overlay
    if not game_state['alive']:
        # Red overlay
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)  # Semi-transparent
        overlay.fill((255, 0, 0))  # Red
        screen.blit(overlay, (0, 0))
        
        # Death text
        screen.draw.text("YOU DIED!", center=(WIDTH // 2, HEIGHT // 2 - 50), 
                        color="white", fontsize=80)
        screen.draw.text("Hit by a car!", center=(WIDTH // 2, HEIGHT // 2 + 20), 
                        color="white", fontsize=40)
        screen.draw.text("Restarting...", center=(WIDTH // 2, HEIGHT // 2 + 80), 
                        color="yellow", fontsize=30)


def update():
    global player
    
    # Update hurt animation if playing
    if player_animation['state'] == 'hurt':
        player_animation['frame_delay'] += 1
        
        if player_animation['frame_delay'] >= player_animation['animation_speed']:
            player_animation['frame_delay'] = 0
            player_animation['current_frame'] += 1
            
            # Hurt animation finished
            if player_animation['current_frame'] >= FRAME_COUNTS['hurt']:
                player_animation['current_frame'] = 0
                # Animation done, keep showing hurt state until restart
    
    # Check if player is alive
    if not game_state['alive']:
        game_state['death_timer'] += 1
        if game_state['death_timer'] >= game_state['death_delay']:
            restart_game()
        return  # Don't update anything else when dead
    
    # Update traffic
    update_traffic()

    # Update NPCs - ADD THIS LINE
    update_npcs()
    
    # Check collision with cars
    if check_collision_with_cars():
        game_state['alive'] = False
        game_state['death_timer'] = 0
        return
    
    # Weapon equip/unequip
    if keyboard.k_1:
        player_weapon['type'] = 'none'
        player_weapon['shoot_animation_done'] = False
    if keyboard.k_2:
        player_weapon['type'] = 'katana'
        player_weapon['shoot_animation_done'] = False
    if keyboard.k_3:
        player_weapon['type'] = 'gun'
        player_weapon['shoot_animation_done'] = False
        # Start shoot animation
        player_animation['state'] = 'shoot'
        player_animation['current_frame'] = 0
        player_animation['frame_delay'] = 0
    
    # Handle shoot animation (plays once when becoming idle with gun)
    if player_weapon['type'] == 'gun' and player_animation['state'] == 'shoot' and not player_weapon['shoot_animation_done']:
        player_animation['frame_delay'] += 1
        
        if player_animation['frame_delay'] >= player_animation['animation_speed']:
            player_animation['frame_delay'] = 0
            player_animation['current_frame'] += 1
            
            # Check if animation finished
            if player_animation['current_frame'] >= FRAME_COUNTS['shoot']:
                # Stop at last frame
                player_animation['current_frame'] = FRAME_COUNTS['shoot'] - 1
                player_weapon['shoot_animation_done'] = True
    
    # Update bullets
    update_bullets()
    
    # Handle katana attack
    if player_weapon['type'] == 'katana' and player_weapon['attacking']:
        # Continue attack animation
        player_animation['frame_delay'] += 1
        
        if player_animation['frame_delay'] >= player_animation['animation_speed']:
            player_animation['frame_delay'] = 0
            player_animation['current_frame'] += 1
            
            # Attack animation finished
            if player_animation['current_frame'] >= FRAME_COUNTS['slash_katana']:
                player_weapon['attacking'] = False
                player_animation['current_frame'] = 0
    else:
        # Normal movement (only when not attacking)
        moving = False
        dx, dy = 0, 0
        
        # Check if SHIFT is pressed for running
        is_running = keyboard.lshift or keyboard.rshift
        current_speed = player_run_speed if is_running else player_walk_speed
        
        if keyboard.up:
            dy = -current_speed
            player_animation['direction'] = 'up'
            moving = True
        if keyboard.down:
            dy = current_speed
            player_animation['direction'] = 'down'
            moving = True
        if keyboard.left:
            dx = -current_speed
            player_animation['direction'] = 'left'
            moving = True
        if keyboard.right:
            dx = current_speed
            player_animation['direction'] = 'right'
            moving = True
        
        # Determine animation state
        if moving:
            # When moving, use normal walk/run (NOT shoot animation)
            if is_running:
                update_player_animation('run', player_animation['direction'])
            else:
                # Use walk_katana if katana equipped, otherwise normal walk
                if player_weapon['type'] == 'katana':
                    update_player_animation('walk_katana', player_animation['direction'])
                else:
                    update_player_animation('walk', player_animation['direction'])
            
            # If gun was equipped, reset shoot animation flag so it plays again when idle
            if player_weapon['type'] == 'gun':
                player_weapon['shoot_animation_done'] = False
        else:
            # Standing still (idle)
            if player_weapon['type'] == 'gun':
                # Play shoot animation once, then stay at last frame
                if not player_weapon['shoot_animation_done']:
                    player_animation['state'] = 'shoot'
                    # Animation will be handled by the shoot animation handler above
            else:
                update_player_animation('idle', player_animation['direction'])

        # Apply movement
        if moving:
            new_x = player.x + dx
            new_y = player.y + dy

            # Check car collision AND NPC collision BEFORE moving
            if not check_player_car_collision(new_x, new_y) and not check_npc_player_collision(new_x, new_y):
                if 0 < new_x < MAP_WIDTH:
                    player.x = new_x
                if 0 < new_y < MAP_HEIGHT:
                    player.y = new_y



def on_mouse_down(pos, button):
    """Handle mouse clicks"""
    # Don't shoot if dead
    if not game_state['alive']:
        return
    
    if button == mouse.LEFT:
        if player_weapon['type'] == 'katana' and not player_weapon['attacking']:
            # Start katana attack
            player_weapon['attacking'] = True
            player_animation['state'] = 'slash_katana'
            player_animation['current_frame'] = 0
            player_animation['frame_delay'] = 0
        
        elif player_weapon['type'] == 'gun':
            # Shoot bullet
            spawn_bullet()
            # Reset shoot animation to play again
            player_weapon['shoot_animation_done'] = False
            player_animation['state'] = 'shoot'
            player_animation['current_frame'] = 0
            player_animation['frame_delay'] = 0


pgzrun.go()