import random
import math
from collections import deque

# --- CẤU TRÚC VÀ KHÁI NIỆM TRONG SIMULATED ANNEALING ---
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


def _evaluate_state(state, map_tiles, target_obj=None, prioritize_combo=True):
    """
    Đánh giá trạng thái hiện tại dựa trên:
    1. Khả năng tạo combo (ưu tiên cao nhất)
    2. Khoảng cách đến vật phẩm mục tiêu gần nhất
    
    Returns:
    - Điểm số: Càng cao càng tốt
    """
    pos, bag_tup, objects = state
    score = 0
    
    # Kiểm tra combo
    empty_slots = BAG_SIZE - len(bag_tup)
    allowed_objs = _allowed_combo_objs(empty_slots)
    
    if _check_combo_sim(bag_tup, allowed_objs):
        # Nếu đã có combo, cho điểm cao nhất
        return 2000  # Tăng điểm thưởng khi tìm thấy combo
    
    if prioritize_combo and bag_tup:
        # Ưu tiên tạo combo với loại vật phẩm đã có trong túi
        object_type = bag_tup[0]  # Lấy loại vật phẩm đầu tiên
        count = sum(1 for x in bag_tup if x == object_type)
        need, _ = COMBO_RULES[object_type]
        
        # Cho điểm dựa trên số lượng vật phẩm cùng loại đã có
        # Sử dụng hàm bình phương để ưu tiên cao hơn cho trạng thái gần hoàn thành combo
        score += ((count / need) ** 2) * 1000  # Tăng hệ số từ 500 lên 1000
        
        # Thưởng thêm nếu chỉ cần thêm 1 hoặc 2 vật phẩm để hoàn thành combo
        if need - count <= 2 and need - count > 0:
            score += 300  # Thưởng thêm cho combo gần hoàn thành
    
    # Điểm trừ dựa trên khoảng cách đến vật phẩm mục tiêu gần nhất
    if objects:  # Nếu còn vật phẩm trên bản đồ
        if target_obj is not None:
            # Tìm vật phẩm mục tiêu gần nhất
            target_positions = []
            for obj_pos in objects:
                x, y = obj_pos
                if map_tiles[y][x] == target_obj:
                    target_positions.append(obj_pos)
            
            if target_positions:
                min_dist = min(_calculate_manhattan_distance(pos, obj_pos) for obj_pos in target_positions)
                score -= min_dist * 5  # Giảm hệ số phạt từ 10 xuống 5
            else:
                # Không còn vật phẩm mục tiêu, điểm trừ lớn
                score -= 500  # Giảm mức phạt
        else:
            # Không chỉ định vật phẩm mục tiêu, lấy vật phẩm gần nhất
            min_dist = min(_calculate_manhattan_distance(pos, obj_pos) for obj_pos in objects)
            score -= min_dist * 5  # Giảm hệ số phạt từ 10 xuống 5
    
    return score


def _get_valid_neighbors(state, map_tiles, allowed_objs=None):
    """
    Trả về danh sách các trạng thái kề với state hiện tại
    """
    pos, bag_tup, objects = state
    rows = len(map_tiles)
    cols = len(map_tiles[0])
    x0, y0 = pos
    
    neighbors = []
    
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
            
            # Kiểm tra các điều kiện về vật phẩm
            if new_bag:
                # Nếu đã có ít nhất một vật phẩm, chỉ cho phép nhặt vật phẩm cùng loại
                candidate = new_bag[0]
                if val != candidate:
                    continue  # Bỏ qua bước này
            else:
                # Nếu túi rỗng, chỉ được nhặt vật phẩm thuộc danh sách cho phép
                if allowed_objs and val not in allowed_objs:
                    continue
            
            # Thêm vật phẩm vào túi
            new_bag.append(val)
            if len(new_bag) > BAG_SIZE:
                new_bag.pop(0)
            
            # Loại bỏ vị trí này khỏi tập objects
            new_objects = objects.difference({(nx, ny)})
        
        new_state = ((nx, ny), tuple(new_bag), new_objects)
        neighbors.append((dir_name, new_state))
    
    return neighbors


