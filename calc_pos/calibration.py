import numpy as np
from scipy.optimize import least_squares

def calibrate_system(mov_data, xy_data):
    """
    使用最小二乘法校准系统参数
    
    参数:
        mov_data: MOV坐标数组，形状为(n, 2)
        xy_data: 对应的XY坐标数组，形状为(n, 2)
    
    返回:
        theta: 旋转角度
        k: 比例因子
        C_x, C_y: 偏移量
    """
    def model(params, mov):
        theta, k, C_x, C_y = params
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)
        x = k * (mov[:, 0] * cos_t + mov[:, 1] * sin_t) + C_x
        y = k * (-mov[:, 0] * sin_t + mov[:, 1] * cos_t) + C_y
        return np.column_stack((x, y))
    
    def residuals(params, mov, xy):
        return (model(params, mov) - xy).flatten()
    
    # 初始参数猜测
    initial_params = [np.pi/4, 1.0, 0.0, 0.0]
    
    # 使用最小二乘法拟合
    result = least_squares(residuals, initial_params, args=(mov_data, xy_data))
    
    theta, k, C_x, C_y = result.x
    return theta, k, C_x, C_y

# 使用示例数据校准
mov_data = np.array([
    [0, 0],
    [4, 0],
    [0, 4],
    [2, 2],
    # 添加更多数据点...
])

xy_data = np.array([
    [288, 138],
    [197, 251],
    [402, 230],
    [295, 245],
    # 添加更多数据点...
])

theta, k, C_x, C_y = calibrate_system(mov_data, xy_data)
print(f"校准结果: theta={theta:.4f}, k={k:.4f}, C_x={C_x:.4f}, C_y={C_y:.4f}")