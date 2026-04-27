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

# Four-directional movement: left, down, right, up
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


def spread_fire(grid, steps=44):
    import copy

    new_grid = copy.deepcopy(grid)

    number_of_rows = len(new_grid)
    number_of_cols = len(new_grid[0])

    for current_step in range(steps):

        fire_positions = []

        for row_index in range(number_of_rows):
            for col_index in range(number_of_cols):

                if new_grid[row_index][col_index] == FIRE:
                    fire_positions.append((row_index, col_index))

                col_index += 1
            row_index += 1

        for r,c in fire_positions:
            current_row = r
            current_col = c

            for r,c in directions:
                new_row = current_row + r
                new_col = current_col + c

                inside_rows = (0 <= new_row < number_of_rows)
                inside_cols = (0 <= new_col < number_of_cols)

                if inside_rows and inside_cols and new_grid[new_row][new_col] == EMPTY:
                        new_grid[new_row][new_col] = FIRE

        current_step += 1

    return new_grid


def _reconstruct(parent, node):
    """Walk parent pointers back to build the path from start → exit."""
    path = []
    while node is not None:
        path.append(node)
        node = parent[node]
    return path[::-1]
