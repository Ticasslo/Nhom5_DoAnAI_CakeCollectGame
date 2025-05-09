import numpy as np
import random
import pickle
import os
from collections import deque

# --- CẤU TRÚC VÀ KHÁI NIỆM TRONG Q-LEARNING ---
# Không gian trạng thái:
#   - pos: vị trí người chơi (x, y)
#   - bag: tuple các vật phẩm hiện có trong túi
#   - objects: các vị trí còn vật phẩm trên bản đồ
#
# Không gian hành động:
#   - 4 hướng di chuyển: lên, xuống, trái, phải
#
# Phần thưởng:
#   - Điểm thưởng cao cho việc tạo combo
#   - Điểm thưởng thấp hơn cho việc nhặt vật phẩm phù hợp với chiến lược
#   - Trừ điểm cho các hành động không hiệu quả

# Quy tắc combo
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

# Tham số cho Q-learning
LEARNING_RATE = 0.2
DISCOUNT_FACTOR = 0.95
EXPLORATION_RATE = 0.1
MAX_DEPTH = 20  # Giới hạn độ sâu tìm kiếm ban đầu
MAX_EPISODES = 10000  # Số lượng tập huấn luyện tối đa
MODEL_PATH = "q_learning_model.pkl"

# Ma trận Q mặc định
q_table = {}

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

def _get_valid_actions(map_tiles, pos, bag, objects):
    """
    Trả về danh sách các hành động hợp lệ từ trạng thái hiện tại.
    Mỗi hành động là một tuple (dir_name, (dx, dy))
    """
    rows = len(map_tiles)
    cols = len(map_tiles[0])
    x, y = pos
    valid_actions = []
    
    for dir_name, (dx, dy) in DIRECTIONS:
        nx, ny = x + dx, y + dy
        
        # Kiểm tra ô mới có nằm trong bản đồ không
        if not (0 <= nx < cols and 0 <= ny < rows):
            continue
            
        # Kiểm tra ô mới có phải là tường không
        cell = map_tiles[ny][nx]
        if isinstance(cell, str) and cell != ' ':
            continue
            
        # Kiểm tra nếu ô có vật phẩm
        if (nx, ny) in objects:
            obj_val = map_tiles[ny][nx]
            
            # Nếu đã có vật phẩm trong túi, kiểm tra xem vật phẩm mới có cùng loại không
            if bag and bag[-1] != obj_val and bag[0] != obj_val:
                # Bỏ qua vì không muốn nhặt vật phẩm khác loại
                continue
                
            # Kiểm tra xem vật phẩm có thuộc danh sách cho phép không
            empty_slots = BAG_SIZE - len(bag)
            allowed = _allowed_combo_objs(empty_slots)
            if not bag and obj_val not in allowed:
                continue
        
        valid_actions.append((dir_name, (dx, dy)))
    
    return valid_actions

