from pynput.keyboard import Key, KeyCode
import threading
import msvcrt
import time

lastKey: Key | KeyCode | None = None
# held_keys: set[Key] = set()

# input_keys = {}


def getKey():
    global lastKey
    k = lastKey
    lastKey = None
    return k


arrow_map = {b"H": Key.up, b"P": Key.down, b"K": Key.left, b"M": Key.right}


def update():
    while True:
        global lastKey
        lastKey = None
        while msvcrt.kbhit():
            ch = msvcrt.getch()

            key = None

            if ch in (b"\x00", b"\xe0"):
                ch2 = msvcrt.getch()
                key = arrow_map.get(ch2)
            elif ch == b"\r":
                key = Key.enter
            elif ch == b"\x1b":
                key = Key.esc
            elif ch == b" ":
                key = Key.space
            elif ch == b"\x03":
                raise KeyboardInterrupt
            else:
                try:
                    char_str = ch.decode("utf-8").lower()
                    key = KeyCode.from_char(char_str)
                except UnicodeDecodeError:
                    continue

            if key:
                lastKey = key
        time.sleep(0.01)


# listener = keyboard.Listener(on_press=pressKey, on_release=releaseKey)


def start():
    t = threading.Thread(target=update, daemon=True)
    t.start()
