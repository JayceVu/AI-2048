import pygame
from random import randint, choice
import os
import colors as c

WIDTH, HEIGHT = 400, 500
FPS = 60

pygame.init()
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('2048 Game')

HINT_ICON_SIZE = (40, 40)
HINT_ICON_POS = (WIDTH - HINT_ICON_SIZE[0] - 10, 25)  # Vị trí của biểu tượng gợi ý
hint_icon = pygame.transform.scale(pygame.image.load(os.path.join('image', 'suggest.png')), HINT_ICON_SIZE)

SCORE_HEIGHT = 50
GRID_TOP_MARGIN = SCORE_HEIGHT + 60  # Đệm cho lưới trò chơi

class Game:
    def __init__(self, window):
        self.window = window
        self.matrix = [[0] * 4 for _ in range(4)]
        self.cells = []
        self.score = [0, 0]
        self.fontEngine = pygame.font.SysFont(c.SCORE_LABEL_FONT, 45)
        self.over = [False, False]
        self.startGame()

    def startGame(self):
        row, col = randint(0, 3), randint(0, 3)
        self.matrix[row][col] = 2
        while self.matrix[row][col] != 0:
            row, col = randint(0, 3), randint(0, 3)
        self.matrix[row][col] = 2
        self.updateCells()

    def updateCells(self):
        self.cells = []
        for i in range(4):
            row = []
            for j in range(4):
                rect = pygame.Rect(10 + j * 100, GRID_TOP_MARGIN + i * 100, 80, 80)
                textSurface, textRect = None, None
                if (x := self.matrix[i][j]) != 0:
                    textSurface = self.fontEngine.render(str(x), True, c.CELL_NUMBER_COLORS[x])
                    textRect = textSurface.get_rect()
                    textRect.center = rect.center
                row.append({
                    "rect": rect,
                    "textRect": textRect,
                    "textSurface": textSurface
                })
            self.cells.append(row)

        scoreSurface = pygame.font.SysFont(c.SCORE_LABEL_FONT, 50).render('Score : ', True, (0, 0, 0))
        scoreRect = scoreSurface.get_rect()
        scoreRect.top = 25
        self.score[1] = [scoreSurface, scoreRect]

    def addNewTile(self):
        row, col = randint(0, 3), randint(0, 3)
        while self.matrix[row][col] != 0:
            row, col = randint(0, 3), randint(0, 3)
        self.matrix[row][col] = choice([2, 2, 2, 2, 4])

    def horMoveExists(self):
        for i in range(4):
            for j in range(3):
                if self.matrix[i][j + 1] == self.matrix[i][j]:
                    return True
        return False

    def verMoveExists(self):
        for i in range(3):
            for j in range(4):
                if self.matrix[i + 1][j] == self.matrix[i][j]:
                    return True
        return False

    def gameOver(self):
        if any(2048 in row for row in self.matrix):
            self.over = [True, True]
        if not any(0 in row for row in self.matrix) and not (self.horMoveExists() or self.verMoveExists()):
            self.over = [True, False]
        return self.over

    def updateTiles(self):
        self.updateCells()

    def stack(self):
        new_matrix = [[0] * 4 for _ in range(4)]
        for i in range(4):
            position = 0
            for j in range(4):
                if self.matrix[i][j] != 0:
                    new_matrix[i][position] = self.matrix[i][j]
                    position += 1
        self.matrix = new_matrix

    def combine(self):
        for i in range(4):
            for j in range(3):
                x = self.matrix[i][j]
                if x != 0 and x == self.matrix[i][j + 1]:
                    self.matrix[i][j] *= 2
                    self.matrix[i][j + 1] = 0
                    self.score[0] += self.matrix[i][j]
        self.stack()  # Di chuyển các ô sau khi hợp nhất

    def reverse(self):
        self.matrix = [row[::-1] for row in self.matrix]

    def transpose(self):
        self.matrix = [[self.matrix[j][i] for j in range(4)] for i in range(4)]

    def scs(self):
        oldmatrix = [row[:] for row in self.matrix]  # Sao chép ma trận
        self.stack()
        self.combine()
        self.stack()
        return oldmatrix

    def aug(self):
        self.addNewTile()
        self.updateTiles()
        self.gameOver()

    def left(self):
        oldmatrix = self.scs()
        if oldmatrix != self.matrix:  # Chỉ thêm ô mới nếu có di chuyển
            self.aug()

    def right(self):
        oldmatrix = self.matrix
        self.reverse()
        self.scs()
        self.reverse()
        if oldmatrix != self.matrix:
            self.aug()

    def up(self):
        oldmatrix = self.matrix
        self.transpose()
        self.scs()
        self.transpose()
        if oldmatrix != self.matrix:
            self.aug()

    def down(self):
        oldmatrix = self.matrix
        self.transpose()
        self.reverse()
        self.scs()
        self.reverse()
        self.transpose()
        if oldmatrix != self.matrix:
            self.aug()

    def reset(self):
        self.__init__(self.window)

    def expectimax(self, depth, player):
        if depth == 0:
            return self.evaluate_heuristics()

        game_over_state = self.gameOver()
        if game_over_state[0]:
            return self.evaluate_heuristics()

        if player:
            max_eval = float('-inf')
            for move in [self.left, self.right, self.up, self.down]:
                old_matrix = [row[:] for row in self.matrix]
                move()
                eval = self.expectimax(depth - 1, False)
                self.matrix = old_matrix
                self.updateTiles()  # Cập nhật ô sau khi khôi phục ma trận
                max_eval = max(max_eval, eval)
            return max_eval
        else:
            total_eval = 0
            empty_tiles = [(i, j) for i in range(4) for j in range(4) if self.matrix[i][j] == 0]
            if not empty_tiles:
                return 0
            for (i, j) in empty_tiles:
                for new_value in [2, 4]:
                    self.matrix[i][j] = new_value
                    total_eval += self.expectimax(depth - 1, True)
                    self.matrix[i][j] = 0
            return total_eval / len(empty_tiles)

    def evaluate_heuristics(self):
        empty_cells = sum(row.count(0) for row in self.matrix)

        # Monotonicity: Ưu tiên nếu hàng hoặc cột có giá trị giảm dần hoặc tăng dần
        monotonicity_score = 0
        for i in range(4):
            for j in range(3):
                if self.matrix[i][j] > self.matrix[i][j + 1]:  # Hàng
                    monotonicity_score += 1
                if self.matrix[j][i] > self.matrix[j + 1][i]:  # Cột
                    monotonicity_score += 1

        # Corner tile bonus: Ưu tiên khi ô lớn nhất nằm ở góc
        max_tile = max(max(row) for row in self.matrix)
        corner_bonus = 0
        if self.matrix[0][0] == max_tile or self.matrix[0][3] == max_tile or \
                self.matrix[3][0] == max_tile or self.matrix[3][3] == max_tile:
            corner_bonus = max_tile * 0.5  # Tăng thêm điểm cho ô lớn nhất nằm ở góc

        # Score tổng hợp: Số điểm hiện tại + ô trống + monotonicity + corner bonus
        return self.score[0] + empty_cells * 100 + monotonicity_score * 10 + corner_bonus


