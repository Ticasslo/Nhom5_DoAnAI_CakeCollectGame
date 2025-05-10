import random
from collections import defaultdict
import heapq
from typing import List, Tuple, FrozenSet, Dict, Set

# Quy tắc combo và kích thước túi
COMBO_RULES = {
    0: (2, 200),
    1: (3, 300),
    2: (4, 400),
    3: (5, 500),
    4: (6, 600),
}
BAG_SIZE = 7

# Các hướng di chuyển: tên và vector (dx, dy)
DIRECTIONS = [
    ("Up", (0, -1)),
    ("Down", (0, 1)),
    ("Left", (-1, 0)),
    ("Right", (1, 0)),
]

def _allowed_combo_objs(empty_slots: int) -> List[int]:
    if empty_slots >= 6:
        return [0, 1, 2, 3, 4]
    elif empty_slots == 5:
        return [0, 1, 2, 3]
    elif empty_slots == 4:
        return [0, 1, 2]
    elif empty_slots == 3:
        return [0, 1]
    elif empty_slots == 2:
        return [0]
    return []

def _check_combo_sim(bag: Tuple[int, ...], allowed_objs: List[int]) -> bool:
    n = len(bag)
    for obj in allowed_objs:
        need, _ = COMBO_RULES[obj]
        if n < need:
            continue
        for i in range(n - need + 1):
            if all(bag[i + j] == obj for j in range(need)):
                return True
    return False

def _calculate_manhattan_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def _heuristic(state: Tuple[Tuple[int, int], Tuple[int, ...], FrozenSet[Tuple[int, int]]], 
              map_tiles: List[List[int | str]], 
              target_type: int | None) -> float:
    pos, bag_tup, objects = state
    empty_slots = BAG_SIZE - len(bag_tup)
    allowed_objs = _allowed_combo_objs(empty_slots)
    
    if _check_combo_sim(bag_tup, allowed_objs):
        return 0.0 
    
    penalty = 0.0
    if target_type is not None:
        for obj_pos in objects:
            if map_tiles[obj_pos[1]][obj_pos[0]] != target_type:
                dist = _calculate_manhattan_distance(pos, obj_pos)
                if dist < 3:
                    penalty += 10.0 / (dist + 1)
    
    if bag_tup:
        obj_type = bag_tup[0]
        count = sum(1 for x in bag_tup if x == obj_type)
        need, _ = COMBO_RULES[obj_type]
        remaining_same_type = sum(1 for obj_pos in objects if map_tiles[obj_pos[1]][obj_pos[0]] == obj_type)
        
        if count + remaining_same_type >= need:
            progress = count / need
            min_dist = float('inf')
            for obj_pos in objects:
                if map_tiles[obj_pos[1]][obj_pos[0]] == obj_type:
                    dist = _calculate_manhattan_distance(pos, obj_pos)
                    min_dist = min(min_dist, dist)
            return (1 - progress) * min_dist + (need - count) + penalty
    
    min_dist = float('inf')
    for obj_pos in objects:
        if target_type is None or map_tiles[obj_pos[1]][obj_pos[0]] == target_type:
            dist = _calculate_manhattan_distance(pos, obj_pos)
            min_dist = min(min_dist, dist)
    return (min_dist if min_dist != float('inf') else 100.0) + penalty

