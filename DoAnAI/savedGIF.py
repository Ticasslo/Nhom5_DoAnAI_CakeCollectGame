import os
import sys
import pygame
from pygame.locals import *
import imageio.v3 as imageio
import threading
import time
import numpy as np

class GifViewer:
    def __init__(self):
        pygame.init()
        self.width, self.height = 1200, 720
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Trình xem GIF thuật toán")
        
        self.font = pygame.font.SysFont(None, 28)
        self.small_font = pygame.font.SysFont(None, 21)
        
        self.algorithms = ["Compare", "BFS", "DFS", "A*"]  # Các thuật toán hỗ trợ
        self.current_algo_index = 0
        
        self.gif_frames = {}      # Lưu các frame của GIF
        self.current_frame_index = {}  # Chỉ số frame hiện tại
        self.frame_count = {}     # Tổng số frame
        self.gif_surfaces = {}    # Surface để vẽ
        self.gif_info = {}        # Thông tin GIF
        
        self.load_all_gifs()      # Tải tất cả các GIF
        
        self.playing = {}         # Trạng thái phát
        for algo in self.algorithms:
            self.playing[algo] = True
            
        self.last_frame_time = time.time()
        self.fps = 5             # Tốc độ phát (frames per second)
        
        self.tabs_height = 40     # Chiều cao của thanh tab
        self.info_height = 60     # Chiều cao phần thông tin
        
    def load_all_gifs(self):
        if not os.path.exists("gif"):
            os.makedirs("gif")
            
        for algo in self.algorithms:
            self.load_gif(algo)
    
    def load_gif(self, algo):
        self.gif_frames[algo] = []
        self.current_frame_index[algo] = 0
        self.frame_count[algo] = 0
        self.gif_surfaces[algo] = None
        self.gif_info[algo] = None
        
        # Tìm các file GIF cho thuật toán này
        gif_files = []
        for file in os.listdir("gif"):
            if file.startswith(f"{algo}_") and file.endswith(".gif"):
                gif_files.append(file)
                
        if not gif_files:
            return
            
        # Sử dụng file mới nhất (theo timestamp)
        latest_file = max(gif_files, key=lambda x: os.path.getmtime(os.path.join("gif", x)))
        file_path = os.path.join("gif", latest_file)
        
        # Trích xuất thông tin từ tên file
        # Định dạng: algorithm_timeXXX_stepsYYY_timestamp.gif
        parts = latest_file.split("_")
        thinking_time = None
        steps = None
        
        for part in parts:
            if part.startswith("time"):
                try:
                    thinking_time = float(part[4:])
                except ValueError:
                    pass
            elif part.startswith("steps"):
                try:
                    steps = int(part[5:])
                except ValueError:
                    pass
        
        self.gif_info[algo] = {
            "filename": latest_file,
            "thinking_time": thinking_time,
            "steps": steps
        }
        
        # Tải các frame trong một luồng riêng để không làm treo giao diện
        threading.Thread(target=self._load_gif_frames, args=(algo, file_path), daemon=True).start()
    
    def _load_gif_frames(self, algo, file_path):
        """Tải các frame GIF trong một luồng riêng"""
        try:
            # Tải file GIF
            gif = imageio.imread(file_path)
            
            # Xử lý từng frame
            for frame in gif:
                # Chuyển từ mảng numpy sang pygame surface
                surface = pygame.surfarray.make_surface(frame.transpose(1, 0, 2))
                if surface.get_locked():
                    surface.unlock()
                self.gif_frames[algo].append(surface)
            
            self.frame_count[algo] = len(self.gif_frames[algo])
            
            # Chuẩn bị surface hiển thị với tỷ lệ khung hình phù hợp
            if self.frame_count[algo] > 0:
                first_frame = self.gif_frames[algo][0]
                frame_width, frame_height = first_frame.get_size()
                
                # Tính toán kích thước để vừa với khu vực xem
                view_width = self.width
                view_height = self.height - self.tabs_height - self.info_height
                
                scale_factor = min(view_width / frame_width, view_height / frame_height)
                new_width = int(frame_width * scale_factor)
                new_height = int(frame_height * scale_factor)
                
                # Scale tất cả các frame
                for i, frame in enumerate(self.gif_frames[algo]):
                    self.gif_frames[algo][i] = pygame.transform.smoothscale(frame, (new_width, new_height))
                
                print(f"Đã tải {self.frame_count[algo]} frame cho {algo}")
            
        except Exception as e:
            print(f"Lỗi khi tải GIF cho {algo}: {e}")
            self.gif_frames[algo] = []
            self.frame_count[algo] = 0
            
    def draw_tabs(self):
        tab_width = self.width // len(self.algorithms)
        
        for i, algo in enumerate(self.algorithms):
            tab_rect = pygame.Rect(i * tab_width, 0, tab_width, self.tabs_height)
            
            # Làm nổi bật tab hiện tại
            if i == self.current_algo_index:
                pygame.draw.rect(self.screen, (220, 220, 255), tab_rect)
                border_color = (0, 0, 128)
            else:
                pygame.draw.rect(self.screen, (200, 200, 200), tab_rect)
                border_color = (128, 128, 128)
                
            pygame.draw.rect(self.screen, border_color, tab_rect, 2)
            
            # Hiển thị tên thuật toán
            text = self.font.render(algo, True, (0, 0, 0))
            text_rect = text.get_rect(center=tab_rect.center)
            self.screen.blit(text, text_rect)
            
            # Thêm một chỉ báo nhỏ nếu có GIF đã được tải
            if self.frame_count.get(algo, 0) > 0:
                indicator_rect = pygame.Rect(tab_rect.right - 15, tab_rect.top + 5, 10, 10)
                pygame.draw.circle(self.screen, (0, 200, 0), indicator_rect.center, 5)
    
    def draw_info(self):
        algo = self.algorithms[self.current_algo_index]
        info_rect = pygame.Rect(0, self.height - self.info_height, self.width, self.info_height)
        pygame.draw.rect(self.screen, (240, 240, 240), info_rect)
        pygame.draw.line(self.screen, (200, 200, 200), 
                         (0, self.height - self.info_height), 
                         (self.width, self.height - self.info_height), 2)
        
        if algo == "Compare":
            # Hiển thị thông tin cho tab so sánh
            info_text = "Compare each search algorithm"
            info_surf = self.font.render(info_text, True, (0, 0, 0))
            info_rect = info_surf.get_rect()
            info_rect.left = 10
            info_rect.top = self.height - self.info_height + 20
            self.screen.blit(info_surf, info_rect)
            
            # Nút Tải lại
            reload_button_width = 80
            reload_button_height = 30
            reload_button_x = self.width - reload_button_width - 20
            reload_button_y = self.height - self.info_height + 15
            reload_button_rect = pygame.Rect(reload_button_x, reload_button_y, reload_button_width, reload_button_height)
            pygame.draw.rect(self.screen, (200, 200, 200), reload_button_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), reload_button_rect, 2)
            
            reload_surf = self.small_font.render("Refresh", True, (0, 0, 0))
            reload_text_rect = reload_surf.get_rect(center=reload_button_rect.center)
            self.screen.blit(reload_surf, reload_text_rect)
            
            return None, None, reload_button_rect, None
    
        if self.gif_info.get(algo) and self.frame_count.get(algo, 0) > 0:
            info = self.gif_info[algo]
            
            # Hiển thị số frame hiện tại / tổng số frame
            frame_text = f"Frame: {self.current_frame_index[algo] + 1}/{self.frame_count[algo]}"
            frame_surf = self.small_font.render(frame_text, True, (0, 0, 0))
            self.screen.blit(frame_surf, (10, self.height - self.info_height + 10))
            
            # Thời gian suy nghĩ
            if info["thinking_time"] is not None:
                time_text = f"Total thinking time: {info['thinking_time']:.6f} s"
                time_surf = self.small_font.render(time_text, True, (0, 0, 0))
                self.screen.blit(time_surf, (10, self.height - self.info_height + 35))
            
            # Số bước
            if info["steps"] is not None:
                steps_text = f"Total steps: {info['steps']}"
                steps_surf = self.small_font.render(steps_text, True, (0, 0, 0))
                self.screen.blit(steps_surf, (250, self.height - self.info_height + 35))
            
            # Nút Phát/Tạm dừng
            button_width = 80
            button_height = 30
            button_x = self.width - button_width - 20
            button_y = self.height - self.info_height + 15
            
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            pygame.draw.rect(self.screen, (200, 200, 200), button_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), button_rect, 2)
            
            button_text = "Pause" if self.playing[algo] else "Play"
            button_surf = self.small_font.render(button_text, True, (0, 0, 0))
            button_text_rect = button_surf.get_rect(center=button_rect.center)
            self.screen.blit(button_surf, button_text_rect)
            
            # Nút Khởi động lại
            restart_button_width = 80
            restart_button_x = button_x - restart_button_width - 10
            restart_button_rect = pygame.Rect(restart_button_x, button_y, restart_button_width, button_height)
            pygame.draw.rect(self.screen, (200, 200, 200), restart_button_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), restart_button_rect, 2)
            
            restart_surf = self.small_font.render("Restart", True, (0, 0, 0))
            restart_text_rect = restart_surf.get_rect(center=restart_button_rect.center)
            self.screen.blit(restart_surf, restart_text_rect)
            
            # Nút Tải lại
            reload_button_width = 80
            reload_button_x = restart_button_x - reload_button_width - 100
            reload_button_rect = pygame.Rect(reload_button_x, button_y, reload_button_width, button_height)
            pygame.draw.rect(self.screen, (200, 200, 200), reload_button_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), reload_button_rect, 2)
            
            reload_surf = self.small_font.render("Reload", True, (0, 0, 0))
            reload_text_rect = reload_surf.get_rect(center=reload_button_rect.center)
            self.screen.blit(reload_surf, reload_text_rect)
            
            # Nút Step
            step_button_width = 60
            step_button_x = restart_button_x - step_button_width - 10
            step_button_rect = pygame.Rect(step_button_x, button_y, step_button_width, button_height)
            pygame.draw.rect(self.screen, (200, 200, 200), step_button_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), step_button_rect, 2)

            step_surf = self.small_font.render("Step", True, (0, 0, 0))
            step_text_rect = step_surf.get_rect(center=step_button_rect.center)
            self.screen.blit(step_surf, step_text_rect)

            # Cập nhật giá trị trả về của hàm để bao gồm nút step
            return button_rect, restart_button_rect, reload_button_rect, step_button_rect
        else:
            # Không có GIF nào được tải cho thuật toán này
            no_gif_text = f"Trying to find records for {algo}"
            no_gif_surf = self.font.render(no_gif_text, True, (128, 128, 128))
            no_gif_rect = no_gif_surf.get_rect(center=(self.width // 2, self.height - self.info_height + 30))
            self.screen.blit(no_gif_surf, no_gif_rect)
            
            # Nút Tải lại
            reload_button_width = 80
            reload_button_height = 30
            reload_button_x = self.width - reload_button_width - 20
            reload_button_y = self.height - self.info_height + 15
            reload_button_rect = pygame.Rect(reload_button_x, reload_button_y, reload_button_width, reload_button_height)
            pygame.draw.rect(self.screen, (200, 200, 200), reload_button_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), reload_button_rect, 2)
            
            reload_surf = self.small_font.render("Reload", True, (0, 0, 0))
            reload_text_rect = reload_surf.get_rect(center=reload_button_rect.center)
            self.screen.blit(reload_surf, reload_text_rect)
            
            return None, None, reload_button_rect, None
    
    def draw_current_frame(self):
        algo = self.algorithms[self.current_algo_index]
        
        if algo == "Compare":
            # Hiển thị biểu đồ so sánh
            self.draw_comparison()
            return
    
        if self.gif_frames.get(algo) and self.frame_count.get(algo, 0) > 0:
            frame = self.gif_frames[algo][self.current_frame_index[algo]]
            if frame.get_locked():
                frame.unlock()
            frame_rect = frame.get_rect()
            
            # Căn giữa frame trong khu vực xem
            frame_x = (self.width - frame_rect.width) // 2
            frame_y = self.tabs_height + (self.height - self.tabs_height - self.info_height - frame_rect.height) // 2
            
            self.screen.blit(frame, (frame_x, frame_y))
        else:
            # Hiển thị thông báo nếu không có GIF nào được tải
            self.screen.fill((255, 255, 255), 
                            (0, self.tabs_height, self.width, self.height - self.tabs_height - self.info_height))
            
            if self.gif_frames.get(algo) is None:
                message = "Loading Records"
            else:
                message = f"Trying to find records for {algo}"
                
            text_surf = self.font.render(message, True, (128, 128, 128))
            text_rect = text_surf.get_rect(center=(self.width // 2, 
                                                  self.tabs_height + (self.height - self.tabs_height - self.info_height) // 2))
            self.screen.blit(text_surf, text_rect)
    
    def update_frame(self):
        current_time = time.time()
        algo = self.algorithms[self.current_algo_index]
        
        if (self.playing.get(algo, False) and 
            self.frame_count.get(algo, 0) > 0 and 
            current_time - self.last_frame_time >= 1.0 / self.fps):
            
            self.current_frame_index[algo] = (self.current_frame_index[algo] + 1) % self.frame_count[algo]
            self.last_frame_time = current_time
    
    def draw_bar_chart(self, data, labels, title, x_pos, y_pos, width, height, max_value=None):
        """Vẽ biểu đồ cột với dữ liệu đã cho"""
        if not data:
            return
            
        # Xác định giá trị lớn nhất để scale
        if max_value is None:
            max_value = max(data) if data else 1
        
        # Vẽ khung biểu đồ
        chart_rect = pygame.Rect(x_pos, y_pos, width, height)
        pygame.draw.rect(self.screen, (240, 240, 240), chart_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), chart_rect, 2)
        
        # Vẽ tiêu đề
        title_surf = self.font.render(title, True, (0, 0, 0))
        title_rect = title_surf.get_rect(center=(x_pos + width // 2, y_pos - 15))
        self.screen.blit(title_surf, title_rect)
        
        # Vẽ các cột
        bar_width = width // (len(data) * 2)
        gap = bar_width // 2
        
        for i, (value, label) in enumerate(zip(data, labels)):
            if value is None:
                continue
                
            # Tính toán chiều cao của cột
            bar_height = int((value / max_value) * (height - 40)) if max_value > 0 else 0
            
            # Vị trí cột
            bar_x = x_pos + gap + i * (bar_width + gap)
            bar_y = y_pos + height - bar_height - 18  # Để lại chỗ cho nhãn
            
            # Vẽ cột
            bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
            pygame.draw.rect(self.screen, (50, 100, 200), bar_rect)
            pygame.draw.rect(self.screen, (0, 0, 150), bar_rect, 2)
            
            # Vẽ giá trị
            if isinstance(value, float):
                value_text = f"{value:.6f}"
            else:
                value_text = str(value)
                
            value_surf = self.small_font.render(value_text, True, (0, 0, 0))
            value_rect = value_surf.get_rect(center=(bar_x + bar_width // 2, bar_y - 12))
            self.screen.blit(value_surf, value_rect)
            
            # Vẽ nhãn
            label_surf = self.small_font.render(label, True, (0, 0, 0))
            label_rect = label_surf.get_rect(center=(bar_x + bar_width // 2, y_pos + height - 12))
            self.screen.blit(label_surf, label_rect)
    
    def draw_comparison(self):
        """Vẽ biểu đồ so sánh giữa các thuật toán"""
        # Lấy dữ liệu so sánh
        thinking_times = []
        steps = []
        labels = []
        
        for algo in self.algorithms:
            if algo == "Compare":
                continue
                
            labels.append(algo)
            
            # Lấy thời gian suy nghĩ
            if (self.gif_info.get(algo) and 
                self.gif_info[algo].get("thinking_time") is not None):
                thinking_times.append(self.gif_info[algo]["thinking_time"])
            else:
                thinking_times.append(None)
                
            # Lấy số bước
            if (self.gif_info.get(algo) and 
                self.gif_info[algo].get("steps") is not None):
                steps.append(self.gif_info[algo]["steps"])
            else:
                steps.append(None)
        
        # Xóa các giá trị None
        valid_times = [t for t in thinking_times if t is not None]
        valid_steps = [s for s in steps if s is not None]
        
        max_time = max(valid_times) if valid_times else 1
        max_steps = max(valid_steps) if valid_steps else 1
        
        # Khu vực hiển thị
        view_area = pygame.Rect(0, self.tabs_height, 
                            self.width, self.height - self.tabs_height - self.info_height)
        pygame.draw.rect(self.screen, (255, 255, 255), view_area)
        
        # Vẽ hai biểu đồ
        chart_width = self.width * 0.8
        chart_height = (self.height - self.tabs_height - self.info_height) * 0.41
        
        # Biểu đồ thời gian suy nghĩ
        time_chart_x = (self.width - chart_width) // 2
        time_chart_y = self.tabs_height + 40
        self.draw_bar_chart(thinking_times, labels, "Total thinking times in each search (s)",
                        time_chart_x, time_chart_y, chart_width, chart_height, max_time)
        
        # Biểu đồ số bước
        steps_chart_x = (self.width - chart_width) // 2
        steps_chart_y = time_chart_y + chart_height + 60
        self.draw_bar_chart(steps, labels, "Total steps (steps)",
                        steps_chart_x, steps_chart_y, chart_width, chart_height, max_steps)
    
    def run(self):
        running = True
        clock = pygame.time.Clock()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Nhấp chuột trái
                        # Kiểm tra xem có nhấp vào tab nào không
                        tab_width = self.width // len(self.algorithms)
                        tab_click_x = event.pos[0] // tab_width
                        
                        if event.pos[1] < self.tabs_height and 0 <= tab_click_x < len(self.algorithms):
                            self.current_algo_index = tab_click_x
                        
                        # Kiểm tra xem có nhấp vào nút phát/tạm dừng hoặc khởi động lại không
                        buttons = self.draw_info()
                        if buttons[0] and buttons[0].collidepoint(event.pos):
                            # Nút Phát/Tạm dừng
                            algo = self.algorithms[self.current_algo_index]
                            self.playing[algo] = not self.playing.get(algo, True)
                        
                        elif buttons[1] and buttons[1].collidepoint(event.pos):
                            # Nút Khởi động lại
                            algo = self.algorithms[self.current_algo_index]
                            self.current_frame_index[algo] = 0
                        
                        elif buttons[2] and buttons[2].collidepoint(event.pos):
                            # Nút Tải lại
                            algo = self.algorithms[self.current_algo_index]
                            self.load_gif(algo)
                            
                        elif buttons[3] and buttons[3].collidepoint(event.pos):
                            # Nút Step
                            algo = self.algorithms[self.current_algo_index]
                            if self.frame_count.get(algo, 0) > 0:
                                # Tạm dừng phát tự động
                                self.playing[algo] = False
                                # Chuyển đến frame tiếp theo
                                self.current_frame_index[algo] = (self.current_frame_index[algo] + 1) % self.frame_count[algo]
                                
                        elif buttons[2] and buttons[2].collidepoint(event.pos):
                            # Nút Tải lại hoặc Refresh
                            algo = self.algorithms[self.current_algo_index]
                            if algo == "Compare":
                                # Làm mới tất cả các gif để cập nhật dữ liệu so sánh
                                for alg in self.algorithms:
                                    if alg != "Compare":
                                        self.load_gif(alg)
                            else:
                                self.load_gif(algo)
            
            # Cập nhật frame
            self.update_frame()
            
            # Vẽ mọi thứ
            self.screen.fill((255, 255, 255))
            self.draw_tabs()
            self.draw_current_frame()
            self.draw_info()
            
            pygame.display.flip()
            clock.tick(30)  # Giới hạn 30 FPS cho giao diện
        
        pygame.display.quit()

def main():
    viewer = GifViewer()
    viewer.run()

if __name__ == "__main__":
    main()