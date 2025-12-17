import tkinter as tk
from tkinter import messagebox
import random

class Ship:
    def __init__(self, size):
        self.size = size
        self.hits = 0
        self.positions = []
        self.horizontal = True
    
    def is_sunk(self):
        return self.hits >= self.size

class Board:
    def __init__(self, size=10):
        self.size = size
        self.grid = [['~' for _ in range(size)] for _ in range(size)]
        self.ships = []
        self.ship_positions = set()
    
    def place_ship(self, ship, row, col, horizontal):
        positions = []
        if horizontal:
            if col + ship.size > self.size:
                return False
            for i in range(ship.size):
                if self.grid[row][col + i] != '~' or self.has_adjacent_ships(row, col + i):
                    return False
                positions.append((row, col + i))
        else:
            if row + ship.size > self.size:
                return False
            for i in range(ship.size):
                if self.grid[row + i][col] != '~' or self.has_adjacent_ships(row + i, col):
                    return False
                positions.append((row + i, col))
        
        for r, c in positions:
            self.grid[r][c] = 'S'
            self.ship_positions.add((r, c))
        
        ship.positions = positions
        ship.horizontal = horizontal
        self.ships.append(ship)
        return True
    
    def has_adjacent_ships(self, row, col):
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                r, c = row + dr, col + dc
                if 0 <= r < self.size and 0 <= c < self.size:
                    if self.grid[r][c] == 'S':
                        return True
        return False
    
    def mark_area_around_ship(self, ship):
        for row, col in ship.positions:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    r, c = row + dr, col + dc
                    if 0 <= r < self.size and 0 <= c < self.size:
                        if self.grid[r][c] == '~':
                            self.grid[r][c] = 'O'
    
    def receive_attack(self, row, col):
        if self.grid[row][col] == 'S':
            self.grid[row][col] = 'X'
            for ship in self.ships:
                if (row, col) in ship.positions:
                    ship.hits += 1
                    sunk = ship.is_sunk()
                    if sunk:
                        self.mark_area_around_ship(ship)
                    return True, sunk, ship
        elif self.grid[row][col] == '~':
            self.grid[row][col] = 'O'
        return False, False, None

class IntelligentBot:
    def __init__(self, board_size=10):
        self.board_size = board_size
        self.hits = []
        self.misses = set()
        self.potential_targets = []
        self.last_hit = None
        self.hunting_mode = False
    
    def place_ships_intelligently(self, ships):
        board = Board(self.board_size)
        for ship_size in sorted(ships, reverse=True):
            placed = False
            attempts = 0
            while not placed and attempts < 100:
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - 1)
                horizontal = random.choice([True, False])
                ship = Ship(ship_size)
                if board.place_ship(ship, row, col, horizontal):
                    placed = True
                attempts += 1
            
            if not placed:
                for r in range(self.board_size):
                    for c in range(self.board_size):
                        for hor in [True, False]:
                            ship = Ship(ship_size)
                            if board.place_ship(ship, r, c, hor):
                                placed = True
                                break
                        if placed:
                            break
                    if placed:
                        break
        return board
    
    def make_attack(self):
        if self.hunting_mode and self.last_hit:
            return self._hunt_around_hit()
        else:
            return self._probability_attack()
    
    def _hunt_around_hit(self):
        if not self.potential_targets:
            self._generate_potential_targets()
        
        if self.potential_targets:
            return self.potential_targets.pop(0)
        else:
            self.hunting_mode = False
            return self._probability_attack()
    
    def _generate_potential_targets(self):
        row, col = self.last_hit
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if (0 <= r < self.board_size and 0 <= c < self.board_size and
                    (r, c) not in self.misses and (r, c) not in self.hits):
                self.potential_targets.append((r, c))
    
    def _probability_attack(self):
        probability_map = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        
        for ship_size in [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]:
            for row in range(self.board_size):
                for col in range(self.board_size):
                    if col + ship_size <= self.board_size:
                        valid = True
                        for i in range(ship_size):
                            if (row, col + i) in self.misses:
                                valid = False
                                break
                        if valid:
                            for i in range(ship_size):
                                probability_map[row][col + i] += 1
                    
                    if row + ship_size <= self.board_size:
                        valid = True
                        for i in range(ship_size):
                            if (row + i, col) in self.misses:
                                valid = False
                                break
                        if valid:
                            for i in range(ship_size):
                                probability_map[row + i][col] += 1
        
        max_prob = -1
        best_moves = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in self.misses and (row, col) not in self.hits:
                    if probability_map[row][col] > max_prob:
                        max_prob = probability_map[row][col]
                        best_moves = [(row, col)]
                    elif probability_map[row][col] == max_prob:
                        best_moves.append((row, col))
        
        if best_moves:
            return random.choice(best_moves)
        else:
            return self._random_attack()
    
    def _random_attack(self):
        while True:
            row = random.randint(0, self.board_size - 1)
            col = random.randint(0, self.board_size - 1)
            if (row, col) not in self.misses and (row, col) not in self.hits:
                return (row, col)
    
    def record_result(self, row, col, hit, sunk):
        if hit:
            self.hits.append((row, col))
            self.last_hit = (row, col)
            self.hunting_mode = True
            
            if sunk:
                self.potential_targets = []
                self.hunting_mode = False
                for r, c in self.hits[-4:]:
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            nr, nc = r + dr, c + dc
                            if (0 <= nr < self.board_size and 0 <= nc < self.board_size and
                                    (nr, nc) not in self.hits):
                                self.misses.add((nr, nc))
        else:
            self.misses.add((row, col))
    
    def reset(self):
        self.hits = []
        self.misses = set()
        self.potential_targets = []
        self.last_hit = None
        self.hunting_mode = False

class BattleshipGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Морской Бой")
        self.root.geometry("800x600")
        
        self.board_size = 10
        self.ship_sizes = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
        
        self.player_board = Board(self.board_size)
        self.bot = IntelligentBot(self.board_size)
        self.bot_board = self.bot.place_ships_intelligently(self.ship_sizes)
        
        self.current_ship_index = 0
        self.placing_ships = True
        self.current_ship_horizontal = True
        self.game_over = False
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        boards_frame = tk.Frame(main_frame)
        boards_frame.pack(fill=tk.BOTH, expand=True)
        
        player_frame = tk.Frame(boards_frame)
        player_frame.pack(side=tk.LEFT, padx=10)
        tk.Label(player_frame, text="Ваше поле", font=("Arial", 12, "bold")).pack()
        
        self.player_canvas = tk.Canvas(player_frame, width=300, height=300, bg="white")
        self.player_canvas.pack()
        
        bot_frame = tk.Frame(boards_frame)
        bot_frame.pack(side=tk.RIGHT, padx=10)
        tk.Label(bot_frame, text="Поле противника", font=("Arial", 12, "bold")).pack()
        
        self.bot_canvas = tk.Canvas(bot_frame, width=300, height=300, bg="white")
        self.bot_canvas.pack()
        self.bot_canvas.bind("<Button-1>", self.on_bot_click)
        
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = tk.Label(control_frame, text="Расставьте ваши корабли", font=("Arial", 12))
        self.status_label.pack()
        
        rotate_button = tk.Button(control_frame, text="Повернуть корабль", command=self.rotate_ship)
        rotate_button.pack(side=tk.LEFT, padx=5)
        
        random_button = tk.Button(control_frame, text="Случайная расстановка", command=self.random_placement)
        random_button.pack(side=tk.LEFT, padx=5)
        
        new_game_button = tk.Button(control_frame, text="Новая игра", command=self.new_game)
        new_game_button.pack(side=tk.LEFT, padx=5)
        
        self.player_canvas.bind("<Motion>", self.on_player_mouse_move)
        self.player_canvas.bind("<Button-1>", self.on_player_click)
        
        self.draw_boards()
    
    def draw_boards(self):
        self.draw_board(self.player_canvas, self.player_board, True)
        self.draw_board(self.bot_canvas, self.bot_board, False)
    
    def draw_board(self, canvas, board, show_ships):
        canvas.delete("all")
        cell_size = 30
        
        for i in range(self.board_size + 1):
            canvas.create_line(i * cell_size, 0, i * cell_size, self.board_size * cell_size)
            canvas.create_line(0, i * cell_size, self.board_size * cell_size, i * cell_size)
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                x1 = col * cell_size
                y1 = row * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                
                cell = board.grid[row][col]
                
                if cell == '~':
                    canvas.create_rectangle(x1, y1, x2, y2, fill="lightblue", outline="gray")
                elif cell == 'S' and show_ships:
                    canvas.create_rectangle(x1, y1, x2, y2, fill="gray", outline="gray")
                elif cell == 'S' and not show_ships:
                    canvas.create_rectangle(x1, y1, x2, y2, fill="lightblue", outline="gray")
                elif cell == 'X':
                    canvas.create_rectangle(x1, y1, x2, y2, fill="red", outline="gray")
                    canvas.create_line(x1, y1, x2, y2, fill="darkred", width=2)
                    canvas.create_line(x2, y1, x1, y2, fill="darkred", width=2)
                elif cell == 'O':
                    canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="gray")
                    canvas.create_oval(x1 + 5, y1 + 5, x2 - 5, y2 - 5, fill="blue")
        
        for i in range(self.board_size):
            canvas.create_text(i * cell_size + cell_size // 2, -15, text=chr(65 + i))
            canvas.create_text(-15, i * cell_size + cell_size // 2, text=str(i + 1))
    
    def on_player_mouse_move(self, event):
        if not self.placing_ships or self.current_ship_index >= len(self.ship_sizes):
            return
        
        self.draw_boards()
        cell_size = 30
        col = event.x // cell_size
        row = event.y // cell_size
        
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            ship_size = self.ship_sizes[self.current_ship_index]
            color = "lightgreen"
            
            can_place = True
            if self.current_ship_horizontal:
                if col + ship_size > self.board_size:
                    can_place = False
                else:
                    for i in range(ship_size):
                        if (self.player_board.grid[row][col + i] != '~' or
                                self.player_board.has_adjacent_ships(row, col + i)):
                            can_place = False
                            break
            else:
                if row + ship_size > self.board_size:
                    can_place = False
                else:
                    for i in range(ship_size):
                        if (self.player_board.grid[row + i][col] != '~' or
                                self.player_board.has_adjacent_ships(row + i, col)):
                            can_place = False
                            break
            
            if not can_place:
                color = "lightcoral"
            
            if self.current_ship_horizontal:
                if col + ship_size <= self.board_size:
                    for i in range(ship_size):
                        x1 = (col + i) * cell_size
                        y1 = row * cell_size
                        x2 = x1 + cell_size
                        y2 = y1 + cell_size
                        self.player_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")
            else:
                if row + ship_size <= self.board_size:
                    for i in range(ship_size):
                        x1 = col * cell_size
                        y1 = (row + i) * cell_size
                        x2 = x1 + cell_size
                        y2 = y1 + cell_size
                        self.player_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")
    
    def on_player_click(self, event):
        if not self.placing_ships or self.current_ship_index >= len(self.ship_sizes):
            return
        
        cell_size = 30
        col = event.x // cell_size
        row = event.y // cell_size
        
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            ship_size = self.ship_sizes[self.current_ship_index]
            ship = Ship(ship_size)
            
            if self.player_board.place_ship(ship, row, col, self.current_ship_horizontal):
                self.current_ship_index += 1
                if self.current_ship_index >= len(self.ship_sizes):
                    self.placing_ships = False
                    self.status_label.config(text="Игра началась! Атакуйте поле противника!")
                else:
                    next_ship_size = self.ship_sizes[self.current_ship_index]
                    self.status_label.config(text=f"Разместите корабль размером {next_ship_size}")
                self.draw_boards()
            else:
                self.status_label.config(text="Невозможно разместить корабль здесь!")
    
    def rotate_ship(self):
        self.current_ship_horizontal = not self.current_ship_horizontal
        self.draw_boards()
    
    def random_placement(self):
        self.player_board = Board(self.board_size)
        self.current_ship_index = 0
        
        for ship_size in self.ship_sizes:
            placed = False
            attempts = 0
            while not placed and attempts < 100:
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - 1)
                horizontal = random.choice([True, False])
                ship = Ship(ship_size)
                if self.player_board.place_ship(ship, row, col, horizontal):
                    placed = True
                attempts += 1
        
        self.placing_ships = False
        self.status_label.config(text="Игра началась! Атакуйте поле противника!")
        self.draw_boards()
    
    def new_game(self):
        self.player_board = Board(self.board_size)
        self.bot.reset()
        self.bot_board = self.bot.place_ships_intelligently(self.ship_sizes)
        
        self.current_ship_index = 0
        self.placing_ships = True
        self.current_ship_horizontal = True
        self.game_over = False
        
        self.status_label.config(text="Расставьте ваши корабли")
        self.draw_boards()
    
    def on_bot_click(self, event):
        if self.placing_ships or self.game_over:
            return
        
        cell_size = 30
        col = event.x // cell_size
        row = event.y // cell_size
        
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            if self.bot_board.grid[row][col] in ['X', 'O']:
                messagebox.showwarning("Внимание", "Вы уже стреляли в эту клетку!")
                return
            
            hit, sunk, ship = self.bot_board.receive_attack(row, col)
            
            if hit:
                if sunk:
                    self.status_label.config(text=f"Попадание! Корабль размером {ship.size} потоплен!")
                else:
                    self.status_label.config(text="Попадание!")
                
                if self.check_win(self.bot_board):
                    self.game_over = True
                    messagebox.showinfo("Победа!", "Вы победили!")
                    self.status_label.config(text="Вы победили! Нажмите 'Новая игра' для повторной игры.")
                    return
            else:
                self.status_label.config(text="Промах!")
            
            self.draw_boards()
            self.root.after(1000, self.bot_turn)
    
    def bot_turn(self):
        if self.game_over:
            return
        
        row, col = self.bot.make_attack()
        hit, sunk, ship = self.player_board.receive_attack(row, col)
        self.bot.record_result(row, col, hit, sunk)
        
        if hit:
            if sunk:
                self.status_label.config(text=f"Бот попал! Ваш корабль размером {ship.size} потоплен!")
            else:
                self.status_label.config(text="Бот попал в вашу клетку!")
            
            if self.check_win(self.player_board):
                self.game_over = True
                messagebox.showinfo("Поражение", "Бот победил!")
                self.status_label.config(text="Бот победил! Нажмите 'Новая игра' для повторной игры.")
                return
        else:
            self.status_label.config(text="Бот промахнулся!")
        
        self.draw_boards()
    
    def check_win(self, board):
        for ship in board.ships:
            if not ship.is_sunk():
                return False
        return True
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    game = BattleshipGame()
    game.run()