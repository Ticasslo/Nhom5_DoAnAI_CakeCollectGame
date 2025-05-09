import pygame
import random
import sys
import os
from collections import deque
import time

from searchBFS import bfs_search
from searchDFS import dfs_search
from animations import AnimationManager
from assets import load_assets, load_sounds
from map_handler import load_map_from_file, place_random_objects

# Khởi tạo pygame
pygame.init()

# --- CÀI ĐẶT MAP ---
GRID_SIZE = 25             # Map thiết kế (25x25)
TILE_SIZE = 25
WIDTH, HEIGHT = TILE_SIZE * GRID_SIZE, TILE_SIZE * GRID_SIZE
INFO_HEIGHT = 140

PANEL_WIDTH = 200
PATH_PANEL_WIDTH = 500
SCREEN_WIDTH = WIDTH + PANEL_WIDTH + PATH_PANEL_WIDTH
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
    
    # Hiển thị Score
    font = pygame.font.SysFont(None, 28)
    score_text = font.render(f"Score: {score}", True, (0,0,0))
    screen.blit(score_text, (10, HEIGHT + 10))
    
    # Hiển thị Total thinking time (với 5 chữ số thập phân)
    thinking_text = font.render(f"Total thinking time: {total_thinking_time:.6f} s", True, (0,0,0))
    screen.blit(thinking_text, (220, HEIGHT + 10))
    
    # Hiển thị Total steps
    steps_text = font.render(f"Total steps: {total_steps}", True, (0,0,0))
    screen.blit(steps_text, (550, HEIGHT + 10))
    
    
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
    
    # Vẽ thông tin combo ở phía bên phải info
    small_font = pygame.font.SysFont(None, 21)  # Font nhỏ hơn cho thông tin combo
    combo_title = small_font.render("Combos:", True, (0,0,0))
    combo_title_x = SCREEN_WIDTH - PATH_PANEL_WIDTH + 200  # Vị trí bắt đầu phần combo
    screen.blit(combo_title, (combo_title_x, HEIGHT + 1)) 
    SMALL_TILE_SIZE = 15
    for i, (need, points) in enumerate(COMBO_RULES.values()):
        # Tính vị trí y cho mỗi dòng combo
        text_y = HEIGHT + 15 + i * (SMALL_TILE_SIZE + 10)    
        # Vẽ hình ảnh vật phẩm
        for j in range(need):
            img_rect = pygame.Rect(
                combo_title_x + j * (SMALL_TILE_SIZE + 5), 
                text_y, 
                SMALL_TILE_SIZE, SMALL_TILE_SIZE
            )        
            if i in assets["object"]:
                screen.blit(assets["object"][i], img_rect)
        
        # Vẽ mũi tên và điểm
        arrow_x = combo_title_x + need * (TILE_SIZE + 5) + 10
        arrow_text = small_font.render("==", True, (0, 0, 0))
        screen.blit(arrow_text, (arrow_x, text_y + 5))    
        points_text = small_font.render(f"+{points} pts", True, (255, 0, 0))
        screen.blit(points_text, (arrow_x + 30, text_y + 5))
        
    # Vẽ các điều khiển AI
    draw_ai_controls()

class ScrollablePathPanel:
    def __init__(self, x, y, width, height, font_size=18):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.SysFont(None, font_size)
        self.path_steps = []
        self.calculation_time = 0.0
        self.scroll_y = 0
        self.line_height = font_size + 4
        self.visible_lines = height // self.line_height
        self.scrollbar_width = 15
        self.dragging = False
        
    def set_path(self, path, calc_time=0.0):
        self.path_steps = []
        self.calculation_time = calc_time
        self.path_steps.append(f"Time: {self.calculation_time:.6f} s")
        
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
            y_pos = i * self.line_height - self.scroll_y + 2
            if -self.line_height <= y_pos < content_rect.height:
                if i == 0 and self.calculation_time > 0:
                    text = self.font.render(step, True, (0, 0, 150))  # Blue for time
                else:
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
  
