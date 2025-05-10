import pygame
import random
import sys
import os
from collections import deque
import time

from searchNearestOnly import search_only_nearest
from searchBFS import bfs_search
from searchDFS import dfs_search
from searchAStar import astar_search
from searchSimulatedAnnealing import simulated_annealing_search
from searchNondeterministic import nondeterministic_search
from searchBacktrackingWithFowardChecking import backtracking_with_forward_checking
from searchQLearning import qlearning_search
from animations import AnimationManager
from assets import load_assets, load_sounds
from map_handler import load_map_from_file, place_random_objects

# Khởi tạo pygame
pygame.init()

# --- CÀI ĐẶT MAP ---
GRID_SIZE = 25             # Map thiết kế (25x25)
TILE_SIZE = 22
WIDTH, HEIGHT = TILE_SIZE * GRID_SIZE, TILE_SIZE * GRID_SIZE
INFO_HEIGHT = 250 

PANEL_WIDTH = 200
SCREEN_WIDTH = WIDTH + PANEL_WIDTH * 3
SCREEN_HEIGHT = HEIGHT + INFO_HEIGHT

# Quy tắc combo
COMBO_RULES = {
    0: (2, 200),
    1: (3, 300),
    2: (4, 400),
    3: (5, 500),
    4: (6, 600)
}
BAG_SIZE = 7

pygame.mixer.init()

# --- KHỞI TẠO MÀN HÌNH ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Battle AI Players")
clock = pygame.time.Clock()

# Áp dụng tài nguyên âm thanh và vật thể
sound_assets = load_sounds()
assets = load_assets(TILE_SIZE)

AI_COLORS = {
    0: (255, 100, 100),  # Đỏ
    1: (100, 255, 100),  # Xanh lá
    2: (100, 100, 255)   # Xanh dương
}

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

def draw_player(x, y, ai_id):
    rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
    screen.blit(assets["floor"], rect)
    
    color = AI_COLORS[ai_id]
    pygame.draw.circle(
        screen, 
        color, 
        (x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2), 
        TILE_SIZE // 2 - 2
    )
    
    pygame.draw.circle(
        screen, 
        (0, 0, 0), 
        (x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2), 
        TILE_SIZE // 2 - 2, 
        2
    )
    
    font = pygame.font.SysFont(None, 20)
    text = font.render(str(ai_id + 1), True, (255, 255, 255))
    text_rect = text.get_rect(center=(x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2))
    screen.blit(text, text_rect)

