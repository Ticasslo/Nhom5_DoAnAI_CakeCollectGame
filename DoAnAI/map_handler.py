#map_handler.py
import os
import sys
import random

def load_map_from_file(filename, GRID_SIZE):
    """
    Đọc và tải bản đồ từ file thiết kế
    
    Tham số:
        filename: Tên file thiết kế map
        GRID_SIZE: Kích thước lưới (25x25)
    
    Trả về:
        design_map: Ma trận 2D chứa thông tin bản đồ
    """
    if not os.path.exists(filename):
        print(f"File {filename} không tồn tại. Vui lòng tạo file thiết kế trước.")
        sys.exit()

    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if len(lines) != GRID_SIZE:
        print("File map không đúng kích thước 25 dòng. Mỗi dòng cần 25 ký tự.")
        sys.exit()

    design_map = []
    for line in lines:
        row = list(line.rstrip("\n"))
        if len(row) != GRID_SIZE:
            print("Một dòng không đủ 25 ký tự.", row)
            sys.exit()
        new_row = []
        for ch in row:
            if ch in ["T", "W", "X", "B", "H", "G"]:
                new_row.append(ch)
            elif ch in ["0", "1", "2", "3", "4"]:
                new_row.append(int(ch))
            else:
                new_row.append(" ")
        design_map.append(new_row)

    return design_map

def place_random_objects(map_tiles, GRID_SIZE, player_positions=None):
    """
    Chèn các vật thể vào map theo số lượng:
      - 2 vật thể loại 0
      - 3 vật thể loại 1
      - 4 vật thể loại 2
      - 5 vật thể loại 3
      - 6 vật thể loại 4
    Đảm bảo mỗi vật thể cách nhau ít nhất 1 ô.
    Không đặt vật thể ở vị trí người chơi và xung quanh.
    Chỉ chèn vào ô trống (được đánh dấu là " ").
    
    Tham số:
        map_tiles: Ma trận 2D chứa thông tin bản đồ
        GRID_SIZE: Kích thước lưới
        player_positions: Danh sách các vị trí người chơi [(x1, y1), (x2, y2), ...]
    """
    # Định nghĩa số lượng cho từng loại vật thể
    placements = {
        0: 2,
        1: 3,
        2: 4,
        3: 5,
        4: 6
    }
    
    # Khởi tạo player_positions nếu không được cung cấp
    if player_positions is None:
        player_positions = []
    
    # Tìm tất cả các vị trí ô trống ban đầu
    valid_positions = []
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if map_tiles[i][j] == " ":  # Ô trống
                valid_positions.append((i, j))
    
    # Danh sách vị trí đã bị chặn (bao gồm vật thể và các ô xung quanh)
    blocked_positions = set()
    
    # Hướng di chuyển để kiểm tra các ô lân cận (8 hướng)
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]
    
    # Thêm vị trí của tất cả người chơi và các ô xung quanh vào danh sách bị chặn
    for player_pos in player_positions:
        player_x, player_y = player_pos
        player_pos_grid = (player_y, player_x)  # Chuyển từ (x, y) sang (hàng, cột)
        
        blocked_positions.add(player_pos_grid)
        for di, dj in directions:
            ni, nj = player_pos_grid[0] + di, player_pos_grid[1] + dj
            if 0 <= ni < GRID_SIZE and 0 <= nj < GRID_SIZE:
                blocked_positions.add((ni, nj))
    
    # Với mỗi loại vật thể, chèn số lượng theo yêu cầu
    for obj_type, count in placements.items():
        placed = 0
        while placed < count and valid_positions:
            # Lọc ra các vị trí hợp lệ (không bị chặn)
            current_valid = [pos for pos in valid_positions if pos not in blocked_positions]
            
            if not current_valid:
                print(f"Không đủ ô trống để chèn vật thể loại {obj_type}")
                break
                
            # Chọn ngẫu nhiên một vị trí hợp lệ
            pos = random.choice(current_valid)
            i, j = pos
            
            # Đặt vật thể
            map_tiles[i][j] = obj_type
            placed += 1
            
            # Loại bỏ vị trí đã chọn khỏi danh sách các vị trí hợp lệ
            valid_positions.remove(pos)
            
            # Đánh dấu vị trí đã đặt và các ô lân cận là đã bị chặn
            blocked_positions.add(pos)
            for di, dj in directions:
                ni, nj = i + di, j + dj
                if 0 <= ni < GRID_SIZE and 0 <= nj < GRID_SIZE:
                    blocked_positions.add((ni, nj)) 
                    
def place1_random_object(map_tiles, GRID_SIZE, obj_type, player_positions=None):
    """
    Chèn một vật thể với loại cụ thể vào một vị trí ngẫu nhiên trên bản đồ
    Đảm bảo vật thể mới cách các vật thể hiện có ít nhất 1 ô
    Không đặt vật thể ở vị trí người chơi và xung quanh
    
    Tham số:
        map_tiles: Ma trận 2D chứa thông tin bản đồ
        GRID_SIZE: Kích thước lưới
        obj_type: Loại vật thể cần chèn (0-4)
        player_positions: Danh sách các vị trí người chơi [(x1, y1), (x2, y2), ...]
        
    Trả về:
        tuple: Vị trí (x, y) của vật thể mới được chèn, hoặc None nếu không thể chèn
    """
    # Kiểm tra loại vật thể hợp lệ
    if obj_type not in range(5):
        print(f"Loại vật thể không hợp lệ: {obj_type}. Phải trong khoảng 0-4.")
        return None
    
    # Khởi tạo player_positions nếu không được cung cấp
    if player_positions is None:
        player_positions = []
    
    # Tìm tất cả các vị trí đã có vật thể (các số từ 0-4)
    existing_objects = []
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if isinstance(map_tiles[i][j], int):
                existing_objects.append((i, j))
    
    # Tìm các vị trí bị chặn (vật thể hiện có và các ô xung quanh)
    blocked_positions = set()
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]
    
    # Thêm vị trí của tất cả người chơi và các ô xung quanh vào danh sách bị chặn
    for player_pos in player_positions:
        player_x, player_y = player_pos
        player_pos_grid = (player_y, player_x)  # Chuyển từ (x, y) sang (hàng, cột)
        
        blocked_positions.add(player_pos_grid)
        for di, dj in directions:
            ni, nj = player_pos_grid[0] + di, player_pos_grid[1] + dj
            if 0 <= ni < GRID_SIZE and 0 <= nj < GRID_SIZE:
                blocked_positions.add((ni, nj))
    
    # Thêm vị trí các vật thể hiện có và ô xung quanh vào danh sách bị chặn
    for i, j in existing_objects:
        blocked_positions.add((i, j))  # Vị trí vật thể
        # Các ô xung quanh
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if 0 <= ni < GRID_SIZE and 0 <= nj < GRID_SIZE:
                blocked_positions.add((ni, nj))
    
    # Tìm tất cả các vị trí ô trống và không bị chặn
    valid_positions = []
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if map_tiles[i][j] == " " and (i, j) not in blocked_positions:
                valid_positions.append((i, j))
    
    # Kiểm tra có ô trống hợp lệ không
    if not valid_positions:
        print("Không có ô trống phù hợp trên bản đồ để chèn vật thể.")
        return None
    
    # Chọn ngẫu nhiên một vị trí
    pos = random.choice(valid_positions)
    i, j = pos
    
    # Chèn vật thể vào vị trí đã chọn
    map_tiles[i][j] = obj_type
    
    # Trả về vị trí (j, i) - theo tọa độ x, y
    return (j, i)