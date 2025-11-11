from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
# FIX: Using PerlinNoise class correctly for the external library
from perlin_noise import PerlinNoise # Correct class import

# --- App Setup ---
app = Ursina()

# --- Global Settings ---
window.title = 'Voxel Builder - Mejorado'
window.borderless = False
window.fullscreen = False
window.exit_button.visible = False
window.fps_counter.enabled = True

# --- Block Definitions ---
# Dictionary to hold block properties: texture and color
block_types = {
    1: {'texture': 'grass', 'color': color.white},
    2: {'texture': 'stone', 'color': color.light_gray},
    3: {'texture': 'dirt', 'color': color.brown},
}

# Default starting block
current_block_type = 1
hand = Entity(parent=camera.ui, model='cube', texture=block_types[current_block_type]['texture'],
              scale=0.15, position=Vec2(0.6, -0.4), rotation=Vec3(0, 45, -10))

# --- Voxel Class ---
class Voxel(Button):
    def __init__(self, position=(0, 0, 0), block_id=1):
        self.block_id = block_id
        properties = block_types.get(block_id, block_types[1]) # Default to grass if ID is missing

        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture=properties['texture'],
            color=properties['color'],
            highlight_color=color.lime,
            tooltip=Tooltip(f"Block ID: {block_id}")
        )

    # Note: Input is now handled globally in the main input() function for block selection consistency.

# --- Terrain Generation (Perlin Noise) ---
chunk_size = 32
frequency = 0.05
amplitude = 5

# Initialize Perlin Noise generator instance
# octaves=4 gives reasonable detail. A random seed ensures different worlds each time.
noise_generator = PerlinNoise(octaves=4, seed=random.randint(1, 10000))

for z in range(chunk_size):
    for x in range(chunk_size):
        # Generate height using Perlin Noise by calling the generator instance
        # The generator takes a list/tuple of coordinates [x, z] scaled by the frequency
        y_raw = noise_generator([x * frequency, z * frequency])
        y = floor(y_raw * amplitude)

        # Place the top grass block
        Voxel(position=(x, y, z), block_id=1)

        # Fill the blocks underneath with dirt/stone
        for depth in range(1, 4):
            if y - depth >= 0:
                # Place dirt immediately below grass, then stone
                block_to_place = 3 if depth == 1 else 2
                Voxel(position=(x, y - depth, z), block_id=block_to_place)

# --- Player and Environment Setup ---
player = FirstPersonController()
# Center the player on the map
player.x = chunk_size / 2
player.z = chunk_size / 2
player.y = 10 # Start high enough to avoid falling through

Sky() # Adds a nice sky box

# --- Input Handling for Building and Selection ---

def input(key):
    global current_block_type

    # Block Placement/Destruction
    if mouse.hovered_entity:
        if isinstance(mouse.hovered_entity, Voxel):
            # Right mouse button: Destroy block
            if key == 'right mouse down':
                destroy(mouse.hovered_entity)

            # Left mouse button: Place block
            if key == 'left mouse down':
                new_position = mouse.hovered_entity.position + mouse.normal
                Voxel(position=new_position, block_id=current_block_type)
                # Update hand texture briefly for visual feedback
                hand.texture = block_types[current_block_type]['texture']


    # Block Selection (Keys 1, 2, 3)
    if key == '1':
        current_block_type = 1
        hand.texture = block_types[current_block_type]['texture']
        print_on_screen("Block Selected: Grass", position=(-.4, .4), duration=1)
    if key == '2':
        current_block_type = 2
        hand.texture = block_types[current_block_type]['texture']
        print_on_screen("Block Selected: Stone", position=(-.4, .4), duration=1)
    if key == '3':
        current_block_type = 3
        hand.texture = block_types[current_block_type]['texture']
        print_on_screen("Block Selected: Dirt", position=(-.4, .4), duration=1)

# Start the application
app.run()