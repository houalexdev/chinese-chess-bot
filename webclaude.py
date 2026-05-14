#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国象棋 Botzone Bot
实现完整合法走法生成、Alpha-Beta剪枝、置换表、Zobrist哈希、
迭代加深、PVS、走法排序、静态搜索、空着剪枝、时间管理。
"""

import sys
import json
import random
import time

# ============================================================
# 常量定义
# ============================================================
RED   = 1   # 红方
BLACK = -1  # 黑方

# 棋子类型（正=红方，负=黑方）
EMPTY = 0
R_KING   =  1  # 帅
R_ADVISOR=  2  # 仕
R_BISHOP =  3  # 相
R_KNIGHT =  4  # 馬
R_ROOK   =  5  # 車
R_CANNON =  6  # 炮
R_PAWN   =  7  # 兵
B_KING   = -1  # 将
B_ADVISOR= -2  # 士
B_BISHOP = -3  # 象
B_KNIGHT = -4  # 馬
B_CANNON = -6  # 炮
B_ROOK   = -5  # 車
B_PAWN   = -7  # 卒

# 棋子基础价值（绝对值）
PIECE_VALUE = {
    1: 10000, 2: 200, 3: 200, 4: 400, 5: 900, 6: 450, 7: 100
}

# 列字母映射
COL_MAP = {c: i for i, c in enumerate('abcdefghi')}
COL_REV = 'abcdefghi'

# ============================================================
# 位置加成表（红方视角，y=0为底线）
# 格式：[y][x]，y=0~9，x=0~8
# ============================================================
# 帅（只在九宫内）
POS_KING = [
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
]

# 車位置加成
POS_ROOK = [
    [206,208,207,213,214,213,207,208,206],
    [206,212,209,216,233,216,209,212,206],
    [206,208,207,214,216,214,207,208,206],
    [206,213,213,216,216,216,213,213,206],
    [208,211,211,214,215,214,211,211,208],
    [208,212,212,214,215,214,212,212,208],
    [206,210,209,216,216,216,209,210,206],
    [206,208,207,213,214,213,207,208,206],
    [206,208,207,213,214,213,207,208,206],
    [206,208,207,213,214,213,207,208,206],
]

# 馬位置加成
POS_KNIGHT = [
    [  90,  90,  90,  96,  90,  96,  90,  90,  90],
    [  90,  96,  103, 97,  94,  97,  103, 96,  90],
    [  92,  98,  99,  103, 99,  103, 99,  98,  92],
    [  93,  108, 100, 107, 100, 107, 100, 108, 93],
    [  90,  100, 99,  103, 104, 103, 99,  100, 90],
    [  90,  98,  101, 102, 103, 102, 101, 98,  90],
    [  92,  94,  98,  95,  98,  95,  98,  94,  92],
    [  93,  92,  94,  95,  92,  95,  94,  92,  93],
    [  85,  90,  92,  93,  78,  93,  92,  90,  85],
    [  88,  85,  90,  88,  90,  88,  90,  85,  88],
]

# 炮位置加成
POS_CANNON = [
    [100,100,96, 91, 90, 91, 96, 100,100],
    [98, 98, 96, 92, 89, 92, 96, 98, 98],
    [97, 97, 96, 91, 92, 91, 96, 97, 97],
    [96, 99, 99, 98, 100,98, 99, 99, 96],
    [96, 96, 96, 96, 100,96, 96, 96, 96],
    [95, 96, 99, 96, 100,96, 99, 96, 95],
    [96, 96, 96, 96, 96, 96, 96, 96, 96],
    [97, 96, 100,99, 101,99, 100,96, 97],
    [96, 97, 98, 98, 98, 98, 98, 97, 96],
    [96, 96, 97, 99, 99, 99, 97, 96, 96],
]

# 相位置加成（只在己方区域）
POS_BISHOP = [
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
]
# 相实际在特定格子
BISHOP_POS_BONUS = {
    (0,2):20,(4,2):20,(8,2):20,(2,0):20,(6,0):20,
    (0,4):20,(4,4):20,(8,4):20,(2,4):15,(6,4):15,
    (2,2):15,(6,2):15,
}

# 仕位置加成
POS_ADVISOR = [
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
]
ADVISOR_POS_BONUS = {
    (3,0):10,(5,0):10,(4,1):20,(3,2):10,(5,2):10
}

# 兵位置加成（红方）
POS_PAWN_RED = [
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],  # y=0
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],  # y=1
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],  # y=2
    [ 10,  0, 20,  0, 20,  0, 20,  0, 10],  # y=3（未过河）
    [ 10,  0, 20,  0, 20,  0, 20,  0, 10],  # y=4（未过河）
    [ 30, 35, 50, 65, 70, 65, 50, 35, 30],  # y=5（过河）
    [ 60, 70, 80, 95,100, 95, 80, 70, 60],  # y=6（过河）
    [ 60, 70, 80, 95,100, 95, 80, 70, 60],  # y=7（过河）
    [ 60, 70, 80, 95,100, 95, 80, 70, 60],  # y=8（过河）
    [100,100,110,120,120,120,110,100,100],   # y=9（底线）
]

# ============================================================
# Zobrist 哈希表
# ============================================================
random.seed(42)
# zobrist_table[piece+7][y][x]，piece范围-7~7（+7偏移后0~14）
ZOBRIST_TABLE = [[[random.getrandbits(64) for _ in range(9)] for _ in range(10)] for _ in range(15)]
ZOBRIST_TURN = random.getrandbits(64)  # 轮次哈希

# ============================================================
# 棋盘类
# ============================================================
class Board:
    def __init__(self):
        # board[y][x]，正值=红方，负值=黑方
        self.board = [[EMPTY]*9 for _ in range(10)]
        self.turn = RED   # 当前行棋方
        self.hash = 0
        self.history = {}  # hash->count，用于重复检测
        self._init_board()
        self._compute_hash()

    def _init_board(self):
        """初始化标准开局"""
        b = self.board
        # 红方（y=0~4）
        b[0] = [R_ROOK, R_KNIGHT, R_BISHOP, R_ADVISOR, R_KING, R_ADVISOR, R_BISHOP, R_KNIGHT, R_ROOK]
        b[2][1] = R_CANNON; b[2][7] = R_CANNON
        b[3] = [R_PAWN,0,R_PAWN,0,R_PAWN,0,R_PAWN,0,R_PAWN]
        # 黑方（y=9~5）
        b[9] = [B_ROOK, B_KNIGHT, B_BISHOP, B_ADVISOR, B_KING, B_ADVISOR, B_BISHOP, B_KNIGHT, B_ROOK]
        b[7][1] = B_CANNON; b[7][7] = B_CANNON
        b[6] = [B_PAWN,0,B_PAWN,0,B_PAWN,0,B_PAWN,0,B_PAWN]

    def _compute_hash(self):
        h = 0
        for y in range(10):
            for x in range(9):
                p = self.board[y][x]
                if p != EMPTY:
                    h ^= ZOBRIST_TABLE[p+7][y][x]
        if self.turn == BLACK:
            h ^= ZOBRIST_TURN
        self.hash = h

    def copy(self):
        nb = Board.__new__(Board)
        nb.board = [row[:] for row in self.board]
        nb.turn = self.turn
        nb.hash = self.hash
        nb.history = dict(self.history)
        return nb

    def piece_at(self, x, y):
        return self.board[y][x]

    def make_move(self, move):
        """执行走法，更新哈希，返回被吃棋子"""
        sx, sy, tx, ty = move
        piece = self.board[sy][sx]
        captured = self.board[ty][tx]
        # 更新哈希
        self.hash ^= ZOBRIST_TABLE[piece+7][sy][sx]
        if captured != EMPTY:
            self.hash ^= ZOBRIST_TABLE[captured+7][ty][tx]
        self.hash ^= ZOBRIST_TABLE[piece+7][ty][tx]
        # 移动棋子
        self.board[ty][tx] = piece
        self.board[sy][sx] = EMPTY
        # 切换行棋方
        self.hash ^= ZOBRIST_TURN
        self.turn = -self.turn
        # 记录局面历史
        self.history[self.hash] = self.history.get(self.hash, 0) + 1
        return captured

    def undo_move(self, move, captured):
        sx, sy, tx, ty = move
        piece = self.board[ty][tx]
        # 撤销哈希
        self.hash ^= ZOBRIST_TABLE[piece+7][ty][tx]
        if captured != EMPTY:
            self.hash ^= ZOBRIST_TABLE[captured+7][ty][tx]
        self.hash ^= ZOBRIST_TABLE[piece+7][sy][sx]
        self.hash ^= ZOBRIST_TURN
        # 还原棋子
        self.board[sy][sx] = piece
        self.board[ty][tx] = captured
        self.turn = -self.turn
        # 撤销历史
        if self.hash in self.history:
            self.history[self.hash] -= 1
            if self.history[self.hash] == 0:
                del self.history[self.hash]

    def is_repeated(self):
        return self.history.get(self.hash, 0) >= 3

    def find_king(self, side):
        """找到指定方的将/帅位置"""
        target = R_KING if side == RED else B_KING
        for y in range(10):
            for x in range(9):
                if self.board[y][x] == target:
                    return (x, y)
        return None

    def is_in_check(self, side):
        """判断side方是否被将军"""
        king_pos = self.find_king(side)
        if king_pos is None:
            return True
        kx, ky = king_pos
        opp = -side
        b = self.board

        # 检查對方車攻击
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = kx+dx, ky+dy
            while 0<=nx<9 and 0<=ny<10:
                p = b[ny][nx]
                if p != EMPTY:
                    if p*opp > 0 and abs(p)==R_ROOK:
                        return True
                    break
                nx += dx; ny += dy

        # 检查对方炮攻击
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = kx+dx, ky+dy
            count = 0
            while 0<=nx<9 and 0<=ny<10:
                p = b[ny][nx]
                if p != EMPTY:
                    count += 1
                    if count == 2 and p*opp > 0 and abs(p)==R_CANNON:
                        return True
                    if count >= 2:
                        break
                nx += dx; ny += dy

        # 检查对方馬攻击
        knight_attacks = [
            (1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)
        ]
        leg_block = {
            (1,2):(kx,ky+1),(2,1):(kx+1,ky),(2,-1):(kx+1,ky),
            (1,-2):(kx,ky-1),(-1,-2):(kx,ky-1),(-2,-1):(kx-1,ky),
            (-2,1):(kx-1,ky),(-1,2):(kx,ky+1)
        }
        for ddx, ddy in knight_attacks:
            nx, ny = kx+ddx, ky+ddy
            if 0<=nx<9 and 0<=ny<10:
                p = b[ny][nx]
                if p*opp > 0 and abs(p)==R_KNIGHT:
                    lx, ly = leg_block[(ddx,ddy)]
                    if 0<=lx<9 and 0<=ly<10 and b[ly][lx]==EMPTY:
                        return True

        # 检查对方兵/卒攻击
        if opp == RED:
            # 红兵攻击黑将：红兵朝y+方向走，过河后可横走
            for ddx, ddy in [(0,-1),(-1,0),(1,0)]:  # 从将的角度看红兵在哪
                nx, ny = kx+ddx, ky+ddy
                if 0<=nx<9 and 0<=ny<10:
                    p = b[ny][nx]
                    if p == R_PAWN:
                        # 红兵能攻击到将吗
                        # 红兵在ny,nx，将在ky,kx
                        if ny < 5:  # 未过河，只能前进（y+）
                            if ny+1==ky and nx==kx:
                                return True
                        else:  # 过河后可前进或左右
                            if (ny+1==ky and nx==kx) or (ny==ky and abs(nx-kx)==1):
                                return True
        else:
            # 黑卒攻击红帅
            for ddx, ddy in [(0,1),(1,0),(-1,0)]:
                nx, ny = kx+ddx, ky+ddy
                if 0<=nx<9 and 0<=ny<10:
                    p = b[ny][nx]
                    if p == B_PAWN:
                        if ny >= 5:  # 未过河
                            if ny-1==ky and nx==kx:
                                return True
                        else:
                            if (ny-1==ky and nx==kx) or (ny==ky and abs(nx-kx)==1):
                                return True

        # 检查对方仕/士攻击（不现实，仕不攻击，跳过）
        # 白脸将检测
        if ky is not None:
            opp_king_pos = self.find_king(opp)
            if opp_king_pos is not None:
                okx, oky = opp_king_pos
                if kx == okx:
                    blocked = False
                    miny, maxy = min(ky,oky)+1, max(ky,oky)
                    for cy in range(miny, maxy):
                        if b[cy][kx] != EMPTY:
                            blocked = True; break
                    if not blocked:
                        return True

        return False

    def is_game_over(self):
        """检测将被吃（没有将则游戏结束）"""
        r_king = self.find_king(RED)
        b_king = self.find_king(BLACK)
        if r_king is None:
            return BLACK
        if b_king is None:
            return RED
        return None


# ============================================================
# 走法生成
# ============================================================
def gen_moves(board, side):
    """生成side方所有合法走法（过滤被将状态）"""
    moves = []
    b = board.board
    for sy in range(10):
        for sx in range(9):
            p = b[sy][sx]
            if p == EMPTY or (p > 0) != (side > 0):
                continue
            pt = abs(p)
            if pt == R_ROOK:
                _gen_rook(b, sx, sy, side, moves)
            elif pt == R_KNIGHT:
                _gen_knight(b, sx, sy, side, moves)
            elif pt == R_BISHOP:
                _gen_bishop(b, sx, sy, side, moves)
            elif pt == R_ADVISOR:
                _gen_advisor(b, sx, sy, side, moves)
            elif pt == R_KING:
                _gen_king(b, sx, sy, side, moves)
            elif pt == R_CANNON:
                _gen_cannon(b, sx, sy, side, moves)
            elif pt == R_PAWN:
                _gen_pawn(b, sx, sy, side, moves)

    # 过滤走后己方被将的走法
    legal = []
    for mv in moves:
        cap = board.make_move(mv)
        if not board.is_in_check(side):
            legal.append(mv)
        board.undo_move(mv, cap)
    return legal

def _gen_rook(b, sx, sy, side, moves):
    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx, ny = sx+dx, sy+dy
        while 0<=nx<9 and 0<=ny<10:
            p = b[ny][nx]
            if p == EMPTY:
                moves.append((sx,sy,nx,ny))
            else:
                if (p>0) != (side>0):
                    moves.append((sx,sy,nx,ny))
                break
            nx += dx; ny += dy

def _gen_knight(b, sx, sy, side, moves):
    steps = [(1,2,(0,1)),(2,1,(1,0)),(2,-1,(1,0)),(1,-2,(0,-1)),
             (-1,-2,(0,-1)),(-2,-1,(-1,0)),(-2,1,(-1,0)),(-1,2,(0,1))]
    for ddx, ddy, (lx,ly) in steps:
        bx, by = sx+lx, sy+ly  # 马腿
        if 0<=bx<9 and 0<=by<10 and b[by][bx]==EMPTY:
            nx, ny = sx+ddx, sy+ddy
            if 0<=nx<9 and 0<=ny<10:
                p = b[ny][nx]
                if p==EMPTY or (p>0)!=(side>0):
                    moves.append((sx,sy,nx,ny))

def _gen_bishop(b, sx, sy, side, moves):
    # 红相不过河（y<=4），黑象不过河（y>=5）
    for ddx, ddy in [(2,2),(2,-2),(-2,2),(-2,-2)]:
        # 象眼
        ex, ey = sx+ddx//2, sy+ddy//2
        if not (0<=ex<9 and 0<=ey<10):
            continue
        if b[ey][ex] != EMPTY:
            continue
        nx, ny = sx+ddx, sy+ddy
        if 0<=nx<9 and 0<=ny<10:
            if side==RED and ny>4: continue
            if side==BLACK and ny<5: continue
            p = b[ny][nx]
            if p==EMPTY or (p>0)!=(side>0):
                moves.append((sx,sy,nx,ny))

def _gen_advisor(b, sx, sy, side, moves):
    # 九宫：红方x=3~5,y=0~2；黑方x=3~5,y=7~9
    for ddx, ddy in [(1,1),(1,-1),(-1,1),(-1,-1)]:
        nx, ny = sx+ddx, sy+ddy
        if 3<=nx<=5:
            if side==RED and 0<=ny<=2:
                p = b[ny][nx]
                if p==EMPTY or (p>0)!=(side>0):
                    moves.append((sx,sy,nx,ny))
            elif side==BLACK and 7<=ny<=9:
                p = b[ny][nx]
                if p==EMPTY or (p>0)!=(side>0):
                    moves.append((sx,sy,nx,ny))

def _gen_king(b, sx, sy, side, moves):
    for ddx, ddy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx, ny = sx+ddx, sy+ddy
        if 3<=nx<=5:
            if side==RED and 0<=ny<=2:
                p = b[ny][nx]
                if p==EMPTY or (p>0)!=(side>0):
                    moves.append((sx,sy,nx,ny))
            elif side==BLACK and 7<=ny<=9:
                p = b[ny][nx]
                if p==EMPTY or (p>0)!=(side>0):
                    moves.append((sx,sy,nx,ny))

def _gen_cannon(b, sx, sy, side, moves):
    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx, ny = sx+dx, sy+dy
        # 不吃子滑动
        while 0<=nx<9 and 0<=ny<10:
            p = b[ny][nx]
            if p != EMPTY:
                break
            moves.append((sx,sy,nx,ny))
            nx += dx; ny += dy
        # 跳过一个棋子后吃子
        if 0<=nx<9 and 0<=ny<10:
            nx += dx; ny += dy
            while 0<=nx<9 and 0<=ny<10:
                p = b[ny][nx]
                if p != EMPTY:
                    if (p>0) != (side>0):
                        moves.append((sx,sy,nx,ny))
                    break
                nx += dx; ny += dy

def _gen_pawn(b, sx, sy, side, moves):
    if side == RED:
        crossed = sy >= 5
        dirs = [(0,1)]
        if crossed:
            dirs += [(1,0),(-1,0)]
    else:
        crossed = sy <= 4
        dirs = [(0,-1)]
        if crossed:
            dirs += [(1,0),(-1,0)]
    for ddx, ddy in dirs:
        nx, ny = sx+ddx, sy+ddy
        if 0<=nx<9 and 0<=ny<10:
            p = b[ny][nx]
            if p==EMPTY or (p>0)!=(side>0):
                moves.append((sx,sy,nx,ny))


# ============================================================
# 评估函数
# ============================================================
def evaluate(board):
    """从当前行棋方视角评估局面"""
    score = 0
    b = board.board
    side = board.turn
    for y in range(10):
        for x in range(9):
            p = b[y][x]
            if p == EMPTY:
                continue
            pt = abs(p)
            base = PIECE_VALUE[pt]
            # 位置加成（红方用原坐标，黑方翻转y轴）
            pos_bonus = _pos_bonus(pt, x, y, p > 0)
            val = base + pos_bonus
            if (p > 0) == (side > 0):
                score += val
            else:
                score -= val
    return score

def _pos_bonus(pt, x, y, is_red):
    """获取位置加成，is_red表示是否红方"""
    if is_red:
        ry = y  # 红方：y=0底线
    else:
        ry = 9 - y  # 黑方翻转

    if pt == R_ROOK:
        return POS_ROOK[ry][x] - 206
    elif pt == R_KNIGHT:
        return POS_KNIGHT[ry][x] - 90
    elif pt == R_CANNON:
        return POS_CANNON[ry][x] - 96
    elif pt == R_PAWN:
        return POS_PAWN_RED[ry][x]
    elif pt == R_BISHOP:
        return BISHOP_POS_BONUS.get((x, ry), 0)
    elif pt == R_ADVISOR:
        return ADVISOR_POS_BONUS.get((x, ry), 0)
    elif pt == R_KING:
        return 0
    return 0


# ============================================================
# 置换表
# ============================================================
TT_SIZE = 1 << 20  # 1M 条目
TT_EXACT = 0
TT_LOWER = 1  # Alpha (下界)
TT_UPPER = 2  # Beta  (上界)

class TranspositionTable:
    def __init__(self):
        self.table = {}

    def store(self, h, depth, score, flag, best_move):
        key = h % TT_SIZE
        self.table[key] = (h, depth, score, flag, best_move)

    def lookup(self, h, depth, alpha, beta):
        key = h % TT_SIZE
        entry = self.table.get(key)
        if entry is None:
            return None, None
        eh, ed, score, flag, best_move = entry
        if eh != h:
            return None, None
        if ed >= depth:
            if flag == TT_EXACT:
                return score, best_move
            elif flag == TT_LOWER and score >= beta:
                return score, best_move
            elif flag == TT_UPPER and score <= alpha:
                return score, best_move
        return None, best_move  # 只返回最优走法用于排序

    def get_best_move(self, h):
        key = h % TT_SIZE
        entry = self.table.get(key)
        if entry and entry[0] == h:
            return entry[4]
        return None


TT = TranspositionTable()

# ============================================================
# 走法排序
# ============================================================
KILLER_MOVES = [[None, None] for _ in range(64)]  # killer[depth][0/1]
HISTORY = {}  # (sx,sy,tx,ty) -> score

def score_move(move, board, depth, tt_best):
    sx, sy, tx, ty = move
    cap = board.board[ty][tx]
    # TT最优走法最高优先级
    if move == tt_best:
        return 30000
    # 吃子走法 MVV-LVA
    if cap != EMPTY:
        victim = PIECE_VALUE[abs(cap)]
        attacker = PIECE_VALUE[abs(board.board[sy][sx])]
        return 20000 + victim * 10 - attacker
    # Killer Move
    if depth < 64:
        if move == KILLER_MOVES[depth][0]:
            return 9000
        if move == KILLER_MOVES[depth][1]:
            return 8000
    # 历史启发
    return HISTORY.get(move, 0)

def update_killer(move, depth):
    if depth < 64:
        if move != KILLER_MOVES[depth][0]:
            KILLER_MOVES[depth][1] = KILLER_MOVES[depth][0]
            KILLER_MOVES[depth][0] = move

def update_history(move, depth):
    HISTORY[move] = HISTORY.get(move, 0) + depth * depth

def sort_moves(moves, board, depth, tt_best):
    return sorted(moves, key=lambda m: -score_move(m, board, depth, tt_best))


# ============================================================
# 搜索引擎
# ============================================================
INF = 1000000
START_TIME = 0
TIME_LIMIT = 4.0
SOFT_LIMIT = 3.0
STOP_SEARCH = False

def time_up():
    return (time.time() - START_TIME) >= TIME_LIMIT

def quiescence(board, alpha, beta, depth=0):
    """静态搜索：只搜索吃子走法"""
    global STOP_SEARCH
    if STOP_SEARCH or time_up():
        STOP_SEARCH = True
        return evaluate(board)

    stand_pat = evaluate(board)
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    if depth > 8:  # 限制静态搜索深度
        return alpha

    # 只生成吃子走法
    moves = gen_moves(board, board.turn)
    cap_moves = [m for m in moves if board.board[m[3]][m[2]] != EMPTY]
    cap_moves = sort_moves(cap_moves, board, 0, None)

    for move in cap_moves:
        cap = board.make_move(move)
        score = -quiescence(board, -beta, -alpha, depth+1)
        board.undo_move(move, cap)
        if STOP_SEARCH:
            return alpha
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha

def alphabeta(board, depth, alpha, beta, null_move_ok=True):
    """带置换表的Alpha-Beta + PVS + 空着剪枝"""
    global STOP_SEARCH

    if STOP_SEARCH or time_up():
        STOP_SEARCH = True
        return evaluate(board)

    # 置换表查找
    h = board.hash
    tt_score, tt_best = TT.lookup(h, depth, alpha, beta)
    if tt_score is not None:
        return tt_score

    # 游戏结束检测
    game_over = board.is_game_over()
    if game_over is not None:
        if game_over == board.turn:
            return INF - 1
        else:
            return -(INF - 1)

    if depth == 0:
        return quiescence(board, alpha, beta)

    in_check = board.is_in_check(board.turn)

    # 空着剪枝（非将军局面，非残局）
    if (null_move_ok and not in_check and depth >= 3):
        # 临时切换行棋方
        board.turn = -board.turn
        board.hash ^= ZOBRIST_TURN
        score = -alphabeta(board, depth-3, -beta, -beta+1, False)
        board.turn = -board.turn
        board.hash ^= ZOBRIST_TURN
        if score >= beta:
            return beta

    # 将军延伸
    ext = 1 if in_check else 0

    moves = gen_moves(board, board.turn)
    if not moves:
        if in_check:
            return -(INF - 1)  # 被将死
        return 0  # 困毙（平局）

    moves = sort_moves(moves, board, depth, tt_best)

    best_score = -INF
    best_move = None
    orig_alpha = alpha
    flag = TT_UPPER

    for i, move in enumerate(moves):
        # 重复局面过滤
        cap = board.make_move(move)
        if board.is_repeated():
            board.undo_move(move, cap)
            continue

        if i == 0:
            score = -alphabeta(board, depth-1+ext, -beta, -alpha)
        else:
            # PVS零窗口搜索
            score = -alphabeta(board, depth-1+ext, -alpha-1, -alpha)
            if alpha < score < beta:
                score = -alphabeta(board, depth-1+ext, -beta, -score)

        board.undo_move(move, cap)

        if STOP_SEARCH:
            return best_score if best_score > -INF else alpha

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score
            flag = TT_EXACT

        if alpha >= beta:
            flag = TT_LOWER
            update_killer(move, depth)
            update_history(move, depth)
            break

    if best_move:
        TT.store(h, depth, best_score, flag, best_move)

    return best_score if best_score > -INF else orig_alpha

def iterative_deepening(board, max_depth=10):
    """迭代加深搜索，返回最优走法"""
    global START_TIME, STOP_SEARCH

    START_TIME = time.time()
    STOP_SEARCH = False

    # 先获取所有合法走法
    moves = gen_moves(board, board.turn)
    if not moves:
        return None

    best_move = moves[0]

    for depth in range(1, max_depth+1):
        if time.time() - START_TIME >= SOFT_LIMIT:
            break

        STOP_SEARCH = False
        alpha, beta = -INF, INF
        cur_best = None
        cur_score = -INF

        tt_best = TT.get_best_move(board.hash)
        sorted_moves = sort_moves(moves, board, depth, tt_best)

        for i, move in enumerate(sorted_moves):
            if time_up():
                STOP_SEARCH = True
                break

            cap = board.make_move(move)
            if board.is_repeated():
                board.undo_move(move, cap)
                continue

            if i == 0:
                score = -alphabeta(board, depth-1, -beta, -alpha)
            else:
                score = -alphabeta(board, depth-1, -alpha-1, -alpha)
                if alpha < score < beta and not STOP_SEARCH:
                    score = -alphabeta(board, depth-1, -beta, -score)

            board.undo_move(move, cap)

            if STOP_SEARCH:
                break

            if score > cur_score:
                cur_score = score
                cur_best = move
                if score > alpha:
                    alpha = score

        if cur_best and not STOP_SEARCH:
            best_move = cur_best
        elif cur_best and cur_score > -INF:
            best_move = cur_best

    return best_move


# ============================================================
# 开局库（常见变例）
# ============================================================
OPENING_BOOK = {
    # 当头炮：炮b2平e2 (1,2)->(4,2)
    (): (1,2,4,2),
    # 当头炮后：红马h0进g2
    ((1,2,4,2),): (7,0,6,2),
    # 炮h2平e2变化
    ((7,2,4,2),): (1,0,2,2),
}

def lookup_opening(move_history):
    """查开局库，返回走法或None"""
    key = tuple(move_history)
    return OPENING_BOOK.get(key)


# ============================================================
# 坐标转换
# ============================================================
def parse_coord(s):
    """'e2' -> (x=4, y=2)"""
    col = COL_MAP[s[0]]
    row = int(s[1])
    return col, row

def format_coord(x, y):
    """(4, 2) -> 'e2'"""
    return COL_REV[x] + str(y)


# ============================================================
# 主程序
# ============================================================
def main():
    data = json.loads(input())
    requests  = data['requests']
    responses = data.get('responses', [])

    # 初始化棋盘
    board = Board()

    # 判断我方颜色
    first_req = requests[0]
    my_side = RED if first_req['source'] == '-1' else BLACK

    # 重建棋盘
    move_history = []  # 记录所有已走的走法 (sx,sy,tx,ty)
    turn_id = len(responses)

    for i in range(turn_id):
        req = requests[i]
        if req['source'] != '-1':
            sx, sy = parse_coord(req['source'])
            tx, ty = parse_coord(req['target'])
            mv = (sx, sy, tx, ty)
            board.make_move(mv)
            move_history.append(mv)
        # 执行responses[i]
        resp = responses[i]
        if resp['source'] != '-1':
            sx, sy = parse_coord(resp['source'])
            tx, ty = parse_coord(resp['target'])
            mv = (sx, sy, tx, ty)
            board.make_move(mv)
            move_history.append(mv)

    # 执行最新的request
    last_req = requests[turn_id]
    if last_req['source'] != '-1':
        sx, sy = parse_coord(last_req['source'])
        tx, ty = parse_coord(last_req['target'])
        mv = (sx, sy, tx, ty)
        board.make_move(mv)
        move_history.append(mv)

    # 现在轮到我方走棋
    assert board.turn == my_side, "行棋方不匹配"

    # 提取我方走法历史（用于开局库）
    my_moves = []
    is_my_turn = (my_side == RED)
    for mv in move_history:
        if is_my_turn:
            my_moves.append(mv)
        is_my_turn = not is_my_turn

    # 查开局库（仅红方）
    best_move = None
    if my_side == RED:
        best_move = lookup_opening(tuple(my_moves))

    if best_move is None:
        # 搜索最优走法
        best_move = iterative_deepening(board, max_depth=12)

    if best_move is None:
        # 无合法走法
        result = {"response": {"source": "-1", "target": "-1"}}
    else:
        sx, sy, tx, ty = best_move
        result = {
            "response": {
                "source": format_coord(sx, sy),
                "target": format_coord(tx, ty)
            }
        }

    print(json.dumps(result))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        # 防御性处理：输出合法的无走法响应
        import traceback
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"response": {"source": "-1", "target": "-1"}}))