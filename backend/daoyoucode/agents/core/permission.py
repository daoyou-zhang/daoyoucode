"""
细粒度权限控制系统

提供文件级别、目录级别、操作级别的权限控制。
采用细粒度权限规则设计
"""

from typing import Dict, List, Literal, Optional, Union, Any
from dataclasses import dataclass, field
from pathlib import Path
import fnmatch
import logging

logger = logging.getLogger(__name__)


PermissionAction = Literal["allow", "deny", "ask"]


@dataclass
class PermissionRule:
    """权限规则"""
    pattern: str                          # 匹配模式（支持通配符）
    action: PermissionAction              # 权限动作
    priority: int = 100                   # 优先级（数字越小越优先）
    reason: Optional[str] = None          # 原因说明
    
    def matches(self, path: str) -> bool:
        """检查路径是否匹配"""
        return fnmatch.fnmatch(path, self.pattern)
    
    def __repr__(self):
        return f"Rule({self.pattern} -> {self.action})"


@dataclass
class PermissionCategory:
    """权限类别"""
    name: str
    rules: List[PermissionRule] = field(default_factory=list)
    default_action: PermissionAction = "ask"
    
    def add_rule(self, pattern: str, action: PermissionAction, priority: int = 100, reason: Optional[str] = None):
        """添加规则"""
        rule = PermissionRule(pattern, action, priority, reason)
        self.rules.append(rule)
        # 按优先级排序
        self.rules.sort(key=lambda r: r.priority)
    
    def check(self, path: str) -> PermissionAction:
        """检查权限"""
        # 按优先级顺序检查规则
        for rule in self.rules:
            if rule.matches(path):
                logger.debug(f"权限匹配: {path} -> {rule}")
                return rule.action
        
        # 没有匹配的规则，使用默认动作
        logger.debug(f"权限默认: {path} -> {self.default_action}")
        return self.default_action


