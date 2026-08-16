import random
from rl_agents.q_learning import QLearningAgent
from rl_agents.reward_logic import get_go_reward
import copy

class BaseAgent:
    def choose_move(self, board_instance):
        raise NotImplementedError
    def learn_from_move(self, old_board_list, new_board_list, turn, move):
        pass
    def save_progress(self):
        pass

class EasyAgent(BaseAgent):
    def choose_move(self, board_instance):
        valid_moves = board_instance.get_valid_moves()
        # Loại bỏ "pass" để agent cố gắng đi nếu có thể
        possible_placements = [m for m in valid_moves if m != "pass"]
        if not possible_placements:
            return "pass"
        return random.choice(possible_placements)

class QLearningGoAgent(BaseAgent):
    """
    Lớp cơ sở cho các Agent Q-Learning (Medium và Hard).
    """
    def __init__(self, q_table_path, epsilon=0.1):
        self.q_table_path = q_table_path
        self.agent = QLearningAgent(actions=[])
        self.agent.load_q_table(self.q_table_path)
        self.agent.epsilon = epsilon

    def get_state_key(self, board_list, turn):
        board_tuple = tuple(map(tuple, board_list))
        
        return str((board_tuple, turn))

    def choose_move(self, board_instance):
        valid_moves = board_instance.get_valid_moves()
        if not valid_moves or (len(valid_moves) == 1 and valid_moves[0] == "pass"):
            return "pass"

        valid_move_strs = [str(move) for move in valid_moves]
        state_key = self.get_state_key(board_instance.board, board_instance.turn)
        
        chosen_move_str = self.agent.choose_action(state_key, valid_move_strs)
        

        return eval(chosen_move_str) if chosen_move_str != "pass" else "pass"

    def learn_from_move(self, old_board_list, new_board_list, turn, move):
        state_key = self.get_state_key(old_board_list, turn)
        
        next_turn = 'white' if turn == 'black' else 'black'
        next_state_key = self.get_state_key(new_board_list, next_turn)
        
        action_str = str(move)
        reward = get_go_reward(old_board_list, new_board_list, turn)
        

        from games.go_game import GoGame
        temp_game = GoGame(None, 'easy', 'ava') 
        temp_game.board = new_board_list
        temp_game.turn = next_turn
        next_valid_moves_raw = temp_game.get_valid_moves()
        next_valid_moves = [str(m) for m in next_valid_moves_raw]
            
        self.agent.update(state_key, action_str, reward, next_state_key, next_valid_moves)

    def save_progress(self):
        self.agent.save_q_table(self.q_table_path)

class MediumAgent(QLearningGoAgent):
    def __init__(self, q_table_path="data/go_q_table_medium.json"):
        super().__init__(q_table_path, epsilon=0.15) 

class HardAgent(QLearningGoAgent):
    def __init__(self, q_table_path="data/go_q_table_hard.json"):
        super().__init__(q_table_path, epsilon=0.05) 