# py-crawler
Python CLI Dungeon Crawler

## Description
A turn-based, terminal roguelike dungeoncrawler. Navigate through randomly generated mazes, fight enemies, and descend into the depths. Play solo or co-op over TCP.

### Features:

- **Party System:** The user can control multiple (4 solo, any co-op) player characters, each with their own inventory, class, and base stats (based on class)

- **Initiative System:** A speed-derived Initiative System where higher-speed units can perform actions more often than those with lower speed, as opposed to just a set turn order, allowing for more complex combats and builds.

- **Maze generation:** Random walk main path with branches off of the path, and sub-branches

- **Relics:** Relics are items with passive abilities that can be equipped to a character, such as more health or damage.

- **Enemies with unique mechanicals:** A large variety of enemies with unique mechanics, such as: 
 - Large Slime splitting into multiple small slimes
 - Strange Man (?) turns into a werewolf

- **Aggro System:** Enemies will target whoever has dealt the most damage to them.

- **Conditions:** Effects that can be applied to units in combat

- **Multiple Floors:** Once the boss room is beat, the party can move to a lower floor, with harder enemies.

- **Save files:** Progress is saved automatically

- **Multiplayer:** Host a server, fight alongside your friends

## Requirements

- **Windows** for client (uses msvcrt), any OS for server
- **Python 3.14 or newer**

## Installation

### Option A: standalone exe

Download latest build from [Releases](../../releases) and run.

### Option B: source

```bash
git clone https://github.com/turtlemaster890/py-crawler.git
cd py-crawler
git checkout online
pip install -r requirements.txt
python main.py
```

## Usage

Modes:

1. **Standalone:** Single player, local save file
2. **Server Host:** Hosts co-op, Needs IPv6 and port forwarding
3. **Client:** Connect to hosted game

### Controls

- **Arrow keys:** Move through maze and menus
- **Enter:** Confirm
- **Esc:** Quit

### Multiplayer hosting
1. Pick option 2 on host machine
2. Ensure port is reachable - port forwarding required for clients outside your local network
3. Give players ip and port.

## Building

```bash
pip install pyinstaller
pyinstaller py-crawler.spec
```

To build exe, use `py-crawler-release.spec`.

