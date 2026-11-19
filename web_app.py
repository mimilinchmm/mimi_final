# -*- coding: utf-8 -*-
"""支援 50/200 題切換、本命元素擴充（建議字/菜餚蔬果滋味）、暫存進度繼續作答、歷史紀錄查詢/軟刪除/復原之網站後端。"""
from __future__ import annotations

import json
import mimetypes
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from seed_database import DB_FILE, connect

BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "index.html"
HOST = "127.0.0.1"
PORT = 8000

MBTI_SYSTEM_META = {
    "ENTJ": {
        "group": "分析家", "mbti_name": "指揮官",
        "month": "一月", "month_trait": "開創秩序",
        "plant": "梅花", "plant_desc": "歲首傲雪綻放，展現領袖風骨。",
        "archetype": "統治者", "archetype_desc": "建立秩序與掌控全局。",
        "primary_color": {"name": "金黃", "hex": "#EAB308"},
        "secondary_color": {"name": "深棕", "hex": "#5C4033"},
        "color_reason": "金色代表權威與榮耀；深棕象徵穩固結構與責任感。",
        "careers": "執行長（CEO）、管理顧問、專案總監、法官",
        "advice_word": "【銳・定】—— 銳意開拓而不失沉穩定見，適時傾聽能讓戰略無往不利。",
        "culinary_taste": {
            "dish": "黑椒炙燒戰斧牛排",
            "fruit": "紅寶石葡萄柚",
            "vegetable": "炭烤蘆筍",
            "flavor_note": "濃郁醇厚中帶有一絲微苦回甘，果斷直接、層次分明，越咀嚼越能感受到掌控全局的底氣。"
        }
    },
    "ESTJ": {
        "group": "守護者", "mbti_name": "總經理",
        "month": "一月", "month_trait": "開創秩序",
        "plant": "梅花", "plant_desc": "歲首傲雪綻放，講求原則與效率。",
        "archetype": "統治者", "archetype_desc": "建立秩序與高效運作。",
        "primary_color": {"name": "金黃", "hex": "#EAB308"},
        "secondary_color": {"name": "深棕", "hex": "#5C4033"},
        "color_reason": "金色代表權威；深棕象徵穩固執行力。",
        "careers": "企業高管、管理顧問、法官、營運長",
        "advice_word": "【衡・寬】—— 制度是高效基石，留三分彈性給人心，團隊會走得更遠。",
        "culinary_taste": {
            "dish": "老火慢燉紅燒獅子頭",
            "fruit": "富士蘋果",
            "vegetable": "清炒荷蘭豆",
            "flavor_note": "紮實鹹香、爽脆俐落，沒有多餘花俏調味，卻是最令人安心的經典實在滋味。"
        }
    },
    "ENFP": {
        "group": "外交家", "mbti_name": "競選者",
        "month": "二月", "month_trait": "浪漫生機",
        "plant": "桃花", "plant_desc": "春風吹拂，象徵熱情感染力與自由創造。",
        "archetype": "愛人者", "archetype_desc": "追求深層連結與對美的熱愛。",
        "primary_color": {"name": "洋紅", "hex": "#DB2777"},
        "secondary_color": {"name": "蜜桃橘", "hex": "#FDBA74"},
        "color_reason": "洋紅象徵濃烈情感；蜜桃色帶出浪漫依戀。",
        "careers": "創意總監、公關媒體、品牌行銷、活動策展",
        "advice_word": "【聚・光】—— 你的靈感如星火燎原，將熱情聚焦於一處，便能照亮整片夜空。",
        "culinary_taste": {
            "dish": "西班牙海鮮燉飯",
            "fruit": "愛文芒果",
            "vegetable": "彩椒溫沙拉",
            "flavor_note": "酸甜奔放、色彩繽紛，每一口都充滿驚喜跳躍的果香與陽光氣息。"
        }
    },
    "ESFP": {
        "group": "探險家", "mbti_name": "表演者",
        "month": "七月", "month_trait": "活在當下",
        "plant": "荔枝樹", "plant_desc": "盛夏果實飽滿，熱愛感官體驗與分享快樂。",
        "archetype": "弄臣", "archetype_desc": "用幽默感與熱情點亮全場。",
        "primary_color": {"name": "檸檬黃", "hex": "#FACC15"},
        "secondary_color": {"name": "萊姆綠", "hex": "#84CC16"},
        "color_reason": "黃色最具幽默感與感染力。",
        "careers": "美食評論家、旅遊部落客、時尚造型師、主持人",
        "advice_word": "【樂・韻】—— 盡情享受當下的每分精彩，同時為明日留下一段悠長餘韻。",
        "culinary_taste": {
            "dish": "泰式酸辣海鮮湯（冬蔭功）",
            "fruit": "玉荷包荔枝",
            "vegetable": "蒜香奶油玉米筍",
            "flavor_note": "酸、辣、甜、鮮在舌尖熱鬧共舞，瞬間點燃感官活力，讓人忍不住想與身邊人分享。"
        }
    },
    "INFP": {
        "group": "外交家", "mbti_name": "調停者",
        "month": "三月", "month_trait": "詩意理想",
        "plant": "油桐花", "plant_desc": "花開清麗，自帶文藝詩意與敏銳共情力。",
        "archetype": "創造者", "archetype_desc": "將豐富情感化為獨特故事與藝術。",
        "primary_color": {"name": "亮橘", "hex": "#F97316"},
        "secondary_color": {"name": "薰衣草紫", "hex": "#C084FC"},
        "color_reason": "亮橘代表靈感；淺紫象徵藝術氣息。",
        "careers": "作家、插畫家、心理諮商師、音樂創作人",
        "advice_word": "【真・芽】—— 守護內心最柔軟的真實，讓夢想在現實土壤裡慢慢發芽。",
        "culinary_taste": {
            "dish": "法式紅酒燉梨佐舒肥鴨胸",
            "fruit": "白桃",
            "vegetable": "紫蘇梅漬小番茄",
            "flavor_note": "清雅微酸中帶著細膩花果甜香，溫柔不張揚，卻能深深撫慰疲憊靈魂。"
        }
    },
    "ISFJ": {
        "group": "守護者", "mbti_name": "守衛者",
        "month": "四月", "month_trait": "內斂務實",
        "plant": "青梅", "plant_desc": "青梅內斂耐品，低調守護與踏實奉獻。",
        "archetype": "照顧者", "archetype_desc": "尋找歸屬與真誠連結。",
        "primary_color": {"name": "米色", "hex": "#D6C7B2"},
        "secondary_color": {"name": "淺灰", "hex": "#CBD5E1"},
        "color_reason": "大地裸色系代表腳踏實地與平易近人。",
        "careers": "護理師、營養師、HR、行政管理",
        "advice_word": "【暖・己】—— 在悉心照料所有人之前，別忘了先為自己留一盞溫暖的燈。",
        "culinary_taste": {
            "dish": "山藥排骨蓮子湯",
            "fruit": "水梨",
            "vegetable": "清炒高麗菜嬰",
            "flavor_note": "溫潤清甜、細火慢熬的甘醇滋味，不搶風頭卻是餐桌上最不可或缺的暖心存在。"
        }
    },
    "ISFP": {
        "group": "探險家", "mbti_name": "探險家",
        "month": "三月", "month_trait": "隨性佛系",
        "plant": "山茶花", "plant_desc": "透過獨特審美表達自我，溫柔忠於內心。",
        "archetype": "探險家", "archetype_desc": "追求自由與真實感官體驗。",
        "primary_color": {"name": "森林綠", "hex": "#15803D"},
        "secondary_color": {"name": "土耳其藍", "hex": "#06B6D4"},
        "color_reason": "綠色代表大自然與不受拘束的靈魂。",
        "careers": "自由藝術家、獨立設計師、花藝師、攝影師",
        "advice_word": "【自在・澄】—— 順隨內心的美感節奏前行，無需迎合外界喧囂。",
        "culinary_taste": {
            "dish": "日式柚子胡椒炙燒鮭魚",
            "fruit": "無花果",
            "vegetable": "芝麻葉油醋沙拉",
            "flavor_note": "清新柑橘香氣交織微苦草本與淡雅果甜，自然純粹、充滿獨特審美格調。"
        }
    },
    "ESTP": {
        "group": "探險家", "mbti_name": "企業家",
        "month": "五月", "month_trait": "行動守護",
        "plant": "菖蒲", "plant_desc": "菖蒲如劍，代表極強的行動力與破局思維。",
        "archetype": "英雄", "archetype_desc": "追求挑戰與戰士精神。",
        "primary_color": {"name": "正紅", "hex": "#EF4444"},
        "secondary_color": {"name": "酒紅", "hex": "#991B1B"},
        "color_reason": "正紅象徵行動力與勇氣。",
        "careers": "急診醫師、金融交易員、工程師、運動員",
        "advice_word": "【躍・思】—— 你的勇氣能撕開任何僵局，出擊前三秒的停頓將讓你更精準。",
        "culinary_taste": {
            "dish": "川味麻辣香鍋",
            "fruit": "紅心芭樂",
            "vegetable": "乾煸四季豆",
            "flavor_note": "辛香麻辣、爽脆帶勁，節奏明快且後勁十足，讓人一吃就熱血沸騰。"
        }
    },
    "ISTP": {
        "group": "探險家", "mbti_name": "鑑賞家",
        "month": "五月", "month_trait": "行動守護",
        "plant": "菖蒲", "plant_desc": "反應敏捷，重視當下實戰與技術破局。",
        "archetype": "英雄", "archetype_desc": "冷靜克服挑戰的獨行戰士。",
        "primary_color": {"name": "正紅", "hex": "#EF4444"},
        "secondary_color": {"name": "酒紅", "hex": "#991B1B"},
        "color_reason": "正紅象徵果斷行動力。",
        "careers": "外科醫師、金融交易員、建築工程師",
        "advice_word": "【鍊・通】—— 精準拆解萬物原理之餘，偶爾分享心聲能讓夥伴更懂你。",
        "culinary_taste": {
            "dish": "鐵板海鹽骰子牛",
            "fruit": "奇異果",
            "vegetable": "鹽烤杏鮑菇",
            "flavor_note": "極簡海鹽引出食材最真實的原汁鮮甜，不拖泥帶水、火候精準到位。"
        }
    },
    "INFJ": {
        "group": "外交家", "mbti_name": "提倡者",
        "month": "六月", "month_trait": "精神引領",
        "plant": "荷花", "plant_desc": "出淤泥而不染，保有精神純粹與深刻洞察力。",
        "archetype": "天真者", "archetype_desc": "守護內心純淨與崇高理想。",
        "primary_color": {"name": "純白", "hex": "#F8FAFC"},
        "secondary_color": {"name": "淡粉紅", "hex": "#FBCFE8"},
        "color_reason": "白色象徵純粹與精神高潔。",
        "careers": "臨床心理師、生涯規劃師、NGO倡議者、編劇",
        "advice_word": "【渡・界】—— 洞察眾生卻不背負他人因果，設立溫柔界線是給自己的慈悲。",
        "culinary_taste": {
            "dish": "松露野菇清燉茶碗蒸",
            "fruit": "綠葡萄",
            "vegetable": "百合炒西芹",
            "flavor_note": "入口滑嫩清雅，幽微的松露與草本清香在鼻息間層層展開，深邃而純淨。"
        }
    },
    "ENFJ": {
        "group": "外交家", "mbti_name": "主人公",
        "month": "八月", "month_trait": "凝聚人心",
        "plant": "桂花", "plant_desc": "氣味溫潤不刺鼻，最能凝聚人心與和諧。",
        "archetype": "魔法師", "archetype_desc": "透過感召力促成團隊蛻變。",
        "primary_color": {"name": "皇家紫", "hex": "#7E22CE"},
        "secondary_color": {"name": "銀灰", "hex": "#94A3B8"},
        "color_reason": "紫色象徵靈性與直覺力。",
        "careers": "教育工作者、團隊教練、社工師、婚禮顧問",
        "advice_word": "【融・輝】—— 以溫暖感召眾人綻放光芒，也允許自己偶爾卸下光環休息。",
        "culinary_taste": {
            "dish": "桂花蜜汁烤雞腿排",
            "fruit": "水蜜桃",
            "vegetable": "金沙南瓜",
            "flavor_note": "蜜香溫潤、甘甜包覆感強，既有讓人愉悅的溫暖甜度，又有飽滿的滋養力量。"
        }
    },
    "ESFJ": {
        "group": "守護者", "mbti_name": "執政官",
        "month": "八月", "month_trait": "凝聚人心",
        "plant": "桂花", "plant_desc": "象徵豐收與團圓，用溫暖照護身邊每個人。",
        "archetype": "魔法師", "archetype_desc": "善於整合人際與資源。",
        "primary_color": {"name": "皇家紫", "hex": "#7E22CE"},
        "secondary_color": {"name": "銀灰", "hex": "#94A3B8"},
        "color_reason": "紫色代表溫潤的精神感召。",
        "careers": "教育工作者、客戶經理、社工師",
        "advice_word": "【和・悅】—— 你的體貼是團體的黏著劑，把真實需求說出口會讓你更輕鬆。",
        "culinary_taste": {
            "dish": "台式三杯杏鮑菇雞煲",
            "fruit": "巨峰葡萄",
            "vegetable": "蒜蓉蒸娃娃菜",
            "flavor_note": "九層塔與麻油醬香撲鼻，熱騰騰的團圓煙火氣息，讓人倍感親切與歸屬。"
        }
    },
    "INTP": {
        "group": "分析家", "mbti_name": "邏輯學家",
        "month": "九月", "month_trait": "獨立思辨",
        "plant": "菊花", "plant_desc": "秋霜中獨自盛開，熱愛獨立思辨與真理。",
        "archetype": "智者", "archetype_desc": "追求客觀真理與底層智慧。",
        "primary_color": {"name": "海軍藍", "hex": "#1E3A8A"},
        "secondary_color": {"name": "靛藍", "hex": "#4338CA"},
        "color_reason": "深藍象徵冷靜與理性分析。",
        "careers": "演算法工程師、研究員、系統架構師、數據分析師",
        "advice_word": "【析・行】—— 腦中的真理模型已臻完美，踏出實驗的第一步就會看見奇蹟。",
        "culinary_taste": {
            "dish": "手沖耶加雪菲佐黑巧克力塔",
            "fruit": "藍莓",
            "vegetable": "冰鎮秋葵佐和風芥末",
            "flavor_note": "前段是冷冽微酸的果韻，中段轉為深邃微苦的可可與芥末辛香，越細品越耐人尋味。"
        }
    },
    "INTJ": {
        "group": "分析家", "mbti_name": "建築師",
        "month": "十月", "month_trait": "暗藏鋒芒",
        "plant": "山茶花", "plant_desc": "逆勢綻放，外表冷靜高雅，內在蘊藏強大戰略能量。",
        "archetype": "反抗者", "archetype_desc": "不盲從常規，蘊含戰略意志。",
        "primary_color": {"name": "純黑", "hex": "#18181B"},
        "secondary_color": {"name": "暗紫", "hex": "#581C87"},
        "color_reason": "黑色代表絕對獨立與拒絕妥協。",
        "careers": "投資銀行家、企業策略長、軟體架構師、律師",
        "advice_word": "【謀・柔】—— 運籌帷幄之中，用一點柔軟的幽默感潤滑人際，藍圖將更早實現。",
        "culinary_taste": {
            "dish": "墨魚汁慢燉海鮮燉飯",
            "fruit": "黑櫻桃",
            "vegetable": "烤孢子甘藍佐巴薩米克醋",
            "flavor_note": "深沉內斂的鮮味與陳年酒醋的酸香交織，外表低調神祕，內裡卻蘊藏極高濃度的風味張力。"
        }
    },
    "ENTP": {
        "group": "分析家", "mbti_name": "辯論家",
        "month": "十一月", "month_trait": "堅毅先驅",
        "plant": "水仙", "plant_desc": "嚴冬中率先破土，象徵靈活變通與探索精神。",
        "archetype": "探險家", "archetype_desc": "永遠在尋找新出路與思維邊界。",
        "primary_color": {"name": "森林綠", "hex": "#15803D"},
        "secondary_color": {"name": "土耳其藍", "hex": "#06B6D4"},
        "color_reason": "綠色代表破土生機與遼闊視野。",
        "careers": "連續創業者、產品經理、廣告創意、趨勢分析師",
        "advice_word": "【破・成】—— 打破舊框架是你的天賦，替最精彩的那個點子畫上完美句點吧。",
        "culinary_taste": {
            "dish": "分子料理跳跳糖鵝肝慕斯",
            "fruit": "百香果",
            "vegetable": "香煎羽衣甘藍脆片",
            "flavor_note": "強烈酸香與酥脆口感碰撞出意想不到的火花，充滿玩心與反轉驚喜。"
        }
    },
    "ISTJ": {
        "group": "守護者", "mbti_name": "物流師",
        "month": "十二月", "month_trait": "承先啟後",
        "plant": "松柏", "plant_desc": "四季常青，展現嚴謹、可靠與傳承精神。",
        "archetype": "照顧者", "archetype_desc": "透過恪守職責成為安心後盾。",
        "primary_color": {"name": "珊瑚粉", "hex": "#FB7185"},
        "secondary_color": {"name": "暖橘", "hex": "#EA580C"},
        "color_reason": "象徵穩固的承諾與細心照護。",
        "careers": "會計師、精算師、稽核專員、供應鏈管理師",
        "advice_word": "【守・新】—— 你的可靠無可替代，偶爾允許計畫外的小驚喜，生活會更有樂趣。",
        "culinary_taste": {
            "dish": "古法清燉牛肉麵",
            "fruit": "甘蔗 / 鳳梨",
            "vegetable": "白灼芥蘭菜",
            "flavor_note": "清澈見底卻底蘊深厚的牛骨甘甜，每一口都遵循黃金比例，穩健而值得信賴。"
        }
    }
}

