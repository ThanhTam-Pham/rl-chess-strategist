import pygame
import sys

from games.chess_game import ChessGame
from games.xiangqi_game import XiangqiGame
from games.go_game import GoGame

pygame.init()
pygame.font.init()
MENU_WIDTH, MENU_HEIGHT = 800, 600
screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
pygame.display.set_caption("Board Game AI Suite")

# Font & Màu sắc
FONT_BIG = pygame.font.SysFont("Arial", 48, bold=True)
FONT_MEDIUM = pygame.font.SysFont("Arial", 28)
FONT_SMALL = pygame.font.SysFont("Arial", 20)

COLOR_BG = (30, 30, 50)
COLOR_WHITE = (255, 255, 255)
COLOR_BUTTON = (220, 220, 220)
COLOR_TEXT = (0, 0, 0)
COLOR_INPUT_ACTIVE = pygame.Color('lightskyblue3')
COLOR_INPUT_INACTIVE = pygame.Color('gray15')
COLOR_ERROR = (255, 100, 100)

# Biến trạng thái toàn cục
app_state = "main_menu"
selected_game = None
selected_difficulty = None
selected_play_mode = None
elo_input_text = ''
input_active = False
error_message = ""

# Hàm tiện ích
def draw_text(text, font, color, surface, x, y, center=True):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect(center=(x, y)) if center else textobj.get_rect(topleft=(x, y))
    surface.blit(textobj, textrect)

def draw_button(text, x, y, w=250, h=60):
    rect = pygame.Rect(x - w // 2, y - h // 2, w, h)
    pygame.draw.rect(screen, COLOR_BUTTON, rect, border_radius=15)
    draw_text(text, FONT_MEDIUM, COLOR_TEXT, screen, x, y)
    return rect

# Xử lý nhập ELO
def handle_elo_input(events, back_btn):
    global input_active, elo_input_text, app_state, error_message
    input_rect = pygame.Rect(MENU_WIDTH // 2 - 100, 340, 200, 50)

    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN:
            input_active = input_rect.collidepoint(event.pos)
            if back_btn.collidepoint(event.pos):
                app_state = "difficulty_select"

        if event.type == pygame.KEYDOWN and input_active:
            if event.key == pygame.K_RETURN:
                try:
                    elo = int(elo_input_text)
                    if elo >= 1001:
                        app_state = "play_mode_select"
                    else:
                        error_message = "ELO for Hard must be >= 1001."
                except ValueError:
                    error_message = "Please enter a valid number."
            elif event.key == pygame.K_BACKSPACE:
                elo_input_text = elo_input_text[:-1]
                error_message = ""
            elif event.unicode.isdigit() and len(elo_input_text) < 5:
                elo_input_text += event.unicode
                error_message = ""

# Hàm khởi động game
def launch_game(game_type, difficulty, play_mode, elo=None):
    try:
        if game_type == "chess":
            game_screen = pygame.display.set_mode((800, 600))
            game_instance = ChessGame(game_screen, difficulty, play_mode, elo=elo)

        elif game_type == "xiangqi":
            # Sử dụng file xiangqi.py tự cài đặt
            from xiangqi import XiangqiGame as LocalXiangqiGame
            game_screen = pygame.display.set_mode((740, 600))
            game_instance = XiangqiGame(game_screen, difficulty, play_mode, local_game=LocalXiangqiGame())

        elif game_type == "go":
            game_screen = pygame.display.set_mode((700, 500))
            game_instance = GoGame(game_screen, difficulty, play_mode)

        else:
            print(f"Unknown game type: {game_type}")
            return

        # Chạy game
        game_instance.run()

    except Exception as e:
        print(f"Error running {game_type}: {e}")

    finally:
        # Quay lại menu chính
        pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))

