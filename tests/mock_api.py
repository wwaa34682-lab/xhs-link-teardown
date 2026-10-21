# 模拟 XHS-Downloader /xhs/detail（真实字段名），仅测试用
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
PNG = bytes.fromhex("ffd8ffe000104a46494600010100000100010000ffd9")
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(PNG if self.path.startswith("/img") else b"ok")
    def do_POST(self):
        b = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        u = b["url"]; port = self.server.server_port
        if "expired" in u: r = {"message": "获取数据失败", "data": None}
        elif "video" in u: r = {"message": "ok", "data": {"作品标题": "示例教学视频", "作品描述": "三步学会", "作品标签": "示例 视频", "作品类型": "视频", "点赞数量": 88, "收藏数量": -1, "评论数量": -1, "分享数量": 2, "发布时间": "2026-10-18_20:00:00", "作者昵称": "小王", "作者链接": "https://www.xiaohongshu.com/user/profile/x", "作品链接": "https://www.xiaohongshu.com/explore/vid123", "作品ID": "vid123", "下载地址": ["http://x/v.mp4"], "动图地址": []}}
        else: r = {"message": "ok", "data": {"作品标题": "示例｜虚构测试帖", "作品描述": "虚构正文 #示例", "作品标签": "示例 测试", "作品类型": "图文", "点赞数量": 17, "收藏数量": 13, "评论数量": -1, "分享数量": 1, "发布时间": "2026-10-20_21:30:00", "作者昵称": "设计师A", "作者链接": "https://www.xiaohongshu.com/user/profile/a", "作品链接": "https://www.xiaohongshu.com/explore/abc123", "作品ID": "abc123", "下载地址": [f"http://127.0.0.1:{port}/img1", f"http://127.0.0.1:{port}/img2"], "动图地址": [None]}}
        out = json.dumps(r, ensure_ascii=False).encode("utf-8")
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(out)
HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
