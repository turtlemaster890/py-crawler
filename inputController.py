import pynput

lastKey = None
held_keys = set()
def getKey():
    global lastKey
    k = lastKey
    lastKey = None
    return k
def pressKey(key):
    global lastKey
    if key not in held_keys:
        held_keys.add(key)
        lastKey = key

def releaseKey(key):
    global lastKey
    held_keys.discard(key)
    if lastKey == key:
        lastKey = None

def start():
    listener = pynput.keyboard.Listener(on_press=pressKey, on_release=releaseKey)
    listener.start()