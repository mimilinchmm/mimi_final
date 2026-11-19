# -*- coding: utf-8 -*-
"""幻界元素 × MBTI/特質測驗聊天機器人後端（支援自由聊天 + 50/200 題智慧引導 + 外部參考連結）。"""
from __future__ import annotations

import json
import os
import random
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8001

EXTERNAL_LINKS = {
    "mbti_200": "https://m.psyctest.cn/q/Vm5baaG6/",
    "adhd_raads": "https://app.raadstest.com/tw/autism/raadsr",
}

QUIZ_TRIGGER_KEYWORDS = [
    "測驗", "測試", "題目", "人格", "性格", "mbti", "MBTI",
    "專注", "注意力", "adhd", "ADHD", "raads", "RAADS", "感官",
    "職業", "工作", "職涯", "學習", "創意", "天賦",
    "情感", "愛情", "人際", "溝通", "情緒", "eq", "EQ", "社交",
    "壓力", "抗壓", "領導", "管理", "決策", "抉擇",
    "50", "五十", "200", "兩百", "精簡", "完整", "練習", "查找"
]

CASUAL_RESPONSES = {
    "greeting": [
        "嗨～今天過得怎麼樣呀？想隨便聊聊、吐吐苦水，還是想測測看自己的本命元素都可以喔！",
        "你好呀！我是幻界引導精靈 🌟 今天想聊點什麼呢？（順帶一提，想測 50 題精簡版或 200 題完整版隨時跟我說～）"
    ],
    "tired_or_sad": [
        "聽起來你今天有點累或心裡悶悶的辛苦了拍拍你。要不先深呼吸一下，想聊聊發生什麼事嗎？如果不想多說，單純放空也很可以。",
        "辛苦啦！有時候什麼都不做、喝杯熱飲讓大腦喘口氣也是很棒的充電。你想聽我陪你聊聊天，還是想用測驗轉換一下心情？"
    ],
    "happy_or_excited": [
        "聽起來狀態很不錯耶！保持這股好心情～有什麼想分享的趣事或新點子嗎？",
        "太棒了！能量滿滿的時候最適合做點喜歡的事，想聊什麼都可以丟過來！"
    ],
    "general": [
        "嗯嗯，我聽到了！你這樣想滿有意思的，可以再多跟我說一點嗎？",
        "哈哈，這個角度很酷耶！你平常遇到這種情況通常會怎麼做？",
        "有道理欸～生活裡很多小細節仔細想都滿好玩的。你最近有在忙什麼特別的事嗎？"
    ]
}