class PermissionManager:
    """权限管理器（单例）"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.categories: Dict[str, PermissionCategory] = {}
        self._init_default_permissions()
        self._initialized = True
        logger.info("PermissionManager 初始化完成")
    
    def _init_default_permissions(self):
        """初始化默认权限"""
        # 读取权限
        read_category = PermissionCategory("read", default_action="allow")
        read_category.add_rule("*", "allow", priority=1000)
        # 敏感文件需要确认
        read_category.add_rule("*.env", "ask", priority=10, reason="敏感文件")
        read_category.add_rule("*.env.*", "ask", priority=10, reason="敏感文件")
        read_category.add_rule("*.env.example", "allow", priority=5)  # 示例文件可以读取
        read_category.add_rule("*.env.local", "ask", priority=8, reason="本地环境变量")
        read_category.add_rule("*.env.production", "ask", priority=5, reason="生产环境变量")
        read_category.add_rule("*.key", "ask", priority=10, reason="密钥文件")
        read_category.add_rule("*.pem", "ask", priority=10, reason="证书文件")
        read_category.add_rule("*.crt", "ask", priority=10, reason="证书文件")
        read_category.add_rule("*.p12", "ask", priority=10, reason="证书文件")
        read_category.add_rule("*secret*", "ask", priority=20, reason="可能包含敏感信息")
        read_category.add_rule("*password*", "ask", priority=20, reason="可能包含密码")
        read_category.add_rule("*token*", "ask", priority=20, reason="可能包含令牌")
        read_category.add_rule("*credential*", "ask", priority=20, reason="可能包含凭证")
        read_category.add_rule(".git/config", "ask", priority=15, reason="Git配置")
        read_category.add_rule(".ssh/*", "ask", priority=10, reason="SSH密钥")
        self.categories["read"] = read_category
        
        # 写入权限（更细粒度）
        write_category = PermissionCategory("write", default_action="ask")
        # 允许写入常见代码文件
        write_category.add_rule("*.py", "allow", priority=100)
        write_category.add_rule("*.js", "allow", priority=100)
        write_category.add_rule("*.ts", "allow", priority=100)
        write_category.add_rule("*.jsx", "allow", priority=100)
        write_category.add_rule("*.tsx", "allow", priority=100)
        write_category.add_rule("*.java", "allow", priority=100)
        write_category.add_rule("*.cpp", "allow", priority=100)
        write_category.add_rule("*.c", "allow", priority=100)
        write_category.add_rule("*.h", "allow", priority=100)
        write_category.add_rule("*.go", "allow", priority=100)
        write_category.add_rule("*.rs", "allow", priority=100)
        write_category.add_rule("*.md", "allow", priority=100)
        write_category.add_rule("*.txt", "allow", priority=100)
        write_category.add_rule("*.json", "allow", priority=100)
        write_category.add_rule("*.yaml", "allow", priority=100)
        write_category.add_rule("*.yml", "allow", priority=100)
        write_category.add_rule("*.toml", "allow", priority=100)
        write_category.add_rule("*.ini", "allow", priority=100)
        write_category.add_rule("*.cfg", "allow", priority=100)
        # 禁止写入敏感文件
        write_category.add_rule("*.env", "deny", priority=10, reason="禁止修改环境变量文件")
        write_category.add_rule("*.env.*", "ask", priority=15, reason="环境变量文件需要确认")
        write_category.add_rule("*.env.example", "allow", priority=5)  # 示例文件可以修改
        write_category.add_rule("*.key", "deny", priority=10, reason="禁止修改密钥文件")
        write_category.add_rule("*.pem", "deny", priority=10, reason="禁止修改证书文件")
        write_category.add_rule("*.crt", "deny", priority=10, reason="禁止修改证书文件")
        write_category.add_rule(".git/*", "deny", priority=10, reason="禁止直接修改Git目录")
        write_category.add_rule(".gitignore", "allow", priority=5)  # 但允许修改.gitignore
        write_category.add_rule("package-lock.json", "ask", priority=20, reason="锁文件需要确认")
        write_category.add_rule("yarn.lock", "ask", priority=20, reason="锁文件需要确认")
        write_category.add_rule("Pipfile.lock", "ask", priority=20, reason="锁文件需要确认")
        write_category.add_rule("poetry.lock", "ask", priority=20, reason="锁文件需要确认")
        self.categories["write"] = write_category
        
        # 删除权限（更细粒度）
        delete_category = PermissionCategory("delete", default_action="ask")
        # 允许删除临时文件
        delete_category.add_rule("*.pyc", "allow", priority=100)
        delete_category.add_rule("__pycache__/*", "allow", priority=100)
        delete_category.add_rule("*.log", "allow", priority=100)
        delete_category.add_rule("*.tmp", "allow", priority=100)
        delete_category.add_rule("*.temp", "allow", priority=100)
        delete_category.add_rule("*.cache", "allow", priority=100)
        delete_category.add_rule(".DS_Store", "allow", priority=100)
        delete_category.add_rule("Thumbs.db", "allow", priority=100)
        delete_category.add_rule("node_modules/*", "ask", priority=50, reason="依赖目录")
        delete_category.add_rule("dist/*", "allow", priority=100)
        delete_category.add_rule("build/*", "allow", priority=100)
        # 禁止删除重要文件
        delete_category.add_rule("*.env", "deny", priority=10, reason="禁止删除环境变量文件")
        delete_category.add_rule("*.key", "deny", priority=10, reason="禁止删除密钥文件")
        delete_category.add_rule("*.pem", "deny", priority=10, reason="禁止删除证书文件")
        delete_category.add_rule(".git/*", "deny", priority=10, reason="禁止删除Git目录")
        delete_category.add_rule("package.json", "deny", priority=10, reason="禁止删除包配置")
        delete_category.add_rule("requirements.txt", "deny", priority=10, reason="禁止删除依赖文件")
        delete_category.add_rule("Pipfile", "deny", priority=10, reason="禁止删除依赖文件")
        delete_category.add_rule("pyproject.toml", "deny", priority=10, reason="禁止删除项目配置")
        self.categories["delete"] = delete_category
        
        # 执行权限（更细粒度）
        execute_category = PermissionCategory("execute", default_action="ask")
        # 允许常见的安全命令
        execute_category.add_rule("git *", "allow", priority=100)
        execute_category.add_rule("python *", "allow", priority=100)
        execute_category.add_rule("python3 *", "allow", priority=100)
        execute_category.add_rule("pip *", "allow", priority=100)
        execute_category.add_rule("pip3 *", "allow", priority=100)
        execute_category.add_rule("npm *", "allow", priority=100)
        execute_category.add_rule("yarn *", "allow", priority=100)
        execute_category.add_rule("pnpm *", "allow", priority=100)
        execute_category.add_rule("node *", "allow", priority=100)
        execute_category.add_rule("cargo *", "allow", priority=100)
        execute_category.add_rule("go *", "allow", priority=100)
        execute_category.add_rule("make *", "allow", priority=100)
        execute_category.add_rule("cmake *", "allow", priority=100)
        execute_category.add_rule("ls *", "allow", priority=100)
        execute_category.add_rule("cat *", "allow", priority=100)
        execute_category.add_rule("grep *", "allow", priority=100)
        execute_category.add_rule("find *", "allow", priority=100)
        execute_category.add_rule("echo *", "allow", priority=100)
        # 危险命令需要确认或禁止
        execute_category.add_rule("rm -rf *", "deny", priority=10, reason="危险命令")
        execute_category.add_rule("rm -rf /*", "deny", priority=5, reason="极度危险")
        execute_category.add_rule("rm -rf .*", "deny", priority=8, reason="删除隐藏文件")
        execute_category.add_rule("rm *", "ask", priority=50, reason="删除命令需要确认")
        execute_category.add_rule("sudo *", "ask", priority=20, reason="需要管理员权限")
        execute_category.add_rule("su *", "ask", priority=20, reason="切换用户")
        execute_category.add_rule("chmod *", "ask", priority=30, reason="修改权限")
        execute_category.add_rule("chown *", "ask", priority=30, reason="修改所有者")
        execute_category.add_rule("dd *", "deny", priority=10, reason="危险的磁盘操作")
        execute_category.add_rule("mkfs*", "deny", priority=10, reason="格式化磁盘")
        execute_category.add_rule("fdisk *", "deny", priority=10, reason="磁盘分区")
        execute_category.add_rule("curl *", "ask", priority=50, reason="网络请求")
        execute_category.add_rule("wget *", "ask", priority=50, reason="网络下载")
        execute_category.add_rule("ssh *", "ask", priority=30, reason="远程连接")
        execute_category.add_rule("scp *", "ask", priority=30, reason="远程复制")
        execute_category.add_rule("rsync *", "ask", priority=30, reason="远程同步")
        # 防止无限循环
        execute_category.add_rule("while true*", "deny", priority=10, reason="无限循环")
        execute_category.add_rule(":(){ :|:& };:", "deny", priority=5, reason="Fork炸弹")
        self.categories["execute"] = execute_category
        
        # 外部目录访问权限
        external_category = PermissionCategory("external_directory", default_action="ask")
        external_category.add_rule("/tmp/*", "allow", priority=100)
        external_category.add_rule("/home/*", "ask", priority=200)
        external_category.add_rule("/root/*", "deny", priority=10, reason="禁止访问root目录")
        external_category.add_rule("C:\\Windows\\*", "deny", priority=10, reason="禁止访问系统目录")
        self.categories["external_directory"] = external_category
        
        # 网络访问权限
        network_category = PermissionCategory("network", default_action="ask")
        network_category.add_rule("https://*", "allow", priority=100)
        network_category.add_rule("http://localhost*", "allow", priority=50)
        network_category.add_rule("http://127.0.0.1*", "allow", priority=50)
        network_category.add_rule("http://*", "ask", priority=200, reason="非HTTPS连接")
        self.categories["network"] = network_category
    
    def check_permission(
        self, 
        category: str, 
        path: str,
        auto_approve: bool = False
    ) -> PermissionAction:
        """
        检查权限
        
        Args:
            category: 权限类别（read, write, delete, execute等）
            path: 路径或命令
            auto_approve: 是否自动批准（用于测试）
            
        Returns:
            权限动作
        """
        if auto_approve:
            return "allow"
        
        cat = self.categories.get(category)
        if not cat:
            logger.warning(f"未知的权限类别: {category}")
            return "ask"
        
        action = cat.check(path)
        logger.info(f"权限检查: {category}:{path} -> {action}")
        return action
    
    def add_rule(
        self, 
        category: str, 
        pattern: str, 
        action: PermissionAction,
        priority: int = 100,
        reason: Optional[str] = None
    ):
        """
        添加权限规则
        
        Args:
            category: 权限类别
            pattern: 匹配模式
            action: 权限动作
            priority: 优先级
            reason: 原因说明
        """
        if category not in self.categories:
            self.categories[category] = PermissionCategory(category)
        
        self.categories[category].add_rule(pattern, action, priority, reason)
        logger.info(f"添加权限规则: {category}:{pattern} -> {action}")
    
    def load_config(self, config: Dict[str, Any]):
        """
        从配置加载权限规则
        
        配置格式:
        {
            "read": {
                "*.secret": "deny",
                "*.public": "allow"
            },
            "write": {
                "*.lock": "deny"
            }
        }
        """
        for category, rules in config.items():
            if isinstance(rules, dict):
                for pattern, action in rules.items():
                    if action in ["allow", "deny", "ask"]:
                        self.add_rule(category, pattern, action)
                    else:
                        logger.warning(f"无效的权限动作: {action}")
            else:
                logger.warning(f"无效的权限配置: {category}")
    
    def get_category(self, category: str) -> Optional[PermissionCategory]:
        """获取权限类别"""
        return self.categories.get(category)
    
    def list_categories(self) -> List[str]:
        """列出所有权限类别"""
        return list(self.categories.keys())
    
    def list_rules(self, category: Optional[str] = None) -> Dict[str, List[PermissionRule]]:
        """
        列出权限规则
        
        Args:
            category: 可选的类别过滤
            
        Returns:
            类别到规则列表的映射
        """
        if category:
            cat = self.categories.get(category)
            return {category: cat.rules if cat else []}
        
        return {
            name: cat.rules
            for name, cat in self.categories.items()
        }
    
    def clear(self, category: Optional[str] = None):
        """
        清空权限规则
        
        Args:
            category: 可选的类别过滤，None表示清空所有
        """
        if category:
            if category in self.categories:
                self.categories[category].rules = []
                logger.info(f"清空权限规则: {category}")
        else:
            for cat in self.categories.values():
                cat.rules = []
            logger.info("清空所有权限规则")


# 全局权限管理器实例
_permission_manager = PermissionManager()


def get_permission_manager() -> PermissionManager:
    """获取权限管理器实例"""
    return _permission_manager


def check_permission(
    category: str, 
    path: str,
    auto_approve: bool = False
) -> PermissionAction:
    """
    便捷函数：检查权限
    
    Args:
        category: 权限类别
        path: 路径或命令
        auto_approve: 是否自动批准
        
    Returns:
        权限动作
    """
    manager = get_permission_manager()
    return manager.check_permission(category, path, auto_approve)


def require_permission(category: str):
    """
    权限装饰器
    
    使用示例:
        @require_permission("write")
        def write_file(path: str, content: str):
            # 自动检查写入权限
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 尝试从参数中提取路径
            path = kwargs.get('path') or (args[0] if args else None)
            if not path:
                logger.warning(f"无法从参数中提取路径，跳过权限检查")
                return func(*args, **kwargs)
            
            action = check_permission(category, str(path))
            
            if action == "deny":
                raise PermissionError(f"权限被拒绝: {category}:{path}")
            elif action == "ask":
                # 这里应该询问用户，简化起见直接拒绝
                logger.warning(f"需要用户确认: {category}:{path}")
                raise PermissionError(f"需要用户确认: {category}:{path}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
