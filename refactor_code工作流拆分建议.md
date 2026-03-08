# refactor_code.md 工作流拆分建议

## 当前状况分析

### 文件规模
- 总行数：约 800+ 行
- 包含内容：
  - 通用重构流程（7个步骤）
  - 5个重构模式（提取函数、提取类、拆分大类、消除重复、简化条件、重命名）
  - 路径处理规则（约 200 行）
  - 工具使用原则
  - 注意事项

### 复杂度评估
- ⚠️ **模式3：拆分大类** 占据约 400 行（50%）
- 其他模式都比较简洁（每个 10-20 行）
- 通用流程清晰但较长

## 拆分建议

### 方案1：按重构类型拆分（推荐 ⭐⭐⭐⭐⭐）

将不同类型的重构拆分为独立工作流，每个工作流专注一个场景。

#### 1.1 保留 refactor_code.md 作为通用入口
```
refactor_code.md（简化版，约 200 行）
├── 核心原则
├── 通用执行步骤（简化）
├── 工具使用原则
└── 路由到具体工作流
```

**内容**：
- 重构的黄金法则
- 通用的 7 步流程（简化版）
- 根据用户需求路由到具体工作流：
  - "提取函数" → extract_function.md
  - "提取类" → extract_class.md
  - "拆分大类" → split_large_class.md
  - "消除重复" → remove_duplication.md
  - "重命名" → rename_code.md
  - "简化条件" → simplify_conditions.md

#### 1.2 创建专门的工作流

**split_large_class.md**（拆分大类，约 400 行）⭐⭐⭐
- 场景：类超过 500-1000 行，职责过多
- 包含完整的步骤0-7
- 包含路径处理规则
- 包含详细的示例和常见错误
- 这是最复杂的重构场景

**extract_function.md**（提取函数，约 150 行）
- 场景：函数太长（超过 50 行）
- 步骤：识别 → 提取 → 替换 → 验证
- 工具：search_replace 为主

**extract_class.md**（提取类，约 200 行）
- 场景：相关功能分散
- 步骤：识别 → 设计 → 创建 → 移动 → 更新 → 验证
- 工具：write_file + search_replace + lsp_find_references

**remove_duplication.md**（消除重复，约 150 行）
- 场景：多处代码重复
- 步骤：查找 → 提取 → 替换 → 验证
- 工具：text_search + search_replace

**rename_code.md**（重命名，约 100 行）
- 场景：命名不清晰
- 步骤：确定新名称 → 查找引用 → 全局替换 → 验证
- 工具：lsp_find_references + search_replace

**simplify_conditions.md**（简化条件，约 150 行）
- 场景：复杂的 if/else 嵌套
- 步骤：识别 → 提前返回 → 提取条件 → 验证
- 工具：search_replace

### 方案2：按复杂度拆分（备选 ⭐⭐⭐）

将重构分为简单、中等、复杂三个级别。

#### 2.1 simple_refactor.md（简单重构）
- 重命名
- 提取函数
- 简化条件

#### 2.2 medium_refactor.md（中等重构）
- 提取类
- 消除重复

#### 2.3 complex_refactor.md（复杂重构）
- 拆分大类
- 重构架构

### 方案3：保持现状但优化（备选 ⭐⭐）

不拆分，但优化当前文件结构。

#### 3.1 优化措施
- 将"模式3：拆分大类"移到单独的章节
- 添加目录导航
- 简化其他模式的描述
- 添加快速决策树

## 推荐方案：方案1（按重构类型拆分）

### 理由

#### 1. 职责单一 ⭐⭐⭐⭐⭐
- 每个工作流专注一个重构场景
- LLM 更容易理解和执行
- 减少混淆和错误

#### 2. 降低复杂度 ⭐⭐⭐⭐⭐
- 当前 refactor_code.md 太长（800+ 行）
- "拆分大类"占 50%，但不是最常用的场景
- 拆分后每个文件 100-400 行，更易维护

#### 3. 提高成功率 ⭐⭐⭐⭐
- 专门的工作流可以提供更详细的指导
- 减少 LLM 需要处理的上下文
- 每个场景的最佳实践更清晰