def _calculate_reward(current_state, next_state, map_tiles):
    """
    Tính toán phần thưởng cho một hành động dựa trên trạng thái hiện tại và trạng thái tiếp theo
    """
    current_pos, current_bag, current_objects = current_state
    next_pos, next_bag, next_objects = next_state
    
    # Phân tích sự thay đổi trạng thái
    reward = -2  # Tăng chi phí cơ bản mỗi bước đi từ -1 lên -2 để ngăn đi loanh quanh
    
    # Kiểm tra xem có nhặt được vật phẩm không
    if len(next_bag) > len(current_bag) or (len(next_bag) == len(current_bag) == BAG_SIZE and next_bag != current_bag):
        reward += 15  # Tăng từ 5 lên 15 - Thưởng lớn hơn cho việc nhặt vật phẩm
        
        # Nếu nhặt vật phẩm cùng loại với vật phẩm cuối cùng trong túi
        if len(current_bag) > 0 and next_bag[-1] == current_bag[-1]:
            reward += 20  # Tăng từ 10 lên 20 - Thưởng nhiều hơn cho việc nhặt vật phẩm cùng loại
    
    # Kiểm tra xem có tạo được combo không 
    empty_slots = BAG_SIZE - len(next_bag)
    allowed_objs = _allowed_combo_objs(empty_slots)
    if _check_combo_sim(next_bag, allowed_objs):
        # Phần thưởng lớn cho việc tạo combo
        obj_type = None
        for obj in allowed_objs:
            need, points = COMBO_RULES[obj]
            # Kiểm tra xem combo thuộc loại nào
            for i in range(len(next_bag) - need + 1):
                if all(next_bag[i+j] == obj for j in range(need)):
                    obj_type = obj
                    break
            if obj_type is not None:
                break
                
        if obj_type is not None:
            _, points = COMBO_RULES[obj_type]
            reward += points / 5  # Tăng từ /10 lên /5 - Điểm thưởng cao hơn cho combo
    
    # Thưởng cho việc đi gần các vật phẩm mục tiêu
    if len(current_bag) > 0:
        target_obj = current_bag[-1]
        
        # Tìm khoảng cách đến vật phẩm cùng loại gần nhất
        target_positions = []
        rows, cols = len(map_tiles), len(map_tiles[0])
        for y in range(rows):
            for x in range(cols):
                if isinstance(map_tiles[y][x], int) and map_tiles[y][x] == target_obj and (x, y) in next_objects:
                    target_positions.append((x, y))
        
        if target_positions:
            # Khoảng cách Manhattan đến vật phẩm gần nhất
            current_dist = min(abs(current_pos[0] - x) + abs(current_pos[1] - y) for x, y in target_positions)
            next_dist = min(abs(next_pos[0] - x) + abs(next_pos[1] - y) for x, y in target_positions)
            
            if next_dist < current_dist:
                reward += 4  # Tăng từ 2 lên 4 - Thưởng nhiều hơn cho việc tiến gần vật phẩm mục tiêu
            elif next_dist > current_dist:
                reward -= 3  # Tăng từ -1 xuống -3 - Phạt mạnh hơn cho việc đi xa vật phẩm mục tiêu
    # Nếu không có vật phẩm nào trong túi, thưởng cho việc đi gần bất kỳ vật phẩm nào
    elif current_objects:
        # Tìm khoảng cách đến vật phẩm gần nhất
        current_dist = min(abs(current_pos[0] - x) + abs(current_pos[1] - y) for x, y in current_objects)
        next_dist = min(abs(next_pos[0] - x) + abs(next_pos[1] - y) for x, y in next_objects) if next_objects else float('inf')
        
        if next_dist < current_dist:
            reward += 3  # Thưởng cho việc tiến gần vật phẩm
        elif next_dist > current_dist:
            reward -= 2  # Phạt cho việc đi xa vật phẩm
    
    # Phạt đi qua ô đã đi qua (tránh đi loanh quanh)
    if current_pos == next_pos:
        reward -= 5  # Phạt nặng cho việc đứng yên
        
    return reward

def _serialize_state(state):
    """
    Chuyển đổi trạng thái thành chuỗi để sử dụng làm khóa cho ma trận Q
    Cải thiện để lưu thông tin về 2 vật phẩm gần nhất thay vì chỉ 1
    """
    pos, bag, objects = state
    
    # Lưu thông tin về hai vật phẩm gần nhất thay vì một
    if objects:
        # Sắp xếp các vật phẩm theo khoảng cách tăng dần
        sorted_objects = sorted(objects, 
                               key=lambda obj_pos: abs(pos[0] - obj_pos[0]) + abs(pos[1] - obj_pos[1]))
        
        if len(sorted_objects) >= 2:
            closest_objs = (sorted_objects[0], sorted_objects[1])
        else:
            closest_objs = (sorted_objects[0],)
            
        simplified_objects = str(closest_objs)
    else:
        simplified_objects = "no_objects"
    
    # Chỉ lưu 2 vật phẩm gần đây nhất trong túi thay vì toàn bộ
    if bag:
        if len(bag) >= 2:
            simplified_bag = (bag[-1], bag[-2])
        else:
            simplified_bag = (bag[-1],)
    else:
        simplified_bag = ()
        
    return f"{pos}_{simplified_bag}_{simplified_objects}"

def _load_q_table():
    """
    Tải ma trận Q từ file
    """
    global q_table
    if os.path.exists(MODEL_PATH):
        try:
            with open(MODEL_PATH, 'rb') as f:
                q_table = pickle.load(f)
            print(f"Đã tải ma trận Q từ {MODEL_PATH}")
        except Exception as e:
            print(f"Lỗi khi tải ma trận Q: {e}")
            q_table = {}
    else:
        print(f"Không tìm thấy file {MODEL_PATH}, khởi tạo ma trận Q mới")
        q_table = {}

