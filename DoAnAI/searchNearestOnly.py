import heapq
from collections import deque

def search_only_nearest(map_data, start_pos):
    """
    Tìm con đường đến vật phẩm gần nhất trên bản đồ.
    
    Parameters:
    - map_data: Bản đồ 2D với các ô chứa thông tin
    - start_pos: Tuple (x, y) vị trí bắt đầu của AI
    
    Returns:
    - Danh sách các bước [(direction, (x, y)), ...] để đi đến vật phẩm gần nhất
    """
    # Hướng di chuyển: phải, xuống, trái, lên
    directions = [(1, 0, "Right"), (0, 1, "Down"), (-1, 0, "Left"), (0, -1, "Up")]
    
    # Vị trí bắt đầu
    x_start, y_start = start_pos
    
    # Kiểm tra nếu đang đứng trên vật phẩm
    if isinstance(map_data[y_start][x_start], int):
        return []  # Trả về danh sách rỗng vì đã ở trên vật phẩm
    
    # Sử dụng BFS tìm đường đến vật phẩm gần nhất
    queue = deque([(x_start, y_start, [])])  # (x, y, path)
    visited = set([(x_start, y_start)])
    
    while queue:
        x, y, path = queue.popleft()
        
        # Duyệt qua 4 hướng di chuyển
        for dx, dy, direction in directions:
            nx, ny = x + dx, y + dy
            
            # Kiểm tra xem có thể di chuyển vào ô mới không
            if (0 <= ny < len(map_data) and 0 <= nx < len(map_data[0]) and 
                map_data[ny][nx] != "T" and map_data[ny][nx] != "W" and 
                map_data[ny][nx] != "X" and map_data[ny][nx] != "B" and
                map_data[ny][nx] != "H" and map_data[ny][nx] != "G" and
                (nx, ny) not in visited):
                
                # Tạo đường đi mới
                new_path = path + [(direction, (nx, ny))]
                
                # Nếu tìm thấy vật phẩm, trả về đường đi
                if isinstance(map_data[ny][nx], int):
                    return new_path
                
                # Nếu chưa tìm thấy, thêm vào hàng đợi để duyệt tiếp
                visited.add((nx, ny))
                queue.append((nx, ny, new_path))
    
    # Nếu không tìm thấy vật phẩm nào, trả về đường đi rỗng
    return []

def search_only_nearest_with_astar(map_data, start_pos):
    """
    Tìm con đường đến vật phẩm gần nhất trên bản đồ sử dụng thuật toán A*.
    
    Parameters:
    - map_data: Bản đồ 2D với các ô chứa thông tin
    - start_pos: Tuple (x, y) vị trí bắt đầu của AI
    
    Returns:
    - Danh sách các bước [(direction, (x, y)), ...] để đi đến vật phẩm gần nhất
    """
    # Hướng di chuyển: phải, xuống, trái, lên
    directions = [(1, 0, "right"), (0, 1, "down"), (-1, 0, "left"), (0, -1, "up")]
    
    # Vị trí bắt đầu
    x_start, y_start = start_pos
    
    # Kiểm tra nếu đang đứng trên vật phẩm
    if isinstance(map_data[y_start][x_start], int):
        return []  # Trả về danh sách rỗng vì đã ở trên vật phẩm
    
    # Heuristic function: Manhattan distance
    def heuristic(pos):
        # Tìm vị trí gần nhất của vật phẩm
        min_dist = float('inf')
        for y in range(len(map_data)):
            for x in range(len(map_data[0])):
                if isinstance(map_data[y][x], int):
                    dist = abs(pos[0] - x) + abs(pos[1] - y)
                    min_dist = min(min_dist, dist)
        return min_dist if min_dist != float('inf') else 0
    
    # A* algorithm
    open_set = []  # Priority Queue
    heapq.heappush(open_set, (0, 0, x_start, y_start, []))  # (f_score, g_score, x, y, path)
    
    # Visited nodes to avoid cycles
    visited = set([(x_start, y_start)])
    
    while open_set:
        _, g_score, x, y, path = heapq.heappop(open_set)
        
        # Check all four directions
        for dx, dy, direction in directions:
            nx, ny = x + dx, y + dy
            
            # Check if the new position is valid
            if (0 <= ny < len(map_data) and 0 <= nx < len(map_data[0]) and 
                map_data[ny][nx] != "T" and map_data[ny][nx] != "W" and 
                map_data[ny][nx] != "X" and map_data[ny][nx] != "B" and
                map_data[ny][nx] != "H" and map_data[ny][nx] != "G" and
                (nx, ny) not in visited):
                
                # Create new path
                new_path = path + [(direction, (nx, ny))]
                
                # If found an item, return the path
                if isinstance(map_data[ny][nx], int):
                    return new_path
                
                # Mark as visited
                visited.add((nx, ny))
                
                # Calculate scores for A*
                new_g = g_score + 1
                new_f = new_g + heuristic((nx, ny))
                
                # Add to open set
                heapq.heappush(open_set, (new_f, new_g, nx, ny, new_path))
    
    # If no path to any item is found
    return []