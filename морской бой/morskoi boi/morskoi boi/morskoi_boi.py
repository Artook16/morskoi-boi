import tkinter as tk
from tkinter import messagebox
import random

BOARD_SIZE = 10
SHIP_SIZES = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
CELL_SIZE = 30
COLORS = {'water': 'lightblue', 'ship': 'gray', 'hit': 'red', 'miss': 'white', 'highlight': 'lightgreen'}

class Ship:
    def __init__(self, size):
        self.size = size
        self.hits = 0
        self.positions = []
    
    def is_sunk(self):
        return self.hits >= self.size

class Board:
    def __init__(self):
        self.grid = [['~'] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.ships = []
    
    def can_place_ship(self, row, col, size, horizontal):
        if horizontal:
            if col + size > BOARD_SIZE: return False
            for i in range(size):
                if not self.is_cell_empty(row, col + i): return False
        else:
            if row + size > BOARD_SIZE: return False
            for i in range(size):
                if not self.is_cell_empty(row + i, col): return False
        return True
    
    def is_cell_empty(self, row, col):
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE): return False
        if self.grid[row][col] != '~': return False
        return not any(self.grid[r][c] == 'S' for dr in [-1,0,1] for dc in [-1,0,1]
                      for r in [row+dr] for c in [col+dc] if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE)
    
    def place_ship(self, row, col, size, horizontal):
        if not self.can_place_ship(row, col, size, horizontal): return False
        
        ship = Ship(size)
        for i in range(size):
            r, c = (row, col + i) if horizontal else (row + i, col)
            self.grid[r][c] = 'S'
            ship.positions.append((r, c))
        
        self.ships.append(ship)
        return True
    
    def receive_attack(self, row, col):
        if self.grid[row][col] == 'S':
            self.grid[row][col] = 'X'
            for ship in self.ships:
                if (row, col) in ship.positions:
                    ship.hits += 1
                    if ship.is_sunk():
                        self.mark_around_ship(ship)
                    return True, ship
        elif self.grid[row][col] == '~':
            self.grid[row][col] = 'O'
        return False, None
    
    def mark_around_ship(self, ship):
        for row, col in ship.positions:
            for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                r, c = row + dr, col + dc
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.grid[r][c] == '~':
                    self.grid[r][c] = 'O'

