"""
Production-Ready Tic-Tac-Toe — Design Pattern Architecture
===========================================================

Patterns used:
  - MVC       : Board (Model), ConsoleView (View), GameController (Controller)
  - Strategy  : Player interface → HumanPlayer, MinimaxAIPlayer
  - Observer  : EventBus notifies listeners on game events (move, win, draw)
  - Factory   : PlayerFactory creates the right Player subclass
  - State     : GameStatus enum drives controller flow
  - Enum/VO   : Mark (X/O) and Cell are value objects — no raw strings in logic
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Callable, Optional


# ─────────────────────────────────────────────
# Value Objects
# ─────────────────────────────────────────────

class Mark(Enum):
    X = "X"
    O = "O"

    def opponent(self) -> "Mark":
        return Mark.O if self is Mark.X else Mark.X

    def __str__(self) -> str:
        return self.value


class GameStatus(Enum):
    PLAYING = auto()
    WON     = auto()
    DRAW    = auto()


# ─────────────────────────────────────────────
# Model — Board
# ─────────────────────────────────────────────

_WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
    (0, 4, 8), (2, 4, 6),             # diagonals
]


class Board:
    """
    Pure data model. Knows nothing about I/O or players.
    Exposes only immutable queries and a single mutating operation (apply_move).
    """

    SIZE = 9

    def __init__(self) -> None:
        self._cells: list[Optional[Mark]] = [None] * self.SIZE

    # ── queries ──────────────────────────────

    def cell(self, index: int) -> Optional[Mark]:
        return self._cells[index]

    def is_empty(self, index: int) -> bool:
        return self._cells[index] is None

    def empty_cells(self) -> list[int]:
        return [i for i in range(self.SIZE) if self._cells[i] is None]

    def winner(self) -> Optional[Mark]:
        for a, b, c in _WIN_LINES:
            if (self._cells[a] is not None
                    and self._cells[a] == self._cells[b] == self._cells[c]):
                return self._cells[a]
        return None

    def is_full(self) -> bool:
        return all(c is not None for c in self._cells)

    def status(self) -> GameStatus:
        if self.winner():
            return GameStatus.WON
        if self.is_full():
            return GameStatus.DRAW
        return GameStatus.PLAYING

    def snapshot(self) -> list[Optional[Mark]]:
        """Return a copy of cells (used by AI look-ahead)."""
        return list(self._cells)

    # ── mutation ─────────────────────────────

    def apply_move(self, index: int, mark: Mark) -> None:
        if not (0 <= index < self.SIZE):
            raise ValueError(f"Index {index} out of range 0–{self.SIZE - 1}.")
        if not self.is_empty(index):
            raise ValueError(f"Cell {index} is already occupied.")
        self._cells[index] = mark

    def reset(self) -> None:
        self._cells = [None] * self.SIZE


# ─────────────────────────────────────────────
# Observer — EventBus
# ─────────────────────────────────────────────

class GameEvent(Enum):
    MOVE_MADE  = auto()
    GAME_WON   = auto()
    GAME_DRAWN = auto()
    GAME_RESET = auto()


EventPayload = dict
Listener = Callable[[EventPayload], None]


class EventBus:
    """
    Lightweight publish/subscribe hub.
    Components register listeners; the controller publishes events.
    """

    def __init__(self) -> None:
        self._listeners: dict[GameEvent, list[Listener]] = {e: [] for e in GameEvent}

    def subscribe(self, event: GameEvent, listener: Listener) -> None:
        self._listeners[event].append(listener)

    def publish(self, event: GameEvent, payload: EventPayload | None = None) -> None:
        for listener in self._listeners[event]:
            listener(payload or {})


# ─────────────────────────────────────────────
# Strategy — Player interface + implementations
# ─────────────────────────────────────────────

class Player(ABC):
    """Strategy interface. Each subclass encapsulates how a move is chosen."""

    def __init__(self, mark: Mark, name: str) -> None:
        self.mark = mark
        self.name = name

    @abstractmethod
    def choose_move(self, board: Board) -> int:
        ...

    def __str__(self) -> str:
        return f"{self.name} ({self.mark})"


class HumanPlayer(Player):
    """Reads a move from stdin."""

    def choose_move(self, board: Board) -> int:
        available = board.empty_cells()
        while True:
            try:
                raw = input(f"  {self} — enter position (0-8): ").strip()
                index = int(raw)
                if index in available:
                    return index
                print(f"  Cell {index} is taken or invalid. Available: {available}")
            except (ValueError, EOFError):
                print("  Please enter a number between 0 and 8.")


class Difficulty(Enum):
    EASY   = "easy"    # fully random moves
    MEDIUM = "medium"  # 50% chance of optimal move, else random
    HARD   = "hard"    # unbeatable Minimax


class MinimaxAIPlayer(Player):
    """
    Bot player with three difficulty levels.

    - EASY   : picks a random empty cell — beatable every time.
    - MEDIUM : flips a coin; heads → best Minimax move, tails → random.
    - HARD   : full Minimax search — cannot be beaten, only drawn.

    Interaction contract:  GameController calls choose_move(board) → int.
    The bot reads board.snapshot() (a copy) so it never mutates game state.
    """

    def __init__(self, mark: Mark, name: str, difficulty: Difficulty = Difficulty.HARD) -> None:
        super().__init__(mark, name)
        self.difficulty = difficulty

    def choose_move(self, board: Board) -> int:
        import random
        empties = board.empty_cells()

        if self.difficulty is Difficulty.EASY:
            return random.choice(empties)

        if self.difficulty is Difficulty.MEDIUM:
            # 50% of the time play optimally, otherwise random
            if random.random() < 0.5:
                return random.choice(empties)

        # HARD (and the optimal branch of MEDIUM): full Minimax
        return self._best_move(board)

    def _best_move(self, board: Board) -> int:
        best_score = -math.inf
        best_move  = board.empty_cells()[0]
        cells      = board.snapshot()

        for move in board.empty_cells():
            cells[move] = self.mark
            score = self._minimax(cells, depth=0, is_maximising=False)
            cells[move] = None
            if score > best_score:
                best_score = score
                best_move  = move
        return best_move

    def _minimax(self, cells: list, depth: int, is_maximising: bool) -> int:
        result = self._terminal(cells)
        if result is not None:
            return result

        if is_maximising:
            best = -math.inf
            for i in range(Board.SIZE):
                if cells[i] is None:
                    cells[i] = self.mark
                    best = max(best, self._minimax(cells, depth + 1, False))
                    cells[i] = None
            return best
        else:
            best = math.inf
            opponent = self.mark.opponent()
            for i in range(Board.SIZE):
                if cells[i] is None:
                    cells[i] = opponent
                    best = min(best, self._minimax(cells, depth + 1, True))
                    cells[i] = None
            return best

    def _terminal(self, cells: list) -> Optional[int]:
        for a, b, c in _WIN_LINES:
            if cells[a] is not None and cells[a] == cells[b] == cells[c]:
                return 1 if cells[a] == self.mark else -1
        if all(c is not None for c in cells):
            return 0
        return None


# ─────────────────────────────────────────────
# Factory — PlayerFactory
# ─────────────────────────────────────────────

class PlayerType(Enum):
    HUMAN  = "human"
    AI     = "ai"


class PlayerFactory:
    """
    Centralises player construction.
    Add new player types here without touching the controller.
    """

    @staticmethod
    def create(
        player_type: PlayerType,
        mark: Mark,
        name: str,
        difficulty: Difficulty = Difficulty.HARD,
    ) -> Player:
        if player_type is PlayerType.HUMAN:
            return HumanPlayer(mark, name)
        if player_type is PlayerType.AI:
            return MinimaxAIPlayer(mark, name, difficulty)
        raise ValueError(f"Unknown player type: {player_type}")


# ─────────────────────────────────────────────
# View — ConsoleView
# ─────────────────────────────────────────────

class GameView:
    """
    Handles all output. Subscribes to EventBus so the controller
    never calls print() directly — keeping View and Controller decoupled.
    """

    _CELL_LABEL = {None: ".", Mark.X: "X", Mark.O: "O"}

    def __init__(self, board: Board, bus: EventBus) -> None:
        self._board = board
        bus.subscribe(GameEvent.MOVE_MADE,  self._on_move)
        bus.subscribe(GameEvent.GAME_WON,   self._on_win)
        bus.subscribe(GameEvent.GAME_DRAWN, self._on_draw)
        bus.subscribe(GameEvent.GAME_RESET, self._on_reset)

    # ── EventBus listeners ────────────────────

    def _on_move(self, payload: EventPayload) -> None:
        self.render_board()

    def _on_win(self, payload: EventPayload) -> None:
        print(f"\n  *** {payload['winner']} wins! Congratulations! ***\n")

    def _on_draw(self, _: EventPayload) -> None:
        print("\n  *** It's a draw! Well played by both sides. ***\n")

    def _on_reset(self, _: EventPayload) -> None:
        print("\n  Board reset. Starting new game...\n")

    # ── rendering ─────────────────────────────

    def render_board(self) -> None:
        b = self._board
        lbl = self._CELL_LABEL
        rows = [
            f"  {lbl[b.cell(0)]} | {lbl[b.cell(1)]} | {lbl[b.cell(2)]}",
            "  --+---+--",
            f"  {lbl[b.cell(3)]} | {lbl[b.cell(4)]} | {lbl[b.cell(5)]}",
            "  --+---+--",
            f"  {lbl[b.cell(6)]} | {lbl[b.cell(7)]} | {lbl[b.cell(8)]}",
        ]
        print("\n" + "\n".join(rows) + "\n")

    def show_position_guide(self) -> None:
        guide = "  0 | 1 | 2\n  --+---+--\n  3 | 4 | 5\n  --+---+--\n  6 | 7 | 8"
        print("\n  Position reference:\n" + guide + "\n")

    @staticmethod
    def ask_play_again() -> bool:
        answer = input("  Play again? (y/n): ").strip().lower()
        return answer in ("y", "yes")


# ─────────────────────────────────────────────
# Controller — GameController
# ─────────────────────────────────────────────

class GameController:
    """
    Orchestrates the game loop.
    Depends on abstractions (Player, Board, EventBus) — not on concrete I/O.
    """

    def __init__(
        self,
        board: Board,
        view: GameView,
        bus: EventBus,
        player_x: Player,
        player_o: Player,
    ) -> None:
        self._board    = board
        self._view     = view
        self._bus      = bus
        self._players  = {Mark.X: player_x, Mark.O: player_o}
        self._current  = Mark.X

    # ── public API ────────────────────────────

    def run(self) -> None:
        self._view.show_position_guide()
        while True:
            self._play_round()
            if not self._view.ask_play_again():
                print("\n  Thanks for playing!\n")
                break
            self._reset()

    # ── internals ─────────────────────────────

    def _play_round(self) -> None:
        self._board.reset()
        self._current = Mark.X

        while self._board.status() is GameStatus.PLAYING:
            self._take_turn()

        status = self._board.status()
        if status is GameStatus.WON:
            winner_player = self._players[self._board.winner()]
            self._bus.publish(GameEvent.GAME_WON, {"winner": winner_player})
        else:
            self._bus.publish(GameEvent.GAME_DRAWN)

    def _take_turn(self) -> None:
        player = self._players[self._current]
        move   = player.choose_move(self._board)
        self._board.apply_move(move, self._current)
        self._bus.publish(GameEvent.MOVE_MADE, {"player": player, "move": move})
        self._current = self._current.opponent()

    def _reset(self) -> None:
        self._board.reset()
        self._current = Mark.X
        self._bus.publish(GameEvent.GAME_RESET)


# ─────────────────────────────────────────────
# Entry Point — wires everything together
# ─────────────────────────────────────────────

def build_game(mode: str = "hvh", difficulty: Difficulty = Difficulty.HARD) -> GameController:
    """
    Factory function — constructs the full object graph.

    mode:       "hvh" = Human vs Human
                "hva" = Human vs AI
                "ava" = AI vs AI
    difficulty: EASY / MEDIUM / HARD  (only affects AI players)
    """
    board = Board()
    bus   = EventBus()
    view  = GameView(board, bus)

    modes = {
        "hvh": (PlayerType.HUMAN, PlayerType.HUMAN),
        "hva": (PlayerType.HUMAN, PlayerType.AI),
        "ava": (PlayerType.AI,    PlayerType.AI),
    }
    if mode not in modes:
        raise ValueError(f"Unknown mode '{mode}'. Choose from: {list(modes)}")

    type_x, type_o = modes[mode]
    ai_name = f"AI [{difficulty.value.upper()}]"
    player_x = PlayerFactory.create(type_x, Mark.X, "Player X", difficulty)
    player_o = PlayerFactory.create(type_o, Mark.O, "Player O" if mode == "hvh" else ai_name, difficulty)

    return GameController(board, view, bus, player_x, player_o)


def main() -> None:
    print("\n  === Tic-Tac-Toe ===")
    print("  Modes: hvh (Human vs Human)  hva (Human vs AI)  ava (AI vs AI)")
    mode = input("  Select mode [hvh]: ").strip().lower() or "hvh"

    difficulty = Difficulty.HARD
    if "a" in mode:  # only ask difficulty when there's a bot
        print("  Difficulty: easy  medium  hard")
        raw = input("  Select difficulty [hard]: ").strip().lower() or "hard"
        difficulty = Difficulty(raw) if raw in ("easy", "medium", "hard") else Difficulty.HARD

    controller = build_game(mode, difficulty)
    controller.run()


if __name__ == "__main__":
    main()
