from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
from perlin_noise import PerlinNoise 

# --- App Setup ---
app = Ursina()

# --- Global Settings ---
window.title = 'Mine Crack'
window.borderless = False
window.fullscreen = False
window.exit_button.visible = True
window.fps_counter.enabled = True

# --- Mob Class ---
class Mob(Entity):
    """
    Representa una criatura simple que se mueve aleatoriamente.
    """
    def __init__(self, position):
        super().__init__(
            parent=scene,
            position=position,
            model='sphere',
            color=color.red, # Mob rojo para ser visible
            collider='box',
            scale=0.5,
            origin_y=-0.5
        )
        self.speed = 0.5
        self.move_timer = 0
        self.target_position = self.position
        
        # Ajustar el collider para que el raycast de gravedad funcione mejor
        self.collider = BoxCollider(self, center=(0, 0, 0), size=(1, 1, 1))

    def update(self):
        # Lógica de movimiento simple (cambia de dirección cada 2-5 segundos)
        self.move_timer -= time.dt
        
        if self.move_timer <= 0:
            # Elegir una nueva posición aleatoria cercana
            move_range = 5
            self.target_position = self.position + Vec3(
                random.uniform(-move_range, move_range), 
                0, 
                random.uniform(-move_range, random.uniform(-move_range, move_range))
            )
            self.target_position.y = self.position.y # Mantener la altura horizontalmente
            self.move_timer = random.uniform(2, 5)

        # Moverse hacia el objetivo
        self.position = lerp(self.position, self.target_position, time.dt * self.speed)

        # Gravedad: Simplemente cae si no hay suelo debajo
        if not self.on_ground():
            self.y -= 2 * time.dt # Caída suave
            
    def on_ground(self):
        # Raycast hacia abajo para verificar si hay un bloque (Voxel) debajo
        hit_info = raycast(self.world_position + Vec3(0, 0.1, 0), 
                           direction=Vec3(0, -1, 0), 
                           distance=0.6, 
                           ignore=[self, player])
        return hit_info.hit and isinstance(hit_info.entity, Voxel)

# --- Spawner Class ---
class Spawner(Entity):
    """
    Un bloque especial que genera un Mob periódicamente.
    """
    def __init__(self, position, spawn_interval=5):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            texture='grass', 
            color=color.magenta, # FIX: Usando magenta en lugar de purple
            collider='box'
        )
        self.spawn_interval = spawn_interval
        self.spawn_timer = 0
        print_on_screen(f"Spawner placed at {position}", position=(-.4, -.5), duration=3)


    def update(self):
        self.spawn_timer += time.dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_mob()
            self.spawn_timer = 0 # Reiniciar temporizador

    def spawn_mob(self):
        # Generar el Mob ligeramente por encima del Spawner
        Mob(position=self.position + Vec3(0, 1.5, 0))
        print_on_screen("Mob Spawned!", position=(-.4, -.4), duration=1)

# --- Block Definitions ---
# Dictionary to hold block properties: texture and color
block_types = {
    1: {'texture': 'grass', 'color': color.white},
    2: {'texture': 'brick', 'color': color.light_gray}, # Stone (Brick)
    3: {'texture': 'shore', 'color': color.brown},      # Dirt (Shore)
    4: {'texture': 'grass', 'color': color.red},   # Spawner
}

# Default starting block
current_block_type = 1
hand = Entity(parent=camera.ui, model='cube', texture=block_types[current_block_type]['texture'],
              scale=0.15, position=Vec2(0.6, -0.4), rotation=Vec3(0, 45, -10))

# --- Voxel Class ---
class Voxel(Button):
    def __init__(self, position=(0, 0, 0), block_id=1):
        self.block_id = block_id
        properties = block_types.get(block_id, block_types[1]) 

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

# --- Terrain Generation (Perlin Noise) ---
chunk_size = 32
frequency = 0.05
amplitude = 5

noise_generator = PerlinNoise(octaves=4, seed=random.randint(1, 10000))

for z in range(chunk_size):
    for x in range(chunk_size):
        y_raw = noise_generator([x * frequency, z * frequency])
        y = floor(y_raw * amplitude)

        # Place the top grass block
        Voxel(position=(x, y, z), block_id=1)

        # Fill the blocks underneath with dirt/stone
        for depth in range(1, 4):
            if y - depth >= 0:
                block_to_place = 3 if depth == 1 else 2
                Voxel(position=(x, y - depth, z), block_id=block_to_place)

# --- Player and Environment Setup ---
player = FirstPersonController()
player.x = chunk_size / 2
player.z = chunk_size / 2
player.y = 10 

Sky() 

# --- Input Handling for Building and Selection ---

def input(key):
    global current_block_type

    # Block Placement/Destruction
    if mouse.hovered_entity:
        if isinstance(mouse.hovered_entity, (Voxel, Spawner)): # El Spawner también se puede destruir
            # Right mouse button: Destroy block
            if key == 'right mouse down':
                destroy(mouse.hovered_entity)

            # Left mouse button: Place block
            if key == 'left mouse down':
                new_position = mouse.hovered_entity.position + mouse.normal
                
                # Lógica especial para colocar el Spawner
                if current_block_type == 4:
                    Spawner(position=new_position) 
                else:
                    # Colocar un Voxel regular
                    Voxel(position=new_position, block_id=current_block_type)
                    
                # Update hand texture briefly for visual feedback
                hand.texture = block_types[current_block_type]['texture']


    # Block Selection (Keys 1, 2, 3, 4)
    if key == '1':
        current_block_type = 1
        hand.texture = block_types[current_block_type]['texture']
        print_on_screen("Block Selected: Grass", position=(-.4, .4), duration=1)
    if key == '2':
        current_block_type = 2
        hand.texture = block_types[current_block_type]['texture']
        print_on_screen("Block Selected: Stone (Brick)", position=(-.4, .4), duration=1)
    if key == '3':
        current_block_type = 3
        hand.texture = block_types[current_block_type]['texture']
        print_on_screen("Block Selected: Dirt (Shore)", position=(-.4, .4), duration=1)
    if key == '4':
        current_block_type = 4
        hand.texture = block_types[current_block_type]['texture']
        print_on_screen("Block Selected: Spawner (grass)", position=(-.4, .4), duration=1)

# Start the application
app.run()