DEFAULT_META = {
    "group": "多元人格系列", "mbti_name": "幻界元素",
    "month": "四季循環", "month_trait": "自然原力",
    "plant": "奇幻靈花", "plant_desc": "蘊含獨特的自然能量與生命氣息。",
    "archetype": "探險家", "archetype_desc": "探索未知與自我潛能。",
    "primary_color": {"name": "皇家紫", "hex": "#7E22CE"},
    "secondary_color": {"name": "銀灰", "hex": "#94A3B8"},
    "color_reason": "象徵靈性轉化與無限可能。",
    "careers": "跨領域創新者、專案顧問、自由創作者",
    "advice_word": "【衡・進】—— 保持好奇與內在平衡，每一步都是獨特的風景。",
    "culinary_taste": {
        "dish": "五彩時蔬野菇炊飯",
        "fruit": "綜合莓果",
        "vegetable": "清炒季節時蔬",
        "flavor_note": "酸甜鹹鮮平衡和諧，清香回甘，蘊含大地四季的圓融滋味。"
    }
}

RAW_ELEMENTS_118 = [
    ("001", "St", "Stellarium", "純真先驅", "ENFP", "第1-2週期", "充滿好奇心的元氣少年，總是一馬當先探索未知。"),
    ("002", "L", "Lunacrys", "清冷月神", "INFJ", "第1-2週期", "安靜優雅的銀髮少女，習慣在夜裡獨處。"),
    ("003", "G", "Glorion", "榮耀騎士", "ESTP", "第1-2週期", "性格耿直熱血、正義感爆棚的戰鬥派。"),
    ("004", "Th", "Thunderium", "暴躁雷公", "ESTJ", "第1-2週期", "說話大聲、行動雷厲風行的可靠夥伴。"),
    ("005", "P", "Phantasma", "神出鬼沒", "ENTP", "第1-2週期", "喜歡躲在角落惡作劇的幽靈系少年。"),
    ("006", "Gx", "Galaxium", "浪漫夢想家", "INFP", "第1-2週期", "腦袋裝滿整片星空的文藝青年。"),
    ("007", "A", "Aurorite", "溫柔治癒師", "ISFJ", "第1-2週期", "散發極光般柔和氣場的溫暖守護者。"),
    ("008", "Py", "Pyroflame", "熱情燃燒者", "ESFP", "第1-2週期", "對任何事都全力以赴的樂天行動派。"),
    ("009", "C", "Cryostone", "理性冰山", "INTJ", "第1-2週期", "外表冷漠、說話一針見血的邏輯控。"),
    ("010", "M", "Mistoria", "慵懶霧隱", "ISFP", "第1-2週期", "總是睡眼惺忪、喜歡泡在茶館的佛系智者。"),
    ("011", "Ce", "Celestium", "高貴天裔", "ESTJ", "第3週期", "舉止優雅、帶點微傲嬌的貴族少爺。"),
    ("012", "Mg", "Magnetara", "萬人迷磁石", "ESFP", "第3週期", "天生具備強烈吸引力的社交焦點。"),
    ("013", "B", "Blueflame", "冷靜狂熱者", "ISTP", "第3週期", "一旦觸及感興趣領域便展現驚人執著。"),
    ("014", "Am", "Amethystium", "神秘占卜師", "INFJ", "第3週期", "直覺敏銳、常能看穿謊言的占卜師。"),
    ("015", "F", "Frostwing", "自由風雪", "ISTP", "第3週期", "嚮往天空的孤高旅人，來去如風。"),
    ("016", "Sh", "Shadowium", "忠誠暗衛", "ISFJ", "第3週期", "習慣隱身身後的沉默守護者，嘴硬心軟。"),
    ("017", "S", "Solarium", "陽光領袖", "ENFJ", "第3週期", "自帶聚光燈的王者型人格，樂觀開朗。"),
    ("018", "N", "Nocturnium", "夜行紳士", "ISFP", "第3週期", "夜晚精神百倍的優雅夜貓子。"),
    ("019", "D", "Draconium", "霸道龍王", "ENTJ", "第4週期", "自尊心極強、護短又霸氣的戰鬥狂。"),
    ("020", "Ph", "Phoenixium", "不屈浴火者", "ESFP", "第4週期", "越挫越勇的樂天派，失敗也能笑著站起。"),
    ("021", "Lu", "Luminaris", "聖潔引路人", "ENFJ", "第4週期", "溫和堅定的燈塔型角色，指明方向。"),
    ("022", "V", "Voidium", "虛無極簡控", "INTP", "第4週期", "對物質毫無慾望的冷靜旁觀者。"),
    ("023", "As", "Astralux", "星軌學者", "INTP", "第4週期", "熱愛計算與觀察宇宙規律的考據狂。"),
    ("024", "O", "Oceanium", "包容海皇", "ESTP", "第4週期", "胸懷寬廣、情緒深沉如海的大叔型角色。"),
    ("025", "Tm", "Tempestium", "狂野風暴", "ESFP", "第4週期", "靈感一來如龍捲風般席捲全場的藝術家。"),
    ("026", "Tu", "Thundora", "雷鳴戰姬", "ESTP", "第4週期", "爽朗豪邁、喜歡直球對決的短髮少女。"),
    ("027", "Sd", "Stardustium", "愛哭小精靈", "INFP", "第4週期", "容易感動落淚的感性派精靈。"),
    ("028", "Lf", "Lightfall", "悲劇詩人", "INFP", "第4週期", "自帶憂鬱濾鏡、喜歡感嘆時光的青年。"),
    ("029", "Dr", "Dreamium", "白日夢家", "INFP", "第4週期", "分不清現實與夢境的迷糊浪漫主義者。"),
    ("030", "Nt", "Netherium", "深淵叛逆者", "ISFP", "第4週期", "嘴上討厭世界其實非常重義氣的少年。"),
    ("031", "Cr", "Crystalia", "完美主義者", "ISTJ", "第4週期", "追求無瑕結構與絕對透明感的工匠。"),
    ("032", "Ne", "Neonara", "派對焦點", "ESFP", "第4週期", "熱愛霓虹燈與音樂的潮流達人。"),
    ("033", "Aq", "Aquavelle", "靈動水精", "ESFJ", "第4週期", "善於察言觀色、處事圓滑的社交高手。"),
    ("034", "Cm", "Crimsonite", "赤紅決鬥者", "ESTP", "第4週期", "追求極致勝負的武癡，對強者充滿敬意。"),
    ("035", "Sk", "Skytherium", "雲端漫步者", "ESFP", "第4週期", "性格灑脫不羈、隨時準備出發旅行。"),
    ("036", "Sn", "Snowphant", "憨厚雪獸", "ISFJ", "第4週期", "體型龐大卻性格溫馴的冬日暖男。"),
    ("037", "Sp", "Sharpium", "毒舌劍客", "ESTJ", "第5週期", "說話如刀般鋒利、是非分明的劍客。"),
    ("038", "Au", "Aurumite", "奢華鑑賞家", "ISFP", "第5週期", "品味極佳、看重事物內在價值的藏家。"),
    ("039", "Az", "Azureon", "深海哲人", "INFJ", "第5週期", "能用平靜語氣化解爭吵的深沉傾聽者。"),
    ("040", "Gl", "Glacielle", "高嶺之花", "ISFJ", "第5週期", "氣質清麗脫俗、熟識後很會照顧人的冰美人。"),
    ("041", "I", "Infernium", "煉獄狂戰士", "ESTP", "第5週期", "戰鬥時忘我的熱血派，私下是居家好男人。"),
    ("042", "T", "Terravium", "大地守衛", "ISTJ", "第5週期", "腳踏實地、說一不二的團隊堅實後盾。"),
    ("043", "Sl", "Starloop", "循環強迫症", "ISTJ", "第5週期", "做事必須照固定流程走的嚴謹計畫控。"),
    ("044", "Sw", "Swiftshadow", "疾風斥候", "ESTP", "第5週期", "行動敏捷、永遠掌握第一手消息的情報販子。"),
    ("045", "Lg", "Lightfeather", "輕盈舞者", "ISFP", "第5週期", "心思細膩、跳起舞來光芒萬丈的少女。"),
    ("046", "Tw", "Twilightium", "黃昏雙面人", "ISFP", "第5週期", "白天與夜晚展現截然不同面貌的雙面人。"),
    ("047", "Mf", "Moonflare", "傲嬌月耀", "ISFP", "第5週期", "被誇獎就會瞬間臉紅害羞的反差萌少女。"),
    ("048", "Sf", "Stormflame", "爆裂先鋒", "ESTP", "第5週期", "信奉先行動再說的冒險家。"),
    ("049", "Sr", "Spiritium", "通靈少年", "INFP", "第5週期", "能聽見萬物心聲的溫柔療癒系男孩。"),
    ("050", "Fn", "Frostnova", "極寒爆破手", "ESTP", "第5週期", "平時乖巧、忍耐極限到達會瞬間爆發者。"),
    ("051", "Ss", "Shatterstar", "破碎重組者", "INTP", "第5週期", "喜歡拆解東西研究原理的機械宅。"),
    ("052", "Ds", "Dawnshine", "元氣晨曦", "ESFJ", "第5週期", "充滿正能量、最早叫大家起床的班長。"),
    ("053", "Vo", "Voltaris", "高壓發明家", "INTP", "第5週期", "滿腦子奇特實驗點子的瘋狂科學家。"),
    ("054", "Fa", "Fantasium", "童話說書人", "ENFP", "第5週期", "把日常講得像史詩冒險的魅力演說家。"),
    ("055", "E", "Emeraldium", "翡翠貴公子", "ESFJ", "第6週期", "溫文儒雅、對待生命極為溫柔的植物學家。"),
    ("056", "Si", "Silvershade", "銀幕策士", "INTJ", "第6週期", "喜歡在暗處運籌帷幄的冷靜幕後軍師。"),
    ("057", "Cf", "Scarletflame", "緋紅女王", "ENTJ", "緋焰系", "氣場強大、自信耀眼的舞台中心領袖。"),
    ("058", "Il", "Illusium", "幻術魔術師", "ENTP", "緋焰系", "用華麗戲法逗人開心的幽默紳士。"),
    ("059", "Wv", "Starwave", "星潮衝浪手", "ESFP", "緋焰系", "隨性樂觀、懂得順勢而為的行動派。"),
    ("060", "Cl", "Cloudspire", "雲端建築師", "ENFP", "緋焰系", "擁有宏大願景、喜歡構築高遠目標的理想家。"),
    ("061", "Vi", "Violetfire", "紫焰魔女", "ISFP", "緋焰系", "對禁忌知識充滿好奇的神祕學者。"),
    ("062", "Ww", "Windwhisper", "風語傾聽者", "ISFJ", "緋焰系", "擅長傾聽他人煩惱的溫柔秘密保管人。"),
    ("063", "Ca", "Celestara", "星辰歌姬", "ESFJ", "緋焰系", "歌聲能撫慰心靈、對世界充滿善意的少女。"),
    ("064", "Ec", "Eclipsium", "日蝕雙子", "ISFP", "緋焰系", "同時擁有光明與陰暗兩面的戲劇張力角色。"),
    ("065", "So", "Soulflame", "靈魂共鳴者", "ENFP", "緋焰系", "共情力極強的藝術家。"),
    ("066", "Nb", "Nebulite", "星雲孕育者", "ENFJ", "緋焰系", "充滿母性光輝與創造力的溫柔導師。"),
    ("067", "Gw", "Goldenwing", "金翼信使", "ESTJ", "緋焰系", "驕傲卻無比盡責的使命必達飛翔者。"),
    ("068", "Gc", "Glacierium", "萬年冰川", "ISTJ", "緋焰系", "記憶力驚人、記仇也記恩的沉穩巨人。"),
    ("069", "Sa", "Solarshadow", "光影行者", "ISTP", "緋焰系", "在光明與黑暗取得平衡的務實派高手。"),
    ("070", "Dc", "Dragoncrys", "龍晶收藏家", "ISFP", "緋焰系", "對珍稀寶物有執著熱愛的鑒寶師。"),
    ("071", "Pf", "Phoenixflame", "涅槃導師", "ENFJ", "緋焰系", "用溫暖話語激勵陷入低潮者的智者。"),
    ("072", "Cs", "Cosmosphere", "宏觀統籌者", "ENTJ", "第6週期", "大局觀極強、擅長協調人際與資源的指揮官。"),
    ("073", "Vf", "Verdaflame", "生命之火", "ESTP", "第6週期", "充滿野性魅力的果斷森林遊俠。"),
    ("074", "Pc", "Phantomcrys", "鏡花水月", "ENTP", "第6週期", "喜歡用謎語考驗別人的神秘貴族。"),
    ("075", "Sv", "Solvion", "破局專家", "ENTJ", "第6週期", "再混亂局面都能理出頭緒的冷靜顧問。"),
    ("076", "Tc", "Thundercrys", "蓄電修行者", "ISTP", "第6週期", "關鍵時刻一鳴驚人的寡言武道家。"),
    ("077", "Sc", "Skycascade", "飛瀑豪傑", "ESTP", "第6週期", "爽快不拘小節、喜歡暢談理想的俠客。"),
    ("078", "Mo", "Moonfrost", "月霜詩人", "INFP", "第6週期", "喜歡在雪夜裡寫詩的清冷才女。"),
    ("079", "Fr", "Starfire", "星火革命家", "ENFP", "第6週期", "眼中永遠燃燒不滅理想的熱血青年。"),
    ("080", "Mv", "Mistveil", "面紗舞姬", "ISFP", "第6週期", "舉手投足充滿神秘美感的優雅女性。"),
    ("081", "Vd", "Violetdawn", "紫霞觀察者", "INFJ", "第6週期", "在清晨靜靜思考人生的沉靜哲學少女。"),
    ("082", "Sg", "Silverglow", "微光守護者", "ISFJ", "第6週期", "不求回報、默默在背後照亮別人的前輩。"),
    ("083", "W", "Windaria", "自由吟遊詩人", "ESFP", "第6週期", "四海為家的浪子，哪裡有故事就往哪裡去。"),
    ("084", "Pr", "Pyrelis", "煉金焰師", "ESTJ", "第6週期", "對火候掌控極度嚴苛的外冷內熱大師。"),
    ("085", "Ar", "Aquaris", "深藍調停者", "ENFJ", "第6週期", "語氣溫柔卻極具說服力的外交官。"),
    ("086", "Tr", "Terralis", "隱世長老", "INFJ", "第6週期", "泰山崩於前而色不變的沉穩賢者。"),
    ("087", "Ln", "Luminucleus", "光明聖王", "ENTJ", "第7週期主族", "象徵絕對正義與秩序之光的威嚴統治者。"),
    ("088", "Dn", "Darknucleus", "暗夜帝君", "INTJ", "第7週期主族", "與 Ln 互為宿敵的深沉莫測幕後主宰。"),
    ("089", "Te", "Temporium", "時間旅人", "ISTJ", "時空系", "隨身帶著懷錶、永遠準時的紳士。"),
    ("090", "Q", "Quantara", "量子貓咪", "ISFP", "時空系", "性格薛丁格化、捉摸不定的神秘少女。"),
    ("091", "Pm", "Prismora", "稜鏡鑑賞家", "ENFJ", "時空系", "善於從不同角度看同一件事的開明智者。"),
    ("092", "Ab", "Abyssium", "深淵凝視者", "INFJ", "時空系", "承載無數秘密的孤獨孤傲守護者。"),
    ("093", "Rs", "Sanctaris", "聖域祭司", "ISFJ", "時空系", "致力保護弱小與神聖之地的溫柔祭司。"),
    ("094", "Mc", "Magicyte", "魔導優等生", "INTP", "時空系", "筆記本永遠寫滿魔法理論的學霸少女。"),
    ("095", "Ws", "Wolfstar", "孤狼獵手", "ISTP", "時空系", "對認定的夥伴絕對忠義的獨行俠。"),
    ("096", "Bo", "Starbornium", "星之驕子", "ESFP", "時空系", "天生自帶好運與天賦的開朗少年。"),
    ("097", "Hf", "Hyperflame", "超新星狂人", "ESTP", "時空系", "情感極度熾熱、毫不掩飾愛恨的豪邁戰士。"),
    ("098", "Ef", "Everfrost", "永凍守望者", "ISTJ", "時空系", "數百年如一日堅守崗位的忠誠衛士。"),
    ("099", "Fl", "Firstlight", "初光少年", "ENFP", "時空系", "象徵希望與黎明的純真孩子。"),
    ("100", "Ev", "Evernight", "永夜淑女", "ISFP", "時空系", "優雅而神秘的暗夜貴婦。"),
    ("101", "Oc", "Oraculum", "神諭先知", "INFJ", "時空系", "喜歡用雙關語讓年輕人自己悟出答案的老者。"),
    ("102", "Is", "Illusionite", "海市蜃樓", "ISFP", "時空系", "在人們最渴望時出現又消失的浪漫旅人。"),
    ("103", "Ch", "Chaotium", "混沌樂子人", "ENTP", "時空系", "哪裡無聊就去製造小混亂的搗蛋鬼。"),
    ("104", "Or", "Ordinium", "法則大法官", "ISTJ", "第7週期主族", "一絲不苟、絕對公正的秩序化身。"),
    ("105", "Vt", "Vitalium", "生命女神", "ESFJ", "第7週期主族", "充滿朝氣與慈愛的自然化身。"),
    ("106", "Su", "Soularis", "靈魂擺渡人", "INFJ", "第7週期主族", "看透生死卻依然珍視每一段記憶的引導者。"),
    ("107", "Dm", "Dimensionium", "空間魔術師", "ENTP", "第7週期主族", "思維跳脫三維限制的怪才。"),
    ("108", "Sb", "Superstringium", "萬物模仿者", "ESFP", "第7週期主族", "能完美扮演任何人的全能演員。"),
    ("109", "Nm", "Nightmarium", "夢魘編織者", "INFJ", "第7週期主族", "幫助人面對內心恐懼的另類心理師。"),
    ("110", "Dv", "Divinium", "神聖審判長", "ENTJ", "第7週期主族", "自帶神聖光環、不容許污穢的理想主義者。"),
    ("111", "U", "Universium", "星海巨人", "INFJ", "第7週期主族", "胸懷包羅萬象、帶著宏觀慈悲的神祇。"),
    ("112", "If", "Infinitium", "無限狂想家", "ENTP", "第7週期主族", "精力永遠用不完的永動機少年。"),
    ("113", "Gn", "Genesisium", "創世造物主", "ENFP", "第7週期主族", "熱愛賦予萬物生命與名字的藝術之神。"),
    ("114", "En", "Endorium", "終焉審判者", "INTJ", "第7週期主族", "負責為一切畫下乾淨俐落句點的收尾人。"),
    ("115", "Et", "Eternium", "永恆見證者", "ISTJ", "第7週期主族", "靜靜看著時代更迭卻從不干涉的紀錄者。"),
    ("116", "Sm", "Singularium", "奇點隱士", "INTJ", "第7週期主族", "一開口便是真理的極致沉默深邃智者。"),
    ("117", "Tp", "Temporalis", "時間頑童", "ENTP", "第7週期主族", "對過去與未來瞭若指掌的調皮神明。"),
    ("118", "Og", "Originarium", "本源創始神", "INFP", "第7週期主族", "一切故事的起點與歸宿之最純粹存在。")]

