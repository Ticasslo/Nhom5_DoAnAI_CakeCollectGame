import pygame
import sys

def load_assets(TILE_SIZE):
    #TILE_SIZE: Kích thước của mỗi ô trong game
    assets = {}
    # Ảnh nhân vật
    try:
        player_img = pygame.image.load("player.png").convert_alpha()
    except Exception as e:
        print("Lỗi tải player.png:", e)
        sys.exit()
    assets["player"] = pygame.transform.scale(player_img, (TILE_SIZE, TILE_SIZE))
    
    # Ảnh nền cho ô trống
    try:
        floor_img = pygame.image.load("floor.png").convert_alpha()
    except Exception as e:
        print("Lỗi tải floor.png, sử dụng nền trắng", e)
        floor_img = pygame.Surface((TILE_SIZE, TILE_SIZE))
        floor_img.fill((255, 255, 255))
    assets["floor"] = pygame.transform.scale(floor_img, (TILE_SIZE, TILE_SIZE))
    
    assets["wall"] = {}
    wall_files = {
        "T": "tree.png",  # Nếu designer ghi "T" thì dùng ảnh cây
        "W": "wood.png",  # Nếu designer ghi "W" thì dùng ảnh gỗ
        "X": "water.png",  # Nếu designer ghi "X" thì dùng ảnh nước
        "B": "barrel.png",  # Nếu designer ghi "B" thì dùng ảnh thùng
        "H": "haybale.png", # Nếu designer ghi "H" thì dùng ảnh haybel
        "G": "grass.png" # Nếu designer ghi "G" thì dùng ảnh grass
    }
    for code, fname in wall_files.items():
        try:
            img = pygame.image.load(fname).convert_alpha()
            img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
            assets["wall"][code] = img
        except Exception as e:
            print(f"Lỗi tải {fname} cho wall type {code}: {e}")
            # Nếu lỗi, tạo một bề mặt màu xám làm fallback
            temp = pygame.Surface((TILE_SIZE, TILE_SIZE))
            temp.fill((128, 128, 128))
            assets["wall"][code] = temp

    # Tải ảnh vật thể cho các giá trị 0,1,2,3,4
    assets["object"] = {}
    for i in range(5):
        filename = f"object{i}.png"
        try:
            img = pygame.image.load(filename).convert_alpha()
            img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
            assets["object"][i] = img
        except Exception as e:
            print(f"Lỗi tải {filename}: {e}")
            # Nếu không có ảnh, tạo bề mặt với màu mặc định
            temp = pygame.Surface((TILE_SIZE, TILE_SIZE))
            colors = {
                0: (255, 255, 255),
                1: (139, 69, 19),
                2: (255, 255, 0),
                3: (0, 255, 0),
                4: (128, 0, 128)
            }
            temp.fill(colors.get(i, (0,0,0)))
            assets["object"][i] = temp
    return assets

def load_sounds():
    sounds = {}
    try:
        # Âm thanh khi nhặt vật phẩm
        sounds["collect"] = pygame.mixer.Sound("collect.wav")
        # Đặt âm lượng thích hợp (0.0 - 1.0)
        sounds["collect"].set_volume(0.4)
        
        # Âm thanh khi tạo combo
        sounds["combo"] = pygame.mixer.Sound("combo.wav")
        sounds["combo"].set_volume(0.4)
        
    except Exception as e:
        print(f"Lỗi tải âm thanh: {e}")
        # Tạo âm thanh trống nếu không tải được
        empty_sound = pygame.mixer.Sound(buffer=bytearray([]))
        sounds["collect"] = empty_sound
        sounds["combo"] = empty_sound
    
    return sounds