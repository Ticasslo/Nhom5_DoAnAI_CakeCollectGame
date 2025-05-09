from collections import deque

# --- CẤU TRÚC VÀ KHÁI NIỆM TRONG SEARCH ---
# Backtracking with Forward Checking:
# - Backtracking: Thuật toán tìm kiếm theo chiều sâu, thử từng khả năng và quay lui khi không thỏa
# - Forward Checking: Kỹ thuật kiểm tra trước các ràng buộc để loại bỏ sớm các lựa chọn không khả thi

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
    Dựa trên số ô trống trong túi, trả về danh sách obj có thể tạo combo:
    - empty >=6: [0,1,2,3,4]
    - empty ==5: [0,1,2,3]
    - empty ==4: [0,1,2]
    - empty ==3: [0,1]
    - empty ==2: [0]
    - else: []
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
    Trả về True ngay khi tìm thấy.
    """
    n = len(bag)
    for obj in allowed_objs:
        need, _ = COMBO_RULES[obj]
        if n < need:
            continue
        # Duyệt các segment độ dài need
        for i in range(n - need + 1):
            if all(bag[i+j] == obj for j in range(need)):
                return True
    return False


def _is_promising(map_tiles, pos, bag, objects, allowed_objs, target_obj=None):
    """
    Forward Checking: Kiểm tra xem trạng thái hiện tại có khả năng dẫn tới combo không.
    
    Tham số:
        map_tiles: Bản đồ
        pos: Vị trí hiện tại (x, y)
        bag: Túi đồ hiện tại
        objects: Các vị trí còn chứa object
        allowed_objs: Các loại object được phép tạo combo
        target_obj: Object đích cần nhặt (nếu có)
    
    Trả về:
        bool: True nếu trạng thái này có tiềm năng dẫn tới combo, False nếu không
    """
    if _check_combo_sim(bag, allowed_objs):
        return True  # Đã có combo
    
    # Nếu có target_obj, kiểm tra xem có thể tìm thấy đường đi đến một object loại target_obj nữa không
    if target_obj is not None:
        # Kiểm tra xem còn object loại target_obj trên bản đồ không
        found = False
        for x, y in objects:
            if map_tiles[y][x] == target_obj:
                found = True
                break
        
        if not found:
            return False  # Không còn object cùng loại
    
    # Kiểm tra xem còn đủ object cùng loại để tạo combo không
    if bag:
        # Nếu đã có vật phẩm trong túi, kiểm tra xem có khả năng tạo combo không
        obj_type = bag[0]  # Lấy loại của vật phẩm đầu tiên (hoặc vật phẩm cuối)
        need, _ = COMBO_RULES[obj_type]
        
        # Đếm số vật phẩm cùng loại trong túi
        same_type_count = sum(1 for item in bag if item == obj_type)
        
        # Đếm số vật phẩm cùng loại còn lại trên bản đồ
        map_same_type = sum(1 for x, y in objects if map_tiles[y][x] == obj_type)
        
        # Nếu tổng số vật phẩm hiện có và trên bản đồ không đủ để tạo combo
        if same_type_count + map_same_type < need:
            return False
    
    return True  # Các trường hợp khác có thể có tiềm năng


def _backtrack_find_combo(map_tiles, start_pos, bag, max_depth):
    """
    Sử dụng backtracking với forward checking để tìm đường tới trạng thái có combo.
    Trả về list of (direction, pos) nếu tìm được, ngược lại []
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
    
    # Khởi tạo trạng thái đầu và đường đi
    stack = [(start_pos, tuple(bag), initial_objects, [], 0)]
    visited = set([(start_pos, tuple(bag), initial_objects)])
    
    best_path = None
    
    while stack:
        pos, bag_tup, objects, path, depth = stack.pop()
        
        # Giới hạn độ sâu
        if depth > max_depth:
            continue
        
        # Tính số ô trống trong túi
        empty_slots = BAG_SIZE - len(bag_tup)
        allowed = _allowed_combo_objs(empty_slots)
        
        # Kiểm tra goal: combo
        if _check_combo_sim(bag_tup, allowed):
            # Nếu tìm thấy combo, trả về đường đi
            return path
        
        # Forward Checking: Kiểm tra xem trạng thái hiện tại có tiềm năng dẫn tới combo không
        target_obj = bag_tup[0] if bag_tup else None
        if not _is_promising(map_tiles, pos, bag_tup, objects, allowed, target_obj):
            continue
        
        # Mở rộng các bước kế tiếp
        x0, y0 = pos
        
        # Xem xét tất cả các hướng di chuyển
        for dir_name, (dx, dy) in DIRECTIONS:
            nx, ny = x0 + dx, y0 + dy
            
            # Kiểm tra hợp lệ trong map và không phải wall
            if not (0 <= nx < cols and 0 <= ny < rows):
                continue
            cell = map_tiles[ny][nx]
            if isinstance(cell, str) and cell != ' ':
                # wall hoặc chướng ngại khác
                continue
            
            # Tạo state mới
            new_bag = list(bag_tup)
            new_objects = objects
            
            # Nếu có object ở ô mới
            if (nx, ny) in objects:
                val = map_tiles[ny][nx]
                
                # Forward checking: Kiểm tra điều kiện trước khi nhặt
                if new_bag:
                    # Nếu đã có vật phẩm trong túi, chỉ nhặt cùng loại
                    candidate = new_bag[0]
                    if val != candidate:
                        continue  # Bỏ qua vì không được nhặt vật phẩm khác loại
                else:
                    # Nếu túi rỗng, kiểm tra xem loại vật phẩm có nằm trong danh sách cho phép không
                    if val not in allowed:
                        continue  # Bỏ qua vì loại vật phẩm không được phép
                
                # Thêm vật phẩm vào túi
                new_bag.append(val)
                if len(new_bag) > BAG_SIZE:
                    new_bag.pop(0)
                
                # Loại bỏ vật phẩm khỏi bản đồ
                new_objects = objects.difference({(nx, ny)})
            
            # Tạo trạng thái mới và kiểm tra đã thăm chưa
            new_state = ((nx, ny), tuple(new_bag), new_objects)
            if new_state in visited:
                continue
            
            visited.add(new_state)
            stack.append((
                (nx, ny),
                tuple(new_bag),
                new_objects,
                path + [(dir_name, (nx, ny))],
                depth + 1
            ))
    
    return []  # Không tìm thấy đường đi đến combo


