from turtle import position
from ursina import *
from myFPC import MyFirstPersonController,Hand
from cube import Cube
from otherplayer import OtherPlayer
from network import GameClient, Event, PlayerMovementEvent, CubeCreationEvent, CubeDestroyEvent, PlayerJoinEvent, PlayerLeaveEvent
from threading import Thread

class MyMCGame:
    def __init__(self):
        self.game_client: GameClient = None
        self.cubes_dict = {}
        self.players_dict = {}

    def init_network(self):
        self.game_client = GameClient("127.0.0.1", 12345)
        self.game_client.run()
        print("Registering player...")
        game_info = self.game_client.register_player() # 注册玩家,下载地图信息（方块和其他玩家）
        player_id, player_position, player_rotation, self.cubes_dict, self.players_dict = game_info
        print(f"Player ID: {player_id}")
        print(f"Player Position: {player_position}")
        print(f"Player Rotation: {player_rotation}")
        print(f"Cubes data: got {len(self.cubes_dict)} cubes")
        print(f"Players List: {self.players_dict}")
        return player_position, player_rotation

    def handle_network_event(self):
        while True:
            new_event = self.game_client.recv_event_queue.get()
            print("recv the event: ", new_event)
            assert new_event.type in ["PlayerMovement", "CubeCreation", "CubeDestroy", "PlayerJoin", "PlayerLeave"]
            if new_event.type == "PlayerMovement":
                self.handle_player_movement(new_event)
            elif new_event.type == "CubeCreation":
                self.handle_cube_creation(new_event)
            elif new_event.type == "CubeDestroy":
                self.handle_cube_destroy(new_event)
            elif new_event.type == "PlayerJoin":
                self.handle_player_join(new_event)
            elif new_event.type == "PlayerLeave":
                self.handle_player_leave(new_event)

    def handle_player_movement(self, event: PlayerMovementEvent):
        player_id = event.player_id
        player_position = event.player_position
        player_rotation = event.player_rotation
        print(f"Player {player_id} moved to {player_position} with rotation {player_rotation}")
        if player_id in self.players_dict:
            other_player = self.players_dict[player_id]["player_object"]
            other_player.position = player_position
            other_player.rotation = player_rotation
            self.players_dict[player_id]["player_position"] = player_position
            self.players_dict[player_id]["player_rotation"] = player_rotation
        else:
            print(self.players_dict)
            print(f"Player {player_id} not found in players_dict")
            exit()

    def handle_cube_creation(self, event: CubeCreationEvent):
        cube_id = event.cube_id
        cube_position = event.cube_position
        cube_type = event.cube_type
        print(f"Cube {cube_id} created at {cube_position} with type {cube_type}")
        new_cube = Cube(
            self.game_client, 
            self.cubes_dict, 
            cube_id=cube_id, 
            cube_position=cube_position, 
            cube_type=cube_type
            )
        self.cubes_dict[cube_id] = {
            "cube_id": cube_id,
            "cube_position": cube_position,
            "cube_type": cube_type,
            "cube_object": new_cube,
        }

    def handle_cube_destroy(self, event: CubeDestroyEvent):
        cube_id = event.cube_id
        assert cube_id in self.cubes_dict
        print(f"Cube {cube_id} destroyed")
        destroy(self.cubes_dict[cube_id]["cube_object"])
        del self.cubes_dict[cube_id]

    def handle_player_join(self, event: PlayerJoinEvent):
        player_id=event.player_id
        player_position = event.player_position
        player_rotation = event.player_rotation
        print(f"Player {player_id} joined the game")
        other_player = OtherPlayer(player_position, player_rotation)
        self.players_dict[player_id] = {
            "player_id": player_id,
            "player_position": player_position,
            "player_rotation": player_rotation,
            "player_object": other_player,
        }

    def handle_player_leave(self, event: PlayerLeaveEvent):
        player_id = event.player_id
        print(f"Player {player_id} left the game")
        assert player_id in self.players_dict
        destroy(self.players_dict[player_id]["player_object"])
        del self.players_dict[player_id]

    def run_game_logic(self):
        player_position, player_rotation = self.init_network()

        app = Ursina()

        player = MyFirstPersonController(self.game_client, position=Vec3(player_position), rotation=Vec3(player_rotation))
        sky = Sky(texture='sky_sunset')


        # 构建地图
        for cube_id in self.cubes_dict:
            cube_info = self.cubes_dict[cube_id]
            cube_position = cube_info["cube_position"]
            cube_type = cube_info["cube_type"]
            new_cube = Cube(
                self.game_client, 
                self.cubes_dict, 
                cube_id=cube_id, 
                cube_position=cube_position, 
                cube_type=cube_type
                )
            cube_info["cube_object"] = new_cube
        

        for player_id in self.players_dict:
            player_info = self.players_dict[player_id]
            player_position = Vec3(player_info["player_position"])
            player_rotation = Vec3(player_info["player_rotation"])
            other_player = OtherPlayer(player_position, player_rotation)
            player_info["player_object"] = other_player

        event_recv_thread = Thread(target=self.handle_network_event)
        event_recv_thread.start()


        app.run()


if __name__ == "__main__":
    mc_game = MyMCGame()
    mc_game.run_game_logic()
