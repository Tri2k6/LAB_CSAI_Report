"""Check the current A* heuristic against exact remaining costs on 15 levels.

Run from any directory: python3 Report/scripts/verify_current_heuristic.py
This reads the frozen solver and level files; it does not run benchmarks or
write source, tests, CSV, or report data.
"""

import sys
from collections import deque
from heapq import heappop, heappush
from itertools import count
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "TH_AI_LABS_1"
sys.path.insert(0, str(SOURCE_ROOT))

from bloxorz.core.game_engine import GameEngine
from bloxorz.core.level_loader import load_level
from bloxorz.solvers.costs import standard_step_cost
from bloxorz.solvers.heuristics import bloxorz_admissible_heuristic


def check_level(path: Path) -> tuple[int, int, int, float]:
    engine = GameEngine(load_level(path))
    start = engine.get_initial_state()
    visited = {start}
    queue = deque([start])
    reverse = {}
    edges = 0
    while queue:
        state = queue.popleft()
        for action, next_state in engine.get_successors(state):
            step_cost = standard_step_cost(state, action, next_state, engine)
            reverse.setdefault(next_state, []).append((state, step_cost))
            edges += 1
            if next_state not in visited:
                visited.add(next_state)
                queue.append(next_state)

    tie_breaker = count()
    distances = {}
    heap = []
    for state in visited:
        if engine.is_goal(state):
            distances[state] = 0.0
            heappush(heap, (0.0, next(tie_breaker), state))
    while heap:
        distance, _, state = heappop(heap)
        if distance > distances[state]:
            continue
        for predecessor, step_cost in reverse.get(state, ()):
            candidate = distance + step_cost
            if candidate < distances.get(predecessor, float("inf")):
                distances[predecessor] = candidate
                heappush(heap, (candidate, next(tie_breaker), predecessor))

    max_excess = float("-inf")
    for state, optimal_remaining in distances.items():
        excess = bloxorz_admissible_heuristic(state, engine) - optimal_remaining
        max_excess = max(max_excess, excess)
        if excess > 1e-9:
            raise AssertionError((path.name, state, excess))
    return len(visited), len(distances), edges, max_excess


totals = [0, 0, 0]
max_excess = float("-inf")
level_paths = sorted((SOURCE_ROOT / "levels").glob("level_*.json"))
if len(level_paths) != 15:
    raise RuntimeError(f"Expected 15 levels, found {len(level_paths)}")
for level_path in level_paths:
    reachable, solvable, edges, excess = check_level(level_path)
    print(level_path.name, reachable, solvable, edges, excess, flush=True)
    for index, value in enumerate((reachable, solvable, edges)):
        totals[index] += value
    max_excess = max(max_excess, excess)
print("TOTAL", *totals, "MAX_EXCESS", max_excess)
