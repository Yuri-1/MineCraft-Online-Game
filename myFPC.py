# from re import L

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from network import GameClient
import os


class MyFirstPersonController(FirstPersonController):
    def __init__(self, game_client, **kwargs):
        super().__init__(**kwargs)
        # print(self.position)
        if "position" in kwargs:
            self.position = kwargs["position"]
        if "rotation" in kwargs:
            self.rotation = kwargs["rotation"]
        self.game_client: GameClient = game_client

        self.broadcast_movement_counter = 0
        self.previous_position = self.position
        self.previous_rotation = self.rotation

        self.punch_sound = Audio('assets/punch_sound',loop = False, autoplay = False)

        self.hand = Hand()

    def broadcast_movement(self):
        BROADCAST_INTERVAL = 5
        if self.broadcast_movement_counter >= BROADCAST_INTERVAL:
            self.broadcast_movement_counter = 0
            if self.position != self.previous_position or self.rotation != self.previous_rotation:
                self.game_client.player_movement(self.position, self.rotation)
                self.previous_position = self.position
                self.previous_rotation = self.rotation
                print("update my new position", self.position, self.rotation)
        else:
            self.broadcast_movement_counter += 1


    def update(self):
        self.broadcast_movement()
        if self.world_y<-100:
            self.game_client.stop()
            application.quit()
            os._exit(0)

        # if held_keys['q']:
            # os._exit()

        # mouse.locked = False
        # mouse.visible = True

        window.exit_button.visible = True

        # 第一视角手臂动作
        if held_keys['left mouse'] or held_keys['right mouse']:
            self.hand.active()
            self.punch_sound.play()

        else:
            self.hand.passive()

        self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity[1]

        self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity[0]
        self.camera_pivot.rotation_x= clamp(self.camera_pivot.rotation_x, -90, 90)

        self.direction = Vec3(
            self.forward * (held_keys['w'] - held_keys['s'])
            + self.right * (held_keys['d'] - held_keys['a'])
            ).normalized()

        feet_ray = raycast(self.position+Vec3(0,0.5,0), self.direction, ignore=(self,), distance=.5, debug=False)
        head_ray = raycast(self.position+Vec3(0,self.height-.1,0), self.direction, ignore=(self,), distance=.5, debug=False)
        if not feet_ray.hit and not head_ray.hit:
            move_amount = self.direction * time.dt * self.speed

            if raycast(self.position+Vec3(-.0,1,0), Vec3(1,0,0), distance=.5, ignore=(self,)).hit:
                move_amount[0] = min(move_amount[0], 0)
            if raycast(self.position+Vec3(-.0,1,0), Vec3(-1,0,0), distance=.5, ignore=(self,)).hit:
                move_amount[0] = max(move_amount[0], 0)
            if raycast(self.position+Vec3(-.0,1,0), Vec3(0,0,1), distance=.5, ignore=(self,)).hit:
                move_amount[2] = min(move_amount[2], 0)
            if raycast(self.position+Vec3(-.0,1,0), Vec3(0,0,-1), distance=.5, ignore=(self,)).hit:
                move_amount[2] = max(move_amount[2], 0)
            self.position += move_amount

            # self.position += self.direction * self.speed * time.dt


        if self.gravity:
            # gravity
            ray = raycast(self.world_position+(0,self.height,0), self.down, ignore=(self,))
            # ray = boxcast(self.world_position+(0,2,0), self.down, ignore=(self,))

            if ray.distance <= self.height+.1:
                if not self.grounded:
                    self.land()
                self.grounded = True
                # make sure it's not a wall and that the point is not too far up
                if ray.world_normal.y > .7 and ray.world_point.y - self.world_y < .5: # walk up slope
                    self.y = ray.world_point[1]
                return
            else:
                self.grounded = False

            # if not on ground and not on way up in jump, fall
            self.y -= min(self.air_time, ray.distance-.05) * time.dt * 100
            self.air_time += time.dt * .25 * self.gravity
    def check_rebirth(self):
        """Check if the player is dead and rebirth if so"""
        if self.world_y < -100:
            # set world position to the spawn point
            self.world_position = (0, 10, 0)
            # set rotation to the spawn rotation
            self.rotation = (0, 0, 0)
            # reset air time
            self.air_time = 0
    def input(self, key):
        if key == 'space':
            self.jump()
        if key=='escape':
            self.game_client.stop()
            application.quit()
            os._exit(0)


