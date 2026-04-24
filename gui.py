"""
gui.py — PySide6 GUI for the Fire Evacuation Visualizer
Draw a building floor plan, place fire and exits, then watch BFS/DFS
find the shortest escape route — with optional live fire spreading.
"""
import copy
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSlider, QFrame,
    QStatusBar, QButtonGroup, QRadioButton, QGroupBox,
    QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush

from search_algorithms import WALL, EMPTY, FIRE, EXIT

# ── Palette ────────────────────────────────────────────────────────────────────
C_EMPTY   = QColor("#f5f5f0")
C_WALL    = QColor("#2c2c2a")
C_FIRE    = QColor("#D85A30")
C_EXIT    = QColor("#1D9E75")
C_PERSON  = QColor("#7F77DD")
C_PATH    = QColor("#EF9F27")
C_EXPLORE_BFS = QColor("#B5D4F4")
C_EXPLORE_DFS = QColor("#CECBF6")
C_GRID    = QColor("#d0d0c8")
C_PATH_BFS = QColor("#185FA5")
C_PATH_DFS = QColor("#534AB7")


class GridCanvas(QWidget):
    CELL = 20
    GAP  = 1

    def __init__(self, rows=25, cols=35, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.cols = cols
        self.grid = [[EMPTY] * cols for _ in range(rows)]
        self.person = None          # (r, c) start position
        self.overlay = {}           # (r,c) -> QColor  for explore/path animation
        self.draw_mode = "wall"     # wall | erase | fire | exit | person
        self._drawing = False
        self._update_size()

    def _update_size(self):
        w = self.cols * (self.CELL + self.GAP) + self.GAP
        h = self.rows * (self.CELL + self.GAP) + self.GAP
        self.setFixedSize(w, h)

    def cell_rect(self, r, c):
        x = self.GAP + c * (self.CELL + self.GAP)
        y = self.GAP + r * (self.CELL + self.GAP)
        return QRect(x, y, self.CELL, self.CELL)

    def cell_at(self, px, py):
        c = int(px) // (self.CELL + self.GAP)
        r = int(py) // (self.CELL + self.GAP)
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return r, c
        return None

    def reset(self):
        self.grid = [[EMPTY] * self.cols for _ in range(self.rows)]
        self.person = None
        self.overlay.clear()
        self.update()

    def clear_overlay(self):
        self.overlay.clear()
        self.update()

    def set_overlay(self, r, c, color):
        self.overlay[(r, c)] = color
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), C_GRID)

        for r in range(self.rows):
            for c in range(self.cols):
                rect = self.cell_rect(r, c)
                v = self.grid[r][c]

                if (r, c) in self.overlay:
                    p.fillRect(rect, self.overlay[(r, c)])
                elif v == WALL:
                    p.fillRect(rect, C_WALL)
                elif v == FIRE:
                    p.fillRect(rect, C_FIRE)
                elif v == EXIT:
                    p.fillRect(rect, C_EXIT)
                    # draw E label
                    p.setPen(QColor("#ffffff"))
                    p.setFont(QFont("Arial", 9, QFont.Bold))
                    p.drawText(rect, Qt.AlignCenter, "E")
                else:
                    p.fillRect(rect, C_EMPTY)

        # draw person marker
        if self.person:
            r, c = self.person
            rect = self.cell_rect(r, c)
            p.fillRect(rect, C_PERSON)
            p.setPen(QColor("#ffffff"))
            p.setFont(QFont("Arial", 9, QFont.Bold))
            p.drawText(rect, Qt.AlignCenter, "P")

    def mousePressEvent(self, e):
        self._drawing = True
        self._handle(e)

    def mouseMoveEvent(self, e):
        if self._drawing:
            self._handle(e)

    def mouseReleaseEvent(self, _):
        self._drawing = False

    def _handle(self, e):
        cell = self.cell_at(e.position().x(), e.position().y())
        if cell is None:
            return
        r, c = cell

        if self.draw_mode == "wall" and e.buttons() & Qt.LeftButton:
            self.grid[r][c] = WALL
            self.overlay.pop((r, c), None)
        elif self.draw_mode == "erase" and e.buttons() & Qt.LeftButton:
            self.grid[r][c] = EMPTY
            self.overlay.pop((r, c), None)
        elif self.draw_mode == "fire" and e.buttons() & Qt.LeftButton:
            self.grid[r][c] = FIRE
            self.overlay.pop((r, c), None)
        elif self.draw_mode == "exit" and e.buttons() & Qt.LeftButton:
            self.grid[r][c] = EXIT
            self.overlay.pop((r, c), None)
        elif self.draw_mode == "person" and e.buttons() & Qt.LeftButton:
            if self.grid[r][c] == EMPTY:
                self.person = (r, c)
        elif e.buttons() & Qt.RightButton:
            self.grid[r][c] = EMPTY
            self.overlay.pop((r, c), None)

        self.update()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fire Evacuation — BFS vs DFS")
        self.setMinimumWidth(980)

        self._anim_steps  = []
        self._anim_idx    = 0
        self._anim_phase  = "explore"   # "explore" | "path"
        self._anim_path   = []
        self._anim_explore = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._saved_grid  = None
        self._fire_timer  = QTimer(self)
        self._fire_timer.timeout.connect(self._spread_fire)

        # status bar before _build_ui (needed by _set_mode)
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self._build_ui()

    # ─────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(16)

        self.canvas = GridCanvas(rows=24, cols=36)
        outer.addWidget(self.canvas)

        panel = QVBoxLayout()
        panel.setSpacing(10)
        panel.setAlignment(Qt.AlignTop)
        outer.addLayout(panel)

        # title
        t = QLabel("Fire Evacuation")
        t.setFont(QFont("Arial", 15, QFont.Medium))
        panel.addWidget(t)
        sub = QLabel("Build a floor plan, place fire & exits,\nthen find the escape route.")
        sub.setStyleSheet("color:#888; font-size:12px;")
        panel.addWidget(sub)

        panel.addWidget(self._div())

        # ── draw tools ────────────────────────────────────────────────────────
        panel.addWidget(self._section("Draw tool"))
        tools = [
            ("Wall",   "wall"),
            ("Erase",  "erase"),
            ("Fire",   "fire"),
            ("Exit",   "exit"),
            ("Person", "person"),
        ]
        self._tool_btns = {}
        grid_tools = QHBoxLayout()
        grid_tools.setSpacing(4)
        for label, mode in tools:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("mode", mode)
            btn.clicked.connect(lambda _, m=mode: self._set_mode(m))
            self._tool_btns[mode] = btn
            grid_tools.addWidget(btn)
        panel.addLayout(grid_tools)

        panel.addWidget(self._div())

        # ── algorithm ─────────────────────────────────────────────────────────
        panel.addWidget(self._section("Algorithm"))
        self.algo_combo = QComboBox()
        self.algo_combo.addItems([
            "BFS  — shortest path",
            "DFS  — any path",
            "Both — compare",
        ])
        panel.addWidget(self.algo_combo)

        panel.addWidget(self._div())

        # ── fire spread ───────────────────────────────────────────────────────
        panel.addWidget(self._section("Live fire spread"))
        self.fire_check = QCheckBox("Spread fire while animating")
        panel.addWidget(self.fire_check)

        spread_row = QHBoxLayout()
        spread_row.addWidget(QLabel("Speed:"))
        self.fire_speed = QSlider(Qt.Horizontal)
        self.fire_speed.setRange(1, 10)
        self.fire_speed.setValue(4)
        spread_row.addWidget(self.fire_speed)
        panel.addLayout(spread_row)

        panel.addWidget(self._div())

        # ── animation speed ───────────────────────────────────────────────────
        panel.addWidget(self._section("Animation speed"))
        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("Slow"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(6)
        speed_row.addWidget(self.speed_slider)
        speed_row.addWidget(QLabel("Fast"))
        panel.addLayout(speed_row)

        panel.addWidget(self._div())

        # ── actions ───────────────────────────────────────────────────────────
        self.btn_run = QPushButton("Find escape route ▶")
        self.btn_run.setStyleSheet(
            "background:#1D9E75; color:white; font-weight:500;"
            "border-radius:6px; padding:6px 10px; border:none;"
        )
        self.btn_run.clicked.connect(self._run)
        panel.addWidget(self.btn_run)

        self.btn_reset = QPushButton("Reset paths")
        self.btn_reset.clicked.connect(self._reset_paths)
        panel.addWidget(self.btn_reset)

        self.btn_random = QPushButton("Random floor plan")
        self.btn_random.clicked.connect(self._random_floor)
        panel.addWidget(self.btn_random)

        self.btn_clear = QPushButton("Clear all")
        self.btn_clear.clicked.connect(self._clear)
        panel.addWidget(self.btn_clear)

        panel.addWidget(self._div())

        # ── stats ─────────────────────────────────────────────────────────────
        self.stats = QLabel("Place a Person (P) and at least\none Exit (E), then click\n'Find escape route'.")
        self.stats.setStyleSheet("font-size:12px; color:#666;")
        self.stats.setWordWrap(True)
        panel.addWidget(self.stats)

        panel.addStretch()

        # ── legend ────────────────────────────────────────────────────────────
        panel.addWidget(self._div())
        panel.addWidget(self._legend())

        self._set_mode("wall")
        self.status.showMessage(
            "Draw walls, place fire (F) and exits (E), set person (P), then run."
        )

    # ── helpers ───────────────────────────────────────────────────────────────
    def _section(self, text):
        l = QLabel(text)
        l.setStyleSheet("font-size:12px; font-weight:500; color:#555; margin-top:2px;")
        return l

    def _div(self):
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setStyleSheet("color:#e0e0e0;")
        return f

    def _set_mode(self, mode):
        self.canvas.draw_mode = mode
        colors = {
            "wall":   "#2c2c2a",
            "erase":  "#888",
            "fire":   "#D85A30",
            "exit":   "#1D9E75",
            "person": "#7F77DD",
        }
        for m, btn in self._tool_btns.items():
            active = m == mode
            btn.setChecked(active)
            btn.setStyleSheet(
                f"background:{colors[m]}; color:white; border-radius:4px; padding:4px 6px;"
                if active else "border-radius:4px; padding:4px 6px;"
            )
        hints = {
            "wall":   "Left-click drag to draw walls  |  Right-click to erase",
            "erase":  "Left-click drag to erase cells",
            "fire":   "Left-click drag to place fire",
            "exit":   "Left-click to place exit doors (E)",
            "person": "Left-click to place the person (P) — start of evacuation",
        }
        self.status.showMessage(hints[mode])

    def _legend(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(3)
        lay.setContentsMargins(0, 0, 0, 0)
        items = [
            (C_PERSON,      "Person (start)"),
            (C_EXIT,        "Exit door"),
            (C_FIRE,        "Fire"),
            (C_WALL,        "Wall"),
            (C_EXPLORE_BFS, "BFS explored"),
            (C_EXPLORE_DFS, "DFS explored"),
            (C_PATH_BFS,    "BFS path"),
            (C_PATH_DFS,    "DFS path"),
        ]
        for color, name in items:
            row = QHBoxLayout()
            dot = QLabel()
            dot.setFixedSize(12, 12)
            dot.setStyleSheet(f"background:{color.name()}; border-radius:2px;")
            lbl = QLabel(name)
            lbl.setStyleSheet("font-size:11px; color:#666;")
            row.addWidget(dot)
            row.addWidget(lbl)
            row.addStretch()
            lay.addLayout(row)
        return w

    # ── grid actions ──────────────────────────────────────────────────────────
    def _clear(self):
        self._timer.stop()
        self._fire_timer.stop()
        self.canvas.reset()
        self._saved_grid = None
        self.stats.setText("Grid cleared.")

    def _reset_paths(self):
        self._timer.stop()
        self._fire_timer.stop()
        if self._saved_grid:
            self.canvas.grid = copy.deepcopy(self._saved_grid)
        self.canvas.clear_overlay()
        self.canvas.update()
        self.stats.setText("Paths cleared. Run again.")

    def _random_floor(self):
        import random
        self._timer.stop()
        self._fire_timer.stop()
        self.canvas.reset()
        rows, cols = self.canvas.rows, self.canvas.cols

        # walls (~25%)
        for r in range(rows):
            for c in range(cols):
                if random.random() < 0.25:
                    self.canvas.grid[r][c] = WALL

        # fire clusters (2-3 spots)
        for _ in range(random.randint(2, 3)):
            fr = random.randint(0, rows - 1)
            fc = random.randint(0, cols - 1)
            if self.canvas.grid[fr][fc] == EMPTY:
                self.canvas.grid[fr][fc] = FIRE

        # exits on edges (2-3)
        for _ in range(random.randint(2, 3)):
            side = random.choice(["top", "bottom", "left", "right"])
            if side == "top":
                r, c = 0, random.randint(0, cols - 1)
            elif side == "bottom":
                r, c = rows - 1, random.randint(0, cols - 1)
            elif side == "left":
                r, c = random.randint(0, rows - 1), 0
            else:
                r, c = random.randint(0, rows - 1), cols - 1
            self.canvas.grid[r][c] = EXIT

        # person in middle area
        for _ in range(100):
            pr = random.randint(rows // 4, 3 * rows // 4)
            pc = random.randint(cols // 4, 3 * cols // 4)
            if self.canvas.grid[pr][pc] == EMPTY:
                self.canvas.person = (pr, pc)
                break

        self._saved_grid = None
        self.canvas.update()
        self.stats.setText("Random floor plan generated.\nClick 'Find escape route'.")

    # ── run ───────────────────────────────────────────────────────────────────
    def _run(self):
        if self.canvas.person is None:
            self.stats.setText("No person placed!\nUse Person tool to set start.")
            return

        has_exit = any(
            self.canvas.grid[r][c] == EXIT
            for r in range(self.canvas.rows)
            for c in range(self.canvas.cols)
        )
        if not has_exit:
            self.stats.setText("No exit placed!\nUse Exit tool to place exits.")
            return

        self._timer.stop()
        self._fire_timer.stop()
        self._saved_grid = copy.deepcopy(self.canvas.grid)
        self.canvas.clear_overlay()

        algo = self.algo_combo.currentIndex()

        if algo == 0:
            self._run_single("bfs")
        elif algo == 1:
            self._run_single("dfs")
        else:
            self._run_both()

        # fire spread timer
        if self.fire_check.isChecked():
            fire_interval = max(300, int(1500 - self.fire_speed.value() * 120))
            self._fire_timer.start(fire_interval)

    def _run_single(self, algo):
        from search_algorithms import bfs, dfs
        g = copy.deepcopy(self._saved_grid)
        start = self.canvas.person

        if algo == "bfs":
            path, explored, elapsed = bfs(g, start)
            exp_color  = C_EXPLORE_BFS
            path_color = C_PATH_BFS
            label = "BFS"
        else:
            path, explored, elapsed = dfs(g, start)
            exp_color  = C_EXPLORE_DFS
            path_color = C_PATH_DFS
            label = "DFS"

        if path is None:
            self.stats.setText(
                f"{label}: No escape route found!\nFire may have cut off all exits."
            )
            # still animate exploration
            self._queue_explore(explored, exp_color, [], path_color, label, elapsed, False)
        else:
            self._queue_explore(explored, exp_color, path, path_color, label, elapsed, True)

    def _run_both(self):
        from search_algorithms import bfs, dfs
        g1 = copy.deepcopy(self._saved_grid)
        g2 = copy.deepcopy(self._saved_grid)
        start = self.canvas.person

        path_b, exp_b, t_b = bfs(g1, start)
        path_d, exp_d, t_d = dfs(g2, start)

        # interleave explore steps
        self._anim_steps = []
        max_e = max(len(exp_b), len(exp_d))
        for i in range(max_e):
            if i < len(exp_b):
                self._anim_steps.append((exp_b[i], C_EXPLORE_BFS))
            if i < len(exp_d):
                self._anim_steps.append((exp_d[i], C_EXPLORE_DFS))

        # then both paths
        for cell in (path_b or []):
            self._anim_steps.append((cell, C_PATH_BFS))
        for cell in (path_d or []):
            self._anim_steps.append((cell, C_PATH_DFS))

        self._anim_idx = 0
        self._start_anim()

        pb = len(path_b) if path_b else 0
        pd = len(path_d) if path_d else 0
        self.stats.setText(
            f"BFS path : {pb} steps   {t_b*1000:.2f} ms\n"
            f"DFS path : {pd} steps   {t_d*1000:.2f} ms\n"
            f"Blue = BFS  |  Purple = DFS"
        )

    def _queue_explore(self, explored, exp_color, path, path_color, label, elapsed, found):
        self._anim_steps = []
        for cell in explored:
            self._anim_steps.append((cell, exp_color))
        for cell in path:
            self._anim_steps.append((cell, path_color))

        self._anim_idx = 0
        self._pending_stats = (label, len(explored), len(path), elapsed, found)
        self._start_anim()

    def _start_anim(self):
        speed = self.speed_slider.value()
        interval = max(5, int(120 - speed * 11))
        self._timer.start(interval)

    def _step(self):
        if self._anim_idx >= len(self._anim_steps):
            self._timer.stop()
            if hasattr(self, "_pending_stats"):
                label, explored, path_len, elapsed, found = self._pending_stats
                if found:
                    self.stats.setText(
                        f"Algorithm : {label}\n"
                        f"Path length : {path_len} steps\n"
                        f"Cells explored : {explored}\n"
                        f"Time : {elapsed*1000:.3f} ms\n\n"
                        f"Route found — press Reset to retry."
                    )
                else:
                    self.stats.setText(
                        f"Algorithm : {label}\n"
                        f"Cells explored : {explored}\n"
                        f"Time : {elapsed*1000:.3f} ms\n\n"
                        f"No escape route found!"
                    )
            return

        cell, color = self._anim_steps[self._anim_idx]
        r, c = cell
        # don't overwrite fire, exits, or person
        if self.canvas.grid[r][c] not in (FIRE, EXIT) and (r, c) != self.canvas.person:
            self.canvas.set_overlay(r, c, color)
        self._anim_idx += 1

    def _spread_fire(self):
        from search_algorithms import spread_fire
        self.canvas.grid = spread_fire(self.canvas.grid, steps=1)
        self.canvas.update()