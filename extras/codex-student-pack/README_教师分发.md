# 教师分发说明

仅分发此目录的 ZIP。包内是团队安装器和控制模板，不含上游源码、教师测试项目或凭据。学生安装时从原仓库获取锁定提交；不要改用 main。

- 上游：https://github.com/XiaoMaColtAI/math-modeling-skill
- 固定提交：abecb641491932d851a57709ed4e7ea66372281d
- 学生无需交给 Codex 复杂安装提示词；安装脚本不调用模型。后续只按学生 README 做一次加载确认及逐阶段执行。
- Windows 默认双击 INSTALL_STUDENT.cmd；指定新目录：`INSTALL_STUDENT.cmd -TargetProject "D:\Modeling\Team01"`；检查同一目录：`VERIFY_INSTALL.cmd -TargetProject "D:\Modeling\Team01"`。
- Python 可经 py/python/python3 或已有 Codex bundled runtime 发现；非标准路径可传 `-PythonExe "D:\Python\python.exe"`。缺失时明确退出，教师人工安装 Git/Python，不用 Codex 猜修复。
- PowerShell 启动参数只作用于本次进程，不修改系统执行策略或任何全局 Codex 配置。不要求管理员权限或 API Key。
- 安装保留 Skill 的 SKILL.md、使用指南、VERSION、README、references、assets、tools，省去 .git、CI、dsh 副本、Star 图片及 tests 等非运行材料；所选文件内容不变，HEAD 和入口 SHA256 均核验。
- 项目控制层关闭自动建模改线、论文、默认多 Agent、默认图数和无界返工。它是项目约定，不是硬件级隔离；不能称上游独立门禁通过。每阶段教师必须提供批准状态、数据含义、路线、baseline、图表清单、预算及依赖。
- 已存在同名文件内容不一致即停；不会覆盖已填写的 TASK_BRIEF。需要重新安装时使用新空目录。验证允许 TASK_BRIEF 正常修改，但校验上游和控制模板哈希。
- 安装不配置完整建模 Python/MATLAB 环境；数学计算依赖按批准方案单独准备，不能把安装成功当成算法/论文验收。
- 已知上游问题：check_env.py 的 `pulp|ortools` 安装建议不可直接复制执行；DOCX check_env 漏查 defusedxml。未改上游逻辑。
- 许可边界：全仓库再分发许可未明确，docx/pdf/xlsx 子工具含专有条款；UI 子包 MIT 不覆盖全仓库。此包采用原仓库固定提交获取方案，不等于使用权或授权链已获确认。
- “低 token”指安装不调用模型、阶段按需加载；不承诺固定 token 数，实际用量还取决于学生已有 Skill/插件、模型和任务。

本包不包含任何赛题、数据、批准模型或最终结论。初始 TASK_BRIEF=NOT_APPROVED，应触发人工复核。