def _get_valid_neighbors(state: Tuple[Tuple[int, int], Tuple[int, ...], FrozenSet[Tuple[int, int]]], 
                        map_tiles: List[List[int | str]], 
                        allowed_objs: List[int] = None, 
                        target_type: int | None = None) -> List[Tuple[str, Tuple[Tuple[int, int], Tuple[int, ...], FrozenSet[Tuple[int, int]]], bool]]:
    pos, bag_tup, objects = state
    rows, cols = len(map_tiles), len(map_tiles[0])
    x0, y0 = pos
    neighbors = []
    
    for dir_name, (dx, dy) in DIRECTIONS:
        nx, ny = x0 + dx, y0 + dy
        if not (0 <= nx < cols and 0 <= ny < rows):
            continue
        cell = map_tiles[ny][nx]
        if isinstance(cell, str) and cell != ' ':
            continue
        
        new_state = ((nx, ny), bag_tup, objects)
        neighbors.append((dir_name, new_state, False))
        
        if (nx, ny) in objects:
            val = map_tiles[ny][nx]
            if bag_tup and target_type is not None and val != target_type:
                continue
            if allowed_objs and val not in allowed_objs:
                continue
            
            new_bag = list(bag_tup) + [val]
            if len(new_bag) > BAG_SIZE:
                new_bag.pop(0)
            new_objects = objects.difference({(nx, ny)})
            new_state = ((nx, ny), tuple(new_bag), new_objects)
            neighbors.append((dir_name, new_state, True))
    
    return neighbors

def _ao_star_find_combo(map_tiles: List[List[int | str]], 
                       start_pos: Tuple[int, int], 
                       bag: List[int], 
                       max_depth: int) -> List[Tuple[str, Tuple[int, int]]]:
    initial_objects = frozenset(
        (x, y) for y in range(len(map_tiles)) for x in range(len(map_tiles[0]))
        if isinstance(map_tiles[y][x], int)
    )
    start_state = (start_pos, tuple(bag), initial_objects)
    target_type = bag[-1] if bag else None
    
    graph: Dict[Tuple, Dict] = {start_state: {'cost': float('inf'), 'solved': False, 'connectors': [], 'path': []}}
    graph[start_state]['cost'] = _heuristic(start_state, map_tiles, target_type)
    
    open_set = [(graph[start_state]['cost'], 0, start_state)]
    heapq.heapify(open_set)
    
    while open_set:
        _, depth, state = heapq.heappop(open_set)
        if depth >= max_depth or graph[state]['solved']:
            continue
        
        pos, bag_tup, objects = state
        empty_slots = BAG_SIZE - len(bag_tup)
        allowed_objs = _allowed_combo_objs(empty_slots)
        
        if _check_combo_sim(bag_tup, allowed_objs):
            graph[state]['solved'] = True
            graph[state]['cost'] = depth
            return graph[state]['path']
        
        current_target = target_type if bag_tup and bag_tup[0] == target_type else (bag_tup[0] if bag_tup else None)
        neighbors = _get_valid_neighbors(state, map_tiles, allowed_objs, current_target)
        for dir_name, next_state, picked in neighbors:
            if next_state not in graph:
                graph[next_state] = {
                    'cost': float('inf'),
                    'solved': False,
                    'connectors': [],
                    'path': graph[state]['path'] + [(dir_name, next_state[0])]
                }
            graph[next_state]['connectors'].append((state, dir_name, picked))
            
            h = _heuristic(next_state, map_tiles, current_target)
            new_cost = depth + 1 + h
            if new_cost < graph[next_state]['cost']:
                graph[next_state]['cost'] = new_cost
                graph[next_state]['path'] = graph[state]['path'] + [(dir_name, next_state[0])]
                heapq.heappush(open_set, (new_cost, depth + 1, next_state))
        
        to_update = {state}
        while to_update:
            current = to_update.pop()
            if graph[current]['solved']:
                continue
            min_cost = float('inf')
            best_path = graph[current]['path']
            for parent, dir_name, _ in graph[current]['connectors']:
                parent_cost = graph[parent]['cost']
                if parent_cost < float('inf'):
                    new_cost = parent_cost + 1
                    if new_cost < min_cost:
                        min_cost = new_cost
                        best_path = graph[parent]['path'] + [(dir_name, current[0])]
            if min_cost < graph[current]['cost']:
                graph[current]['cost'] = min_cost
                graph[current]['path'] = best_path
                for parent, _, _ in graph[current]['connectors']:
                    to_update.add(parent)
    
    return []

