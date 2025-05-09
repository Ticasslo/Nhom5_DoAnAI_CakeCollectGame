import pygame
import random
import sys
import os
from collections import deque
import time

from searchBFS import bfs_search
from animations import AnimationManager
from assets import load_assets, load_sounds
from map_handler import load_map_from_file, place_random_objects

# Khởi tạo pygame
pygame.init()

# --- CÀI ĐẶT MAP ---
GRID_SIZE = 17             # Map thiết kế (17x17)
TILE_SIZE = 37
WIDTH, HEIGHT = TILE_SIZE * GRID_SIZE, TILE_SIZE * GRID_SIZE
INFO_HEIGHT = 140

PANEL_WIDTH = 200
SCREEN_WIDTH = WIDTH + PANEL_WIDTH
SCREEN_HEIGHT = HEIGHT + INFO_HEIGHT

# Quy tắc combo không thay đổi
COMBO_RULES = {
    0: (2, 200),
    1: (3, 300),
    2: (4, 400),
    3: (5, 500),
    4: (6, 600)
}
BAG_SIZE = 7

# Thêm vào phần khởi tạo pygame
pygame.mixer.init()

# --- KHỞI TẠO MÀN HÌNH ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Game AI Player")
clock = pygame.time.Clock()

# Áp dụng tài nguyên âm thanh và vật thể
sound_assets = load_sounds()
assets = load_assets(TILE_SIZE)

# --- HÀM VẼ CÁC THÀNH PHẦN ---
def draw_grid():
    for x in range(0, WIDTH, TILE_SIZE):
        pygame.draw.line(screen, (200,200,200), (x,0), (x,HEIGHT))
    for y in range(0, HEIGHT, TILE_SIZE):
        pygame.draw.line(screen, (200,200,200), (0,y), (WIDTH,y))

