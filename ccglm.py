#!/usr/bin/env python3
"""
Top-tier Chinese Chess (Xiangqi) Bot for Botzone platform.
Alpha-Beta with TT, PVS, null-move, quiescence, killer/history heuristics.

Claude Code with GLM 5.1
Cost: about 1.78M tokens
"""
import json
import sys
import time
import random

# ============================================================
# Constants
# ============================================================
EMPTY = 0
R_KING, R_ADVISOR, R_BISHOP, R_KNIGHT, R_ROOK, R_CANNON, R_PAWN = 1, 2, 3, 4, 5, 6, 7
B_KING, B_ADVISOR, B_BISHOP, B_KNIGHT, B_ROOK, B_CANNON, B_PAWN = 8, 9, 10, 11, 12, 13, 14

RED, BLACK = 0, 1

PIECE_COLOR = [0] * 15
for i in range(1, 8):
    PIECE_COLOR[i] = RED
for i in range(8, 15):
    PIECE_COLOR[i] = BLACK

PIECE_VALUE = [0, 10000, 200, 200, 400, 900, 450, 100, 10000, 200, 200, 400, 900, 450, 100]

INF = 99999
MATE_SCORE = 50000

# ============================================================
# Zobrist keys
# ============================================================
random.seed(42)
ZOBRIST = [[random.getrandbits(64) for _ in range(14)] for _ in range(90)]
ZOBRIST_SIDE = random.getrandbits(64)

# ============================================================
# Position value tables (red perspective, row 0 = red base)
# ============================================================
ROOK_TABLE = [
    [206,208,207,213,214,213,207,208,206],
    [206,212,209,216,233,216,209,212,206],
    [206,208,207,214,216,214,207,208,206],
    [206,213,213,216,216,216,213,213,206],
    [208,211,211,214,215,214,211,211,208],
    [208,212,212,214,215,214,212,212,208],
    [204,209,204,212,214,212,204,209,204],
    [198,208,204,212,212,212,204,208,198],
    [200,208,206,212,200,212,206,208,200],
    [194,206,204,212,200,212,204,206,194],
]

KNIGHT_TABLE = [
    [  4,  8, 16, 12,  4, 12, 16,  8,  4],
    [  4, 10, 28, 16,  8, 16, 28, 10,  4],
    [ 12, 14, 16, 20, 18, 20, 16, 14, 12],
    [  8, 24, 18, 24, 20, 24, 18, 24,  8],
    [  6, 16, 14, 18, 16, 18, 14, 16,  6],
    [  4, 12, 16, 14, 12, 14, 16, 12,  4],
    [  2,  6,  8,  6, 10,  6,  8,  6,  2],
    [  4,  2,  8,  8,  4,  8,  8,  2,  4],
    [  0,  2,  4,  4, -2,  4,  4,  2,  0],
    [  0, -4,  0,  0,  0,  0,  0, -4,  0],
]

CANNON_TABLE = [
    [  6,  4,  0,-10,-12,-10,  0,  4,  6],
    [  2,  2,  0, -4,-14, -4,  0,  2,  2],
    [  2,  2,  0,-10, -8,-10,  0,  2,  2],
    [  0,  0, -2,  4, 10,  4, -2,  0,  0],
    [  0,  0,  0,  2,  8,  2,  0,  0,  0],
    [ -2,  0,  4,  2,  6,  2,  4,  0, -2],
    [  0,  0,  0,  2,  4,  2,  0,  0,  0],
    [  4,  0,  8,  6, 10,  6,  8,  0,  4],
    [  0,  2,  4,  6,  6,  6,  4,  2,  0],
    [  0,  0,  2,  6,  6,  6,  2,  0,  0],
]

ADVISOR_TABLE = [
    [  0,  0,  0, 20,  0, 20,  0,  0,  0],
    [  0,  0,  0,  0, 23,  0,  0,  0,  0],
    [  0,  0,  0, 20,  0, 20,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
]

BISHOP_TABLE = [
    [  0,  0, 20,  0,  0,  0, 20,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 18,  0,  0,  0, 23,  0,  0,  0, 18],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0, 20,  0,  0,  0, 20,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
]

PAWN_TABLE = [
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 10,  0, 20,  0, 30,  0, 20,  0, 10],
    [ 10, 20, 30, 40, 50, 40, 30, 20, 10],
    [ 20, 30, 50, 60, 70, 60, 50, 30, 20],
    [ 20, 40, 50, 70, 80, 70, 50, 40, 20],
    [  0,  0, 20,  0,  0,  0, 20,  0,  0],
]

