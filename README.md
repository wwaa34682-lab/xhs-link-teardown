# xhs-link-teardown（小红书 贴链接 → 拆解 → 入对标库）

> An agent skill: paste a Xiaohongshu share link → fetch the post → tear it down with a fixed template → append it to your benchmark library (CSV / Excel / Feishu). Works with Codex, Claude Code and other agents.

## 它做什么
贴一条（或多条）小红书「分享 → 复制链接」的文字，agent 自动：
1. 抓取原图、标题、正文、标签和点赞/收藏/分享数据（接口没给的标「待补」，不乱填）；
2. 按 `templates/拆解模板.md` 逐图拆解；
3. **只追加**写入你的对标库，已存在自动跳过；
4. 回复 3–5 行要点 +「可借鉴到你品牌的点」。

流程细节见 `SKILL.md`（Codex 读 `AGENTS.md`，Claude Code 读 `CLAUDE.md`）。

## 运行环境要求
必须在**小红书能正常访问的网络**（中国大陆网络）的电脑上运行抓取；境外服务器会被跳转到登录页。

## 第一次使用
agent 会先问你品牌名，再问：**你已经有自己的对标库吗？**
- **有**：给出位置后，agent 只读地读出列名，生成「标准字段 → 你的列」映射请你确认，确认后才写入；
- **没有**：按标准结构新建——默认本地 CSV（零配置），也可选 Excel 或飞书多维表格（见下）。

## 日常使用
在小红书 App 点「分享 → 复制链接」，把整段文字发给 agent（可一次多条）。它会抓取 → 拆解 → 入库 → 回你要点和记录位置。


## 一次性安装（Windows）
抓取依赖外部工具 [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader)（**GPL-3.0，需你自行安装**，本仓库不含其代码，只调用它的本地接口）。需先装好 git 和 [uv](https://docs.astral.sh/uv/)：
```
mkdir %USERPROFILE%\xhs-tools && cd %USERPROFILE%\xhs-tools
git clone https://github.com/JoeanAmier/XHS-Downloader.git
cd XHS-Downloader
uv venv --python 3.12 .venv
uv pip install -p .venv\Scripts\python.exe -r requirements.txt pyyaml openpyxl -i https://pypi.tuna.tsinghua.edu.cn/simple
```
XHS-Downloader 为 GPL-3.0 外部工具，本 skill 只调用它的本地接口，不含其代码。

## 配置
复制 `config/kb_local.example.yaml` 为 `config/kb_local.yaml`（已被 .gitignore 忽略，不要提交）。标准库结构在 `config/kb_schema.yaml`。

## 对标库三种存法
- **本地 CSV（默认，零配置）**：`python scripts/kb.py init`
- **Excel**：`python scripts/kb.py init --backend xlsx`
- **飞书多维表格（用你自己的飞书应用）**：
  1. 打开 https://open.feishu.cn/app → 创建企业自建应用，记下 App ID / App Secret。
  2. 「权限管理」开通：`bitable:app`（查看、评论、编辑和管理多维表格）。发布版本，等管理员审批。
  3. 设置环境变量（PowerShell）：`$env:FEISHU_APP_ID="cli_xxx"; $env:FEISHU_APP_SECRET="xxx"`（别写进任何文件）。
  4. 新建库：`python scripts/kb.py init --backend feishu`，把输出的 app_token / table_id 填进 kb_local.yaml，`backend: feishu`。
     用已有表：在表格右上角「…→ 更多 → 添加文档应用」把你的应用加进来（可编辑），从链接 `/base/<app_token>?table=<table_id>` 填进 kb_local.yaml。
  5. `python scripts/kb.py check` 核对列映射，确认后把 `confirmed_mapping` 改为 true。

## 规则
- 不登录小红书，**绝不使用主号 Cookie**；不发布、不评论、不私信。
- 抓到的原图原文**只做内部研究**，不转发、不当自家素材。
- 链接要**刚从 App 复制**的分享链接，过期请重新复制。
- 只新增行，不改、不删已有行，不改表结构；记录ID 已存在就跳过。不登录小红书，不发布、不评论。

## 相关项目
完整的小红书内容工作流（选题、出图、审核、复盘）：https://github.com/wwaa34682-lab/xhs-workflow-kit

## 许可证
MIT。XHS-Downloader 为独立的 GPL-3.0 项目，遵循其自身许可。
