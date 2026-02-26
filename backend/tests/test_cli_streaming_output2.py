# 测试文件 - CLI 流式显示

def hello_world():
    """打印 Hello World"""
    print("Hello, World!")
    return "Hello"

def calculate_sum(numbers):
    """计算数字列表的总和"""
    total = 0
    for num in numbers:
        total += num
    return total

class DataProcessor:
    """数据处理器"""
    
    def __init__(self, name):
        self.name = name
        self.data = []
    
    def add_data(self, item):
        """添加数据"""
        self.data.append(item)
    
    def process(self):
        """处理数据"""
        result = []
        for item in self.data:
            processed = self._process_item(item)
            result.append(processed)
        return result
    
    def _process_item(self, item):
        """处理单个数据项"""
        return item.upper() if isinstance(item, str) else item

if __name__ == "__main__":
    hello_world()
    print(calculate_sum([1, 2, 3, 4, 5]))
    
    processor = DataProcessor("test")
    processor.add_data("hello")
    processor.add_data("world")
    print(processor.process())
