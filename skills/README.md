# daoyoucode Skills

内置 Skill 系统，每个 Skill 是一个可复用的 Prompt 模板。

## 目录结构

```
skills/
├── editblock/          # 块级编辑
├── wholefile/          # 全文件编辑
├── git-master/         # Git 专家
└── playwright/         # 浏览器自动化
```

## Skill 格式

每个 Skill 包含：

```
my-skill/
├── skill.yaml          # Skill 配置
├── system.md           # 系统提示词
└── user.md             # 用户提示词模板
```

### skill.yaml 示例

```yaml
name: my-skill
description: 我的技能
version: 1.0.0
author: Your Name
tags:
  - coding
  - refactor
```

### system.md 示例

```markdown
你是一个代码重构专家...
```

### user.md 示例

```markdown
请重构以下代码：

{{code}}

要求：
{{requirements}}
```
