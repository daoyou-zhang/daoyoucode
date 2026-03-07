# 运行测试工作流

## 目标
运行项目的测试用例，验证代码功能是否正常。

## 关键原则
- 先确认测试命令，不要猜测
- 测试失败时提供具体的错误信息和修复建议
- 如果需要特定环境，提醒用户检查

## 推荐工具
- `discover_project_docs` - 查找测试说明
- `read_file` - 查看配置文件（package.json、pytest.ini等）
- `get_repo_structure` - 查找测试目录
- `run_command` - 执行测试命令

## 常见测试命令
- Python: `pytest`, `python -m pytest`, `python -m unittest`
- JavaScript: `npm test`, `yarn test`, `jest`
- Rust: `cargo test`
- Go: `go test ./...`
- Java: `mvn test`, `gradle test`

## 注意事项
- 先确认测试命令，查看文档或配置文件
- 测试失败时，提取错误信息和行号
- 如果测试运行时间长，可以提醒用户
- 如果需要数据库等环境，提醒用户检查
