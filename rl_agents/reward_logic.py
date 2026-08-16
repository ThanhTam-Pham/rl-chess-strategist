import chess

# --- Logic phần thưởng cho Cờ Vua (Chess) ---
CHESS_PIECE_VALUES = {
    chess.PAWN: 10,
    chess.KNIGHT: 30,
    chess.BISHOP: 30,
    chess.ROOK: 50,
    chess.QUEEN: 90,
}

def get_chess_reward(board: chess.Board, move: chess.Move):
    reward = -0.1
    if board.is_capture(move):
        # Lấy quân cờ tại ô ĐẾN, nhưng từ bàn cờ TRƯỚC KHI đi
        captured_piece = board.piece_at(move.to_square)
        if captured_piece:
            reward += CHESS_PIECE_VALUES.get(captured_piece.piece_type, 0)
        elif board.is_en_passant(move): # Xử lý bắt Tốt qua đường
            reward += CHESS_PIECE_VALUES[chess.PAWN]
    if move.promotion:
        reward += CHESS_PIECE_VALUES.get(move.promotion, 90)
    
    temp_board = board.copy()
    temp_board.push(move)
    
    if temp_board.is_checkmate():
        reward += 1000
    elif temp_board.is_stalemate() or temp_board.is_insufficient_material():
        reward = 0
    elif temp_board.is_check():
        reward += 5
    return reward

# --- Logic phần thưởng cho Cờ Tướng (Xiangqi) ---
XIANGQI_VALUES = {
    "Soldier": 10,
    "Horse": 30,
    "Elephant": 30,
    "Advisor": 30,
    "Cannon": 40,
    "Chariot": 50,
    "General": 1000
}

def get_xiangqi_reward(board, from_pos, to_pos):
    """Tính toán phần thưởng cho nước đi trong cờ tướng"""
    reward = -0.1  # Chi phí cơ bản cho mỗi nước đi
    
    # Kiểm tra có bắt được quân không
    captured = board.get_board()[to_pos[0]][to_pos[1]]
    if captured:
        reward += XIANGQI_VALUES.get(captured.name, 0)
    
    return reward

# --- Logic phần thưởng cho Cờ Vây (Go) ---
def get_go_reward(old_board, new_board, turn):
    """Tính toán phần thưởng cho nước đi trong cờ vây.

    old_board, new_board are 2D lists (size x size) with values 'black', 'white', or None.
    turn is the player who just moved ('black' or 'white').

    Returned reward is a small negative step cost plus positive reward for capturing
    opponent stones or increasing the mover's stone count.
    """
    # small negative cost per move to discourage useless moves
    reward = -0.1

    def count_stones(board):
        black = 0
        white = 0
        for row in board:
            for cell in row:
                if cell == 'black':
                    black += 1
                elif cell == 'white':
                    white += 1
        return black, white

    try:
        old_black, old_white = count_stones(old_board)
        new_black, new_white = count_stones(new_board)
    except Exception:
        # If board format is unexpected, return small step cost
        return reward

    # reward from change in own stones
    if turn == 'black':
        reward += (new_black - old_black) * 0.5
        # reward for capturing opponent stones (old - new)
        captured = max(0, old_white - new_white)
        reward += captured * 3.0
    else:
        reward += (new_white - old_white) * 0.5
        captured = max(0, old_black - new_black)
        reward += captured * 3.0

    return reward