#### 4. 更好的可扩展性 ⭐⭐⭐⭐
- 未来可以添加更多重构模式
- 不会让单个文件越来越大
- 每个工作流可以独立优化

#### 5. 更好的用户体验 ⭐⭐⭐⭐
- 用户意图更明确："我要拆分大类" vs "我要重构代码"
- 可以在 intents.yaml 中添加更精确的意图匹配
- 减少不必要的步骤

### 缺点

#### 1. 文件数量增加
- 从 1 个文件变成 7 个文件
- 需要维护更多文件

**解决方案**：
- 创建共享的 refactor_common.md 存放公共内容
- 使用引用避免重复

#### 2. 可能的重复内容
- 路径处理规则
- 工具使用原则
- 验证步骤

**解决方案**：
- 提取公共部分到 refactor_common.md
- 在各个工作流中引用：`参考：[公共规则](refactor_common.md)`

## 具体实施方案

### 阶段1：创建核心工作流（优先级高）

#### 1.1 split_large_class.md ⭐⭐⭐⭐⭐
**原因**：
- 最复杂的场景
- 已经有完整的内容（模式3）
- 用户最近的需求

**内容**：
- 直接从当前 refactor_code.md 的"模式3"提取
- 包含完整的路径处理规则
- 包含详细的步骤0-7
- 包含常见错误和解决方案

**工作量**：1-2 小时（主要是复制和调整）

#### 1.2 refactor_common.md ⭐⭐⭐⭐
**原因**：
- 避免重复
- 统一标准

**内容**：
- 路径处理规则（完整版）
- 工具使用原则
- 验证步骤模板
- 常见错误（通用部分）

**工作量**：1 小时

#### 1.3 refactor_code.md（简化版）⭐⭐⭐⭐
**原因**：
- 作为入口和路由
- 保持向后兼容

**内容**：
- 重构的黄金法则
- 简化的通用流程
- 场景识别和路由
- 引用其他工作流

**工作量**：1 小时

### 阶段2：创建其他工作流（优先级中）

#### 2.1 extract_class.md ⭐⭐⭐
**原因**：
- 中等复杂度
- 常见场景

**工作量**：2 小时

#### 2.2 extract_function.md ⭐⭐⭐
**原因**：
- 最常见的重构
- 相对简单

**工作量**：1.5 小时

#### 2.3 rename_code.md ⭐⭐
**原因**：
- 简单但重要
- 需要注意引用更新

**工作量**：1 小时

### 阶段3：创建补充工作流（优先级低）

#### 3.1 remove_duplication.md ⭐⭐
**工作量**：1.5 小时

#### 3.2 simplify_conditions.md ⭐
**工作量**：1.5 小时

### 总工作量估算
- 阶段1（核心）：3-4 小时
- 阶段2（常用）：4.5 小时
- 阶段3（补充）：3 小时
- **总计**：10.5-11.5 小时

## 文件结构设计

```
skills/sisyphus-orchestrator/prompts/workflows/
├── refactor/                          # 重构工作流目录（新建）
│   ├── refactor_common.md            # 公共规则和原则
│   ├── split_large_class.md          # 拆分大类（最复杂）
│   ├── extract_class.md              # 提取类
│   ├── extract_function.md           # 提取函数
│   ├── rename_code.md                # 重命名
│   ├── remove_duplication.md         # 消除重复
│   └── simplify_conditions.md        # 简化条件
├── refactor_code.md                   # 入口和路由（简化）
└── ...其他工作流
```

## intents.yaml 更新

