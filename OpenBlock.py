import tkinter as tk
from tkinter import messagebox
import random
import time

# --- 1. КОНСТАНТЫ И НАСТРОЙКИ ---
GRID_SIZE = 10
CELL_SIZE = 35  # Размер ячейки
HEIGHT = GRID_SIZE * CELL_SIZE
SCORE_HEIGHT = 40
PIECE_AREA_HEIGHT = 150
WIDTH = GRID_SIZE * CELL_SIZE
TOTAL_HEIGHT = HEIGHT + SCORE_HEIGHT + PIECE_AREA_HEIGHT
ANIMATION_DURATION = 150  # мс

# Цвета (Темная тема)
BG_COLOR = '#121212' 
SURFACE_COLOR = '#1e1e1e'
GRID_COLOR = '#2c2c2c'
LINE_COLOR = '#444444'

# Цвета для блоков
BLOCK_COLORS = {
    1: '#4CAF50', 2: '#2196F3', 3: '#FF9800',
    4: '#E91E63', 5: '#9C27B0', 6: '#00BCD4',
}

# Определение фигур (без изменений)
PIECE_TEMPLATES = [
    [[[1]], 1, 1], [[[1, 1, 1]], 2, 3], [[[1], [1], [1]], 3, 3],
    [[[1, 1], [1, 1]], 4, 4], [[[1, 0], [1, 1]], 5, 3], 
    [[[0, 1, 0], [1, 1, 1]], 6, 4],
    [[[1, 1, 1, 1]], 1, 4], # 4-блок
    [[[1, 0], [1, 0], [1, 0], [1, 0]], 2, 4], # 4-блок вертикальный
]


# --- 2. ГЛАВНЫЙ КЛАСС ИГРЫ ---

