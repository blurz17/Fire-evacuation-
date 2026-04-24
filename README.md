# 🔥 Fire Evacuation — Pathfinding Visualizer

A Python desktop application that simulates emergency evacuation from a burning building
using classical uninformed search algorithms.
Built with **PySide6** — one install, no other dependencies.

---

## 🚀 Quick Start

```bash
# 1. Make sure Python 3.9+ is installed
python --version

# 2. Create and activate a virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate.ps1   # Windows
# source venv/bin/activate  # macOS / Linux

# 3. Install the only dependency
pip install PySide6

# 4. Run the app
python main.py
```

---

## 🖥️ How to Use

| Step | Action |
|------|--------|
| 1 | Select **🧱 Wall** tool → click/drag to draw walls |
| 2 | Select **🔥 Fire** tool → click/drag to place fire zones |
| 3 | Select **🚪 Exit** tool → click cells to place exit doors (E) |
| 4 | Select **🧍 Person** tool → click a cell to place the evacuee (P) |
| 5 | Choose an algorithm (BFS / DFS / Both) from the dropdown |
| 6 | Optionally tick **Spread fire while animating** |
| 7 | Click **Find escape route ▶** and watch the animation |
| 8 | Use **Reset paths** to retry on the same floor plan |
| 9 | Use **Clear all** to start fresh |

> 💡 **Tip:** Click **Random floor plan** to instantly generate a building with walls, fire, exits, and a person — ready to run.

---

## 🧠 Algorithms

### Breadth-First Search (BFS)
- Uses a **FIFO queue** (`collections.deque`)
- Explores cells level by level (nearest exit first)
- ✅ **Guarantees the shortest escape path** on unweighted grids
- ❌ Uses more memory than DFS (holds the entire frontier)

### Depth-First Search (DFS)
- Uses a **LIFO stack** (Python list with `.pop()`)
- Dives deep along one corridor before backtracking
- ✅ Low memory footprint, fast to find *any* exit
- ❌ Does **not** guarantee the shortest path

### Fire Spread
- Implemented as a **BFS expansion** from all current fire cells
- Fire spreads one cell per tick into adjacent empty cells
- Fire never spreads through walls
- Enabled via the **Spread fire while animating** checkbox

---

## ⚙️ PEAS Description

| Component | Description |
|-----------|-------------|
| **Performance** | Shortest path length · cells explored · execution time (ms) |
| **Environment** | 2D grid building floor plan with walls, fire, and exits |
| **Actuators** | Move Up / Down / Left / Right (4-directional) |
| **Sensors** | Current position · fire detection · exit detection · wall detection |

---

## 🧩 ODESA Classification

| Property | Value | Reason |
|----------|-------|--------|
| **Observable** | Fully Observable | Agent sees the complete grid at all times |
| **Deterministic** | Deterministic | Same action always produces the same result |
| **Episodic** | Sequential | Each move depends on all prior moves |
| **Static** | Static (default) / Dynamic (fire spread on) | Grid can change mid-search when fire spreading is enabled |
| **Agents** | Single Agent | One person evacuates independently |

---

## 📁 Project Structure

```
fire_evacuation/
├── main.py              ← Entry point + app launch
├── gui.py               ← PySide6 UI, grid canvas, animation engine, fire timer
├── search_algorithms.py ← BFS, DFS, and spread_fire implementations
└── README.md            ← This file
```

---

## 🔧 Grid Encoding

The grid is a 2D list of integers:

| Value | Constant | Meaning |
|-------|----------|---------|
| `0` | `WALL` | Impassable wall |
| `1` | `EMPTY` | Open corridor — passable |
| `2` | `FIRE` | Fire zone — blocks movement |
| `3` | `EXIT` | Exit door — goal cell |

The algorithms check `grid[nr][nc] != WALL and grid[nr][nc] != FIRE` to decide if a neighbor is reachable.

---

## 🎨 UI Color Guide

| Color | Meaning |
|-------|---------|
| ⬛ Very dark | Wall |
| 🟠 Orange-red | Fire zone |
| 🟢 Teal / Green | Exit door (E) |
| 🟣 Purple | Person / evacuee (P) |
| 🔵 Light blue | BFS explored cells |
| 🟣 Light purple | DFS explored cells |
| 🔵 Dark blue | BFS final escape path |
| 🟣 Dark purple | DFS final escape path |