def _calculate_manhattan_distance(pos1, pos2):
    """
    Tính khoảng cách Manhattan giữa hai điểm
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def _reconstruct_path(came_from, current_pos):
    """
    Tạo lại đường đi từ điểm bắt đầu đến điểm hiện tại
    """
    path = []
    while current_pos in came_from:
        direction, prev_pos = came_from[current_pos]
        path.append((direction, current_pos))
        current_pos = prev_pos
    
    return path[::-1]  # Đảo ngược để có thứ tự từ đầu đến cuối


def _backtrack_nearest_target(map_tiles, start_pos, target_vals):
    """
    Tìm đường ngắn nhất tới vật phẩm mục tiêu.
    Kết hợp A* để tìm đường ngắn nhất với forward checking để loại sớm các đường đi không hợp lệ.
    """
    rows = len(map_tiles)
    cols = len(map_tiles[0])
    
    # Danh sách các điểm đến (vị trí các vật phẩm mục tiêu)
    target_positions = []
    for y in range(rows):
        for x in range(cols):
            if isinstance(map_tiles[y][x], int) and map_tiles[y][x] in target_vals:
                target_positions.append((x, y))
    
    if not target_positions:
        return []  # Không có vật phẩm mục tiêu nào
    
    # Sử dụng A* để tìm đường đi ngắn nhất
    open_set = deque([(start_pos, 0)])  # (pos, cost)
    came_from = {}  # Lưu lại đường đi
    cost_so_far = {start_pos: 0}  # Chi phí đến mỗi điểm
    
    while open_set:
        current_pos, current_cost = open_set.popleft()
        
        # Nếu đến đích (vật phẩm mục tiêu)
        x, y = current_pos
        if isinstance(map_tiles[y][x], int) and map_tiles[y][x] in target_vals:
            return _reconstruct_path(came_from, current_pos)
        
        # Xét các hướng di chuyển
        for dir_name, (dx, dy) in DIRECTIONS:
            nx, ny = x + dx, y + dy
            next_pos = (nx, ny)
            
            # Kiểm tra hợp lệ
            if not (0 <= nx < cols and 0 <= ny < rows):
                continue
            
            cell = map_tiles[ny][nx]
            # Bỏ qua ô tường
            if isinstance(cell, str) and cell != ' ':
                continue
            
            # Forward checking: Kiểm tra nếu ô chứa vật phẩm không nằm trong target_vals
            if isinstance(cell, int) and cell not in target_vals:
                continue  # Bỏ qua vì không được nhặt vật phẩm khác loại
            
            # Tính toán chi phí mới
            new_cost = current_cost + 1
            
            # Nếu vị trí mới chưa được thăm hoặc chi phí mới tốt hơn
            if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                cost_so_far[next_pos] = new_cost
                
                # Sắp xếp theo khoảng cách Manhattan đến target gần nhất
                priority = new_cost + min(_calculate_manhattan_distance(next_pos, target) for target in target_positions)
                
                # Thêm vào open_set theo thứ tự ưu tiên
                # (Đơn giản hóa bằng cách dùng deque, không phải priority queue)
                open_set.append((next_pos, new_cost))
                
                # Lưu lại đường đi
                came_from[next_pos] = (dir_name, current_pos)
    
    return []  # Không tìm thấy đường đi


def backtracking_with_forward_checking(map_tiles, start_pos, bag, max_depth=70):
    """
    Tìm đường cho AI sử dụng backtracking với forward checking:
    1) Thử tìm combo trong max_depth bước.
    2) Nếu không tìm được, fallback:
       - Nếu bag rỗng: nhặt bất kỳ vật gần nhất
       - Nếu bag không rỗng: nhặt vật cùng loại với item vừa được thêm vào túi
    """
    # 1) Tìm combo
    combo_path = _backtrack_find_combo(map_tiles, start_pos, bag, max_depth)
    if combo_path:
        return combo_path
    
    # 2) Fallback: tìm nearest
    rows = len(map_tiles)
    cols = len(map_tiles[0])
    
    # Xác định target_vals dựa trên túi
    if not bag:
        target_vals = [0, 1, 2, 3, 4]
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
            target_vals = [0, 1, 2, 3, 4]
    
    return _backtrack_nearest_target(map_tiles, start_pos, target_vals)