```yaml
# 重构相关意图
- intent: refactor_split_large_class
  keywords:
    - 拆分大类
    - 拆分类
    - 类太大
    - 职责太多
    - split class
    - split large class
  workflow: refactor/split_large_class.md
  description: 拆分承担过多职责的大类

- intent: refactor_extract_class
  keywords:
    - 提取类
    - 创建新类
    - extract class
  workflow: refactor/extract_class.md
  description: 将相关功能提取为新类

- intent: refactor_extract_function
  keywords:
    - 提取函数
    - 提取方法
    - 函数太长
    - extract function
    - extract method
  workflow: refactor/extract_function.md
  description: 将代码块提取为独立函数

- intent: refactor_rename
  keywords:
    - 重命名
    - 改名
    - rename
  workflow: refactor/rename_code.md
  description: 重命名类、函数或变量

- intent: refactor_remove_duplication
  keywords:
    - 消除重复
    - 去重
    - 重复代码
    - remove duplication
    - DRY
  workflow: refactor/remove_duplication.md
  description: 消除重复代码

- intent: refactor_simplify_conditions
  keywords:
    - 简化条件
    - 简化if
    - 复杂条件
    - simplify conditions
  workflow: refactor/simplify_conditions.md
  description: 简化复杂的条件逻辑

- intent: refactor_general
  keywords:
    - 重构
    - 重构代码
    - refactor
    - refactoring
  workflow: refactor_code.md
  description: 通用代码重构（会路由到具体工作流）
```

## 优势总结

### 对 LLM 的优势
1. ✅ 上下文更小，理解更准确
2. ✅ 步骤更清晰，执行更可靠
3. ✅ 减少混淆，提高成功率

### 对用户的优势
1. ✅ 意图匹配更精确
2. ✅ 执行速度更快（不需要处理无关内容）
3. ✅ 结果更可预测

### 对维护的优势
1. ✅ 每个文件职责单一，易于理解
2. ✅ 修改影响范围小
3. ✅ 可以独立优化每个场景
4. ✅ 添加新场景不影响现有工作流

## 风险和缓解

### 风险1：文件过多，难以管理
**缓解**：
- 使用 refactor/ 子目录组织
- 创建 README.md 说明每个文件的用途
- 使用一致的命名规范

### 风险2：公共内容重复
**缓解**：
- 提取到 refactor_common.md
- 使用引用而不是复制
- 定期检查和同步

### 风险3：用户不知道选哪个
**缓解**：
- refactor_code.md 提供决策树
- intents.yaml 精确匹配关键词
- 每个工作流开头说明适用场景

### 风险4：向后兼容性
**缓解**：
- 保留 refactor_code.md 作为入口
- 在 refactor_code.md 中路由到新工作流
- 逐步迁移，不强制切换

## 实施建议

### 建议1：分阶段实施 ⭐⭐⭐⭐⭐
1. 先创建 split_large_class.md（最紧急）
2. 再创建 refactor_common.md（避免重复）
3. 简化 refactor_code.md（保持兼容）
4. 逐步添加其他工作流

### 建议2：先试点再推广 ⭐⭐⭐⭐
1. 先创建 split_large_class.md
2. 测试效果
3. 如果效果好，再创建其他工作流
4. 如果效果不好，调整方案

### 建议3：保持灵活性 ⭐⭐⭐
- 不需要一次性创建所有工作流
- 根据实际使用情况决定优先级
- 可以随时调整文件结构

## 最终建议

### 立即执行（推荐）⭐⭐⭐⭐⭐

**创建以下文件**：
1. `refactor/split_large_class.md` - 从当前"模式3"提取
2. `refactor/refactor_common.md` - 提取公共规则
3. 简化 `refactor_code.md` - 添加路由逻辑

**理由**：
- split_large_class.md 已经有完整内容，工作量小
- 立即解决当前最大的问题（文件太长）
- 可以快速验证拆分方案的效果
- 不影响其他功能

**工作量**：3-4 小时

### 后续执行（可选）⭐⭐⭐

根据实际需求和效果，逐步添加其他工作流：
- extract_class.md
- extract_function.md
- rename_code.md
- 等等

## 总结

**是否需要拆分**：✅ 强烈建议拆分

**拆分方案**：方案1（按重构类型拆分）

**优先级**：
1. 高：split_large_class.md + refactor_common.md + 简化 refactor_code.md
2. 中：extract_class.md + extract_function.md + rename_code.md
3. 低：remove_duplication.md + simplify_conditions.md

**预期效果**：
- 每个工作流更专注、更清晰
- LLM 执行成功率提高
- 维护和扩展更容易
- 用户体验更好