KING_TABLE = [
    [  0]*9, [  0]*9, [  0]*9, [  0]*9, [  0]*9,
    [  0]*9, [  0]*9, [  0]*9, [  0]*9, [  0]*9,
]

POS_TABLE = {
    R_ROOK: ROOK_TABLE, B_ROOK: ROOK_TABLE,
    R_KNIGHT: KNIGHT_TABLE, B_KNIGHT: KNIGHT_TABLE,
    R_CANNON: CANNON_TABLE, B_CANNON: CANNON_TABLE,
    R_ADVISOR: ADVISOR_TABLE, B_ADVISOR: ADVISOR_TABLE,
    R_BISHOP: BISHOP_TABLE, B_BISHOP: BISHOP_TABLE,
    R_PAWN: PAWN_TABLE, B_PAWN: PAWN_TABLE,
    R_KING: KING_TABLE, B_KING: KING_TABLE,
}

# Pre-compute combined piece-value + position-score tables for fast eval
# EVAL_TABLE[color][piece_type][y][x] = PIECE_VALUE[p] + position_score
EVAL_TABLE = [[[0]*9 for _ in range(10)] for _ in range(15)]
for pt in range(1, 15):
    table = POS_TABLE.get(pt)
    for y in range(10):
        for x in range(9):
            pos_val = table[y][x] if table else 0
            if PIECE_COLOR[pt] == BLACK:
                pos_val = table[9-y][x] if table else 0
            EVAL_TABLE[pt][y][x] = PIECE_VALUE[pt] + pos_val

# Knight move offsets: (dx, dy, block_dx, block_dy)
KNIGHT_MOVES = [
    (-1, 2, 0, 1), (1, 2, 0, 1),
    (-2, 1, -1, 0), (2, 1, 1, 0),
    (-2, -1, -1, 0), (2, -1, 1, 0),
    (-1, -2, 0, -1), (1, -2, 0, -1),
]

BISHOP_MOVES = [
    (-2, 2, -1, 1), (2, 2, 1, 1),
    (-2, -2, -1, -1), (2, -2, 1, -1),
]

# ============================================================
# Opening book
# ============================================================
BOOK_SEQUENCES = [
    # Red first moves
    #("", "e2e5"),  # 中炮
    ("", "b2e2"),  # 中炮
    # 中炮对屏风马
    ("e2e5", "h9g7"),
    ("e2e5 h9g7", "h0g2"),
    ("e2e5 h9g7 h0g2", "i9h9"),
    ("e2e5 h9g7 h0g2 i9h9", "b0c2"),
    ("e2e5 h9g7 h0g2 i9h9 b0c2", "b9c7"),
    # 飞相局
    ("g0e2", "b9c7"),
    ("g0e2 b9c7", "b0c2"),
    ("g0e2 b9c7 b0c2", "h9g7"),
    # 当头炮对顺手炮
    ("e2e5 b7e7", "h0g2"),
    ("e2e5 b7e7 h0g2", "h9g7"),
    ("e2e5 b7e7 h0g2 h9g7", "i0h0"),
    # 仙人指路
    ("g2g3", "b9c7"),
    ("g2g3 b9c7", "b0c2"),
    # 过宫炮
    ("e2c2", "h9g7"),
    ("e2c2 h9g7", "h0g2"),
    # 士角炮
    ("e2d2", "b9c7"),
]

BOOK_DICT = {seq: mv for seq, mv in BOOK_SEQUENCES}

def lookup_book(move_seq_str):
    return BOOK_DICT.get(move_seq_str)

