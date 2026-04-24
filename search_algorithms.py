"""
search_algorithms.py — BFS and DFS for Fire Evacuation
Grid values:
    0 = wall
    1 = empty / passable
    2 = fire  (blocks movement)
    3 = exit  (goal)
Returns: (path, explored_list, elapsed_seconds)
"""
import time
from collections import deque

# Four-directional movement: up, down, left, right
directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]

WALL  = 0
EMPTY = 1
FIRE  = 2
EXIT  = 3


def bfs(grid, start):
    """
    Breadth-First Search — guarantees the shortest escape path.
    Explores level by level; first exit reached = nearest exit.
    Returns: (path, explored_list, elapsed_seconds)
    """
    t0 = time.time()
    rows = len(grid)
    cols = len(grid[0])

    Q = deque([start])
    visited = {start}
    parent = {start: None}
    explored = []

    while Q:
        curr = Q.popleft()
        explored.append(curr)
        r, c = curr

        if grid[r][c] == EXIT:
            return _reconstruct(parent, curr), explored, time.time() - t0

        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            neighbor = (nr, nc)
            if (
                0 <= nr < rows
                and 0 <= nc < cols
                and grid[nr][nc] != WALL
                and grid[nr][nc] != FIRE
                and neighbor not in visited
            ):
                visited.add(neighbor)
                parent[neighbor] = curr
                Q.append(neighbor)

    return None, explored, time.time() - t0   # no exit reachable


def dfs(grid, start):
    """
    Depth-First Search — finds an escape path but NOT guaranteed shortest.
    Dives deep before backtracking; useful to check if any exit exists.
    Returns: (path, explored_list, elapsed_seconds)
    """
    t0 = time.time()
    rows = len(grid)
    cols = len(grid[0])

    stack = [start]
    visited = {start}
    parent = {start: None}
    explored = []

    while stack:
        curr = stack.pop()
        explored.append(curr)
        r, c = curr

        if grid[r][c] == EXIT:
            return _reconstruct(parent, curr), explored, time.time() - t0

        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            neighbor = (nr, nc)
            if (
                0 <= nr < rows
                and 0 <= nc < cols
                and grid[nr][nc] != WALL
                and grid[nr][nc] != FIRE
                and neighbor not in visited
            ):
                visited.add(neighbor)
                parent[neighbor] = curr
                stack.append(neighbor)

    return None, explored, time.time() - t0


def spread_fire(grid, steps=1):
    """
    Spreads fire outward by `steps` cells (BFS expansion).
    Fire does not spread through walls.
    Returns a new grid with updated fire positions.
    """
    import copy
    g = copy.deepcopy(grid)
    rows, cols = len(g), len(g[0])

    for _ in range(steps):
        sources = [
            (r, c)
            for r in range(rows)
            for c in range(cols)
            if g[r][c] == FIRE
        ]
        for r, c in sources:
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and g[nr][nc] == EMPTY:
                    g[nr][nc] = FIRE

    return g


def _reconstruct(parent, node):
    """Walk parent pointers back to build the path from start → exit."""
    path = []
    while node is not None:
        path.append(node)
        node = parent[node]
    return path[::-1]