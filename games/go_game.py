import pygame
import time
import os
import copy
from engines.go_engine import EasyAgent, MediumAgent, HardAgent

def draw_text(text, font, color, surface, x, y, center=True):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect(center=(x, y)) if center else textobj.get_rect(topleft=(x, y))
    surface.blit(textobj, textrect)

class GoGame:
    def __init__(self, screen, difficulty, play_mode):
        self.screen = screen
        self.difficulty = difficulty
        self.play_mode = play_mode
        self.size = 9
        self.board = [[None for _ in range(self.size)] for _ in range(self.size)]
        self.turn = 'black'
        self.last_move = None
        
        self.history = []
        self.passes = 0
        self.black_captures = 0
        self.white_captures = 0
        self.running = True
        self.clock = pygame.time.Clock()

        self.black_player = None
        self.white_player = None
        if self.play_mode == 'pvp':
            self.white_player = self._create_agent(difficulty)
        elif self.play_mode == 'ava':
            self.black_player = self._create_agent(difficulty)
            self.white_player = self._create_agent(difficulty)

        self.BOARD_OFFSET = 25
        self.GRID_SIZE = 50
        self.panel_rect = pygame.Rect(self.size * self.GRID_SIZE, 0, 200, self.size * self.GRID_SIZE + 50)
        self.ai_is_thinking = False
        self.ai_move_time = 0
        self.game_over_message = ""
        self.font_large = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 20)
        self.font_info = pygame.font.SysFont("Arial", 18)
    
    def _create_agent(self, difficulty):
        if difficulty == 'easy': 
            return EasyAgent()
        elif difficulty == 'medium': 
            return MediumAgent()
        elif difficulty == 'hard': 
            return HardAgent()
        return EasyAgent()

    def run(self):
        while self.running:
            self.clock.tick(30)
            self.handle_events()

            if not self.game_over_message:
                is_ai_turn = (self.play_mode == 'pvp' and self.turn == 'white') or (self.play_mode == 'ava')
                if is_ai_turn:
                    if not self.ai_is_thinking:
                        self.ai_is_thinking = True
                        self.ai_move_time = time.time() + 0.5
                    if time.time() >= self.ai_move_time:
                        agent = self.white_player if self.turn == 'white' else self.black_player
                        if agent: self.execute_ai_move(agent)
                        self.ai_is_thinking = False
            self.draw()

        if self.black_player: self.black_player.save_progress()
        if self.white_player: self.white_player.save_progress()

    def execute_ai_move(self, agent):
        old_board_list = copy.deepcopy(self.board)
        move = agent.choose_move(self)
        self.last_move = move
        
        if move == "pass":
            self.passes += 1
            if self.passes >= 2: self.end_game()
        else:
            row, col = move
            self.place_stone(row, col)
            self.passes = 0
            
        agent.learn_from_move(old_board_list, self.board, self.turn, move)
        self.switch_turn()
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            is_player_turn = self.play_mode == 'pvp' and self.turn == 'black'
            if is_player_turn and not self.game_over_message:
                if event.type == pygame.MOUSEBUTTONDOWN and not self.panel_rect.collidepoint(event.pos):
                    self.handle_player_click(event.pos)
    
    def handle_player_click(self, pos):
        x, y = pos
        row = round((y - self.BOARD_OFFSET) / self.GRID_SIZE)
        col = round((x - self.BOARD_OFFSET) / self.GRID_SIZE)
        if 0 <= row < self.size and 0 <= col < self.size:
            if self.place_stone(row, col):
                self.last_move = (row, col)
                self.passes = 0
                self.switch_turn()

    def get_valid_moves(self):
        moves = []
        for r in range(self.size):
            for c in range(self.size):
                if self.is_valid(r, c): moves.append((r, c))
        moves.append("pass")
        return moves
    def is_valid(self, row, col):
        if self.board[row][col] is not None: return False
        temp_board = copy.deepcopy(self.board)
        temp_board[row][col] = self.turn
        if self.count_liberties(row, col, temp_board) == 0:
            opponent_color = 'white' if self.turn == 'black' else 'black'
            captured = False
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.size and 0 <= nc < self.size and temp_board[nr][nc] == opponent_color:
                    if self.count_liberties(nr, nc, temp_board) == 0:
                        captured = True; break
            if not captured: return False
        if str(temp_board) in self.history: return False
        return True
    def place_stone(self, row, col):
        if not self.is_valid(row, col): return False
        old_board = copy.deepcopy(self.board)
        self.board[row][col] = self.turn
        captured_stones = self.remove_captured_stones(row, col)
        if self.turn == 'black': self.black_captures += captured_stones
        else: self.white_captures += captured_stones
        self.history.append(str(old_board))
        return True
    def remove_captured_stones(self, row, col):
        count = 0
        opponent = 'white' if self.turn == 'black' else 'black'
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.size and 0 <= nc < self.size and self.board[nr][nc] == opponent:
                if self.count_liberties(nr, nc, self.board) == 0:
                    group = self.get_group(nr, nc, self.board)
                    count += len(group)
                    for r, c in group: self.board[r][c] = None
        return count
    def count_liberties(self, row, col, board):
        group = self.get_group(row, col, board)
        liberties = set()
        for r, c in group:
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.size and 0 <= nc < self.size and board[nr][nc] is None:
                    liberties.add((nr, nc))
        return len(liberties)
    def get_group(self, row, col, board):
        color = board[row][col]
        if color is None: return []
        q, visited, group = [(row, col)], set([(row, col)]), []
        while q:
            r, c = q.pop(0)
            group.append((r, c))
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.size and 0 <= nc < self.size and (nr, nc) not in visited and board[nr][nc] == color:
                    visited.add((nr, nc)); q.append((nr, nc))
        return group
    def switch_turn(self):
        self.turn = 'white' if self.turn == 'black' else 'black'
    def end_game(self): self.game_over_message = "Game Over (2 passes)"
    def draw(self):
        self.screen.fill((210, 180, 140))
        self.draw_board()
        self.draw_panel()
        pygame.display.flip()

    def draw_board(self):
        for i in range(self.size):
            pygame.draw.line(self.screen, (0,0,0), (self.BOARD_OFFSET + i * self.GRID_SIZE, self.BOARD_OFFSET), (self.BOARD_OFFSET + i * self.GRID_SIZE, self.BOARD_OFFSET + (self.size - 1) * self.GRID_SIZE))
            pygame.draw.line(self.screen, (0,0,0), (self.BOARD_OFFSET, self.BOARD_OFFSET + i * self.GRID_SIZE), (self.BOARD_OFFSET + (self.size - 1) * self.GRID_SIZE, self.BOARD_OFFSET + i * self.GRID_SIZE))
        
        if self.last_move and self.last_move != "pass":
            row, col = self.last_move
            center_x = self.BOARD_OFFSET + col * self.GRID_SIZE
            center_y = self.BOARD_OFFSET + row * self.GRID_SIZE
            pygame.draw.circle(self.screen, (255, 100, 100), (center_x, center_y), self.GRID_SIZE // 4)

        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] is not None:
                    color = (0,0,0) if self.board[r][c] == 'black' else (255,255,255)
                    pygame.draw.circle(self.screen, color, (self.BOARD_OFFSET + c * self.GRID_SIZE, self.BOARD_OFFSET + r * self.GRID_SIZE), self.GRID_SIZE // 2 - 2)
    
    def draw_panel(self):
        pygame.draw.rect(self.screen, (50, 50, 60), self.panel_rect)
        ai_name = f"AI ({self.difficulty.capitalize()})"
        
        black_color = (255, 255, 0) if self.turn == 'black' else (255, 255, 255)
        white_color = (255, 255, 0) if self.turn == 'white' else (255, 255, 255)

        if self.play_mode == 'pvp':
            draw_text("You (Black)", self.font_small, black_color, self.screen, 600, 50)
            draw_text(f"Captures: {self.black_captures}", self.font_info, black_color, self.screen, 600, 80)
            draw_text(ai_name, self.font_small, white_color, self.screen, 600, 350)
            draw_text(f"Captures: {self.white_captures}", self.font_info, white_color, self.screen, 600, 380)
        elif self.play_mode == 'ava':
            draw_text(f"Black {ai_name}", self.font_small, black_color, self.screen, 600, 50)
            draw_text(f"Captures: {self.black_captures}", self.font_info, black_color, self.screen, 600, 80)
            draw_text(f"White {ai_name}", self.font_small, white_color, self.screen, 600, 350)
            draw_text(f"Captures: {self.white_captures}", self.font_info, white_color, self.screen, 600, 380)

        if not self.game_over_message:
            turn_text = "Black's Turn" if self.turn == 'black' else "White's Turn"
            draw_text(turn_text, self.font_small, (220, 220, 220), self.screen, 600, 210)
        if self.last_move:
            move_text = f"Last: {self.last_move}"
            draw_text(move_text, self.font_info, (180, 180, 180), self.screen, 600, 240)

        if self.ai_is_thinking: draw_text("Thinking...", self.font_small, (255,165,0), self.screen, 600, 150)
        if self.game_over_message: draw_text(self.game_over_message, self.font_large, (255,0,0), self.screen, 600, 280)