def _save_q_table():
    """
    Lưu ma trận Q vào file
    """
    try:
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(q_table, f)
        print(f"Đã lưu ma trận Q vào {MODEL_PATH}")
    except Exception as e:
        print(f"Lỗi khi lưu ma trận Q: {e}")

def _train_q_learning(map_tiles, start_pos, initial_bag):
    """
    Huấn luyện ma trận Q bằng thuật toán Q-learning
    """
    global q_table
    
    rows = len(map_tiles)
    cols = len(map_tiles[0])
    
    # Tập các vị trí còn chứa object
    initial_objects = frozenset(
        (x, y) 
        for y in range(rows)
        for x in range(cols)
        if isinstance(map_tiles[y][x], int)
    )
    
    total_rewards = []
    
    for episode in range(MAX_EPISODES):
        # Khởi tạo trạng thái ban đầu
        state = (start_pos, tuple(initial_bag), initial_objects)
        done = False
        steps = 0
        episode_reward = 0
        
        while not done and steps < MAX_DEPTH:
            # Chuyển đổi trạng thái thành chuỗi
            state_key = _serialize_state(state)
            
            # Lấy danh sách hành động hợp lệ
            valid_actions = _get_valid_actions(map_tiles, state[0], state[1], state[2])
            
            if not valid_actions:
                break  # Không còn hành động hợp lệ
                
            # Kiểm tra xem đã tạo được combo chưa
            empty_slots = BAG_SIZE - len(state[1])
            allowed = _allowed_combo_objs(empty_slots)
            if _check_combo_sim(state[1], allowed):
                done = True
                # Thưởng lớn khi tạo được combo
                episode_reward += 50
                break
                
            # Khởi tạo giá trị Q cho trạng thái nếu chưa có
            if state_key not in q_table:
                q_table[state_key] = {dir_name: 0 for dir_name, _ in valid_actions}
                
            # Chọn hành động bằng epsilon-greedy
            if random.random() < EXPLORATION_RATE:
                action = random.choice(valid_actions)
            else:
                # Chọn hành động có giá trị Q cao nhất
                action_values = q_table[state_key]
                valid_action_names = [dir_name for dir_name, _ in valid_actions]
                best_action_name = max(
                    [a for a in valid_action_names if a in action_values],
                    key=lambda a: action_values.get(a, 0)
                )
                action = next((a for a in valid_actions if a[0] == best_action_name), valid_actions[0])
            
            # Thực hiện hành động và nhận trạng thái mới
            dir_name, (dx, dy) = action
            pos = state[0]
            new_pos = (pos[0] + dx, pos[1] + dy)
            bag = list(state[1])
            objects = state[2]
            
            # Nếu có vật phẩm ở vị trí mới, nhặt nó
            x, y = new_pos
            if (x, y) in objects:
                obj_val = map_tiles[y][x]
                bag.append(obj_val)
                if len(bag) > BAG_SIZE:
                    bag.pop(0)
                objects = objects.difference({(x, y)})
            
            new_state = (new_pos, tuple(bag), objects)
            
            # Tính toán phần thưởng
            reward = _calculate_reward(state, new_state, map_tiles)
            episode_reward += reward
            
            # Cập nhật ma trận Q
            new_state_key = _serialize_state(new_state)
            
            # Khởi tạo giá trị Q cho trạng thái mới nếu chưa có
            if new_state_key not in q_table:
                new_valid_actions = _get_valid_actions(map_tiles, new_state[0], new_state[1], new_state[2])
                q_table[new_state_key] = {a[0]: 0 for a in new_valid_actions}
            
            # Tính toán giá trị Q mới
            if q_table[new_state_key]:
                max_future_q = max(q_table[new_state_key].values())
            else:
                max_future_q = 0
                
            current_q = q_table[state_key].get(dir_name, 0)
            new_q = (1 - LEARNING_RATE) * current_q + LEARNING_RATE * (reward + DISCOUNT_FACTOR * max_future_q)
            
            # Cập nhật giá trị Q
            q_table[state_key][dir_name] = new_q
            
            # Chuyển sang trạng thái mới
            state = new_state
            steps += 1
        
        total_rewards.append(episode_reward)
        
        # In thông tin sau mỗi 100 episode
        if episode % 100 == 0:
            avg_reward = sum(total_rewards[-100:]) / min(100, len(total_rewards))
            print(f"Episode {episode}/{MAX_EPISODES}, Q-table size: {len(q_table)}, Avg reward: {avg_reward:.2f}")
    
    # In thông tin cuối cùng
    if total_rewards:
        print(f"Phần thưởng trung bình sau {MAX_EPISODES} episodes: {sum(total_rewards) / MAX_EPISODES:.2f}")
    
    # Lưu ma trận Q sau khi huấn luyện
    _save_q_table()

