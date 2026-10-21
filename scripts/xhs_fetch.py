#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小红书对标帖抓取：调用本机 XHS-Downloader API（外部工具，GPL-3.0，本脚本不含其代码）。
用法: python xhs_fetch.py "<链接或分享文本>" ["<更多>" ...] [--file links.txt] [--out 目录]
"""
import argparse, csv, json, os, re, subprocess, sys, time, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

DEFAULT_DL = os.environ.get("XHS_DOWNLOADER_DIR", str(Path.home() / "xhs-tools" / "XHS-Downloader"))
DEFAULT_API = os.environ.get("XHS_API", "http://127.0.0.1:5556")
TBD = "待补"
TBA = "【待拆解】"

def load_brand():
    """从 config/kb_local.yaml 读 brand（不依赖 pyyaml）；没有则用「本品牌」。"""
    p = Path(__file__).resolve().parent.parent / "config" / "kb_local.yaml"
    if p.exists():
        m = re.search(r"^brand:\s*([^#\n]+)", p.read_text(encoding="utf-8"), re.M)
        if m and m.group(1).strip(): return m.group(1).strip()
    return "本品牌"

BRAND = load_brand()
URL_RE = re.compile(r"https?://(?:www\.)?(?:xhslink\.com|xhslink\.cn|xiaohongshu\.com)/[^\s，。,\"'<>）)】]+", re.I)

def extract_links(texts):
    out = []
    for t in texts:
        for u in URL_RE.findall(t):
            if u not in out: out.append(u)
    return out

def v(x):
    if x is None: return TBD
    if isinstance(x, (int, float)) and x < 0: return TBD
    s = str(x).strip()
    return TBD if s in ("", "-1", "None", "null") else s

def api_alive(api):
    try:
        urllib.request.urlopen(api + "/docs", timeout=3); return True
    except urllib.error.HTTPError: return True
    except Exception: return False

def start_api(dl_dir, api):
    dl = Path(dl_dir)
    py = dl / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not (dl / "main.py").exists() or not py.exists():
        sys.exit(f"找不到 XHS-Downloader：{dl}\n请按 SKILL.md 的「新电脑安装」先装好，或用 --downloader 指定路径。")
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    log = open(dl / "api_log.txt", "w", encoding="utf-8")
    p = subprocess.Popen([str(py), "main.py", "api"], cwd=str(dl), stdout=log, stderr=log,
                         stdin=subprocess.DEVNULL, env=env, creationflags=flags)
    for _ in range(40):
        if api_alive(api): return p
        if p.poll() is not None: break
        time.sleep(1)
    p.kill()
    sys.exit(f"XHS-Downloader 接口没能启动，请看日志：{dl / 'api_log.txt'}")

def fetch(api, url):
    body = json.dumps({"url": url, "download": False}).encode("utf-8")
    req = urllib.request.Request(api + "/xhs/detail", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def safe_name(s, n=12):
    s = re.sub(r'[\\/:*?"<>|\r\n\t#@]+', "", s or "").strip()
    return (s[:n] or "无标题")

def tags_list(t):
    if not t or t == -1: return []
    if isinstance(t, list): return [str(i) for i in t if str(i).strip()]
    return [i for i in re.split(r"[\s,，#]+", str(t)) if i]

def dl_images(urls, folder):
    saved = []
    for i, u in enumerate(urls, 1):
        f = folder / f"{i:02d}.jpg"
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.xiaohongshu.com/"})
            with urllib.request.urlopen(req, timeout=60) as r: f.write_bytes(r.read())
            saved.append(f.name)
        except Exception as e:
            print(f"  ⚠ 第{i}张图下载失败（{e}），已跳过", file=sys.stderr)
        time.sleep(0.5)
    return saved

def render_md(d, link, imgs, is_video, today):
    title, desc = v(d.get("作品标题")), v(d.get("作品描述"))
    tags = " ".join("#" + t for t in tags_list(d.get("作品标签"))) or TBD
    nid = v(d.get("作品ID"))
    plink = v(d.get("作品链接")) if v(d.get("作品链接")) != TBD else link
    data = f"{v(d.get('点赞数量'))}赞、{v(d.get('收藏数量'))}藏、{v(d.get('评论数量'))}评、{v(d.get('分享数量'))}分享"
    rows = [
        ("样本ID", f"BM-{nid}"), ("资格", "候选（评论意向未核验）"), ("首图附件 / 其余图附件", ", ".join(imgs) or TBD),
        ("标题", title), ("行业", TBA), ("发布日期原样", v(d.get("发布时间"))),
        ("日期解释", v(d.get("发布时间"))), ("日期证据状态", "来自 XHS-Downloader 接口返回的发布时间，未在页面核对"),
        ("已核不同用户下限", TBD), ("已核意向评论下限", TBD), ("拆解图片数", str(len(imgs))),
        ("已取全图", "否（视频，仅文案）" if is_video else ("是" if imgs else "否")),
        ("帖子链接", plink), ("筛选状态", "未核验近一年与意向评论门槛"),
        ("评论核验口径", "未加载评论（本工具不抓评论）"),
        ("图序观察", TBA), ("设计结论", TBA), ("点击机制_推断", TBA + "（结尾注明：没有曝光/CTR/成交归因）"),
        ("咨询解释", TBA), (f"{BRAND}迁移", TBA), ("不可照搬", TBA), ("查看边界", TBA),
        ("作者", v(d.get("作者昵称")) + f"（{v(d.get('作者链接'))}）"),
        ("文案/正文摘要", "见 caption.txt"), ("标签", tags),
        ("文案记录方式", "接口返回的标题+正文全文，原样存于 caption.txt"),
    ]
    L = [f"# 拆解：{title}", "",
         f"> 抓取日期 {today}；互动数据（采集时）：{data}。-1/缺失一律写“{TBD}”，不补零。",
         f"> 作品类型：{v(d.get('作品类型'))}；作品ID：{nid}", "",
         "## A1 样本概览", f"样本BM-{nid} {title}。候选；日期未在页面核验；已核咨询下限 {TBD}。", "",
         "## A2 逐帖摘要", "| # | 字段 | 内容 |", "|---|---|---|"]
    for i, (k, val) in enumerate(rows, 1):
        L.append(f"| {i} | {k} | {str(val).replace('|', '／').replace(chr(10), ' ')} |")
    L += ["", "## A3 逐图详解"]
    if is_video:
        L += ["", "⚠ 视频笔记：只保存了文案。请用户在 App 里截 3–5 张关键帧（开头/卖点/结尾）发来，再按下面格式逐张填写（注明“只分析静态关键帧”）。"]
    for i, f in enumerate(imgs or (["关键帧01.jpg"] if is_video else []), 1):
        L += ["", "```", f"样本 BM-{nid} {TBA}（图片角色）", f"{TBA}（行业） | 候选/日期未核 | BM-{nid}_P{i:02d}", "",
              f"构图：{TBA}", f"主体比例：{TBA}", f"字体与配色：{TBA}（字体层级） {TBA}（配色）",
              f"信息作用：{TBA}", f"优点与局限：{TBA}（优点） {TBA}（局限）", f"可迁移到{BRAND}：{TBA}",
              f"推断与边界：{TBA}", "", f"图{i} {TBA}（W×H px） 文件 {f}",
              "网页配图原始下载（XHS-Downloader 接口地址）", f"发布者：{v(d.get('作者昵称'))}", "原图未做视觉改写", f"打开该样本原帖 {plink}", "```",
              f"阅读顺序_推断：{TBA}　不可照搬：{TBA}　图示区域_近似归一坐标：{TBA}"]
    L += ["", "## A4 咨询证据", "| 匿名编号 | 样本ID | 资格 | 所属帖子 | 评论短证据 | 原有意向判断理由 | 原帖链接 |",
          "|---|---|---|---|---|---|---|", f"| {TBD} | BM-{nid} | 候选 | {title} | {TBD}（本工具不抓评论） | {TBD} | {plink} |",
          "", f"## 可借鉴到{BRAND}的点", f"- {TBA}", f"- {TBA}", f"- {TBA}", "",
          "---", f"观察与推断分开记录；原帖图片仅作设计研究参考，不作为{BRAND}可用商业素材。", ""]
    return "\n".join(L)

CSV_HEAD = ["抓取日期", "标题", "作者", "类型", "点赞", "收藏", "评论", "分享", "标签", "链接", "文件夹"]

def main():
    ap = argparse.ArgumentParser(description="小红书对标帖抓取")
    ap.add_argument("inputs", nargs="*", help="链接或整段分享文本")
    ap.add_argument("--file", help="每行一个链接/分享文本的 txt")
    ap.add_argument("--out", default=str(Path.home() / "xhs-tools" / "对标库"))
    ap.add_argument("--downloader", default=DEFAULT_DL)
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("--delay", type=float, default=3.0)
    a = ap.parse_args()
    texts = list(a.inputs)
    if a.file: texts += Path(a.file).read_text(encoding="utf-8-sig").splitlines()
    links = extract_links(texts)
    if not links: sys.exit("没找到小红书链接。请在 App 里点「分享→复制链接」，把整段文字贴过来。")
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    proc = None if api_alive(a.api) else start_api(a.downloader, a.api)
    today = datetime.now().strftime("%Y%m%d")
    ok = fail = 0
    try:
        for n, link in enumerate(links, 1):
            if n > 1: time.sleep(a.delay)
            print(f"[{n}/{len(links)}] {link}")
            try:
                res = fetch(a.api, link)
            except Exception as e:
                print(f"  ✗ 接口请求失败（{e}）。请确认 XHS-Downloader 正常运行。"); fail += 1; continue
            d = res.get("data") if isinstance(res, dict) else None
            if not d or not isinstance(d, dict):
                msg = (res or {}).get("message", "") if isinstance(res, dict) else ""
                print(f"  ✗ 没取到内容：链接过期或无效，请重新在App里分享→复制链接。（接口提示：{msg or '无'}）"); fail += 1; continue
            title = v(d.get("作品标题")); nid = v(d.get("作品ID"))
            typ = v(d.get("作品类型")); is_video = "视频" in typ
            folder = out / f"{today}_{safe_name(nid, 24)}_{safe_name(title)}"
            folder.mkdir(parents=True, exist_ok=True)
            urls = [u for u in (d.get("下载地址") or []) if u] if not is_video else []
            imgs = [] if a.no_images else dl_images(urls, folder)
            (folder / "caption.txt").write_text(f"{title}\n\n{v(d.get('作品描述'))}\n", encoding="utf-8")
            (folder / "meta.json").write_text(json.dumps({"抓取日期": today, "输入链接": link, **d}, ensure_ascii=False, indent=2), encoding="utf-8")
            (folder / "拆解.md").write_text(render_md(d, link, imgs, is_video, today), encoding="utf-8")
            tags = " ".join("#" + t for t in tags_list(d.get("作品标签"))) or TBD
            csvp = out / "对标库.csv"; new = not csvp.exists()
            with open(csvp, "a", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                if new: w.writerow(CSV_HEAD)
                w.writerow([today, title, v(d.get("作者昵称")), typ, v(d.get("点赞数量")), v(d.get("收藏数量")),
                            v(d.get("评论数量")), v(d.get("分享数量")), tags, v(d.get("作品链接")) if v(d.get("作品链接")) != TBD else link, folder.name])
            print(f"  ✓ {title}｜{typ}｜图{len(imgs)}张 → {folder}")
            if is_video: print("  ⚠ 视频笔记：只存了文案，请在App里截3–5张关键帧发给助手。")
            elif urls and len(imgs) < len(urls): print(f"  ⚠ 图片只下到 {len(imgs)}/{len(urls)} 张")
            ok += 1
    finally:
        if proc:
            proc.terminate()
            try: proc.wait(10)
            except Exception: proc.kill()
    print(f"完成：成功 {ok}，失败 {fail}。汇总表：{out / '对标库.csv'}")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