# ============================================================
# Board class
# ============================================================
class Board:
    __slots__ = ['board', 'side', 'zhash', 'history', 'move_history',
                 'king_pos']

    def __init__(self):
        self.board = [0] * 90
        self.side = RED
        self.zhash = 0
        self.history = []
        self.move_history = []
        self.king_pos = [None, None]  # [red_king_pos, black_king_pos]
        self._init_board()

    def _init_board(self):
        b = self.board
        b[0]=R_ROOK; b[1]=R_KNIGHT; b[2]=R_BISHOP; b[3]=R_ADVISOR; b[4]=R_KING
        b[5]=R_ADVISOR; b[6]=R_BISHOP; b[7]=R_KNIGHT; b[8]=R_ROOK
        b[19]=R_CANNON; b[25]=R_CANNON
        for x in range(0, 9, 2):
            b[27+x] = R_PAWN
        b[81]=B_ROOK; b[82]=B_KNIGHT; b[83]=B_BISHOP; b[84]=B_ADVISOR; b[85]=B_KING
        b[86]=B_ADVISOR; b[87]=B_BISHOP; b[88]=B_KNIGHT; b[89]=B_ROOK
        b[64]=B_CANNON; b[70]=B_CANNON
        for x in range(0, 9, 2):
            b[54+x] = B_PAWN

        self.king_pos[RED] = (4, 0)
        self.king_pos[BLACK] = (4, 9)

        self.zhash = 0
        for i in range(90):
            p = b[i]
            if p:
                self.zhash ^= ZOBRIST[i][p-1]

    def make_move(self, fx, fy, tx, ty):
        b = self.board
        fi = fy * 9 + fx
        ti = ty * 9 + tx
        p = b[fi]
        cap = b[ti]

        self.history.append((fi, ti, p, cap, self.zhash))

        b[fi] = EMPTY
        b[ti] = p

        zh = self.zhash ^ ZOBRIST[fi][p-1] ^ ZOBRIST[ti][p-1]
        if cap:
            zh ^= ZOBRIST[ti][cap-1]
        zh ^= ZOBRIST_SIDE
        self.zhash = zh

        # Update king position
        if p == R_KING:
            self.king_pos[RED] = (tx, ty)
        elif p == B_KING:
            self.king_pos[BLACK] = (tx, ty)

        self.side ^= 1
        self.move_history.append((fx, fy, tx, ty))
        return cap

    def undo_move(self):
        fi, ti, p, cap, old_hash = self.history.pop()
        b = self.board
        b[fi] = p
        b[ti] = cap
        self.zhash = old_hash
        self.side ^= 1
        self.move_history.pop()

        fx, fy = fi % 9, fi // 9
        if p == R_KING:
            self.king_pos[RED] = (fx, fy)
        elif p == B_KING:
            self.king_pos[BLACK] = (fx, fy)

    def make_null_move(self):
        self.history.append((-1, -1, 0, 0, self.zhash))
        self.zhash ^= ZOBRIST_SIDE
        self.side ^= 1

    def undo_null_move(self):
        _, _, _, _, old_hash = self.history.pop()
        self.zhash = old_hash
        self.side ^= 1

    def is_in_check(self, color):
        """Check if 'color' king is in check. Uses cached king position."""
        kp = self.king_pos[color]
        if kp is None:
            return True
        kx, ky = kp
        opp = 1 - color
        b = self.board

        # Rook / opponent King (flying general) attacks along straight lines
        if color == RED:
            opp_rook = B_ROOK; opp_king = B_KING
            opp_knight = B_KNIGHT; opp_cannon = B_CANNON; opp_pawn = B_PAWN
        else:
            opp_rook = R_ROOK; opp_king = R_KING
            opp_knight = R_KNIGHT; opp_cannon = R_CANNON; opp_pawn = R_PAWN

        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = kx+dx, ky+dy
            while 0 <= nx < 9 and 0 <= ny < 10:
                p = b[ny*9+nx]
                if p:
                    if PIECE_COLOR[p] == opp:
                        if p == opp_rook or p == opp_king:
                            return True
                    break
                nx += dx
                ny += dy

        # Knight attacks (reverse: check if any opponent knight attacks this square)
        for dx, dy, _, _ in KNIGHT_MOVES:
            nx, ny = kx+dx, ky+dy
            if 0 <= nx < 9 and 0 <= ny < 10 and b[ny*9+nx] == opp_knight:
                return True

        # Cannon attacks
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = kx+dx, ky+dy
            found = False
            while 0 <= nx < 9 and 0 <= ny < 10:
                p = b[ny*9+nx]
                if p:
                    if not found:
                        found = True
                    else:
                        if PIECE_COLOR[p] == opp and p == opp_cannon:
                            return True
                        break
                nx += dx
                ny += dy

        # Pawn attacks
        if color == RED:
            # Black pawn attacks from above: pawn at (kx, ky+1) attacks down
            # Black pawn at row <=4 can also attack sideways
            for dx, dy in ((0,1),(-1,0),(1,0)):
                nx, ny = kx+dx, ky+dy
                if 0 <= nx < 9 and 0 <= ny < 10 and b[ny*9+nx] == opp_pawn:
                    return True
        else:
            for dx, dy in ((0,-1),(-1,0),(1,0)):
                nx, ny = kx+dx, ky+dy
                if 0 <= nx < 9 and 0 <= ny < 10 and b[ny*9+nx] == opp_pawn:
                    return True

        return False

    def kings_facing(self):
        """Flying general: two kings on same file with nothing between."""
        rk = self.king_pos[RED]
        bk = self.king_pos[BLACK]
        if rk is None or bk is None:
            return False
        rx, ry = rk
        bx, by_ = bk
        if rx != bx:
            return False
        b = self.board
        for y in range(ry+1, by_):
            if b[y*9+rx]:
                return False
        return True

    def generate_legal_moves(self, color):
        moves = []
        b = self.board
        for y in range(10):
            for x in range(9):
                p = b[y*9+x]
                if p and PIECE_COLOR[p] == color:
                    self._gen_piece_moves(x, y, p, color, b, moves)

        legal = []
        for m in moves:
            fx, fy, tx, ty = m
            self.make_move(fx, fy, tx, ty)
            if not self.is_in_check(color) and not self.kings_facing():
                legal.append(m)
            self.undo_move()
        return legal

    def generate_pseudo_moves(self, color):
        moves = []
        b = self.board
        for y in range(10):
            for x in range(9):
                p = b[y*9+x]
                if p and PIECE_COLOR[p] == color:
                    self._gen_piece_moves(x, y, p, color, b, moves)
        return moves

    def _gen_piece_moves(self, x, y, p, color, b, moves):
        if p == R_ROOK or p == B_ROOK:
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx, ny = x+dx, y+dy
                while 0 <= nx < 9 and 0 <= ny < 10:
                    tp = b[ny*9+nx]
                    if not tp:
                        moves.append((x, y, nx, ny))
                    else:
                        if PIECE_COLOR[tp] != color:
                            moves.append((x, y, nx, ny))
                        break
                    nx += dx; ny += dy

        elif p == R_KNIGHT or p == B_KNIGHT:
            for dx, dy, bx_, by_ in KNIGHT_MOVES:
                nx, ny = x+dx, y+dy
                if not (0 <= nx < 9 and 0 <= ny < 10):
                    continue
                blkx, blky = x+bx_, y+by_
                if b[blky*9+blkx]:
                    continue
                tp = b[ny*9+nx]
                if not tp or PIECE_COLOR[tp] != color:
                    moves.append((x, y, nx, ny))

        elif p == R_BISHOP or p == B_BISHOP:
            for dx, dy, ebx, eby in BISHOP_MOVES:
                nx, ny = x+dx, y+dy
                if not (0 <= nx < 9 and 0 <= ny < 10):
                    continue
                if color == RED and ny > 4:
                    continue
                if color == BLACK and ny < 5:
                    continue
                if b[(y+eby)*9+(x+ebx)]:
                    continue
                tp = b[ny*9+nx]
                if not tp or PIECE_COLOR[tp] != color:
                    moves.append((x, y, nx, ny))

        elif p == R_ADVISOR or p == B_ADVISOR:
            for dx, dy in ((-1,-1),(1,-1),(-1,1),(1,1)):
                nx, ny = x+dx, y+dy
                if not (0 <= nx < 9 and 0 <= ny < 10):
                    continue
                if color == RED:
                    if not (3 <= nx <= 5 and 0 <= ny <= 2):
                        continue
                else:
                    if not (3 <= nx <= 5 and 7 <= ny <= 9):
                        continue
                tp = b[ny*9+nx]
                if not tp or PIECE_COLOR[tp] != color:
                    moves.append((x, y, nx, ny))

        elif p == R_KING or p == B_KING:
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx, ny = x+dx, y+dy
                if not (0 <= nx < 9 and 0 <= ny < 10):
                    continue
                if color == RED:
                    if not (3 <= nx <= 5 and 0 <= ny <= 2):
                        continue
                else:
                    if not (3 <= nx <= 5 and 7 <= ny <= 9):
                        continue
                tp = b[ny*9+nx]
                if not tp or PIECE_COLOR[tp] != color:
                    moves.append((x, y, nx, ny))

        elif p == R_CANNON or p == B_CANNON:
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx, ny = x+dx, y+dy
                jumped = False
                while 0 <= nx < 9 and 0 <= ny < 10:
                    tp = b[ny*9+nx]
                    if not jumped:
                        if not tp:
                            moves.append((x, y, nx, ny))
                        else:
                            jumped = True
                    else:
                        if tp:
                            if PIECE_COLOR[tp] != color:
                                moves.append((x, y, nx, ny))
                            break
                    nx += dx; ny += dy

        elif p == R_PAWN:
            ny = y + 1
            if ny <= 9:
                tp = b[ny*9+x]
                if not tp or PIECE_COLOR[tp] != color:
                    moves.append((x, y, x, ny))
            if y >= 5:
                if x > 0:
                    tp = b[y*9+x-1]
                    if not tp or PIECE_COLOR[tp] != color:
                        moves.append((x, y, x-1, y))
                if x < 8:
                    tp = b[y*9+x+1]
                    if not tp or PIECE_COLOR[tp] != color:
                        moves.append((x, y, x+1, y))

        elif p == B_PAWN:
            ny = y - 1
            if ny >= 0:
                tp = b[ny*9+x]
                if not tp or PIECE_COLOR[tp] != color:
                    moves.append((x, y, x, ny))
            if y <= 4:
                if x > 0:
                    tp = b[y*9+x-1]
                    if not tp or PIECE_COLOR[tp] != color:
                        moves.append((x, y, x-1, y))
                if x < 8:
                    tp = b[y*9+x+1]
                    if not tp or PIECE_COLOR[tp] != color:
                        moves.append((x, y, x+1, y))