def _q_nearest_target(map_tiles, start_pos, target_vals):
    """
    Sử dụng ma trận Q để tìm đường đến vật phẩm mục tiêu gần nhất
    """
    rows = len(map_tiles)
    cols = len(map_tiles[0])
    
    # Sử dụng BFS khi ma trận Q không đủ thông tin
    queue = deque([(start_pos, [])])
    visited = {start_pos}
    
    while queue:
        pos, path = queue.popleft()
        x, y = pos
        
        # Nếu đã đến vật phẩm mục tiêu
        cell = map_tiles[y][x]
        if isinstance(cell, int) and cell in target_vals:
            return path
            
        # Lấy hành động từ ma trận Q nếu có
        state_key = _serialize_state((pos, (), frozenset()))
        
        if state_key in q_table and q_table[state_key]:
            # Sử dụng ma trận Q để chọn hướng đi
            best_dir = max(q_table[state_key].items(), key=lambda x: x[1])[0]
            dx, dy = next(d for n, d in DIRECTIONS if n == best_dir)
            nx, ny = x + dx, y + dy
            
            if 0 <= nx < cols and 0 <= ny < rows:
                c = map_tiles[ny][nx]
                
                # Kiểm tra ô mới có hợp lệ không
                if (isinstance(c, str) and c == ' ') or (isinstance(c, int) and c in target_vals):
                    if (nx, ny) not in visited:
                        return path + [(best_dir, (nx, ny))]
        
        # Nếu không có thông tin từ ma trận Q, sử dụng BFS
        for dir_name, (dx, dy) in DIRECTIONS:
            nx, ny = x + dx, y + dy
            
            if not (0 <= nx < cols and 0 <= ny < rows):
                continue
                
            c = map_tiles[ny][nx]
            
            # Bỏ qua ô là tường
            if isinstance(c, str) and c != ' ':
                continue
                
            # Bỏ qua ô chứa vật phẩm không nằm trong target_vals
            if isinstance(c, int) and c not in target_vals:
                continue
                
            if (nx, ny) in visited:
                continue
                
            visited.add((nx, ny))
            queue.append(((nx, ny), path + [(dir_name, (nx, ny))]))
    
    return []