def draw_map(map_tiles):
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            rect = pygame.Rect(j * TILE_SIZE, i * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            
            screen.blit(assets["floor"], rect)
            
            cell = map_tiles[i][j]
            if cell in ["T", "W", "X", "B", "H", "G"]:
                # Nếu ô là wall do thiết kế, lấy ảnh tương ứng từ assets["wall"]
                if cell in assets["wall"]:
                    screen.blit(assets["wall"][cell], rect)
                else:
                    pygame.draw.rect(screen, (128,128,128), rect)
            elif cell == " ":
                screen.blit(assets["floor"], rect)
            else:
                # Ô chứa vật thể (0..4)
                if cell in assets["object"]:
                    screen.blit(assets["object"][cell], rect)
                else:
                    pygame.draw.rect(screen, (255,255,255), rect)

def draw_player(x, y):
    rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
    screen.blit(assets["player"], rect)

def draw_path(path):
    """Vẽ đường đi của AI"""
    if not path:
        return
        
    for _, pos in path:
        x, y = pos
        rect = pygame.Rect(x * TILE_SIZE + TILE_SIZE//4, y * TILE_SIZE + TILE_SIZE//4, TILE_SIZE//2, TILE_SIZE//2)
        pygame.draw.rect(screen, (255, 100, 100, 128), rect, border_radius=5)

def draw_info(bag, score):
    info_rect = pygame.Rect(0, HEIGHT, SCREEN_WIDTH, INFO_HEIGHT)
    pygame.draw.rect(screen, (220,220,220), info_rect)
    
    font = pygame.font.SysFont(None, 28)
    score_text = font.render(f"Score: {score}", True, (0,0,0))
    screen.blit(score_text, (10, HEIGHT + 10))
    
    bag_text = font.render("Bag:", True, (0,0,0))
    screen.blit(bag_text, (10, HEIGHT + 50))
    
    for idx in range(BAG_SIZE):
        slot_rect = pygame.Rect(80 + idx * (TILE_SIZE + 5), HEIGHT + 45, TILE_SIZE, TILE_SIZE)
        screen.blit(assets["floor"], slot_rect)
        pygame.draw.rect(screen, (0,0,0), slot_rect, 1)
        if idx < len(bag):
            value = bag[idx]
            if value in assets["object"]:
                screen.blit(assets["object"][value], slot_rect)
            else:
                pygame.draw.rect(screen, (255,255,255), slot_rect)
    
    # Vẽ các điều khiển AI
    draw_ai_controls()

class ScrollablePathPanel:
    def __init__(self, x, y, width, height, font_size=18):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.SysFont(None, font_size)
        self.path_steps = []
        self.scroll_y = 0
        self.line_height = font_size + 4
        self.visible_lines = height // self.line_height
        self.scrollbar_width = 15
        self.dragging = False
        
    def set_path(self, path):
        self.path_steps = []
        for i, (direction, pos) in enumerate(path):
            x, y = pos
            self.path_steps.append(f"Step {i+1}: {direction} -> ({x},{y})")
        
    def draw(self, surface):
        # Draw panel background
        pygame.draw.rect(surface, (240, 240, 240), self.rect)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2)
        
        # Draw title
        title = self.font.render("AI Path Steps", True, (0, 0, 0))
        title_rect = title.get_rect(center=(self.rect.centerx, self.rect.y + 15))
        surface.blit(title, title_rect)
        
        # Create content area
        content_rect = pygame.Rect(
            self.rect.x + 5, 
            self.rect.y + 35, 
            self.rect.width - self.scrollbar_width - 10, 
            self.rect.height - 40
        )
        pygame.draw.rect(surface, (255, 255, 255), content_rect)
        pygame.draw.rect(surface, (200, 200, 200), content_rect, 1)
        
        # Create clipping area for text
        content_surface = pygame.Surface((content_rect.width, content_rect.height))
        content_surface.fill((255, 255, 255))
        
        # Draw path steps
        max_scroll = max(0, len(self.path_steps) * self.line_height - content_rect.height)
        self.scroll_y = min(self.scroll_y, max_scroll)
        
        for i, step in enumerate(self.path_steps):
            y_pos = i * self.line_height - self.scroll_y
            if -self.line_height <= y_pos < content_rect.height:
                text = self.font.render(step, True, (0, 0, 0))
                content_surface.blit(text, (5, y_pos))
        
        # Draw content with clipping
        surface.blit(content_surface, content_rect)
        
        # Draw scrollbar if needed
        if len(self.path_steps) * self.line_height > content_rect.height:
            scrollbar_rect = pygame.Rect(
                self.rect.right - self.scrollbar_width - 5,
                content_rect.y,
                self.scrollbar_width,
                content_rect.height
            )
            pygame.draw.rect(surface, (220, 220, 220), scrollbar_rect)
            
            # Calculate thumb size and position
            visible_ratio = min(1.0, content_rect.height / (len(self.path_steps) * self.line_height))
            thumb_height = max(20, int(scrollbar_rect.height * visible_ratio))
            
            if max_scroll > 0:
                thumb_y = scrollbar_rect.y + (self.scroll_y / max_scroll) * (scrollbar_rect.height - thumb_height)
            else:
                thumb_y = scrollbar_rect.y
                
            thumb_rect = pygame.Rect(
                scrollbar_rect.x,
                thumb_y,
                self.scrollbar_width,
                thumb_height
            )
            pygame.draw.rect(surface, (180, 180, 180), thumb_rect)
            pygame.draw.rect(surface, (100, 100, 100), thumb_rect, 1)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Scroll up
                self.scroll_y = max(0, self.scroll_y - self.line_height)
                return True
            elif event.button == 5:  # Scroll down
                self.scroll_y += self.line_height
                return True
            elif event.button == 1:  # Left click for scrollbar dragging
                scrollbar_rect = pygame.Rect(
                    self.rect.right - self.scrollbar_width - 5,
                    self.rect.y + 35,
                    self.scrollbar_width,
                    self.rect.height - 40
                )
                if scrollbar_rect.collidepoint(event.pos):
                    self.dragging = True
                    return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging:
                self.dragging = False
                return True
        
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            content_height = len(self.path_steps) * self.line_height
            visible_height = self.rect.height - 40
            
            if content_height > visible_height:
                # Calculate relative position and set scroll
                rel_y = event.pos[1] - (self.rect.y + 35)
                scroll_ratio = rel_y / visible_height
                self.scroll_y = int(scroll_ratio * (content_height - visible_height))
                self.scroll_y = max(0, min(self.scroll_y, content_height - visible_height))
            return True
        
        return False
    
# Tạo lớp Button để xử lý nút bấm
class Button:
    def __init__(self, x, y, width, height, text, font_size=24, color=(200, 200, 200), hover_color=(180, 180, 220)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont(None, font_size)
        self.hover = False
        self.color = color
        self.hover_color = hover_color
        
    def draw(self, surface):
        # Vẽ nền nút
        if self.hover:
            color = self.hover_color
        else:
            color = self.color
            
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2, border_radius=5)  # Viền
        
        # Vẽ text
        text_surf = self.font.render(self.text, True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.hover = self.rect.collidepoint(pos)
        return self.hover
        
    def is_clicked(self, pos, click):
        return click and self.rect.collidepoint(pos)

# Tạo lớp DropdownMenu
class DropdownMenu:
    def __init__(self, x, y, width, height, options, font_size=24):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_index = 0
        self.font = pygame.font.SysFont(None, font_size)
        self.is_opened = False
        self.option_height = height
        
        # Tính toán chiều cao khi menu mở (không cần thiết dùng biến này nếu không sử dụng trong draw)
        self.expanded_rect = pygame.Rect(x, y - height * len(options), width, height * len(options))
    
    def draw(self, surface):
        # Vẽ ô được chọn (nút chính)
        selected_color = (220, 220, 240) 
        pygame.draw.rect(surface, selected_color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2, border_radius=5)  # Viền
        
        # Vẽ text của lựa chọn hiện tại
        text_surf = self.font.render(self.options[self.selected_index], True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
        # Vẽ mũi tên chỉ menu mở lên (giờ các mục sẽ hiển thị phía trên)
        arrow_points = [
            (self.rect.right - 20, self.rect.centery + 3),
            (self.rect.right - 10, self.rect.centery + 3),
            (self.rect.right - 15, self.rect.centery - 3)
        ]
        pygame.draw.polygon(surface, (0, 0, 0), arrow_points)
        
        # Nếu menu đang mở, vẽ danh sách lựa chọn lên phía trên nút được chọn
        if self.is_opened:
            for i, option in enumerate(self.options):
                # Vẽ tất cả các lựa chọn; nếu bạn muốn bỏ qua lựa chọn đang được hiển thị thì có thể thêm điều kiện
                # Ở đây mình vẽ tất cả để dễ thay đổi, tùy theo logic bạn có thể bỏ qua mục đã chọn
                option_rect = pygame.Rect(
                    self.rect.x, 
                    self.rect.y - (i+1) * self.option_height, 
                    self.rect.width,
                    self.option_height
                )
                pygame.draw.rect(surface, (255, 255, 255), option_rect)
                pygame.draw.rect(surface, (0, 0, 0), option_rect, 1)
                
                text_surf = self.font.render(option, True, (0, 0, 0))
                text_rect = text_surf.get_rect(center=option_rect.center)
                surface.blit(text_surf, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_opened = not self.is_opened
                return True
            elif self.is_opened:
                # Nếu đang mở, kiểm tra xem có click vào lựa chọn nào không
                for i, option in enumerate(self.options):
                    option_rect = pygame.Rect(
                        self.rect.x, 
                        self.rect.y - (i+1) * self.option_height,
                        self.rect.width,
                        self.option_height
                    )
                    if option_rect.collidepoint(event.pos):
                        self.selected_index = i
                        self.is_opened = False
                        return True
                # Nếu click bên ngoài, đóng menu
                self.is_opened = False
        return False
        
    def get_selected(self):
        return self.options[self.selected_index]


# Tạo nút và dropdown cho điều khiển AI
ai_buttons = {
    "start": Button(10, HEIGHT + 90, 120, 40, "Start AI", color=(144, 238, 144), hover_color=(100, 200, 100)),
    "stop": Button(140, HEIGHT + 90, 120, 40, "Stop AI", color=(255, 200, 200), hover_color=(255, 150, 150)),
    "step": Button(270, HEIGHT + 90, 80, 40, "Step", color=(173, 216, 230), hover_color=(70, 130, 180)),
    "reset": Button(660, HEIGHT + 90, 120, 40, "RESET", color=(255, 215, 0), hover_color=(230, 190, 0))
}

ai_speed_options = ["Slow", "Normal", "Fast", "Instant"]
ai_speed_dropdown = DropdownMenu(370, HEIGHT + 90, 100, 40, ai_speed_options)

ai_algo_options = ["BFS", "DFS", "Greedy", "A*"]
ai_algo_dropdown = DropdownMenu(480, HEIGHT + 90, 170, 40, ai_algo_options)

def draw_ai_controls():
    # Vẽ các nút điều khiển khác
    for name, button in ai_buttons.items():
        # Chỉ vẽ nút RESET khi AI không chạy hoặc đã chạy hết đường đi
        if name == "reset":
            if not ai_running or (ai_path and current_path_index >= len(ai_path)):
                button.draw(screen)
        else:
            button.draw(screen)
        
    # Vẽ label cho dropdown
    font = pygame.font.SysFont(None, 22)
    speed_text = font.render("Speed:", True, (0, 0, 0))
    screen.blit(speed_text, (370, HEIGHT + 70))
    
    algo_text = font.render("Algorithm:", True, (0, 0, 0))
    screen.blit(algo_text, (480, HEIGHT + 70))
    
    # Vẽ dropdown
    ai_speed_dropdown.draw(screen)
    ai_algo_dropdown.draw(screen)

def check_combos(bag):
    global score, animations
    removed = False
    for obj, (need, points) in COMBO_RULES.items():
        if len(bag) < need:
            continue
        for i in range(len(bag) - need + 1):
            segment = bag[i:i+need]
            if all(x == obj for x in segment):
                # Tạo animation trước khi xóa vật phẩm
                positions = list(range(i, i + need))
                animation_manager.add_combo_animation(obj, positions, points)
                
                # Phát âm thanh combo
                sound_assets["combo"].play()
                
                # Xóa vật phẩm khỏi túi
                del bag[i:i+need]
                score += points
                removed = True
                return removed
    return removed

# --- KHỞI TẠO GAME ---
map_file = "map_design_small.txt"
map_tiles = load_map_from_file(map_file, GRID_SIZE)

path_panel = ScrollablePathPanel(WIDTH, 0, PANEL_WIDTH, HEIGHT)
place_random_objects(map_tiles, GRID_SIZE)
original_map_tiles = [row[:] for row in map_tiles]  # Tạo bản sao sâu của map ban đầu

player_x, player_y = GRID_SIZE // 2, GRID_SIZE // 2
animation_manager = AnimationManager(assets, TILE_SIZE, HEIGHT, sound_assets)
bag = []
score = 0

# --- BIẾN CHO AI ---
ai_running = False
step_mode = False
do_step = False
ai_path = []
current_path_index = 0
ai_speed_dict = {
    "Slow": 5,  # FPS
    "Normal": 10,
    "Fast": 20,
    "Instant": 60
}

# Hàm tính toán đường đi cho AI
def calculate_ai_path():
    global ai_path, current_path_index
    
    # Lấy thuật toán đã chọn
    algorithm = ai_algo_dropdown.get_selected()
    
    # Tạo bản sao của map để AI phân tích
    map_copy = [row[:] for row in map_tiles]
    
    # Gọi hàm tìm đường dựa trên thuật toán được chọn
    if algorithm == "BFS":
        path = bfs_search(map_copy, (player_x, player_y), bag)
    elif algorithm == "DFS":
        # Giả sử bạn đã có một hàm dfs tìm đường
        path = dfs_search(map_copy, (player_x, player_y))
    elif algorithm == "Greedy":
        # Giả sử bạn đã có một hàm greedy tìm đường
        path = greedy_search(map_copy, (player_x, player_y))
    elif algorithm == "A*":
        # Giả sử bạn đã có một hàm A* tìm đường
        path = astar_search(map_copy, (player_x, player_y))
    
    ai_path = path
    current_path_index = 0
    path_panel.set_path(path)
    return path

# --- VÒNG LẶP GAME CHÍNH ---
running = True
fps_timer = pygame.time.Clock()

while running:
    # Điều chỉnh tốc độ dựa trên lựa chọn từ dropdown
    ai_speed = ai_speed_dict[ai_speed_dropdown.get_selected()]
    fps_timer.tick(ai_speed)
    
    # Xử lý các sự kiện
    mouse_click = False
    for event in pygame.event.get():
        path_panel.handle_event(event)

        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_click = True
            
        # Xử lý dropdown
        ai_speed_dropdown.handle_event(event)
        ai_algo_dropdown.handle_event(event)
            
        # Xử lý các nút điều khiển AI
        mouse_pos = pygame.mouse.get_pos()
        
        for name, button in ai_buttons.items():
            button.check_hover(mouse_pos)
            if mouse_click and button.is_clicked(mouse_pos, True):
                if name == "start":
                    ai_running = True
                    step_mode = False
                    if not ai_path or current_path_index >= len(ai_path):
                        calculate_ai_path()
                elif name == "stop":
                    ai_running = False
                    step_mode = False
                elif name == "step":
                    step_mode = True
                    ai_running = False
                    do_step = True
                    if not ai_path:
                        calculate_ai_path()
                elif name == "reset":
                    # Logic reset game
                    ai_running = False
                    step_mode = False
                    ai_path = []
                    current_path_index = 0
                    path_panel.set_path([])  # Xóa đường đi trong panel
                    
                    # Reset vị trí người chơi về giữa bản đồ
                    player_x, player_y = GRID_SIZE // 2, GRID_SIZE // 2
                    
                    # Có thể thêm: reset túi đồ và điểm số
                    bag = []
                    score = 0
                    
                    # Khôi phục map về trạng thái ban đầu (KHÔNG tạo map mới)
                    map_tiles = [row[:] for row in original_map_tiles]
    
    # Xử lý di chuyển AI
    if (ai_running or (step_mode and do_step)) and ai_path and current_path_index < len(ai_path):
        direction, pos = ai_path[current_path_index]
        new_x, new_y = pos
        
        # Di chuyển người chơi
        player_x, player_y = new_x, new_y
        
        # Kiểm tra ô đã đến có vật phẩm không
        cell = map_tiles[player_y][player_x]
        if isinstance(cell, int):
            # Thêm hiệu ứng thu thập
            animation_manager.add_collect_animation(player_x, player_y, cell)
            sound_assets["collect"].play()
            
            # Thêm vào túi
            bag.append(cell)
            
            # Animation khi thêm vào túi đồ
            bag_position = len(bag) - 1
            if bag_position >= BAG_SIZE:
                bag_position = BAG_SIZE - 1
            animation_manager.add_bag_animation(cell, bag_position)
            
            if len(bag) > BAG_SIZE:
                bag.pop(0)
                
            # Cập nhật map
            map_tiles[player_y][player_x] = " "
            
            # Kiểm tra combo
            while check_combos(bag):
                pass
        
        # Di chuyển đến bước tiếp theo
        current_path_index += 1
        
        # Nếu đã đi hết đường, tính toán lại nếu còn vật phẩm
        if current_path_index >= len(ai_path):
            # Kiểm tra xem còn vật phẩm nào trên bản đồ không
            has_objects = False
            for row in map_tiles:
                for cell in row:
                    if isinstance(cell, int):
                        has_objects = True
                        break
                if has_objects:
                    break
                    
            if has_objects and ai_running:
                # Tính lại đường đi
                calculate_ai_path()
        
        # Reset do_step flag
        do_step = False
    
    # Vẽ màn hình game
    screen.fill((255,255,255))
    draw_map(map_tiles)
    if ai_path and not ai_running:
        # Chỉ vẽ đường đi khi AI không chạy
        draw_path(ai_path[current_path_index:] if current_path_index < len(ai_path) else [])
    draw_grid()
    draw_player(player_x, player_y)
    draw_info(bag, score)
    
    # Add this line to draw the path panel
    path_panel.draw(screen)

    # Vẽ các animation
    animation_manager.update_and_draw(screen)
    
    pygame.display.flip()

pygame.quit()