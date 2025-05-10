import numpy as np
import pickle
import os
import random
import math
from collections import deque
import time

# Định nghĩa các hướng di chuyển
DIRECTIONS = [
    ("Up", (0, -1)),
    ("Down", (0, 1)),
    ("Left", (-1, 0)),
    ("Right", (1, 0)),
]

# Quy tắc combo và kích thước túi
COMBO_RULES = {
    0: (2, 200),
    1: (3, 300),
    2: (4, 400),
    3: (5, 500),
    4: (6, 600),
}
BAG_SIZE = 7

# Tên file để lưu Q-table
Q_TABLE_FILE = "qtable16_path.pkl"

# Thu nhỏ không gian trạng thái
def get_state_key(pos, map_tiles, last_item_type):
    """
    Tạo khóa trạng thái dựa trên thông tin tương đối thay vì tọa độ chính xác
    - Hướng tương đối đến vật phẩm mục tiêu gần nhất
    - Loại vật phẩm cuối cùng trong túi
    """
    # Xác định vật phẩm mục tiêu
    target_type = last_item_type if last_item_type >= 0 else None
    
    # Tìm vật phẩm mục tiêu gần nhất
    target_pos, distance = find_nearest_object(map_tiles, pos, target_type)
    
    # Nếu không tìm thấy, tìm vật phẩm bất kỳ
    if target_pos is None:
        target_pos, distance = find_nearest_object(map_tiles, pos)
        if target_pos is None:
            # Không còn vật phẩm nào trên bản đồ
            return (-1, -1, last_item_type)
    
    # Tính hướng tương đối (phân chia không gian thành 8 hướng)
    dx = target_pos[0] - pos[0]
    dy = target_pos[1] - pos[1]
    
    # Chuyển đổi thành hướng tương đối (8 hướng)
    if dx > 0 and dy > 0:
        direction = 0  # Đông Nam
    elif dx > 0 and dy == 0:
        direction = 1  # Đông
    elif dx > 0 and dy < 0:
        direction = 2  # Đông Bắc
    elif dx == 0 and dy < 0:
        direction = 3  # Bắc
    elif dx < 0 and dy < 0:
        direction = 4  # Tây Bắc
    elif dx < 0 and dy == 0:
        direction = 5  # Tây
    elif dx < 0 and dy > 0:
        direction = 6  # Tây Nam
    else:
        direction = 7  # Nam
    
    # Phân chia khoảng cách thành 3 mức: gần (0), trung bình (1), xa (2)
    if distance <= 3:
        distance_level = 0
    elif distance <= 10:
        distance_level = 1
    else:
        distance_level = 2
    
    return (direction, distance_level, last_item_type)

def get_available_actions(map_tiles, pos):
    """
    Xác định các hành động hợp lệ từ vị trí hiện tại
    """
    rows = len(map_tiles)
    cols = len(map_tiles[0])
    valid_actions = []
    
    for i, (direction, (dx, dy)) in enumerate(DIRECTIONS):
        nx, ny = pos[0] + dx, pos[1] + dy
        # Kiểm tra vị trí mới có nằm trong bản đồ không
        if 0 <= nx < cols and 0 <= ny < rows:
            # Kiểm tra không phải là tường
            if not (isinstance(map_tiles[ny][nx], str) and map_tiles[ny][nx] != ' '):
                valid_actions.append(i)
    
    return valid_actions

