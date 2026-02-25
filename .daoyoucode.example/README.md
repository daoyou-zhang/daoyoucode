# DaoyouCode 项目配置示例

这个目录展示了 `.daoyoucode/` 目录的结构和可选的团队共享配置。

## 目录结构

```
.daoyoucode/
├── project_context.json     # 项目上下文（可选：团队共享）
├── chat.history.md          # 对话历史（不上传）
├── summaries.json           # 会话摘要（不上传）
├── key_info.json            # 关键信息（不上传）
├── cache/                   # 缓存目录（不上传）
│   └── repomap/             # RepoMap 缓存
└── archive/                 # 归档目录（不上传）
    └── chat.history.*.md    # 归档的对话历史
```

## 团队共享配置（可选）

如果你希望团队成员共享项目上下文，可以：

1. 从 `.gitignore` 中移除这一行：
   ```
   # .daoyoucode/project_context.json
   ```

2. 创建 `.daoyoucode/project_context.json`：
   ```json
   {
     "architecture": {
       "type": "microservices",
       "patterns": ["DDD", "CQRS"],
       "key_modules": ["agents", "orchestrators", "tools"]
     },
     "team_conventions": {
       "code_review": {
         "required_approvals": 2,
         "checklist": [
           "代码风格符合规范",
           "添加了单元测试",
           "更新了文档"
         ]
       },
       "naming_conventions": {
         "files": "snake_case",
         "classes": "PascalCase",
         "functions": "snake_case",
         "constants": "UPPER_SNAKE_CASE"
       },
       "testing_requirements": {
         "coverage_threshold": 80,
         "required_tests": ["unit", "integration"]
       }
     },
     "project_history": {
       "major_refactorings": [
         {
           "date": "2026-02-01",
           "description": "重构记忆系统，实现分层存储",
           "impact": "提升性能，减少 C 盘占用"
         }
       ],
       "known_issues": [
         {
           "id": "ISSUE-123",
           "description": "Windows CMD 中文显示乱码",
           "workaround": "使用 UTF-8 编辑器查看"
         }
       ],
       "technical_debt": [
         {
           "area": "测试覆盖率",
           "description": "部分模块缺少单元测试",
           "priority": "medium"
         }
       ]
     }
   }
   ```

3. 提交到 Git：
   ```bash
   git add .daoyoucode/project_context.json
   git commit -m "添加项目上下文配置"
   ```

## 个人配置（不上传）

以下文件包含个人信息或敏感数据，不应上传到 Git：

- `chat.history.md` - 对话历史（可能包含敏感信息）
- `summaries.json` - 会话摘要
- `key_info.json` - 关键信息
- `cache/` - 缓存数据
- `archive/` - 归档数据

## 用户级配置（在用户目录）

以下配置存储在用户目录（`~/.daoyoucode/`），不会被 Git 追踪：

- `user_profile.json` - 用户画像（编码风格、沟通偏好）
- `preferences.json` - 全局偏好设置
- `user_sessions.json` - 用户会话映射

## 清理缓存

如果需要清理缓存：

```bash
# 清理项目级缓存
rm -rf .daoyoucode/cache/
rm -rf .daoyoucode/archive/

# 清理对话历史
rm .daoyoucode/chat.history.md

# 清理用户级缓存（Windows）
rmdir /s /q %USERPROFILE%\.daoyoucode\memory

# 清理用户级缓存（Linux/Mac）
rm -rf ~/.daoyoucode/memory
```

## 注意事项

1. **对话历史包含敏感信息**：不要上传到公开仓库
2. **项目上下文可以共享**：帮助团队成员快速了解项目
3. **缓存可以删除**：会自动重新生成
4. **用户画像是个人的**：存储在用户目录，不会被 Git 追踪
