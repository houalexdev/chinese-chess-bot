#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
中国象棋Bot - 适用于Botzone平台
实现：Zobrist哈希，完整走法生成，Alpha-Beta+PVS，置换表，静态搜索，空着剪枝，
     迭代加深，时间管理，长将禁手，开局库，位置评估。
"""

import sys
import json
import time
import random

# ================= 全局常量 =================
TIME_LIMIT_SOFT = 3.0   # 软时限，停止加深
TIME_LIMIT_HARD = 4.0   # 硬时限，立即返回
MAX_DEPTH = 64

# 子力基础价值
VALUE = {
    'K': 10000, 'k': 10000,
    'R': 900, 'r': 900,
    'C': 450, 'c': 450,
    'N': 400, 'n': 400,
    'B': 200, 'b': 200,
    'A': 200, 'a': 200,
    'P': 100, 'p': 100,
}

# ================= Zobrist 哈希 =================
ZOBRIST_TABLE = {}
ZOBRIST_SIDE_RED = 0
ZOBRIST_SIDE_BLACK = 0

def init_zobrist():
    global ZOBRIST_TABLE, ZOBRIST_SIDE_RED, ZOBRIST_SIDE_BLACK
    random.seed(20230513)
    pieces = ['R','N','B','A','K','C','P','r','n','b','a','k','c','p']
    ZOBRIST_TABLE = {
        p: [[random.getrandbits(64) for _ in range(9)] for __ in range(10)]
        for p in pieces
    }
    ZOBRIST_SIDE_RED = random.getrandbits(64)
    ZOBRIST_SIDE_BLACK = random.getrandbits(64)

ZOBRIST_SIDE = (ZOBRIST_SIDE_RED, ZOBRIST_SIDE_BLACK)

# 在模块加载时初始化
init_zobrist()

# ================= 位置评估表（红方，10行×9列）=================
# 黑方将使用对称行：9 - y
POS_RED = {
    'R': [  # 车
        [-20,-10,  0,  0,  0,  0,  0,-10,-20],
        [-15,  0,  0,  0,  0,  0,  0,  0,-15],
        [-10,  0,  5,  5,  5,  5,  5,  0,-10],
        [ -5,  0, 10, 10, 10, 10, 10,  0, -5],
        [  0,  0, 10, 15, 15, 15, 10,  0,  0],
        [  5, 10, 15, 20, 20, 20, 15, 10,  5],
        [ 10, 15, 20, 25, 25, 25, 20, 15, 10],
        [ 10, 15, 20, 25, 30, 25, 20, 15, 10],
        [  5, 10, 15, 20, 20, 20, 15, 10,  5],
        [  0,  0,  5, 10, 10, 10,  5,  0,  0]
    ],
    'N': [  # 马
        [-20,-20,-10,-10,  0,-10,-10,-20,-20],
        [-15,-10,  0,  5,  5,  5,  0,-10,-15],
        [-10,  0, 10, 10, 10, 10, 10,  0,-10],
        [ -5,  5, 15, 20, 20, 20, 15,  5, -5],
        [  0,  5, 15, 25, 25, 25, 15,  5,  0],
        [  5, 10, 20, 30, 30, 30, 20, 10,  5],
        [  5, 15, 20, 25, 25, 25, 20, 15,  5],
        [  0,  5, 10, 15, 15, 15, 10,  5,  0],
        [-10,  0,  5,  5,  5,  5,  5,  0,-10],
        [-20,-10,  0,  0,  0,  0,  0,-10,-20]
    ],
    'B': [  # 相
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0, 10,  0,  0,  0, 10,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0, 20,  0,  0,  0, 20,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0]
    ],
    'A': [  # 士
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0, 20,  0, 20,  0,  0,  0],
        [  0,  0,  0,  0, 30,  0,  0,  0,  0],
        [  0,  0,  0, 20,  0, 20,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0]
    ],
    'K': [  # 帅/将
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,-10,-10,-10,  0,  0,  0],
        [  0,  0,  0,-10,-20,-10,  0,  0,  0],
        [  0,  0,  0,-10,-10,-10,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0]
    ],
    'C': [  # 炮
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  5, 10, 10,-10,-10,-10, 10, 10,  5],
        [  5, 10, 10, 15, 15, 15, 10, 10,  5],
        [  0,  5, 10, 20, 20, 20, 10,  5,  0],
        [  0,  5, 10, 20, 25, 20, 10,  5,  0],
        [  0,  5, 10, 20, 20, 20, 10,  5,  0],
        [  0,  5, 10, 15, 15, 15, 10,  5,  0],
        [  0,  0,  5, 10, 10, 10,  5,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0]
    ],
    'P': [  # 兵/卒
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [ 10, 10, 10, 20, 20, 20, 10, 10, 10],
        [ 20, 20, 30, 40, 40, 40, 30, 20, 20],
        [ 30, 30, 40, 50, 50, 50, 40, 30, 30],
        [ 40, 40, 50, 60, 60, 60, 50, 40, 40],
        [ 50, 50, 60, 70, 70, 70, 60, 50, 50],
        [  0,  0,  0,  0,  0,  0,  0,  0,  0]
    ]
}

def get_position_value(piece, x, y):
    """返回棋子位置附加分"""
    if piece.isupper():  # 红方
        if piece == 'R': return POS_RED['R'][y][x]
        if piece == 'N': return POS_RED['N'][y][x]
        if piece == 'B': return POS_RED['B'][y][x]
        if piece == 'A': return POS_RED['A'][y][x]
        if piece == 'K': return POS_RED['K'][y][x]
        if piece == 'C': return POS_RED['C'][y][x]
        if piece == 'P': return POS_RED['P'][y][x]
    else:                  # 黑方，对称行
        if piece == 'r': return POS_RED['R'][9-y][x]
        if piece == 'n': return POS_RED['N'][9-y][x]
        if piece == 'b': return POS_RED['B'][9-y][x]
        if piece == 'a': return POS_RED['A'][9-y][x]
        if piece == 'k': return POS_RED['K'][9-y][x]
        if piece == 'c': return POS_RED['C'][9-y][x]
        if piece == 'p': return POS_RED['P'][9-y][x]
    return 0

# ================= 棋盘与走法 =================
def pos_to_str(x, y):
    return chr(ord('a') + x) + str(y)

def str_to_pos(s):
    return ord(s[0]) - ord('a'), int(s[1])

class Board:
    def __init__(self):
        self.board = [['.' for _ in range(9)] for _ in range(10)]
        self.turn = 0   # 0红 1黑
        self.zobrist_hash = 0
        self.red_king_pos = None
        self.black_king_pos = None
        self.setup_initial()
        self.init_hash()
        self.find_kings()

    def setup_initial(self):
        # 红方底线
        self.board[0] = list("RNBAKABNR")
        # 红炮
        self.board[2][1] = 'C'
        self.board[2][7] = 'C'
        # 红兵
        for x in [0,2,4,6,8]:
            self.board[3][x] = 'P'
        # 黑方
        self.board[9] = list("rnbakabnr")
        self.board[7][1] = 'c'
        self.board[7][7] = 'c'
        for x in [0,2,4,6,8]:
            self.board[6][x] = 'p'

    def init_hash(self):
        h = 0
        for y in range(10):
            for x in range(9):
                p = self.board[y][x]
                if p != '.':
                    h ^= ZOBRIST_TABLE[p][y][x]
        h ^= ZOBRIST_SIDE[0]  # 红方先手
        self.zobrist_hash = h

    def find_kings(self):
        for y in range(10):
            for x in range(9):
                p = self.board[y][x]
                if p == 'K':
                    self.red_king_pos = (x, y)
                elif p == 'k':
                    self.black_king_pos = (x, y)

    def piece_attacks(self, piece, x, y, tx, ty):
        """判断棋子piece能否从(x,y)攻击到(tx,ty)"""
        dx, dy = tx - x, ty - y
        p = piece
        if p in 'Rr':
            if dx == 0:
                step = 1 if dy > 0 else -1
                for yi in range(y+step, ty, step):
                    if self.board[yi][x] != '.':
                        return False
                return True
            if dy == 0:
                step = 1 if dx > 0 else -1
                for xi in range(x+step, tx, step):
                    if self.board[y][xi] != '.':
                        return False
                return True
            return False
        elif p in 'Nn':
            if not ((abs(dx)==2 and abs(dy)==1) or (abs(dx)==1 and abs(dy)==2)):
                return False
            if abs(dx)==2:
                leg_x, leg_y = x + dx//2, y
            else:
                leg_x, leg_y = x, y + dy//2
            return self.board[leg_y][leg_x] == '.'
        elif p in 'Bb':
            if abs(dx)!=2 or abs(dy)!=2:
                return False
            if (p == 'B' and ty > 4) or (p == 'b' and ty < 5):
                return False
            eye_x, eye_y = x + dx//2, y + dy//2
            return self.board[eye_y][eye_x] == '.'
        elif p in 'Aa':
            if abs(dx)!=1 or abs(dy)!=1:
                return False
            if p == 'A':
                if not (3<=tx<=5 and 0<=ty<=2): return False
            else:
                if not (3<=tx<=5 and 7<=ty<=9): return False
            return True
        elif p in 'Kk':
            if abs(dx)+abs(dy) != 1:
                return False
            if p == 'K':
                if not (3<=tx<=5 and 0<=ty<=2): return False
            else:
                if not (3<=tx<=5 and 7<=ty<=9): return False
            return True
        elif p in 'Cc':
            if dx == 0:
                step = 1 if dy > 0 else -1
                cnt = 0
                for yi in range(y+step, ty, step):
                    if self.board[yi][x] != '.':
                        cnt += 1
                return cnt == 1
            if dy == 0:
                step = 1 if dx > 0 else -1
                cnt = 0
                for xi in range(x+step, tx, step):
                    if self.board[y][xi] != '.':
                        cnt += 1
                return cnt == 1
            return False
        elif p in 'Pp':
            if p == 'P':
                if dy == 1 and dx == 0:
                    return True
                if y >= 5 and dy == 0 and abs(dx) == 1:
                    return True
                return False
            else:
                if dy == -1 and dx == 0:
                    return True
                if y <= 4 and dy == 0 and abs(dx) == 1:
                    return True
                return False
        return False

    def is_check(self, side):
        """检查side方是否被将军"""
        king_pos = self.red_king_pos if side == 0 else self.black_king_pos
        if king_pos is None:
            return False
        kx, ky = king_pos
        opponent = 1 - side
        for y in range(10):
            for x in range(9):
                p = self.board[y][x]
                if p == '.':
                    continue
                if (opponent == 0 and p.isupper()) or (opponent == 1 and p.islower()):
                    if self.piece_attacks(p, x, y, kx, ky):
                        return True
        # 白脸将（将帅对面）
        opp_king = self.red_king_pos if opponent == 0 else self.black_king_pos
        if opp_king and kx == opp_king[0]:
            min_y = min(ky, opp_king[1]) + 1
            max_y = max(ky, opp_king[1])
            blocked = any(self.board[yi][kx] != '.' for yi in range(min_y, max_y))
            if not blocked:
                return True
        return False

    def make_move(self, x1, y1, x2, y2):
        piece = self.board[y1][x1]
        captured = self.board[y2][x2]
        old_hash = self.zobrist_hash
        old_red_king = self.red_king_pos
        old_black_king = self.black_king_pos
        old_turn = self.turn

        # 更新棋盘
        self.board[y1][x1] = '.'
        self.board[y2][x2] = piece

        # 更新哈希
        h = old_hash
        h ^= ZOBRIST_TABLE[piece][y1][x1]
        if captured != '.':
            h ^= ZOBRIST_TABLE[captured][y2][x2]
        h ^= ZOBRIST_TABLE[piece][y2][x2]
        h ^= ZOBRIST_SIDE[self.turn] ^ ZOBRIST_SIDE[1 - self.turn]
        self.zobrist_hash = h
        self.turn = 1 - self.turn

        # 更新王位置
        if piece == 'K':
            self.red_king_pos = (x2, y2)
        elif piece == 'k':
            self.black_king_pos = (x2, y2)
        if captured == 'K':
            self.red_king_pos = None
        elif captured == 'k':
            self.black_king_pos = None

        return (piece, captured, x1, y1, x2, y2, old_hash, old_red_king, old_black_king, old_turn)

    def unmake_move(self, move_info):
        piece, captured, x1, y1, x2, y2, old_hash, old_red_king, old_black_king, old_turn = move_info
        self.board[y1][x1] = piece
        self.board[y2][x2] = captured
        self.zobrist_hash = old_hash
        self.red_king_pos = old_red_king
        self.black_king_pos = old_black_king
        self.turn = old_turn

# ================= 走法生成 =================
def generate_pseudo_moves(board, side):
    """生成所有伪合法走法（未过滤己方被将）"""
    moves = []
    for y in range(10):
        for x in range(9):
            p = board.board[y][x]
            if p == '.':
                continue
            if (side == 0 and not p.isupper()) or (side == 1 and not p.islower()):
                continue

            if p in 'Rr':  # 车
                for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                    tx, ty = x+dx, y+dy
                    while 0 <= tx < 9 and 0 <= ty < 10:
                        target = board.board[ty][tx]
                        if target == '.':
                            moves.append((x, y, tx, ty))
                        else:
                            if (side == 0 and target.islower()) or (side == 1 and target.isupper()):
                                moves.append((x, y, tx, ty))
                            break
                        tx += dx; ty += dy
            elif p in 'Nn':  # 马
                for dx, dy in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                    tx, ty = x+dx, y+dy
                    if 0 <= tx < 9 and 0 <= ty < 10:
                        if abs(dx) == 2:
                            leg_x, leg_y = x + dx//2, y
                        else:
                            leg_x, leg_y = x, y + dy//2
                        if board.board[leg_y][leg_x] == '.':
                            target = board.board[ty][tx]
                            if target == '.' or (side == 0 and target.islower()) or (side == 1 and target.isupper()):
                                moves.append((x, y, tx, ty))
            elif p in 'Bb':  # 象/相
                for dx, dy in [(-2,-2),(-2,2),(2,-2),(2,2)]:
                    tx, ty = x+dx, y+dy
                    if 0 <= tx < 9 and 0 <= ty < 10:
                        if (p == 'B' and ty > 4) or (p == 'b' and ty < 5):
                            continue
                        eye_x, eye_y = x + dx//2, y + dy//2
                        if board.board[eye_y][eye_x] == '.':
                            target = board.board[ty][tx]
                            if target == '.' or (side == 0 and target.islower()) or (side == 1 and target.isupper()):
                                moves.append((x, y, tx, ty))
            elif p in 'Aa':  # 士
                for dx, dy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                    tx, ty = x+dx, y+dy
                    if 0 <= tx < 9 and 0 <= ty < 10:
                        if p == 'A':
                            if not (3 <= tx <= 5 and 0 <= ty <= 2): continue
                        else:
                            if not (3 <= tx <= 5 and 7 <= ty <= 9): continue
                        target = board.board[ty][tx]
                        if target == '.' or (side == 0 and target.islower()) or (side == 1 and target.isupper()):
                            moves.append((x, y, tx, ty))
            elif p in 'Kk':  # 将/帅
                for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                    tx, ty = x+dx, y+dy
                    if 0 <= tx < 9 and 0 <= ty < 10:
                        if p == 'K':
                            if not (3 <= tx <= 5 and 0 <= ty <= 2): continue
                        else:
                            if not (3 <= tx <= 5 and 7 <= ty <= 9): continue
                        target = board.board[ty][tx]
                        if target == '.' or (side == 0 and target.islower()) or (side == 1 and target.isupper()):
                            moves.append((x, y, tx, ty))
            elif p in 'Cc':  # 炮
                for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                    tx, ty = x+dx, y+dy
                    while 0 <= tx < 9 and 0 <= ty < 10:
                        target = board.board[ty][tx]
                        if target == '.':
                            moves.append((x, y, tx, ty))
                        else:
                            # 找炮架后的目标
                            tx2, ty2 = tx+dx, ty+dy
                            while 0 <= tx2 < 9 and 0 <= ty2 < 10:
                                target2 = board.board[ty2][tx2]
                                if target2 != '.':
                                    if (side == 0 and target2.islower()) or (side == 1 and target2.isupper()):
                                        moves.append((x, y, tx2, ty2))
                                    break
                                tx2 += dx; ty2 += dy
                            break
                        tx += dx; ty += dy
            elif p in 'Pp':  # 兵/卒
                if p == 'P':
                    ty = y + 1
                    if ty <= 9:
                        target = board.board[ty][x]
                        if target == '.' or target.islower():
                            moves.append((x, y, x, ty))
                    if y >= 5:
                        for tx in [x-1, x+1]:
                            if 0 <= tx < 9:
                                target = board.board[y][tx]
                                if target == '.' or target.islower():
                                    moves.append((x, y, tx, y))
                else:
                    ty = y - 1
                    if ty >= 0:
                        target = board.board[ty][x]
                        if target == '.' or target.isupper():
                            moves.append((x, y, x, ty))
                    if y <= 4:
                        for tx in [x-1, x+1]:
                            if 0 <= tx < 9:
                                target = board.board[y][tx]
                                if target == '.' or target.isupper():
                                    moves.append((x, y, tx, y))
    return moves

def generate_legal_moves(board, side, history_hashes=None):
    """合法走法：过滤掉走后被将，以及可选的重复禁手"""
    pseudo = generate_pseudo_moves(board, side)
    legal = []
    for move in pseudo:
        x1, y1, x2, y2 = move
        info = board.make_move(x1, y1, x2, y2)
        if not board.is_check(side):
            if history_hashes is not None:
                # 长将/长捉：若走成历史出现2次以上，禁止
                if history_hashes.count(board.zobrist_hash) >= 2:
                    board.unmake_move(info)
                    continue
            legal.append(move)
        board.unmake_move(info)
    return legal

# ================= 评估函数 =================
def evaluate(board, side):
    """静态评估，从side视角返回分数"""
    score = 0
    for y in range(10):
        for x in range(9):
            p = board.board[y][x]
            if p == '.':
                continue
            val = VALUE.get(p, 0)
            pos = get_position_value(p, x, y)
            if p.isupper():
                score += (val + pos) if side == 0 else -(val + pos)
            else:
                score += (val + pos) if side == 1 else -(val + pos)
    if board.is_check(1 - side):
        score += 50
    if board.is_check(side):
        score -= 50
    return score

# ================= 走法排序 =================
# 全局历史表、杀手走法表
history_table = {}
killer_moves = [[None, None] for _ in range(100)]

def order_moves(moves, board, side, hash_move, killer1, killer2):
    def move_score(m):
        x1, y1, x2, y2 = m[:4]
        if hash_move and m == hash_move:
            return 1000000
        if killer1 and m == killer1:
            return 900000
        if killer2 and m == killer2:
            return 800000
        captured = board.board[y2][x2]
        attacker = board.board[y1][x1]
        if captured != '.':
            victim_val = VALUE.get(captured, 0)
            attacker_val = VALUE.get(attacker, 0)
            return 100000 + victim_val * 10 - attacker_val
        key = (x1, y1, x2, y2)
        return history_table.get(key, 0)
    moves.sort(key=move_score, reverse=True)
    return moves

def update_killer(move, ply):
    if move is None:
        return
    if killer_moves[ply][0] != move:
        killer_moves[ply][1] = killer_moves[ply][0]
        killer_moves[ply][0] = move

def update_history(move, depth):
    key = (move[0], move[1], move[2], move[3])
    history_table[key] = history_table.get(key, 0) + depth * depth

# ================= 搜索引擎 =================
TRANSPOSITION = {}  # 置换表
nodes_searched = 0
search_aborted = False
best_move_sofar = None
start_time = 0

class TimeoutError(Exception):
    pass

def generate_capture_moves(board, side):
    pseudo = generate_pseudo_moves(board, side)
    return [m for m in pseudo
            if board.board[m[3]][m[2]] != '.' 
            and ((side==0 and board.board[m[3]][m[2]].islower()) or (side==1 and board.board[m[3]][m[2]].isupper()))]

def quiescence(board, side, alpha, beta, ply):
    global nodes_searched
    nodes_searched += 1
    stand_pat = evaluate(board, side)
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat
    moves = generate_capture_moves(board, side)
    if not moves:
        return alpha
    moves = order_moves(moves, board, side, None, None, None)
    for move in moves:
        x1, y1, x2, y2 = move[:4]
        info = board.make_move(x1, y1, x2, y2)
        if board.is_check(side):
            board.unmake_move(info)
            continue
        value = -quiescence(board, 1-side, -beta, -alpha, ply+1)
        board.unmake_move(info)
        if value >= beta:
            return beta
        if value > alpha:
            alpha = value
    return alpha

def has_non_pawn_material(side, board):
    for y in range(10):
        for x in range(9):
            p = board.board[y][x]
            if p == '.':
                continue
            if side == 0 and p.isupper() and p not in ('K', 'P'):
                return True
            if side == 1 and p.islower() and p not in ('k', 'p'):
                return True
    return False

def alpha_beta(board, side, alpha, beta, depth, ply, allow_null):
    global nodes_searched, search_aborted, TRANSPOSITION, start_time
    if nodes_searched % 1000 == 0 and time.time() - start_time > TIME_LIMIT_HARD:
        search_aborted = True
        raise TimeoutError()
    nodes_searched += 1

    # 置换表探査
    hash_key = board.zobrist_hash
    entry = TRANSPOSITION.get(hash_key)
    if entry and entry[0] >= depth:
        flag, val, hash_move = entry[1], entry[2], entry[3]
        if flag == 0:
            return val
        if flag == 1 and val <= alpha:
            return alpha
        if flag == 2 and val >= beta:
            return beta

    in_check = board.is_check(side)
    if in_check:
        depth = max(depth, 1)

    if depth <= 0:
        return quiescence(board, side, alpha, beta, ply)

    # 空着剪枝
    if allow_null and depth >= 2 and not in_check and has_non_pawn_material(side, board):
        old_turn, old_hash = board.turn, board.zobrist_hash
        board.turn = 1 - board.turn
        board.zobrist_hash ^= ZOBRIST_SIDE[old_turn] ^ ZOBRIST_SIDE[board.turn]
        val = -alpha_beta(board, 1-side, -beta, -beta+1, depth-3, ply+1, False)
        board.turn, board.zobrist_hash = old_turn, old_hash
        if val >= beta:
            return beta

    moves = generate_legal_moves(board, side, [])
    if not moves:
        return -999999 + ply if in_check else 0

    hash_move = entry[3] if entry else None
    killer1, killer2 = killer_moves[ply][0], killer_moves[ply][1]
    moves = order_moves(moves, board, side, hash_move, killer1, killer2)

    best_value = -999999
    best_move_local = None
    alpha_orig = alpha

    for i, move in enumerate(moves):
        x1, y1, x2, y2 = move[:4]
        info = board.make_move(x1, y1, x2, y2)
        if i == 0:
            value = -alpha_beta(board, 1-side, -beta, -alpha, depth-1, ply+1, True)
        else:
            value = -alpha_beta(board, 1-side, -alpha-1, -alpha, depth-1, ply+1, True)
            if alpha < value < beta:
                value = -alpha_beta(board, 1-side, -beta, -alpha, depth-1, ply+1, True)
        board.unmake_move(info)

        if value > best_value:
            best_value = value
            best_move_local = move
            if value > alpha:
                alpha = value
            if value >= beta:
                update_killer(move, ply)
                update_history(move, depth)
                break
        if search_aborted:
            raise TimeoutError()

    if best_value <= alpha_orig:
        flag = 2
    elif best_value >= beta:
        flag = 1
    else:
        flag = 0
    TRANSPOSITION[hash_key] = (depth, flag, best_value, best_move_local)
    return best_value

def alpha_beta_root(board, side, max_depth, history_hashes):
    global best_move_sofar, search_aborted
    best_value = -999999
    moves = generate_legal_moves(board, side, history_hashes)
    if not moves:
        return -999999

    hash_move = None
    entry = TRANSPOSITION.get(board.zobrist_hash)
    if entry and entry[3]:
        hash_move = entry[3]

    moves = order_moves(moves, board, side, hash_move,
                        killer_moves[0][0], killer_moves[0][1])
    alpha = -999999
    beta = 999999

    for i, move in enumerate(moves):
        x1, y1, x2, y2 = move[:4]
        info = board.make_move(x1, y1, x2, y2)
        if i == 0:
            value = -alpha_beta(board, 1-side, -beta, -alpha, max_depth-1, 1, False)
        else:
            value = -alpha_beta(board, 1-side, -alpha-1, -alpha, max_depth-1, 1, False)
            if alpha < value < beta:
                value = -alpha_beta(board, 1-side, -beta, -alpha, max_depth-1, 1, False)
        board.unmake_move(info)
        if value > alpha:
            alpha = value
            best_move_sofar = move
            if value >= beta:
                update_killer(move, 0)
                break
        if (i & 31) == 0 and time.time() - start_time > TIME_LIMIT_HARD:
            search_aborted = True
            break
    return alpha

def iterative_deepening(board, side, history_hashes):
    global best_move_sofar, start_time, search_aborted
    best_move_sofar = None
    search_aborted = False
    start_time = time.time()
    depth = 1
    try:
        while True:
            alpha_beta_root(board, side, depth, history_hashes)
            if search_aborted:
                break
            if time.time() - start_time > TIME_LIMIT_SOFT and best_move_sofar is not None:
                break
            depth += 1
            if depth > MAX_DEPTH:
                break
    except TimeoutError:
        pass
    return best_move_sofar

# ================= 开局库 =================
def get_move_sequence(requests, responses):
    seq = []
    for i in range(len(responses)):
        req = requests[i]
        if req['source'] != '-1':
            seq.append((req['source'], req['target']))
        resp = responses[i]
        if resp['source'] != '-1':
            seq.append((resp['source'], resp['target']))
    last = requests[-1]
    if last['source'] != '-1':
        seq.append((last['source'], last['target']))
    return tuple(seq)

# 至少10条变例（坐标均为Botzone格式）
OPENING_BOOK = {
    (): ("b2", "e2"),                                 # 红当头炮
    (("b2","e2"),): ("b8","e8"),                     # 黑顺炮
    (("b2","e2"),("b8","e8")): ("b0","c2"),          # 红马二进三
    (("b2","e2"),("b8","e8"),("b0","c2")): ("b9","c7"), # 黑马8进7
    (("b2","e2"),("b8","e8"),("b0","c2"),("b9","c7")): ("h0","g2"), # 红马八进七
    (("b2","e2"),): ("b8","d8"),                     # 黑炮8平6
    (("b2","e2"),("b8","d8")): ("e2","e4"),
    (): ("c0","e2"),                                 # 飞相局
    (("c0","e2"),): ("b8","e8"),
    (("c0","e2"),("b8","e8")): ("b2","e2"),
}

def get_opening_move(board, my_color, history_hashes, requests, responses):
    seq = get_move_sequence(requests, responses)
    if seq in OPENING_BOOK:
        src, tgt = OPENING_BOOK[seq]
        x1, y1 = str_to_pos(src)
        x2, y2 = str_to_pos(tgt)
        legal = generate_legal_moves(board, my_color, history_hashes)
        for m in legal:
            if m[0] == x1 and m[1] == y1 and m[2] == x2 and m[3] == y2:
                return m
    return None

# ================= 主程序 =================
def main():
    global TRANSPOSITION, killer_moves, history_table, best_move_sofar
    try:
        input_str = sys.stdin.readline().strip()
        data = json.loads(input_str)
        requests = data.get('requests', [])
        responses = data.get('responses', [])

        my_color = 0 if requests[0]['source'] == '-1' else 1
        board = Board()
        history_hashes = [board.zobrist_hash]

        turn_id = len(responses)
        for i in range(turn_id):
            req = requests[i]
            if req['source'] != '-1':
                x1, y1 = str_to_pos(req['source'])
                x2, y2 = str_to_pos(req['target'])
                board.make_move(x1, y1, x2, y2)
                history_hashes.append(board.zobrist_hash)
            resp = responses[i]
            if resp['source'] != '-1':
                x1, y1 = str_to_pos(resp['source'])
                x2, y2 = str_to_pos(resp['target'])
                board.make_move(x1, y1, x2, y2)
                history_hashes.append(board.zobrist_hash)
        current_req = requests[turn_id]
        if current_req['source'] != '-1':
            x1, y1 = str_to_pos(current_req['source'])
            x2, y2 = str_to_pos(current_req['target'])
            board.make_move(x1, y1, x2, y2)
            history_hashes.append(board.zobrist_hash)

        # 重置搜索引擎全局状态
        TRANSPOSITION.clear()
        killer_moves = [[None, None] for _ in range(100)]
        history_table.clear()
        best_move_sofar = None

        best_move = get_opening_move(board, my_color, history_hashes, requests, responses)
        if best_move is None:
            best_move = iterative_deepening(board, my_color, history_hashes)

        if best_move is None:
            output = {"response": {"source": "-1", "target": "-1"}}
        else:
            sx, sy = best_move[0], best_move[1]
            tx, ty = best_move[2], best_move[3]
            output = {"response": {"source": pos_to_str(sx, sy), "target": pos_to_str(tx, ty)}}
        sys.stdout.write(json.dumps(output) + '\n')
    except Exception:
        out = {"response": {"source": "-1", "target": "-1"}}
        sys.stdout.write(json.dumps(out) + '\n')

if __name__ == '__main__':
    main()