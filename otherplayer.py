from ursina import *

class OtherPlayer(Entity):
    def __init__(self, position, rotation, **kwargs):
        super().__init__(
            parent=scene,
            model="assets/models/block",
            texture="assets/textures/dirt_block_face.png",
            # color=color.red,
            position=position,
            rotation=rotation,
            scale=0.3,
            origin_y=-2,
            **kwargs
            )
        # self.scale_y = 0.3

    # def update(self):
    #     self.position += Vec3(0, 0, 0.1)