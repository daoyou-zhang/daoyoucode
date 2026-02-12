# CLI测试指南

## 🎯 测试目标

验证Agent集成是否成功，确保CLI在各种场景下都能正常工作。

---

## 🚀 快速开始

### 环境准备

```bash
# 进入backend目录
cd backend

# 激活虚拟环境
.\venv\Scripts\activate

# 验证Agent系统
python -c "from daoyoucode.agents.core.agent import get_agent_registry; print('Agent系统可用')"
```

如果看到 "Agent系统可用"，说明环境正常。

---

## 📋 测试场景

### 场景1: chat命令 - Agent可用

**目标**: 测试真实AI对话

```bash
# 启动chat
python daoyoucode.py chat
```

**测试步骤**:

1. **基本对话**
   ```
   你 › 你好
   ```
   期望: AI友好回应

2. **代码生成**
   ```
   你 › 写一个Python函数计算斐波那契数列
   ```
   期望: AI生成完整的代码

3. **问题解答**
   ```
   你 › 什么是装饰器？
   ```
   期望: AI解释概念

4. **上下文理解**
   ```
   你 › 写一个函数
   你 › 给它添加文档字符串
   ```
   期望: AI理解"它"指的是之前的函数

5. **命令测试**
   ```
   你 › /help
   你 › /history
   你 › /model
   你 › /exit
   ```
   期望: 所有命令正常工作

**检查点**:
- [ ] AI响应合理
- [ ] 代码格式正确
- [ ] Markdown渲染正常
- [ ] 命令系统工作
- [ ] 退出正常

---

### 场景2: chat命令 - Agent不可用

**目标**: 测试优雅降级

**模拟方法**: 临时重命名daoyoucode目录
```bash
# 重命名（模拟Agent不可用）
ren daoyoucode daoyoucode_backup

# 启动chat
python daoyoucode.py chat

# 恢复
ren daoyoucode_backup daoyoucode
```

**测试步骤**:

1. **启动时提示**
   期望: 看到 "⚠ Agent初始化失败，使用模拟模式"

2. **基本对话**
   ```
   你 › 你好
   ```
   期望: 模拟响应

3. **命令仍然工作**
   ```
   你 › /help
   你 › /exit
   ```
   期望: 命令系统正常

**检查点**:
- [ ] 降级提示清晰
- [ ] 模拟模式工作
- [ ] 命令系统正常
- [ ] 没有崩溃

---

### 场景3: edit命令 - Agent可用

**目标**: 测试真实代码编辑

**准备测试文件**:
```bash
# 创建测试文件
echo "# TODO: Add code here" > test.py
```

**测试步骤**:

1. **简单编辑**
   ```bash
   python daoyoucode.py edit test.py "添加一个hello world函数"
   ```
   期望: 
   - 显示 "✓ CodeAgent初始化完成"
   - 显示 "🤖 AI正在分析和修改代码..."
   - 显示AI的修改建议
   - 询问确认

2. **查看结果**
   ```bash
   type test.py
   ```
   期望: 文件被修改

3. **多文件编辑**
   ```bash
   echo "# File 1" > file1.py
   echo "# File 2" > file2.py
   python daoyoucode.py edit file1.py file2.py "添加导入语句"
   ```
   期望: 两个文件都被处理

4. **自动确认**
   ```bash
   python daoyoucode.py edit test.py "添加注释" --yes
   ```
   期望: 不询问确认，直接应用

**检查点**:
- [ ] Agent初始化成功
- [ ] AI分析文件
- [ ] 显示修改建议
- [ ] 确认流程正常
- [ ] 文件被修改
- [ ] --yes选项工作

---

### 场景4: edit命令 - Agent不可用

**目标**: 测试编辑命令的降级

**模拟方法**: 同场景2

**测试步骤**:

1. **启动编辑**
   ```bash
   python daoyoucode.py edit test.py "添加函数"
   ```
   期望:
   - 显示 "⚠ Agent初始化失败，使用模拟模式"
   - 显示进度动画
   - 显示模拟的diff
   - 询问确认

**检查点**:
- [ ] 降级提示清晰
- [ ] 模拟模式工作
- [ ] UI正常显示
- [ ] 没有崩溃

---

### 场景5: 错误处理

**目标**: 测试各种错误场景

**测试步骤**:

1. **文件不存在**
   ```bash
   python daoyoucode.py edit nonexistent.py "添加代码"
   ```
   期望: 友好的错误提示

2. **空指令**
   ```bash
   python daoyoucode.py edit test.py ""
   ```
   期望: 提示需要指令

3. **无效命令**
   ```
   你 › /invalid
   ```
   期望: 提示未知命令

4. **Ctrl+C中断**
   ```
   你 › (按Ctrl+C)
   ```
   期望: 优雅退出

