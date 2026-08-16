import chess
import chess.engine
import random
import os
from rl_agents.q_learning import QLearningAgent
from rl_agents.reward_logic import get_chess_reward

STOCKFISH_PATH = "engines/stockfish/stockfish-windows-x86-64-avx2.exe"

class BaseAgent:
    def choose_move(self, board):
        raise NotImplementedError
    def learn_from_move(self, old_board, move, new_board):
        pass
    def save_progress(self):
        pass

class EasyAgent(BaseAgent):
    """Agent đơn giản nhưng không hoàn toàn random."""
    def choose_move(self, board):
        legal_moves = list(board.legal_moves)
        if not legal_moves: return None

        capture_moves = []
        check_moves = []
        for move in legal_moves:
            temp_board = board.copy()
            temp_board.push(move)
            if board.is_capture(move):
                capture_moves.append(move)
            elif temp_board.is_check():
                check_moves.append(move)

        if capture_moves:
            return random.choice(capture_moves)
        elif check_moves:
            return random.choice(check_moves)
        else:
            return random.choice(legal_moves)


class MediumAgent(BaseAgent):
    """Agent Q-learning, có tăng cường chiến thuật chiếu/bắt quân."""
    def __init__(self, q_table_path="data/chess_q_table.json"):
        self.q_table_path = q_table_path
        self.agent = QLearningAgent(actions=[])
        self.agent.load_q_table(self.q_table_path)

    def get_board_state_key(self, board):
        return " ".join(board.fen().split(" ")[:3])

    def choose_move(self, board):
        legal_moves = list(board.legal_moves)
        if not legal_moves: return None
        valid_move_strs = [move.uci() for move in legal_moves]
        state_key = self.get_board_state_key(board)

        chosen_move_str = self.agent.choose_action(state_key, valid_move_strs)
        chosen_move = chess.Move.from_uci(chosen_move_str)

        capture_moves = []
        check_moves = []
        for move in legal_moves:
            temp_board = board.copy()
            temp_board.push(move)
            if board.is_capture(move):
                capture_moves.append(move)
            elif temp_board.is_check():
                check_moves.append(move)

        if capture_moves and random.random() < 0.4:
            return random.choice(capture_moves)
        if check_moves and random.random() < 0.3:
            return random.choice(check_moves)

        return chosen_move

    def learn_from_move(self, old_board, move, new_board):
        state_key = self.get_board_state_key(old_board)
        next_state_key = self.get_board_state_key(new_board)
        action_str = move.uci()
        reward = get_chess_reward(old_board, move)
        next_valid_moves = [m.uci() for m in new_board.legal_moves]
        self.agent.update(state_key, action_str, reward, next_state_key, next_valid_moves)

    def save_progress(self):
        self.agent.save_q_table(self.q_table_path)


class HardAgent(BaseAgent):
    """Stockfish hỗ trợ cả giới hạn ELO và full-power."""
    def __init__(self, elo=None, depth=25, thinking_time=1.5):
        self.engine = None
        self.depth = depth
        self.thinking_time = thinking_time
        self.elo = elo
        if not os.path.exists(STOCKFISH_PATH):
            print("="*50)
            print(f"LỖI: Không tìm thấy Stockfish tại '{STOCKFISH_PATH}'")
            print("Chế độ 'Hard' sẽ chơi ngẫu nhiên. Vui lòng cập nhật đường dẫn.")
            print("="*50)
        else:
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

                if elo is None or elo >= 3500:
                    # Bật full sức mạnh
                    self.engine.configure({
                        "UCI_LimitStrength": False,
                        "Skill Level": 20
                    })
                    print("HardAgent: Đang chạy ở chế độ FULL sức mạnh (vô hạn ELO)")
                else:
                    # Giới hạn theo ELO
                    self.engine.configure({
                        "UCI_LimitStrength": True,
                        "UCI_Elo": elo
                    })
                    print(f"HardAgent: Đang giới hạn ELO = {elo}")

            except Exception as e:
                print(f"Lỗi khi khởi tạo Stockfish: {e}")
                self.engine = None

    def choose_move(self, board):
        if not self.engine:
            return EasyAgent().choose_move(board)
        try:
            result = self.engine.play(
                board,
                chess.engine.Limit(depth=self.depth, time=self.thinking_time)
            )
            return result.move
        except Exception as e:
            print(f"Lỗi khi Stockfish chọn nước đi: {e}")
            return EasyAgent().choose_move(board)

    def __del__(self):
        if self.engine:
            self.engine.quit()