# .gitignore 规则说明

## 已添加的规则

### DaoyouCode 记忆和缓存

```gitignore
# DaoyouCode 记忆和缓存（新版本）
# 项目级存储（不上传）
.daoyoucode/
!.daoyoucode/.gitkeep

# 用户级存储（在用户目录，不会被 git 追踪）
# ~/.daoyoucode/

# 旧版本备份（不上传）
.daoyou.backups/

# 代码索引缓存（不上传）
.daoyoucode/cache/
.daoyoucode/codebase_index/

# 对话历史（不上传，包含敏感信息）
.daoyoucode/chat.history.md
.daoyoucode/archive/

# 项目上下文（可选：如果团队共享，可以上传）
# .daoyoucode/project_context.json

# 会话摘要（不上传）
.daoyoucode/summaries.json
.daoyoucode/key_info.json
```

---

## 规则说明

### 1. 项目级存储（`.daoyoucode/`）

**规则**：`.daoyoucode/`

**说明**：忽略整个 `.daoyoucode/` 目录

**原因**：
- 包含个人对话历史（可能有敏感信息）
- 包含缓存数据（可以重新生成）
- 包含会话摘要（个人数据）

**例外**：
- 如果需要团队共享项目上下文，可以注释掉 `# .daoyoucode/project_context.json`

---

### 2. 旧版本备份（`.daoyou.backups/`）

**规则**：`.daoyou.backups/`

**说明**：忽略旧版本的备份目录

**原因**：
- 旧版本的历史记录
- 已迁移到新位置
- 不需要上传

---

### 3. 对话历史（`.daoyoucode/chat.history.md`）

**规则**：`.daoyoucode/chat.history.md`

**说明**：忽略对话历史文件

**原因**：
- **包含敏感信息**：可能包含代码片段、API 密钥、个人信息
- **个人数据**：每个开发者的对话历史不同
- **文件较大**：随着使用会越来越大

**重要**：不要上传到公开仓库！

---

### 4. 缓存目录（`.daoyoucode/cache/`）

**规则**：`.daoyoucode/cache/`

**说明**：忽略缓存目录

**原因**：
- 可以重新生成
- 文件较大（RepoMap 缓存可能有几十 MB）
- 每个开发者的缓存不同

**包含**：
- `repomap/` - RepoMap 缓存（SQLite）
- 其他工具的缓存

---

### 5. 归档目录（`.daoyoucode/archive/`）

**规则**：`.daoyoucode/archive/`

**说明**：忽略归档目录

**原因**：
- 旧的对话历史（超过 30 天）
- 文件较大
- 个人数据

---

### 6. 项目上下文（`.daoyoucode/project_context.json`）

**规则**：`# .daoyoucode/project_context.json`（注释掉，可选）

**说明**：默认不上传，但可以选择上传

**团队共享场景**：
- 项目架构说明
- 团队编码规范
- 代码审查清单
- 已知问题和技术债

**如何启用团队共享**：
1. 从 `.gitignore` 中删除或注释掉这一行
2. 创建 `.daoyoucode/project_context.json`
3. 提交到 Git

**示例内容**：
```json
{
  "architecture": {
    "type": "microservices",
    "patterns": ["DDD", "CQRS"]
  },
  "team_conventions": {
    "naming_conventions": {
      "files": "snake_case",
      "classes": "PascalCase"
    }
  }
}
```

---

### 7. 会话摘要（`.daoyoucode/summaries.json`）

**规则**：`.daoyoucode/summaries.json`

**说明**：忽略会话摘要

**原因**：
- 个人数据
- 可能包含敏感信息

---

### 8. 关键信息（`.daoyoucode/key_info.json`）

**规则**：`.daoyoucode/key_info.json`

**说明**：忽略关键信息

**原因**：
- 个人数据
- 可能包含敏感信息

---

## 用户级存储（不需要规则）

以下文件存储在用户目录（`~/.daoyoucode/`），不在项目目录中，因此不需要 `.gitignore` 规则：

- `user_profile.json` - 用户画像
- `preferences.json` - 全局偏好
- `user_sessions.json` - 用户会话映射

**位置**：
- Windows: `C:\Users\[用户名]\.daoyoucode\`
- Linux/Mac: `~/.daoyoucode/`

---

## 检查规则是否生效

### 检查被忽略的文件

```bash
# 查看被忽略的文件
git status --ignored

# 检查特定文件是否被忽略
git check-ignore -v .daoyoucode/chat.history.md
```

### 清理已追踪的文件

如果之前已经提交了这些文件，需要从 Git 中删除（但保留本地文件）：

```bash
# 从 Git 中删除（但保留本地文件）
git rm --cached -r .daoyoucode/
git rm --cached -r .daoyou.backups/

# 提交更改
git commit -m "从 Git 中移除记忆和缓存文件"
```

---

## 最佳实践

### 1. 不要上传敏感信息

- ❌ 对话历史（可能包含 API 密钥、密码）
- ❌ 会话摘要（可能包含敏感信息）
- ❌ 缓存数据（可能包含代码片段）

### 2. 可以选择性上传

- ✅ 项目上下文（团队共享）
- ✅ 编码规范（团队共享）
- ✅ 架构说明（团队共享）

### 3. 定期清理

```bash
# 清理缓存（可以重新生成）
rm -rf .daoyoucode/cache/

# 清理归档（旧的对话历史）
rm -rf .daoyoucode/archive/

# 清理对话历史（如果太大）
rm .daoyoucode/chat.history.md
```

### 4. 备份重要数据

如果对话历史中有重要信息，建议定期备份：

```bash
# 备份对话历史
cp .daoyoucode/chat.history.md ~/backups/chat.history.$(date +%Y%m%d).md

# 或者使用 Git 私有仓库
git init .daoyoucode-private
cd .daoyoucode-private
git add chat.history.md
git commit -m "备份对话历史"
git remote add origin <私有仓库地址>
git push
```

---

## 团队协作建议

### 场景 1：开源项目

```gitignore
# 忽略所有 .daoyoucode/ 内容
.daoyoucode/
```

**原因**：避免泄露敏感信息

### 场景 2：私有项目（团队共享项目上下文）

```gitignore
# 忽略个人数据
.daoyoucode/chat.history.md
.daoyoucode/summaries.json
.daoyoucode/key_info.json
.daoyoucode/cache/
.daoyoucode/archive/

# 允许上传项目上下文（团队共享）
# .daoyoucode/project_co