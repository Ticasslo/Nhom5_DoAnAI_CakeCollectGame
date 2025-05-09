import random
from collections import deque
import heapq

# --- CẤU TRÚC VÀ KHÁI NIỆM TRONG NONDETERMINISTIC SEARCH (AND-OR TREE) ---
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


def _calculate_manhattan_distance(pos1, pos2):
    """
    Tính khoảng cách Manhattan giữa hai điểm
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def _evaluate_state(state, map_tiles, depth=0):
    """
    Hàm đánh giá trạng thái trong AND-OR tree search:
    - Nếu có combo: trả về điểm số cao
    - Nếu đang nhặt được nhiều vật phẩm cùng loại: trả về điểm số trung bình
    - Nếu túi rỗng/không có triển vọng: trả về điểm số thấp
    
    Trả về (giá_trị, có_combo?)
    """
    pos, bag_tup, objects = state
    
    # Kiểm tra combo
    empty_slots = BAG_SIZE - len(bag_tup)
    allowed_objs = _allowed_combo_objs(empty_slots)
    
    if _check_combo_sim(bag_tup, allowed_objs):
        # Nếu đã có combo, cho điểm cao nhất
        return (1000 - depth, True)  # Trừ depth để ưu tiên combo sớm
    
    # Nếu túi không rỗng, đánh giá triển vọng tạo combo
    if bag_tup:
        obj_type = bag_tup[0]  # Lấy loại vật phẩm đầu tiên
        count = sum(1 for x in bag_tup if x == obj_type)
        need, _ = COMBO_RULES[obj_type]
        
        # Tính xem có bao nhiêu vật phẩm cùng loại còn trên bản đồ
        remaining_same_type = 0
        for obj_pos in objects:
            x, y = obj_pos
            if map_tiles[y][x] == obj_type:
                remaining_same_type += 1
        
        # Nếu có đủ vật phẩm trên bản đồ để hoàn thành combo
        if count + remaining_same_type >= need:
            # Cho điểm dựa trên tỷ lệ hoàn thành
            progress = count / need
            return (500 * progress - depth, False)
    
    # Trường hợp còn lại: túi rỗng hoặc không có triển vọng
    return (100 - depth, False)  # Điểm thấp, ưu tiên độ sâu nhỏ


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

def _nondeterministic_find_combo(map_tiles, start_pos, bag, max_depth):
    """
    Thuật toán AND-OR tree search để tìm đường tạo combo.
    
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
    start_state = (start_pos, tuple(bag), initial_objects)
    
    # Hàng đợi ưu tiên với các trạng thái cần khám phá
    # Mỗi phần tử là (điểm_đánh_giá, độ_sâu, trạng_thái, đường_đi)
    open_set = []
    heapq.heappush(open_set, (-1000, 0, start_state, []))  # -1000 cho ưu tiên cao
    
    # Tập các trạng thái đã thăm
    visited = {start_state: 0}  # state -> độ sâu tốt nhất
    
    # Biến lưu trữ điểm đánh giá tốt nhất cho mỗi độ sâu
    best_value_per_depth = {}
    
    while open_set:
        # Lấy trạng thái có ưu tiên cao nhất (giá trị nhỏ nhất vì dùng heapq)
        priority, depth, state, path = heapq.heappop(open_set)
        priority = -priority  # Đảo ngược lại vì dùng min-heap
        
        pos, bag_tup, objects = state
        
        # Nếu đã tìm được combo, trả về đường đi
        empty_slots = BAG_SIZE - len(bag_tup)
        allowed_objs = _allowed_combo_objs(empty_slots)
        if _check_combo_sim(bag_tup, allowed_objs):
            return path
        
        # Nếu đã đạt tới độ sâu tối đa, bỏ qua
        if depth >= max_depth:
            continue
        
        # Nếu đã có trạng thái tốt hơn ở độ sâu này, bỏ qua
        if depth in best_value_per_depth and priority < best_value_per_depth[depth] * 0.9:
            continue
        
        # Lấy các trạng thái kề
        neighbors = _get_valid_neighbors(state, map_tiles, allowed_objs)
        
        # Với mỗi trạng thái kề, đánh giá và thêm vào open_set nếu cần
        for dir_name, next_state in neighbors:
            new_depth = depth + 1
            
            # Nếu đã có đường đi tốt hơn đến trạng thái này, bỏ qua
            if next_state in visited and visited[next_state] <= new_depth:
                continue
            
            # Đánh giá trạng thái mới
            value, has_combo = _evaluate_state(next_state, map_tiles, new_depth)
            
            # Cập nhật giá trị tốt nhất cho độ sâu này
            if new_depth not in best_value_per_depth or value > best_value_per_depth[new_depth]:
                best_value_per_depth[new_depth] = value
            
            # Thêm vào open_set
            visited[next_state] = new_depth
            heapq.heappush(open_set, (-value, new_depth, next_state, path + [(dir_name, next_state[0])]))
    
    # Nếu không tìm được combo, trả về đường đi rỗng
    return []


