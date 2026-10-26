import json
import threading

class MessageSocket:
    def __init__(self, sock):
        self.sock = sock
        self.buffer = b""
        self.send_lock = threading.Lock()


    def send_msg(self, obj):
        try:
            line = json.dumps(obj) + "\n"
            with self.send_lock:
                self.sock.sendall(line.encode())
        except OSError:
            pass

    def recv_msg(self):
        while b"\n" not in self.buffer:
            try:
                chunk = self.sock.recv(1024)
            except OSError:
                return None
            if not chunk:
                return None
            self.buffer += chunk
        line, _, self.buffer = self.buffer.partition(b"\n")
        return json.loads(line.decode())