class PathVisualizationPanel:
    """
    A panel to visualize the AI path as a map overlay.
    Each node shows its position on a minimap version of the actual game map.
    Uses the exact grid size and displays the legend vertically below the map.
    """
    def __init__(self, x, y, width, height, font_size=16):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.SysFont(None, font_size)
        self.path = []
        self.current_index = 0
        self.node_radius = 10  # Slightly smaller radius to fit grid
        self.font_node = pygame.font.SysFont(None, 15)  # Font nhỏ hơn cho chữ trong node

        # Space for legend at the bottom
        self.legend_height = 100
        
        # Calculate margins to center the minimap
        self.map_margin_x = 10  # Left margin for minimap
        self.map_margin_y = 40  # Top margin for minimap
        
        # Available space for minimap (accounting for title, margins, and legend)
        self.minimap_width = width - 2 * self.map_margin_x
        self.minimap_height = height - self.map_margin_y - self.legend_height
        
        # Calculate cell size to maintain proper grid ratio
        self.cell_size = min(self.minimap_width / GRID_SIZE, self.minimap_height / GRID_SIZE)
        
        # Recalculate actual minimap dimensions
        self.minimap_width = self.cell_size * GRID_SIZE
        self.minimap_height = self.cell_size * GRID_SIZE
        
    def set_path(self, path):
        """Set a new path. `path` is a list of (direction, (x, y)) tuples."""
        self.path = path
        self.current_index = 0
        
    def update(self, current_index):
        """Update the panel with the current path index."""
        self.current_index = current_index

    def draw(self, surface):
        # Draw panel background and border
        pygame.draw.rect(surface, (240, 240, 240), self.rect)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2)

        # Draw title
        title = self.font.render("Path Visualization (Map View)", True, (0, 0, 0))
        surface.blit(title, (self.rect.x + 10, self.rect.y + 10))

        # Calculate minimap area with centering
        # Center horizontally
        minimap_x = self.rect.x + (self.rect.width - self.minimap_width) // 2
        minimap_y = self.rect.y + self.map_margin_y
        minimap_rect = pygame.Rect(minimap_x, minimap_y, self.minimap_width, self.minimap_height)
        
        # Draw minimap background
        pygame.draw.rect(surface, (220, 220, 220), minimap_rect)
        pygame.draw.rect(surface, (0, 0, 0), minimap_rect, 1)
        
        # Draw grid lines
        for i in range(GRID_SIZE + 1):
            # Vertical lines
            line_x = minimap_x + i * self.cell_size
            pygame.draw.line(surface, (200, 200, 200), 
                            (line_x, minimap_y), 
                            (line_x, minimap_y + self.minimap_height))
            
            # Horizontal lines
            line_y = minimap_y + i * self.cell_size
            pygame.draw.line(surface, (200, 200, 200), 
                            (minimap_x, line_y), 
                            (minimap_x + self.minimap_width, line_y))
        
        # Draw obstacle markers (X) on walls
        for y_map in range(GRID_SIZE):
            for x_map in range(GRID_SIZE):
                # Check if this cell is a wall/obstacle
                if (0 <= y_map < len(map_tiles) and 0 <= x_map < len(map_tiles[0]) and 
                    map_tiles[y_map][x_map] in ["T", "W", "X", "B", "H", "G"]):
                    # Convert map coordinates to minimap coordinates
                    node_x = minimap_x + x_map * self.cell_size + self.cell_size/2
                    node_y = minimap_y + y_map * self.cell_size + self.cell_size/2
                    
                    # Draw an X
                    x_size = self.cell_size * 0.1  # Size of X relative to cell
                    pygame.draw.line(surface, (0, 0, 0), 
                                (node_x - x_size, node_y - x_size), 
                                (node_x + x_size, node_y + x_size), 2)
                    pygame.draw.line(surface, (0, 0, 0), 
                                (node_x + x_size, node_y - x_size), 
                                (node_x - x_size, node_y + x_size), 2)
            
        # Draw path nodes
        if self.path:
            # First, draw lines connecting path nodes
            for i in range(1, len(self.path)):
                prev_pos = self.path[i-1][1]
                curr_pos = self.path[i][1]
                
                # Convert map positions to minimap coordinates
                prev_x = minimap_x + prev_pos[0] * self.cell_size + self.cell_size/2
                prev_y = minimap_y + prev_pos[1] * self.cell_size + self.cell_size/2
                curr_x = minimap_x + curr_pos[0] * self.cell_size + self.cell_size/2
                curr_y = minimap_y + curr_pos[1] * self.cell_size + self.cell_size/2
                
                # Determine line color based on current position
                if i <= self.current_index:
                    line_color = (100, 200, 100)  # Green for visited path
                else:
                    line_color = (200, 200, 200)  # Gray for future path
                    
                pygame.draw.line(surface, line_color, (prev_x, prev_y), (curr_x, curr_y), 2)
            
            # Then, draw the nodes themselves
            for i, (direction, pos) in enumerate(self.path):
                # Convert map position to minimap coordinates
                node_x = minimap_x + pos[0] * self.cell_size + self.cell_size/2
                node_y = minimap_y + pos[1] * self.cell_size + self.cell_size/2
                
                if current_path_index == 0 and i == 0 and not ai_running and not do_step:
                    # Nếu là nút đầu tiên và chưa bắt đầu di chuyển, vẫn để là màu tương lai
                    color = (200, 200, 200)  # Gray for future positions
                elif i == self.current_index:
                    color = (255, 100, 100)  # Red for current position
                elif i < self.current_index:
                    color = (100, 200, 100)  # Green for visited positions
                else:
                    color = (200, 200, 200)  # Gray for future positions
                    
                # Check if the node represents a combo item
                x, y_map = pos
                if 0 <= y_map < len(map_tiles) and 0 <= x < len(map_tiles[0]):
                    tile = map_tiles[y_map][x]
                    if isinstance(tile, int) and tile in COMBO_RULES:
                        # If it's a combo item, use gold color
                        color = (255, 215, 0)
                
                # Draw node
                pygame.draw.circle(surface, color, (node_x, node_y), self.node_radius)
                pygame.draw.circle(surface, (0, 0, 0), (node_x, node_y), self.node_radius, 1)
                
                # Draw step number inside the node
                step_text = str(i + 1)
                step_surf = self.font_node.render(step_text, True, (0, 0, 0))
                step_rect = step_surf.get_rect(center=(node_x, node_y))
                surface.blit(step_surf, step_rect)
        
        # Draw legend horizontally below the minimap - ALWAYS DRAW THIS PART REGARDLESS OF PATH
        # This is moved outside the "if self.path:" condition so it always appears
        legend_y = minimap_y + self.minimap_height + 15
        
        # Calculate spacing between legend items (divide available space by 4 items)
        legend_spacing = self.rect.width // 4
        
        # Create a legend title
        legend_title = self.font.render("Annotation:", True, (0, 0, 0))
        surface.blit(legend_title, (self.rect.x + 10, legend_y))
        
        # Current position legend (first item)
        legend_x1 = self.rect.x + 10
        pygame.draw.circle(surface, (255, 100, 100), 
                        (legend_x1 + 10, legend_y + 25), self.node_radius)
        surface.blit(self.font.render("Current", True, (0, 0, 0)), 
                    (legend_x1 + 25, legend_y + 25 - 8))
        
        # Visited positions legend (second item)
        legend_x2 = self.rect.x + legend_spacing
        pygame.draw.circle(surface, (100, 200, 100), 
                        (legend_x2 + 10, legend_y + 25), self.node_radius)
        surface.blit(self.font.render("Visited", True, (0, 0, 0)), 
                    (legend_x2 + 25, legend_y + 25 - 8))
        
        # Future positions legend (third item)
        legend_x3 = self.rect.x + 2 * legend_spacing
        pygame.draw.circle(surface, (200, 200, 200), 
                        (legend_x3 + 10, legend_y + 25), self.node_radius)
        surface.blit(self.font.render("Future", True, (0, 0, 0)), 
                    (legend_x3 + 25, legend_y + 25 - 8))
        
        # Combo items legend (fourth item)
        legend_x4 = self.rect.x + 3 * legend_spacing
        pygame.draw.circle(surface, (255, 215, 0), 
                        (legend_x4 + 10, legend_y + 25), self.node_radius)
        surface.blit(self.font.render("Combo", True, (0, 0, 0)), 
                    (legend_x4 + 25, legend_y + 25 - 8))

            
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
map_file = "map_design.txt"
map_tiles = load_map_from_file(map_file, GRID_SIZE)

