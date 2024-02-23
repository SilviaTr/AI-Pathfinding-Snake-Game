#!/usr/bin/env python3
from typing import List, Set
from dataclasses import dataclass
import pygame
from enum import Enum, unique
import sys
import random


FPS = 10

INIT_LENGTH = 4

WIDTH = 480
HEIGHT = 480
GRID_SIDE = 24
GRID_WIDTH = WIDTH // GRID_SIDE
GRID_HEIGHT = HEIGHT // GRID_SIDE

BRIGHT_BG = (103, 223, 235)
DARK_BG = (78, 165, 173)

SNAKE_COL = (6, 38, 7)
FOOD_COL = (224, 160, 38)
OBSTACLE_COL = (209, 59, 59)
VISITED_COL = (24, 42, 142)


@unique
class Direction(tuple, Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    def reverse(self):
        x, y = self.value
        return Direction((x * -1, y * -1))


@dataclass
class Position:
    x: int
    y: int

    def check_bounds(self, width: int, height: int):
        return (self.x >= width) or (self.x < 0) or (self.y >= height) or (self.y < 0)

    def draw_node(self, surface: pygame.Surface, color: tuple, background: tuple):
        r = pygame.Rect(
            (int(self.x * GRID_SIDE), int(self.y * GRID_SIDE)), (GRID_SIDE, GRID_SIDE)
        )
        pygame.draw.rect(surface, color, r)
        pygame.draw.rect(surface, background, r, 1)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Position):
            return (self.x == o.x) and (self.y == o.y)
        else:
            return False

    def __str__(self):
        return f"X{self.x};Y{self.y};"

    def __hash__(self):
        return hash(str(self))


class GameNode:
    nodes: Set[Position] = set()

    def __init__(self):
        self.position = Position(0, 0)
        self.color = (0, 0, 0)

    def randomize_position(self):
        try:
            GameNode.nodes.remove(self.position)
        except KeyError:
            pass

        condidate_position = Position(
            random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1),
        )

        if condidate_position not in GameNode.nodes:
            self.position = condidate_position
            GameNode.nodes.add(self.position)
        else:
            self.randomize_position()

    def draw(self, surface: pygame.Surface):
        self.position.draw_node(surface, self.color, BRIGHT_BG)


class Food(GameNode):
    def __init__(self):
        super(Food, self).__init__()
        self.color = FOOD_COL
        self.randomize_position()


class Obstacle(GameNode):
    def __init__(self):
        super(Obstacle, self).__init__()
        self.color = OBSTACLE_COL
        self.randomize_position()


