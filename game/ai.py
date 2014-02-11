import datetime
import sys

__author__ = 'bengt'

from game.settings import *


class AlphaBetaPruner(object):
    """Alpha-Beta Pruning algorithm."""
    def __init__(self, mutex, duration, pieces, first_player, second_player):
        self.mutex = mutex

        self.board = 0
        self.move = 1
        self.white = 2
        self.black = 3

        self.duration = duration
        self.lifetime = None

        self.infinity = 1.0e400

        self.first_player, self.second_player = (self.white, self.black) \
            if first_player == WHITE else (self.black, self.white)

        self.state = self.make_state(pieces)

    def make_state(self, pieces):
        results = {BOARD: self.board, MOVE: self.board, WHITE: self.white, BLACK: self.black}
        return self.first_player, [results[p.get_state()] for p in pieces]

    def alpha_beta_search(self):
        """Returns an action"""
        player, state = self.state
        self.lifetime = datetime.datetime.now() + datetime.timedelta(seconds=self.duration)
        depth = 0
        fn = lambda action: self.min_value(depth, self.next_state(self.state, action), -self.infinity,
                                           self.infinity)
        maxfn = lambda value: value[0]
        actions = self.actions(self.state)
        moves = [(fn(action), action) for action in actions]
        
        if len(moves) == 0:
            raise NoMovesError
        
        return max(moves, key=maxfn)[1]

    def max_value(self, depth, current_state, alpha, beta):
        player, state = current_state
        if self.cutoff_test(current_state, depth):
            return self.evaluation(current_state, self.first_player)

        value = -self.infinity

        actions = self.actions(current_state)
        for action in actions:
            value = max([value, self.min_value(depth + 1, self.next_state(current_state, action), alpha, beta)])
            if value >= beta:
                return value
            alpha = max(alpha, value)

        return value

    def min_value(self, depth, state, alpha, beta):
        if self.cutoff_test(state, depth):
            return self.evaluation(state, self.second_player)

        value = self.infinity

        actions = self.actions(state)
        for action in actions:
            value = min([value, self.max_value(depth + 1, self.next_state(state, action), alpha, beta)])
            if value <= alpha:
                return value
            beta = min([beta, value])

        return value

    def evaluation(self, current_state, player_to_check):
        """
        Returns 1 for a win for 'player'
        Returns 0 for a draw for 'player'
        Returns -1 for a lose for 'player'
        """
        player_state, state   = current_state
        player = player_to_check
        opponent = self.opponent(player)

        # count_eval stands for the player with the most pieces next turn
        moves           = self.get_moves(player, opponent, state)
        player_pieces    = len([p for p in state if p == player])
        opponent_pieces    = len([p for p in state if p == opponent])
        count_eval     = 1 if player_pieces > opponent_pieces else \
                         0 if player_pieces == opponent_pieces else \
                        -1

        moves_player    = moves
        moves_oppponent = self.get_moves(opponent, player, state)
        move_eval       = 1 if moves_player > moves_oppponent else \
                          0 if moves_player == moves_oppponent else \
                         -1

        corners_player  = (state[0] == player) +  \
                          (state[7] == player) +  \
                          (state[56] == player) + \
                          (state[63] == player)
        corners_opponent= -1*(state[0] == opponent) +  \
                          (state[7] == opponent) +  \
                          (state[56] == opponent) + \
                          (state[63] == opponent)
        corners_eval = corners_player + corners_opponent

        eval = count_eval * 2 + move_eval * 1.5 + corners_eval * 0.5

        return eval

    def terminal_test(self, state):
        return len(self.get_moves(state[0], self.opponent(state[0]), state[1])) == 0 # No moves in the state...

    def actions(self, current_state):
        """Returns """
        player, state = current_state
        return self.get_moves(player, self.opponent(player), state)

    def opponent(self, player):
        return self.second_player if player is self.first_player else self.first_player

    def next_state(self, current_state, action):
        player, state = current_state
        opponent = self.opponent(player)

        xx, yy = action
        state[xx + (yy * WIDTH)] = player
        for d in DIRECTIONS:
            tile = xx + (yy * WIDTH) + d
            if tile < 0 or tile >= 64:
                continue

            while state[tile] != self.board:
                state[tile] = player
                tile += d
                if tile < 0 or tile >= WIDTH * HEIGHT:
                    tile -= d
                    break

        return opponent, state

    def get_moves(self, player, opponent, state):
        """ Returns a generator of (x,y) coordinates.
        """
        moves = [self.mark_move(player, opponent, tile, state, d)
                 for tile in range(WIDTH*HEIGHT)
                 for d in DIRECTIONS
                 if not outside_board(tile, d) and state[tile] == player]

        return [(x,y) for found, x,y, tile in moves if found]


    def mark_move(self, player, opponent, tile, pieces, direction):
        if not outside_board(tile, direction):
            tile += direction
        else:
            return False, int(tile % WIDTH), int(tile / HEIGHT), tile

        if pieces[tile] == opponent:
            while pieces[tile] == opponent:
                if outside_board(tile, direction):
                    break
                else:
                    tile += direction

            if pieces[tile] == self.board:
                return True, int(tile % WIDTH), int(tile / HEIGHT), tile

        return False, int(tile % WIDTH), int(tile / HEIGHT), tile

    def cutoff_test(self, state, depth):
        return depth > 1000 or datetime.datetime.now() > self.lifetime


