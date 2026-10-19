import json

class MessageSocket:
    def __init__(self, sock):
        self.sock = sock
        self.buffer = b""


    def send_msg(self, obj):
        line = json.dumps(obj) + "\n"
        self.sock.sendall(line.encode())

    def recv_msg(self):
        while b"\n" not in self.buffer:
            chunk = self.sock.recv(1024)
            if not chunk:
                return None
            self.buffer += chunk
        line, _, self.buffer = self.buffer.partition(b"\n")
        return json.loads(line.decode())