# py-crawler
Python CLI Dungeon Crawler

## Description
A turn-based roguelike dungeoncrawler with a randomly generated map, displayed through the terminal.

### Features:

#### Party System
The user can control multiple (4) player characters, each with their own inventory, class, and base stats (based on class)

#### Initiative System
A speed-derived Initiative System where higher-speed units can perform actions more often than those with lower speed, as opposed to just a set turn order, allowing for more complex combats and builds.

#### Maze generation
Random walk main path with branches off of the path, and sub-branches

#### Relics
Relics are items with passive abilities that can be equipped to a character, such as more health or damage.

#### Enemies
A large variety of enemies with unique mechanics, such as:
Large Slime splitting into multiple small slimes
Strange Man (?) turns into a werewolf

#### Aggro System
Enemies will target whoever has dealt the most damage to them.

#### Conditions
Effects that can be applied to units in combat

#### Multiple Floors
Once the boss room is beat, the party can move to a lower floor, with harder enemies.

## Usage
Use arrow keys and enter to navigate the maze and menus.

## Installation
Download standalone exe from releases, or clone locally and run `main.py` <--- ENSURE YOU HAVE PYTHON >=3.14, AS IT WILL NOT WORK WITH A LOWER VERSION
