#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chinese Chess Bot for Botzone Platform
Features: PVS search, Zobrist hashing, transposition table, quiescence search,
          null move pruning, killer/heuristic move ordering, opening book,
          repetition detection, fine-grained position evaluation tables.

Coordinate system (Botzone convention):
  x: 0-8 (columns a-i), y: 0-9 (rows)
  RED back rank y=0, BLACK back rank y=9
  RED forward = y+1, BLACK forward = y-1

Claude Code with DeepSeek V4 Pro
Cost: about 6.3M tokens
"""

import sys
import json
import time
import random
from collections import deque

# ===================== Piece Constants =====================
EMPTY = 0
R_KING = 1;    R_ADVISOR = 2; R_BISHOP = 3
R_KNIGHT = 4;  R_ROOK = 5;    R_CANNON = 6; R_PAWN = 7
B_KING = -1;   B_ADVISOR = -2; B_BISHOP = -3
B_KNIGHT = -4; B_ROOK = -5;    B_CANNON = -6; B_PAWN = -7

PIECE_VALUE = {
    R_KING: 10000, R_ADVISOR: 200, R_BISHOP: 200,
    R_KNIGHT: 400, R_ROOK: 900, R_CANNON: 450, R_PAWN: 100
}

_is_red = lambda p: p > 0
_same_side = lambda p1, p2: (p1 > 0 and p2 > 0) or (p1 < 0 and p2 < 0)

# ===================== Zobrist Hashing =====================
# 14 piece types (7 red + 7 black), 10 rows x 9 cols
_zobrist_keys = [[[random.getrandbits(64) for _ in range(14)]
                  for _ in range(9)] for _ in range(10)]

def _zobrist_idx(piece):
    """Map piece value to Zobrist table index (0-13)."""
    if piece > 0:
        return piece - 1     # R_KING(1)→0 ... R_PAWN(7)→6
    else:
        return -piece + 6    # B_KING(-1)→7 ... B_PAWN(-7)→13

# ===================== Position Evaluation Tables =====================
# All tables from RED perspective: [y][x], y=0 is RED back rank.
# BLACK evaluation uses mirrored index [9-y][x].

# Rook: active in opponent territory, central files, river area
ROOK_POS = [
    [194,206,204,212,200,212,204,206,194],
    [200,208,206,212,200,212,206,208,200],
    [198,208,204,212,212,212,204,208,198],
    [204,209,204,212,214,212,204,209,204],
    [208,212,212,214,215,214,212,212,208],
    [208,211,211,214,215,214,211,211,208],
    [206,213,213,216,216,216,213,213,206],
    [206,208,207,214,216,214,207,208,206],
    [206,212,209,216,233,216,209,212,206],
    [206,208,207,213,214,213,207,208,206],
]

# Cannon: best with many pieces, central control
CANNON_POS = [
    [170,184,182,193,193,193,182,184,170],
    [173,184,182,196,193,196,182,184,173],
    [173,184,182,196,196,196,182,184,173],
    [174,186,186,196,196,196,186,186,174],
    [176,187,187,195,200,195,187,187,176],
    [183,190,190,196,197,196,190,190,183],
    [185,191,193,197,198,197,193,191,185],
    [187,191,191,192,194,192,191,191,187],
    [189,194,187,192,196,192,187,194,189],
    [190,190,192,194,191,194,192,190,190],
]

# Knight: central squares best, avoid edges
KNIGHT_POS = [
    [88, 85, 90, 88, 90, 88, 90, 85, 88],
    [85, 90, 92, 93, 78, 93, 92, 90, 85],
    [93, 92, 96, 93, 94, 93, 96, 92, 93],
    [92, 94, 98, 95,102, 95, 98, 94, 92],
    [90, 98,101,102,103,102,101, 98, 90],
    [90,100, 99,103,104,103, 99,100, 90],
    [93,108,100,107,100,107,100,108, 93],
    [92, 98, 99,103, 99,103, 99, 98, 92],
    [90, 96,103, 97, 94, 97,103, 96, 90],
    [90, 90, 90, 96, 90, 96, 90, 90, 90],
]

# Bishop: defensive, connected
BISHOP_POS = [
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0, 20,  0,  0,  0, 20,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
]

# Advisor: center of palace best (5-square palace: x=3-5, y=0-2 or y=7-9)
ADVISOR_POS = [
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
]

# King: center of palace safest; edges vulnerable to checks
KING_POS = [
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
]

# Pawn: gains value dramatically after crossing river
PAWN_POS = [
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [18, 36, 56, 80, 80, 80, 56, 36, 18],
    [14, 26, 42, 44, 54, 44, 42, 26, 14],
    [10, 20, 30, 34, 40, 34, 30, 20, 10],
    [ 6, 12, 18, 18, 20, 18, 18, 12,  6],
    [ 2,  0,  8,  0,  8,  0,  8,  0,  2],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
]

# Flatten position tables for faster lookup: index = y * 9 + x
ROOK_POS_FLAT = [v for row in ROOK_POS for v in row]
CANNON_POS_FLAT = [v for row in CANNON_POS for v in row]
KNIGHT_POS_FLAT = [v for row in KNIGHT_POS for v in row]
BISHOP_POS_FLAT = [v for row in BISHOP_POS for v in row]
ADVISOR_POS_FLAT = [v for row in ADVISOR_POS for v in row]
KING_POS_FLAT = [v for row in KING_POS for v in row]
PAWN_POS_FLAT = [v for row in PAWN_POS for v in row]

def _get_pos_bonus(piece, y, x):
    """Get position bonus for a piece at (x, y). Positive bonus is good."""
    ap = abs(piece)
    if ap == 1:   tbl = KING_POS_FLAT
    elif ap == 2: tbl = ADVISOR_POS_FLAT
    elif ap == 3: tbl = BISHOP_POS_FLAT
    elif ap == 4: tbl = KNIGHT_POS_FLAT
    elif ap == 5: tbl = ROOK_POS_FLAT
    elif ap == 6: tbl = CANNON_POS_FLAT
    else:         tbl = PAWN_POS_FLAT

    if _is_red(piece):
        return tbl[y * 9 + x]
    else:
        return tbl[(9 - y) * 9 + x]


# ===================== Coordinate Conversion =====================
def decode(s):
    """'e0' -> (4, 0); '-1' -> (-1, -1)"""
    if s == "-1":
        return (-1, -1)
    return (ord(s[0]) - ord('a'), int(s[1:]))

def encode(x, y):
    """(4, 0) -> 'e0'"""
    return chr(ord('a') + x) + str(y)


# ===================== Board Class =====================
class Board:
    """Incremental board state with Zobrist hashing and repetition tracking."""

    def __init__(self):
        self.board = [[EMPTY] * 9 for _ in range(10)]
        self.rkx = 4; self.rky = 0  # red king at e0
        self.bkx = 4; self.bky = 9  # black king at e9
        self.zobrist = 0
        self.hash_history = deque(maxlen=200)
        self._init_board()
        self._init_hash()

    def _init_board(self):
        b = self.board
        # RED back rank (y=0)
        b[0][0] = R_ROOK; b[0][1] = R_KNIGHT; b[0][2] = R_BISHOP
        b[0][3] = R_ADVISOR; b[0][4] = R_KING; b[0][5] = R_ADVISOR
        b[0][6] = R_BISHOP; b[0][7] = R_KNIGHT; b[0][8] = R_ROOK
        # RED cannons (y=2)
        b[2][1] = R_CANNON; b[2][7] = R_CANNON
        # RED pawns (y=3)
        b[3][0] = R_PAWN; b[3][2] = R_PAWN; b[3][4] = R_PAWN
        b[3][6] = R_PAWN; b[3][8] = R_PAWN
        # BLACK back rank (y=9)
        b[9][0] = B_ROOK; b[9][1] = B_KNIGHT; b[9][2] = B_BISHOP
        b[9][3] = B_ADVISOR; b[9][4] = B_KING; b[9][5] = B_ADVISOR
        b[9][6] = B_BISHOP; b[9][7] = B_KNIGHT; b[9][8] = B_ROOK
        # BLACK cannons (y=7)
        b[7][1] = B_CANNON; b[7][7] = B_CANNON
        # BLACK pawns (y=6)
        b[6][0] = B_PAWN; b[6][2] = B_PAWN; b[6][4] = B_PAWN
        b[6][6] = B_PAWN; b[6][8] = B_PAWN

    def _init_hash(self):
        h = 0
        for y in range(10):
            for x in range(9):
                p = self.board[y][x]
                if p != EMPTY:
                    h ^= _zobrist_keys[y][x][_zobrist_idx(p)]
        self.zobrist = h
        self.hash_history.append(h)

    def make_move(self, x1, y1, x2, y2):
        """Execute move in-place. Returns (captured, orkx, orky, obkx, obky)."""
        board = self.board
        piece = board[y1][x1]
        captured = board[y2][x2]

        orkx, orky = self.rkx, self.rky
        obkx, obky = self.bkx, self.bky

        board[y2][x2] = piece
        board[y1][x1] = EMPTY

        if piece == R_KING:
            self.rkx, self.rky = x2, y2
        elif piece == B_KING:
            self.bkx, self.bky = x2, y2

        # Incremental Zobrist update
        h = self.zobrist
        h ^= _zobrist_keys[y1][x1][_zobrist_idx(piece)]
        h ^= _zobrist_keys[y2][x2][_zobrist_idx(piece)]
        if captured != EMPTY:
            h ^= _zobrist_keys[y2][x2][_zobrist_idx(captured)]
        self.zobrist = h
        self.hash_history.append(h)

        return captured, orkx, orky, obkx, obky

    def unmake_move(self, x1, y1, x2, y2, piece, captured, orkx, orky, obkx, obky):
        """Undo a move, restoring all state."""
        self.board[y1][x1] = piece
        self.board[y2][x2] = captured
        self.rkx, self.rky = orkx, orky
        self.bkx, self.bky = obkx, obky
        self.hash_history.pop()
        self.zobrist = self.hash_history[-1] if self.hash_history else 0


# ===================== Move Generation =====================
def _gen_rook_moves(board, x, y):
    piece = board[y][x]
    moves = []
    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx, ny = x + dx, y + dy
        while 0 <= nx <= 8 and 0 <= ny <= 9:
            t = board[ny][nx]
            if t == EMPTY:
                moves.append((x, y, nx, ny))
            else:
                if not _same_side(piece, t):
                    moves.append((x, y, nx, ny))
                break
            nx += dx; ny += dy
    return moves

def _gen_cannon_moves(board, x, y):
    piece = board[y][x]
    moves = []
    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx, ny = x + dx, y + dy
        screened = False
        while 0 <= nx <= 8 and 0 <= ny <= 9:
            t = board[ny][nx]
            if not screened:
                if t == EMPTY:
                    moves.append((x, y, nx, ny))
                else:
                    screened = True
            else:
                if t != EMPTY:
                    if not _same_side(piece, t):
                        moves.append((x, y, nx, ny))
                    break
            nx += dx; ny += dy
    return moves

def _gen_knight_moves(board, x, y):
    piece = board[y][x]
    moves = []
    patterns = [
        (1,0, 1,1), (1,0, 1,-1), (-1,0, -1,1), (-1,0, -1,-1),
        (0,1, 1,1), (0,1, -1,1), (0,-1, 1,-1), (0,-1, -1,-1),
    ]
    for lx, ly, fx, fy in patterns:
        leg_x, leg_y = x + lx, y + ly
        if not (0 <= leg_x <= 8 and 0 <= leg_y <= 9):
            continue
        if board[leg_y][leg_x] != EMPTY:
            continue
        nx, ny = x + lx + fx, y + ly + fy
        if not (0 <= nx <= 8 and 0 <= ny <= 9):
            continue
        if not _same_side(piece, board[ny][nx]):
            moves.append((x, y, nx, ny))
    return moves

def _gen_bishop_moves(board, x, y):
    piece = board[y][x]
    red = _is_red(piece)
    moves = []
    for dx, dy in [(2,2),(2,-2),(-2,2),(-2,-2)]:
        nx, ny = x + dx, y + dy
        if not (0 <= nx <= 8 and 0 <= ny <= 9):
            continue
        if red and ny > 4:
            continue
        if not red and ny < 5:
            continue
        eye_x, eye_y = x + dx // 2, y + dy // 2
        if board[eye_y][eye_x] != EMPTY:
            continue
        if not _same_side(piece, board[ny][nx]):
            moves.append((x, y, nx, ny))
    return moves

def _gen_advisor_moves(board, x, y):
    piece = board[y][x]
    red = _is_red(piece)
    moves = []
    for dx, dy in [(1,1),(1,-1),(-1,1),(-1,-1)]:
        nx, ny = x + dx, y + dy
        if not (0 <= nx <= 8 and 0 <= ny <= 9):
            continue
        if red:
            if not (3 <= nx <= 5 and 0 <= ny <= 2):
                continue
        else:
            if not (3 <= nx <= 5 and 7 <= ny <= 9):
                continue
        if not _same_side(piece, board[ny][nx]):
            moves.append((x, y, nx, ny))
    return moves

def _gen_king_moves(board, x, y):
    piece = board[y][x]
    red = _is_red(piece)
    moves = []
    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx, ny = x + dx, y + dy
        if not (0 <= nx <= 8 and 0 <= ny <= 9):
            continue
        if red:
            if not (3 <= nx <= 5 and 0 <= ny <= 2):
                continue
        else:
            if not (3 <= nx <= 5 and 7 <= ny <= 9):
                continue
        if not _same_side(piece, board[ny][nx]):
            moves.append((x, y, nx, ny))
    return moves

def _gen_pawn_moves(board, x, y):
    piece = board[y][x]
    red = _is_red(piece)
    moves = []
    if red:
        fwd = 1
        crossed = y >= 5
    else:
        fwd = -1
        crossed = y <= 4

    ny = y + fwd
    if 0 <= ny <= 9:
        if not _same_side(piece, board[ny][x]):
            moves.append((x, y, x, ny))

    if crossed:
        for dx in [-1, 1]:
            nx = x + dx
            if 0 <= nx <= 8:
                if not _same_side(piece, board[y][nx]):
                    moves.append((x, y, nx, y))
    return moves

def _gen_raw_moves(board, x, y):
    p = board[y][x]
    ap = abs(p)
    if ap == 5:   return _gen_rook_moves(board, x, y)
    elif ap == 6: return _gen_cannon_moves(board, x, y)
    elif ap == 4: return _gen_knight_moves(board, x, y)
    elif ap == 3: return _gen_bishop_moves(board, x, y)
    elif ap == 2: return _gen_advisor_moves(board, x, y)
    elif ap == 1: return _gen_king_moves(board, x, y)
    elif ap == 7: return _gen_pawn_moves(board, x, y)
    return []


# ===================== Check Detection =====================
def _flying_kings(board):
    """Return True if the two kings face each other with nothing between."""
    rkx, rky = board.rkx, board.rky
    bkx, bky = board.bkx, board.bky
    if rkx != bkx:
        return False
    lo, hi = (rky, bky) if rky < bky else (bky, rky)
    for y in range(lo + 1, hi):
        if board.board[y][rkx] != EMPTY:
            return False
    return True

def _square_attacked(board, tx, ty, by_red):
    """Return True if square (tx, ty) is attacked by 'by_red' side."""
    board_arr = board.board
    for y in range(10):
        for x in range(9):
            p = board_arr[y][x]
            if p == EMPTY or _is_red(p) != by_red:
                continue
            ap = abs(p)
            if ap == 1:  # King
                if abs(tx - x) + abs(ty - y) == 1:
                    return True
            elif ap == 2:  # Advisor
                if abs(tx - x) == 1 and abs(ty - y) == 1:
                    return True
            elif ap == 3:  # Bishop
                if abs(tx - x) == 2 and abs(ty - y) == 2:
                    eye_x, eye_y = (x + tx) // 2, (y + ty) // 2
                    if board_arr[eye_y][eye_x] == EMPTY:
                        return True
            elif ap == 4:  # Knight
                dx, dy = abs(tx - x), abs(ty - y)
                if (dx == 2 and dy == 1) or (dx == 1 and dy == 2):
                    if dx == 2:
                        leg_x = x + (1 if tx > x else -1)
                        leg_y = y
                    else:
                        leg_x = x
                        leg_y = y + (1 if ty > y else -1)
                    if board_arr[leg_y][leg_x] == EMPTY:
                        return True
            elif ap == 5:  # Rook
                if tx == x:
                    lo, hi = (y, ty) if y < ty else (ty, y)
                    if all(board_arr[iy][x] == EMPTY for iy in range(lo + 1, hi)):
                        return True
                elif ty == y:
                    lo, hi = (x, tx) if x < tx else (tx, x)
                    if all(board_arr[y][ix] == EMPTY for ix in range(lo + 1, hi)):
                        return True
            elif ap == 6:  # Cannon
                if tx == x:
                    lo, hi = (y, ty) if y < ty else (ty, y)
                    cnt = sum(1 for iy in range(lo + 1, hi) if board_arr[iy][x] != EMPTY)
                    if cnt == 1:
                        return True
                elif ty == y:
                    lo, hi = (x, tx) if x < tx else (tx, x)
                    cnt = sum(1 for ix in range(lo + 1, hi) if board_arr[y][ix] != EMPTY)
                    if cnt == 1:
                        return True
            elif ap == 7:  # Pawn
                red_pawn = _is_red(p)
                if red_pawn:
                    if ty == y + 1 and tx == x:
                        return True
                    if y >= 5 and ty == y and abs(tx - x) == 1:
                        return True
                else:
                    if ty == y - 1 and tx == x:
                        return True
                    if y <= 4 and ty == y and abs(tx - x) == 1:
                        return True
    return False

def is_in_check(board, red):
    """Return True if the side 'red' is in check."""
    kx, ky = (board.rkx, board.rky) if red else (board.bkx, board.bky)
    return _flying_kings(board) or _square_attacked(board, kx, ky, not red)


def _causes_flying_kings(board, x1, y1, x2, y2):
    """Check if this move would cause the two kings to face each other."""
    piece = board.board[y1][x1]
    ap = abs(piece)

    if ap == 1:
        # Moving a king
        red = _is_red(piece)
        if red:
            tkx, tky = x2, y2
            okx, oky = board.bkx, board.bky
        else:
            tkx, tky = x2, y2
            okx, oky = board.rkx, board.rky
        if tkx != okx:
            return False
        lo, hi = (tky, oky) if tky < oky else (oky, tky)
        for yy in range(lo + 1, hi):
            if board.board[yy][tkx] != EMPTY:
                return False
        return True

    # Moving a non-king piece: check if it was the sole blocker between kings
    rkx, rky = board.rkx, board.rky
    bkx, bky = board.bkx, board.bky
    if rkx != bkx or x1 != rkx:
        return False

    lo, hi = (rky, bky) if rky < bky else (bky, rky)
    if not (lo < y1 < hi):
        return False

    # Check if this is the only piece between kings (besides itself)
    for yy in range(lo + 1, hi):
        if yy == y1:
            continue
        if yy == y2 and x2 == rkx and lo < y2 < hi:
            continue  # moving within column between kings
        if board.board[yy][rkx] != EMPTY:
            return False

    # If destination is off-column or outside the interval, kings face
    if x2 != rkx:
        return True
    return not (lo < y2 < hi)


# ===================== Legal Move Generation =====================
def get_legal_moves(board, red_turn):
    """Generate all fully legal moves, filtering self-check, flying kings, repetition."""
    board_arr = board.board
    moves = []
    for y in range(10):
        for x in range(9):
            p = board_arr[y][x]
            if p == EMPTY or _is_red(p) != red_turn:
                continue
            raw = _gen_raw_moves(board_arr, x, y)
            for (x1, y1, x2, y2) in raw:
                if _causes_flying_kings(board, x1, y1, x2, y2):
                    continue
                cap, orkx, orky, obkx, obky = board.make_move(x1, y1, x2, y2)
                in_chk = is_in_check(board, red_turn)
                # Capture new hash BEFORE unmake for repetition detection
                new_hash = board.zobrist
                board.unmake_move(x1, y1, x2, y2, p, cap, orkx, orky, obkx, obky)
                if in_chk:
                    continue
                # 3-fold repetition: filter if resulting position appears >= 3 times
                cnt = sum(1 for z in board.hash_history if z == new_hash)
                if cnt < 3:
                    moves.append((x1, y1, x2, y2))
    return moves


# ===================== Evaluation =====================
def evaluate(board):
    """Static evaluation from RED perspective (positive = good for RED).
    Uses piece-square tables and check bonus only. Mobility is assessed by
    the search itself (quiescence handles tactical exchanges)."""
    if board.board[board.rky][board.rkx] != R_KING:
        return -99999
    if board.board[board.bky][board.bkx] != B_KING:
        return 99999

    score = 0
    board_arr = board.board
    for y in range(10):
        for x in range(9):
            p = board_arr[y][x]
            if p == EMPTY:
                continue
            ap = abs(p)
            val = PIECE_VALUE[ap]
            pos = _get_pos_bonus(p, y, x)
            if _is_red(p):
                score += val + pos
            else:
                score -= val + pos

    if is_in_check(board, False):
        score += 50
    if is_in_check(board, True):
        score -= 50

    return score


# ===================== Move Ordering =====================
def _mvv_lva(board, move):
    """MVV-LVA score: higher = more valuable victim, less valuable attacker."""
    victim = abs(board.board[move[3]][move[2]])
    attacker = abs(board.board[move[1]][move[0]])
    if victim == 0:
        return 0
    return victim * 10 - attacker


# ===================== Search Engine =====================
class Searcher:
    def __init__(self):
        self.tt = {}
        self.killers = [[] for _ in range(64)]
        self.history = [[0] * 90 for _ in range(90)]
        self.nodes = 0
        self.start_time = 0
        self.time_limit = 4.0
        self.soft_limit = 3.0
        self.best_move_sofar = None

    def _check_time(self):
        return time.time() - self.start_time >= self.time_limit

    def _check_soft_time(self):
        return time.time() - self.start_time >= self.soft_limit

    def _tt_lookup(self, hash_key, depth, alpha, beta):
        """Returns (found, value, best_move) from transposition table."""
        if hash_key not in self.tt:
            return False, 0, None
        tt_depth, tt_flag, tt_value, tt_move = self.tt[hash_key]
        if tt_depth >= depth:
            if tt_flag == 0:  # EXACT
                return True, tt_value, tt_move
            elif tt_flag == 1 and tt_value <= alpha:  # UPPER_BOUND
                return True, tt_value, tt_move
            elif tt_flag == 2 and tt_value >= beta:   # LOWER_BOUND
                return True, tt_value, tt_move
        return False, 0, tt_move

    def _tt_store(self, hash_key, depth, flag, value, best_move):
        if hash_key in self.tt and self.tt[hash_key][0] > depth:
            return
        self.tt[hash_key] = (depth, flag, value, best_move)

    def _order_moves(self, board, moves, tt_move, ply):
        """Order moves: TT move > captures (MVV-LVA) > killers > history."""
        scored = []
        board_arr = board.board
        for m in moves:
            score = 0
            if tt_move is not None and m == tt_move:
                score = 10000000
            elif board_arr[m[3]][m[2]] != EMPTY:
                score = 900000 + _mvv_lva(board, m)
            elif self.killers[ply] and m in self.killers[ply]:
                score = 800000
            else:
                frm = m[1] * 9 + m[0]
                to = m[3] * 9 + m[2]
                score = self.history[frm][to]
            scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]

    def quiescence(self, board, alpha, beta, red_turn, qdepth=0):
        """Quiescence search: only capture moves to avoid horizon effect."""
        self.nodes += 1
        if self._check_time() or qdepth >= 8:
            return evaluate(board)

        stand_pat = evaluate(board)
        if stand_pat >= beta:
            return beta
        if stand_pat > alpha:
            alpha = stand_pat

        # Generate only capture moves
        board_arr = board.board
        captures = []
        for y in range(10):
            for x in range(9):
                p = board_arr[y][x]
                if p == EMPTY or _is_red(p) != red_turn:
                    continue
                raw = _gen_raw_moves(board_arr, x, y)
                for (x1, y1, x2, y2) in raw:
                    if board_arr[y2][x2] == EMPTY:
                        continue
                    if _causes_flying_kings(board, x1, y1, x2, y2):
                        continue
                    cap, orkx, orky, obkx, obky = board.make_move(x1, y1, x2, y2)
                    ok = not is_in_check(board, red_turn)
                    board.unmake_move(x1, y1, x2, y2, p, cap, orkx, orky, obkx, obky)
                    if ok:
                        captures.append((x1, y1, x2, y2))

        if not captures:
            return stand_pat

        captures.sort(key=lambda m: _mvv_lva(board, m), reverse=True)

        for (x1, y1, x2, y2) in captures:
            p = board_arr[y1][x1]
            cap, orkx, orky, obkx, obky = board.make_move(x1, y1, x2, y2)

            # Delta pruning
            victim_val = PIECE_VALUE.get(abs(cap), 0)
            if stand_pat + victim_val + 200 < alpha:
                board.unmake_move(x1, y1, x2, y2, p, cap, orkx, orky, obkx, obky)
                continue

            score = -self.quiescence(board, -beta, -alpha, not red_turn, qdepth + 1)
            board.unmake_move(x1, y1, x2, y2, p, cap, orkx, orky, obkx, obky)

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def pvs(self, board, depth, alpha, beta, red_turn, ply, is_pv):
        """Principal Variation Search (NegaScout) with null move pruning."""
        self.nodes += 1

        if self._check_time():
            return -99999

        # Transposition table probe
        hash_key = board.zobrist
        tt_hit, tt_value, tt_move = self._tt_lookup(hash_key, depth, alpha, beta)
        if tt_hit and not is_pv:
            return tt_value

        # Null move pruning (skip for PV nodes and when in check)
        if depth >= 3 and not is_in_check(board, red_turn) and not is_pv:
            R = 3
            score = -self.pvs(board, depth - R - 1, -beta, -beta + 1, not red_turn, ply + 2, False)
            if score >= beta:
                return beta

        # Leaf node
        if depth <= 0:
            return self.quiescence(board, alpha, beta, red_turn)

        # Generate and order moves
        moves = get_legal_moves(board, red_turn)
        if not moves:
            if is_in_check(board, red_turn):
                return -99999 + ply * 10
            return 0

        ordered = self._order_moves(board, moves, tt_move, ply)

        best_score = -99999
        best_move = ordered[0]
        board_arr = board.board
        old_alpha = alpha

        for i, (x1, y1, x2, y2) in enumerate(ordered):
            if self._check_time():
                break

            p = board_arr[y1][x1]
            cap, orkx, orky, obkx, obky = board.make_move(x1, y1, x2, y2)

            if i == 0:
                score = -self.pvs(board, depth - 1, -beta, -alpha, not red_turn, ply + 1, is_pv)
            else:
                score = -self.pvs(board, depth - 1, -alpha - 1, -alpha, not red_turn, ply + 1, False)
                if alpha < score < beta:
                    score = -self.pvs(board, depth - 1, -beta, -alpha, not red_turn, ply + 1, True)

            board.unmake_move(x1, y1, x2, y2, p, cap, orkx, orky, obkx, obky)

            if score > best_score:
                best_score = score
                best_move = (x1, y1, x2, y2)
                if score > alpha:
                    alpha = score

            if score >= beta:
                if cap == EMPTY:
                    if not self.killers[ply] or self.killers[ply][0] != (x1, y1, x2, y2):
                        self.killers[ply] = [(x1, y1, x2, y2)] + self.killers[ply]
                        if len(self.killers[ply]) > 2:
                            self.killers[ply] = self.killers[ply][:2]

                    frm = y1 * 9 + x1
                    to = y2 * 9 + x2
                    self.history[frm][to] += depth * depth

                break

        # Determine TT flag based on final score vs bounds
        if best_score >= beta:
            flag = 2  # LOWER_BOUND
        elif best_score > old_alpha:
            flag = 0  # EXACT
        else:
            flag = 1  # UPPER_BOUND

        self._tt_store(hash_key, depth, flag, best_score, best_move)
        return best_score

    def search_root(self, board, red_turn, max_depth=20):
        """Iterative deepening at root."""
        self.start_time = time.time()
        self.nodes = 0
        self.best_move_sofar = None

        root_moves = get_legal_moves(board, red_turn)
        if not root_moves:
            return None
        if len(root_moves) == 1:
            return root_moves[0]

        best_move = root_moves[0]

        for depth in range(1, max_depth + 1):
            if self._check_soft_time():
                break

            best_score = -99999
            current_best = root_moves[0]
            board_arr = board.board

            # Order root moves
            scored_root = []
            for m in root_moves:
                score = 0
                if m == best_move:
                    score = 10000000
                elif board_arr[m[3]][m[2]] != EMPTY:
                    score = 900000 + _mvv_lva(board, m)
                else:
                    frm = m[1] * 9 + m[0]
                    to = m[3] * 9 + m[2]
                    score = self.history[frm][to]
                scored_root.append((score, m))
            scored_root.sort(key=lambda x: x[0], reverse=True)
            ordered_root = [m for _, m in scored_root]

            for i, (x1, y1, x2, y2) in enumerate(ordered_root):
                if self._check_time():
                    break

                p = board_arr[y1][x1]
                cap, orkx, orky, obkx, obky = board.make_move(x1, y1, x2, y2)

                if i == 0:
                    score = -self.pvs(board, depth - 1, -99999, 99999, not red_turn, 1, True)
                else:
                    score = -self.pvs(board, depth - 1, -best_score - 1, -best_score, not red_turn, 1, False)
                    if best_score < score < 99999:
                        score = -self.pvs(board, depth - 1, -99999, -best_score, not red_turn, 1, True)

                board.unmake_move(x1, y1, x2, y2, p, cap, orkx, orky, obkx, obky)

                if score > best_score:
                    best_score = score
                    current_best = (x1, y1, x2, y2)

            if not self._check_time():
                best_move = current_best
                self.best_move_sofar = best_move

        return best_move


# ===================== Opening Book =====================
# Botzone coordinates: RED back rank y=0, BLACK back rank y=9.
# RED key pieces: e0=king, h2/b2=cannons, h0/b0=knights, g0/c0=bishops, a0/i0=rooks.
# BLACK key pieces: e9=king, h7/b7=cannons, h9/b9=knights, g9/c9=bishops, a9/i9=rooks.
OPENING_BOOK = [
    # 1. 当头炮对屏风马
    ["h2","e2","h9","g7","h0","g2","b9","c7","a0","a1","i9","i8"],
    # 2. 飞相局
    ["g0","e2","b9","c7","h0","g2","h9","g7","a0","a1","i9","i8"],
    # 3. 仙人指路 (pawn then cannon, knight later)
    ["e3","e4","h9","g7","h2","e2","b9","c7","h0","g2","i9","i8"],
    # 4. 起马局 (use left cannon instead, right blocked by knight)
    ["h0","g2","h9","g7","b2","e2","b9","c7","a0","a1","i9","i8"],
    # 5. 过宫炮
    ["b2","e2","b9","c7","h0","g2","h9","g7","a0","a1","i9","i8"],
    # 6. 仕角炮
    ["b2","c2","h9","g7","h0","g2","i9","i8","c2","e2","b9","c7"],
    # 7. 上仕局
    ["d0","e1","h9","g7","h2","e2","b9","c7","h0","g2","i9","i8"],
    # 8. 金钩炮
    ["h2","f2","h9","g7","h0","g2","i9","i8","b2","e2","b9","c7"],
    # 9. 五七炮
    ["h2","e2","h9","g7","h0","g2","i9","i8","b2","c2","b7","c7"],
    # 10. 五六炮
    ["h2","e2","h9","g7","h0","g2","i9","i8","b2","d2","b7","d7"],
    # 11. 顺炮
    ["h2","e2","h7","e7","h0","g2","i9","i8","a0","a1","a9","a8"],
    # 12. 列炮
    ["h2","e2","h7","d7","h0","g2","h9","g7","a0","a1","i9","i8"],
    # 13. 过河车
    ["h2","e2","h9","g7","h0","g2","i9","i8","a0","a1","a9","a8"],
]


def _lookup_opening(our_color_is_red, history_moves):
    """Check opening book. history_moves: list of (src, tgt) string pairs played so far.
    Returns (src, tgt) string pair if found, None otherwise.
    """
    move_count = len(history_moves) // 2

    for opening in OPENING_BOOK:
        if move_count * 2 >= len(opening):
            continue
        match = True
        for i in range(move_count * 2):
            if history_moves[i] != opening[i]:
                match = False
                break
        if match:
            idx = move_count * 2
            return opening[idx], opening[idx + 1]
    return None


# ===================== Main =====================
def main():
    try:
        raw = sys.stdin.readline()
        data = json.loads(raw)
    except Exception:
        print(json.dumps({"response": {"source": "e0", "target": "e1"}}))
        return

    requests_list = data.get("requests", [])
    responses_list = data.get("responses", [])

    if not requests_list:
        print(json.dumps({"response": {"source": "e0", "target": "e1"}}))
        return

    # Determine our color
    first_src = requests_list[0].get("source", "")
    am_red = (first_src == "-1")

    # Replay board to current state
    board = Board()
    turn_id = len(responses_list)
    history_moves = []

    for i in range(turn_id):
        req_src = requests_list[i].get("source", "")
        req_tgt = requests_list[i].get("target", "")
        if req_src and req_src != "-1":
            x1, y1 = decode(req_src)
            x2, y2 = decode(req_tgt)
            if x1 >= 0:
                board.make_move(x1, y1, x2, y2)
                history_moves.append(req_src)
                history_moves.append(req_tgt)

        res_src = responses_list[i].get("source", "")
        res_tgt = responses_list[i].get("target", "")
        if res_src and res_src != "-1":
            x1, y1 = decode(res_src)
            x2, y2 = decode(res_tgt)
            if x1 >= 0:
                board.make_move(x1, y1, x2, y2)
                history_moves.append(res_src)
                history_moves.append(res_tgt)

    # Current opponent move
    last_req = requests_list[turn_id]
    last_src = last_req.get("source", "")
    last_tgt = last_req.get("target", "")
    if last_src and last_src != "-1":
        x1, y1 = decode(last_src)
        x2, y2 = decode(last_tgt)
        if x1 >= 0:
            board.make_move(x1, y1, x2, y2)
            history_moves.append(last_src)
            history_moves.append(last_tgt)

    # Opening book lookup
    if turn_id < 6:
        opening = _lookup_opening(am_red, history_moves)
        if opening:
            src_str, tgt_str = opening
            print(json.dumps({"response": {"source": src_str, "target": tgt_str}}))
            return

    # AI Search
    searcher = Searcher()
    best_move = searcher.search_root(board, am_red)

    if best_move is None:
        legal = get_legal_moves(board, am_red)
        if legal:
            best_move = legal[0]
        else:
            print(json.dumps({"response": {"source": "-1", "target": "-1"}}))
            return

    x1, y1, x2, y2 = best_move
    print(json.dumps({"response": {"source": encode(x1, y1), "target": encode(x2, y2)}}))


if __name__ == "__main__":
    main()
