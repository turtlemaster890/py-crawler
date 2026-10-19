import socket
from netutil import MessageSocket

HOST = "localhost"
PORT = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("waiting for a client...")
    conn, addr = s.accept()
    print("client found")
    ms = MessageSocket(conn)
    while True:
        msg = ms.recv_msg()
        if msg == None:
            print("client disconnected")
            break
        print (msg)