def _nondeterministic_nearest_target(map_tiles, start_pos, target_vals, max_depth=100):
    """
    Sử dụng thuật toán nondeterministic để tìm đường đi đến vật phẩm gần nhất.
    
    Tham số:
    - map_tiles: Bản đồ 2D
    - start_pos: Vị trí bắt đầu (x, y)
    - target_vals: Danh sách các loại vật phẩm mục tiêu
    - max_depth: Độ sâu tối đa được phép
    
    Trả về:
    - Danh sách các bước đi [(direction, (x, y)), ...]
    """
    rows = len(map_tiles)
    cols = len(map_tiles[0])
    
    # Tạo danh sách các vị trí mục tiêu
    target_positions = []
    for y in range(rows):
        for x in range(cols):
            if isinstance(map_tiles[y][x], int) and map_tiles[y][x] in target_vals:
                target_positions.append((x, y))
    
    if not target_positions:
        return []  # Không có vật phẩm mục tiêu nào
    
    # Hàng đợi ưu tiên với các trạng thái cần khám phá
    # Mỗi phần tử là (ưu_tiên, độ_sâu, vị_trí, đường_đi)
    open_set = []
    
    # Tính khoảng cách đến vật phẩm gần nhất
    min_dist = min(_calculate_manhattan_distance(start_pos, target_pos) for target_pos in target_positions)
    
    # Thêm trạng thái ban đầu vào hàng đợi
    # Ưu tiên = khoảng cách Manhattan đến vật phẩm gần nhất
    heapq.heappush(open_set, (min_dist, 0, start_pos, []))
    
    # Tập các vị trí đã thăm
    visited = {start_pos: 0}  # position -> độ sâu tốt nhất
    
    while open_set:
        # Lấy trạng thái có ưu tiên cao nhất (khoảng cách nhỏ nhất)
        priority, depth, pos, path = heapq.heappop(open_set)
        x0, y0 = pos
        
        # Kiểm tra nếu đã đến vật phẩm mục tiêu
        cell = map_tiles[y0][x0]
        if isinstance(cell, int) and cell in target_vals:
            return path
        
        # Nếu đã đạt tới độ sâu tối đa, bỏ qua
        if depth >= max_depth:
            continue
        
        # Xét các hướng đi tiếp theo
        for dir_name, (dx, dy) in DIRECTIONS:
            nx, ny = x0 + dx, y0 + dy
            
            # Kiểm tra vị trí hợp lệ
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
            new_depth = depth + 1
            
            # Nếu đã có đường đi tốt hơn đến vị trí này, bỏ qua
            if new_pos in visited and visited[new_pos] <= new_depth:
                continue
            
            # Tính khoảng cách mới đến vật phẩm gần nhất
            if isinstance(c, int) and c in target_vals:
                new_priority = 0  # Đã đến vật phẩm mục tiêu
            else:
                # Tính khoảng cách đến vật phẩm gần nhất
                new_priority = min(_calculate_manhattan_distance(new_pos, target_pos) 
                                 for target_pos in target_positions)
            
            # Thêm yếu tố ngẫu nhiên để khám phá nhiều đường đi khác nhau
            # (đặc trưng của thuật toán nondeterministic)
            random_factor = random.uniform(0.9, 1.1)
            new_priority = new_priority * random_factor
            
            # Cập nhật và thêm vào open_set
            visited[new_pos] = new_depth
            heapq.heappush(open_set, 
                          (new_priority, new_depth, new_pos, path + [(dir_name, new_pos)]))
    
    return []


def nondeterministic_search(map_tiles, start_pos, bag, max_depth=50):
    """
    Tìm đường cho AI sử dụng AND-OR tree search:
    1) Thử tìm combo trong max_depth bước.
    2) Nếu không tìm được, fallback:
       - Nếu bag rỗng: nhặt bất kỳ vật gần nhất
       - Nếu bag không rỗng: nhặt vật cùng loại với item VỪA MỚI ĐƯỢC THÊM VÀO trong bag
       
    Cách thuật toán hoạt động:
    - Khám phá không gian trạng thái theo chiến lược AND-OR tree
    - Tại mỗi bước, đánh giá nhiều lựa chọn khác nhau
    - Chọn đường đi có triển vọng cao nhất để tạo combo
    - Thực hiện backtracking khi cần thiết
    - Trong trường hợp không tìm được combo, tìm đường đi đến vật phẩm gần nhất cùng loại
      cũng bằng phương pháp nondeterministic với yếu tố ngẫu nhiên
    """
    # 1) Tìm combo với AND-OR tree search
    combo_path = _nondeterministic_find_combo(map_tiles, start_pos, bag, max_depth)
    if combo_path:
        return combo_path

    # 2) Fallback: tìm nearest bằng nondeterministic
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

    # Sử dụng phương pháp nondeterministic để tìm đường đi đến vật phẩm gần nhất
    return _nondeterministic_nearest_target(map_tiles, start_pos, target_vals)
