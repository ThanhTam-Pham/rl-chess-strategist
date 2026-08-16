# file: rl_agents/q_learning.py
import numpy as np
import random
import json
import os

class QLearningAgent:
    def __init__(self, actions, alpha=0.1, gamma=0.9, epsilon=0.2):
        self.q_table = {}
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon

    def get_state_key(self, state):
        # Chuyển đổi state (ví dụ: list của list) thành một string
        return str(state)

    def choose_action(self, state, valid_moves):
        state_key = self.get_state_key(state)
        
        # Thăm dò (exploration) hoặc nếu state chưa có trong Q-table
        if random.uniform(0, 1) < self.epsilon or state_key not in self.q_table:
            return random.choice(valid_moves)
        
        # Khai thác (exploitation)
        q_values = self.q_table[state_key]
        
        # Chỉ xem xét các nước đi hợp lệ
        valid_q_values = {move: q_values.get(move, 0) for move in valid_moves}
        if not valid_q_values:
            return random.choice(valid_moves) # Dự phòng nếu không có q-value nào

        max_q = max(valid_q_values.values())
        best_moves = [move for move, q in valid_q_values.items() if q == max_q]
        return random.choice(best_moves) # Chọn ngẫu nhiên nếu có nhiều nước tốt nhất

    def update(self, state, action, reward, next_state, next_valid_moves):
        state_key = self.get_state_key(state)
        next_key = self.get_state_key(next_state)

        # Đảm bảo các state đều có trong q_table
        if state_key not in self.q_table:
            self.q_table[state_key] = {}
        if next_key not in self.q_table:
            self.q_table[next_key] = {}

        current_q = self.q_table[state_key].get(action, 0)
        
        max_next_q = 0
        if next_valid_moves:
            next_q_values = self.q_table[next_key]
            # Lấy Q-value của các nước đi hợp lệ ở trạng thái tiếp theo
            valid_next_q = [next_q_values.get(move, 0) for move in next_valid_moves]
            if valid_next_q:
                max_next_q = max(valid_next_q)

        # Công thức cập nhật Q-learning
        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state_key][action] = new_q

    def save_q_table(self, file_path):
        # Tạo thư mục nếu nó chưa tồn tại
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        try:
            with open(file_path, 'w') as f:
                json.dump(self.q_table, f)
            # Đã sửa: Tiếng Việt không dấu
            print(f"Q-table da duoc luu vao {file_path}")
        except Exception as e:
            print(f"Loi khi luu Q-table: {e}")

    def load_q_table(self, file_path):
        if not os.path.exists(file_path):
            # Đã sửa: Tiếng Việt không dấu
            print(f"Khong tim thay file Q-table tai {file_path}. Bat dau voi bang moi.")
            return
        try:
            with open(file_path, 'r') as f:
                self.q_table = json.load(f)
            # Đã sửa: Tiếng Việt không dấu
            print(f"Q-table da duoc tai tu {file_path}")
        except (json.JSONDecodeError, IOError) as e:
            # Đã sửa: Tiếng Việt không dấu
            print(f"Loi khi tai Q-table tu {file_path}: {e}. Bat dau voi bang moi.")
            self.q_table = {}