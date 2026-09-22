# 学生安装

前提：Windows、Git、Python ≥3.10、已可使用的 Codex；安装时能访问 GitHub。缺少前提会停止，请找教师处理。

解压后双击 **INSTALL_STUDENT.cmd**，看到 `INSTALL_OK` 后完成。默认项目是本包旁的 `math_modeling_project`；冲突时不覆盖，可换一个空目录。`VERIFY_INSTALL.cmd` 可离线检查文件。

### Step 1

在新项目目录重新打开 Codex。

### Step 2

```text
请确认项目中的数学建模 Skill 已加载。
只回复：
SKILL_READY
或者
SKILL_NOT_READY + 原因
不要执行任何建模任务。
```

### Step 3

比赛当天教师给出赛题、数据和已批准的 `TASK_BRIEF.md`。只输入：

```text
读取 AGENTS.md、TASK_BRIEF.md、赛题和附件。

严格按 TASK_BRIEF 执行当前阶段。
不要重新设计整套模型。
不得自行更换主路线。

如遇 AGENTS.md 中规定的停止条件，
生成 reports/HUMAN_REVIEW.md 后立即停止。

正常完成当前阶段后，
生成 reports/STAGE_REPORT.md 后停止。
```
