# 测试文件

def calculate_sum(numbers):
    """计算数字列表的总和（优化版）"""
    return sum(numbers)

def calculate_average(numbers):
    """计算平均值（改进版）"""
    if not numbers:
        return 0
    total = calculate_sum(numbers)
    return total / len(numbers)

class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        """加法运算"""
        result = a + b
        self.history.append(('add', a, b, result))
        return result
    
    def subtract(self, a, b):
        result = a - b
        self.history.append(('subtract', a, b, result))
        return result

if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(5, 3))
    print(calc.subtract(10, 4))
