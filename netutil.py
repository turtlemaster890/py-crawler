import json
import socket
import threading

from packets import Packet, PacketError


class MessageSocket:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.buffer = b""
        self.send_lock = threading.Lock()

    def send(self, pkt: Packet) -> None:
        try:
            line = json.dumps(pkt.to_dict()) + "\n"
            with self.send_lock:
                self.sock.sendall(line.encode())
        except OSError:
            pass

    def recv(self) -> Packet | None:
        while b"\n" not in self.buffer:
            try:
                chunk = self.sock.recv(1024)
            except OSError:
                return None
            if not chunk:
                return None
            self.buffer += chunk
        line, _, self.buffer = self.buffer.partition(b"\n")
        try:
            return Packet.from_dict(json.loads(line.decode()))
        except json.JSONDecodeError:
            raise PacketError("Invalid json")
