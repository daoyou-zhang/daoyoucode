"""
测试验证机制和增强的权限系统
"""

import pytest
import asyncio
from pathlib import Path
from daoyoucode.agents.core.verification import (
    VerificationManager,
    VerificationLevel,
    get_verification_manager,
)
from daoyoucode.agents.core.permission import (
    PermissionManager,
    get_permission_manager,
    check_permission,
)


# ==================== 验证机制测试 ====================

def test_verification_manager_singleton():
    """测试验证管理器单例"""
    manager1 = VerificationManager()
    manager2 = get_verification_manager()
    assert manager1 is manager2


def test_verification_manager_configure():
    """测试验证管理器配置"""
    manager = get_verification_manager()
    manager.configure(
        project_root=Path("."),
        build_command="echo 'build'",
        test_command="echo 'test'",
        timeout=60
    )
    
    assert manager.project_root == Path(".")
    assert manager.build_command == "echo 'build'"
    assert manager.test_command == "echo 'test'"
    assert manager.timeout == 60


@pytest.mark.asyncio
async def test_verification_none_level():
    """测试NONE级别验证"""
    manager = get_verification_manager()
    
    result = await manager.verify(
        result={'success': True},
        level=VerificationLevel.NONE
    )
    
    assert result.passed is True
    assert result.level == VerificationLevel.NONE


@pytest.mark.asyncio
async def test_verification_basic_level():
    """测试BASIC级别验证"""
    manager = get_verification_manager()
    manager.configure(project_root=Path("."))
    
    result = await manager.verify(
        result={'success': True},
        level=VerificationLevel.BASIC
    )
    
    assert result.level == VerificationLevel.BASIC
    assert 'diagnostics' in result.details


@pytest.mark.asyncio
async def test_verification_with_files():
    """测试文件检查"""
    manager = get_verification_manager()
    manager.configure(project_root=Path("."))
    
    # 测试存在的文件
    result = await manager.verify(
        result={'success': True},
        level=VerificationLevel.BASIC,
        modified_files=[Path(__file__)]  # 测试文件本身
    )
    
    assert result.file_check_passed is True


# ==================== 权限系统测试 ====================

def test_permission_manager_singleton():
    """测试权限管理器单例"""
    manager1 = PermissionManager()
    manager2 = get_permission_manager()
    assert manager1 is manager2


def test_permission_read_allow():
    """测试读取权限 - 允许"""
    action = check_permission("read", "test.py")
    assert action == "allow"


def test_permission_read_env_ask():
    """测试读取权限 - 环境变量文件需要确认"""
    action = check_permission("read", ".env")
    assert action == "ask"
    
    action = check_permission("read", ".env.local")
    assert action == "ask"
    
    action = check_permission("read", ".env.production")
    assert action == "ask"


def test_permission_read_env_example_allow():
    """测试读取权限 - 示例文件允许"""
    action = check_permission("read", ".env.example")
    assert action == "allow"


def test_permission_read_sensitive():
    """测试读取权限 - 敏感文件"""
    # 密钥文件
    assert check_permission("read", "private.key") == "ask"
    assert check_permission("read", "cert.pem") == "ask"
    assert check_permission("read", "cert.crt") == "ask"
    
    # 包含敏感词的文件
    assert check_permission("read", "secret_config.json") == "ask"
    assert check_permission("read", "password_list.txt") == "ask"
    assert check_permission("read", "api_token.txt") == "ask"
    assert check_permission("read", "credentials.json") == "ask"


def test_permission_write_code_allow():
    """测试写入权限 - 代码文件允许"""
    assert check_permission("write", "test.py") == "allow"
    assert check_permission("write", "app.js") == "allow"
    assert check_permission("write", "main.ts") == "allow"
    assert check_permission("write", "App.jsx") == "allow"
    assert check_permission("write", "Component.tsx") == "allow"
    assert check_permission("write", "Main.java") == "allow"
    assert check_permission("write", "main.cpp") == "allow"
    assert check_permission("write", "main.go") == "allow"
    assert check_permission("write", "main.rs") == "allow"


def test_permission_write_config_allow():
    """测试写入权限 - 配置文件允许"""
    assert check_permission("write", "config.json") == "allow"
    assert check_permission("write", "config.yaml") == "allow"
    assert check_permission("write", "config.yml") == "allow"
    assert check_permission("write", "config.toml") == "allow"
    assert check_permission("write", "README.md") == "allow"


def test_permission_write_env_deny():
    """测试写入权限 - 环境变量文件禁止"""
    assert check_permission("write", ".env") == "deny"


def test_permission_write_env_example_allow():
    """测试写入权限 - 示例文件允许"""
    assert check_permission("write", ".env.example") == "allow"


def test_permission_write_sensitive_deny():
    """测试写入权限 - 敏感文件禁止"""
    assert check_permission("write", "private.key") == "deny"
    assert check_permission("write", "cert.pem") == "deny"
    assert check_permission("write", "cert.crt") == "deny"


def test_permission_write_git_deny():
    """测试写入权限 - Git目录禁止"""
    assert check_permission("write", ".git/config") == "deny"
    assert check_permission("write", ".git/HEAD") == "deny"