def _simulated_annealing_find_combo(map_tiles, start_pos, bag, max_depth):
    """
    Sử dụng thuật toán Simulated Annealing để tìm đường đi tạo combo.
    
    Tham số:
    - map_tiles: Bản đồ 2D
    - start_pos: Vị trí bắt đầu (x, y)
    - bag: Danh sách các vật phẩm trong túi
    - max_depth: Độ sâu tối đa được phép
    
    Trả về:
    - Danh sách các bước đi [(direction, (x, y)), ...]
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
    
    # Trạng thái ban đầu
    current_state = (start_pos, tuple(bag), initial_objects)
    
    # Tham số cho Simulated Annealing
    initial_temp = 200  # Tăng nhiệt độ ban đầu cho phép khám phá nhiều hơn
    cooling_rate = 0.98  # Làm chậm quá trình làm lạnh
    min_temp = 0.05  # Nhiệt độ tối thiểu
    
    # Số lần lặp ở mỗi nhiệt độ
    iterations_per_temp = 15  # Tăng số lần lặp
    
    # Biến lưu trữ trạng thái tốt nhất
    best_state = current_state
    best_score = _evaluate_state(current_state, map_tiles)
    
    # Lưu vết đường đi
    state_path = {current_state: []}
    
    temp = initial_temp
    iteration = 0
    
    while temp > min_temp and iteration < max_depth:
        # Lấy các trạng thái kề hợp lệ
        empty_slots = BAG_SIZE - len(current_state[1])
        allowed_objs = _allowed_combo_objs(empty_slots)
        
        neighbors = _get_valid_neighbors(current_state, map_tiles, allowed_objs)
        
        if not neighbors:
            break  # Không có bước đi hợp lệ
        
        # Chọn ngẫu nhiên một trạng thái kề
        dir_name, next_state = random.choice(neighbors)
        
        # Đánh giá trạng thái hiện tại và trạng thái kề
        current_score = _evaluate_state(current_state, map_tiles)
        next_score = _evaluate_state(next_state, map_tiles)
        
        # Kiểm tra nếu đã tìm thấy combo
        if next_score >= 2000:  # Điểm cao được cho khi có combo
            # Cập nhật đường đi
            state_path[next_state] = state_path[current_state] + [(dir_name, next_state[0])]
            return state_path[next_state]
        
        # Tính delta score
        delta = next_score - current_score
        
        # Quyết định chấp nhận trạng thái mới hay không
        if delta > 0 or random.random() < math.exp(delta / temp):
            # Cập nhật đường đi
            state_path[next_state] = state_path[current_state] + [(dir_name, next_state[0])]
            
            # Chuyển sang trạng thái mới
            current_state = next_state
            
            # Cập nhật trạng thái tốt nhất nếu cần
            if next_score > best_score:
                best_state = next_state
                best_score = next_score
        
        # Cập nhật nhiệt độ theo lịch trình làm lạnh
        if iteration % iterations_per_temp == 0:
            temp *= cooling_rate
        
        iteration += 1
        
        # Hạn chế độ sâu của đường đi
        if len(state_path[current_state]) >= max_depth:
            break
    
    # Nếu không tìm thấy combo, trả về đường đi tới trạng thái tốt nhất
    return state_path[best_state]


def _bfs_nearest_target(map_tiles, start_pos, target_vals):
    """
    BFS để tìm đường ngắn nhất tới ô chứa giá trị trong target_vals.
    Trả về path list hoặc [] nếu không tìm.
    Đảm bảo không nhặt vật phẩm khác trên đường đi.
    """
    rows = len(map_tiles)
    cols = len(map_tiles[0])
    queue = deque([(start_pos, [])])
    visited = {start_pos}

    while queue:
        (x0, y0), path = queue.popleft()
        # Nếu ô này chứa target
        cell = map_tiles[y0][x0]
        if isinstance(cell, int) and cell in target_vals:
            return path  # path dẫn tới (x0,y0)

        for dir_name, (dx, dy) in DIRECTIONS:
            nx, ny = x0 + dx, y0 + dy
            if not (0 <= nx < cols and 0 <= ny < rows):
                continue
            
            c = map_tiles[ny][nx]
            # Bỏ qua ô là tường
            if isinstance(c, str) and c != ' ':
                continue
            
            # Bỏ qua ô chứa vật phẩm KHÔNG nằm trong target_vals
            # không cho phép nhặt vật phẩm khác
            if isinstance(c, int) and c not in target_vals:
                continue
                
            if (nx, ny) in visited:
                continue
                
            visited.add((nx, ny))
            queue.append(((nx, ny), path + [(dir_name, (nx, ny))]))

    return []


def simulated_annealing_search(map_tiles, start_pos, bag, max_depth=50):  # Tăng max_depth
    """
    Tìm đường cho AI sử dụng Simulated Annealing:
    1) Thử tìm combo trong max_depth bước.
    2) Nếu không tìm được, fallback:
       - Nếu bag rỗng: nhặt bất kỳ vật gần nhất
       - Nếu bag không rỗng: nhặt vật cùng loại với item VỪA MỚI ĐƯỢC THÊM VÀO trong bag
    """
    # 1) Tìm combo
    combo_path = _simulated_annealing_find_combo(map_tiles, start_pos, bag, max_depth)
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

    return _bfs_nearest_target(map_tiles, start_pos, target_vals)