# Hàm chính
def main_loop():
    global app_state, selected_game, selected_difficulty, selected_play_mode
    global elo_input_text, error_message

    clock = pygame.time.Clock()

    while True:
        events = pygame.event.get()
        screen.fill(COLOR_BG)

        if app_state == "main_menu":
            draw_text("Board Game AI Suite", FONT_BIG, COLOR_WHITE, screen, MENU_WIDTH // 2, 100)
            chess_btn = draw_button("Play Chess", MENU_WIDTH // 2, 250)
            xiangqi_btn = draw_button("Play Xiangqi", MENU_WIDTH // 2, 350)
            go_btn = draw_button("Play Go (9x9)", MENU_WIDTH // 2, 450)
            quit_btn = draw_button("Quit", MENU_WIDTH // 2, 550)

        elif app_state == "difficulty_select":
            draw_text("Select Difficulty", FONT_BIG, COLOR_WHITE, screen, MENU_WIDTH // 2, 100)
            easy_btn = draw_button("Easy", MENU_WIDTH // 2, 250)
            medium_btn = draw_button("Medium", MENU_WIDTH // 2, 350)
            hard_btn = draw_button("Hard", MENU_WIDTH // 2, 450)
            back_btn = draw_button("Back", MENU_WIDTH // 2, 550)

        elif app_state == "elo_select":
            draw_text("Select ELO for Stockfish (Hard)", FONT_BIG, COLOR_WHITE, screen, MENU_WIDTH // 2, 100)
            draw_text("Range: 1001 - 3000+", FONT_SMALL, COLOR_WHITE, screen, MENU_WIDTH // 2, 200)
            draw_text("Default: 3000", FONT_SMALL, COLOR_WHITE, screen, MENU_WIDTH // 2, 230)
            draw_text("Press Enter to Start", FONT_SMALL, (150, 150, 255), screen, MENU_WIDTH // 2, 260)

            input_rect = pygame.Rect(MENU_WIDTH // 2 - 100, 340, 200, 50)
            color = COLOR_INPUT_ACTIVE if input_active else COLOR_INPUT_INACTIVE
            pygame.draw.rect(screen, (50, 50, 60), input_rect)
            pygame.draw.rect(screen, color, input_rect, 2)
            draw_text(elo_input_text, FONT_MEDIUM, COLOR_WHITE, screen, input_rect.centerx, input_rect.centery)
            back_btn = draw_button("Back", MENU_WIDTH // 2, 550)

            if error_message:
                draw_text(error_message, FONT_SMALL, COLOR_ERROR, screen, MENU_WIDTH // 2, 420)

            handle_elo_input(events, back_btn)

        elif app_state == "play_mode_select":
            game_name_map = {"chess": "Chess", "xiangqi": "Xiangqi", "go": "Go"}
            title = f"Select Mode for {game_name_map.get(selected_game, '')}"
            draw_text(title, FONT_BIG, COLOR_WHITE, screen, MENU_WIDTH // 2, 100)

            pvp_btn = draw_button("Player vs. AI", MENU_WIDTH // 2, 280)
            ava_btn = draw_button("AI vs. AI", MENU_WIDTH // 2, 380)
            back_btn_mode = draw_button("Back", MENU_WIDTH // 2, 500)

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if app_state == "main_menu":
                    if chess_btn.collidepoint(event.pos):
                        selected_game = "chess"
                        app_state = "difficulty_select"
                    elif xiangqi_btn.collidepoint(event.pos):
                        selected_game = "xiangqi"
                        app_state = "difficulty_select"
                    elif go_btn.collidepoint(event.pos):
                        selected_game = "go"
                        app_state = "difficulty_select"
                    elif quit_btn.collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()

                elif app_state == "difficulty_select":
                    difficulty = None
                    if easy_btn.collidepoint(event.pos):
                        difficulty = "easy"
                    elif medium_btn.collidepoint(event.pos):
                        difficulty = "medium"
                    elif hard_btn.collidepoint(event.pos):
                        difficulty = "hard"
                    elif back_btn.collidepoint(event.pos):
                        app_state = "main_menu"

                    if difficulty:
                        selected_difficulty = difficulty
                        if selected_game == "chess" and difficulty == "hard":
                            elo_input_text = '3000'
                            app_state = "elo_select"
                            error_message = ""
                        else:
                            app_state = "play_mode_select"

                elif app_state == "play_mode_select":
                    play_mode = None
                    if pvp_btn.collidepoint(event.pos):
                        play_mode = "pvp"
                    elif ava_btn.collidepoint(event.pos):
                        play_mode = "ava"
                    elif back_btn_mode.collidepoint(event.pos):
                        if selected_game == "chess" and selected_difficulty == "hard":
                            app_state = "elo_select"
                        else:
                            app_state = "difficulty_select"

                    if play_mode:
                        selected_play_mode = play_mode
                        elo_val = int(elo_input_text) if (selected_difficulty == "hard" and elo_input_text) else None
                        launch_game(selected_game, selected_difficulty, selected_play_mode, elo=elo_val)

                        # Reset trạng thái sau khi thoát game
                        app_state = "main_menu"
                        selected_game = selected_difficulty = selected_play_mode = None
                        elo_input_text = ''
                        error_message = ""

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main_loop()
