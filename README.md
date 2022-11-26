# MineCraft-Online-Game
计算机网络大作业，“我的世界”联机小游戏
## 文件目录
### 游戏模块
main.py - 客户端主文件
server.py - 服务端主文件
cube.py - 方块类
myFPC.py - 第一视角
otherplayer.py - 其他文件配置
launch_client.py - 双击启动客户端
startup_server.py - 双击启动服务端

### 网络模块
network包
client - 客户端
server - 服务端
event - 事件定义
serialize - 序列化操作
constants - 常量定义

## 使用
修改network中constants中的客户端、端口 -> 服务端
修改main.py中init_network方法中的IP和端口号，连接服务端 -> 客户端