**检查点**:
- [ ] 错误提示友好
- [ ] 没有崩溃
- [ ] 可以恢复
- [ ] 退出优雅

---

## 🔍 详细检查

### UI检查

- [ ] 横幅显示正常
- [ ] Panel边框完整
- [ ] Table对齐正确
- [ ] 颜色搭配合理
- [ ] Spinner动画流畅
- [ ] Progress显示正确
- [ ] Markdown渲染正常（代码块、列表等）

### 功能检查

**chat命令**:
- [ ] /help - 显示帮助
- [ ] /exit - 退出
- [ ] /add - 添加文件
- [ ] /drop - 移除文件
- [ ] /files - 显示文件列表
- [ ] /clear - 清空历史
- [ ] /model - 查看/切换模型
- [ ] /history - 显示历史

**edit命令**:
- [ ] 单文件编辑
- [ ] 多文件编辑
- [ ] --yes自动确认
- [ ] --model指定模型
- [ ] --repo指定仓库

### 性能检查

- [ ] 启动速度 < 2秒
- [ ] Agent初始化 < 3秒
- [ ] 响应时间合理
- [ ] 内存使用正常
- [ ] 没有内存泄漏

---

## 📊 测试报告模板

```markdown
# CLI测试报告

## 测试环境
- 操作系统: Windows
- Python版本: 3.x
- 虚拟环境: backend/venv
- Agent系统: 可用/不可用

## 测试结果

### chat命令
- [ ] Agent可用场景: 通过/失败
- [ ] Agent不可用场景: 通过/失败
- [ ] 命令系统: 通过/失败
- [ ] UI显示: 通过/失败

### edit命令
- [ ] Agent可用场景: 通过/失败
- [ ] Agent不可用场景: 通过/失败
- [ ] 多文件编辑: 通过/失败
- [ ] UI显示: 通过/失败

### 错误处理
- [ ] 文件不存在: 通过/失败
- [ ] 无效命令: 通过/失败
- [ ] Ctrl+C中断: 通过/失败

## 发现的问题
1. 问题描述
   - 重现步骤
   - 期望行为
   - 实际行为

## 建议
- 优化建议
- 功能建议
```

---

## 🐛 常见问题

### 问题1: Agent初始化失败

**症状**: 
```
⚠ Agent初始化失败，使用模拟模式
原因: No module named 'daoyoucode'
```

**解决**:
```bash
# 检查是否在backend目录
cd backend

# 检查daoyoucode目录是否存在
dir daoyoucode

# 检查Python路径
python -c "import sys; print(sys.path)"
```

### 问题2: 虚拟环境未激活

**症状**: 找不到typer等依赖

**解决**:
```bash
# 激活虚拟环境
.\venv\Scripts\activate

# 验证
where python
```

### 问题3: 编码问题

**症状**: 中文显示乱码

**解决**:
```bash
# 设置控制台编码
chcp 65001
```

---

## ✅ 测试完成标准

所有场景测试通过，且：

1. **功能完整**
   - chat命令所有功能工作
   - edit命令所有功能工作
   - 所有内置命令工作

2. **错误处理**
   - 所有错误场景有友好提示
   - 没有未捕获的异常
   - 降级机制工作

3. **用户体验**
   - UI美观
   - 响应快速
   - 提示清晰
   - 操作流畅

4. **稳定性**
   - 长时间运行不崩溃
   - 内存使用正常
   - 可以正常退出

---

## 🎯 下一步

测试完成后：

1. **记录结果** - 填写测试报告
2. **修复问题** - 解决发现的bug
3. **优化体验** - 根据测试反馈优化
4. **更新文档** - 完善使用文档

---

## 📝 快速测试脚本

创建 `test_cli.bat`:
```batch
@echo off
echo ========== DaoyouCode CLI 测试 ==========
echo.

echo [1/5] 测试环境...
python -c "from daoyoucode.agents.core.agent import get_agent_registry; print('✓ Agent系统可用')"
if errorlevel 1 (
    echo ✗ Agent系统不可用
    goto :end
)
echo.

echo [2/5] 创建测试文件...
echo # TODO > test.py
echo ✓ 测试文件已创建
echo.

echo [3/5] 测试edit命令...
python daoyoucode.py edit test.py "添加hello函数" --yes
if errorlevel 1 (
    echo ✗ edit命令失败
    goto :end
)
echo ✓ edit命令成功
echo.

echo [4/5] 检查结果...
type test.py
echo.

echo [5/5] 清理...
del test.py
echo ✓ 清理完成
echo.

echo ========== 测试完成 ==========

:end
pause
```

运行:
```bash
cd backend
.\venv\Scripts\activate
test_cli.bat
```

---

## 🎉 开始测试

准备好了吗？开始测试吧！

```bash
cd backend
.\venv\Scripts\activate
python daoyoucode.py chat
```

祝测试顺利！🚀
