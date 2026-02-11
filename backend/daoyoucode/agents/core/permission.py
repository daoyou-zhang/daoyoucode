"""
权限控制系统

借鉴OpenCode的权限管理机制
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import fnmatch
import logging

logger = logging.getLogger(__name__)


class PermissionAction(Enum):
    """权限动作"""
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


@dataclass
class PermissionRule:
    """权限规则"""
    action: str  # read/write/execute/delete
    pattern: str  # 文件/目录模式 (支持通配符)
    permission: PermissionAction
    
    def matches(self, path: str) -> bool:
        """检查路径是否匹配"""
        return fnmatch.fnmatch(path, self.pattern)


class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        self.rules: List[PermissionRule] = []
        self.ask_callback: Optional[Callable] = None
        self.logger = logging.getLogger("permission")
    
    def add_rule(
        self,
        action: str,
        pattern: str,
        permission: str
    ):
        """添加规则"""
        rule = PermissionRule(
            action=action,
            pattern=pattern,
            permission=PermissionAction(permission)
        )
        self.rules.append(rule)
        self.logger.debug(f"添加规则: {action} {pattern} -> {permission}")
    
    def add_rules_from_config(self, config: Dict[str, Any]):
        """
        从配置添加规则
        
        config示例:
        {
            "read": {
                "*": "allow",
                "*.env": "deny"
            },
            "write": {
                "*.py": "allow",
                "*.env": "deny"
            },
            "execute": {
                "*.sh": "ask"
            }
        }
        """
        for action, patterns in config.items():
            if isinstance(patterns, dict):
                for pattern, permission in patterns.items():
                    self.add_rule(action, pattern, permission)
            elif isinstance(patterns, str):
                # 简化配置：action: permission
                self.add_rule(action, "*", patterns)
    
    async def check_permission(
        self,
        action: str,
        path: str,
        agent_name: Optional[str] = None
    ) -> bool:
        """
        检查权限
        
        Args:
            action: 动作类型 (read/write/execute/delete)
            path: 文件路径
            agent_name: Agent名称（用于日志）
        
        Returns:
            是否允许
        """
        # 查找匹配的规则（最后匹配的优先）
        matched_rule = None
        
        for rule in self.rules:
            if rule.action == action and rule.matches(path):
                matched_rule = rule
                # 继续查找，后面的规则优先级更高
        
        if not matched_rule:
            # 没有匹配规则，默认拒绝
            self.logger.warning(
                f"没有匹配规则: {action} {path}, 默认拒绝"
            )
            return False
        
        # 根据规则决定
        if matched_rule.permission == PermissionAction.ALLOW:
            self.logger.debug(f"允许: {action} {path}")
            return True
        
        elif matched_rule.permission == PermissionAction.DENY:
            self.logger.warning(f"拒绝: {action} {path}")
            return False
        
        elif matched_rule.permission == PermissionAction.ASK:
            # 询问用户
            return await self._ask_user(action, path, agent_name)
        
        return False
    
    async def _ask_user(
        self,
        action: str,
        path: str,
        agent_name: Optional[str]
    ) -> bool:
        """询问用户"""
        if self.ask_callback:
            try:
                return await self.ask_callback(action, path, agent_name)
            except Exception as e:
                self.logger.error(f"询问用户失败: {e}")
                return False
        
        # 没有回调，默认拒绝
        self.logger.warning(
            f"需要用户确认但没有回调: {action} {path}, 默认拒绝"
        )
        return False
    
    def set_ask_callback(self, callback: Callable):
        """设置询问回调"""
        self.ask_callback = callback
    
    def clear_rules(self):
        """清空所有规则"""
        self.rules.clear()
    
    def get_rules(self) -> List[PermissionRule]:
        """获取所有规则"""
        return self.rules.copy()


# 全局权限管理器
_permission_manager = PermissionManager()


def get_permission_manager() -> PermissionManager:
    """获取权限管理器"""
    return _permission_manager


def check_permission(action: str, path: str, agent_name: Optional[str] = None) -> bool:
    """检查权限（同步版本）"""
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            _permission_manager.check_permission(action, path, agent_name)
        )
    except RuntimeError:
        # 没有事件循环，创建新的
        return asyncio.run(
            _permission_manager.check_permission(action, path, agent_name)
        )


# 预定义的权限配置
DEFAULT_PERMISSIONS = {
    "read": {
        "*": "allow",
        "*.env": "ask",
        "*.key": "deny",
        "*.pem": "deny",
    },
    "write": {
        "*.py": "allow",
        "*.md": "allow",
        "*.txt": "allow",
        "*.env": "deny",
        "*.key": "deny",
    },
    "execute": {
        "*.sh": "ask",
        "*.bat": "ask",
        "*.exe": "deny",
    },
    "delete": {
        "*": "ask",
    }
}


STRICT_PERMISSIONS = {
    "read": {
        "*": "ask",  # 默认ask
        "*.py": "allow",  # 后面的规则会覆盖
        "*.md": "allow",
        "*.txt": "allow",
    },
    "write": {
        "*": "deny",  # 默认deny
        "*.md": "allow",  # 后面的规则会覆盖
        "*.py": "ask",
    },
    "execute": {
        "*": "deny",
    },
    "delete": {
        "*": "deny",
    }
}


def apply_default_permissions():
    """应用默认权限"""
    manager = get_permission_manager()
    manager.clear_rules()
    manager.add_rules_from_config(DEFAULT_PERMISSIONS)


def apply_strict_permissions():
    """应用严格权限"""
    manager = get_permission_manager()
    manager.clear_rules()
    manager.add_rules_from_config(STRICT_PERMISSIONS)
