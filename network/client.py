import socket
import threading
import queue
from .event import *
from .serialize import *
from .constants import *
from rich import print
import time

class GameClient:
    def __init__(self, host: str, port: int):
        self.server_host = host
        self.server_port = port
        self.socket_client: socket.socket = None
        self.recv_buffer: bytes = b''
        self.recv_event_queue: queue.Queue = queue.Queue()
        self.send_event_queue: queue.Queue = queue.Queue()
        self.recv_thread: threading.Thread = None
        self.send_thread: threading.Thread = None
        self.running: bool = False

        self.player_id: int = None

    def connect_to_server(self):
        """连接到服务器"""
        self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.socket_client.connect((self.server_host, self.server_port))
        # 连接到本地服务器并判断是否连接成功
        try:
            self.socket_client.connect((self.server_host, self.server_port))
            print("Connect to server successfully!")
        except ConnectionRefusedError:
            print("Connection Refused")
            return False

    def send_event_to_server(self, event: Event):
        """用户调用的发送事件函数"""
        self.send_event_queue.put(event)

    def send_event(self, event: Event):
        bytes_to_send = serialize_event(event)
        packet_length = len(bytes_to_send)
        packet_header = b'pack' + packet_length.to_bytes(4, "big")
        packet_body = bytes_to_send
        packet_bytes = packet_header + packet_body
        self.socket_client.send(packet_bytes)

    def iter_events(self):
        while self.running:
            # clear buffer
            self.recv_buffer = b''
            # recv header
            header_bytes_to_recv_left = 8
            while header_bytes_to_recv_left > 0:
                try:
                    header_bytes = self.socket_client.recv(header_bytes_to_recv_left)
                except Exception as e:
                    # print(e)
                    self.running = False
                    return
                self.recv_buffer += header_bytes
                header_bytes_to_recv_left -= len(header_bytes)
            # check header
            if self.recv_buffer[:4] != b'pack':
                raise RuntimeError("Invalid packet header")
            packet_length = int.from_bytes(self.recv_buffer[4:8], "big")
            # recv body
            body_bytes_to_recv_left = packet_length
            while body_bytes_to_recv_left > 0:
                try:
                    body_bytes = self.socket_client.recv(body_bytes_to_recv_left)
                except Exception as e:
                    # print(e)
                    self.running = False
                    return
                self.recv_buffer += body_bytes
                body_bytes_to_recv_left -= len(body_bytes)
            # check body
            if len(self.recv_buffer) != 8 + packet_length:
                raise RuntimeError("Invalid packet body")
            # deserialize event
            event = deserialize_event(self.recv_buffer[8:])
            yield event

    def packet_recv_thread(self):
        # print("Packet recv thread started")
        for event in self.iter_events():
            if not self.running:
                break
            # print(f"Received event: {event}")
            assert event.type in ("PlayerMovement", "CubeCreation", "CubeDestroy", "PlayerJoin", "PlayerLeave", "PlayerRegisterResponse")
            self.recv_event_queue.put(event)
        print("Packet recv thread stopped")

    def packet_send_thread(self):
        print("Packet send thread started")
        while self.running:
            time.sleep(0.1) # 这里很重要，不能写一个永远不会挂起的死循环把所有CPU都占了，否则其他线程就几乎无法运行了
            if not self.send_event_queue.empty():
                event = self.send_event_queue.get()
                self.send_event(event)
                print(f"Sent event: {event}")
            else:
                if not self.running:
                    break
        print("Packet send thread stopped")

    def run(self):
        print("Connecting to server...")
        self.running = True
        self.connect_to_server()
        self.recv_thread = threading.Thread(target=self.packet_recv_thread)
        self.recv_thread.start()
        self.send_thread = threading.Thread(target=self.packet_send_thread)
        self.send_thread.start()
        print("Game client started")

    def stop(self):
        self.running = False
        self.send_thread.join() 
        time.sleep(1) # 等待发送线程最后发送的事件发送完再关闭socket
        self.socket_client.close()
        self.recv_thread.join()     
        print("Game client stopped")

    # 返回player_id, player_position, cubes_list, players_list
    def register_player(self):
        player_register_request_event = PlayerRegisterRequestEvent()
        self.send_event(player_register_request_event)
        # self.socket_client.send(serialize_event(player_register_request_event))
        print("Player register request sent")
        player_register_response_event: PlayerRegisterResponseEvent = self.recv_event_queue.get()
        assert player_register_response_event.type == "PlayerRegisterResponse"
        self.player_id = player_register_response_event.player_id
        return player_register_response_event.player_id, player_register_response_event.player_position, player_register_response_event.player_rotation, player_register_response_event.map_cubes, player_register_response_event.map_players

    def player_movement(self, new_player_position: Tuple[float, float, float], new_player_rotation: Tuple[float, float, float]):
        player_movement_event = PlayerMovementEvent(self.player_id, new_player_position, new_player_rotation)
        self.send_event_to_server(player_movement_event)

    def cube_creation(self, cube_id: int, cube_position: Tuple[float, float, float], cube_type: int):
        # cube_id = int(f"{player_id}{time.time_ns()}")
        cube_creation_event = CubeCreationEvent(cube_id, cube_position, cube_type)
        self.send_event_to_server(cube_creation_event)

    def cube_destroy(self, cube_id: int):
        cube_destroy_event = CubeDestroyEvent(cube_id)
        self.send_event_to_server(cube_destroy_event)



def client_log(*args, title="[cyan]Server threads[/cyan]"):
    print(title, *args)
    
if __name__ == "__main__":
    GAME_SERVER_HOST = "127.0.0.1"
    GAME_SERVER_PORT = 12345
    client = GameClient(GAME_SERVER_HOST, GAME_SERVER_PORT)
    client.run()
    print("Registering player...")
    game_info = client.register_player() # 注册玩家,下载地图信息（方块和其他玩家）
    player_id, player_position, player_rotation, cubes_list, players_list = game_info
    print(f"Player ID: {player_id}")
    print(f"Player Position: {player_position}")
    print(f"Player Rotation: {player_rotation}")
    print(f"Cubes List: {cubes_list}")
    print(f"Players List: {players_list}")



    # make a CubeCreationEvent and send it to server
    cube_id = int(f"{player_id}{time.time_ns()}")
    client.cube_creation(cube_id, (0,0,0), CUBE_TYPE_GRASS)

    # make a CubeDestroyEvent and send it to server
    # client.cube_destroy(cube_id)

    # make a PlayerMovementEvent and send it to server
    player_new_position = (player_position[0] + 1, player_position[1], player_position[2])
    player_new_rotation = (0, 0, 0)
    client.player_movement(player_new_position, player_new_rotation)

    # __import__('sleep').sleep(1)
    # client.stop()


    # 启动一个新线程，用来接收服务器发来的事件，以便更新本地的游戏状态
    while True:
        # 1. 接收服务器发来的事件
        game_event = client.recv_event_queue.get()
        # 2. 处理事件
        print(f"Handling event: {game_event}")

    # 主线程用来处理玩家的输入，然后发送给服务器
    # 例如，玩家按下了W键，那么就发送一个PlayerMovement事件给服务器