# ============================================================
# Search engine
# ============================================================
TT_EXACT = 0
TT_LOWER = 1
TT_UPPER = 2

class Engine:
    def __init__(self, board):
        self.board = board
        tt_size = 1 << 20
        self.tt_size = tt_size
        self.tt = [None] * tt_size
        self.history_table = [[0]*90 for _ in range(90)]
        self.killer_moves = [[None, None] for _ in range(100)]
        self.start_time = 0
        self.time_limit = 3.5
        self.hard_limit = 4.5
        self.nodes = 0
        self.stopped = False

    def check_time(self):
        if self.stopped:
            return False
        if time.time() - self.start_time >= self.hard_limit:
            self.stopped = True
            return False
        return True

    def tt_store(self, h, depth, score, flag, best_move):
        idx = h & (self.tt_size - 1)
        self.tt[idx] = (h, depth, score, flag, best_move)

    def tt_probe(self, h, depth, alpha, beta):
        idx = h & (self.tt_size - 1)
        entry = self.tt[idx]
        if entry is None or entry[0] != h:
            return None, None
        _, sd, sc, fl, bm = entry
        if sd >= depth:
            if fl == TT_EXACT:
                return sc, bm
            elif fl == TT_LOWER and sc >= beta:
                return sc, bm
            elif fl == TT_UPPER and sc <= alpha:
                return sc, bm
        return None, bm

    def tt_get_move(self, h):
        idx = h & (self.tt_size - 1)
        entry = self.tt[idx]
        if entry and entry[0] == h:
            return entry[4]
        return None

    def order_moves(self, moves, depth, tt_move):
        b = self.board.board
        ht = self.history_table
        km = self.killer_moves[depth] if 0 <= depth < 100 else (None, None)
        km0, km1 = km[0], km[1]
        scored = []
        for m in moves:
            fx, fy, tx, ty = m
            if m == tt_move:
                s = 10000000
            else:
                cap = b[ty*9+tx]
                if cap:
                    s = 5000000 + PIECE_VALUE[cap] * 100 - PIECE_VALUE[b[fy*9+fx]]
                elif m == km0:
                    s = 4000000
                elif m == km1:
                    s = 3900000
                else:
                    s = ht[fy*9+fx][ty*9+tx]
            scored.append((s, m))
        scored.sort(key=lambda x: -x[0])
        return [m for _, m in scored]

    def evaluate(self):
        """Fast evaluation from current side's perspective."""
        b = self.board.board
        score = 0
        side = self.board.side
        for i in range(90):
            p = b[i]
            if not p:
                continue
            y = i // 9
            x = i - y * 9
            val = EVAL_TABLE[p][y][x]
            if PIECE_COLOR[p] == side:
                score += val
            else:
                score -= val
        return score

    def quiesce(self, alpha, beta, qdepth):
        if not self.check_time():
            return 0
        self.nodes += 1

        stand_pat = self.evaluate()
        if stand_pat >= beta:
            return beta
        if stand_pat > alpha:
            alpha = stand_pat
        if qdepth <= 0:
            return alpha

        b = self.board
        pseudo = b.generate_pseudo_moves(b.side)
        captures = []
        bb = b.board
        for m in pseudo:
            fx, fy, tx, ty = m
            if bb[ty*9+tx]:
                captures.append(m)

        captures.sort(key=lambda m: -PIECE_VALUE[bb[m[3]*9+m[2]]])

        for m in captures:
            fx, fy, tx, ty = m
            b.make_move(fx, fy, tx, ty)
            if b.is_in_check(1 - b.side) or b.kings_facing():
                b.undo_move()
                continue
            score = -self.quiesce(-beta, -alpha, qdepth - 1)
            b.undo_move()

            if self.stopped:
                return 0

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def alpha_beta(self, alpha, beta, depth, can_null):
        if not self.check_time():
            return 0

        self.nodes += 1
        b = self.board
        orig_alpha = alpha

        if depth <= 0:
            return self.quiesce(alpha, beta, 6)

        # TT probe
        tt_score, tt_move = self.tt_probe(b.zhash, depth, alpha, beta)
        if tt_score is not None:
            return tt_score

        in_check = b.is_in_check(b.side)

        # Null move pruning
        if can_null and not in_check and depth >= 3:
            b.side ^= 1
            b.zhash ^= ZOBRIST_SIDE
            self.nodes += 1
            nm_score = -self.alpha_beta(-beta, -beta+1, depth - 3, False)
            b.zhash ^= ZOBRIST_SIDE
            b.side ^= 1
            if not self.stopped and nm_score >= beta:
                return beta

        pseudo = b.generate_pseudo_moves(b.side)
        tt_best = self.tt_get_move(b.zhash)
        moves = self.order_moves(pseudo, depth, tt_best)

        if not moves:
            if in_check:
                return -MATE_SCORE + (64 - depth)
            return 0

        best_move = moves[0]
        best_score = -INF
        move_count = 0

        for m in moves:
            fx, fy, tx, ty = m
            b.make_move(fx, fy, tx, ty)
            if b.is_in_check(1 - b.side) or b.kings_facing():
                b.undo_move()
                continue

            move_count += 1

            if move_count == 1:
                score = -self.alpha_beta(-beta, -alpha, depth - 1, True)
            else:
                score = -self.alpha_beta(-alpha-1, -alpha, depth - 1, True)
                if not self.stopped and alpha < score < beta:
                    score = -self.alpha_beta(-beta, -alpha, depth - 1, True)

            b.undo_move()

            if self.stopped:
                return 0

            if score > best_score:
                best_score = score
                best_move = m
                if score > alpha:
                    alpha = score
                    if alpha >= beta:
                        if 0 <= depth < 100:
                            km = self.killer_moves[depth]
                            if m != km[0]:
                                km[1] = km[0]
                                km[0] = m
                        self.history_table[fy*9+fx][ty*9+tx] += depth * depth
                        break

        if move_count == 0:
            if in_check:
                return -MATE_SCORE + (64 - depth)
            return 0

        # TT store
        if best_score <= orig_alpha:
            flag = TT_UPPER
        elif best_score >= beta:
            flag = TT_LOWER
        else:
            flag = TT_EXACT
        self.tt_store(b.zhash, depth, best_score, flag, best_move)

        return best_score

    def search(self, time_limit=3.5):
        self.start_time = time.time()
        self.time_limit = time_limit
        self.hard_limit = time_limit + 1.0
        self.stopped = False
        self.nodes = 0

        b = self.board
        best_move = None

        for depth in range(1, 50):
            pseudo = b.generate_pseudo_moves(b.side)
            tt_best = self.tt_get_move(b.zhash)
            moves = self.order_moves(pseudo, depth, tt_best)

            if not moves:
                break

            current_best = moves[0]
            current_score = -INF
            alpha = -INF
            beta = INF
            legal_count = 0

            for m in moves:
                fx, fy, tx, ty = m
                b.make_move(fx, fy, tx, ty)
                if b.is_in_check(1 - b.side) or b.kings_facing():
                    b.undo_move()
                    continue

                legal_count += 1
                if legal_count == 1:
                    score = -self.alpha_beta(-beta, -alpha, depth - 1, True)
                else:
                    score = -self.alpha_beta(-alpha-1, -alpha, depth - 1, True)
                    if not self.stopped and score > alpha:
                        score = -self.alpha_beta(-beta, -alpha, depth - 1, True)

                b.undo_move()

                if self.stopped:
                    break

                if score > current_score:
                    current_score = score
                    current_best = m
                    if score > alpha:
                        alpha = score

            if not self.stopped:
                best_move = current_best
                elapsed = time.time() - self.start_time
                if elapsed > self.time_limit * 0.6:
                    break
            else:
                break

        return best_move