def test_permission_write_gitignore_allow():
    """测试写入权限 - .gitignore允许"""
    assert check_permission("write", ".gitignore") == "allow"


def test_permission_write_lock_ask():
    """测试写入权限 - 锁文件需要确认"""
    assert check_permission("write", "package-lock.json") == "ask"
    assert check_permission("write", "yarn.lock") == "ask"
    assert check_permission("write", "Pipfile.lock") == "ask"
    assert check_permission("write", "poetry.lock") == "ask"


def test_permission_delete_temp_allow():
    """测试删除权限 - 临时文件允许"""
    assert check_permission("delete", "test.pyc") == "allow"
    assert check_permission("delete", "__pycache__/test.pyc") == "allow"
    assert check_permission("delete", "app.log") == "allow"
    assert check_permission("delete", "temp.tmp") == "allow"
    assert check_permission("delete", ".DS_Store") == "allow"
    assert check_permission("delete", "dist/bundle.js") == "allow"


def test_permission_delete_important_deny():
    """测试删除权限 - 重要文件禁止"""
    assert check_permission("delete", ".env") == "deny"
    assert check_permission("delete", "private.key") == "deny"
    assert check_permission("delete", ".git/config") == "deny"
    assert check_permission("delete", "package.json") == "deny"
    assert check_permission("delete", "requirements.txt") == "deny"


def test_permission_execute_safe_allow():
    """测试执行权限 - 安全命令允许"""
    assert check_permission("execute", "git status") == "allow"
    assert check_permission("execute", "python test.py") == "allow"
    assert check_permission("execute", "npm install") == "allow"
    assert check_permission("execute", "ls -la") == "allow"
    assert check_permission("execute", "cat file.txt") == "allow"


def test_permission_execute_dangerous_deny():
    """测试执行权限 - 危险命令禁止"""
    assert check_permission("execute", "rm -rf /") == "deny"
    assert check_permission("execute", "rm -rf *") == "deny"
    assert check_permission("execute", "dd if=/dev/zero of=/dev/sda") == "deny"
    assert check_permission("execute", "mkfs.ext4 /dev/sda") == "deny"
    assert check_permission("execute", "while true; do echo 'loop'; done") == "deny"
    assert check_permission("execute", ":(){ :|:& };:") == "deny"


def test_permission_execute_need_confirm():
    """测试执行权限 - 需要确认的命令"""
    assert check_permission("execute", "rm file.txt") == "ask"
    assert check_permission("execute", "sudo apt install") == "ask"
    assert check_permission("execute", "chmod 777 file.txt") == "ask"
    assert check_permission("execute", "curl https://example.com") == "ask"
    assert check_permission("execute", "ssh user@host") == "ask"


def test_permission_external_directory():
    """测试外部目录权限"""
    assert check_permission("external_directory", "/tmp/test") == "allow"
    assert check_permission("external_directory", "/root/test") == "deny"
    assert check_permission("external_directory", "C:\\Windows\\System32") == "deny"


def test_permission_network():
    """测试网络权限"""
    assert check_permission("network", "https://api.example.com") == "allow"
    assert check_permission("network", "http://localhost:3000") == "allow"
    assert check_permission("network", "http://127.0.0.1:8000") == "allow"
    assert check_permission("network", "http://example.com") == "ask"


def test_permission_add_custom_rule():
    """测试添加自定义规则"""
    manager = get_permission_manager()
    
    # 添加自定义规则
    manager.add_rule("read", "*.secret", "deny", priority=5, reason="绝密文件")
    
    # 验证规则生效
    action = check_permission("read", "data.secret")
    assert action == "deny"


def test_permission_load_config():
    """测试从配置加载规则"""
    manager = get_permission_manager()
    
    config = {
        "read": {
            "*.custom": "deny"
        },
        "write": {
            "*.readonly": "deny"
        }
    }
    
    manager.load_config(config)
    
    assert check_permission("read", "file.custom") == "deny"
    assert check_permission("write", "file.readonly") == "deny"


def test_permission_list_categories():
    """测试列出权限类别"""
    manager = get_permission_manager()
    categories = manager.list_categories()
    
    assert "read" in categories
    assert "write" in categories
    assert "delete" in categories
    assert "execute" in categories
    assert "external_directory" in categories
    assert "network" in categories


def test_permission_list_rules():
    """测试列出权限规则"""
    manager = get_permission_manager()
    
    # 列出所有规则
    all_rules = manager.list_rules()
    assert "read" in all_rules
    assert len(all_rules["read"]) > 0
    
    # 列出特定类别的规则
    read_rules = manager.list_rules("read")
    assert "read" in read_rules
    assert len(read_rules["read"]) > 0


def test_permission_priority():
    """测试权限优先级"""
    manager = get_permission_manager()
    
    # .env.example 的优先级(5)高于 *.env.*(10)
    # 所以 .env.example 应该是 allow
    assert check_permission("read", ".env.example") == "allow"
    
    # .env.local 匹配 *.env.*(10)，应该是 ask
    assert check_permission("read", ".env.local") == "ask"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