def draw(window, matrix, cells, score, over, hint_icon):
    window.fill(c.GRID_COLOR)
    window.blit(score[1][0], score[1][1])

    scoreSurface = pygame.font.SysFont(c.SCORE_LABEL_FONT, 50).render(str(score[0]), True, (0, 0, 0))
    scoreRect = scoreSurface.get_rect()
    scoreRect.top = 25
    scoreRect.left = score[1][1].right + 10
    window.blit(scoreSurface, scoreRect)

    for i in range(4):
        for j in range(4):
            cell = cells[i][j]
            if (x := matrix[i][j]) != 0:
                pygame.draw.rect(window, c.CELL_COLORS[x], cell['rect'])
                if cell['textSurface']:
                    window.blit(cell['textSurface'], cell['textRect'])
            else:
                pygame.draw.rect(window, c.EMPTY_CELL_COLOR, cell['rect'])

    window.blit(hint_icon, HINT_ICON_POS)

    if over[0]:
        message = '2048 Completed. Ctrl + q to reset' if over[1] else 'No moves left. Ctrl + q to reset'
        gameOverSurface = pygame.font.SysFont(c.SCORE_LABEL_FONT, 25).render(message, True, (0, 0, 0))
        gameOverRect = gameOverSurface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        window.blit(gameOverSurface, gameOverRect)

    pygame.display.update()

