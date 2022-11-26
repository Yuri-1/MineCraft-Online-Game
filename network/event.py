from typing import Dict, List, Tuple, Union

class Event:
    def __init__(self, type: str):
        self.type = type
    
    def __repr__(self) -> str:
        return f"<{self.type} event>"

class PlayerMovementEvent(Event):
    def __init__(self, player_id: int, player_position: Tuple[float, float, float], player_rotation: Tuple[float, float, float]):
        super().__init__("PlayerMovement")
        self.player_id: int = player_id
        self.player_position: Tuple[float, float, float] = player_position
        self.player_rotation: Tuple[float, float, float] = player_rotation

    def __repr__(self) -> str:
        return f"<{self.type} event: pid={self.player_id}, pos={self.player_position}, rot={self.player_rotation}>"

class CubeCreationEvent(Event):
    def __init__(self, cube_id: int, cube_position: Tuple[float, float, float], cube_type: int):
        super().__init__("CubeCreation")
        self.cube_id: int = cube_id
        self.cube_position: Tuple[float, float, float] = cube_position
        self.cube_type: int = cube_type
        assert cube_type in [1,2,3,4]

    def __repr__(self) -> str:
        return f"<{self.type} event: cid={self.cube_id}, type={self.cube_type}, pos={self.cube_position}>"

class CubeDestroyEvent(Event):
    def __init__(self, cube_id: int):
        super().__init__("CubeDestroy")
        self.cube_id: int = cube_id

    def __repr__(self) -> str:
        return f"<{self.type} event: cid={self.cube_id}>"

class PlayerJoinEvent(Event):
    def __init__(self, player_id: int, player_position: Tuple[float, float, float], player_rotation: Tuple[float, float, float]):
        super().__init__("PlayerJoin")
        self.player_id: int = player_id
        self.player_position: Tuple[float, float, float] = player_position
        self.player_rotation: Tuple[float, float, float] = player_rotation

    def __repr__(self) -> str:
        return f"<{self.type} event: pid={self.player_id}, pos={self.player_position}, rot={self.player_rotation}>"

class PlayerLeaveEvent(Event):
    def __init__(self, player_id: int):
        super().__init__("PlayerLeave")
        self.player_id: int = player_id

    def __repr__(self) -> str:
        return f"<{self.type} event: pid={self.player_id}>"

# class MapDownloadRequestEvent(Event):
#     def __init__(self):
#         super().__init__("MapDownloadrequest")

#     def __repr__(self) -> str:
#         return f"<{self.type} event>"

# class MapDownloadResponseEvent(Event):
#     def __init__(self, map_cubes: List[Tuple[int, Tuple[float, float, float], int]], map_players: List[Tuple[int, Tuple[float, float, float]]]):
#         super().__init__("MapDownloadResponse")
#         self.map_cube_list: List[Tuple[int, Tuple[float, float, float], int]] = map_cubes
#         self.map_player_list: List[Tuple[int, Tuple[float, float, float]]] = map_players

#     def __repr__(self) -> str:
#         return f"<{self.type} event: {len(self.map_cube_list)} cubes, {len(self.map_player_list)} players>"

class PlayerRegisterRequestEvent(Event):
    def __init__(self):
        super().__init__("PlayerRegisterRequest")

    def __repr__(self) -> str:
        return f"<{self.type} event>"

# class PlayerRegisterResponseEvent(Event):
#     def __init__(self, player_id: int, player_position: Tuple[float, float, float], map_cubes: List[Tuple[int, Tuple[float, float, float], int]], map_players: List[Tuple[int, Tuple[float, float, float]]]):
#         super().__init__("PlayerRegisterResponse")
#         self.player_id: int = player_id
#         self.player_position: Tuple[float, float, float] = player_position
#         self.map_cube_list: List[Tuple[int, Tuple[float, float, float], int]] = map_cubes
#         self.map_player_list: List[Tuple[int, Tuple[float, float, float]]] = map_players

#     def __repr__(self) -> str:
#         return f"<{self.type} event: {self.player_id},{self.player_position}; {len(self.map_cube_list)} cubes, {len(self.map_player_list)} players>"

class PlayerRegisterResponseEvent(Event):
    def __init__(self, player_id: int, player_position: Tuple[float, float, float], player_rotation: Tuple[float, float, float], map_cubes: Dict[int, Dict[str, Union[Tuple[float, float, float], int]]], map_players: Dict[int, Dict[str, Union[Tuple[float, float, float], int]]]):
        super().__init__("PlayerRegisterResponse")
        self.player_id: int = player_id
        self.player_position: Tuple[float, float, float] = player_position
        self.player_rotation: Tuple[float, float, float] = player_rotation
        self.map_cubes: Dict[int, Dict[str, Union[Tuple[float, float, float], int]]] = map_cubes
        self.map_players: Dict[int, Dict[str, Union[Tuple[float, float, float], int]]] = map_players


    def __repr__(self) -> str:
        return f"<{self.type} event: pid={self.player_id}, pos={self.player_position}, rot={self.player_rotation}; {len(self.map_cubes)} cubes, {len(self.map_players)} players>"
