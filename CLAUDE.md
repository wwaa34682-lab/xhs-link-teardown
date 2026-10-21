# CLAUDE.md
与具体 agent 无关的 skill（Codex / Claude Code / Grok Bot 等通用）。用户贴小红书链接或分享文本时，读取并严格遵循 `SKILL.md`。
要点：抓取在用户本机运行；第一次使用先问有没有自己的对标库（`SKILL.md` 第 0 节）；补全拆解不编造，`待补` 保持原样；入库只追加、按记录ID去重；不登录、不发布。
测试：`python tests/mock_api.py 5599` 后 `python scripts/xhs_fetch.py https://xhslink.com/a/demo --api http://127.0.0.1:5599 --out ./tmp_lib`，再 `python scripts/kb.py init` / `write`。
