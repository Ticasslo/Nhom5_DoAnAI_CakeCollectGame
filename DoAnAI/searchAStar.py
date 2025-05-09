import heapq
import math

# --- CẤU TRÚC VÀ KHÁI NIỆM TRONG SEARCH A* ---
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
        return [0,1,2,3,4]
    elif empty_slots == 5:
        return [0,1,2,3]
    elif empty_slots == 4:
        return [0,1,2]
    elif empty_slots == 3:
        return [0,1]
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


def _calculate_manhattan_distance(pos1, pos2):
    """
    Tính khoảng cách Manhattan giữa hai điểm
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def _calculate_heuristic(pos, bag, objects, map_tiles, target_obj=None):
    """
    Hàm heuristic cho A*:
    - Nếu target_obj được chỉ định (tức là đang tìm vật phẩm cụ thể), 
      trả về khoảng cách Manhattan đến vật phẩm gần nhất có loại target_obj
    - Nếu không, trả về khoảng cách Manhattan đến vật phẩm gần nhất bất kỳ
    """
    if not objects:  # Không còn vật phẩm nào
        return 0
    
    if target_obj is not None:
        # Tìm vật phẩm target_obj gần nhất
        target_objects = []
        for obj_pos in objects:
            x, y = obj_pos
            if map_tiles[y][x] == target_obj:
                target_objects.append(obj_pos)
        
        if not target_objects:  # Không còn vật phẩm loại target_obj
            # Fallback sang vật phẩm bất kỳ
            return min(_calculate_manhattan_distance(pos, obj_pos) for obj_pos in objects)
        
        return min(_calculate_manhattan_distance(pos, obj_pos) for obj_pos in target_objects)
    
    # Trả về khoảng cách đến vật phẩm gần nhất bất kỳ
    return min(_calculate_manhattan_distance(pos, obj_pos) for obj_pos in objects)


def _astar_find_combo(map_tiles, start_pos, bag, max_depth):
    """
    A* giới hạn độ sâu max_depth để tìm đường tới trạng thái có combo.
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
    
    start_state = (start_pos, tuple(bag), initial_objects)
    
    # Hàng đợi ưu tiên sử dụng heapq
    open_set = []
    
    # Mỗi phần tử trong open_set là (f_score, g_score, depth, state, path)
    # f_score = g_score + h_score, g_score là số bước đã đi, h_score là heuristic
    heapq.heappush(open_set, (0, 0, 0, start_state, []))
    
    # Lưu trữ các trạng thái đã duyệt và g_score tốt nhất
    best_g_scores = {start_state: 0}
    
    while open_set:
        f, g, depth, state, path = heapq.heappop(open_set)
        
        pos, bag_tup, objects = state
        
        # Giới hạn độ sâu
        if depth > max_depth:
            continue
        
        # Tính số ô trống
        empty_slots = BAG_SIZE - len(bag_tup)
        allowed = _allowed_combo_objs(empty_slots)
        
        # Kiểm tra goal: combo
        if _check_combo_sim(bag_tup, allowed):
            return path
        
        # Mở rộng các bước kế tiếp
        x0, y0 = pos
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
            new_depth = depth + 1
            
            # Nếu có object ở ô mới
            if (nx, ny) in objects:
                val = map_tiles[ny][nx]
                # Nếu đã có ít nhất một object trong chuỗi combo thì chỉ cho phép nhặt object cùng loại
                if new_bag:
                    candidate = new_bag[0]
                    if val != candidate:
                        continue  # Bỏ qua bước này vì không được đi qua object khác
                # Nếu chưa có object nào trong chuỗi thì object cần phải thuộc danh sách cho phép
                else:
                    if val not in allowed:
                        continue  # Bỏ qua object không thuộc danh sách cho phép
                        
                new_bag.append(val)
                if len(new_bag) > BAG_SIZE:
                    new_bag.pop(0)
                # Loại bỏ vị trí này khỏi tập objects
                new_objects = objects.difference({(nx, ny)})
            
            new_state = ((nx, ny), tuple(new_bag), new_objects)
            new_g = g + 1  # Tăng g_score lên 1 (mỗi bước đi có chi phí 1)
            
            # Nếu đã có đường đi tốt hơn đến state này thì bỏ qua
            if new_state in best_g_scores and best_g_scores[new_state] <= new_g:
                continue
                
            # Tính heuristic dựa trên vật phẩm hiện có trong túi
            target_obj = None
            if new_bag:
                target_obj = new_bag[-1]  # Vật phẩm vừa mới thêm vào
                
            h = _calculate_heuristic((nx, ny), tuple(new_bag), new_objects, map_tiles, target_obj)
            f = new_g + h
            
            # Cập nhật best_g_score và thêm vào open_set
            best_g_scores[new_state] = new_g
            heapq.heappush(open_set, (f, new_g, new_depth, new_state, path + [(dir_name, (nx, ny))]))
    
    return []


