#animations.py
import pygame
from collections import deque

class CollectAnimation:
    def __init__(self, x, y, obj_type, assets, tile_size, duration=300):
        self.x = x
        self.y = y
        self.obj_type = obj_type
        self.assets = assets
        self.tile_size = tile_size
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        self.finished = False

    def draw(self, surface):
        now = pygame.time.get_ticks()
        elapsed = now - self.start_time
        if elapsed >= self.duration:
            self.finished = True
            return

        scale_factor = 1.0 + 0.5 * (1 - abs((elapsed / self.duration) * 2 - 1))  # Scale in/out

        size = int(self.tile_size * scale_factor)
        img = pygame.transform.scale(self.assets["object"][self.obj_type], (size, size))
        rect = img.get_rect(center=(self.x * self.tile_size + self.tile_size // 2, self.y * self.tile_size + self.tile_size // 2))
        surface.blit(img, rect)

class ComboAnimation:
    def __init__(self, obj_type, positions, points, assets, tile_size, height, duration=500):
        self.obj_type = obj_type
        self.positions = positions  # Danh sách vị trí của các vật phẩm trong túi
        self.points = points
        self.assets = assets
        self.tile_size = tile_size
        self.height = height
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        self.finished = False
        self.font = pygame.font.SysFont(None, 36)
        self.text = self.font.render(f"+{points}", True, (255, 0, 0))
        
    def draw(self, surface):
        now = pygame.time.get_ticks()
        elapsed = now - self.start_time
        if elapsed >= self.duration:
            self.finished = True
            return
        
        # Hiệu ứng phóng to thu nhỏ và mờ dần
        progress = elapsed / self.duration
        alpha = int(255 * (1 - progress))
        scale_factor = 1.0 + 0.5 * (1 - progress)
        
        # Vẽ hiệu ứng cho mỗi vị trí vật phẩm trong combo
        for idx, pos in enumerate(self.positions):
            base_x = 80 + pos * (self.tile_size + 5)
            base_y = self.height + 45
            
            # Tạo bản sao của hình ảnh và điều chỉnh độ trong suốt
            img = self.assets["object"][self.obj_type].copy()
            img_scaled = pygame.transform.scale(img, (int(self.tile_size * scale_factor), int(self.tile_size * scale_factor)))
            
            # Tạo surface có độ trong suốt
            temp = pygame.Surface(img_scaled.get_size(), pygame.SRCALPHA)
            temp.fill((255, 255, 255, alpha))
            img_scaled.blit(temp, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            # Vẽ lên màn hình
            rect = img_scaled.get_rect(center=(base_x + self.tile_size // 2, base_y + self.tile_size // 2))
            surface.blit(img_scaled, rect)
        
        # Hiển thị điểm combo
        text_alpha = pygame.Surface(self.text.get_size(), pygame.SRCALPHA)
        text_alpha.fill((255, 255, 255, alpha))
        text_copy = self.text.copy()
        text_copy.blit(text_alpha, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Vị trí hiển thị điểm ở giữa các vật phẩm
        mid_pos = sum(self.positions) / len(self.positions)
        text_x = 80 + mid_pos * (self.tile_size + 5)
        text_y = self.height + 20 - progress * 30  # Di chuyển lên trên khi animation diễn ra
        
        text_rect = text_copy.get_rect(center=(text_x, text_y))
        surface.blit(text_copy, text_rect)

class BagAddAnimation:
    def __init__(self, obj_type, bag_position, assets, tile_size, height, duration=300):
        self.obj_type = obj_type
        self.bag_position = bag_position  # Vị trí trong túi đồ (0-6)
        self.assets = assets
        self.tile_size = tile_size
        self.height = height
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        self.finished = False
        
    def draw(self, surface):
        now = pygame.time.get_ticks()
        elapsed = now - self.start_time
        if elapsed >= self.duration:
            self.finished = True
            return
        
        # Vị trí trong túi đồ
        base_x = 80 + self.bag_position * (self.tile_size + 5)
        base_y = self.height + 45
        
        # Hiệu ứng phóng to rồi thu nhỏ
        progress = elapsed / self.duration
        if progress < 0.5:
            # Phóng to trong nửa đầu animation
            scale = 1.0 + progress  # Từ 1.0 lên 1.5
        else:
            # Thu nhỏ lại trong nửa sau
            scale = 1.5 - (progress - 0.5) * 2  # Từ 1.5 xuống 1.0
        
        # Tạo bản sao hình ảnh với kích thước mới
        size = int(self.tile_size * scale)
        img = pygame.transform.scale(self.assets["object"][self.obj_type], (size, size))
        
        # Định vị tại tâm của ô túi đồ
        rect = img.get_rect(center=(base_x + self.tile_size // 2, base_y + self.tile_size // 2))
        
        # Vẽ hiệu ứng lên màn hình
        surface.blit(img, rect)
        
        # Tạo hiệu ứng lóe sáng xung quanh
        if progress < 0.3:
            # Vẽ viền sáng
            glow_size = int(self.tile_size * (1.0 + progress * 0.8))
            glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            alpha = int(150 * (1 - progress / 0.3))
            pygame.draw.rect(glow_surf, (255, 255, 0, alpha), 
                            pygame.Rect(0, 0, glow_size, glow_size), 
                            border_radius=5)
            glow_rect = glow_surf.get_rect(center=(base_x + self.tile_size // 2, base_y + self.tile_size // 2))
            surface.blit(glow_surf, glow_rect, special_flags=pygame.BLEND_ALPHA_SDL2)

class TextAnimation:
    def __init__(self, text, x, y, color=(0, 128, 0), duration=2000, speed=1.0, font_size=26):
        self.font = pygame.font.SysFont(None, font_size)
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.start_time = pygame.time.get_ticks()
        self.duration = duration  # Thời gian tồn tại (milliseconds)
        self.speed = speed        # Tốc độ trôi lên
        self.finished = False
        
    def draw(self, surface):
        now = pygame.time.get_ticks()
        elapsed = now - self.start_time
        if elapsed >= self.duration:
            self.finished = True
            return
            
        # Tính toán độ trong suốt (alpha)
        # Ban đầu hiển thị đầy đủ, sau đó mờ dần
        if elapsed < self.duration / 2:
            alpha = 255
        else:
            alpha = int(255 * (1 - (elapsed - self.duration/2) / (self.duration/2)))
        
        # Di chuyển text lên trên
        progress = elapsed / self.duration
        offset_y = int(progress * 50 * self.speed)  # Di chuyển lên 50 pixel trong suốt thời gian animation
        
        # Tạo surface cho text với alpha
        text_surface = self.font.render(self.text, True, self.color)
        temp = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
        temp.fill((255, 255, 255, alpha))
        text_surface.blit(temp, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Vẽ text với vị trí đã được di chuyển lên
        surface.blit(text_surface, (self.x, self.y - offset_y))

    
# Animation Manager class to handle all animations
class AnimationManager:
    def __init__(self, assets, tile_size, height, sound_assets=None):
        self.animations = []
        self.assets = assets
        self.tile_size = tile_size
        self.height = height
        self.sound_assets = sound_assets

    def add_collect_animation(self, x, y, obj_type):
        self.animations.append(CollectAnimation(x, y, obj_type, self.assets, self.tile_size))


    def add_combo_animation(self, obj_type, positions, points):
        self.animations.append(ComboAnimation(obj_type, positions, points, self.assets, self.tile_size, self.height))


    def add_bag_animation(self, obj_type, bag_position):
        self.animations.append(BagAddAnimation(obj_type, bag_position, self.assets, self.tile_size, self.height))

    def add_text_animation(self, text, x, y, color=(0, 128, 0), duration=2000, speed=1.0, font_size=26):
        self.animations.append(TextAnimation(text, x, y, color, duration, speed, font_size))
    
    def update_and_draw(self, surface):
        for anim in self.animations[:]:
            anim.draw(surface)
            if anim.finished:
                self.animations.remove(anim)

    def clear(self):
        self.animations.clear()