def draw_path(path, ai_id):
    #Vẽ đường đi của AI
    if not path:
        return
        
    for _, pos in path:
        x, y = pos
        rect = pygame.Rect(x * TILE_SIZE + TILE_SIZE//4, y * TILE_SIZE + TILE_SIZE//4, TILE_SIZE//2, TILE_SIZE//2)
        color = list(AI_COLORS[ai_id])
        color.append(128)  # Thêm độ trong suốt
        pygame.draw.rect(screen, color, rect, border_radius=5)

def draw_info(bags, scores, ai_algos):
    info_rect = pygame.Rect(0, HEIGHT, SCREEN_WIDTH, INFO_HEIGHT)
    pygame.draw.rect(screen, (220,220,220), info_rect)
    
    font = pygame.font.SysFont(None, 23)
    
    # Vẽ thông tin cho từng AI
    for ai_id in range(3):
        # Tính toán vị trí y cho từng AI
        y_pos = HEIGHT + 10 + ai_id * 60
        
        # Vẽ khung cho AI
        ai_rect = pygame.Rect(5, y_pos, SCREEN_WIDTH - 10, 55)
        ai_color = (*AI_COLORS[ai_id], 100)  # Thêm độ trong suốt
        pygame.draw.rect(screen, ai_color, ai_rect, border_radius=5)
        pygame.draw.rect(screen, AI_COLORS[ai_id], ai_rect, 2, border_radius=5)
        
        # Vẽ tiêu đề AI
        ai_text = font.render(f"AI {ai_id + 1}: {ai_algos[ai_id] if ai_algos[ai_id] != 'No play' else 'Not playing'}", True, (0,0,0))
        screen.blit(ai_text, (10, y_pos + 5))
        
        # Vẽ điểm số
        score_text = font.render(f"Score: {scores[ai_id]}", True, (0,0,0))
        screen.blit(score_text, (180, y_pos + 5))
        
        # Vẽ thời gian suy nghĩ
        time_text = font.render(f"Total thinking time: {thinking_times[ai_id]:.6f} s", True, (0,0,0))
        screen.blit(time_text, (300, y_pos + 5))
        
        # Vẽ túi đồ
        bag_text = font.render("Bag:", True, (0,0,0))
        screen.blit(bag_text, (10, y_pos + 30))
        
        # Vẽ các ô trong túi đồ
        for idx in range(BAG_SIZE):
            slot_rect = pygame.Rect(80 + idx * (TILE_SIZE + 5), y_pos + 25, TILE_SIZE, TILE_SIZE)
            screen.blit(assets["floor"], slot_rect)
            pygame.draw.rect(screen, (0,0,0), slot_rect, 1)
            if idx < len(bags[ai_id]):
                value = bags[ai_id][idx]
                if value in assets["object"]:
                    screen.blit(assets["object"][value], slot_rect)
                else:
                    pygame.draw.rect(screen, (255,255,255), slot_rect)
    
    # Vẽ các điều khiển
    draw_controls()

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
        
    def set_path(self, path, cal_time=0.0):
        self.path_steps = []
        self.path_steps.append(f"Time: {cal_time:.6f} s")
        
        for i, (direction, pos) in enumerate(path):
            x, y = pos
            self.path_steps.append(f"Step {i+1}: {direction} -> ({x},{y})")
        
    def draw(self, surface):
        pygame.draw.rect(surface, (240, 240, 240), self.rect)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2)
        
        title = self.font.render("AI Path Steps", True, (0, 0, 0))
        title_rect = title.get_rect(center=(self.rect.centerx, self.rect.y + 15))
        surface.blit(title, title_rect)
        
        content_rect = pygame.Rect(
            self.rect.x + 5, 
            self.rect.y + 35, 
            self.rect.width - self.scrollbar_width - 10, 
            self.rect.height - 40
        )
        pygame.draw.rect(surface, (255, 255, 255), content_rect)
        pygame.draw.rect(surface, (200, 200, 200), content_rect, 1)
        
        content_surface = pygame.Surface((content_rect.width, content_rect.height))
        content_surface.fill((255, 255, 255))
        
        max_scroll = max(0, len(self.path_steps) * self.line_height - content_rect.height)
        self.scroll_y = min(self.scroll_y, max_scroll)
        
        for i, step in enumerate(self.path_steps):
            y_pos = i * self.line_height - self.scroll_y + 2
            if -self.line_height <= y_pos < content_rect.height:
                if i == 0:  # First line is the time
                    text = self.font.render(step, True, (0, 0, 150))
                else:
                    text = self.font.render(step, True, (0, 0, 0))
                content_surface.blit(text, (5, y_pos))
        
        surface.blit(content_surface, content_rect)
        
        if len(self.path_steps) * self.line_height > content_rect.height:
            scrollbar_rect = pygame.Rect(
                self.rect.right - self.scrollbar_width - 5,
                content_rect.y,
                self.scrollbar_width,
                content_rect.height
            )
            pygame.draw.rect(surface, (220, 220, 220), scrollbar_rect)
            
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
            elif event.button == 1:  # scrollbar dragging
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
        
    def draw(self, surface):
        # Vẽ ô được chọn (nút chính)
        selected_color = (220, 220, 240) 
        pygame.draw.rect(surface, selected_color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2, border_radius=5)  # Viền
        
        # Vẽ text của lựa chọn hiện tại
        text_surf = self.font.render(self.options[self.selected_index], True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
        # Vẽ mũi tên chỉ menu mở lên
        arrow_points = [
            (self.rect.right - 20, self.rect.centery + 3),
            (self.rect.right - 10, self.rect.centery + 3),
            (self.rect.right - 15, self.rect.centery - 3)
        ]
        pygame.draw.polygon(surface, (0, 0, 0), arrow_points)
        
        # Nếu menu đang mở, vẽ danh sách lựa chọn lên phía trên nút được chọn
        if self.is_opened:
            for i, option in enumerate(self.options):
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

# Tạo nút và dropdown cho điều khiển game
control_buttons = {
    "start": Button(10, HEIGHT + 190, 120, 40, "Start All", color=(144, 238, 144), hover_color=(100, 200, 100)),
    "stop": Button(140, HEIGHT + 190, 120, 40, "Stop All", color=(255, 200, 200), hover_color=(255, 150, 150)),
    "step": Button(270, HEIGHT + 190, 80, 40, "Step", color=(173, 216, 230), hover_color=(70, 130, 180)),
    "reset": Button(630, HEIGHT + 190, 120, 40, "RESET", color=(255, 215, 0), hover_color=(230, 190, 0))
}

speed_options = ["Slow", "Normal", "Fast", "Instant"]
game_speed_dropdown = DropdownMenu(370, HEIGHT + 190, 100, 40, speed_options)

# Dropdown cho thuật toán của từng AI
ai_algo_options = ["No play","Nearest", "BFS", "DFS", "A_Star", "Simulated_Annealing", "Nondeterministic", "BTwForwardChecking", "QLearning"]
# Thay đổi vị trí X cho mỗi dropdown
ai_algorithm_dropdowns = [
    DropdownMenu(550 + i * 100, HEIGHT + 18 + i * 60, 170, 40, ai_algo_options) for i in range(3)
]

def draw_controls():
    # Vẽ các nút điều khiển
    for name, button in control_buttons.items():
        button.draw(screen)
        
    # Vẽ label cho dropdown tốc độ game
    font = pygame.font.SysFont(None, 22)
    speed_text = font.render("Speed:", True, (0, 0, 0))
    screen.blit(speed_text, (370, HEIGHT + 170))
    
    # Vẽ dropdown tốc độ game
    game_speed_dropdown.draw(screen)
    
    # Vẽ bộ đếm bước đi
    steps_font = pygame.font.SysFont(None, 28)
    steps_text = steps_font.render(f"Steps: {total_steps}", True, (0, 0, 0))
    steps_rect = steps_text.get_rect(left=control_buttons["reset"].rect.right + 20, 
                                     centery=control_buttons["reset"].rect.centery)
    screen.blit(steps_text, steps_rect)
    
    # Dropdowns cho thuật toán của mỗi AI được vẽ trong phần draw_info

def check_combos(bag):
    global scores, animations
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
                
                # Xóa vật phẩm khỏi túi
                del bag[i:i+need]
                return True, points
    return False, 0

# --- KHỞI TẠO GAME ---
map_file = "map_design.txt"
map_tiles = load_map_from_file(map_file, GRID_SIZE)

path_panels = [
    ScrollablePathPanel(
        WIDTH + i * PANEL_WIDTH,  # mỗi panel dịch sang phải một PANEL_WIDTH
        0,                        # đều bắt đầu từ đỉnh
        PANEL_WIDTH,
        HEIGHT                    # chiều cao bằng hẳn map
    ) for i in range(3)
]


original_map_tiles = [row[:] for row in map_tiles]  # Tạo bản sao sâu của map ban đầu

# Khởi tạo các vị trí ban đầu cho AI
player_positions = [
    (GRID_SIZE // 4, GRID_SIZE // 4),             # AI 1 ở góc trên trái
    (GRID_SIZE // 4 * 3, GRID_SIZE // 4),         # AI 2 ở góc trên phải
    (GRID_SIZE // 2, GRID_SIZE // 4 * 3)          # AI 3 ở giữa dưới
]

animation_manager = AnimationManager(assets, TILE_SIZE, HEIGHT, sound_assets)

# Khởi tạo túi đồ và điểm số, thinking time cho từng AI
bags = [[] for _ in range(3)]
scores = [0, 0, 0]
thinking_times = [0.0, 0.0, 0.0]
current_calculation_times = [0.0, 0.0, 0.0]

# --- BIẾN CHO GAME ---
game_running = False
step_mode = False
do_step = False
ai_paths = [[] for _ in range(3)]
ai_active = [False, False, False]  # Mặc định không AI nào chơi
current_path_indices = [0, 0, 0]
game_speed_dict = {
    "Slow": 5,  # FPS
    "Normal": 10,
    "Fast": 20,
    "Instant": 60
}

# Biến đếm bước để thả vật phẩm mới
step_counter = 0
total_steps = 0  # Biến đếm tổng số bước đi

# hàm calculate_ai_path để cập nhật panel path tương ứng
def calculate_ai_path(ai_id):
    global ai_paths, current_path_indices, thinking_times, current_calculation_times
    
    # Lấy thuật toán đã chọn
    algorithm = ai_algorithm_dropdowns[ai_id].get_selected()
    
    # Nếu AI không chơi, không tính đường đi
    if algorithm == "No play":
        ai_paths[ai_id] = []
        current_path_indices[ai_id] = 0
        path_panels[ai_id].set_path([], 0.0)
        return []
    
    # Tạo bản sao của map để AI phân tích
    map_copy = [row[:] for row in map_tiles]
    
    # Lấy vị trí hiện tại của AI
    x, y = player_positions[ai_id]
    
    start_time = time.time()
    
    # Gọi hàm tìm đường dựa trên thuật toán được chọn
    if algorithm == "Nearest":
        path = search_only_nearest(map_copy, (x, y))
    elif algorithm == "BFS":
        path = bfs_search(map_copy, (x, y), bags[ai_id])
    elif algorithm == "DFS":
        path = dfs_search(map_copy, (x, y), bags[ai_id])
    elif algorithm == "A_Star":
        path = astar_search(map_copy, (x, y), bags[ai_id])
    elif algorithm == "Simulated_Annealing":
        path = simulated_annealing_search(map_copy, (x, y), bags[ai_id])
    elif algorithm == "Nondeterministic":
        path = nondeterministic_search(map_copy, (x, y), bags[ai_id])
    elif algorithm == "BTwForwardChecking":
        path = backtracking_with_forward_checking(map_copy, (x, y), bags[ai_id])
    elif algorithm == "QLearning":
        path = qlearning_search(map_copy, (x, y), bags[ai_id])
    
    end_time = time.time()
    calculation_time = end_time - start_time
    
    # Lưu thời gian tính toán hiện tại và thêm vào tổng
    current_calculation_times[ai_id] = calculation_time
    thinking_times[ai_id] += calculation_time
    
    ai_paths[ai_id] = path
    current_path_indices[ai_id] = 0
    
    # Cập nhật path panel tương ứng cho AI
    path_panels[ai_id].set_path(path, current_calculation_times[ai_id])
        
    return path
            

# --- VÒNG LẶP GAME CHÍNH ---
running = True
fps_timer = pygame.time.Clock()

# Đặt vài vật phẩm ban đầu
place_random_objects(map_tiles, GRID_SIZE, player_positions)

while running:
    # Điều chỉnh tốc độ dựa trên lựa chọn từ dropdown
    game_speed = game_speed_dict[game_speed_dropdown.get_selected()]
    fps_timer.tick(game_speed)
    
    # Xử lý các sự kiện
    mouse_click = False
    for event in pygame.event.get():
        # Xử lý sự kiện cho mỗi path panel
        for panel in path_panels:
            panel.handle_event(event)

        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_click = True
            
        # Xử lý các dropdown
        game_speed_dropdown.handle_event(event)
        for dropdown in ai_algorithm_dropdowns:
            dropdown.handle_event(event)
            
        # Xử lý các nút điều khiển game
        mouse_pos = pygame.mouse.get_pos()
        
        for name, button in control_buttons.items():
            button.check_hover(mouse_pos)
            if mouse_click and button.is_clicked(mouse_pos, True):
                if name == "start":
                    game_running = True
                    step_mode = False
                    # Kiểm tra và kích hoạt các AI
                    for i in range(3):
                        algo = ai_algorithm_dropdowns[i].get_selected()
                        if algo != "No play":
                            ai_active[i] = True
                            if not ai_paths[i] or current_path_indices[i] >= len(ai_paths[i]):
                                calculate_ai_path(i)
                        else:
                            ai_active[i] = False
                            
                elif name == "stop":
                    game_running = False
                    step_mode = False
                    
                elif name == "step":
                    step_mode = True
                    game_running = False
                    do_step = True
                    # Kiểm tra và kích hoạt các AI
                    for i in range(3):
                        algo = ai_algorithm_dropdowns[i].get_selected()
                        if algo != "No play":
                            ai_active[i] = True
                            if not ai_paths[i] or current_path_indices[i] >= len(ai_paths[i]):
                                calculate_ai_path(i)
                        else:
                            ai_active[i] = False
                    
                elif name == "reset":
                    # Reset game
                    game_running = False
                    step_mode = False
                    ai_paths = [[] for _ in range(3)]
                    ai_active = [False, False, False]
                    current_path_indices = [0, 0, 0]
                    for i, panel in enumerate(path_panels):
                        panel.set_path([], 0.0)
                    
                    # Reset vị trí AI về vị trí ban đầu
                    player_positions = [
                        (GRID_SIZE // 4, GRID_SIZE // 4),
                        (GRID_SIZE // 4 * 3, GRID_SIZE // 4),
                        (GRID_SIZE // 2, GRID_SIZE // 4 * 3)
                    ]
                    
                    # Reset túi đồ và điểm số
                    bags = [[] for _ in range(3)]
                    scores = [0, 0, 0]
                    thinking_times = [0.0, 0.0, 0.0]
                    current_calculation_times = [0.0, 0.0, 0.0]
                    total_steps = 0
                    
                    # Khôi phục map về trạng thái ban đầu
                    map_tiles = [row[:] for row in original_map_tiles]
                    
                    # Đặt vật phẩm 
                    place_random_objects(map_tiles, GRID_SIZE, player_positions)
                    
                    animation_manager.clear()
                    
                

    # Cập nhật vị trí AI dựa trên đường đi đã tính
    if game_running or do_step:
        # Tăng bộ đếm bước để thả vật phẩm mới với điều kiện số AI và số vật trên map
        step_counter += 1

        # Đếm số AI đang hoạt động
        active_count = sum(1 for a in ai_active if a)
        if active_count > 0:
            # Xác định khoảng interval theo số AI
            if active_count == 1:
                drop_interval = 150
            elif active_count == 2:
                drop_interval = 100
            else:  # 3 AI
                drop_interval = 50

            # Đếm số vật hiện có trên map
            item_count = sum(
                1 
                for row in map_tiles 
                for cell in row 
                if isinstance(cell, int)
            )

            # Nếu đã đủ bước và map chưa có đủ 20 vật hoặc còn dưới 5 vật phẩm thì thả thêm
            if (step_counter >= drop_interval and item_count < 20) or item_count <= 5:
                place_random_objects(map_tiles, GRID_SIZE, player_positions)
                
                # Thêm text animation khi thả vật phẩm
                animation_manager.add_text_animation(
                    "Dropped new objects!",
                    control_buttons["reset"].rect.right + 180,  # Vị trí X (bên phải nút Reset)
                    HEIGHT + 190,  # Vị trí Y (cùng hàng với nút)
                    color=(0, 0, 0),  # Màu
                    duration=4000,      # Thời gian tồn tại
                    speed=1.5,          # Tốc độ di chuyển
                    font_size=29        # Kích thước font
                )
                # -- KHI THẢ RANDOM XONG, PHẢI TÍNH LẠI ĐƯỜNG CHO CÁC AI ĐANG ACTIVE --
                for ai_id in range(3):
                    if ai_active[ai_id]:
                        calculate_ai_path(ai_id)
                step_counter = 0
            
            
        
        # Thu thập các di chuyển dự định của tất cả AI trong bước này
        intended_moves = []
        for ai_id in range(3):
            if ai_active[ai_id] and ai_paths[ai_id]:
                if current_path_indices[ai_id] < len(ai_paths[ai_id]):
                    direction, (new_x, new_y) = ai_paths[ai_id][current_path_indices[ai_id]]
                    # Kiểm tra mục tiêu còn tồn tại không
                    if len(ai_paths[ai_id]) > current_path_indices[ai_id] + 1:
                        _, (target_x, target_y) = ai_paths[ai_id][-1]
                        # Chỉ kiểm tra nếu thuật toán không phải Simulated Annealing hoặc Q-learning
                        algorithm = ai_algorithm_dropdowns[ai_id].get_selected()
                        if algorithm not in ["Simulated_Annealing", "QLearning"]:
                            # Kiểm tra nếu vị trí cuối cùng dự kiến chứa vật phẩm thì nó đã bị lấy chưa
                            if (isinstance(map_tiles[target_y][target_x], int) == False and map_tiles[target_y][target_x] == " "):
                                # Vật phẩm đã bị nhặt, cần tính toán lại đường đi
                                # Vật phẩm đã bị nhặt, thêm animation "Object Stolen!" dưới path panel của AI này
                                animation_manager.add_text_animation(
                                    "Object Got Stolen!",
                                    path_panels[ai_id].rect.x + 18,         # căn lề trái trong panel
                                    path_panels[ai_id].rect.height - 20,    # cách đáy panel Y px
                                    color=(255, 0, 0),                      # màu đỏ nổi bật
                                    duration=3000,                          # hiển thị 3 giây
                                    speed=1.5,                              # tốc độ di chuyển nhẹ
                                    font_size=24                            # kích thước chữ
                                )
                                calculate_ai_path(ai_id)
                                continue
                    # Lưu lại ý định di chuyển
                    intended_moves.append((ai_id, new_x, new_y))
        
        # Tạo từ điển để theo dõi các xung đột
        conflict_positions = {}
        
        # Xác định các xung đột
        for ai_id, new_x, new_y in intended_moves:
            position = (new_x, new_y)
            if position not in conflict_positions:
                conflict_positions[position] = []
            conflict_positions[position].append(ai_id)
        
        # Xử lý từng di chuyển của mỗi AI TRONG PHẦN MẢNG CONFLICT POSITION
        for position, ai_ids in conflict_positions.items():
            new_x, new_y = position
            
            # Xử lý vật phẩm (nếu có)
            if isinstance(map_tiles[new_y][new_x], int):
                obj = map_tiles[new_y][new_x]
                
                # Tạo số ngẫu nhiên dựa trên số lượng AI đang xung đột (cùng nhặt 1 vp) 
                # ai_id ở đây là theo trình tự AI được thêm vào ví dụ xung đột giữa AI 1 và 3 thì là ai_ids = [0,2]
                # num_competing_ais = len(ai_ids)
                # if num_competing_ais > 1:
                #     # Random từ 0 đến (số lượng AI) để đảm bảo phân phối đều rồi lấy int 
                #     # Vì random uni (x,y) sẽ lấy từ [x; y) 
                #     random_index = int(random.uniform(0, num_competing_ais))
                #     chosen_ai_id = ai_ids[random_index]
                #     print(f"Xung đột tại {new_x},{new_y}: AI {ai_ids} -> rand {random_index} -> Chọn AI {chosen_ai_id}")
                # else:
                #     chosen_ai_id = ai_ids[0]  # Chỉ có 1 AI
                
                # Xử lý trường hợp xung đột (nhiều AI cùng muốn nhặt một vật phẩm)
                num_competing_ais = len(ai_ids)
                if num_competing_ais > 1:
                    # Tìm AI có thời gian suy nghĩ ngắn nhất cho lần tính toán hiện tại
                    min_calculation_time = float('inf')
                    chosen_ai_id = ai_ids[0]  # Mặc định chọn AI đầu tiên
                    # Random cộng thêm 1 phần rất nhỏ thời gian tránh trường hợp 2,3 cái đều cùng 0.000000s hoặc cùng thời gian
                    for ai_id in ai_ids:
                        temp = current_calculation_times[ai_id] + (random.uniform(0, 99)/1000000000)
                        if  temp < min_calculation_time:
                            min_calculation_time = temp
                            chosen_ai_id = ai_id          
                    print(f"Xung đột tại {new_x},{new_y}: AI {ai_ids} -> AI {chosen_ai_id} được chọn (thời gian nghĩ: {min_calculation_time:.10f}s)")
                else:
                    chosen_ai_id = ai_ids[0]  # Chỉ có 1 AI
                
                
                # Chỉ AI được chọn mới nhận vật phẩm
                bags[chosen_ai_id].append(obj)
                # Nếu vượt quá sức chứa thì pop đầu
                if len(bags[chosen_ai_id]) > BAG_SIZE:
                    bags[chosen_ai_id].pop(0)
                
                # Animation và xóa vật phẩm khỏi map
                animation_manager.add_collect_animation(new_x, new_y, obj)
                sound_assets["collect"].play()
                map_tiles[new_y][new_x] = " "
                
                # Kiểm tra combo
                has_combo, combo_points = check_combos(bags[chosen_ai_id])
                if has_combo:
                    scores[chosen_ai_id] += combo_points
            
            # Cập nhật vị trí cho tất cả AI tham gia vào ô này
            for ai_id in ai_ids:
                player_positions[ai_id] = (new_x, new_y)
                current_path_indices[ai_id] += 1
                
                # Nếu đã đi hết đường đi, tính đường đi mới
                if current_path_indices[ai_id] >= len(ai_paths[ai_id]):
                    calculate_ai_path(ai_id)
        
        # Tăng số bước đi
        total_steps += 1

        # Reset trạng thái bước
        do_step = False
    
    # --- VẼ MÀN HÌNH ---
    screen.fill((255, 255, 255))
    
    # Vẽ map
    draw_map(map_tiles)
    draw_grid()
    
    # Vẽ đường đi của AI đang chơi
    for ai_id in range(3):
        if ai_active[ai_id] and ai_paths[ai_id]:
            remaining_path = ai_paths[ai_id][current_path_indices[ai_id]:]
            draw_path(remaining_path, ai_id)
    
    # Vẽ các AI
    for ai_id in range(3):
        x, y = player_positions[ai_id]
        draw_player(x, y, ai_id)
    
    # Vẽ panel thông tin
    draw_info(bags, scores, [dropdown.get_selected() for dropdown in ai_algorithm_dropdowns])
    
    # Vẽ các path panel
    for i, panel in enumerate(path_panels):
        panel.draw(screen)
    
    # Vẽ dropdowns cho thuật toán AI
    for i, dropdown in enumerate(ai_algorithm_dropdowns):
        dropdown.draw(screen)
    
    game_speed_dropdown.draw(screen)
    
    # Vẽ và cập nhật animations
    animation_manager.update_and_draw(screen)
    
    # Cập nhật màn hình
    pygame.display.flip()

pygame.quit()
sys.exit()