ELEMENTS_118 = []
ELEMENTS_BY_MBTI = {}
for num, sym, eng, title, mbti, period, desc in RAW_ELEMENTS_118:
    meta = MBTI_SYSTEM_META.get(mbti, DEFAULT_META)
    item = {
        "num": num, "sym": sym, "eng": eng, "title": title,
        "mbti": mbti, "period": period, "desc": desc,
        "group": meta["group"], "mbti_name": meta["mbti_name"],
        "month": meta["month"], "month_trait": meta["month_trait"],
        "plant": meta["plant"], "plant_desc": meta["plant_desc"],
        "archetype": meta["archetype"], "archetype_desc": meta["archetype_desc"],
        "primary_color": meta["primary_color"],
        "secondary_color": meta["secondary_color"],
        "color_reason": meta["color_reason"],
        "careers": meta["careers"],
        "advice_word": meta["advice_word"],
        "culinary_taste": meta["culinary_taste"]
    }
    ELEMENTS_118.append(item)
    ELEMENTS_BY_MBTI.setdefault(mbti, []).append(item)


def ensure_extra_tables():
    """確保資料庫包含歷史報告表與暫存進度表，避免任何欄位缺失錯誤。"""
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_reports (
                report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                primary_session_id INTEGER UNIQUE NOT NULL,
                group_id INTEGER NOT NULL DEFAULT 1,
                question_count INTEGER NOT NULL DEFAULT 48,
                element_num TEXT NOT NULL,
                element_sym TEXT NOT NULL,
                element_title TEXT NOT NULL,
                mbti_code TEXT NOT NULL,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_drafts (
                draft_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL DEFAULT 1,
                target_count INTEGER NOT NULL DEFAULT 50,
                current_index INTEGER NOT NULL DEFAULT 0,
                total_questions INTEGER NOT NULL DEFAULT 0,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def score_answers(quiz_id: str, answers_by_question: dict, conn) -> dict:
    dims = conn.execute("SELECT * FROM dimensions WHERE quiz_id = ? ORDER BY dimension_id", (quiz_id,)).fetchall()
    tally = {d["dimension_key"]: {"code_a": d["code_a"], "code_b": d["code_b"], "count_a": 0, "count_b": 0} for d in dims}

    answer_signature = 0
    for qid, option_key in answers_by_question.items():
        q_int = int(qid)
        answer_signature += q_int * (ord(option_key) - 64)
        row = conn.execute("""
            SELECT o.score_code, d.dimension_key
            FROM options o
            JOIN questions q ON q.question_id = o.question_id
            JOIN dimensions d ON d.dimension_id = q.dimension_id
            WHERE q.question_id = ? AND o.option_key = ?
        """, (q_int, option_key)).fetchone()

        if row:
            d_key = row["dimension_key"]
            s_code = row["score_code"]
            if s_code == tally[d_key]["code_a"]:
                tally[d_key]["count_a"] += 1
            elif s_code == tally[d_key]["code_b"]:
                tally[d_key]["count_b"] += 1

    dimension_results = []
    mbti_letters = []
    for idx, d in enumerate(dims):
        d_key = d["dimension_key"]
        cA = tally[d_key]["count_a"]
        cB = tally[d_key]["count_b"]
        code_a = tally[d_key]["code_a"]
        code_b = tally[d_key]["code_b"]
        total = cA + cB

        if total == 0:
            pct_a, pct_b = 50, 50
        else:
            pct_a = round((cA / total) * 100)
            pct_b = 100 - pct_a

        if cA > cB:
            selected = code_a
        elif cB > cA:
            selected = code_b
        else:
            selected = code_a if ((answer_signature + idx) % 2 == 0) else code_b

        desc_row = conn.execute(
            "SELECT result_name, description FROM result_descriptions WHERE quiz_id = ? AND result_code = ?",
            (quiz_id, selected)
        ).fetchone()

        res_info = {"name": "均衡發展型", "description": "在此維度展現高度平衡的特質。"}
        if desc_row:
            res_info = {"name": desc_row["result_name"], "description": desc_row["description"]}

        dimension_results.append({
            "key": d_key,
            "name": d["dimension_name"],
            "code_a": code_a, "count_a": cA, "pct_a": pct_a,
            "code_b": code_b, "count_b": cB, "pct_b": pct_b,
            "selected": selected,
            "description": res_info
        })
        mbti_letters.append(selected)

    mbti_code = "".join(mbti_letters) if len(mbti_letters) == 4 else "INFJ"
    candidates = ELEMENTS_BY_MBTI.get(mbti_code, ELEMENTS_118)
    assigned_element = candidates[answer_signature % len(candidates)]
    peer_elements = [
        {"num": e["num"], "sym": e["sym"], "eng": e["eng"], "title": e["title"], "desc": e["desc"]}
        for e in candidates if e["num"] != assigned_element["num"]
    ]

    return {
        "answered_count": len(answers_by_question),
        "profile_code": mbti_code,
        "dimensions": dimension_results,
        "assigned_element": assigned_element,
        "peer_elements": peer_elements,
        "notice": "本報告結合 16 型人格光譜、《幻界 118 元素圖鑑》與專屬味覺建議生成。"
    }


class UnifiedGroupQuizHandler(BaseHTTPRequestHandler):
    server_version = "MultiQuizWeb/8.0"

    def log_message(self, format, *args):
        print("[web] " + (format % args))

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

    def _send_file(self, file_path: Path):
        if not file_path.exists():
            self.send_error(404, "File not found")
            return
        raw = file_path.read_bytes()
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
            content_type += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
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
        if parsed.path in ("/", "/index.html"):
            self._send_file(HTML_FILE)
            return

        if parsed.path == "/api/elements":
            self._send_json({"ok": True, "total": len(ELEMENTS_118), "elements": ELEMENTS_118})
            return

        if parsed.path == "/api/quizzes":
            try:
                with connect() as conn:
                    quizzes = conn.execute("SELECT quiz_id, group_id, quiz_title, description FROM quizzes ORDER BY group_id, quiz_id").fetchall()
                    self._send_json({"ok": True, "quizzes": [dict(q) for q in quizzes]})
            except Exception as exc:
                self._send_json({"ok": False, "message": str(exc)}, 500)
            return

        if parsed.path == "/api/group-start":
            params = parse_qs(parsed.query)
            group_id = params.get("group_id", ["1"])[0]
            target_count = int(params.get("count", ["0"])[0])
            try:
                with connect() as conn:
                    if target_count >= 200:
                        quizzes = conn.execute("SELECT quiz_id, quiz_title, description FROM quizzes ORDER BY group_id, quiz_id").fetchall()
                    else:
                        quizzes = conn.execute(
                            "SELECT quiz_id, quiz_title, description FROM quizzes WHERE group_id = ? ORDER BY quiz_id",
                            (group_id,)
                        ).fetchall()

                    group_quizzes = []
                    for q in quizzes:
                        q_id = q["quiz_id"]
                        cur = conn.execute("INSERT INTO test_sessions (quiz_id, status, last_question_index) VALUES (?, 'active', 0)", (q_id,))
                        session_id = int(cur.lastrowid)

                        questions = conn.execute(
                            "SELECT question_id, question_type, question_text FROM questions WHERE quiz_id = ? ORDER BY question_id",
                            (q_id,)
                        ).fetchall()

                        q_list = []
                        for item in questions:
                            opts = conn.execute(
                                "SELECT option_key, option_text FROM options WHERE question_id = ? ORDER BY option_key",
                                (item["question_id"],)
                            ).fetchall()
                            q_list.append({
                                "question_id": item["question_id"],
                                "question_type": item["question_type"],
                                "question_text": item["question_text"],
                                "options": [{"key": o["option_key"], "text": o["option_text"]} for o in opts]
                            })

                        group_quizzes.append({
                            "quiz_id": q_id,
                            "quiz_title": q["quiz_title"],
                            "description": q["description"],
                            "session_id": session_id,
                            "questions": q_list
                        })

                    self._send_json({"ok": True, "group_id": group_id, "target_count": target_count, "quizzes": group_quizzes})
            except Exception as exc:
                self._send_json({"ok": False, "message": str(exc)}, 500)
            return

        if parsed.path == "/api/drafts":
            try:
                ensure_extra_tables()
                with connect() as conn:
                    rows = conn.execute("""
                        SELECT draft_id, group_id, target_count, current_index, total_questions, state_json, updated_at
                        FROM quiz_drafts
                        ORDER BY draft_id DESC
                    """).fetchall()
                    drafts = []
                    for r in rows:
                        drafts.append({
                            "draft_id": r["draft_id"],
                            "group_id": r["group_id"],
                            "target_count": r["target_count"],
                            "current_index": r["current_index"],
                            "total_questions": r["total_questions"],
                            "updated_at": r["updated_at"],
                            "state": json.loads(r["state_json"])
                        })
                    self._send_json({"ok": True, "drafts": drafts})
            except Exception as exc:
                self._send_json({"ok": False, "message": str(exc)}, 500)
            return

        if parsed.path == "/api/history":
            try:
                ensure_extra_tables()
                with connect() as conn:
                    rows = conn.execute("""
                        SELECT report_id, primary_session_id, group_id, question_count,
                               element_num, element_sym, element_title, mbti_code,
                               report_json, created_at, is_deleted
                        FROM session_reports
                        ORDER BY report_id DESC
                    """).fetchall()

                    active_list = []
                    deleted_list = []
                    for r in rows:
                        item = {
                            "report_id": r["report_id"],
                            "session_id": r["primary_session_id"],
                            "group_id": r["group_id"],
                            "question_count": r["question_count"],
                            "element_num": r["element_num"],
                            "element_sym": r["element_sym"],
                            "element_title": r["element_title"],
                            "mbti_code": r["mbti_code"],
                            "created_at": r["created_at"],
                            "is_deleted": r["is_deleted"],
                            "report": json.loads(r["report_json"])
                        }
                        if r["is_deleted"] == 1:
                            deleted_list.append(item)
                        else:
                            active_list.append(item)

                    self._send_json({"ok": True, "active_records": active_list, "deleted_records": deleted_list})
            except Exception as exc:
                self._send_json({"ok": False, "message": str(exc)}, 500)
            return

        self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/save-progress":
            try:
                ensure_extra_tables()
                length = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                draft_id = data.get("draft_id")
                group_id = int(data.get("group_id", 1))
                target_count = int(data.get("target_count", 50))
                current_index = int(data.get("current_index", 0))
                total_questions = int(data.get("total_questions", 0))
                state_payload = {
                    "activeGroupQuizzes": data.get("activeGroupQuizzes", []),
                    "allFlattenedQuestions": data.get("allFlattenedQuestions", []),
                    "userAnswersGlobal": data.get("userAnswersGlobal", {}),
                    "currentGlobalQIndex": current_index,
                    "currentGroupId": group_id,
                    "currentTargetCount": target_count
                }
                now_str = datetime.now().isoformat(timespec="seconds")

                with connect() as conn:
                    # 同步更新對應的 test_sessions 狀態為 paused
                    for q in state_payload["activeGroupQuizzes"]:
                        sid = q.get("session_id")
                        if sid:
                            conn.execute(
                                "UPDATE test_sessions SET status = 'paused', last_question_index = ? WHERE session_id = ?",
                                (current_index, sid)
                            )

                    if draft_id:
                        conn.execute("""
                            UPDATE quiz_drafts
                            SET current_index = ?, total_questions = ?, state_json = ?, updated_at = ?
                            WHERE draft_id = ?
                        """, (current_index, total_questions, json.dumps(state_payload, ensure_ascii=False), now_str, int(draft_id)))
                        saved_id = int(draft_id)
                    else:
                        cur = conn.execute("""
                            INSERT INTO quiz_drafts (group_id, target_count, current_index, total_questions, state_json, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (group_id, target_count, current_index, total_questions, json.dumps(state_payload, ensure_ascii=False), now_str))
                        saved_id = int(cur.lastrowid)

                self._send_json({"ok": True, "draft_id": saved_id})
            except Exception as exc:
                self._send_json({"ok": False, "message": str(exc)}, 500)
            return

        if parsed.path == "/api/drafts/delete":
            try:
                ensure_extra_tables()
                length = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                draft_id = int(data.get("draft_id"))
                with connect() as conn:
                    conn.execute("DELETE FROM quiz_drafts WHERE draft_id = ?", (draft_id,))
                self._send_json({"ok": True})
            except Exception as exc:
                self._send_json({"ok": False, "message": str(exc)}, 500)
            return

        if parsed.path == "/api/submit-unified-group":
            try:
                ensure_extra_tables()
                length = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                submissions = data.get("submissions", [])
                group_id = int(data.get("group_id", 1))
                draft_id = data.get("draft_id")

                combined_answers = {}
                now_str = datetime.now().isoformat(timespec="seconds")
                with connect() as conn:
                    for sub in submissions:
                        session_id = sub.get("session_id")
                        answers = sub.get("answers", {})

                        for qid, opt_key in answers.items():
                            combined_answers[qid] = opt_key
                            opt = conn.execute("SELECT option_id FROM options WHERE question_id = ? AND option_key = ?", (int(qid), opt_key)).fetchone()
                            if opt:
                                conn.execute("""
                                    INSERT INTO answers (session_id, question_id, option_id) VALUES (?, ?, ?)
                                    ON CONFLICT(session_id, question_id) DO UPDATE SET option_id = ?
                                """, (session_id, int(qid), opt["option_id"], opt["option_id"]))

                        conn.execute(
                            "UPDATE test_sessions SET status = 'completed', completed_at = ? WHERE session_id = ?",
                            (now_str, session_id)
                        )

                    if draft_id:
                        conn.execute("DELETE FROM quiz_drafts WHERE draft_id = ?", (int(draft_id),))

                    base_quiz_id = submissions[0]["quiz_id"] if submissions else "mbti_16"
                    primary_session_id = submissions[0]["session_id"] if submissions else 0
                    unified_result = score_answers(base_quiz_id, combined_answers, conn)
                    el = unified_result["assigned_element"]

                    conn.execute("""
                        INSERT OR REPLACE INTO session_reports
                        (primary_session_id, group_id, question_count, element_num, element_sym, element_title, mbti_code, report_json, created_at, is_deleted)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """, (
                        primary_session_id, group_id, len(combined_answers),
                        el["num"], el["sym"], el["title"], el["mbti"],
                        json.dumps(unified_result, ensure_ascii=False), now_str
                    ))

                self._send_json({"ok": True, "unified_result": unified_result})
            except Exception as exc:
                self._send_json({"ok": False, "message": str(exc)}, 500)
            return

        if parsed.path in ("/api/history/delete", "/api/history/restore"):
            is_del = 1 if parsed.path.endswith("/delete") else 0
            try:
                ensure_extra_tables()
                length = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                report_id = int(data.get("report_id"))
                with connect() as conn:
                    row = conn.execute("SELECT primary_session_id FROM session_reports WHERE report_id = ?", (report_id,)).fetchone()
                    conn.execute("UPDATE session_reports SET is_deleted = ? WHERE report_id = ?", (is_del, report_id))
                    if row:
                        conn.execute("UPDATE test_sessions SET is_deleted = ? WHERE session_id = ?", (is_del, row["primary_session_id"]))
                self._send_json({"ok": True, "report_id": report_id, "is_deleted": is_del})
            except Exception as exc:
                self._send_json({"ok": False, "message": str(exc)}, 500)
            return

        self.send_error(404)


def main():
    if not DB_FILE.exists():
        from seed_database import init_and_seed
        init_and_seed()
    ensure_extra_tables()

    server = ThreadingHTTPServer((HOST, PORT), UnifiedGroupQuizHandler)
    print("==================================================")
    print(" 幻界 118 元素 × 16 型人格深度心理測驗系統已啟動！")
    print(f" 請在瀏覽器開啟：http://{HOST}:{PORT}")
    print("==================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n伺服器已安全停止。")


if __name__ == "__main__":
    main()