path_panel = ScrollablePathPanel(WIDTH, 0, PANEL_WIDTH, HEIGHT)
viz_panel = PathVisualizationPanel(WIDTH + PANEL_WIDTH, 0, PATH_PANEL_WIDTH, HEIGHT)
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

total_thinking_time = 0.0
total_steps = 0

# Hàm tính toán đường đi cho AI
def calculate_ai_path():
    global ai_path, current_path_index, total_thinking_time
    
    # Lấy thuật toán đã chọn
    algorithm = ai_algo_dropdown.get_selected()
    
    # Đo thời gian tính toán
    start_time = time.time()
    
    # Tạo bản sao của map để AI phân tích
    map_copy = [row[:] for row in map_tiles]
    
    # Gọi hàm tìm đường dựa trên thuật toán được chọn
    if algorithm == "BFS":
        path = bfs_search(map_copy, (player_x, player_y), bag)
    elif algorithm == "DFS":
        # Giả sử bạn đã có một hàm dfs tìm đường
        path = dfs_search(map_copy, (player_x, player_y), bag)
    elif algorithm == "Greedy":
        # Giả sử bạn đã có một hàm greedy tìm đường
        path = greedy_search(map_copy, (player_x, player_y))
    elif algorithm == "A*":
        # Giả sử bạn đã có một hàm A* tìm đường
        path = astar_search(map_copy, (player_x, player_y))
    
    # Tính thời gian và cộng vào tổng
    end_time = time.time()
    thinking_time = end_time - start_time
    total_thinking_time += thinking_time
    
    ai_path = path
    current_path_index = 0
    path_panel.set_path(path, thinking_time)
    viz_panel.set_path(path)

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
                    elif current_path_index >= len(ai_path):
                        # Kiểm tra xem còn vật phẩm nào trên bản đồ không
                        has_objects = False
                        for row in map_tiles:
                            for cell in row:
                                if isinstance(cell, int):
                                    has_objects = True
                                    break
                            if has_objects:
                                break
                                
                        if has_objects:
                            # Tính lại đường đi nếu còn vật phẩm
                            calculate_ai_path()
                elif name == "reset":
                    # Logic reset game
                    ai_running = False
                    step_mode = False
                    ai_path = []
                    current_path_index = 0
                    path_panel.set_path([], 0.0)  # Xóa đường đi trong panel
                    viz_panel.set_path([])  # Also clear the path visualization panel

                    # Reset vị trí người chơi về giữa bản đồ
                    player_x, player_y = GRID_SIZE // 2, GRID_SIZE // 2
                    
                    # reset túi đồ và điểm số
                    bag = []
                    score = 0
                    
                    # Reset các bộ đếm
                    total_thinking_time = 0.0
                    total_steps = 0
    
                    # Khôi phục map về trạng thái ban đầu (KHÔNG tạo map mới)
                    map_tiles = [row[:] for row in original_map_tiles]
    
    # Xử lý di chuyển AI
    if (ai_running or (step_mode and do_step)) and ai_path and current_path_index < len(ai_path):
        direction, pos = ai_path[current_path_index]
        new_x, new_y = pos
        
        # Di chuyển người chơi
        player_x, player_y = new_x, new_y
        
        # Tăng bộ đếm số bước
        total_steps += 1
        
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
        viz_panel.update(current_path_index - 1)

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
                    
            if has_objects and (ai_running or step_mode):
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
    viz_panel.draw(screen)

    draw_ai_controls()

    # Vẽ các animation
    animation_manager.update_and_draw(screen)
    
    pygame.display.flip()

pygame.quit()