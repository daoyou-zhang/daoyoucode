# 代码上下文获取工作流

## 目标
根据用户问题，获取相关的代码上下文，帮助理解和回答问题。

## 关键原则
- 先搜索定位，再读取细节
- 使用 repo_map 了解全局结构
- 只读取相关文件，避免信息过载

## 推荐工具
- `semantic_code_search` - 语义搜索（适合自然语言描述）
- `text_search` / `regex_search` - 精确搜索（适合关键词）
- `repo_map` (enable_lsp=true) - 查看代码结构和引用关系
- `read_file` / `batch_read_files` - 读取文件内容
- `get_file_symbols` - 获取文件的符号信息（类、函数等）

## 注意事项
- 先搜索再读取，不要盲目读取
- 如果搜索结果太多，使用更精确的关键词
- 如果搜索结果为空，尝试不同的关键词或使用 repo_map