class Hand(Entity):
    def __init__(self):
        super().__init__(
            parent = camera.ui,
            model = 'assets/arm',
            texture = load_texture('assets/arm_texture.png'),
            scale = 0.2,
            rotation = Vec3(150,-10,0),
            position = Vec2(0.4,-0.6)
            )

    def check_rebirth(self):
        """Check if the player is dead and rebirth if so"""
        if self.world_y < -100:
            # set world position to the spawn point
            self.world_position = (0, 10, 0)
            # set rotation to the spawn rotation
            self.rotation = (0, 0, 0)
            # reset air time
            self.air_time = 0


    def active(self):
        self.position = Vec2(0.3,-0.5)

    def passive(self):
        self.position = Vec2(0.4,-0.6)

# class FirstPersonController(Entity):
#     def __init__(self, **kwargs):
#         self.cursor = Entity(parent=camera.ui, model='quad', color=color.pink, scale=.008, rotation_z=45)
#         super().__init__()
#         self.speed = 5
#         self.height = 2
#         self.camera_pivot = Entity(parent=self, y=self.height)

#         camera.parent = self.camera_pivot
#         camera.position = (0,0,0)
#         camera.rotation = (0,0,0)
#         camera.fov = 90
#         mouse.locked = True
#         self.mouse_sensitivity = Vec2(40, 40)

#         self.gravity = 1
#         self.grounded = False
#         self.jump_height = 2
#         self.jump_up_duration = .5
#         self.fall_after = .35 # will interrupt jump up
#         self.jumping = False
#         self.air_time = 0

#         for key, value in kwargs.items():
#             setattr(self, key ,value)

#         # make sure we don't fall through the ground if we start inside it
#         if self.gravity:
#             ray = raycast(self.world_position+(0,self.height,0), self.down, ignore=(self,))
#             if ray.hit:
#                 self.y = ray.world_point.y


#     def update(self):
#         self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity[1]

#         self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity[0]
#         self.camera_pivot.rotation_x= clamp(self.camera_pivot.rotation_x, -90, 90)

#         self.direction = Vec3(
#             self.forward * (held_keys['w'] - held_keys['s'])
#             + self.right * (held_keys['d'] - held_keys['a'])
#             ).normalized()

#         feet_ray = raycast(self.position+Vec3(0,0.5,0), self.direction, ignore=(self,), distance=.5, debug=False)
#         head_ray = raycast(self.position+Vec3(0,self.height-.1,0), self.direction, ignore=(self,), distance=.5, debug=False)
#         if not feet_ray.hit and not head_ray.hit:
#             move_amount = self.direction * time.dt * self.speed

#             if raycast(self.position+Vec3(-.0,1,0), Vec3(1,0,0), distance=.5, ignore=(self,)).hit:
#                 move_amount[0] = min(move_amount[0], 0)
#             if raycast(self.position+Vec3(-.0,1,0), Vec3(-1,0,0), distance=.5, ignore=(self,)).hit:
#                 move_amount[0] = max(move_amount[0], 0)
#             if raycast(self.position+Vec3(-.0,1,0), Vec3(0,0,1), distance=.5, ignore=(self,)).hit:
#                 move_amount[2] = min(move_amount[2], 0)
#             if raycast(self.position+Vec3(-.0,1,0), Vec3(0,0,-1), distance=.5, ignore=(self,)).hit:
#                 move_amount[2] = max(move_amount[2], 0)
#             self.position += move_amount

#             # self.position += self.direction * self.speed * time.dt


#         if self.gravity:
#             # gravity
#             ray = raycast(self.world_position+(0,self.height,0), self.down, ignore=(self,))
#             # ray = boxcast(self.world_position+(0,2,0), self.down, ignore=(self,))

#             if ray.distance <= self.height+.1:
#                 if not self.grounded:
#                     self.land()
#                 self.grounded = True
#                 # make sure it's not a wall and that the point is not too far up
#                 if ray.world_normal.y > .7 and ray.world_point.y - self.world_y < .5: # walk up slope
#                     self.y = ray.world_point[1]
#                 return
#             else:
#                 self.grounded = False

#             # if not on ground and not on way up in jump, fall
#             self.y -= min(self.air_time, ray.distance-.05) * time.dt * 100
#             self.air_time += time.dt * .25 * self.gravity


#     def input(self, key):
#         if key == 'space':
#             self.jump()


#     def jump(self):
#         if not self.grounded:
#             return

#         self.grounded = False
#         self.animate_y(self.y+self.jump_height, self.jump_up_duration, resolution=int(1//time.dt), curve=curve.out_expo)
#         invoke(self.start_fall, delay=self.fall_after)


#     def start_fall(self):
#         self.y_animator.pause()
#         self.jumping = False

#     def land(self):
#         # print('land')
#         self.air_time = 0
#         self.grounded = True


#     def on_enable(self):
#         mouse.locked = True
#         self.cursor.enabled = True


#     def on_disable(self):
#         mouse.locked = False
#         self.cursor.enabled = False
