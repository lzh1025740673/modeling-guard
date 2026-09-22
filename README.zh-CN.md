# Modeling Guard · 建模验收助手

**教师先确认，学生按阶段运行，结果留下可检查的记录。**

[English](README.md) · [任务配置](docs/CONTRACT.md) · [能力边界](SECURITY.md)

面向使用 AI 辅助编程的数学建模团队。教师审核任务、代码和数据后，工具记录文件指纹；学生运行一次实验，工具检查时间、日志、次数、输出和指标阈值，生成可直接打开的 HTML 验收报告。

核心功能只需要 **Python 3.10+**。不需要 GitHub 账号、Git、API Key 或 AI 会员；不调用模型、不上传数据、不安装全局配置。

## 学生怎么用

1. 在仓库点 **Code → Download ZIP**，下载并解压。公开仓库下载不用注册 GitHub。
2. Windows 双击 **RUN_DEMO.cmd**。脚本检测 Python，创建新演示文件夹，运行合成数据验收，并打开报告。如果缺少 Python，请从 [Python 官网](https://www.python.org/downloads/) 安装 3.10 或更高版本后重试。
3. 看到 `PASS` 和 MAE `1.0`，表示演示流程通过。这里是五行明确标注的合成数据，不是赛题、训练结果或竞赛成绩。

教师和开发者也可以在解压目录打开终端，逐条执行：

```powershell
py -3 -m modeling_guard init demo-project
py -3 -m modeling_guard check demo-project
# 先阅读 demo-project 中的任务和代码，再由教师确认。
py -3 -m modeling_guard approve demo-project --teacher "演示审核人"
py -3 -m modeling_guard run demo-project
```

macOS/Linux 使用 `python3` 替换 `py -3`。命令最后会显示 `report.html` 的路径，双击即可查看。

## 正式使用时教师负责什么

- 明确当前阶段、输入数据含义、方法和评价标准。
- 修改 `experiment.json`，写入命令参数、所有本地代码和数据、输出文件、指标阈值、秒数和次数预算。
- 阅读实际代码；`check` 只检查配置有效性，不代表算法正确。
- 审核后执行 `approve`。学生再执行 `run`。修改任务、输入或代码会使旧审批失效。
- 失败、超时、指标不达标时先查看 `HUMAN_REVIEW.md`，教师复核后再批准。工具不会自动换模型或扩大预算。

每次运行使用独立快照，保留命令、文件 SHA-256、Python/系统版本、日志、输出和报告。一次只运行一个阶段。报告中的 `PASS` 只表示预先声明的检查通过，**不能证明建模思路、无信息泄漏或论文结论正确**。

## 别的 AI 软件能用吗

核心是普通 Python 命令，不绑定 AI 平台。支持终端的 AI 软件可以调用，学生也可以手动运行。普通网页聊天不能直接运行本地命令。

`AGENTS.md` 是给配合规则的 AI 助手看的简短说明，各软件是否自动读取需单独确认。审批记录是本地可编辑文件，无法防止学生或 AI 故意绕过；如需强制隔离，应由教师控制的服务或操作系统沙箱承担。详见 [集成说明](docs/INTEGRATIONS.md)。

## 之前的 Skill 安装包在哪里

`extras/codex-student-pack/` 保留了原来的学生安装器和团队模板，只按固定提交从原作者仓库下载，不打包原作者源码。它需要 Python、Git 和网络，许可条件需要另行确认；**本项目核心功能不依赖它**。已有 Skill 不会被核心工具修改。

这里的“低 token”指安装和校验过程不消耗模型调用，不能保证某个节省比例。核心工具本身没有 token 计量、计费控制或 GPU/内存配额功能。

## 项目现状与参与

这是 v0.1.0 初版，欢迎教师和学生提交真实的安装问题、失败日志的脱敏片段、验收规则建议和测试。不要上传正式赛题保密材料、学生个人信息、API Key 或完整私有运行目录。

测试与已知边界见 [VALIDATION.md](docs/VALIDATION.md) 和 [SECURITY.md](SECURITY.md)。本项目为独立开源项目，非 OpenAI 官方项目，不承诺竞赛成绩、社区热度或活动奖励。原创代码和文档使用 MIT 许可，外部软件保留各自条款。