def _astar_nearest_target(map_tiles, start_pos, target_vals):
    """
    A* để tìm đường ngắn nhất tới ô chứa giá trị trong target_vals.
    Trả về path list hoặc [] nếu không tìm.
    Đảm bảo không nhặt vật phẩm khác trên đường đi.
    """
    rows = len(map_tiles)
    cols = len(map_tiles[0])
    
    # Tìm vị trí của tất cả các vật phẩm target_vals
    target_positions = []
    for y in range(rows):
        for x in range(cols):
            cell = map_tiles[y][x]
            if isinstance(cell, int) and cell in target_vals:
                target_positions.append((x, y))
    
    if not target_positions:
        return []  # Không có vật phẩm mục tiêu nào trên bản đồ
    
    # Sử dụng A* để tìm đường đi ngắn nhất
    open_set = []
    # Mỗi phần tử trong open_set là (f_score, g_score, pos, path)
    heapq.heappush(open_set, (0, 0, start_pos, []))
    
    # Lưu trữ chi phí g tốt nhất đến mỗi vị trí
    g_scores = {start_pos: 0}
    visited = set()
    
    while open_set:
        f, g, pos, path = heapq.heappop(open_set)
        
        # Nếu vị trí hiện tại là target
        x0, y0 = pos
        cell = map_tiles[y0][x0]
        if isinstance(cell, int) and cell in target_vals:
            return path
        
        # Nếu đã xét vị trí này rồi, bỏ qua
        if pos in visited:
            continue
        visited.add(pos)
        
        # Xét các hướng di chuyển
        for dir_name, (dx, dy) in DIRECTIONS:
            nx, ny = x0 + dx, y0 + dy
            
            # Kiểm tra hợp lệ
            if not (0 <= nx < cols and 0 <= ny < rows):
                continue
                
            c = map_tiles[ny][nx]
            # Bỏ qua ô là tường
            if isinstance(c, str) and c != ' ':
                continue
                
            # Bỏ qua ô chứa vật phẩm KHÔNG nằm trong target_vals
            if isinstance(c, int) and c not in target_vals:
                continue
                
            new_pos = (nx, ny)
            new_g = g + 1
            
            # Nếu đã có đường đi tốt hơn đến vị trí này thì bỏ qua
            if new_pos in g_scores and g_scores[new_pos] <= new_g:
                continue
                
            # Tính khoảng cách Manhattan đến vật phẩm target gần nhất
            h = min(_calculate_manhattan_distance(new_pos, target_pos) for target_pos in target_positions)
            f = new_g + h
            
            # Cập nhật g_score và thêm vào open_set
            g_scores[new_pos] = new_g
            heapq.heappush(open_set, (f, new_g, new_pos, path + [(dir_name, new_pos)]))
    
    return []


def astar_search(map_tiles, start_pos, bag, max_depth=20):
    """
    Tìm đường cho AI theo A*:
    1) Thử tìm combo trong max_depth bước.
    2) Nếu không tìm được, fallback:
       - Nếu bag rỗng: nhặt bất kỳ vật gần nhất
       - Nếu bag không rỗng: nhặt vật cùng loại với item VỪA MỚI ĐƯỢC THÊM VÀO trong bag
    """
    # 1) Tìm combo
    combo_path = _astar_find_combo(map_tiles, start_pos, bag, max_depth)
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

    return _astar_nearest_target(map_tiles, start_pos, target_vals)