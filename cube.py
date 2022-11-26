from ursina import *
from network.constants import CUBE_TYPE_GRASS, CUBE_TYPE_DIRT, CUBE_TYPE_BRICK, CUBE_TYPE_STONE
from network import GameClient
import random
from typing import Dict
import uuid

# textures = {
#     "grass": load_texture("assets/textures/grass_block.png"),
#     "dirt": load_texture("assets/textures/dirt_block.png"),
#     "stone": load_texture("assets/textures/stone_block.png"),
#     "brick": load_texture("assets/textures/brick_block.png"),
# }
cube_id_to_cube_ins_map: Dict[int, Cube] = {}

class Cube(Entity):
    def __init__(self, game_client, cubes_dict: Dict, cube_id: int, cube_position, cube_type=CUBE_TYPE_GRASS, **kwargs):
        texure_type = ["grass", "stone", "brick", "dirt"][cube_type-1]
        texture = load_texture(f"assets/textures/{texure_type}_block.png")
        super().__init__(
            parent=scene,
            model="assets/models/block",
            texture=texture,
            color=color.color(0, 0, random.uniform(0.9, 1)),
            position=cube_position,
            scale=0.5,
            collider='box',
            **kwargs
            )
        self.cube_id = cube_id
        self.cube_position = cube_position
        self.cube_type = cube_type
        self.game_client: GameClient = game_client
        self.cubes_dict: Dict = cubes_dict
            

    def input(self, key):
        if self.hovered:
            if key == 'left mouse down':
                new_cube_position = self.position + mouse.normal
                if not new_cube_position in [e.position for e in scene.entities]:
                    new_cube_id=uuid.uuid4().int
                    new_cube = Cube(
                        self.game_client, 
                        self.cubes_dict, 
                        cube_id=new_cube_id, 
                        cube_position=new_cube_position, 
                        cube_type=self.cube_type
                    )
                    self.cubes_dict[new_cube_id] = {
                        "cube_id": new_cube_id,
                        "cube_position": new_cube_position,
                        "cube_type": self.cube_type,
                        "cube_object": new_cube,
                    }
                    self.game_client.cube_creation(
                        cube_id=new_cube_id,
                        cube_position=new_cube_position,
                        cube_type=self.cube_type
                    )
            if key == 'right mouse down':
                self.game_client.cube_destroy(self.cube_id)
                # TODO: 这里可能会有问题，消息还没完全发出去，就已经self.destroy()了
                destroy(self)
                