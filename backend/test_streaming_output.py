# 测试文件

def hello():
    print("Hello, World!")

def add(a, b):
    return a + b

class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, x):
        self.result += x
        return self.result
    
    def subtract(self, x):
        self.result -= x
        return self.result

if __name__ == "__main__":
    hello()
    print(add(1, 2))
