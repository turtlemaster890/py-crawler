import socket
from netutil import MessageSocket

HOST = "localhost"
PORT = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    ms = MessageSocket(s)
    ms.send_msg({"type": "move", "dir": "UP"})
    ms.send_msg({"type": "move", "dir": "DOWN"})
    ms.send_msg({"type": "move", "dir": "LEFT"})