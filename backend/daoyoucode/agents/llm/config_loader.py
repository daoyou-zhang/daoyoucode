"""
LLM配置加载器
从配置文件加载API密钥和提供商配置
"""

import yaml
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def load_llm_config(config_path: str = None) -> dict:
    """
    加载LLM配置
    
    Args:
        config_path: 配置文件路径，默认为 backend/config/llm_config.yaml
    
    Returns:
        配置字典
    """
    if config_path is None:
        # 默认配置路径
        backend_dir = Path(__file__).parent.parent.parent.parent
        config_path = backend_dir / "config" / "llm_config.yaml"
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        logger.warning(f"配置文件不存在: {config_path}")
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"已加载LLM配置: {config_path}")
        return config
    
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return {}


def configure_from_file(client_manager, config_path: str = None):
    """
    从配置文件配置客户端管理器
    
    Args:
        client_manager: LLMClientManager实例
        config_path: 配置文件路径
    """
    config = load_llm_config(config_path)
    
    if not config:
        logger.warning("未加载任何配置")
        return
    
    providers = config.get('providers', {})
    configured_count = 0
    
    for provider_name, provider_config in providers.items():
        # 检查是否启用
        if not provider_config.get('enabled', False):
            logger.debug(f"提供商 {provider_name} 未启用")
            continue
        
        # 检查API密钥
        api_key = provider_config.get('api_key', '')
        if not api_key or api_key.startswith('your-'):
            logger.warning(f"提供商 {provider_name} 的API密钥未配置")
            continue
        
        # 配置提供商
        try:
            client_manager.configure_provider(
                provider=provider_name,
                api_key=api_key,
                base_url=provider_config.get('base_url'),
                models=provider_config.get('models', [])
            )
            configured_count += 1
            logger.info(f"✓ 已配置提供商: {provider_name}")
        
        except Exception as e:
            logger.error(f"配置提供商 {provider_name} 失败: {e}")
    
    if configured_count == 0:
        logger.warning("未配置任何LLM提供商，请检查配置文件")
    else:
        logger.info(f"成功配置 {configured_count} 个LLM提供商")


def configure_from_env(client_manager):
    """
    从环境变量配置客户端管理器
    
    支持的环境变量:
    - QWEN_API_KEY
    - DEEPSEEK_API_KEY
    - OPENAI_API_KEY
    - ANTHROPIC_API_KEY
    """
    env_configs = {
        'qwen': {
            'env_var': 'QWEN_API_KEY',
            'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            'models': ['qwen-max', 'qwen-plus', 'qwen-coder-plus']
        },
        'deepseek': {
            'env_var': 'DEEPSEEK_API_KEY',
            'base_url': 'https://api.deepseek.com/v1',
            'models': ['deepseek-chat', 'deepseek-coder']
        },
        'openai': {
            'env_var': 'OPENAI_API_KEY',
            'base_url': 'https://api.openai.com/v1',
            'models': ['gpt-4', 'gpt-3.5-turbo']
        },
        'anthropic': {
            'env_var': 'ANTHROPIC_API_KEY',
            'base_url': 'https://api.anthropic.com/v1',
            'models': ['claude-3-opus', 'claude-3-sonnet']
        }
    }
    
    configured_count = 0
    
    for provider_name, config in env_configs.items():
        api_key = os.getenv(config['env_var'])
        
        if api_key:
            try:
                client_manager.configure_provider(
                    provider=provider_name,
                    api_key=api_key,
                    base_url=config['base_url'],
                    models=config['models']
                )
                configured_count += 1
                logger.info(f"✓ 从环境变量配置提供商: {provider_name}")
            
            except Exception as e:
                logger.error(f"配置提供商 {provider_name} 失败: {e}")
    
    if configured_count > 0:
        logger.info(f"从环境变量成功配置 {configured_count} 个LLM提供商")


def auto_configure(client_manager, config_path: str = None):
    """
    自动配置：先尝试配置文件，再尝试环境变量
    
    Args:
        client_manager: LLMClientManager实例
        config_path: 配置文件路径
    """
    # 1. 尝试从配置文件加载
    configure_from_file(client_manager, config_path)
    
    # 2. 如果没有配置任何提供商，尝试从环境变量加载
    if not client_manager.provider_configs:
        logger.info("配置文件未配置提供商，尝试从环境变量加载...")
        configure_from_env(client_manager)
    
    # 3. 最终检查
    if not client_manager.provider_configs:
        logger.warning("⚠ 未配置任何LLM提供商")
        logger.warning("请配置 backend/config/llm_config.yaml 或设置环境变量")
    else:
        providers = list(client_manager.provider_configs.keys())
        logger.info(f"✓ LLM配置完成，可用提供商: {', '.join(providers)}")