class Bot:
    def __init__(self):
        self.hits = set()
        self.misses = set()
        self.targets = []
    
    def place_ships(self):
        board = Board()
        for size in sorted(SHIP_SIZES, reverse=True):
            placed = False
            for _ in range(100):
                row, col = random.randint(0, BOARD_SIZE-1), random.randint(0, BOARD_SIZE-1)
                horizontal = random.choice([True, False])
                if board.place_ship(row, col, size, horizontal):
                    placed = True
                    break
            if not placed:
                for r in range(BOARD_SIZE):
                    for c in range(BOARD_SIZE):
                        for hor in [True, False]:
                            if board.place_ship(r, c, size, hor):
                                placed = True
                                break
                        if placed: break
                    if placed: break
        return board
    
    def make_attack(self):
        if self.targets:
            return self.targets.pop()
        
        probability_map = [[0]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        for size in SHIP_SIZES:
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if col + size <= BOARD_SIZE and all((row, col+i) not in self.misses for i in range(size)):
                        for i in range(size):
                            probability_map[row][col+i] += 1
                    if row + size <= BOARD_SIZE and all((row+i, col) not in self.misses for i in range(size)):
                        for i in range(size):
                            probability_map[row+i][col] += 1
        
        max_prob = max(probability_map[r][c] for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
                      if (r,c) not in self.hits | self.misses)
        best_moves = [(r,c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
                     if (r,c) not in self.hits | self.misses and probability_map[r][c] == max_prob]
        
        return random.choice(best_moves) if best_moves else self.random_move()
    
    def random_move(self):
        while True:
            row, col = random.randint(0, BOARD_SIZE-1), random.randint(0, BOARD_SIZE-1)
            if (row, col) not in self.hits | self.misses:
                return (row, col)
    
    def record_result(self, row, col, hit, sunk=False):
        if hit:
            self.hits.add((row, col))
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                r, c = row + dr, col + dc
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and (r,c) not in self.hits | self.misses:
                    self.targets.append((r, c))
            if sunk:
                for r, c in self.hits:
                    for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                            self.misses.add((nr, nc))
                self.targets = []
        else:
            self.misses.add((row, col))
    
    def reset(self):
        self.hits.clear()
        self.misses.clear()
        self.targets.clear()

class Game:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Морской Бой")
        self.root.geometry("800x650")  # Увеличена высота для размещения кнопок
        
        self.player_board = Board()
        self.bot = Bot()
        self.bot_board = self.bot.place_ships()
        
        self.current_ship = 0
        self.placing_ships = True
        self.horizontal = True
        self.game_over = False
        
        self.setup_ui()
    
    def setup_ui(self):
        # Создаем основной контейнер для всей игры
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Верхняя часть с надписями
        top_frame = tk.Frame(main_container)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = tk.Label(top_frame, text="Расставьте ваши корабли", 
                                    font=("Arial", 12))
        self.status_label.pack()
        
        # Средняя часть с полями
        boards_frame = tk.Frame(main_container)
        boards_frame.pack(fill=tk.BOTH, expand=True)
        
        # Левое поле игрока
        left_frame = tk.Frame(boards_frame)
        left_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0, 20))
        tk.Label(left_frame, text="Ваше поле", font=("Arial", 11)).pack()
        self.player_canvas = tk.Canvas(left_frame, width=BOARD_SIZE*CELL_SIZE, 
                                      height=BOARD_SIZE*CELL_SIZE, bg="white")
        self.player_canvas.pack()
        
        # Правое поле бота
        right_frame = tk.Frame(boards_frame)
        right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        tk.Label(right_frame, text="Поле противника", font=("Arial", 11)).pack()
        self.bot_canvas = tk.Canvas(right_frame, width=BOARD_SIZE*CELL_SIZE, 
                                   height=BOARD_SIZE*CELL_SIZE, bg="white")
        self.bot_canvas.pack()
        self.bot_canvas.bind("<Button-1>", self.on_attack)
        
        # Нижняя часть с кнопками в левом нижнем углу
        bottom_frame = tk.Frame(main_container)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        # Создаем фрейм для кнопок и размещаем его слева
        button_frame = tk.Frame(bottom_frame)
        button_frame.pack(side=tk.LEFT)
        
        # Кнопки с увеличенным размером
        buttons = [
            ("Повернуть корабль", self.rotate_ship),
            ("Случайная расстановка", self.random_placement),
            ("Новая игра", self.new_game)
        ]
        
        for text, command in buttons:
            btn = tk.Button(button_frame, text=text, command=command, 
                           font=("Arial", 9), width=25, height=1)
            btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Привязка событий
        self.player_canvas.bind("<Motion>", self.on_mouse_move)
        self.player_canvas.bind("<Button-1>", self.on_place_ship)
    
    def draw_board(self, canvas, board, show_ships=True):
        canvas.delete("all")
        
        for i in range(BOARD_SIZE + 1):
            canvas.create_line(i*CELL_SIZE, 0, i*CELL_SIZE, BOARD_SIZE*CELL_SIZE)
            canvas.create_line(0, i*CELL_SIZE, BOARD_SIZE*CELL_SIZE, i*CELL_SIZE)
        
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                x1, y1 = col*CELL_SIZE, row*CELL_SIZE
                x2, y2 = x1+CELL_SIZE, y1+CELL_SIZE
                
                cell = board.grid[row][col]
                fill_color = COLORS['water']
                
                if cell == 'S':
                    fill_color = COLORS['ship'] if show_ships else COLORS['water']
                elif cell == 'X':
                    fill_color = COLORS['hit']
                elif cell == 'O':
                    fill_color = COLORS['miss']
                
                canvas.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline="gray")
                
                if cell == 'X':
                    canvas.create_line(x1, y1, x2, y2, fill="darkred", width=2)
                    canvas.create_line(x2, y1, x1, y2, fill="darkred", width=2)
                elif cell == 'O':
                    canvas.create_oval(x1+5, y1+5, x2-5, y2-5, fill="blue")
    
    def highlight_ship(self, row, col, size, can_place):
        color = COLORS['highlight'] if can_place else 'lightcoral'
        if self.horizontal and col + size <= BOARD_SIZE:
            for i in range(size):
                x1, y1 = (col + i)*CELL_SIZE, row*CELL_SIZE
                self.player_canvas.create_rectangle(x1, y1, x1+CELL_SIZE, y1+CELL_SIZE, fill=color, outline="black")
        elif not self.horizontal and row + size <= BOARD_SIZE:
            for i in range(size):
                x1, y1 = col*CELL_SIZE, (row + i)*CELL_SIZE
                self.player_canvas.create_rectangle(x1, y1, x1+CELL_SIZE, y1+CELL_SIZE, fill=color, outline="black")
    
    def on_mouse_move(self, event):
        if not self.placing_ships or self.current_ship >= len(SHIP_SIZES):
            return
        
        self.draw_board(self.player_canvas, self.player_board)
        row, col = event.y//CELL_SIZE, event.x//CELL_SIZE
        
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            size = SHIP_SIZES[self.current_ship]
            can_place = self.player_board.can_place_ship(row, col, size, self.horizontal)
            self.highlight_ship(row, col, size, can_place)
    
    def on_place_ship(self, event):
        if not self.placing_ships or self.current_ship >= len(SHIP_SIZES):
            return
        
        row, col = event.y//CELL_SIZE, event.x//CELL_SIZE
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            size = SHIP_SIZES[self.current_ship]
            if self.player_board.place_ship(row, col, size, self.horizontal):
                self.current_ship += 1
                if self.current_ship >= len(SHIP_SIZES):
                    self.placing_ships = False
                    self.status_label.config(text="Игра началась! Атакуйте поле противника!")
                else:
                    self.status_label.config(text=f"Разместите корабль размером {SHIP_SIZES[self.current_ship]}")
                self.draw_board(self.player_canvas, self.player_board)
    
    def rotate_ship(self):
        self.horizontal = not self.horizontal
        self.draw_board(self.player_canvas, self.player_board)
    
    def random_placement(self):
        self.player_board = Board()
        for size in SHIP_SIZES:
            for _ in range(100):
                row, col = random.randint(0, BOARD_SIZE-1), random.randint(0, BOARD_SIZE-1)
                if self.player_board.place_ship(row, col, size, random.choice([True, False])):
                    break
        
        self.placing_ships = False
        self.status_label.config(text="Игра началась! Атакуйте поле противника!")
        self.draw_board(self.player_canvas, self.player_board)
    
    def new_game(self):
        self.player_board = Board()
        self.bot.reset()
        self.bot_board = self.bot.place_ships()
        
        self.current_ship = 0
        self.placing_ships = True
        self.horizontal = True
        self.game_over = False
        
        self.status_label.config(text="Расставьте ваши корабли")
        self.draw_board(self.player_canvas, self.player_board)
        self.draw_board(self.bot_canvas, self.bot_board, False)
    
    def on_attack(self, event):
        if self.placing_ships or self.game_over:
            return
        
        row, col = event.y//CELL_SIZE, event.x//CELL_SIZE
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return
        
        if self.bot_board.grid[row][col] in ['X', 'O']:
            messagebox.showwarning("Внимание", "Вы уже стреляли в эту клетку!")
            return
        
        hit, ship = self.bot_board.receive_attack(row, col)
        
        if hit:
            msg = f"Попадание! Корабль размером {ship.size} потоплен!" if ship.is_sunk() else "Попадание!"
            self.status_label.config(text=msg)
            
            if all(s.is_sunk() for s in self.bot_board.ships):
                self.game_over = True
                messagebox.showinfo("Победа!", "Вы победили!")
                self.status_label.config(text="Вы победили! Нажмите 'Новая игра' для повторной игры.")
                return
        else:
            self.status_label.config(text="Промах!")
        
        self.draw_board(self.bot_canvas, self.bot_board, False)
        self.root.after(1000, self.bot_turn)
    
    def bot_turn(self):
        if self.game_over:
            return
        
        row, col = self.bot.make_attack()
        hit, ship = self.player_board.receive_attack(row, col)
        self.bot.record_result(row, col, hit, ship.is_sunk() if ship else False)
        
        if hit:
            msg = f"Бот попал! Ваш корабль размером {ship.size} потоплен!" if ship.is_sunk() else "Бот попал!"
            self.status_label.config(text=msg)
            
            if all(s.is_sunk() for s in self.player_board.ships):
                self.game_over = True
                messagebox.showinfo("Поражение", "Бот победил!")
                self.status_label.config(text="Бот победил! Нажмите 'Новая игра' для повторной игры.")
                return
        else:
            self.status_label.config(text="Бот промахнулся!")
        
        self.draw_board(self.player_canvas, self.player_board)
    
    def run(self):
        self.draw_board(self.player_canvas, self.player_board)
        self.draw_board(self.bot_canvas, self.bot_board, False)
        self.root.mainloop()

if __name__ == "__main__":
    Game().run()