def _ao_star_nearest_target(map_tiles: List[List[int | str]], 
                           start_pos: Tuple[int, int], 
                           target_vals: List[int], 
                           max_depth: int = 50) -> List[Tuple[str, Tuple[int, int]]]:
    rows, cols = len(map_tiles), len(map_tiles[0])
    target_positions = [
        (x, y) for y in range(rows) for x in range(cols)
        if isinstance(map_tiles[y][x], int) and map_tiles[y][x] in target_vals
    ]
    if not target_positions:
        return []
    
    graph: Dict[Tuple[int, int], Dict] = {
        start_pos: {'cost': float('inf'), 'solved': False, 'connectors': [], 'path': []}
    }
    min_dist = min(_calculate_manhattan_distance(start_pos, tp) for tp in target_positions)
    graph[start_pos]['cost'] = min_dist
    
    open_set = [(min_dist, 0, start_pos)]
    heapq.heapify(open_set)
    
    while open_set:
        _, depth, pos = heapq.heappop(open_set)
        if depth >= max_depth or graph[pos]['solved']:
            continue
        
        cell = map_tiles[pos[1]][pos[0]]
        if isinstance(cell, int) and cell in target_vals:
            graph[pos]['solved'] = True
            graph[pos]['cost'] = depth
            return graph[pos]['path']
        
        for dir_name, (dx, dy) in DIRECTIONS:
            nx, ny = pos[0] + dx, pos[1] + dy
            if not (0 <= nx < cols and 0 <= ny < rows):
                continue
            c = map_tiles[ny][nx]
            if isinstance(c, str) and c != ' ':
                continue
            if isinstance(c, int) and c not in target_vals:
                continue
            
            new_pos = (nx, ny)
            if new_pos not in graph:
                graph[new_pos] = {
                    'cost': float('inf'),
                    'solved': False,
                    'connectors': [],
                    'path': graph[pos]['path'] + [(dir_name, new_pos)]
                }
            graph[new_pos]['connectors'].append((pos, dir_name, False))
            
            new_dist = min(_calculate_manhattan_distance(new_pos, tp) for tp in target_positions)
            random_factor = random.uniform(0.9, 1.1)
            new_cost = depth + 1 + new_dist * random_factor
            if new_cost < graph[new_pos]['cost']:
                graph[new_pos]['cost'] = new_cost
                graph[new_pos]['path'] = graph[pos]['path'] + [(dir_name, new_pos)]
                heapq.heappush(open_set, (new_cost, depth + 1, new_pos))
        
        to_update = {pos}
        while to_update:
            current = to_update.pop()
            if graph[current]['solved']:
                continue
            min_cost = float('inf')
            best_path = graph[current]['path']
            for parent, dir_name, _ in graph[current]['connectors']:
                parent_cost = graph[parent]['cost']
                if parent_cost < float('inf'):
                    new_cost = parent_cost + 1
                    if new_cost < min_cost:
                        min_cost = new_cost
                        best_path = graph[parent]['path'] + [(dir_name, current)]
            if min_cost < graph[current]['cost']:
                graph[current]['cost'] = min_cost
                graph[current]['path'] = best_path
                for parent, _, _ in graph[current]['connectors']:
                    to_update.add(parent)
    
    return []

def nondeterministic_search(map_tiles: List[List[int | str]], 
                          start_pos: Tuple[int, int], 
                          bag: List[int], 
                          max_depth: int = 50) -> List[Tuple[str, Tuple[int, int]]]:
    combo_path = _ao_star_find_combo(map_tiles, start_pos, bag, max_depth)
    if combo_path:
        return combo_path
    
    rows, cols = len(map_tiles), len(map_tiles[0])
    if not bag:
        target_vals = [0, 1, 2, 3, 4]
    else:
        last = bag[-1]
        exists_same = any(
            isinstance(map_tiles[y][x], int) and map_tiles[y][x] == last
            for y in range(rows) for x in range(cols)
        )
        target_vals = [last] if exists_same else [0, 1, 2, 3, 4]
    
    return _ao_star_nearest_target(map_tiles, start_pos, target_vals)