def calculate_manhattan_distance(pos1, pos2):
    """
    Tính khoảng cách Manhattan giữa hai điểm - vẫn giữ lại để tham khảo
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def get_distance_with_obstacles(map_tiles, pos1, pos2):
    """
    Tính khoảng cách giữa hai điểm có xét đến vật cản
    - Nếu có đường đi trực tiếp: trả về khoảng cách Manhattan
    - Nếu có vật cản: trả về khoảng cách Manhattan + phạt dựa trên số lượng vật cản
    - Sử dụng hàm phạt phi tuyến để đánh giá tốt hơn
    """
    if pos2 is None:
        return float('inf')
    
    # Tính khoảng cách Manhattan
    manhattan_dist = calculate_manhattan_distance(pos1, pos2)
    
    # Kiểm tra đường đi thẳng
    if has_clear_path(map_tiles, pos1, pos2):
        return manhattan_dist
    
    # Nếu có vật cản, đếm số lượng vật cản trên đường đi
    obstacles = 0
    x1, y1 = pos1
    x2, y2 = pos2
    
    # Đếm vật cản theo đường đi Manhattan
    if x1 != x2 and y1 != y2:
        # Đường đi chéo, kiểm tra cả 2 đường đi có thể
        path1_obstacles = 0
        path2_obstacles = 0
        
        # Đường đi 1: đi ngang trước, dọc sau
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if isinstance(map_tiles[y1][x], str) and map_tiles[y1][x] != ' ':
                path1_obstacles += 1
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if isinstance(map_tiles[y][x2], str) and map_tiles[y][x2] != ' ':
                path1_obstacles += 1
                
        # Đường đi 2: đi dọc trước, ngang sau
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if isinstance(map_tiles[y][x1], str) and map_tiles[y][x1] != ' ':
                path2_obstacles += 1
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if isinstance(map_tiles[y2][x], str) and map_tiles[y2][x] != ' ':
                path2_obstacles += 1
                
        obstacles = min(path1_obstacles, path2_obstacles)
    else:
        # Đường đi thẳng ngang hoặc dọc
        if x1 == x2:  # Đường dọc
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if isinstance(map_tiles[y][x1], str) and map_tiles[y][x1] != ' ':
                    obstacles += 1
        else:  # Đường ngang
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if isinstance(map_tiles[y1][x], str) and map_tiles[y1][x] != ' ':
                    obstacles += 1
    
    # Phạt phi tuyến dựa trên số lượng vật cản
    # obstacles * (1 + 0.2 * obstacles) tạo ra phạt tăng dần theo số lượng vật cản
    # ví dụ: 1 vật cản = 1*1.2 = 1.2, 2 vật cản = 2*1.4 = 2.8, 3 vật cản = 3*1.6 = 4.8
    penalty = obstacles * (1 + 0.2 * obstacles)
    result = manhattan_dist + penalty
    
    return result

def find_nearest_object(map_tiles, pos, target_type=None):
    """
    Tìm vật phẩm gần nhất có loại target_type, xét đến vật cản
    Nếu target_type là None, tìm vật phẩm bất kỳ gần nhất
    Trả về (vị trí, khoảng cách) hoặc (None, float('inf')) nếu không tìm thấy
    """
    rows = len(map_tiles)
    cols = len(map_tiles[0])
    min_distance = float('inf')
    nearest_pos = None
    
    # Thu thập tất cả các vật phẩm phù hợp
    candidates = []
    for y in range(rows):
        for x in range(cols):
            cell = map_tiles[y][x]
            if isinstance(cell, int):
                if target_type is None or cell == target_type:
                    candidates.append((x, y))
    
    # Tính khoảng cách có xét đến vật cản đến từng vật phẩm
    for candidate_pos in candidates:
        distance = get_distance_with_obstacles(map_tiles, pos, candidate_pos)
        if distance < min_distance:
            min_distance = distance
            nearest_pos = candidate_pos
    
    return nearest_pos, min_distance

def _check_combo_potential(bag, item_type):
    """
    Kiểm tra xem việc thêm item_type vào bag có thể tạo thành combo không
    """
    if item_type not in COMBO_RULES:
        return False
    
    need, _ = COMBO_RULES[item_type]
    count = 1  # Tính cả item_type sắp thêm vào
    
    # Đếm số lượng item_type liên tiếp ở cuối bag
    for i in range(len(bag) - 1, -1, -1):
        if bag[i] == item_type:
            count += 1
        else:
            break
    
    return count >= need

def moving_towards_target(pos, new_pos, target_pos, map_tiles):
    """
    Kiểm tra xem việc di chuyển từ pos đến new_pos có tiến gần đến target_pos không
    Sử dụng khoảng cách có xét đến vật cản
    """
    if target_pos is None:
        return False
    
    current_distance = get_distance_with_obstacles(map_tiles, pos, target_pos)
    new_distance = get_distance_with_obstacles(map_tiles, new_pos, target_pos)
    
    return new_distance < current_distance

class QLearningAgent:
    def __init__(self, alpha=0.2, gamma=0.9, epsilon=0.3, epsilon_decay=0.995, min_epsilon=0.1):
        """
        Khởi tạo agent Q-learning với các tham số cải tiến
        
        Tham số:
        - alpha: Tỷ lệ học (learning rate) - tăng để học nhanh hơn
        - gamma: Hệ số giảm (discount factor)
        - epsilon: Xác suất khám phá (exploration rate) - tăng để khám phá nhiều hơn
        - epsilon_decay: Tỷ lệ giảm epsilon - giảm nhanh hơn
        - min_epsilon: Giá trị tối thiểu của epsilon
        """
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon
        self.q_table = {}
        self.load_q_table()
        
        # Thống kê
        self.explored_actions = 0
        self.exploited_actions = 0
    
    def get_q_value(self, state, action):
        """
        Lấy giá trị Q cho cặp (state, action)
        """
        if (state, action) not in self.q_table:
            # Khởi tạo giá trị Q ban đầu thấp hơn 0
            self.q_table[(state, action)] = random.uniform(-0.1, 0.1)
        return self.q_table[(state, action)]
    
    def choose_action(self, state, valid_actions):
        """
        Chọn hành động dựa trên chính sách epsilon-greedy
        """
        if random.random() < self.epsilon:
            # Khám phá: chọn hành động ngẫu nhiên
            self.explored_actions += 1
            return random.choice(valid_actions)
        else:
            # Khai thác: chọn hành động có giá trị Q cao nhất
            q_values = [self.get_q_value(state, action) for action in valid_actions]
            max_q = max(q_values)
            # Nếu có nhiều hành động có cùng giá trị Q tối đa, chọn ngẫu nhiên một trong số đó
            best_actions = [action for action, q in zip(valid_actions, q_values) if q == max_q]
            self.exploited_actions += 1
            return random.choice(best_actions)
    
    def update_q_value(self, state, action, reward, next_state, next_valid_actions):
        """
        Cập nhật giá trị Q cho cặp (state, action)
        """
        if not next_valid_actions:
            max_next_q = 0
        else:
            max_next_q = max(self.get_q_value(next_state, next_action) for next_action in next_valid_actions)
        
        current_q = self.get_q_value(state, action)
        # Công thức Q-learning chuẩn
        self.q_table[(state, action)] = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
    
    def decay_epsilon(self):
        """
        Giảm giá trị epsilon sau mỗi episode
        """
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
    
    def save_q_table(self):
        """
        Lưu Q-table vào file
        """
        with open(Q_TABLE_FILE, 'wb') as f:
            pickle.dump(self.q_table, f)
        print(f"Q-table đã được lưu vào {Q_TABLE_FILE} (kích thước: {len(self.q_table)} entries)")
    
    def load_q_table(self):
        """
        Tải Q-table từ file
        """
        if os.path.exists(Q_TABLE_FILE):
            with open(Q_TABLE_FILE, 'rb') as f:
                self.q_table = pickle.load(f)
            print(f"Q-table đã được tải từ {Q_TABLE_FILE} (kích thước: {len(self.q_table)} entries)")
        else:
            self.q_table = {}
            print("Khởi tạo Q-table mới")
    
    def get_statistics(self):
        """
        Trả về thống kê về agent
        """
        total_actions = self.explored_actions + self.exploited_actions
        exploration_rate = self.explored_actions / total_actions if total_actions > 0 else 0
        
        return {
            'q_table_size': len(self.q_table),
            'explored_actions': self.explored_actions,
            'exploited_actions': self.exploited_actions,
            'exploration_rate': exploration_rate,
            'current_epsilon': self.epsilon
        }

def get_reward(map_tiles, pos, new_pos, cell_type, bag, target_type, last_distance):
    """
    Tính toán reward dựa trên hành động của agent
    """
    # Chi phí di chuyển cơ bản
    reward = -0.1
    
    # Tìm vật phẩm mục tiêu và khoảng cách
    target_pos, new_distance = find_nearest_object(map_tiles, new_pos, target_type)
    
    # Nếu không tìm thấy vật phẩm cùng loại, tìm vật phẩm bất kỳ
    if target_pos is None:
        target_pos, new_distance = find_nearest_object(map_tiles, new_pos)
    
    # Phần thưởng cho việc tiến gần hơn đến vật phẩm
    if target_pos and last_distance > new_distance:
        reward += 5  # Thưởng cho việc tiến gần hơn
    elif target_pos and last_distance < new_distance:
        reward -= 1  # Phạt cho việc đi xa hơn
    
    # Nhặt vật phẩm
    if isinstance(cell_type, int):
        if target_type is None or cell_type == target_type:
            # Thưởng lớn cho việc nhặt đúng loại
            reward += 30
            
            # Thưởng thêm nếu có khả năng tạo combo
            if _check_combo_potential(bag + [cell_type], cell_type):
                reward += 40
        else:
            # Phạt nặng cho việc nhặt sai loại
            reward -= 50
    
    # Thêm thưởng cho việc không đi qua vật phẩm khác loại khi túi không rỗng
    if target_type is not None:
        nearby_cells = []
        for dir_name, (dx, dy) in DIRECTIONS:
            nx, ny = new_pos[0] + dx, new_pos[1] + dy
            if 0 <= nx < len(map_tiles[0]) and 0 <= ny < len(map_tiles):
                cell = map_tiles[ny][nx]
                if isinstance(cell, int) and cell != target_type:
                    nearby_cells.append(cell)
        
        # Thưởng cho việc không đi gần vật phẩm khác loại
        if nearby_cells:
            reward += 0.5  # Thưởng khi tránh được vật phẩm khác loại
    
    return reward, new_distance

def train_agent(map_tiles, num_episodes=1000, max_steps=500, save_interval=1000):
    """
    Huấn luyện agent Q-learning với random map định kỳ
    """
    agent = QLearningAgent()
    total_rewards = []
    avg_rewards = []
    
    # Biến theo dõi thời gian
    start_time = time.time()
    last_save_time = start_time
    
    # Tạo bản sao ban đầu của map để không ảnh hưởng đến map gốc
    original_map = [row[:] for row in map_tiles]
    
    # Giám sát Q-value
    q_value_samples = []
    sample_states = []
    sample_actions = []
    
    for episode in range(num_episodes):
        # Random lại vật phẩm sau mỗi 500 episode
        if episode % 500 == 0:
            # Tạo lại bản đồ từ bản gốc (chỉ giữ tường và không gian trống)
            current_map = [row[:] for row in original_map]
            for i in range(len(current_map)):
                for j in range(len(current_map[i])):
                    # Giữ lại các bức tường và ô trống, xóa các vật phẩm
                    if isinstance(current_map[i][j], int):
                        current_map[i][j] = ' '
            
            # Random vật phẩm mới vào bản đồ
            from map_handler import place_random_objects
            place_random_objects(current_map, len(current_map))
            print(f"*** Random lại vật phẩm cho episode {episode} ***")
        else:
            # Tạo bản sao của map hiện tại để sử dụng
            current_map = [row[:] for row in map_tiles]
        
        # Khởi tạo vị trí người chơi ngẫu nhiên
        player_pos = (random.randint(0, len(current_map[0])-1), random.randint(0, len(current_map)-1))
        # Đảm bảo vị trí bắt đầu là ô trống
        while isinstance(current_map[player_pos[1]][player_pos[0]], str) and current_map[player_pos[1]][player_pos[0]] != ' ':
            player_pos = (random.randint(0, len(current_map[0])-1), random.randint(0, len(current_map)-1))
        
        bag = []
        episode_reward = 0
        steps_taken = 0
        
        # Khởi tạo target_type và last_distance
        target_type = None
        target_pos, last_distance = find_nearest_object(current_map, player_pos, target_type)
        
        # Tạo một số cặp (state, action) mẫu để theo dõi
        if episode == 0:
            for _ in range(5):
                sample_state = get_state_key(player_pos, current_map, -1)
                valid_actions = get_available_actions(current_map, player_pos)
                if valid_actions:
                    sample_action = random.choice(valid_actions)
                    sample_states.append(sample_state)
                    sample_actions.append(sample_action)
        
        for step in range(max_steps):
            # Kiểm tra nếu không còn vật phẩm nào trên bản đồ
            if not any(isinstance(current_map[y][x], int) for y in range(len(current_map)) for x in range(len(current_map[0]))):
                # Reward bổ sung khi hoàn thành tất cả vật phẩm
                episode_reward += 50
                break
            
            # Xác định trạng thái hiện tại
            last_item_type = bag[-1] if bag else -1  # -1 nếu túi rỗng
            state = get_state_key(player_pos, current_map, last_item_type)
            
            # Xác định các hành động hợp lệ từ vị trí hiện tại
            valid_actions = get_available_actions(current_map, player_pos)
            
            if not valid_actions:
                break
            
            # Chọn hành động
            action = agent.choose_action(state, valid_actions)
            
            # Thực hiện hành động
            direction, (dx, dy) = DIRECTIONS[action]
            new_pos = (player_pos[0] + dx, player_pos[1] + dy)
            
            # Kiểm tra ô mới đi đến
            x, y = new_pos
            new_cell = current_map[y][x]
            
            # Cập nhật target_type
            if bag:
                target_type = bag[-1]
            
            # Tính toán reward
            reward, new_distance = get_reward(current_map, player_pos, new_pos, new_cell, bag, target_type, last_distance)
            last_distance = new_distance
            
            # Cập nhật túi nếu nhặt vật phẩm
            if isinstance(new_cell, int):
                # Chỉ nhặt nếu điều kiện phù hợp (túi rỗng hoặc cùng loại)
                if not bag or new_cell == bag[-1]:
                    bag.append(new_cell)
                    if len(bag) > BAG_SIZE:
                        bag.pop(0)
                    current_map[y][x] = ' '  # Xóa vật phẩm khỏi bản đồ
                    
                    # Kiểm tra combo
                    for obj in range(5):  # Các loại vật phẩm từ 0 đến 4
                        need, points = COMBO_RULES[obj]
                        for i in range(len(bag) - need + 1):
                            if all(bag[i+j] == obj for j in range(need)):
                                # Có combo, thưởng điểm
                                reward += points / 10  # Chia để tránh giá trị quá lớn
                                # Xóa phần tử combo khỏi túi
                                for _ in range(need):
                                    bag.pop(i)
            
            # Xác định trạng thái mới
            player_pos = new_pos
            last_item_type = bag[-1] if bag else -1
            next_state = get_state_key(player_pos, current_map, last_item_type)
            next_valid_actions = get_available_actions(current_map, player_pos)
            
            # Cập nhật Q-value
            agent.update_q_value(state, action, reward, next_state, next_valid_actions)
            
            episode_reward += reward
            steps_taken += 1
        
        # Thưởng thêm cho việc hoàn thành nhanh
        if steps_taken < max_steps / 2:
            episode_reward += 20
        
        # Giảm epsilon sau mỗi episode
        agent.decay_epsilon()
        total_rewards.append(episode_reward)
        
        # Tính average reward cho 100 episodes gần nhất
        if episode >= 99:
            avg_reward = sum(total_rewards[-100:]) / 100
            avg_rewards.append(avg_reward)
        else:
            avg_reward = sum(total_rewards) / (episode + 1)
            avg_rewards.append(avg_reward)
        
        # Lấy mẫu Q-values để theo dõi
        if sample_states:
            q_values = []
            for s, a in zip(sample_states, sample_actions):
                q_values.append(agent.get_q_value(s, a))
            q_value_samples.append(q_values)
        
        # In thông tin tiến trình
        if (episode + 1) % 100 == 0:
            current_time = time.time()
            elapsed = current_time - start_time
            stats = agent.get_statistics()
            
            print(f"Episode {episode+1}/{num_episodes}, Avg Reward: {avg_reward:.2f}, Epsilon: {agent.epsilon:.4f}")
            print(f"Steps: {steps_taken}, Time: {elapsed:.1f}s, Q-table size: {stats['q_table_size']}")
            print(f"Explore/Exploit: {stats['exploration_rate']:.2f} ({stats['explored_actions']}/{stats['exploited_actions']})")
            
            if q_value_samples:
                last_samples = q_value_samples[-1]
                print(f"Sample Q-values: {', '.join([f'{q:.2f}' for q in last_samples])}")
            
            print("-" * 50)
        
        # Lưu Q-table định kỳ
        if (episode + 1) % save_interval == 0:
            current_time = time.time()
            if current_time - last_save_time > 60:  # Chỉ lưu nếu đã qua ít nhất 1 phút
                agent.save_q_table()
                last_save_time = current_time
                
                # Vẽ biểu đồ rewards (cần matplotlib)
                try:
                    import matplotlib.pyplot as plt
                    plt.figure(figsize=(12, 6))
                    plt.subplot(1, 2, 1)
                    plt.plot(total_rewards[-1000:])
                    plt.title('Episode Rewards (Last 1000)')
                    plt.xlabel('Episode')
                    plt.ylabel('Reward')
                    
                    plt.subplot(1, 2, 2)
                    plt.plot(avg_rewards)
                    plt.title('Average Rewards (Window=100)')
                    plt.xlabel('Episode')
                    plt.ylabel('Avg Reward')
                    
                    plt.tight_layout()
                    plt.savefig('qlearning_progress16.png')
                    plt.close()
                    
                    # Vẽ biểu đồ Q-values
                    if q_value_samples:
                        plt.figure(figsize=(10, 5))
                        for i, values in enumerate(zip(*q_value_samples)):
                            plt.plot(values, label=f'State-Action {i+1}')
                        plt.title('Q-values Over Time')
                        plt.xlabel('Episode (sampled)')
                        plt.ylabel('Q-value')
                        plt.legend()
                        plt.savefig('qlearning_qvalues16.png')
                        plt.close()
                        
                    print("Đã lưu biểu đồ tiến trình")
                except ImportError:
                    print("Không thể vẽ biểu đồ (matplotlib không được cài đặt)")
    
    # Lưu Q-table cuối cùng
    agent.save_q_table()
    
    # Vẽ biểu đồ rewards sau khi huấn luyện
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(12, 6))
        
        plt.subplot(1, 2, 1)
        plt.plot(total_rewards)
        plt.title('Episode Rewards')
        plt.xlabel('Episode')
        plt.ylabel('Reward')
        
        plt.subplot(1, 2, 2)
        plt.plot(avg_rewards)
        plt.title('Average Rewards (Window=100)')
        plt.xlabel('Episode')
        plt.ylabel('Avg Reward')
        
        plt.tight_layout()
        plt.savefig('qlearning_rewards16.png')
        print("Đã lưu biểu đồ rewards vào qlearning_rewards16.png")
    except ImportError:
        print("Không thể vẽ biểu đồ rewards (matplotlib không được cài đặt)")
    
    return agent, total_rewards, avg_rewards

def is_valid_move(map_tiles, pos, action, target_type):
    """
    Kiểm tra xem hành động có hợp lệ không - không dẫn đến vật phẩm khác loại
    """
    # Nếu không có target_type, mọi ô đều hợp lệ
    if target_type is None:
        return True
        
    direction, (dx, dy) = DIRECTIONS[action]
    nx, ny = pos[0] + dx, pos[1] + dy
    
    # Kiểm tra ô mới
    rows = len(map_tiles)
    cols = len(map_tiles[0])
    if 0 <= nx < cols and 0 <= ny < rows:
        cell = map_tiles[ny][nx]
        # Nếu là vật phẩm và khác loại mục tiêu
        if isinstance(cell, int) and cell != target_type:
            return False
    
    return True

def has_clear_path(map_tiles, pos1, pos2):
    """
    Kiểm tra xem có đường đi trực tiếp không bị chắn bởi tường hay không
    Trả về True nếu có đường thẳng không bị chắn, False nếu có vật cản
    """
    if pos2 is None:
        return False
        
    x1, y1 = pos1
    x2, y2 = pos2
    
    # Nếu hai điểm trùng nhau
    if x1 == x2 and y1 == y2:
        return True
    
    # Kiểm tra ngay nếu hai điểm ở cạnh nhau
    if abs(x1 - x2) + abs(y1 - y2) == 1:
        # Nếu hai điểm kề nhau, không cần kiểm tra thêm
        return True
    
    # Trường hợp di chuyển theo hàng ngang
    if y1 == y2:
        start_x, end_x = min(x1, x2), max(x1, x2)
        for x in range(start_x + 1, end_x):
            if isinstance(map_tiles[y1][x], str) and map_tiles[y1][x] != ' ':
                return False
        return True
    
    # Trường hợp di chuyển theo hàng dọc
    if x1 == x2:
        start_y, end_y = min(y1, y2), max(y1, y2)
        for y in range(start_y + 1, end_y):
            if isinstance(map_tiles[y][x1], str) and map_tiles[y][x1] != ' ':
                return False
        return True
    
    # Nếu hai điểm không nằm trên một đường thẳng, đường đi sẽ là đường gấp khúc
    # Cần di chuyển theo hàng ngang rồi dọc hoặc ngược lại
    # Kiểm tra nếu đi theo hàng ngang trước
    has_horizontal_first = True
    for x in range(min(x1, x2) + 1, max(x1, x2)):
        if isinstance(map_tiles[y1][x], str) and map_tiles[y1][x] != ' ':
            has_horizontal_first = False
            break
    
    for y in range(min(y1, y2) + 1, max(y1, y2)):
        if isinstance(map_tiles[y][x2], str) and map_tiles[y][x2] != ' ':
            has_horizontal_first = False
            break
    
    # Kiểm tra nếu đi theo hàng dọc trước
    has_vertical_first = True
    for y in range(min(y1, y2) + 1, max(y1, y2)):
        if isinstance(map_tiles[y][x1], str) and map_tiles[y][x1] != ' ':
            has_vertical_first = False
            break
    
    for x in range(min(x1, x2) + 1, max(x1, x2)):
        if isinstance(map_tiles[y2][x], str) and map_tiles[y2][x] != ' ':
            has_vertical_first = False
            break
    
    # Nếu có ít nhất một đường đi không bị chắn
    return has_horizontal_first or has_vertical_first

def qlearning_search(map_tiles, start_pos, bag):
    """
    Sử dụng thuần túy Q-learning để tìm đường đi
    
    1. Nếu túi rỗng: Nhặt vật phẩm gần nhất bất kỳ
    2. Nếu túi không rỗng: Nhặt vật phẩm gần nhất có cùng loại
       Nếu không còn vật phẩm cùng loại: Nhặt vật phẩm gần nhất bất kỳ
    
    CẢI TIẾN: Đảm bảo không đi qua vật phẩm khác loại khi túi không rỗng
    """
    agent = QLearningAgent()
    
    # Hiển thị thông tin Q-table
    q_table_size = len(agent.q_table)
    print(f"Q-table đã tải: {q_table_size} trạng thái")
    
    # Khởi tạo biến đếm Q-table hit
    q_hits = 0
    
    # Khởi tạo path và trạng thái
    path = []
    current_pos = start_pos
    visited = set([current_pos])
    
    # Xác định loại vật phẩm mục tiêu
    target_type = None
    if bag:
        target_type = bag[-1]  # Loại vật phẩm cuối cùng trong túi
    
    # Tìm vị trí vật phẩm mục tiêu để ghi nhận
    target_pos, _ = find_nearest_object(map_tiles, start_pos, target_type)
    if target_pos is None:
        target_pos, _ = find_nearest_object(map_tiles, start_pos)
    
    max_steps = 100  # Giới hạn số bước
    last_distance = float('inf')
    
    for step in range(max_steps):
        # Kiểm tra nếu đã đến vật phẩm mục tiêu
        x, y = current_pos
        current_cell = map_tiles[y][x]
        
        if isinstance(current_cell, int):
            if target_type is None or current_cell == target_type:
                # Đã đến đích, dừng lại
                break
        
        # Xác định trạng thái
        last_item_type = bag[-1] if bag else -1
        state = get_state_key(current_pos, map_tiles, last_item_type)
        
        # Xác định các hành động hợp lệ
        all_valid_actions = get_available_actions(map_tiles, current_pos)
        
        if not all_valid_actions:
            break
            
        # *** CẢI TIẾN: Lọc các hành động dẫn đến vật phẩm khác loại ***
        valid_actions = []
        for action in all_valid_actions:
            if is_valid_move(map_tiles, current_pos, action, target_type):
                valid_actions.append(action)
        
        # Nếu không còn hành động hợp lệ, có thể phải đi đường vòng
        # hoặc không có đường đi đến mục tiêu
        if not valid_actions:
            if target_type is not None:
                # Thử tìm vật phẩm cùng loại ở vị trí khác
                new_target_pos, _ = find_nearest_object(map_tiles, current_pos, target_type)
                if new_target_pos is None:
                    # Nếu không tìm thấy vật phẩm cùng loại, chuyển sang nhặt bất kỳ
                    target_type = None
                    target_pos, _ = find_nearest_object(map_tiles, current_pos)
                    # Sử dụng lại tất cả hành động
                    valid_actions = all_valid_actions
                else:
                    # Cập nhật target_pos và thử tìm đường mới
                    target_pos = new_target_pos
                    # Sử dụng lại all_valid_actions vì chúng ta sẽ tính toán lại đường đi
                    valid_actions = all_valid_actions
            
            # Nếu vẫn không có hành động hợp lệ, dừng tìm kiếm
            if not valid_actions:
                break
        
        # Tìm hành động tốt nhất theo Q-table (chỉ từ các hành động hợp lệ)
        q_values = []
        for action in valid_actions:
            q_pair = (state, action)
            if q_pair in agent.q_table:
                q_hits += 1
            q_values.append(agent.get_q_value(state, action))
            
        best_val = max(q_values)
        best_actions = [action for action, val in zip(valid_actions, q_values) if val == best_val]
        
        # Khởi tạo best_action mặc định
        best_action = None
        
        # Nếu tất cả Q-values bằng 0 hoặc rất nhỏ, ưu tiên di chuyển về phía vật phẩm mục tiêu
        if (all(val == 0 or val < 0.1 for val in q_values) and target_pos):
            # Chọn hướng tiến gần nhất đến mục tiêu
            min_distance = float('inf')
            for action in valid_actions:
                dir_dx, dir_dy = DIRECTIONS[action][1]
                new_x = current_pos[0] + dir_dx
                new_y = current_pos[1] + dir_dy
                new_pos_to_check = (new_x, new_y)
                
                # Sử dụng khoảng cách có xét đến vật cản
                dist = get_distance_with_obstacles(map_tiles, new_pos_to_check, target_pos)
                if dist < min_distance:
                    min_distance = dist
                    best_action = action
        
        if best_action is None:
            # Nếu không tìm được hành động tốt nhất từ các heuristic, sử dụng Q-value
            best_action = random.choice(best_actions) if best_actions else None
            if best_action is None:
                break
        
        # Thực hiện hành động
        direction, (dx, dy) = DIRECTIONS[best_action]
        next_pos = (current_pos[0] + dx, current_pos[1] + dy)
        
        # *** CẢI TIẾN: Kiểm tra lần cuối trước khi đi để đảm bảo không đi qua vật phẩm khác loại ***
        nx, ny = next_pos
        next_cell = map_tiles[ny][nx]
        if target_type is not None and isinstance(next_cell, int) and next_cell != target_type:
            # Nếu ô tiếp theo có vật phẩm khác loại, tìm hành động khác
            alternative_actions = [a for a in valid_actions if a != best_action]
            if not alternative_actions:
                # Không có hành động thay thế, phải dừng lại
                break
            
            # Chọn hành động thay thế
            alt_action = random.choice(alternative_actions)
            direction, (dx, dy) = DIRECTIONS[alt_action]
            next_pos = (current_pos[0] + dx, current_pos[1] + dy)
            
            # Kiểm tra lại một lần nữa
            nx, ny = next_pos
            next_cell = map_tiles[ny][nx]
            if target_type is not None and isinstance(next_cell, int) and next_cell != target_type:
                # Vẫn là vật phẩm khác loại, dừng lại
                break
        
        # Kiểm tra trùng lặp để tránh vòng lặp vô hạn
        if next_pos in visited:
            # Nếu đã thăm, chọn ngẫu nhiên một ô khác
            alternative_actions = [a for a in valid_actions if a != best_action]
            if not alternative_actions:
                break  # Không còn hành động thay thế
            
            alt_action = random.choice(alternative_actions)
            direction, (dx, dy) = DIRECTIONS[alt_action]
            next_pos = (current_pos[0] + dx, current_pos[1] + dy)
            
            # Kiểm tra lại một lần nữa
            nx, ny = next_pos
            next_cell = map_tiles[ny][nx]
            if target_type is not None and isinstance(next_cell, int) and next_cell != target_type:
                # Vẫn là vật phẩm khác loại, dừng lại
                break
                
            # Nếu vẫn đã thăm, bỏ qua
            if next_pos in visited:
                break
        
        # Thêm vào đường đi
        path.append((direction, next_pos))
        visited.add(next_pos)
        
        # Kiểm tra nếu đi đến vật phẩm mục tiêu
        nx, ny = next_pos
        cell = map_tiles[ny][nx]
        if isinstance(cell, int):
            if target_type is None or cell == target_type:
                # Đã đến đích, dừng lại
                current_pos = next_pos
                break
            else:
                # Đi đến vật phẩm khác loại (không nên xảy ra sau các kiểm tra)
                print(f"Lỗi: Đi đến vật phẩm khác loại. Túi có {target_type}, đi đến {cell}")
                break
        
        # Tính khoảng cách mới đến mục tiêu
        if target_pos:
            new_distance = get_distance_with_obstacles(map_tiles, next_pos, target_pos)
            if new_distance >= last_distance and len(path) > 10:
                # Nếu không tiến gần hơn sau 10 bước, có thể bị lặp
                # Tìm lại vật phẩm mục tiêu
                if target_type is not None:
                    target_pos, _ = find_nearest_object(map_tiles, next_pos, target_type)
                if target_pos is None:
                    target_pos, _ = find_nearest_object(map_tiles, next_pos)
                last_distance = get_distance_with_obstacles(map_tiles, next_pos, target_pos) if target_pos else float('inf')
            else:
                last_distance = new_distance
        
        # Cập nhật vị trí hiện tại
        current_pos = next_pos
    
    # In thống kê chỉ về Q-table hits
    print(f"Tìm đường xong: {len(path)} bước | Q-table hits: {q_hits}")
    
    return path

def main():
    """
    Hàm main để huấn luyện và kiểm tra thuật toán Q-learning
    """
    from map_handler import load_map_from_file, place_random_objects
    
    # Tải map mặc định
    GRID_SIZE = 25
    map_file = "map_design.txt"
    map_tiles = load_map_from_file(map_file, GRID_SIZE)
    
    # Khởi tạo ngẫu nhiên các vật phẩm
    place_random_objects(map_tiles, GRID_SIZE)
    
    # Huấn luyện agent
    print("Bắt đầu huấn luyện Q-learning...")
    agent, rewards, avg_rewards = train_agent(map_tiles, num_episodes=5000, max_steps=500, save_interval=1000)
    
    # Kiểm tra thuật toán
    start_pos = (GRID_SIZE // 2, GRID_SIZE // 2)
    bag = []
    
    print("\nKiểm tra tìm đường với túi rỗng:")
    path = qlearning_search(map_tiles, start_pos, bag)
    print(f"Tìm thấy đường đi với {len(path)} bước")
    
    # Mô phỏng nhặt vật phẩm đầu tiên
    if path:
        last_pos = path[-1][1]
        x, y = last_pos
        if isinstance(map_tiles[y][x], int):
            bag.append(map_tiles[y][x])
            print(f"Đã nhặt vật phẩm loại {map_tiles[y][x]}")
            # Đánh dấu vị trí đã nhặt
            map_tiles[y][x] = " "
    
    print("\nKiểm tra tìm đường với túi có vật phẩm:")
    path = qlearning_search(map_tiles, last_pos, bag)
    print(f"Tìm thấy đường đi với {len(path)} bước")

if __name__ == "__main__":
    main()
