from collections import deque

# --- CẤU TRÚC VÀ KHÁI NIỆM ---
# Mỗi trạng thái được mô tả bởi:
#   - pos: vị trí người chơi (x, y)
#   - bag: tuple các vật phẩm hiện có trong túi (giữ thứ tự theo hàng đợi)
#   - objects: frozenset các vị trí (x, y) trên map còn chứa vật phẩm
#
# Không gian trạng thái ban đầu (S0):
#   - pos = start_pos (từ game hiện tại)
#   - bag = tuple(bag hiện tại)
#   - objects = tập tất cả tọa độ ô chứa int trong map_tiles
#
# Không gian trạng thái kết thúc (goal):
#   - Trong khi tìm combo: xuất hiện một combo hợp lệ (theo COMBO_RULES và số ô trống)
#     tức là bag mới chứa segment liên tiếp đúng loại và đúng số lượng.
#   - Nếu không tìm được combo trong max_depth, ta fallback sang nhặt vật gần nhất.

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

def _allowed_combo_objs(empty_slots):
    """
    Dựa trên số ô trống trong túi, trả về danh sách obj có thể tạo combo.
    """
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
    else:
        return []

def _check_combo_sim(bag, allowed_objs):
    """
    Kiểm tra xem bag (tuple) có chứa segment combo hợp lệ cho bất kỳ obj nào trong allowed_objs.
    Trả về True nếu tìm thấy.
    """
    n = len(bag)
    for obj in allowed_objs:
        need, _ = COMBO_RULES[obj]
        if n < need:
            continue
        for i in range(n - need + 1):
            if all(bag[i+j] == obj for j in range(need)):
                return True
    return False

def _dfs_find_combo(map_tiles, start_pos, bag, max_depth):
    """
    DFS giới hạn độ sâu max_depth để tìm đường tới trạng thái có combo.
    Trả về list of (direction, pos) nếu tìm được, ngược lại [].
    """
    rows = len(map_tiles)
    cols = len(map_tiles[0])
    
    # Tập các vị trí còn chứa object
    initial_objects = frozenset(
        (x, y)
        for y in range(rows)
        for x in range(cols)
        if isinstance(map_tiles[y][x], int)
    )
    
    start_state = (start_pos, tuple(bag), initial_objects)
    
    # Stack dùng để DFS: mỗi phần tử là (state, path)
    stack = []
    stack.append((start_state, []))
    
    visited = set()
    visited.add(start_state)
    
    while stack:
        (pos, bag_tup, objects), path = stack.pop()
        
        # Giới hạn độ sâu
        if len(path) > max_depth:
            continue
        
        empty_slots = BAG_SIZE - len(bag_tup)
        allowed = _allowed_combo_objs(empty_slots)
        if _check_combo_sim(bag_tup, allowed):
            return path  # Đã tìm được combo
        
        x0, y0 = pos
        for dir_name, (dx, dy) in DIRECTIONS:
            nx, ny = x0 + dx, y0 + dy
            
            if not (0 <= nx < cols and 0 <= ny < rows):
                continue
            cell = map_tiles[ny][nx]
            if isinstance(cell, str) and cell != ' ':
                continue
            
            new_bag = list(bag_tup)
            new_objects = objects
            # Nếu có object ở ô mới
            if (nx, ny) in objects:
                val = map_tiles[ny][nx]
                # Nếu đã có vật trong túi, chỉ cho phép nhặt nếu nó cùng loại với phần tử đầu tiên (hoặc có thể dùng bag[-1] tùy chiến lược)
                if new_bag:
                    candidate = new_bag[0]
                    if val != candidate:
                        continue
                else:
                    if val not in allowed:
                        continue
                new_bag.append(val)
                if len(new_bag) > BAG_SIZE:
                    new_bag.pop(0)
                new_objects = objects.difference({(nx, ny)})
            
            new_state = ((nx, ny), tuple(new_bag), new_objects)
            if new_state in visited:
                continue
            visited.add(new_state)
            stack.append((new_state, path + [(dir_name, (nx, ny))]))
    
    return []

def _dfs_nearest_target(map_tiles, start_pos, target_vals):
    """
    DFS để tìm đường (không tối ưu về độ dài) tới ô chứa giá trị trong target_vals.
    Đảm bảo không nhặt vật phẩm khác trên đường đi.
    Trả về path list hoặc [] nếu không tìm.
    """
    rows = len(map_tiles)
    cols = len(map_tiles[0])
    
    # Stack cho DFS: (position, path)
    stack = []
    stack.append((start_pos, []))
    visited = set([start_pos])
    
    while stack:
        (x0, y0), path = stack.pop()
        cell = map_tiles[y0][x0]
        if isinstance(cell, int) and cell in target_vals:
            return path  # Đã tìm thấy ô mục tiêu
        
        for dir_name, (dx, dy) in DIRECTIONS:
            nx, ny = x0 + dx, y0 + dy
            if not (0 <= nx < cols and 0 <= ny < rows):
                continue
            c = map_tiles[ny][nx]
            if isinstance(c, str) and c != ' ':
                continue
            # Nếu ô có vật phẩm nhưng không thuộc target, không được nhặt
            if isinstance(c, int) and c not in target_vals:
                continue
            if (nx, ny) in visited:
                continue
            visited.add((nx, ny))
            stack.append(((nx, ny), path + [(dir_name, (nx, ny))]))
    
    return []

def dfs_search(map_tiles, start_pos, bag, max_depth=50):
    """
    Tìm đường cho AI theo DFS:
    1) Thử tìm combo trong max_depth bước.
    2) Nếu không tìm được, fallback:
       - Nếu bag rỗng: nhặt bất kỳ vật nào (0..4)
       - Nếu bag không rỗng: nhặt vật cùng loại với item VỪA MỚI ĐƯỢC THÊM vào trong bag.
    """
    combo_path = _dfs_find_combo(map_tiles, start_pos, bag, max_depth)
    if combo_path:
        return combo_path

    # 2) Fallback: tìm nearest
    rows = len(map_tiles)
    cols = len(map_tiles[0])
    # Xác định target_vals dựa trên túi
    if not bag:
        target_vals = [0,1,2,3,4]
    else:
        last = bag[-1]
        # Kiểm tra xem map còn object cùng loại last hay không
        exists_same = any(
            isinstance(map_tiles[y][x], int) and map_tiles[y][x] == last
            for y in range(rows)
            for x in range(cols)
        )
        if exists_same:
            target_vals = [last]
        else:
            # Nếu không còn, nhặt gần nhất bất kỳ
            target_vals = [0,1,2,3,4]
    
    return _dfs_nearest_target(map_tiles, start_pos, target_vals)
