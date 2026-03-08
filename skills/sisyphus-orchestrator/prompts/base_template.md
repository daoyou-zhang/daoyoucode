# {{ agent_name }} - {{ agent_description }}

## 用户请求

{{ user_input }}

---

## 角色定义

{{ role }}

## 工作目录

项目根目录: {{ repo }}

## 角色定位

{{ positioning }}

---

## 🎯 当前任务工作流

{{ workflow }}

{% if project_understanding_block %}
---

## 项目信息（已预取）

{{ project_understanding_block }}
{% endif %}

{% if conversation_history %}
---

## 对话历史

{% for item in conversation_history %}
**用户**: {{ item.user }}

**AI**: {{ item.ai }}

{% endfor %}
{% endif %}

---

## 开始工作

请根据上述信息完成用户的请求。