def try_llm_chat(user_message: str, history: list[dict] | None = None) -> str | None:
    """若有設定 GEMINI_API_KEY，呼叫 Gemini API 進行自然自由聊天；失敗或未設定則回傳 None。"""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    system_instruction = (
        "你是「幻界 118 元素 × 16 型人格測驗平台」的親切聊天小幫手。"
        "請用繁體中文、自然親切且像朋友一樣與使用者自由聊天。"
        "若使用者詢問與心理測驗無關的日常話題，請正常回答並陪伴聊天，"
        "僅在結尾用簡短一句話自然提醒：若想測驗可說「稍微測一下（50題）」或「做完整測驗（200題）」。"
    )

    contents = []
    for item in (history or [])[-6:]:
        role = "user" if item.get("role") == "user" else "model"
        text = str(item.get("content", "")).strip()
        if text:
            contents.append({"role": role, "parts": [{"text": text}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 400},
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                texts = [p.get("text", "") for p in parts if p.get("text")]
                if texts:
                    return "".join(texts).strip()
    except Exception:
        return None
    return None


def rule_based_casual_reply(msg: str) -> str:
    if any(k in msg for k in ["嗨", "你好", "哈囉", "hello", "hi", "早安", "午安", "晚安"]):
        base = random.choice(CASUAL_RESPONSES["greeting"])
    elif any(k in msg for k in ["累", "煩", "難過", "壓力大", "失眠", "悶", "不想動", "辛苦"]):
        base = random.choice(CASUAL_RESPONSES["tired_or_sad"])
    elif any(k in msg for k in ["開心", "讚", "太棒", "哈哈", "嘻嘻", "順利", "喜歡"]):
        base = random.choice(CASUAL_RESPONSES["happy_or_excited"])
    else:
        base = random.choice(CASUAL_RESPONSES["general"])

    return f"{base}\n\n💡 想測驗時也可以跟我說「**稍微測一下（50 題）**」或「**做完整測驗（200 題）**」喔！"


def detect_mode(msg: str) -> str:
    short_keywords = ["稍微", "隨便", "簡單", "快速", "練習", "精簡", "50", "五十", "先測一下", "大概"]
    full_keywords = ["完整", "深度", "詳細", "仔細", "全部", "200", "兩百", "正式"]
    if any(k in msg for k in short_keywords):
        return "50"
    if any(k in msg for k in full_keywords):
        return "200"
    return "200"


def detect_group(msg: str) -> int:
    if any(k in msg for k in ["職業", "工作", "職涯", "學習", "創意", "天賦", "專注", "拖延", "adhd", "ADHD", "raads", "RAADS", "感官"]):
        return 2 if any(k in msg for k in ["職業", "工作", "職涯", "學習", "創意", "天賦"]) else 1
    if any(k in msg for k in ["情感", "愛情", "人際", "溝通", "情緒", "eq", "EQ", "社交"]):
        return 3
    if any(k in msg for k in ["壓力", "抗壓", "領導", "管理", "決策", "抉擇"]):
        return 4
    return 1


def generate_chat_reply(message: str, history: list[dict] | None = None) -> dict:
    msg = message.strip()
    if not msg:
        return {
            "reply": "想聊什麼都可以打字給我喔！也可以直接說「**稍微查找我的人格特質**」或「**做完整測驗**」。",
            "recommended_group": None,
            "question_count": None,
            "button_text": None,
            "external_links": EXTERNAL_LINKS,
            "chat_mode": "casual",
        }

    # 1. 偵測是否為測驗引導需求
    is_quiz_intent = any(k in msg for k in QUIZ_TRIGGER_KEYWORDS)
    if is_quiz_intent:
        mode = detect_mode(msg)
        group_id = detect_group(msg)
        mode_label = "精簡練習版（50 題）" if mode == "50" else "完整測驗版（200 題）"
        group_titles = {
            1: "第一大類：核心人格 × 注意力與感官特質（MBTI + ADHD/特質融合）",
            2: "第二大類：職涯方向 × 學習與執行策略",
            3: "第三大類：情緒覺察 × 人際與溝通互動",
            4: "第四大類：壓力調適 × 決策與領導風格",
        }
        reply_text = (
            f"已依照你的需求為你搭配**「{mode_label}」**，推薦從**「{group_titles[group_id]}」**開始：\n"
            f"• 外部參考網站（200 題結構）：{EXTERNAL_LINKS['mbti_200']}\n"
            f"• 外部參考網站（特質/感官量表）：{EXTERNAL_LINKS['adhd_raads']}"
        )
        return {
            "reply": reply_text,
            "recommended_group": group_id,
            "question_count": int(mode),
            "button_text": f"✨ 開始測驗（{mode_label}）",
            "external_links": EXTERNAL_LINKS,
            "chat_mode": "quiz_guide",
        }

    # 2. 一般自由聊天模式（優先嘗試 LLM，無金鑰則使用內建自然對話）
    llm_reply = try_llm_chat(msg, history=history)
    final_reply = llm_reply if llm_reply else rule_based_casual_reply(msg)

    return {
        "reply": final_reply,
        "recommended_group": None,
        "question_count": None,
        "button_text": None,
        "external_links": EXTERNAL_LINKS,
        "chat_mode": "casual",
    }


class ChatBotHandler(BaseHTTPRequestHandler):
    server_version = "ChatBotAgent/4.0"

    def log_message(self, format, *args):
        print("[chat_bot] " + (format % args))

    def _send_json(self, payload: dict, status: int = 200):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/api/chat"):
            self._send_json({"ok": True, "message": "🤖 幻界元素聊天機器人 API 運行中！"})
            return
        self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/chat":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                res_data = generate_chat_reply(
                    data.get("message", ""),
                    history=data.get("history", [])
                )
                self._send_json({"ok": True, **res_data})
            except Exception as exc:
                self._send_json({"ok": False, "reply": f"系統發生錯誤: {str(exc)}"}, 500)
            return
        self.send_error(404)


def main():
    server = ThreadingHTTPServer((HOST, PORT), ChatBotHandler)
    print("==================================================")
    print(" 🤖 幻界元素諮詢聊天機器人後端已啟動（支援自由聊天 + 測驗引導）！")
    print(f" 聊天 API 位址：http://{HOST}:{PORT}/api/chat")
    print("==================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n聊天機器人伺服器已安全停止。")


if __name__ == "__main__":
    main()