def _q_find_combo(map_tiles, start_pos, bag, max_depth):
    """
    Sử dụng ma trận Q để tìm đường dẫn đến combo
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
    
    state = (start_pos, tuple(bag), initial_objects)
    path = []
    visited = {state}
    
    for _ in range(max_depth):
        # Kiểm tra xem đã tạo được combo chưa
        pos, bag_tup, objects = state
        empty_slots = BAG_SIZE - len(bag_tup)
        allowed = _allowed_combo_objs(empty_slots)
        
        if _check_combo_sim(bag_tup, allowed):
            return path
            
        # Lấy danh sách hành động hợp lệ
        valid_actions = _get_valid_actions(map_tiles, pos, bag_tup, objects)
        
        if not valid_actions:
            break
            
        # Chọn hành động từ ma trận Q nếu có
        state_key = _serialize_state(state)
        
        if state_key in q_table and q_table[state_key]:
            # Lọc các hành động hợp lệ có trong ma trận Q
            valid_actions_in_q = [(dir_name, dxdy) for dir_name, dxdy in valid_actions if dir_name in q_table[state_key]]
            
            if valid_actions_in_q:
                # Chọn hành động có giá trị Q cao nhất
                best_dir = max((dir_name for dir_name, _ in valid_actions_in_q), key=lambda d: q_table[state_key].get(d, 0))
                action = next((a for a in valid_actions if a[0] == best_dir), valid_actions[0])
            else:
                # Nếu không có hành động hợp lệ trong ma trận Q, chọn ngẫu nhiên
                action = random.choice(valid_actions)
        else:
            # Nếu trạng thái không có trong ma trận Q, chọn ngẫu nhiên
            action = random.choice(valid_actions)
            
        # Thực hiện hành động
        dir_name, (dx, dy) = action
        x, y = pos
        nx, ny = x + dx, y + dy
        
        # Tạo trạng thái mới
        new_bag = list(bag_tup)
        new_objects = objects
        
        if (nx, ny) in objects:
            val = map_tiles[ny][nx]
            new_bag.append(val)
            if len(new_bag) > BAG_SIZE:
                new_bag.pop(0)
            new_objects = objects.difference({(nx, ny)})
            
        new_state = ((nx, ny), tuple(new_bag), new_objects)
        
        if new_state in visited:
            # Nếu đã ghé thăm trạng thái này, chọn hành động khác
            continue
            
        visited.add(new_state)
        path.append((dir_name, (nx, ny)))
        state = new_state
    
    return path  # Trả về đường đi đã tìm được, có thể không dẫn đến combo

def qlearning_search(map_tiles, start_pos, bag, max_depth=20):
    """
    Sử dụng Q-learning để tìm đường đi:
    1) Tải ma trận Q từ file (nếu có)
    2) Huấn luyện nếu cần thiết
    3) Tìm đường đi đến combo trong max_depth bước
    4) Nếu không tìm được combo, fallback:
       - Nếu túi rỗng: nhặt bất kỳ vật phẩm gần nhất
       - Nếu túi không rỗng: nhặt vật phẩm cùng loại với vật phẩm mới nhất
    """
    # 1) Tải ma trận Q
    _load_q_table()
    
    # 2) Huấn luyện nếu ma trận Q rỗng hoặc quá nhỏ
    if len(q_table) < 200:  # Tăng ngưỡng từ 100 lên 200 để đảm bảo đủ dữ liệu học
        print("Huấn luyện mô hình Q-learning...")
        _train_q_learning(map_tiles, start_pos, bag)
    
    # 3) Tìm đường đi đến combo
    combo_path = _q_find_combo(map_tiles, start_pos, bag, max_depth)
    if combo_path:
        return combo_path
        
    # 4) Fallback: tìm vật phẩm gần nhất
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
    
    # Sử dụng luôn BFS để tìm vật phẩm gần nhất khi fallback
    # Đảm bảo luôn có đường đi tối ưu khi fallback
    return _bfs_nearest_target(map_tiles, start_pos, target_vals)

def _bfs_nearest_target(map_tiles, start_pos, target_vals):
    """
    BFS để tìm đường ngắn nhất tới ô chứa giá trị trong target_vals.
    Thêm hàm này để đảm bảo luôn có đường đi tối ưu khi fallback
    """
    rows = len(map_tiles)
    cols = len(map_tiles[0])
    queue = deque([(start_pos, [])])
    visited = {start_pos}

    while queue:
        pos, path = queue.popleft()
        x, y = pos
        
        # Nếu ô này chứa target
        cell = map_tiles[y][x]
        if isinstance(cell, int) and cell in target_vals:
            return path  # path dẫn tới (x0,y0)

        for dir_name, (dx, dy) in DIRECTIONS:
            nx, ny = x + dx, y + dy
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

# Hàm chính để chạy thuật toán từ bên ngoài
def main():
    """
    Hàm chính để huấn luyện và kiểm tra mô hình
    """
    # Tải bản đồ
    from map_handler import load_map_from_file, place_random_objects
    map_tiles = load_map_from_file("map_design.txt", 25)
    
    # Đặt vật phẩm ngẫu nhiên vào bản đồ trước khi huấn luyện
    place_random_objects(map_tiles, 25)
    
    # Hiển thị số lượng vật phẩm trên bản đồ
    obj_count = sum(1 for y in range(len(map_tiles)) for x in range(len(map_tiles[0])) 
                 if isinstance(map_tiles[y][x], int))
    print(f"Đã đặt {obj_count} vật phẩm vào bản đồ")
    
    # Huấn luyện mô hình
    print("Bắt đầu huấn luyện Q-learning...")
    _load_q_table()
    _train_q_learning(map_tiles, (12, 12), [])
    
    print("Hoàn thành huấn luyện và lưu mô hình")

if __name__ == "__main__":
    main()
