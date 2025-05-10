import pygame
import random
import sys
import os

from animations import AnimationManager
from map_handler import load_map_from_file, place_random_objects
from assets import load_assets, load_sounds

pygame.init()

# --- CÀI ĐẶT MAP ---
GRID_SIZE = 25             # Map thiết kế (25x25)
TILE_SIZE = 26
WIDTH, HEIGHT = TILE_SIZE * GRID_SIZE, TILE_SIZE * GRID_SIZE
INFO_HEIGHT = 120
SCREEN_WIDTH = WIDTH
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
pygame.display.set_caption("Game")
clock = pygame.time.Clock()

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
    
     # Vẽ nút hướng dẫn
    help_button.draw(screen)

# biến để quản lý trạng thái của hướng dẫn
show_help = False

# Tạo lớp Button để xử lý nút
class Button:
    def __init__(self, x, y, width, height, text, font_size=24):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont(None, font_size)
        self.hover = False
        
    def draw(self, surface):
        # Vẽ nền nút
        if self.hover:
            color = (180, 180, 220)  # Màu khi hover
        else:
            color = (200, 200, 200)  # Màu bình thường
            
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

# hiển thị hướng dẫn
class HelpScreen:
    def __init__(self, screen_width, screen_height):
        self.width = int(screen_width * 0.8)
        self.height = int(screen_height * 0.8)
        self.x = (screen_width - self.width) // 2
        self.y = (screen_height - self.height) // 2
        
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.font_title = pygame.font.SysFont(None, 36)
        self.font_text = pygame.font.SysFont(None, 24)
        self.close_button = Button(
            self.x + self.width - 100, 
            self.y + self.height - 50,
            80, 40, "Đóng", 28
        )
        
    def draw(self, surface):
        # Vẽ nền
        pygame.draw.rect(surface, (240, 240, 240), self.rect, border_radius=10)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2, border_radius=10)
        
        # Tiêu đề
        title = self.font_title.render("Tutorial", True, (0, 0, 0))
        title_rect = title.get_rect(center=(self.x + self.width // 2, self.y + 30))
        surface.blit(title, title_rect)
        
        # Nội dung - Luật chơi
        text_y = self.y + 80
        texts = [
            "Move character with W, A, S, D.",
            "Collect object into your bag (Maximum is 7)",
            "When have the same object in the RIGHT ORDER, it a combo:"
        ]
        
        for line in texts:
            text_surf = self.font_text.render(line, True, (0, 0, 0))
            surface.blit(text_surf, (self.x + 30, text_y))
            text_y += 30
            
        # Hiển thị thông tin các combo
        combo_text_x = self.x + 50
        
        for i, (need, points) in enumerate(COMBO_RULES.values()):
            # Vẽ hình ảnh vật phẩm
            for j in range(need):
                img_rect = pygame.Rect(
                    combo_text_x + j * (TILE_SIZE + 5), 
                    text_y + 5, 
                    TILE_SIZE, TILE_SIZE
                )
                surface.blit(assets["object"][i], img_rect)
            
            # Vẽ mũi tên và điểm
            arrow_x = combo_text_x + need * (TILE_SIZE + 5) + 10
            arrow_text = self.font_text.render("==", True, (0, 0, 0))
            surface.blit(arrow_text, (arrow_x, text_y + 5))
            
            points_text = self.font_text.render(f"+{points} point", True, (255, 0, 0))
            surface.blit(points_text, (arrow_x + 30, text_y + 5))
            
            text_y += TILE_SIZE + 15
            
        # Vẽ ví dụ về combo
        text_y += 20
        example_text = self.font_text.render("Combo Example:", True, (0, 0, 0))
        surface.blit(example_text, (self.x + 30, text_y))
        text_y += 30
        
        # Vẽ ví dụ mô phỏng túi đồ với combo
        example_bag = [2, 0, 0, 1, 1 ,1]
        bag_text = self.font_text.render("Bag before combo:", True, (0, 0, 0))
        surface.blit(bag_text, (self.x + 30, text_y))
        
        for i, obj in enumerate(example_bag):
            img_rect = pygame.Rect(
                self.x + 180 + i * (TILE_SIZE + 5),
                text_y - 5,
                TILE_SIZE, TILE_SIZE
            )
            surface.blit(assets["object"][obj], img_rect)
        
        text_y += 40
        result_text = self.font_text.render("Result: Combo of three brown cake == +300 point", True, (0, 0, 0))
        surface.blit(result_text, (self.x + 30, text_y))
        
        text_y += 25
        after_text = self.font_text.render("Bag after combo:", True, (2, 0, 0))
        surface.blit(after_text, (self.x + 30, text_y))
        
        for i, obj in enumerate(example_bag[:3]):
            img_rect = pygame.Rect(
                self.x + 180 + i * (TILE_SIZE + 5),
                text_y - 5,
                TILE_SIZE, TILE_SIZE
            )
            surface.blit(assets["object"][obj], img_rect)
        
        # Vẽ nút đóng
        self.close_button.draw(surface)
        
    def check_events(self, event):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        
        self.close_button.check_hover(mouse_pos)
        if self.close_button.is_clicked(mouse_pos, mouse_click):
            return False  # Đóng hướng dẫn
            
        return True  # Giữ hướng dẫn mở

help_button = Button(SCREEN_WIDTH - 50, HEIGHT + INFO_HEIGHT - 50, 40, 40, "?", 36)
help_screen = HelpScreen(SCREEN_WIDTH, SCREEN_HEIGHT)       
        
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
place_random_objects(map_tiles, GRID_SIZE)

player_x, player_y = GRID_SIZE // 2, GRID_SIZE // 2
animation_manager = AnimationManager(assets, TILE_SIZE, HEIGHT, sound_assets)
bag = []
score = 0

# --- VÒNG LẶP GAME CHÍNH ---
running = True
while running:
    clock.tick(10)
    
    # Xử lý các sự kiện
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Xử lý di chuyển khi không hiển thị màn hình hướng dẫn
        if not show_help and event.type == pygame.KEYDOWN:
            dx, dy = 0, 0
            if event.key == pygame.K_w:
                dy = -1
            elif event.key == pygame.K_s:
                dy = 1
            elif event.key == pygame.K_a:
                dx = -1
            elif event.key == pygame.K_d:
                dx = 1
            new_x = player_x + dx
            new_y = player_y + dy
            if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE and map_tiles[new_y][new_x] not in ["T","W","X","B","H", "G"]:
                player_x, player_y = new_x, new_y
                cell = map_tiles[player_y][player_x]
                
                if isinstance(cell, int):
                    animation_manager.add_collect_animation(player_x, player_y, cell)
                    
                    # Phát âm thanh khi nhặt vật phẩm
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
                    map_tiles[player_y][player_x] = " "
                    while check_combos(bag):
                        pass
        
        # Xử lý click chuột cho nút hướng dẫn
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            if not show_help:
                # Kiểm tra nút hướng dẫn
                if help_button.is_clicked(mouse_pos, True):
                    show_help = True
            else:
                # Nếu đang hiển thị hướng dẫn, kiểm tra nút đóng
                show_help = help_screen.check_events(event)
        
        # Cập nhật trạng thái hover của các nút
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            help_button.check_hover(mouse_pos)
            if show_help:
                help_screen.close_button.check_hover(mouse_pos)
                
    # Vẽ màn hình game
    screen.fill((255,255,255))
    draw_map(map_tiles)
    draw_grid()
    draw_player(player_x, player_y)
    draw_info(bag, score)
    
    # Vẽ các animation
    animation_manager.update_and_draw(screen)
    
    # Hiển thị màn hình hướng dẫn nếu được yêu cầu
    if show_help:
        help_screen.draw(screen)
            
    pygame.display.flip()

pygame.quit()
