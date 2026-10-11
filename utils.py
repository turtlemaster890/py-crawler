import os
from typing import Callable
from pynput.keyboard import Key

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

printSqs: dict[str, tuple[Callable, int]] = {}

def addPrintFunction(name: str, func: Callable, priority: int):
    printSqs[name] = (func, priority)

def removePrintFunction(name: str):
    del printSqs[name]

def printSequences():
    clear()
    order = list(printSqs.values())
    order.sort(key=lambda x: x[1]) #.sort(key = lambda x: x[1])
    for func in order:
        func[0]()

key_to_delta = {
    Key.up: -1,
    Key.down: 1
}