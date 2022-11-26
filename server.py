from network.constants import *
from network.server import GameServer

if __name__ == '__main__':
    server = GameServer(SERVER_HOST, SERVER_PORT)
    server.run()