# ============================================================
# Coordinate conversion
# ============================================================
def coord_to_str(x, y):
    return chr(97 + x) + str(y)

def str_to_coord(s):
    return ord(s[0]) - 97, int(s[1])


# ============================================================
# Main
# ============================================================
def main():
    try:
        raw = input()
        data = json.loads(raw.strip())
        requests = data.get("requests", [])
        responses = data.get("responses", [])

        board = Board()
        turn_id = len(responses)

        # Determine color: requests[0].source == "-1" means we are Red (first mover)
        my_color = RED if requests[0]["source"] == "-1" else BLACK

        # Replay history
        for i in range(turn_id):
            req = requests[i]
            if req["source"] != "-1":
                fx, fy = str_to_coord(req["source"])
                tx, ty = str_to_coord(req["target"])
                board.make_move(fx, fy, tx, ty)

            resp = responses[i]
            if resp["source"] != "-1":
                fx, fy = str_to_coord(resp["source"])
                tx, ty = str_to_coord(resp["target"])
                board.make_move(fx, fy, tx, ty)

        # Current request (opponent's latest move)
        req = requests[turn_id]
        if req["source"] != "-1":
            fx, fy = str_to_coord(req["source"])
            tx, ty = str_to_coord(req["target"])
            board.make_move(fx, fy, tx, ty)

        board.side = my_color

        # Build move sequence string for opening book lookup
        move_seq = []
        for i in range(turn_id):
            if requests[i]["source"] != "-1":
                move_seq.append(requests[i]["source"] + requests[i]["target"])
            if responses[i]["source"] != "-1":
                move_seq.append(responses[i]["source"] + responses[i]["target"])
        if requests[turn_id]["source"] != "-1":
            move_seq.append(requests[turn_id]["source"] + requests[turn_id]["target"])

        book_str = " ".join(move_seq)
        book_move = lookup_book(book_str)

        if book_move is not None and len(move_seq) < 20:
            fx, fy = str_to_coord(book_move[:2])
            tx, ty = str_to_coord(book_move[2:])
            result = {"response": {"source": coord_to_str(fx, fy), "target": coord_to_str(tx, ty)}}
        else:
            engine = Engine(board)
            best = engine.search(time_limit=3.5)

            legal = board.generate_legal_moves(my_color)

            if best is not None and best not in legal:
                best = legal[0] if legal else None
            elif best is None:
                best = legal[0] if legal else None

            # Filter repetition: avoid moves that create 3-fold repetition
            if best is not None and len(legal) > 1:
                h = board.zhash
                # Check how many times current hash appeared
                hash_count = 0
                for entry in board.history:
                    if entry[4] == h:
                        hash_count += 1
                if hash_count >= 2:
                    # Current position repeated, avoid repeating further
                    for alt in legal:
                        if alt == best:
                            continue
                        board.make_move(*alt)
                        new_h = board.zhash
                        repeat = False
                        cnt = 0
                        for entry in board.history[:-1]:
                            if entry[4] == new_h:
                                cnt += 1
                                if cnt >= 2:
                                    repeat = True
                                    break
                        board.undo_move()
                        if not repeat:
                            best = alt
                            break

            if best is None:
                result = {"response": {"source": "-1", "target": "-1"}}
            else:
                fx, fy, tx, ty = best
                result = {"response": {"source": coord_to_str(fx, fy), "target": coord_to_str(tx, ty)}}

        print(json.dumps(result))

    except Exception:
        print(json.dumps({"response": {"source": "-1", "target": "-1"}}))

if __name__ == "__main__":
    main()