class Snake:
    def __init__(self, screen_width, screen_height, init_length):
        self.color = SNAKE_COL
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.init_length = init_length
        self.reset()

    def reset(self):
        self.length = self.init_length
        self.positions = [Position((GRID_SIDE // 2), (GRID_SIDE // 2))]
        self.direction = random.choice([e for e in Direction])
        self.score = 0
        self.hasReset = True

    def get_head_position(self) -> Position:
        return self.positions[0]

    def turn(self, direction: Direction):
        if self.length > 1 and direction.reverse() == self.direction:
            return
        else:
            self.direction = direction

    def move(self):
        self.hasReset = False
        cur = self.get_head_position()
        x, y = self.direction.value
        new = Position(cur.x + x, cur.y + y,)
        if self.collide(new):
            self.reset()
        else:
            self.positions.insert(0, new)
            while len(self.positions) > self.length:
                self.positions.pop()

    def collide(self, new: Position):
        return (new in self.positions) or (new.check_bounds(GRID_WIDTH, GRID_HEIGHT))

    def eat(self, food: Food):
        if self.get_head_position() == food.position:
            self.length += 1
            self.score += 1
            while food.position in self.positions:
                food.randomize_position()

    def hit_obstacle(self, obstacle: Obstacle):
        if self.get_head_position() == obstacle.position:
            self.length -= 1
            self.score -= 1
            if self.length == 0:
                self.reset()

    def draw(self, surface: pygame.Surface):
        for p in self.positions:
            p.draw_node(surface, self.color, BRIGHT_BG)


class Player:
    def __init__(self) -> None:
        self.visited_color = VISITED_COL
        self.visited: Set[Position] = set()
        self.chosen_path: List[Direction] = []

    def move(self, snake: Snake) -> bool:
        try:
            next_step = self.chosen_path.pop(0)
            snake.turn(next_step)
            return False
        except IndexError:
            return True

    def search_path(self, snake: Snake, food: Food, *obstacles: Set[Obstacle]):
        """
        Do nothing, control is defined in derived classes
        """
        pass

    def turn(self, direction: Direction):
        """
        Do nothing, control is defined in derived classes
        """
        pass

    def draw_visited(self, surface: pygame.Surface):
        for p in self.visited:
            p.draw_node(surface, self.visited_color, BRIGHT_BG)


class SnakeGame:
    def __init__(self, snake: Snake, player: Player) -> None:
        pygame.init()
        pygame.display.set_caption("AIFundamentals - SnakeGame")

        self.snake = snake
        self.food = Food()
        self.obstacles: Set[Obstacle] = set()
        for _ in range(40):
            ob = Obstacle()
            while any([ob.position == o.position for o in self.obstacles]):
                ob.randomize_position()
            self.obstacles.add(ob)

        self.player = player

        self.fps_clock = pygame.time.Clock()

        self.screen = pygame.display.set_mode(
            (snake.screen_height, snake.screen_width), 0, 32
        )
        self.surface = pygame.Surface(self.screen.get_size()).convert()
        self.myfont = pygame.font.SysFont("monospace", 16)

    def drawGrid(self):
        for y in range(0, int(GRID_HEIGHT)):
            for x in range(0, int(GRID_WIDTH)):
                p = Position(x, y)
                if (x + y) % 2 == 0:
                    p.draw_node(self.surface, BRIGHT_BG, BRIGHT_BG)
                else:
                    p.draw_node(self.surface, DARK_BG, DARK_BG)

    def run(self):
        while not self.handle_events():
            self.fps_clock.tick(FPS)
            self.drawGrid()
            if self.player.move(self.snake) or self.snake.hasReset:
                self.player.search_path(self.snake, self.food, self.obstacles)
                self.player.move(self.snake)
            self.snake.move()
            self.snake.eat(self.food)
            for ob in self.obstacles:
                self.snake.hit_obstacle(ob)
            for ob in self.obstacles:
                ob.draw(self.surface)
            self.player.draw_visited(self.surface)
            self.snake.draw(self.surface)
            self.food.draw(self.surface)
            self.screen.blit(self.surface, (0, 0))
            text = self.myfont.render(
                "Score {0}".format(self.snake.score), 1, (0, 0, 0)
            )
            self.screen.blit(text, (5, 10))
            pygame.display.update()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_UP:
                    self.player.turn(Direction.UP)
                elif event.key == pygame.K_DOWN:
                    self.player.turn(Direction.DOWN)
                elif event.key == pygame.K_LEFT:
                    self.player.turn(Direction.LEFT)
                elif event.key == pygame.K_RIGHT:
                    self.player.turn(Direction.RIGHT)
        return False


class HumanPlayer(Player):
    def __init__(self):
        super(HumanPlayer, self).__init__()

    def turn(self, direction: Direction):
        self.chosen_path.append(direction)


# ----------------------------------
# DO NOT MODIFY CODE ABOVE THIS LINE
# ----------------------------------
        
from collections import deque
from queue import PriorityQueue

class SearchType(Enum):
    BFS = 1
    DFS = 2
    DIJKSTRA = 3
    ASTAR = 4

class SearchBasedPlayer(Player):
    def __init__(self, search_type=SearchType.BFS):
        super(SearchBasedPlayer, self).__init__()
        self.search_type = search_type

    def bfs(self, start, goal, obstacles):
        queue = deque([(start, [start])])
        visited = set()
        while queue:
            (current, path) = queue.popleft()
            if current not in visited:
                if current == goal:
                    return path
                visited.add(current)
                for direction in Direction:
                    next_pos = Position(current.x + direction.value[0], current.y + direction.value[1])
                    if (not next_pos.check_bounds(GRID_WIDTH, GRID_HEIGHT) and
                    next_pos not in visited and
                    next_pos not in obstacles and
                    next_pos not in snake.positions[1:]):  # Exclude the head from the snake's body positions
                        queue.append((next_pos, path + [next_pos]))
        return []

    def dfs(self, start, goal, snake, obstacles):
        stack = [(start, [start])]
        visited = set()
        while stack:
            current, path = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            if current == goal:
                return path
            for direction in Direction:
                next_pos = Position(current.x + direction.value[0], current.y + direction.value[1])
                # Integrated the validity check here
                if (not next_pos.check_bounds(GRID_WIDTH, GRID_HEIGHT) and
                    next_pos not in visited and
                    next_pos not in obstacles and
                    next_pos not in snake.positions[1:]):  # Exclude the head from the snake's body positions
                    stack.append((next_pos, path + [next_pos]))
        return []
    
    def dijkstra(self, start, goal, snake, obstacles):
        pq = PriorityQueue()
        counter = 0  # Unique sequence count
        pq.put((0, counter, start, [start]))  # Cost from start to start is 0
        visited = set()
        obstacle_cost = 10  # Assign a high cost to moving onto an obstacle
        while not pq.empty():
            cost, _, current, path = pq.get()
            if current in visited:
                continue
            visited.add(current)
            if current == goal:
                return path
            for direction in Direction:
                next_pos = Position(current.x + direction.value[0], current.y + direction.value[1])
                if next_pos in visited or next_pos in snake.positions:
                    continue
                new_cost = cost + (obstacle_cost if next_pos in obstacles else 1)  # High cost for obstacles
                counter += 1
                pq.put((new_cost, counter, next_pos, path + [next_pos]))
        return []

    def heuristic(self, a, b):
        # Use Manhattan distance as the heuristic
        return abs(a.x - b.x) + abs(a.y - b.y)

    def astar(self, start, goal, snake, obstacles):
        pq = PriorityQueue()
        counter = 0  # Unique sequence count
        pq.put((0, counter, start, [start]))  # Initial priority, counter, position, path
        visited = set()
        cost_so_far = {start: 0}
        obstacle_cost = 10  # Assign a high cost to moving onto an obstacle

        while not pq.empty():
            _, _, current, path = pq.get()
            if current in visited:
                continue
            visited.add(current)
            if current == goal:
                return path

            for direction in Direction:
                next_pos = Position(current.x + direction.value[0], current.y + direction.value[1])
                if next_pos in visited or next_pos in snake.positions:
                    continue

                new_cost = cost_so_far[current] + (obstacle_cost if next_pos in obstacles else 1)
                if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                    cost_so_far[next_pos] = new_cost
                    priority = new_cost + self.heuristic(next_pos, goal)
                    counter += 1
                    pq.put((priority, counter, next_pos, path + [next_pos]))

        return []

    def search_path(self, snake: Snake, food: Food, obstacles: Set[Obstacle]):
        start = snake.get_head_position()
        goal = food.position
        path = []
        obstacle_positions = {ob.position for ob in obstacles}
        if self.search_type == SearchType.BFS:
            path = self.bfs(start, goal, obstacle_positions)
        elif self.search_type == SearchType.DFS:
            path = self.dfs(start, goal, snake, obstacle_positions)
        elif self.search_type == SearchType.DIJKSTRA:
            path = self.dijkstra(start, goal, snake, obstacle_positions)
        elif self.search_type == SearchType.ASTAR:
            path = self.astar(start, goal, snake, obstacle_positions)
        
        if path:
            self.visited = set(path)  # Update the visited nodes for drawing
            self.chosen_path = self.positions_to_directions(path, snake.direction)
        else:
            self.chosen_path = []

    def positions_to_directions(self, positions, current_direction):
        directions = []
        for i in range(1, len(positions)):
            delta_x = positions[i].x - positions[i-1].x
            delta_y = positions[i].y - positions[i-1].y
            direction = Direction((delta_x, delta_y))
            if current_direction.reverse() != direction:  # Prevent reversing direction
                directions.append(direction)
                current_direction = direction
        return directions

if __name__ == "__main__":
    snake = Snake(WIDTH, HEIGHT, INIT_LENGTH)  # Make sure to use HEIGHT for the second parameter

    # Ask the user for the search algorithm to use
    print("Select the search algorithm:")
    print("1 - BFS (Breadth-First Search)")
    print("2 - DFS (Depth-First Search)")
    print("3 - Dijkstra's Algorithm")
    print("4 - A* Search")
    choice = input("Enter your choice (1-4): ")

    # Map the user's choice to the corresponding search type
    search_type = SearchType.BFS  # Default to BFS
    if choice == "1":
        search_type = SearchType.BFS
    elif choice == "2":
        search_type = SearchType.DFS
    elif choice == "3":
        search_type = SearchType.DIJKSTRA
    elif choice == "4":
        search_type = SearchType.ASTAR
    else:
        print("Invalid choice. Using default BFS algorithm.")

    player = SearchBasedPlayer(search_type=search_type)
    game = SnakeGame(snake, player)
    game.run()