def draw(window, matrix, cells, score, over, hint_icon, best_move_direction=None):
        window.fill(c.GRID_COLOR)
        window.blit(score[1][0], score[1][1])

        scoreSurface = pygame.font.SysFont(c.SCORE_LABEL_FONT, 50).render(str(score[0]), True, (0, 0, 0))
        scoreRect = scoreSurface.get_rect()
        scoreRect.top = 25
        scoreRect.left = score[1][1].right + 10
        window.blit(scoreSurface, scoreRect)

        for i in range(4):
            for j in range(4):
                cell = cells[i][j]
                if (x := matrix[i][j]) != 0:
                    pygame.draw.rect(window, c.CELL_COLORS[x], cell['rect'])
                    if cell['textSurface']:
                        window.blit(cell['textSurface'], cell['textRect'])
                else:
                    pygame.draw.rect(window, c.EMPTY_CELL_COLOR, cell['rect'])

        window.blit(hint_icon, HINT_ICON_POS)

        # Hiển thị mũi tên gợi ý
        if best_move_direction:
            if best_move_direction == "left":
                pygame.draw.polygon(window, (255, 0, 0),
                                    [(20, HEIGHT // 2), (50, HEIGHT // 2 - 10), (50, HEIGHT // 2 + 10)])
            elif best_move_direction == "right":
                pygame.draw.polygon(window, (255, 0, 0), [(WIDTH - 20, HEIGHT // 2), (WIDTH - 50, HEIGHT // 2 - 10),
                                                          (WIDTH - 50, HEIGHT // 2 + 10)])
            elif best_move_direction == "up":
                pygame.draw.polygon(window, (255, 0, 0),
                                    [(WIDTH // 2, 20), (WIDTH // 2 - 10, 50), (WIDTH // 2 + 10, 50)])
            elif best_move_direction == "down":
                pygame.draw.polygon(window, (255, 0, 0), [(WIDTH // 2, HEIGHT - 20), (WIDTH // 2 - 10, HEIGHT - 50),
                                                          (WIDTH // 2 + 10, HEIGHT - 50)])

        if over[0]:
            message = '2048 Completed. Ctrl + q to reset' if over[1] else 'Game Over!!'
            gameOverSurface = pygame.font.SysFont(c.SCORE_LABEL_FONT, 25).render(message, True, (0, 0, 0))
            gameOverRect = gameOverSurface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            window.blit(gameOverSurface, gameOverRect)

        pygame.display.update()


def main():
    running = True
    clock = pygame.time.Clock()
    game = Game(window)
    best_move_direction = None  # Biến để lưu hướng di chuyển tốt nhất

    while running:
        clock.tick(FPS)

        # Truyền best_move_direction vào hàm draw
        draw(window, game.matrix, game.cells, game.score, game.over, hint_icon, best_move_direction)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    game.left()
                    best_move_direction = None  # Reset hướng gợi ý
                if event.key == pygame.K_RIGHT:
                    game.right()
                    best_move_direction = None  # Reset hướng gợi ý
                if event.key == pygame.K_UP:
                    game.up()
                    best_move_direction = None  # Reset hướng gợi ý
                if event.key == pygame.K_DOWN:
                    game.down()
                    best_move_direction = None  # Reset hướng gợi ý

                if event.key == pygame.K_q and pygame.key.get_mods() & pygame.KMOD_CTRL and game.over:
                    game.reset()
                    best_move_direction = None  # Reset gợi ý khi bắt đầu lại trò chơi

            if event.type == pygame.MOUSEBUTTONUP:
                mouse_pos = event.pos
                # Kiểm tra xem chuột có nhấn vào biểu tượng gợi ý không
                if HINT_ICON_POS[0] <= mouse_pos[0] <= HINT_ICON_POS[0] + HINT_ICON_SIZE[0] and \
                        HINT_ICON_POS[1] <= mouse_pos[1] <= HINT_ICON_POS[1] + HINT_ICON_SIZE[1]:

                    # Lưu trạng thái game
                    game_over_state = game.gameOver()
                    if not game_over_state[0]:  # Nếu game chưa kết thúc
                        best_move_direction = None
                        best_score = float('-inf')

                        # Duyệt qua từng hướng di chuyển khả thi
                        for move_func, direction in [(game.left, "left"), (game.right, "right"),
                                                     (game.up, "up"), (game.down, "down")]:
                            old_matrix = [row[:] for row in game.matrix]  # Sao chép ma trận hiện tại
                            old_score = game.score[0]  # Sao chép điểm số hiện tại

                            move_func()  # Thực hiện di chuyển
                            score = game.expectimax(2, True)  # Đánh giá điểm số của trạng thái mới

                            # Cập nhật hướng di chuyển tốt nhất nếu tìm thấy điểm số cao hơn
                            if score > best_score:
                                best_score = score
                                best_move_direction = direction  # Cập nhật hướng di chuyển tốt nhất

                            # Khôi phục ma trận và điểm số về trạng thái cũ
                            game.matrix = old_matrix
                            game.score[0] = old_score  # Khôi phục điểm số
                            game.updateTiles()  # Cập nhật lại các ô sau khi khôi phục ma trận


if __name__ == "__main__":
    main()
