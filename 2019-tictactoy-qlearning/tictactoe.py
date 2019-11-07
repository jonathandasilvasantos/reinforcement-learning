import pygame, sys
from pygame.locals import *
import numpy as np
from random import choice
import math
from random import randint
from tqdm import tqdm

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

class Game:

    def __init__(self):
        pygame.init()
        self.windowSurface = pygame.display.set_mode((500, 400), 0, 32)
        pygame.display.set_caption('Tic Tac Toe: RL')
        self.basicFont = pygame.font.SysFont(None, 48)
        spacing = 50
        cy = self.windowSurface.get_rect().centery - spacing
        cx = self.windowSurface.get_rect().centerx - spacing
        self.positions = []
        for y in range(0, 3):
            for x in range(0, 3):
                position = (cx + (x * spacing), cy + (y * spacing))
                self.positions.append(position)

    def display(self, board, scoreboard):
        text = self.basicFont.render(scoreboard, True, WHITE, BLACK)
        textRect = text.get_rect()
        textRect.centerx = self.windowSurface.get_rect().centerx
        textRect.centery = self.windowSurface.get_rect().centery
        textRect.y += 150
        self.windowSurface.fill(BLACK)

        pygame.draw.rect(self.windowSurface, BLACK,
                         (textRect.left - 20, textRect.top - 20, textRect.width + 40, textRect.height + 40))
        for i, p in enumerate(self.positions):
            if board[i] == 2:
                pygame.draw.circle(self.windowSurface, WHITE, (p[0], p[1]), 20, 0)
            if board[i] == 1:
                pygame.draw.line(self.windowSurface, WHITE, (p[0] - 20, p[1] - 20), (p[0] + 20, p[1] + 20), 4)
                pygame.draw.line(self.windowSurface, WHITE, (p[0] + 20, p[1] - 20), (p[0] - 20, p[1] + 20), 4)

        self.windowSurface.blit(text, textRect)
        pygame.display.update()


class Board:


    def __init__(self, b):
        self.current_board = b

    def a2b(self, board_vector):
        result = 0
        for i, p in enumerate(board_vector):
            mask = p << (i * 2)
            result |= mask
        return result

    def b2a(self):
        result = []
        mask = 0b11
        for i in range(0,9):
            v = ((self.current_board << 16-(i*2))  >> 16) & mask
            result.append(v)
        return result

    def is_terminal(self):
        b = self.b2a()
        if 0 not in b: return -1
        if b[0] == b[1] == b[2] != 0: return b[0]  # -
        if b[3] == b[4] == b[5] != 0: return b[3]  # -
        if b[6] == b[7] == b[8] != 0: return b[6]  # -
        if b[0] == b[3] == b[6] != 0: return b[0]  # |
        if b[1] == b[4] == b[7] != 0: return b[1]  # |
        if b[2] == b[5] == b[8] != 0: return b[2]  # |
        if b[0] == b[4] == b[8] != 0: return b[0]  # X
        if b[6] == b[4] == b[2] != 0: return b[6]  # X
        return 0

    def make_a_move(self, action, player_id):
        b = self.b2a()
        b[action] = player_id
        self.current_board = self.a2b(b)

    def free_positions(self):
        b = self.b2a()
        positions = []
        for i, p in enumerate(b):
            if p == 0: positions.append(i)
        return positions

    def reset(self):
        self.current_board = self.a2b([0,0,0,0,0,0,0,0,0])


