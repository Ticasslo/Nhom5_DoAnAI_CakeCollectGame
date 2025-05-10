import pygame
import sys
import subprocess  # For launching the game file
import os
import threading

pygame.init()
pygame.mixer.init()

# Screen settings
SCREEN_WIDTH = 675
SCREEN_HEIGHT = 760
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Game Menu")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_BLUE = (173, 216, 230)
DARK_BLUE = (70, 130, 180)
LIGHT_GREEN = (144, 238, 144)
DARK_GREEN = (0, 100, 0)
LIGHT_ORANGE = (255, 200, 100)
DARK_ORANGE = (255, 140, 0)

# Font
title_font = pygame.font.SysFont(None, 80)
button_font = pygame.font.SysFont(None, 50)

class Button:
    def __init__(self, x, y, width, height, text, font, color=(200, 200, 200), hover_color=(180, 180, 220)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.hover = False
        
    def draw(self, surface):
        current_color = self.hover_color if self.hover else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=10)  # Border
        
        text_surf = self.font.render(self.text, True, BLACK)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.hover = self.rect.collidepoint(pos)
        return self.hover
        
    def is_clicked(self, pos, click):
        return click and self.rect.collidepoint(pos)

# Biến toàn cục để kiểm tra trạng thái hiển thị cửa sổ Credit
show_credits = False
# Hàm tải hình ảnh
def load_image(filename, size=(100, 100)):
    try:
        img = pygame.image.load(filename).convert_alpha()
        img = pygame.transform.scale(img, size)
        return img
    except Exception as e:
        print(f"Không thể tải hình ảnh {filename}: {e}")
        # Tạo một hình ảnh giả
        surf = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surf, GRAY, (0, 0, size[0], size[1]), 2)
        text = button_font.render("No Image", True, BLACK)
        surf.blit(text, text.get_rect(center=(size[0]//2, size[1]//2)))
        return surf

# Hàm hiển thị cửa sổ Credit
def display_credits(screen):
    credit_surf = pygame.Surface((550, 600))
    credit_surf.fill(WHITE)
    pygame.draw.rect(credit_surf, BLACK, (0, 0, 550, 600), 2)
    
    # Font cho nội dung Credit
    title_font = pygame.font.SysFont(None, 35)
    content_font = pygame.font.SysFont(None, 27)
    
    # Tiêu đề
    title_text = title_font.render("Ho Chi Minh City University", True, BLACK)
    title_text2 = title_font.render("of Technology and Education", True, BLACK)
    
    # Nội dung
    ai_project = content_font.render("- Artificial Intelligence Project -", True, BLACK)
    topic = content_font.render("Topic: Cake Collect Game", True, BLACK)
    student1 = content_font.render("23110327 - Huynh Ngoc Thang", True, BLACK)
    student2 = content_font.render("23110203 - Pham Tran Thien Dang", True, BLACK)
    inspiration = content_font.render("This project was inspired from an event game", True, BLACK)
    inspiration2 = content_font.render("called \"Cake Hound Round-Up!\" from Cookie Run: Kingdom", True, BLACK)
    
    # Vẽ nội dung
    credit_surf.blit(title_text, (20, 27))
    credit_surf.blit(title_text2, (20, 60))
    credit_surf.blit(ai_project, (20, 110))
    credit_surf.blit(topic, (20, 150))
    credit_surf.blit(student1, (18, 190))
    credit_surf.blit(student2, (18, 220))
    credit_surf.blit(inspiration, (12, 258))
    credit_surf.blit(inspiration2, (12, 280))
    
    # Thêm hình ảnh sinh viên
    student1_img = load_image("student1.png", (100, 100))
    student2_img = load_image("student2.png", (100, 100))
    example_img = load_image("example.png", (510, 220))
    hcmute_img = load_image("hcmute.png", (100, 100))
    
    # Vẽ hình ảnh
    credit_surf.blit(student1_img, (332, 135))
    credit_surf.blit(student2_img, (440, 135))
    credit_surf.blit(example_img, (20, 310))
    credit_surf.blit(hcmute_img, (389, 12))
    
    # Thêm thông báo về video demo
    video_text = content_font.render("Video demo gameplay:", True, BLACK)
    credit_surf.blit(video_text, (10, 555))
    
    # Vẽ nút play video và close
    play_video_button = Button(225, 540, 150, 50, "Play Video", content_font, LIGHT_GREEN, DARK_GREEN)
    close_button = Button(385, 540, 150, 50, "Close", button_font, LIGHT_BLUE, DARK_BLUE)
    
    play_video_button.draw(credit_surf)
    close_button.draw(credit_surf)
    
    # Hiển thị cửa sổ Credit
    screen.blit(credit_surf, (SCREEN_WIDTH//2 - 275, SCREEN_HEIGHT//2 - 250))
    
    return close_button, play_video_button

# Hàm phát video demo
def play_video_demo():
    try:
        video_path = "gameplay_demo.mp4"  # Đường dẫn đến file video
        
        if os.path.exists(video_path):
            if sys.platform == "win32":
                os.startfile(video_path)
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, video_path])
        else:
            print("Không tìm thấy file video demo.")
    except Exception as e:
        print(f"Lỗi khi phát video: {e}")
        
        
def load_background():
    try:
        bg_img = pygame.image.load("menu_background.png").convert()
        bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        return bg_img
    except Exception as e:
        print(f"Could not load background image: {e}")
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            # Create a gradient from light blue to white
            color_value = 173 + (255 - 173) * (y / SCREEN_HEIGHT)
            pygame.draw.line(bg, (color_value, color_value, 255), (0, y), (SCREEN_WIDTH, y))
        return bg

def main_menu():
    buttons = {
        "play": Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 250, 200, 70, "Play", button_font, LIGHT_BLUE, DARK_BLUE),
        "playai": Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 165, 200, 70, "Play AI", button_font, LIGHT_GREEN, DARK_GREEN),
        "battleai": Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 165, 200, 70, "AI Battle!", button_font, LIGHT_ORANGE, DARK_ORANGE),
        "quit": Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 250, 200, 70, "Quit", button_font, LIGHT_BLUE, DARK_BLUE),
        "credit": Button(SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT - 50, 100, 40, "Credit", pygame.font.SysFont(None, 30), LIGHT_BLUE, DARK_BLUE),
    }
    
    background = load_background()
    
    running = True
    clock = pygame.time.Clock()
    show_credits = False
    
    while running:
        clock.tick(60)
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True
        
        screen.blit(background, (0, 0))
        
        title_text = title_font.render("CAKE COLLECT GAME", True, WHITE)
        title_border = title_font.render("CAKE COLLECT GAME", True, BLACK)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4 - 105))

        # Vẽ viền đen bằng cách blit title_border quanh title_rect
        for dx, dy in [(-2,0),(2,0),(0,-2),(0,2),(-2,-2),(-2,2),(2,-2),(2,2)]:
            screen.blit(title_border, title_rect.move(dx, dy))

        # Vẽ chữ chính
        screen.blit(title_text, title_rect)
        
        # Vẽ và kiểm tra các nút
        if not show_credits:
            for button in buttons.values():
                button.check_hover(mouse_pos)
                button.draw(screen)
                
            # Xử lý nhấn nút
            if buttons["play"].is_clicked(mouse_pos, mouse_click):
                start_game()
            elif buttons["playai"].is_clicked(mouse_pos, mouse_click):
                start_ai_game()
            elif buttons["battleai"].is_clicked(mouse_pos, mouse_click):
                start_battle_ai()
            elif buttons["quit"].is_clicked(mouse_pos, mouse_click):
                pygame.quit()
                sys.exit()
            elif buttons["credit"].is_clicked(mouse_pos, mouse_click):
                show_credits = True
        else:
            # Vị trí của cửa sổ Credit trên màn hình
            credit_pos = (SCREEN_WIDTH//2 - 275, SCREEN_HEIGHT//2 - 250)
            
            # Hiển thị cửa sổ Credit
            close_button, play_video_button = display_credits(screen)
            
            # Điều chỉnh vị trí chuột tương đối với cửa sổ Credit
            credit_mouse_pos = (mouse_pos[0] - credit_pos[0], mouse_pos[1] - credit_pos[1])
            
            # Kiểm tra nút Close và Play Video với vị trí chuột đã điều chỉnh
            close_button.check_hover(credit_mouse_pos)
            play_video_button.check_hover(credit_mouse_pos)
            
            if close_button.is_clicked(credit_mouse_pos, mouse_click):
                show_credits = False
            elif play_video_button.is_clicked(credit_mouse_pos, mouse_click):
                # Phát video trong một thread riêng
                video_thread = threading.Thread(target=play_video_demo)
                video_thread.daemon = True
                video_thread.start()
                
        pygame.display.flip()

def start_game():
    try:
        pygame.display.quit()
        
        subprocess.run([sys.executable, "main.py"], check=True)
        
        pygame.init()
        pygame.mixer.init()
        global screen
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Game Menu")
        
    except Exception as e:
        print(f"Error starting game: {e}")
        pygame.quit()
        sys.exit()

def start_ai_game():
    try:
        pygame.display.quit()
        
        subprocess.run([sys.executable, "playAI5.py"], check=True)
        
        pygame.init()
        pygame.mixer.init()
        global screen
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Game Menu")
        
    except Exception as e:
        print(f"Error starting AI game: {e}")
        pygame.quit()
        sys.exit()

def start_battle_ai():
    try:
        pygame.display.quit()
        
        subprocess.run([sys.executable, "battleAI.py"], check=True)
        
        pygame.init()
        pygame.mixer.init()
        global screen
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Game Menu")
        
    except Exception as e:
        print(f"Error starting Battle AI game: {e}")
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main_menu()