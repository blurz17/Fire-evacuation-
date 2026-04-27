import copy
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QStatusBar,
)
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QColor

from search_algorithms import WALL, EMPTY, FIRE, EXIT, bfs, dfs, spread_fire

COLORS = {
    WALL: QColor("#2c2c2a"), FIRE: QColor("#e05a30"),
    EXIT: QColor("#1d9e75"), EMPTY: QColor("#f0f0eb"),
    "grid": QColor("#ccc"),  "person": QColor("#7f77dd"),
    "exp_bfs": QColor("#b5d4f4"), "exp_dfs": QColor("#cecbf6"),
    "path_bfs": QColor("#185fa5"), "path_dfs": QColor("#534ab7"),
}
MODES = ["wall", "erase", "fire", "exit", "person"]


class Grid(QWidget):
    S, G = 20, 1  # cell size, gap

    def __init__(self, rows=22, cols=34):
        super().__init__()
        self.rows, self.cols = rows, cols
        self.grid = [[EMPTY]*cols for _ in range(rows)]
        self.person, self.overlay, self.mode = None, {}, "wall"
        self.setFixedSize(cols*(self.S+self.G)+self.G, rows*(self.S+self.G)+self.G)

    # Returns pixel rect for a cell
    def rect_of(self, r, c):
        return QRect(self.G+c*(self.S+self.G), self.G+r*(self.S+self.G), self.S, self.S)

    # Returns (row, col) from pixel coords
    def cell_of(self, x, y):
        c, r = int(x)//(self.S+self.G), int(y)//(self.S+self.G)
        return (r, c) if 0<=r<self.rows and 0<=c<self.cols else None

    # Resets everything to blank
    def reset(self):
        self.grid = [[EMPTY]*self.cols for _ in range(self.rows)]
        self.person = None
        self.overlay.clear()
        self.update()

    # Paints all cells, overlays, and person
    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), COLORS["grid"])
        for r in range(self.rows):
            for c in range(self.cols):
                rc = self.rect_of(r, c)
                if (r,c) in self.overlay:
                    p.fillRect(rc, self.overlay[(r,c)])
                else:
                    p.fillRect(rc, COLORS[self.grid[r][c]])
                if self.grid[r][c] == EXIT:
                    p.setPen(Qt.white); p.drawText(rc, Qt.AlignCenter, "E")
        if self.person:
            rc = self.rect_of(*self.person)
            p.fillRect(rc, COLORS["person"])
            p.setPen(Qt.white); p.drawText(rc, Qt.AlignCenter, "P")

    # Handles mouse drawing on the grid
    def mousePressEvent(self, e): self._draw(e)
    def mouseMoveEvent(self, e): self._draw(e)

    def _draw(self, e):
        cell = self.cell_of(e.position().x(), e.position().y())
        if not cell: return
        r, c = cell
        if e.buttons() & Qt.RightButton:
            self.grid[r][c] = EMPTY; self.overlay.pop((r,c), None)
        elif e.buttons() & Qt.LeftButton:
            if self.mode == "person":
                if self.grid[r][c] == EMPTY: self.person = (r, c)
            else:
                self.grid[r][c] = {"wall":WALL,"erase":EMPTY,"fire":FIRE,"exit":EXIT}[self.mode]
                self.overlay.pop((r,c), None)
        self.update()


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fire Evacuation")
        self._saved, self._steps, self._idx, self._pstats = None, [], 0, None
        self._atimer = QTimer(self, timeout=self._step)
        self._ftimer = QTimer(self, timeout=self._fire)
        self.status = QStatusBar(); self.setStatusBar(self.status)
        self._build()

    # Builds the full UI layout
    def _build(self):
        root = QWidget(); self.setCentralWidget(root)
        h = QHBoxLayout(root); h.setContentsMargins(12,12,12,12); h.setSpacing(12)

        self.grid = Grid(); h.addWidget(self.grid)

        v = QVBoxLayout(); v.setSpacing(8); v.setAlignment(Qt.AlignTop); h.addLayout(v)

        v.addWidget(QLabel("<b>Draw tool</b>"))
        row = QHBoxLayout()
        self._btns = {}
        for m in MODES:
            b = QPushButton(m.title()); b.setCheckable(True)
            b.clicked.connect(lambda _, x=m: self._mode(x))
            self._btns[m] = b; row.addWidget(b)
        v.addLayout(row)

        v.addWidget(QLabel("<b>Algorithm</b>"))
        self.algo = QComboBox()
        self.algo.addItems(["BFS — shortest", "DFS — any path", "Both"])
        v.addWidget(self.algo)

        for label, slot in [("Run", self._run), ("Reset paths", self._reset), ("Clear all", self._clear)]:
            b = QPushButton(label); b.clicked.connect(slot); v.addWidget(b)

        self.info = QLabel("Place P and E, then Run."); self.info.setWordWrap(True)
        v.addWidget(self.info)

        self._mode("wall")

    # Sets the active drawing mode and highlights the button
    def _mode(self, m):
        self.grid.mode = m
        for k, b in self._btns.items(): b.setChecked(k == m)
        self.status.showMessage(f"Mode: {m}")

    # Clears the whole grid
    def _clear(self):
        self._atimer.stop(); self._ftimer.stop()
        self.grid.reset(); self._saved = None; self.info.setText("Cleared.")

    # Restores grid to pre-run state and removes overlays
    def _reset(self):
        self._atimer.stop(); self._ftimer.stop()
        if self._saved: self.grid.grid = copy.deepcopy(self._saved)
        self.grid.overlay.clear(); self.grid.update(); self.info.setText("Reset.")

    # Validates, then runs the selected algorithm(s)
    def _run(self):
        if not self.grid.person: self.info.setText("No person set."); return
        if not any(self.grid.grid[r][c]==EXIT for r in range(self.grid.rows) for c in range(self.grid.cols)):
            self.info.setText("No exit set."); return
        self._atimer.stop(); self._ftimer.stop()
        self._saved = copy.deepcopy(self.grid.grid)
        self.grid.overlay.clear()
        idx = self.algo.currentIndex()
        if idx == 0: self._queue("bfs")
        elif idx == 1: self._queue("dfs")
        else: self._both()
        self._ftimer.start(800)

    # Runs one algorithm and queues animation steps
    def _queue(self, algo):
        fn = bfs if algo == "bfs" else dfs
        path, exp, t = fn(copy.deepcopy(self._saved), self.grid.person)
        ec = COLORS["exp_bfs" if algo=="bfs" else "exp_dfs"]
        pc = COLORS["path_bfs" if algo=="bfs" else "path_dfs"]
        self._steps = [(c, ec) for c in exp] + [(c, pc) for c in (path or [])]
        self._idx = 0
        self._pstats = (algo.upper(), len(exp), len(path) if path else 0, t, path is not None)
        self._atimer.start(30)

    # Runs both algorithms and interleaves their steps
    def _both(self):
        s = self.grid.person
        pb, eb, tb = bfs(copy.deepcopy(self._saved), s)
        pd, ed, td = dfs(copy.deepcopy(self._saved), s)
        steps = []
        for i in range(max(len(eb), len(ed))):
            if i < len(eb): steps.append((eb[i], COLORS["exp_bfs"]))
            if i < len(ed): steps.append((ed[i], COLORS["exp_dfs"]))
        for c in (pb or []): steps.append((c, COLORS["path_bfs"]))
        for c in (pd or []): steps.append((c, COLORS["path_dfs"]))
        self._steps, self._idx, self._pstats = steps, 0, None
        self._atimer.start(30)
        self.info.setText(f"BFS: {len(pb or [])} steps\nDFS: {len(pd or [])} steps")

    # Advances animation by one cell per tick
    def _step(self):
        if self._idx >= len(self._steps):
            self._atimer.stop()
            if self._pstats:
                a, ex, pl, t, found = self._pstats
                self.info.setText(f"{a}: {'found' if found else 'no route'}\nPath: {pl}  Explored: {ex}\nTime: {t*1000:.2f}ms")
            return
        (r,c), col = self._steps[self._idx]
        if self.grid.grid[r][c] not in (FIRE,EXIT) and (r,c) != self.grid.person:
            self.grid.overlay[(r,c)] = col; self.grid.update()
        self._idx += 1

    # Spreads fire one step and repaints
    def _fire(self):
        self.grid.grid = spread_fire(self.grid.grid, 1); self.grid.update()
