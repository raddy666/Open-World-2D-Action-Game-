# 🕹️ 2D Open-World Action Game (Python / PgZero)

A **2D open-world action game** built in **Python using PgZero**, featuring real-time combat, vehicles, NPC AI, and multiple interconnected city zones.

This project implements a **custom-built 2D game engine and gameplay layer**, supporting **50+ concurrent entities**, modular systems, and scalable open-world simulation.

---

## 🎮 Gameplay

- Explore a multi-zone city world:
  - Residential
  - Industrial
  - Downtown
- Engage in melee and ranged combat
- Interact with NPCs, enemies, vehicles, and shops
- Hijack vehicles and navigate live city traffic
- Progress through increasing difficulty, including custom boss encounters

---

## ✨ Core Features

### 🌆 Open-World Systems
- Seamless gameplay across multiple environments
- Dynamic NPC spawning based on player position and progression
- Centralized game state management supporting high entity counts

### ⚔️ Combat System
- Object-oriented weapon hierarchy (melee / ranged)
- Player and enemy combat state management
- Proximity-based enemy engagement and targeting
- Custom boss fight mechanics with specialized behaviors

### 🤖 AI & NPCs
- Enemy AI implemented using behavior trees
- Finite state machines for NPC and player logic
- Autonomous NPC movement and interaction
- Difficulty scaling through adaptive spawning and AI aggression

### 🚗 Vehicle System
- Player vehicle hijacking mechanics
- Physics-aware driving controls with collision handling
- Autonomous NPC traffic system with rule-based collision avoidance

---

## 🧠 Engine Design

The game is powered by a **modular, event-driven engine architecture**:

- Decoupled systems for input, AI, combat, physics, and world logic
- Central event dispatcher for inter-system communication
- Spatial partitioning for efficient collision detection and entity updates
- Designed for extensibility and future system expansion

### Engine vs Game Logic

- **Engine Layer:** entity system, event handling, AI framework, collision, world state
- **Game Layer:** weapons, enemies, vehicles, levels, progression, boss mechanics

Character sprites are generated using the  
**Universal LPC Spritesheet Generator**, ensuring consistent animation and character customization.

---

## 🎮 Controls

| Key | Action |
|----|------|
| `W / A / S / D` | Player movement |
| `Mouse / Attack Key` | Attack |
| `1 / 2 / 3` | Switch weapons |
| `E` | Interact / enter vehicle |
| `Left Shift` | Run |
| `Esc` | Quit game |

Controls are configurable via the input mapping module and can be easily extended.

---

## ▶️ Setup & Run

### Requirements
- Python 3.x
- PgZero

### Option 1: pip (requirements.txt)

Install dependencies using pip:

```bash
pip install -r requirements.txt
```
### Option 2: Conda (environment.yml)

Create and activate the conda environment:

```bash
conda env create -f environment.yml
conda activate <environment_name>
```
---

## 🛠️ Technology Stack

- **Language:** Python  
- **Framework:** PgZero  
- **Architecture:** Object-Oriented Design  
- **AI:** Behavior Trees, Finite State Machines  

---

## 🚧 Possible Extensions

- Save / load system  
- Procedural world expansion  
- Advanced pathfinding (A*)  
- Improved physics and collision response  
- UI overlays (map, inventory, missions)  
- Cross-platform packaging  

---

## 👤 Author

**MD Tahmid Hamim**
