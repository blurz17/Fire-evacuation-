"""
main.py  —  Delivery Robot Pathfinding Visualizer
--------------------------------------------------
Zero external dependencies — uses Python's built-in Tkinter.

Run:
    python main.py

──────────────────────────────────────────────────
PEAS Description
──────────────────────────────────────────────────
Performance : Shortest path length, nodes explored, time (ms)
Environment : 2D grid city map with static obstacles
Actuators   : Move Up / Down / Left / Right
Sensors     : Current position, adjacent obstacle detection, goal detection

──────────────────────────────────────────────────
ODESA Classification
──────────────────────────────────────────────────
Observable   : Fully Observable  — agent sees entire grid
Deterministic: Deterministic     — same action → same result always
Episodic     : Sequential        — each move depends on prior state
Static       : Static            — grid doesn't change during search
Agents       : Single Agent      — one robot, no other agents
──────────────────────────────────────────────────
"""

"""
Run:  python main.py
"""

import sys
from PySide6.QtWidgets import QApplication
from gui import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Fire Evacuation Visualizer")
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()