class Player:
    def __init__(self, player_id):
        self.player_id = player_id
        self.moves_in_a_match = []
        self.knowledge = dict()
        self.score = 0
        self.gama = 0.95
        self.learning_rate = 0.05
        self.dummy = False

    def action_to_vector(self, board, action, reward):
        result = [0,0,0,0,0,0,0,0,0]
        for index, value in enumerate(Board(board).b2a()):
            if value != 0:
                result[index] = -math.inf
        result[action] = reward
        return result


    def clear_moves(self):
        self.moves_in_a_match = []


    def update_rewards(self, reward):
        self.moves_in_a_match.reverse()
        next_max = None
        for board,  action in self.moves_in_a_match:
            q = self.knowledge[board]

            if next_max is None:
                self.knowledge[board][action] = reward
            else:
                self.knowledge[board][action] = self.knowledge[board][action] * \
                                (1.0 - self.learning_rate) + self.learning_rate * self.gama * next_max
            next_max = max(self.knowledge[board])



    def predict_move(self, board):
        legal_moves = board.free_positions()

        if board.current_board in self.knowledge:
        	qvals = self.knowledge[board.current_board]
        else:
        	qvals = [0 if i in legal_moves else float('-inf') for i in range(9)]

        self.knowledge[board.current_board] = qvals

        if not self.dummy:
            max_val = max(self.knowledge[board.current_board])
            max_actions = [i for i, v in enumerate(qvals) if v == max_val]
            action = choice(max_actions)
        else:
        	action = choice([i for i in range(9) if i in legal_moves])

        self.moves_in_a_match.append( [board.current_board, action] )
        return action


def selfplay(player1, player2, board):

    current_player = player1.player_id
    while board.is_terminal() == 0:


        if current_player == player1.player_id:
            action = player1.predict_move(board)
            board.make_a_move(action, player1.player_id)
            current_player = player2.player_id
        else:
            action = player2.predict_move(board)
            board.make_a_move(action, player2.player_id)
            current_player = player1.player_id
    result = board.is_terminal()
    if result == player1.player_id:
        player1.update_rewards(1)
        player2.update_rewards(-1)
    if result == player2.player_id:
        player2.update_rewards(1)
        player1.update_rewards(-1)
    if result == -1:
        player1.update_rewards(0)
        player2.update_rewards(0)

    player1.clear_moves()
    player2.clear_moves()
    board.reset()





def run(game, board, player1, player2):
    kreturn = False
    turn = 1
    draw = 0

    scoreboard = "SPACE to autoplay"
    auto = False
    while True:
        game.display(board.b2a(), scoreboard)
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                if event.key == pygame.K_SPACE:
                    if auto:
                        auto = False
                    else:
                        auto = True
                if event.key == pygame.K_RETURN:
                    kreturn = True
                    auto = False


        if auto or kreturn:
            kreturn = False
            if board.is_terminal() != 0:
                if player1.player_id == board.is_terminal():
                    player1.score += 1
                    player1.update_rewards(1)
                    player2.update_rewards(-1)
                elif player2.player_id == board.is_terminal():
                    player2.score += 1
                    player2.update_rewards(1)
                    player1.update_rewards(-1)
                else:
                    draw += 1
                    player1.update_rewards(0)
                    player2.update_rewards(0)
                scoreboard = str(player1.score) + " x " + str(player2.score) + " : " + str(draw)
                board.reset()
                player1.clear_moves()
                player2.clear_moves()
                # The first player isn't deterministic
                turn = 1

            if turn == 1:
                action = player1.predict_move(board)
                board.make_a_move(action, player1.player_id)
                turn = 2
            else:
                action = player2.predict_move(board)
                board.make_a_move(action, player2.player_id)
                turn = 1



if __name__ == '__main__':

    gameboard = Board(0)
    player1 = Player(1)
    player2 = Player(2)
    player2.dummy = True

    p1 = "AI"
    p2 = "AI"
    if player1.dummy: p1 = "Random"
    if player2.dummy: p2 = "Random"
    print("Training " + p1 + " vs " + p2)

    for i in tqdm(range(10000)):
        selfplay(player1, player2, gameboard)

    print("Press RETURN to go turn by turn")
    print("Press SPACE to turn autoplay ON / OFF")
    print("Press ESC to exit")
    game = Game()

    player1.dummy = False
    player2.dummy = False
    run(game, gameboard, player1, player2)

    pygame.quit()
    sys.exit()

