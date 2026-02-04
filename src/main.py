import os
import time
from src.engine import GameEngine
from src.constants import Tile, Direction, GhostState

def render(state):
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"Score: {state.score} | Ticks: {state.ticks} | PowerUp: {state.pacman.power_up_timer if state.pacman.is_powered_up else 0}")
    
    output = []
    for y in range(state.map.height):
        row = []
        for x in range(state.map.width):
            char = ' '
            tile = state.map.get_tile(x, y)
            if tile == Tile.WALL: char = '#'
            elif tile == Tile.PELLET: char = '.'
            elif tile == Tile.POWER_PELLET: char = 'O'
            elif tile == Tile.CHERRY: char = 'C'
            
            # Check entities
            if (x, y) == (state.pacman.x, state.pacman.y):
                char = 'P'
            else:
                for ghost in state.ghosts:
                    if (x, y) == (ghost.x, ghost.y):
                        if ghost.state == GhostState.FRIGHTENED:
                            char = 'f'
                        elif ghost.state == GhostState.EATEN:
                            char = 'e'
                        else:
                            char = ghost.name[0]
            row.append(char)
        output.append("".join(row))
    print("
".join(output))

def main():
    engine = GameEngine()
    
    # Simple test loop: Pacman just moves RIGHT then UP etc.
    # In a real benchmark, the LLM would provide these directions.
    directions = [Direction.RIGHT] * 5 + [Direction.UP] * 5 + [Direction.LEFT] * 10
    
    for i in range(100):
        # For now, just a dummy direction or NONE
        move = Direction.NONE
        if i < len(directions):
            move = directions[i]
            
        engine.step(move)
        render(engine.state)
        if engine.state.game_over:
            print("GAME OVER")
            break
        time.sleep(0.1)

if __name__ == "__main__":
    main()
