# 存储地图信息，存储当前玩家列表

# 提供注册功能，当新玩家注册时，为其分配id和位置，将其加入玩家列表，
# 将其id和位置以及地图方块信息和玩家列表发送给新玩家，向所有玩家广播新玩家加入事件

# 提供广播功能，当玩家移动时，将其位置信息广播给所有玩家
# 当玩家创建方块时，将其方块信息广播给所有玩家，更新服务器地图信息
# 当玩家摧毁方块时，将其方块信息广播给所有玩家，更新服务器地图信息
# 当玩家断开连接时，将其id广播给所有玩家，从服务器玩家列表中删除



import socket
import threading
import queue
from typing import List, Tuple, Any, Dict, Union
from .event import *
from .serialize import *
from .constants import *
from rich import print
import json
import time
import random

class GameServer:
    def __init__(self, host:str, port: int):
        self.host = host
        self.port = port
        self.server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(128)

        # 服务器存储的地图信息（方块和玩家）
        self.cubes: Dict[int, Dict[str, Union[Tuple[float, float, float], int]]] = {}
        self.players: Dict[int, Dict[str, Union[Tuple[float, float, float], int]]] = {}

        # 加载默认地图
        self.cubes = self.load_default_map()

        # 玩家id分配器
        self.player_id_counter = 0

        # 玩家ID到客户端信息的映射
        self.player_id_to_client_info: Dict[int, Dict[str, Any]] = {}
        # thread lock for player_id_to_client_info
        self.player_id_to_client_info_lock = threading.Lock()  # 互斥信号量

    def load_default_map(path="default_map.json") -> Dict[int, Dict[str, Union[Tuple[float, float, float], int]]]:
        map_dict = {}
        for x in range(20):
            for z in range(15):
                cube_id = int(f"1{x}{z}{time.time_ns()}{random.randint(0, 1000)}")
                map_dict[cube_id] = {
                    "cube_id": cube_id,
                    "cube_position": (x, 0, z),
                    "cube_type": CUBE_TYPE_GRASS if x<10 else CUBE_TYPE_STONE,
                }
        server_log(f"Loaded default map [{len(map_dict)} blocks]", title="[yellow]Main thread[/yellow]")
        return map_dict

    def run(self):  
        '''循环等待客户端连接'''
        server_log(f"Server started on {self.host}:{self.port}", title="[yellow]Main thread[/yellow]")
        while True:
            server_log("Waiting for new client", title="[yellow]Main thread[/yellow]")
            client_socket, client_addr = self.server_socket.accept()
            server_log(f"Client connected: {client_addr[0]}:{client_addr[1]}", title="[yellow]Main thread[/yellow]")
            client_info = {
                'socket': client_socket,
                'recv_buffer': b'',
                'event_to_send_queue': queue.Queue(),
                'recv_thread': None,
                'send_thread': None,
                'running': False,
                'player_id': None,
            }
            self.start_client_threads(client_info)

    def start_client_threads(self, client_info: dict):
        """为新客户端启动接收和发送线程"""
        client_info['running'] = True
        client_info['recv_thread'] = threading.Thread(target=self.client_recv_thread, args=(client_info,))
        client_info['recv_thread'].start()
        client_info['send_thread'] = threading.Thread(target=self.client_send_thread, args=(client_info,))
        client_info['send_thread'].start()
        server_log("Threads for new client started", title="[yellow]Main thread[/yellow]")

    def client_send_thread(self, client_info: dict):   
        """为客户端服务的发送线程"""
        while client_info['running']:
            time.sleep(0.01)
            if not client_info['event_to_send_queue'].empty():
                event_to_send = client_info['event_to_send_queue'].get()
                try:
                    self.send_event_to_client(client_info, event_to_send)
                    # print("[yellow]Client threads[/yellow]:", f"Sent event: {event_to_send}")
                    server_log(f"Sent event: {event_to_send}", player_id=client_info['player_id'])
                except Exception as e:
                    print(e)
                    client_info['running'] = False
                    break
        # print(f"Player {client_info['player_id']} send thread exit")

    def send_event_to_client(self, client_info: dict, event: Event):
        """Send event to client"""
        bytes_to_send = serialize_event(event)
        packet_length = len(bytes_to_send)
        packet_header = b'pack' + packet_length.to_bytes(4, "big")
        packet_body = bytes_to_send
        packet_bytes = packet_header + packet_body
        client_info['socket'].send(packet_bytes)

    def client_recv_thread(self, client_info: dict):
        # print("Client recv thread started")
        for event in self.iter_client_events(client_info):
            server_log(f"Received event: {event}", player_id=client_info['player_id'])
            self.handle_client_event(client_info, event)
        client_info['socket'].close()
        client_info['running'] = False
        # print(f"Player {client_info['player_id']} recv thread exit")

    def iter_client_events(self, client_info: dict):
        """Iterate events from client"""
        while client_info['running']:
            # clear recv_buffer
            client_info['recv_buffer'] = b''
            # recv header
            header_bytes_to_recv_left = 8
            while header_bytes_to_recv_left > 0:
                try:
                    recv_bytes = client_info['socket'].recv(header_bytes_to_recv_left)
                except Exception as e:
                    # print(e)
                    client_info['running'] = False
                    break

                if len(recv_bytes) == 0:
                    client_info['running'] = False
                    break
                client_info['recv_buffer'] += recv_bytes
                header_bytes_to_recv_left -= len(recv_bytes)
            if not client_info['running']:
                server_log("Client disconnected", player_id=client_info['player_id'])
                break
            # print(f"Received header: {client_info['recv_buffer']}")
            # check header
            if client_info['recv_buffer'][:4] != b'pack':
                client_info['running'] = False
                server_log("Invalid header, disconnecting", player_id=client_info['player_id'])
                break
            # print("Header check passed")
            packet_length = int.from_bytes(client_info['recv_buffer'][4:8], 'big')
            # recv body
            body_bytes_to_recv_left = packet_length
            while body_bytes_to_recv_left > 0:
                try:
                    recv_bytes = client_info['socket'].recv(body_bytes_to_recv_left)
                except Exception as e:
                    # print(e)
                    client_info['running'] = False
                    break
                if len(recv_bytes) == 0:
                    client_info['running'] = False
                    break
                client_info['recv_buffer'] += recv_bytes
                body_bytes_to_recv_left -= len(recv_bytes)
            if not client_info['running']:
                server_log("Client disconnected", player_id=client_info['player_id'])
                break
            # print(f"Received body: {client_info['recv_buffer']}")
            # check body
            if len(client_info['recv_buffer']) != 8 + packet_length:
                client_info['running'] = False
                server_log("Invalid body, disconnecting", player_id=client_info['player_id'])
                break
            # print("Body check passed")
            # print(f"Received packet: {client_info['recv_buffer']}")
            event = deserialize_event(client_info['recv_buffer'][8:])
            yield event
        # 运行到这里，客户端已经断开连接
        self.process_client_disconnect(client_info)
    
    def handle_client_event(self, client_info: dict, event: Event):
        assert event.type in ("PlayerMovement", "CubeCreation", "CubeDestroy", "PlayerRegisterRequest")
        if event.type == "PlayerMovement":
            self.handle_player_movement_event(client_info, event)
        elif event.type == "CubeCreation":
            self.handle_cube_creation_event(client_info, event)
        elif event.type == "CubeDestroy":
            self.handle_cube_destroy_event(client_info, event)
        elif event.type == "PlayerRegisterRequest":
            self.handle_player_register_request_event(client_info, event)
        else:
            raise ValueError("Unknown event type: " + event.type)
    
    def handle_player_register_request_event(self, client_info: dict, event: PlayerRegisterRequestEvent):
        assert event.type == "PlayerRegisterRequest"
        player_id = self.player_id_counter
        self.player_id_counter += 1
        player_position = (random.randint(0, 10), 0.5, random.randint(0, 10))
        player_rotation = (0, 45+180, 0)
        cubes = self.cubes.copy()
        players = self.players.copy()
        # make response event
        event_to_send = PlayerRegisterResponseEvent(player_id, player_position, player_rotation, cubes, players)
        # put event into self queue
        client_info['event_to_send_queue'].put(event_to_send)

        # map player_id to client_info
        self.player_id_to_client_info[player_id] = client_info
        # add player to self.players
        self.players[player_id] = {
            "player_id": player_id,
            "player_position": player_position,
            "player_rotation": player_rotation,
        }

        # set player_id in client_info
        client_info['player_id'] = player_id
        server_log(f"Player {player_id} registered", player_id=player_id)


        # broadcast player join event
        player_join_event = PlayerJoinEvent(player_id, player_position, player_rotation)
        self.broadcast_event_except_sender(client_info, player_join_event)
    
    def handle_player_movement_event(self, client_info: dict, event: PlayerMovementEvent):
        assert event.type == "PlayerMovement"
        player_id = event.player_id
        player_position = event.player_position
        player_rotation = event.player_rotation

        # update player position
        self.players[player_id]['player_position'] = player_position
        self.players[player_id]['player_rotation'] = player_rotation

        # broadcast player movement event
        player_movement_event = PlayerMovementEvent(player_id, player_position, player_rotation)
        self.broadcast_event_except_sender(client_info, player_movement_event)
    
    def handle_cube_creation_event(self, client_info: dict, event: CubeCreationEvent):
        assert event.type == "CubeCreation"
        cube_id = event.cube_id
        cube_position = event.cube_position
        cube_type = event.cube_type

        # add cube to self.cubes
        self.cubes[cube_id] = {
            "cube_id": cube_id,
            "cube_position": cube_position,
            "cube_type": cube_type,
        }

        # broadcast cube creation event
        cube_creation_event = CubeCreationEvent(cube_id, cube_position, cube_type)
        self.broadcast_event_except_sender(client_info, cube_creation_event)

    def handle_cube_destroy_event(self, client_info: dict, event: CubeDestroyEvent):
        assert event.type == "CubeDestroy"
        cube_id = event.cube_id

        # remove the cube info from self.cubes
        del self.cubes[cube_id]

        # broadcast cube destroy event
        cube_destroy_event = CubeDestroyEvent(cube_id)
        self.broadcast_event_except_sender(client_info, cube_destroy_event)
    
    def broadcast_event_except_sender(self, sender_client_info: dict, event: Event):
        for player_id in self.player_id_to_client_info:
            other_client_info = self.player_id_to_client_info[player_id]
            # do not send to sender
            if other_client_info == sender_client_info:
                continue
            other_client_info['event_to_send_queue'].put(event)
        server_log(f"Broadcasted event {event}", player_id=sender_client_info['player_id'])
    
    def process_client_disconnect(self, client_info: dict):
        """处理客户端断开连接的情况"""
        player_id = client_info['player_id']
        assert player_id is not None
        # remove player from self.players
        del self.players[player_id]
        # remove player_id from self.player_id_to_client_info
        del self.player_id_to_client_info[player_id]
        # broadcast player leave event
        player_leave_event = PlayerLeaveEvent(player_id)
        self.broadcast_event_except_sender(client_info, player_leave_event)



def server_log(*args, title="[cyan]Client threads[/cyan]", player_id=None):
    title += f"[{player_id}]" if player_id is not None else ""
    print(title, *args)

if __name__ == '__main__':
    server = GameServer(SERVER_HOST, SERVER_PORT)
    server.run()