class BlockBlastGame:
    def __init__(self, root):
        self.root = root
        root.title("Block Blast Clone (Полная реализация)")
        root.geometry(f"{WIDTH}x{TOTAL_HEIGHT}")
        root.resizable(False, False)
        root.configure(bg=BG_COLOR)
        
        self.score = 0
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.pieces = []
        self.MINI_CELL_SIZE = CELL_SIZE // 2
        self.last_cleared_count = 0  # Для комбо
        
        # Переменные для Drag-and-Drop
        self.dragging = False
        self.active_piece_data = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_clone_ids = []  # ID блоков клона (в натуральную величину)

        self._setup_ui()
        self.init_game()

    def _setup_ui(self):
        """Создание элементов интерфейса."""
        
        self.score_label = tk.Label(self.root, text=f"Счет: {self.score}", 
                                    font=("Arial", 16, "bold"), bg=BG_COLOR, fg="white")
        self.score_label.pack(pady=5)

        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT + PIECE_AREA_HEIGHT, 
                                bg=SURFACE_COLOR, highlightthickness=0)
        self.canvas.pack()

        self.restart_button = tk.Button(self.root, text="Новая игра", command=self.init_game, 
                                        bg="#00BCD4", fg=BG_COLOR, font=("Arial", 12, "bold"))
        self.restart_button.pack(pady=10)

        # Привязка событий мыши
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_move)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)

    def init_game(self):
        """Инициализация или сброс игры."""
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.score = 0
        self.last_cleared_count = 0
        self.score_label.config(text=f"Счет: {self.score}")
        self.canvas.delete("all")
        
        self.draw_grid_lines()
        self.generate_pieces()
        self.draw_pieces_selection()

    def draw_grid_lines(self):
        """Отрисовка сетки и пустых ячеек."""
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=GRID_COLOR, outline=LINE_COLOR, width=3)
        
        for i in range(1, GRID_SIZE):
            self.canvas.create_line(i * CELL_SIZE, 0, i * CELL_SIZE, HEIGHT, fill=LINE_COLOR)
            self.canvas.create_line(0, i * CELL_SIZE, WIDTH, i * CELL_SIZE, fill=LINE_COLOR)

    def draw_game_blocks(self):
        """Отрисовка занятых блоков на сетке."""
        self.canvas.delete("placed_block")
        
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                color_index = self.grid[r][c]
                if color_index != 0:
                    color = BLOCK_COLORS[color_index]
                    x1 = c * CELL_SIZE
                    y1 = r * CELL_SIZE
                    x2 = x1 + CELL_SIZE
                    y2 = y1 + CELL_SIZE
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=LINE_COLOR, tags="placed_block")
        
        # Проверка конца игры после любой отрисовки/очистки
        self.check_game_over()

    def generate_pieces(self):
        """Генерирует 3 случайные фигуры."""
        self.pieces = []
        indices = random.sample(range(len(PIECE_TEMPLATES)), 3)
        for i, idx in enumerate(indices):
            template = PIECE_TEMPLATES[idx]
            self.pieces.append({
                'id': i,
                'shape': template[0],
                'color': template[1],
                'points': template[2],
                'placed': False,
            })
        
    def draw_pieces_selection(self):
        """Отрисовка доступных фигур в области выбора."""
        self.canvas.delete("piece") 
        
        selection_y_offset = HEIGHT + 20
        piece_x_offset = 20

        for piece in self.pieces:
            if piece['placed']:
                continue
            
            piece['canvas_ids'] = []
            shape = piece['shape']
            color = BLOCK_COLORS[piece['color']]
            
            cols = len(shape[0])
            rows = len(shape)
            
            # Отрисовываем блоки фигуры
            for r in range(rows):
                for c in range(cols):
                    if shape[r][c] == 1:
                        x1 = piece_x_offset + c * self.MINI_CELL_SIZE
                        y1 = selection_y_offset + r * self.MINI_CELL_SIZE
                        x2 = x1 + self.MINI_CELL_SIZE
                        y2 = y1 + self.MINI_CELL_SIZE
                        
                        block_id = self.canvas.create_rectangle(x1, y1, x2, y2, 
                                                               fill=color, outline=LINE_COLOR, 
                                                               tags=("piece", f"piece_{piece['id']}"))
                        piece['canvas_ids'].append(block_id)

            piece_x_offset += cols * self.MINI_CELL_SIZE + 30
            
            # Сохраняем начальные координаты для возврата фигуры
            piece['start_x'] = piece_x_offset - (cols * self.MINI_CELL_SIZE + 30)
            piece['start_y'] = selection_y_offset
            
            # Устанавливаем смещение для центрирования фигуры под курсором
            piece['center_offset_x'] = cols * self.MINI_CELL_SIZE / 2
            piece['center_offset_y'] = rows * self.MINI_CELL_SIZE / 2
            
            
    # --- 3. ИГРОВАЯ ЛОГИКА ---
    
    def can_place_piece(self, piece, start_r, start_c):
        """Проверяет возможность размещения фигуры на сетке."""
        shape = piece['shape']
        rows = len(shape)
        cols = len(shape[0])

        for r in range(rows):
            for c in range(cols):
                if shape[r][c] == 1:
                    grid_r, grid_c = start_r + r, start_c + c

                    # 1. Проверка границ
                    if not (0 <= grid_r < GRID_SIZE and 0 <= grid_c < GRID_SIZE):
                        return False
                    # 2. Проверка на занятость ячейки
                    if self.grid[grid_r][grid_c] != 0:
                        return False
        return True

    def place_piece(self, piece, start_r, start_c):
        """Размещает фигуру на сетке и начисляет очки."""
        shape = piece['shape']
        for r in range(len(shape)):
            for c in range(len(shape[0])):
                if shape[r][c] == 1:
                    self.grid[start_r + r][start_c + c] = piece['color']
        
        self.score += piece['points']
        self.score_label.config(text=f"Счет: {self.score}")
        piece['placed'] = True

    def check_clear(self):
        """Проверяет и запускает анимацию очистки линий."""
        
        cells_to_clear = []
        cleared_count = 0

        # 1. Проверка строк
        for r in range(GRID_SIZE):
            if all(self.grid[r]):
                cleared_count += 1
                for c in range(GRID_SIZE):
                    cells_to_clear.append((r, c))

        # 2. Проверка столбцов
        for c in range(GRID_SIZE):
            if all(self.grid[r][c] != 0 for r in range(GRID_SIZE)):
                cleared_count += 1
                for r in range(GRID_SIZE):
                    if (r, c) not in cells_to_clear: # Исключаем дублирование
                        cells_to_clear.append((r, c))

        if cleared_count > 0:
            self.animate_and_clear(cells_to_clear, cleared_count)
            return True
        else:
            self.last_cleared_count = 0
            return False

    def animate_and_clear(self, cells_to_clear, lines_cleared):
        """Анимация исчезновения и начисление комбо-очков."""
        
        # 1. Комбо-бонус
        combo_bonus = 0
        if self.last_cleared_count > 0:
            combo_bonus = lines_cleared * (self.last_cleared_count + 1) * 5
            self._show_combo_text(lines_cleared)
        
        self.last_cleared_count = lines_cleared
        self.score += lines_cleared * 10 + combo_bonus
        self.score_label.config(text=f"Счет: {self.score}")
        
        # 2. Визуальная анимация (уменьшение и исчезновение)
        
        def fade_step(step=10):
            if step > 0:
                self.canvas.delete("clearing") # Удаляем предыдущий кадр
                
                for r, c in cells_to_clear:
                    color = BLOCK_COLORS[self.grid[r][c]]
                    
                    # Уменьшение размера и смещение для центрирования
                    scale = step / 10
                    dx = (CELL_SIZE * (1 - scale)) / 2
                    
                    x1 = c * CELL_SIZE + dx
                    y1 = r * CELL_SIZE + dx
                    x2 = (c + 1) * CELL_SIZE - dx
                    y2 = (r + 1) * CELL_SIZE - dx
                    
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=LINE_COLOR, tags="clearing")

                self.root.after(ANIMATION_DURATION // 10, lambda: fade_step(step - 1))
            else:
                # 3. Фактическая очистка после анимации
                self.canvas.delete("clearing")
                for r, c in cells_to_clear:
                    self.grid[r][c] = 0
                
                self.draw_game_blocks()
                self.check_game_over()

        fade_step()

    def _show_combo_text(self, lines_cleared):
        """Отображает текст комбо по центру сетки."""
        combo_text = f"x{lines_cleared} КОМБО!" if lines_cleared > 1 else "ЛИНИЯ!"
        
        text_id = self.canvas.create_text(WIDTH / 2, HEIGHT / 2, text=combo_text, 
                                          font=("Arial", 30, "bold"), fill="#FFD700", tags="combo_text")
        
        # Анимация исчезновения текста
        def fade_text(opacity=10):
            if opacity > 0:
                # В Tkinter нет прямой прозрачности, только удаление
                self.root.after(100, lambda: fade_text(opacity - 1))
            else:
                self.canvas.delete(text_id)
                
        self.root.after(100, lambda: fade_text())


    def check_game_over(self):
        """Проверяет, можно ли разместить оставшиеся фигуры."""
        remaining_pieces = [p for p in self.pieces if not p['placed']]
        
        # Если фигуры закончились, генерируем новые
        if not remaining_pieces:
            self.generate_pieces()
            self.draw_pieces_selection()
            remaining_pieces = self.pieces

        # Проверка, можно ли разместить хотя бы одну из оставшихся
        for piece in remaining_pieces:
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    if self.can_place_piece(piece, r, c):
                        return # Игра продолжается

        # Если ни одна фигура не может быть размещена
        self.show_game_over()
        
    def show_game_over(self):
        """Отображает окно Game Over."""
        messagebox.showinfo("ИГРА ОКОНЧЕНА", f"Ваш финальный счет: {self.score}")
        self.init_game() # Начинаем новую игру


    # --- 4. РЕАЛИЗАЦИЯ DRAG-AND-DROP (с изменением размера) ---

    def start_drag(self, event):
        """Начало перетаскивания: клонируем фигуру в полный размер."""
        
        item_id = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(item_id)
        
        if "piece" in tags:
            piece_tag = next((tag for tag in tags if tag.startswith("piece_")), None)
            piece_index = int(piece_tag.split('_')[1])
            
            self.active_piece_data = next((p for p in self.pieces if p['id'] == piece_index and not p['placed']), None)
            
            if self.active_piece_data:
                self.dragging = True
                self.drag_start_x, self.drag_start_y = event.x, event.y
                
                # 1. Скрываем мини-фигуру
                for block_id in self.active_piece_data['canvas_ids']:
                    self.canvas.itemconfig(block_id, state='hidden')
                
                # 2. Создаем клон в натуральную величину (CELL_SIZE)
                self.drag_clone_ids = self._create_full_size_clone(event.x, event.y)
                
    def _create_full_size_clone(self, center_x, center_y):
        """Создает временную фигуру в натуральную величину по центру курсора."""
        
        piece = self.active_piece_data
        shape = piece['shape']
        color = BLOCK_COLORS[piece['color']]
        clone_ids = []
        
        cols = len(shape[0])
        rows = len(shape)
        
        # Корректировка, чтобы центр фигуры был под курсором
        start_x = center_x - (cols * CELL_SIZE / 2)
        start_y = center_y - (rows * CELL_SIZE / 2)

        for r in range(rows):
            for c in range(cols):
                if shape[r][c] == 1:
                    x1 = start_x + c * CELL_SIZE
                    y1 = start_y + r * CELL_SIZE
                    x2 = x1 + CELL_SIZE
                    y2 = y1 + CELL_SIZE
                    
                    block_id = self.canvas.create_rectangle(x1, y1, x2, y2, 
                                                           fill=color, outline="#333", width=2,
                                                           tags="drag_clone")
                    clone_ids.append(block_id)
        
        return clone_ids

    def drag_move(self, event):
        """Перемещение клона за курсором."""
        if self.dragging and self.active_piece_data:
            
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            # Перемещаем все блоки клона
            for block_id in self.drag_clone_ids:
                self.canvas.move(block_id, dx, dy)
            
            self.drag_start_x, self.drag_start_y = event.x, event.y
            
            # Опционально: Добавление визуальной обратной связи для валидной позиции
            # (опущено для краткости, но это место для анимации подсветки)

    def end_drag(self, event):
        """Завершение перетаскивания: проверка размещения на сетке."""
        if self.dragging and self.active_piece_data:
            
            # 1. Получаем координаты первого блока клона (верхний левый угол фигуры)
            first_block_coords = self.canvas.coords(self.drag_clone_ids[0])
            clone_x1, clone_y1 = first_block_coords[0], first_block_coords[1]
            
            # 2. Определяем ячейку сетки (row, col) для верхнего левого угла
            # Используем округление для привязки к сетке
            start_c = round(clone_x1 / CELL_SIZE)
            start_r = round(clone_y1 / CELL_SIZE)
            
            is_placed = False

            # 3. Проверка размещения
            if self.can_place_piece(self.active_piece_data, start_r, start_c):
                self.place_piece(self.active_piece_data, start_r, start_c)
                is_placed = True
            
            # 4. Удаление клона
            self.canvas.delete("drag_clone")
            self.drag_clone_ids = []
            
            if is_placed:
                # Фигура размещена: удаляем оригинал из области выбора
                for block_id in self.active_piece_data['canvas_ids']:
                    self.canvas.delete(block_id)
                
                self.draw_game_blocks()
                self.check_clear()
            else:
                # Не размещена: возвращаем мини-фигуру в область выбора
                for block_id in self.active_piece_data['canvas_ids']:
                    self.canvas.itemconfig(block_id, state='normal')
            
            self.dragging = False
            self.active_piece_data = None
            
            # Проверяем, нужны ли новые фигуры
            if not [p for p in self.pieces if not p['placed']]:
                 self.draw_pieces_selection() # Генерируем новые, если все размещены


# --- 5. ЗАПУСК ---
if __name__ == "__main__":
    root = tk.Tk()
    game = BlockBlastGame(root)
    root.mainloop()
