import pygame
import chess
import time
import os
from engines.chess_engine import EasyAgent, MediumAgent, HardAgent

def draw_text(text, font, color, surface, x, y, center=True):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect(center=(x, y)) if center else textobj.get_rect(topleft=(x, y))
    surface.blit(textobj, textrect)

class ChessGame:
    def __init__(self, screen, difficulty, play_mode, elo=None):
        self.screen, self.difficulty, self.play_mode, self.elo = screen, difficulty, play_mode, elo
        self.board = chess.Board()
        self.clock = pygame.time.Clock()
        self.running = True
        self.last_move = None
        
        self.white_player = None
        self.black_player = None
        if self.play_mode == 'pvp':
            self.player_color, self.ai_color = chess.WHITE, chess.BLACK
            self.black_player = self._create_agent(difficulty, elo)
        elif self.play_mode == 'ava':
            self.player_color, self.ai_color = None, None
            self.white_player = self._create_agent(difficulty, elo)
            self.black_player = self._create_agent(difficulty, elo)

        self.board_rect = pygame.Rect(0, 0, 600, 600)
        self.panel_rect = pygame.Rect(600, 0, 200, 600)
        self.BOARD_OFFSET = 33 
        self.EFFECTIVE_BOARD_SIZE = self.board_rect.width - (self.BOARD_OFFSET * 2)
        self.SQUARE_SIZE = self.EFFECTIVE_BOARD_SIZE / 8
        self.piece_images = {}
        self.board_image = None
        self.load_assets()
        self.selected_piece_square = None
        self.valid_moves_for_selected = []
        self.ai_is_thinking = False
        self.ai_move_time = 0
        self.game_over_message = ""
        self.player_time, self.ai_time = 300, 300
        self.font_large = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 20)
        self.font_info = pygame.font.SysFont("Arial", 18)
    
    def _create_agent(self, difficulty, elo):
        if difficulty == 'easy': return EasyAgent()
        elif difficulty == 'medium': return MediumAgent()
        elif difficulty == 'hard': return HardAgent(elo=elo if elo else 3000)
        return EasyAgent()

    def load_assets(self):
        asset_path = os.path.join("assets", "chess")
        try:
            board_img_path = os.path.join(asset_path, "board.png")
            self.board_image = pygame.transform.scale(pygame.image.load(board_img_path), (self.board_rect.width, self.board_rect.height))
            piece_size = (int(self.SQUARE_SIZE * 0.9), int(self.SQUARE_SIZE * 0.9))
            pieces = {'P': 'pw', 'N': 'nw', 'B': 'bw', 'R': 'rw', 'Q': 'qw', 'K': 'kw', 'p': 'pb', 'n': 'nb', 'b': 'bb', 'r': 'rb', 'q': 'qb', 'k': 'kb'}
            for symbol, filename in pieces.items():
                path = os.path.join(asset_path, f"{filename}.png")
                self.piece_images[symbol] = pygame.transform.smoothscale(pygame.image.load(path).convert_alpha(), piece_size)
        except pygame.error as e:
            print(f"Lỗi khi tải tài nguyên: {e}"); self.running = False

    def run(self):
        while self.running:
            delta_time = self.clock.tick(30) / 1000.0
            self.handle_events()
            self.update_time(delta_time)
            if not self.game_over_message: self.check_game_over()

            if not self.game_over_message:
                current_turn = self.board.turn
                is_ai_turn = (self.play_mode == 'pvp' and current_turn == self.ai_color) or (self.play_mode == 'ava')
                if is_ai_turn:
                    if not self.ai_is_thinking:
                        self.ai_is_thinking = True
                        self.ai_move_time = time.time() + 0.5
                    if time.time() >= self.ai_move_time:
                        current_player = self.black_player if current_turn == chess.BLACK else self.white_player
                        if current_player: self.execute_ai_move(current_player)
                        self.ai_is_thinking = False
            self.draw()
        
        if self.white_player: self.white_player.save_progress()
        if self.black_player: self.black_player.save_progress()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            if self.play_mode == 'pvp' and self.board.turn == self.player_color and not self.game_over_message:
                if event.type == pygame.MOUSEBUTTONDOWN and self.board_rect.collidepoint(event.pos):
                    self.handle_player_click(event.pos)

    def update_time(self, delta):
        if not self.game_over_message:
            if self.board.turn == chess.WHITE: self.player_time -= delta
            else: self.ai_time -= delta

    def check_game_over(self):
        if self.board.is_checkmate():
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            self.game_over_message = f"{winner} Wins!"
        elif self.board.is_stalemate() or self.board.is_insufficient_material() or self.board.is_seventyfive_moves() or self.board.is_fivefold_repetition():
            self.game_over_message = "Draw!"
        elif self.player_time <= 0: self.game_over_message = "Black Won on Time!"
        elif self.ai_time <= 0: self.game_over_message = "White Won on Time!"


    def handle_player_click(self, pos):
        if not (self.BOARD_OFFSET < pos[0] < self.board_rect.width - self.BOARD_OFFSET and self.BOARD_OFFSET < pos[1] < self.board_rect.height - self.BOARD_OFFSET): return
        col = int((pos[0] - self.BOARD_OFFSET) // self.SQUARE_SIZE)
        row = int((pos[1] - self.BOARD_OFFSET) // self.SQUARE_SIZE)
        square = chess.square(col, 7 - row)
        if self.selected_piece_square is not None:
            move = self.get_move(self.selected_piece_square, square)
            if move in self.valid_moves_for_selected:
                self.board.push(move)
                self.last_move = move
                self.reset_selection()
            else: self.select_square(square)
        else: self.select_square(square)

    def select_square(self, square):
        piece = self.board.piece_at(square)
        if piece and piece.color == self.player_color:
            self.selected_piece_square = square; self.update_valid_moves()
        else: self.reset_selection()

    def execute_ai_move(self, agent):
        old_board = self.board.copy()
        move = agent.choose_move(self.board)
        if move:
            self.board.push(move)
            self.last_move = move
            agent.learn_from_move(old_board, move, self.board)
    
    def get_move(self, from_sq, to_sq):
        piece = self.board.piece_at(from_sq)
        if piece and piece.piece_type == chess.PAWN and chess.square_rank(to_sq) in [0, 7]:
            return chess.Move(from_sq, to_sq, promotion=chess.QUEEN)
        return chess.Move(from_sq, to_sq)
    def reset_selection(self): self.selected_piece_square = None; self.valid_moves_for_selected = []
    def update_valid_moves(self):
        self.valid_moves_for_selected = []
        if self.selected_piece_square:
            for move in self.board.legal_moves:
                if move.from_square == self.selected_piece_square: self.valid_moves_for_selected.append(move)
    def draw(self):
        self.screen.fill((30, 30, 30))
        self.draw_board()
        self.draw_panel()
        pygame.display.flip()
    

    def draw_board(self):
        if not self.board_image: return
        self.screen.blit(self.board_image, self.board_rect)

        if self.last_move:
            from_sq = self.last_move.from_square
            to_sq = self.last_move.to_square
            
            from_col = chess.square_file(from_sq)
            from_row = 7 - chess.square_rank(from_sq)
            s = pygame.Surface((self.SQUARE_SIZE, self.SQUARE_SIZE), pygame.SRCALPHA)
            s.fill((255, 204, 102, 128))
            self.screen.blit(s, (self.BOARD_OFFSET + from_col * self.SQUARE_SIZE, self.BOARD_OFFSET + from_row * self.SQUARE_SIZE))
            
            to_col = chess.square_file(to_sq)
            to_row = 7 - chess.square_rank(to_sq)
            self.screen.blit(s, (self.BOARD_OFFSET + to_col * self.SQUARE_SIZE, self.BOARD_OFFSET + to_row * self.SQUARE_SIZE))

        if self.selected_piece_square is not None:
            col = chess.square_file(self.selected_piece_square)
            row = 7 - chess.square_rank(self.selected_piece_square)
            pygame.draw.rect(self.screen, (255, 255, 0, 100), (self.BOARD_OFFSET + col * self.SQUARE_SIZE, self.BOARD_OFFSET + row * self.SQUARE_SIZE, self.SQUARE_SIZE, self.SQUARE_SIZE))
            for move in self.valid_moves_for_selected:
                to_col = chess.square_file(move.to_square)
                to_row = 7 - chess.square_rank(move.to_square)
                center_x = self.BOARD_OFFSET + to_col * self.SQUARE_SIZE + self.SQUARE_SIZE / 2
                center_y = self.BOARD_OFFSET + to_row * self.SQUARE_SIZE + self.SQUARE_SIZE / 2
                pygame.draw.circle(self.screen, (0, 255, 0, 120), (center_x, center_y), self.SQUARE_SIZE / 4)
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                image = self.piece_images[piece.symbol()]
                col = chess.square_file(square)
                row = 7 - chess.square_rank(square)
                square_x = self.BOARD_OFFSET + col * self.SQUARE_SIZE
                square_y = self.BOARD_OFFSET + row * self.SQUARE_SIZE
                self.screen.blit(image, image.get_rect(center=(square_x + self.SQUARE_SIZE / 2, square_y + self.SQUARE_SIZE / 2)))

    def draw_panel(self):
        pygame.draw.rect(self.screen, (50, 50, 60), self.panel_rect)
        
        ai_name, elo_text = "", ""
        if self.difficulty == 'easy': ai_name = "AI (Easy)"
        elif self.difficulty == 'medium': ai_name = "AI (Medium)"
        elif self.difficulty == 'hard': ai_name = "AI (Hard)"; elo_text = f"ELO: {self.elo}"
        white_time_str = f"{int(self.player_time//60):02}:{int(self.player_time%60):02}"
        black_time_str = f"{int(self.ai_time//60):02}:{int(self.ai_time%60):02}"
        white_color = (255, 255, 0) if self.board.turn == chess.WHITE else (255, 255, 255)
        black_color = (255, 255, 0) if self.board.turn == chess.BLACK else (255, 255, 255)

        if self.play_mode == 'pvp':
            draw_text(ai_name, self.font_small, black_color, self.screen, 700, 50)
            draw_text(black_time_str, self.font_large, black_color, self.screen, 700, 90)
            if elo_text: draw_text(elo_text, self.font_small, (180, 180, 180), self.screen, 700, 130)
            draw_text("You", self.font_small, white_color, self.screen, 700, 500)
            draw_text(white_time_str, self.font_large, white_color, self.screen, 700, 540)
        elif self.play_mode == 'ava':
            draw_text(f"Black {ai_name}", self.font_small, black_color, self.screen, 700, 50)
            draw_text(black_time_str, self.font_large, black_color, self.screen, 700, 90)
            if elo_text: draw_text(elo_text, self.font_small, (180, 180, 180), self.screen, 700, 130)
            draw_text(f"White {ai_name}", self.font_small, white_color, self.screen, 700, 500)
            draw_text(white_time_str, self.font_large, white_color, self.screen, 700, 540)
        
        if not self.game_over_message:
            turn_text = "White's Turn" if self.board.turn == chess.WHITE else "Black's Turn"
            draw_text(turn_text, self.font_small, (220, 220, 220), self.screen, 700, 250)
        if self.last_move:
            move_text = f"Last: {self.last_move.uci()}"
            draw_text(move_text, self.font_info, (180, 180, 180), self.screen, 700, 280)
        
        if self.ai_is_thinking: draw_text("Thinking...", self.font_small, (255,165,0), self.screen, 700, 200)
        if self.game_over_message: draw_text(self.game_over_message, self.font_large, (255,0,0), self.screen, 700, 320)