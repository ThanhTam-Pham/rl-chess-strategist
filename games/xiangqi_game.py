import pygame
import time
import os

def draw_text(text, font, color, surface, x, y, center=True):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect(center=(x, y)) if center else textobj.get_rect(topleft=(x, y))
    surface.blit(textobj, textrect)

class XiangqiGame:
    def __init__(self, screen, difficulty, play_mode, local_game=None):
        self.screen = screen
        self.difficulty = difficulty
        self.play_mode = play_mode
        
        if local_game is not None:
            self.board = local_game
        else:
            from xiangqi import XiangqiGame as LocalGame
            self.board = LocalGame()
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.last_move = None

        self.red_player = None
        self.black_player = None
        if self.play_mode == 'pvp':
            self.player_color = 'red'
            self.ai_color = 'black'
            self.black_player = self._create_agent(difficulty)
        elif self.play_mode == 'ava':
            self.player_color = None
            self.ai_color = None
            self.red_player = self._create_agent(difficulty)
            self.black_player = self._create_agent(difficulty)

        self.board_rect = pygame.Rect(0, 0, 540, 600)
        self.panel_rect = pygame.Rect(540, 0, 200, 600)
        self.SQUARE_SIZE = 60
        self.piece_images = {}
        self.board_image = None
        self.load_assets()

        self.selected_piece_square = None
        self.valid_moves_for_selected = []
        self.ai_is_thinking = False
        self.ai_move_time = 0
        self.game_over_message = ""
        self.game_over_time = None
        self.font_large = pygame.font.SysFont("SimSun", 36, bold=True)
        self.font_small = pygame.font.SysFont("SimSun", 20)
        self.font_info = pygame.font.SysFont("SimSun", 18)
        # Per-player clocks (seconds). 5 minutes each by default.
        self.time_left = {
            'red': 5 * 60,
            'black': 5 * 60
        }
        self.ai_delay_ms = 150
        if self.play_mode == 'ava':
            self.ai_delay_ms = 10000
    
    def _create_agent(self, difficulty):
        from engines.xiangqi_engine import EasyAgent, MediumAgent
        if difficulty == "easy":
            return EasyAgent(self.board)
        else:
            return MediumAgent(self.board)

    def load_assets(self):
        assets_path = os.path.join('assets', 'xiangqi')
        board_img_path = os.path.join(assets_path, 'board.png')
        try:
            self.board_image = pygame.image.load(board_img_path)
            self.board_image = pygame.transform.scale(self.board_image, (self.board_rect.width, self.board_rect.height))
        except Exception:
            self.board_image = pygame.Surface((self.board_rect.width, self.board_rect.height))
            self.board_image.fill((200, 180, 140))
        class_to_code = {
            'Chariot': 'R',
            'Horse': 'N',
            'Elephant': 'B',
            'Advisor': 'A',
            'General': 'K',
            'Cannon': 'C',
            'Soldier': 'P'
        }

        for color_prefix, color_name in (('r', 'red'), ('b', 'black')):
            for cls_name, code in class_to_code.items():
                fname = f"{color_prefix}{code}.png"
                img_path = os.path.join(assets_path, fname)
                try:
                    img = pygame.image.load(img_path)
                    img = pygame.transform.scale(img, (self.SQUARE_SIZE - 10, self.SQUARE_SIZE - 10))
                except Exception:
                    img = pygame.Surface((self.SQUARE_SIZE - 10, self.SQUARE_SIZE - 10), pygame.SRCALPHA)
                    color = (180, 50, 50) if color_name == 'red' else (50, 50, 180)
                    img.fill(color)
                self.piece_images[(color_name, cls_name)] = img

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            current_player = getattr(self.board, 'current_player', None)

            if not self.game_over_message and current_player in self.time_left:
                self.time_left[current_player] -= dt
                if self.time_left[current_player] <= 0:
                    winner = 'black' if current_player == 'red' else 'red'
                    self.game_over_message = f"{winner.capitalize()} wins on time"
                    self.game_over_time = time.time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if not self.ai_is_thinking and \
                           ((self.play_mode == 'pvp' and current_player == self.player_color) or \
                            self.play_mode is None):
                            self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            # AI move
            if not self.ai_is_thinking and ((self.play_mode == 'pvp' and current_player == self.ai_color) or (self.play_mode == 'ava')):
                self.handle_ai_move()

            # Vẽ game
            self.draw()
            # display updated in draw()

            # If game over was just set, show overlay for a few seconds then exit to menu
            if self.game_over_message and self.game_over_time is not None:
                # show overlay for 6 seconds
                if time.time() - self.game_over_time > 6:
                    break
    # ... (hàm handle_events không đổi)
    def handle_click(self, pos):
        if not self.board_rect.collidepoint(pos):
            return
            
        board_pos = self.screen_pos_to_board(pos)
        if not (0 <= board_pos[0] < 10 and 0 <= board_pos[1] < 9):
            return

        # Xử lý click
        if self.selected_piece_square is None:
            piece = self.board.get_board()[board_pos[0]][board_pos[1]]
            if piece and piece.color == self.board.current_player:
                self.selected_piece_square = board_pos
        else:
            # Thử di chuyển quân cờ
            moving_color = getattr(self.board, 'current_player', None)
            res = self.board.make_move(self.selected_piece_square, board_pos)
            moved = False
            captured = None
            if isinstance(res, tuple):
                moved, captured = res
            else:
                moved = bool(res)

            if moved:
                self.last_move = (self.selected_piece_square, board_pos)
                # If captured General -> moving_color wins
                if captured and getattr(captured, 'name', '') == 'General':
                    self.game_over_message = f"{moving_color.capitalize()} captured the General and wins"
                    self.game_over_time = time.time()
                else:
                    # check for checkmate on opponent
                    opponent = getattr(self.board, 'current_player', None)
                    try:
                        if self.board.is_checkmate(opponent):
                            self.game_over_message = f"{moving_color.capitalize()} wins by checkmate"
                            self.game_over_time = time.time()
                    except Exception:
                        pass
            self.selected_piece_square = None
                    
    def handle_ai_move(self):
        self.ai_is_thinking = True
        start_time = time.time()
        
        current_player = self.board.current_player
        agent = self.black_player if current_player == 'black' else self.red_player
        
        if agent:
            from_pos, to_pos = agent.select_move()
            if from_pos and to_pos:
                moving_color = current_player
                res = self.board.make_move(from_pos, to_pos)
                moved = False
                captured = None
                if isinstance(res, tuple):
                    moved, captured = res
                else:
                    moved = bool(res)
                if moved:
                    self.last_move = (from_pos, to_pos)
                    # If captured General -> moving_color wins
                    if captured and getattr(captured, 'name', '') == 'General':
                        self.game_over_message = f"{moving_color.capitalize()} captured the General and wins"
                        self.running = False
                    else:
                        opponent = getattr(self.board, 'current_player', None)
                        try:
                            if self.board.is_checkmate(opponent):
                                self.game_over_message = f"{moving_color.capitalize()} wins by checkmate"
                                self.running = False
                        except Exception:
                            pass
                    # Pause according to configured AI delay so users can observe
                    try:
                        pygame.time.delay(self.ai_delay_ms)
                    except Exception:
                        time.sleep(self.ai_delay_ms / 1000.0)
        
        self.ai_move_time = time.time() - start_time
        self.ai_is_thinking = False

    def board_pos_to_screen(self, pos):
        row, col = pos
        x = col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
        y = row * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
        return (x, y)

    def screen_pos_to_board(self, pos):
        x, y = pos
        col = x // self.SQUARE_SIZE
        row = y // self.SQUARE_SIZE
        return (row, col)
        

    # ... (các hàm select_square, reset_selection, draw không đổi)
    def select_square(self, square):
        # square is (row, col)
        board_arr = self.board.get_board()
        row, col = square
        piece = None
        try:
            piece = board_arr[row][col]
        except Exception:
            piece = None

        if piece and getattr(piece, 'color', None) == getattr(self.board, 'current_player', None):
            self.selected_piece_square = square
            # We don't have a unified legal_moves API for the local xiangqi board here;
            # keep valid_moves_for_selected empty to avoid calling unknown methods.
            self.valid_moves_for_selected = []
        else:
            self.reset_selection()

    def reset_selection(self):
        self.selected_piece_square = None
        self.valid_moves_for_selected = []

    def draw(self):
        self.screen.fill((30, 30, 30))
        self.draw_board()
        self.draw_panel()
        # If game over, draw an overlay showing winner/message
        if self.game_over_message:
            self.draw_end_overlay()
        pygame.display.flip()

    def draw_end_overlay(self):
        # Semi-transparent overlay
        w, h = self.screen.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        # Big message
        msg = self.game_over_message
        # Determine short winner text (Red/Black)
        winner = None
        if msg.lower().startswith('red') or 'red' in msg.lower():
            winner = 'Red'
            color = (200, 30, 30)
        elif msg.lower().startswith('black') or 'black' in msg.lower():
            winner = 'Black'
            color = (30, 30, 200)
        else:
            color = (255, 255, 255)

        # Draw overlay then texts
        self.screen.blit(overlay, (0, 0))
        title = f"{winner} Wins!" if winner else "Game Over"
        try:
            draw_text(title, self.font_large, color, self.screen, w // 2, h // 2 - 20)
            draw_text(msg, self.font_small, (220, 220, 220), self.screen, w // 2, h // 2 + 30)
            draw_text("Returning to menu shortly...", self.font_small, (180, 180, 180), self.screen, w // 2, h // 2 + 70)
        except Exception:
            pass

    def draw_board(self):
        # Draw board background
        self.screen.blit(self.board_image, self.board_rect)

        # Highlight last move (stored as ((r1,c1),(r2,c2)))
        if self.last_move and isinstance(self.last_move, tuple) and len(self.last_move) == 2:
            s = pygame.Surface((self.SQUARE_SIZE, self.SQUARE_SIZE), pygame.SRCALPHA)
            s.fill((255, 204, 102, 128))
            try:
                (fr, fc), (tr, tc) = self.last_move
                from_pos = (fc * self.SQUARE_SIZE, fr * self.SQUARE_SIZE)
                to_pos = (tc * self.SQUARE_SIZE, tr * self.SQUARE_SIZE)
                self.screen.blit(s, from_pos)
                self.screen.blit(s, to_pos)
            except Exception:
                pass

        # Highlight selected square
        if self.selected_piece_square is not None:
            row, col = self.selected_piece_square
            center_x = col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
            center_y = row * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
            pygame.draw.circle(self.screen, (255, 255, 0, 100), (center_x, center_y), self.SQUARE_SIZE // 2, 4)

        # Draw pieces from board.get_board()
        board_arr = self.board.get_board()
        # Chinese glyphs mapping (black, red) order to match xiangqi.print_board
        PIECE_GLYPHS = {
            'Chariot': ('楚', '車'),
            'Horse': ('馬', '马'),
            'Elephant': ('相', '象'),
            'Advisor': ('士', '仕'),
            'General': ('將', '帥'),
            'Cannon': ('砲', '炮'),
            'Soldier': ('卒', '兵')
        }

        for r in range(len(board_arr)):
            for c in range(len(board_arr[r])):
                piece = board_arr[r][c]
                if not piece:
                    continue

                # compute center once
                center_x = c * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
                center_y = r * self.SQUARE_SIZE + self.SQUARE_SIZE // 2

                # attempt to draw image first using loaded asset keys (color name, class name)
                try:
                    color_name = 'red' if getattr(piece, 'color', '').lower().startswith('r') or getattr(piece, 'color', '') == 'red' else 'black'
                    cls_name = getattr(piece, 'name', '')
                    img = self.piece_images.get((color_name, cls_name))
                    if img:
                        self.screen.blit(img, img.get_rect(center=(center_x, center_y)))
                        continue
                except Exception:
                    pass

                # Fallback: draw Chinese glyph using font
                try:
                    glyphs = PIECE_GLYPHS.get(getattr(piece, 'name', ''), ('?', '?'))
                    glyph = glyphs[0] if getattr(piece, 'color', '') == 'black' else glyphs[1]
                    # choose font size based on square size
                    font_sz = max(18, self.SQUARE_SIZE - 10)
                    font = pygame.font.SysFont('SimSun', font_sz)
                    text_surf = font.render(glyph, True, (0, 0, 0) if getattr(piece, 'color', '') == 'black' else (200, 20, 20))
                    self.screen.blit(text_surf, text_surf.get_rect(center=(center_x, center_y)))
                except Exception:
                    # final fallback: draw small colored rect
                    s = pygame.Surface((self.SQUARE_SIZE - 12, self.SQUARE_SIZE - 12))
                    s.fill((180, 50, 50) if getattr(piece, 'color', '') == 'red' else (50, 50, 180))
                    self.screen.blit(s, (c * self.SQUARE_SIZE + 6, r * self.SQUARE_SIZE + 6))

    def draw_panel(self):
        pygame.draw.rect(self.screen, (50, 50, 60), self.panel_rect)
        ai_name = f"AI ({self.difficulty.capitalize()})"
        # Colors for active player
        turn = getattr(self.board, 'current_player', None)
        red_active = (255, 255, 0) if turn == 'red' else (255, 255, 255)
        black_active = (255, 255, 0) if turn == 'black' else (255, 255, 255)

        if self.play_mode == 'pvp':
            draw_text(ai_name, self.font_small, black_active, self.screen, 640, 90)
            draw_text("You (Red)", self.font_small, red_active, self.screen, 640, 500)
        elif self.play_mode == 'ava':
            draw_text(f"Black {ai_name}", self.font_small, black_active, self.screen, 640, 90)
            draw_text(f"Red {ai_name}", self.font_small, red_active, self.screen, 640, 500)

        # Show whose turn
        if not self.game_over_message:
            turn_text = "Red's Turn" if turn == 'red' else "Black's Turn"
            draw_text(turn_text, self.font_small, (220, 220, 220), self.screen, 640, 250)

        # Show last move in simple coordinate string
        if self.last_move and isinstance(self.last_move, tuple) and len(self.last_move) == 2:
            try:
                (fr, fc), (tr, tc) = self.last_move
                move_text = f"Last: {fr},{fc} → {tr},{tc}"
            except Exception:
                move_text = "Last: -"
            draw_text(move_text, self.font_info, (180, 180, 180), self.screen, 640, 280)

        # Show clocks
        red_min = int(self.time_left['red'] // 60)
        red_sec = int(self.time_left['red'] % 60)
        black_min = int(self.time_left['black'] // 60)
        black_sec = int(self.time_left['black'] % 60)
        draw_text(f"Red: {red_min:02d}:{red_sec:02d}", self.font_small, red_active, self.screen, 640, 340)
        draw_text(f"Black: {black_min:02d}:{black_sec:02d}", self.font_small, black_active, self.screen, 640, 370)

        if self.ai_is_thinking:
            draw_text("Thinking...", self.font_small, (255,165,0), self.screen, 640, 200)
        if self.game_over_message:
            draw_text(self.game_over_message, self.font_large, (255,0,0), self.screen, 640, 320)