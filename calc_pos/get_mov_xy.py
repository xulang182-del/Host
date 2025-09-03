import math
import numpy as np

class CoordinateTransformer:
    def __init__(self):
        self.theta = math.atan2(-28.25, -22.75)
        self.k = math.sqrt(22.75 ** 2 + 28.25 ** 2)
        self.C_x = 288
        self.C_y = 138
        
        self.cos_theta = math.cos(self.theta)
        self.sin_theta = math.sin(self.theta)
    
    def mov_to_xy(self, mov_x, mov_y):
        x = self.k * (mov_x * self.cos_theta + mov_y * self.sin_theta) + self.C_x
        y = self.k * (-mov_x * self.sin_theta + mov_y * self.cos_theta) + self.C_y
        return x, y
    
    def xy_to_mov(self, x, y):
        mov_x = ((x - self.C_x) * self.cos_theta - (y - self.C_y) * self.sin_theta) / self.k
        mov_y = ((x - self.C_x) * self.sin_theta + (y - self.C_y) * self.cos_theta) / self.k
        return mov_x, mov_y
    
    def calculate_movement(self, current_x, current_y, target_x, target_y):
        current_mov_x, current_mov_y = self.xy_to_mov(current_x, current_y)
        
        target_mov_x, target_mov_y = self.xy_to_mov(target_x, target_y)
        
        delta_mov_x = target_mov_x - current_mov_x
        delta_mov_y = target_mov_y - current_mov_y
        
        return delta_mov_x, delta_mov_y

if __name__ == "__main__":
    transformer = CoordinateTransformer()

    current_x, current_y = 402, 230
    target_x, target_y = 288, 138

    delta_mov_x, delta_mov_y = transformer.calculate_movement(current_x, current_y, target_x, target_y)
    
    print(f"从位置({current_x}, {current_y})移动到({target_x}, {target_y})")
    print(f"需要改变MOV_X: {delta_mov_x:.2f}, MOV_Y: {delta_mov_y:.2f}")

    mov_x, mov_y = transformer.xy_to_mov(current_x, current_y)
    new_mov_x = mov_x + delta_mov_x
    new_mov_y = mov_y + delta_mov_y
    new_x, new_y = transformer.mov_to_xy(new_mov_x, new_mov_y)
    print(f"验证: 移动后位置应为({new_x:.2f}, {new_y:.2f})")
