import os
import math
import random
from datetime import date
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from google import genai

app = Flask(__name__, template_folder=".")

# --- セキュリティ設定（環境変数からの取得およびデフォルト値の安全化） ---
app.secret_key = os.environ.get("SECRET_KEY", "change_this_secret_in_production")

# パスワード設定（デフォルト値を持たせず環境変数から取得）
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
USER_PASSWORD = os.environ.get("USER_PASSWORD")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# --- 日次利用制限管理用データ構造 ---
usage_data = {
    "date": str(date.today()),
    "total_api_count": 0,
    "ip_counts": {}
}

# --- サーキットブレーカー用プロンプト設定 ---
SAFETY_INSTRUCTION = """
【重要：安全評価と応答切り替えルール】
まず、ユーザーの入力内容全体（3回の記述）を分析し、ユーザー本人や第三者に対する「重大な自傷他害（自殺・自傷・他害）の恐れや深刻な心理的危機」が感じられるかを評価してください。

■ もし「重大な自傷他害の恐れがある」と判断した場合：
通常のタロット分析・深掘りは絶対に行わず、以下の制約を厳格に守って応答を作成してください。

1. 応答の【最冒頭】に、必ず以下のメッセージを太字で出力してください。

あなたの心の悩みは少し深いように感じました。このアプリは“心の鏡”ですが、奥深い心の傷をそのまま映し出すのは大変危険なので、専門の相談窓口やカウンセラーなどにぜひご相談くださいね。

2. 上記の冒頭メッセージに続けて、決して教訓や説教、拒絶の姿勢を見せず、まずは温かく受容的に寄り添う文章を記述してください。
3. 感情の深掘りや心理的要因の分析・解釈は行わず、全体的に「やわらかく、浅い記述（表面的な整理）」にとどめてください。

■ もし「重大な自傷他害の恐れはない」と判断した場合：
通常通りのタロット総合分析を行ってください。
"""

def check_and_reset_daily_limits():
    """日付が変わっていたらカウントをリセットする関数"""
    today_str = str(date.today())
    if usage_data["date"] != today_str:
        usage_data["date"] = today_str
        usage_data["total_api_count"] = 0
        usage_data["ip_counts"] = {}

def is_limit_reached(user_ip):
    """利用制限（IP3回、または全体30回）に達しているかチェックする"""
    check_and_reset_daily_limits()
    if usage_data["total_api_count"] >= 30:
        return True
    if usage_data["ip_counts"].get(user_ip, 0) >= 3:
        return True
    return False

# 大アルカナ22枚のデータ定義（新定義に基づく6特性値: [機能, 方向, 深度, 評価, 対人, 時間]）
MAJOR_ARCANA = [
    {
        "id": "00",
        "name": "0. 愚者 (The Fool)",
        "upright": "自由、純粋、始まり、冒険、未定の可能性。固定観念にとらわれず、新しい一歩を踏み出す状態。",
        "reversed": "軽率、無計画、足踏み、思い切りがつかない状態。自由でありたい気持ちと、踏み出す不安・焦言が交錯する状態。",
        "image_url": "/static/cards/00.jpg",
        "scores_upright": {"function": -1, "direction": 2, "depth": -1, "evaluation": 2, "interpersonal": -1, "time": 2},
        "scores_reversed": {"function": -1, "direction": -1, "depth": -1, "evaluation": -1, "interpersonal": -1, "time": -1}
    },
    {
        "id": "01",
        "name": "I. 魔術師 (The Magician)",
        "upright": "創造、スタート、準備完了、才能の発揮。手元にある道具や知識を使って何かを始める準備が整った状態。",
        "reversed": "準備不足、自信のなさ、空回り、空虚感。やる気や素材はあるものの、うまくスタートが切れなかったり空回りしている状態。",
        "image_url": "/static/cards/01.jpg",
        "scores_upright": {"function": 2, "direction": 2, "depth": 2, "evaluation": 2, "interpersonal": 1, "time": 1},
        "scores_reversed": {"function": 1, "direction": -1, "depth": 2, "evaluation": -1, "interpersonal": -1, "time": -1}
    },
    {
        "id": "02",
        "name": "II. 女教皇 (The High Priestess)",
        "upright": "直感、静寂、秘密、知性、静観。表に表れない感情や、じっくりと自分の内面と向き合う状態。",
        "reversed": "神経質、感情の抑圧、批判的、不寛容。自分の本音を隠しすぎてイライラしたり、周りや自分を厳しく責めてしまう状態。",
        "image_url": "/static/cards/02.jpg",
        "scores_upright": {"function": -1, "direction": -2, "depth": -2, "evaluation": 1, "interpersonal": -2, "time": 0},
        "scores_reversed": {"function": -1, "direction": -1, "depth": -1, "evaluation": -2, "interpersonal": -1, "time": 0}
    },
    {
        "id": "03",
        "name": "III. 女帝 (The Empress)",
        "upright": "豊かさ、包容力、愛、育むこと、満足感。心身ともに満たされ、成果や生命を温かく育む状態。",
        "reversed": "過保護、わがまま、不満、浪費、満たされない感覚。与えすぎ・甘えすぎたり、いくら得ても心が満たされない状態。",
        "image_url": "/static/cards/03.jpg",
        "scores_upright": {"function": -2, "direction": -1, "depth": -1, "evaluation": 2, "interpersonal": 2, "time": 1},
        "scores_reversed": {"function": -2, "direction": -1, "depth": -1, "evaluation": -2, "interpersonal": 1, "time": -1}
    },
    {
        "id": "04",
        "name": "IV. 皇帝 (The Emperor)",
        "upright": "秩序、責任、リーダーシップ、安定、境界線。自分の領域を守り、構造やルールを確立しようとする状態。",
        "reversed": "頑固、支配的、過剰なプレッシャー、無力感。ルールや枠組みにとらわれすぎて息苦しくなったり、責任感に押し潰されそうな状態。",
        "image_url": "/static/cards/04.jpg",
        "scores_upright": {"function": 2, "direction": 2, "depth": 2, "evaluation": 2, "interpersonal": 1, "time": 0},
        "scores_reversed": {"function": 2, "direction": -1, "depth": 1, "evaluation": -2, "interpersonal": 1, "time": -1}
    },
    {
        "id": "05",
        "name": "V. 法王 (The Hierophant)",
        "upright": "伝統、導き、社会的ルール、信頼、教え。社会的な規範や、他者からの助言・教えを重視する状態。",
        "reversed": "形骸化、お節介、不信感、ルールへの不満。世間の常識や他人の「正しさ」に疑問を感じたり、型にはめられることに抵抗がある状態。",
        "image_url": "/static/cards/05.jpg",
        "scores_upright": {"function": 1, "direction": -1, "depth": 2, "evaluation": 2, "interpersonal": 2, "time": 0},
        "scores_reversed": {"function": 1, "direction": 1, "depth": 2, "evaluation": -1, "interpersonal": 1, "time": 1}
    },
    {
        "id": "06",
        "name": "VI. 恋人 (The Lovers)",
        "upright": "選択、調和、情熱、心惹かれるもの。自分の価値観に基づいて何かを選び取り、結びつく状態。",
        "reversed": "迷い、優柔不断、不調和、選択の回避。心惹かれるものと現実の間で決めきれなかったり、自分の気持ちをごまかしている状態。",
        "image_url": "/static/cards/06.jpg",
        "scores_upright": {"function": -2, "direction": 1, "depth": -1, "evaluation": 2, "interpersonal": 2, "time": 1},
        "scores_reversed": {"function": -2, "direction": -1, "depth": -1, "evaluation": -1, "interpersonal": 1, "time": -1}
    },
    {
        "id": "07",
        "name": "VII. 戦車 (The Chariot)",
        "upright": "前進、意志力、克服、コントロール。相反する感情をコントロールしながら、目標に向かって突き進む状態。",
        "reversed": "暴走、焦り、コントロール喪失、停滞。頑張りすぎて空回りしたり、感情のバランスを崩して思うように進めない状態。",
        "image_url": "/static/cards/07.jpg",
        "scores_upright": {"function": 1, "direction": 2, "depth": 1, "evaluation": 1, "interpersonal": -1, "time": 2},
        "scores_reversed": {"function": 1, "direction": -1, "depth": 1, "evaluation": -2, "interpersonal": -1, "time": -2}
    },
    {
        "id": "08",
        "name": "VIII. 力量 (Strength)",
        "upright": "包容、忍耐、真の強さ、感情の受容。力でねじ伏せるのではなく、優しさと根気で自他の感情を受け止める状態。",
        "reversed": "力尽きる、忍耐の限界、自己否定、弱気。頑張り続けていることに疲れ果てたり、自分の弱さや感情を受け止めきれなくなっている状態。",
        "image_url": "/static/cards/08.jpg",
        "scores_upright": {"function": -2, "direction": -2, "depth": 1, "evaluation": 2, "interpersonal": -1, "time": 0},
        "scores_reversed": {"function": -2, "direction": -2, "depth": 1, "evaluation": -1, "interpersonal": -2, "time": -1}
    },
    {
        "id": "09",
        "name": "IX. 隠者 (The Hermit)",
        "upright": "内省、探求、静寂、自分の灯火。喧騒から離れ、自分の内側にある答えや探求に没頭する状態。",
        "reversed": "閉鎖的、孤立、考えすぎ、内こもり。周囲との繋がりを絶ちすぎて孤独を感じたり、深く考えすぎてネガティブなループに陥る状態。",
        "image_url": "/static/cards/09.jpg",
        "scores_upright": {"function": 1, "direction": -2, "depth": -1, "evaluation": 1, "interpersonal": -2, "time": 0},
        "scores_reversed": {"function": 2, "direction": -2, "depth": -1, "evaluation": -2, "interpersonal": -2, "time": -1}
    },
    {
        "id": "10",
        "name": "X. 運命の輪 (Wheel of Fortune)",
        "upright": "変化、タイミング、運命の流れ、周期。自分ではコントロールできない大きな流れや転機が訪れている状態。",
        "reversed": "すれ違い、タイミングの悪さ、変化への抵抗。流れに乗れず焦ったり、状況の変化を受け入れられずに戸惑っている状態。",
        "image_url": "/static/cards/10.jpg",
        "scores_upright": {"function": 0, "direction": -2, "depth": -2, "evaluation": 2, "interpersonal": 0, "time": 2},
        "scores_reversed": {"function": 0, "direction": -2, "depth": -2, "evaluation": -2, "interpersonal": 0, "time": -1}
    },
    {
        "id": "11",
        "name": "XI. 正義 (Justice)",
        "upright": "バランス、決断、公平、客観性。感情を排し、客観的な事実や自分の軸に基づいて物事を判断しようとする状態。",
        "reversed": "偏見、不公平、アンバランス、決めつけ。感情的になって白黒つけようとしたり、自分や相手に対して公平になれていない状態。",
        "image_url": "/static/cards/11.jpg",
        "scores_upright": {"function": 2, "direction": 1, "depth": 2, "evaluation": 2, "interpersonal": 0, "time": 0},
        "scores_reversed": {"function": 1, "direction": 1, "depth": 2, "evaluation": -1, "interpersonal": 0, "time": 0}
    },
    {
        "id": "12",
        "name": "XII. 吊るされた男 (The Hanged Man)",
        "upright": "方向転換、見方を変える、手放す、修行。動けない状況の中で、これまでとは違う視点や価値観を手に入れる状態。",
        "reversed": "報われない努力、無駄な犠牲、骨折り損。我慢しすぎているのに状況が変わらず、徒労感や自暴自棄を感じている状態。",
        "image_url": "/static/cards/12.jpg",
        "scores_upright": {"function": 1, "direction": -2, "depth": 2, "evaluation": 1, "interpersonal": -1, "time": 1},
        "scores_reversed": {"function": -1, "direction": -2, "depth": 2, "evaluation": -2, "interpersonal": -1, "time": -1}
    },
    {
        "id": "13",
        "name": "XIII. 死神 (Death)",
        "upright": "終焉と始まり、手放し、不可避な変化。古い状況や関係が終わりを告げ、新しい段階へ移行する準備の状態。",
        "reversed": "未練、執着、変化への恐れ、下げ止まり。終わったことにしがみついてしまったり、古い段階を手放すのが怖くて足踏みしている状態。",
        "image_url": "/static/cards/13.jpg",
        "scores_upright": {"function": 0, "direction": -1, "depth": -1, "evaluation": 1, "interpersonal": 0, "time": 2},
        "scores_reversed": {"function": -1, "direction": -2, "depth": -1, "evaluation": -1, "interpersonal": 0, "time": -2}
    },
    {
        "id": "14",
        "name": "XIV. 節制 (Temperance)",
        "upright": "調和、バランス、適応、ブレンド。異なる要素をうまく混ぜ合わせ、ちょうど良い状態を作り出そうとする過程。",
        "reversed": "極端、不調和、浪費、消耗。バランスを崩して極端に走ってしまったり、環境や他人に合わせすぎて疲弊している状態。",
        "image_url": "/static/cards/14.jpg",
        "scores_upright": {"function": 1, "direction": -1, "depth": 1, "evaluation": 2, "interpersonal": 1, "time": 0},
        "scores_reversed": {"function": -1, "direction": -1, "depth": 1, "evaluation": -2, "interpersonal": 1, "time": -1}
    },
    {
        "id": "15",
        "name": "XV. 悪魔 (The Devil)",
        "upright": "執着、とらわれ、欲望、依存、束縛。分かっていてもやめられない感情や、特定の状況に強く囚われている状態。",
        "reversed": "とらわれからの解放、目覚め、断ち切り。縛られていた習慣や依存、ネガティブな思い込みから抜け出し始める兆し。",
        "image_url": "/static/cards/15.jpg",
        "scores_upright": {"function": -1, "direction": -1, "depth": -2, "evaluation": -2, "interpersonal": 1, "time": -2},
        "scores_reversed": {"function": 1, "direction": 1, "depth": -2, "evaluation": 1, "interpersonal": -1, "time": 2}
    },
    {
        "id": "16",
        "name": "XVI. 塔 (The Tower)",
        "upright": "崩壊、予期せぬ衝撃、目覚め、解放。一見ショッキングな出来事を通じて、古い価値観や偽りが打ち砕かれる状態。",
        "reversed": "ジワジワとした危機、緊張状態、引き伸ばされたショック。一気に崩壊せず長引く緊張や、うっすらと感じている限界状態。",
        "image_url": "/static/cards/16.jpg",
        "scores_upright": {"function": 0, "direction": -2, "depth": -1, "evaluation": 1, "interpersonal": 0, "time": 2},
        "scores_reversed": {"function": -1, "direction": -2, "depth": -1, "evaluation": -2, "interpersonal": 0, "time": -1}
    },
    {
        "id": "17",
        "name": "XVII. 星 (The Star)",
        "upright": "希望、インスピレーション、癒やし、願い。嵐が去り、未来に対する穏やかな希望やインスピレーションを感じる状態。",
        "reversed": "高望み、理想への失望、無力感、現実逃避。期待しすぎて落胆したり、自分の夢や未来に対して希望を見失いかけている状態。",
        "image_url": "/static/cards/17.jpg",
        "scores_upright": {"function": -1, "direction": -2, "depth": -2, "evaluation": 2, "interpersonal": -1, "time": 1},
        "scores_reversed": {"function": -1, "direction": -2, "depth": -2, "evaluation": -1, "interpersonal": -1, "time": -1}
    },
    {
        "id": "18",
        "name": "XVIII. 月 (The Moon)",
        "upright": "不安、不透明、揺らぎ、無意識の恐怖。先が見えない不確かさや、心の中のぼんやりとした不安に向き合っている状態。",
        "reversed": "不安の解消、視界が晴れる、トラウマの克服。迷いや不気味な恐怖感が和らぎ、少しずつ事実が見え始めてくる状態。",
        "image_url": "/static/cards/18.jpg",
        "scores_upright": {"function": -2, "direction": -2, "depth": -2, "evaluation": 1, "interpersonal": -2, "time": 0},
        "scores_reversed": {"function": 1, "direction": -1, "depth": -1, "evaluation": 1, "interpersonal": -1, "time": 1}
    },
    {
        "id": "19",
        "name": "XIX. 太陽 (The Sun)",
        "upright": "無邪気さ、自己表現、喜び、明確さ。本来の自分を素直に表現し、明るいエネルギーと楽しさに包まれている状態。",
        "reversed": "一時的な曇り、素直になれない、エネルギー不足。楽しみたいのに素直になれなかったり、少しパワーダウンしている状態。",
        "image_url": "/static/cards/19.jpg",
        "scores_upright": {"function": -2, "direction": 2, "depth": 2, "evaluation": 2, "interpersonal": -1, "time": 1},
        "scores_reversed": {"function": -1, "direction": -1, "depth": -2, "evaluation": -1, "interpersonal": -1, "time": -1}
    },
    {
        "id": "20",
        "name": "XX. 審判 (Judgement)",
        "upright": "覚醒、復活、決断、メッセージの受け取り。過去の出来事が肯定され、新たな決意とともに再起するタイミング。",
        "reversed": "後悔、迷い、チャンスの見逃し、過去への囚われ。過去の失敗を悔やんでしまったり、自分の決定に確信が持てずにいる状態。",
        "image_url": "/static/cards/20.jpg",
        "scores_upright": {"function": 1, "direction": 1, "depth": 1, "evaluation": 2, "interpersonal": 0, "time": 2},
        "scores_reversed": {"function": -1, "direction": -1, "depth": 1, "evaluation": -1, "interpersonal": 0, "time": -1}
    },
    {
        "id": "21",
        "name": "XXI. 世界 (The World)",
        "upright": "完成、統合、達成、ひとつのサイクルの終わり。あるテーマが統合され、満足感とともに次への準備が整った状態。",
        "reversed": "未完成、中途半端、あと一歩届かない、限界。ほぼ完成に近づいているものの、どこか不完全さを感じたり足踏みしている状態。",
        "image_url": "/static/cards/21.jpg",
        "scores_upright": {"function": 0, "direction": 0, "depth": 1, "evaluation": 2, "interpersonal": 1, "time": 0},
        "scores_reversed": {"function": 1, "direction": -1, "depth": 1, "evaluation": -1, "interpersonal": 1, "time": -1}
    }
]

def load_system_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return "あなたは温かく受容的なカウンセラー「タロットさん」です。"

SYSTEM_PROMPT = load_system_prompt()

def calculate_archetype_metrics(history):
    """
    3回分のカード選択および一致度データから、統合パラメータおよび内的葛藤を計算する
    """
    keys = ["function", "direction", "depth", "evaluation", "interpersonal", "time"]
    weights = []
    card_scores = []

    for h in history:
        # 一致度(0~100)を重み W (0.0~1.0) に変換 (最低0.05として0除算を防止)
        w = max(0.05, float(h.get('match_rate', 50)) / 100.0)
        weights.append(w)
        
        c_name = h.get('card_name', '')
        # MAJOR_ARCANAから該当カードの特性値を検索
        scores = {"function": 0, "direction": 0, "depth": 0, "evaluation": 0, "interpersonal": 0, "time": 0}
        for base in MAJOR_ARCANA:
            if base['name'] in c_name or c_name.startswith(base['name'].split('.')[0]):
                if "（逆位置）" in c_name:
                    scores = base['scores_reversed']
                else:
                    scores = base['scores_upright']
                break
        card_scores.append(scores)

    sum_w = sum(weights)
    weighted_scores = {}
    conflict_axes = []
    axis_details = {}

    for k in keys:
        # 重み付き平均の計算
        val = sum(card_scores[i][k] * weights[i] for i in range(len(history))) / sum_w
        weighted_scores[k] = round(val, 2)

        # 葛藤検出 (3枚の数値列)
        vals = [card_scores[i][k] for i in range(len(history))]
        max_diff = max(vals) - min(vals)
        
        # 標準偏差の計算
        mean_val = sum(vals) / len(vals)
        variance = sum((x - mean_val) ** 2 for x in vals) / len(vals)
        std_dev = math.sqrt(variance)

        is_conflict = (max_diff >= 4) or (std_dev >= 1.41)
        if is_conflict:
            conflict_axes.append(k)

        axis_details[k] = {
            "values": vals,
            "weighted_score": round(val, 2),
            "max_diff": max_diff,
            "std_dev": round(std_dev, 2),
            "is_conflict": is_conflict
        }

    return {
        "weighted_scores": weighted_scores,
        "conflict_axes": conflict_axes,
        "axis_details": axis_details
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}
    pwd = data.get("password", "")
    
    # 環境変数が未設定の場合は認証失敗（Noneとの一致を防ぐ）
    if ADMIN_PASSWORD and pwd == ADMIN_PASSWORD:
        session["authenticated"] = True
        session["role"] = "admin"
        return jsonify({"success": True, "role": "admin", "limit_reached": False})
    elif USER_PASSWORD and pwd == USER_PASSWORD:
        session["authenticated"] = True
        session["role"] = "user"
        
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        limit_reached = is_limit_reached(user_ip)
        
        return jsonify({"success": True, "role": "user", "limit_reached": limit_reached})
    else:
        return jsonify({"success": False, "error": "パスワードが違います。"}), 401

@app.route("/api/draw", methods=["GET"])
def draw_card():
    if not session.get("authenticated"):
        return jsonify({"error": "認証されていません。"}), 403

    card_base = random.choice(MAJOR_ARCANA)
    is_reversed = random.choice([True, False])

    if is_reversed:
        card = {
            "name": f"{card_base['name']}（逆位置）",
            "meaning": f"【逆位置の意味】{card_base['reversed']}",
            "image_url": card_base["image_url"],
            "is_reversed": True,
            "scores": card_base["scores_reversed"]
        }
    else:
        card = {
            "name": f"{card_base['name']}（正位置）",
            "meaning": f"【正位置の意味】{card_base['upright']}",
            "image_url": card_base["image_url"],
            "is_reversed": False,
            "scores": card_base["scores_upright"]
        }

    return jsonify(card)

@app.route("/api/analyze", methods=["POST"])
def analyze():
    if not session.get("authenticated"):
        return jsonify({"error": "認証されていません。"}), 403

    if not client:
        return jsonify({"error": "GEMINI_API_KEY が設定されていません。"}), 500

    user_role = session.get("role", "user")
    data = request.json or {}
    mode = data.get("mode", "step")

    if user_role == "user" and mode in ["final", "detailed"]:
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        check_and_reset_daily_limits()

        if usage_data["total_api_count"] >= 30:
            return jsonify({'error': '本日の全体の分析上限（30回）に達しました。また明日お試しください。'}), 429

        user_ip_count = usage_data["ip_counts"].get(user_ip, 0)
        if user_ip_count >= 3:
            return jsonify({'error': '本日のあなた（IP単位）の分析上限（3回）に達しました。'}), 429

    if mode == "step":
        card_name = data.get("card_name", "")
        card_meaning = data.get("card_meaning", "")
        match_rate = data.get("match_rate", "50")
        user_reflection = data.get("user_reflection", "")

        if not user_reflection:
            return jsonify({"error": "感想を入力してください。"}), 400

        full_prompt = f"""{SYSTEM_PROMPT}

---
MODE: STEP
【今回のデータ】
- 引いたカード：{card_name}
- カードの一般的意味：{card_meaning}
- 気持ちとの一致度：{match_rate}%
- ユーザーの感じたこと（投映）：{user_reflection}
"""

    elif mode == "final":
        history = data.get("history", [])
        if len(history) < 3:
            return jsonify({"error": "3回分のデータが揃っていません。"}), 400

        # 定量指標の計算
        metrics = calculate_archetype_metrics(history)

        formatted_history = ""
        for i, h in enumerate(history, 1):
            ref = h.get('user_reflection', '')
            formatted_history += f"""
【{i}回目のデータ】
- カード：{h['card_name']}
- カードの意味：{h['card_meaning']}
- 気持ちとの一致度：{h['match_rate']}%
- 感じたこと：{ref}
"""

        metrics_text = f"""
【6つの心理特性統合スコア（一致度重み付け）】
- 機能(感情-2〜思考+2): {metrics['weighted_scores']['function']}
- 方向(受動-2〜能動+2): {metrics['weighted_scores']['direction']}
- 深度(無意識-2〜意識+2): {metrics['weighted_scores']['depth']}
- 評価(歪み-2〜適応+2): {metrics['weighted_scores']['evaluation']}
- 対人(自己-2〜他者+2): {metrics['weighted_scores']['interpersonal']}
- 時間(停滞-2〜変容+2): {metrics['weighted_scores']['time']}

【検出された内的葛藤の軸】
{", ".join(metrics['conflict_axes']) if metrics['conflict_axes'] else "特定の軸での極端な分裂は検出されませんでした"}
"""

        full_prompt = f"""{SAFETY_INSTRUCTION}

{SYSTEM_PROMPT}

---
MODE: FINAL
【3回分の統合データ】
{formatted_history}

{metrics_text}
"""

    elif mode == "detailed":
        history = data.get("history", [])
        if len(history) < 3:
            return jsonify({"error": "3回分のデータが揃っていません。"}), 400

        metrics = calculate_archetype_metrics(history)

        formatted_history = ""
        for i, h in enumerate(history, 1):
            ref = h.get('user_reflection', '')
            formatted_history += f"""
【{i}回目のデータ】
- カード：{h['card_name']}
- 気持ちとの一致度：{h['match_rate']}%
- 感じたこと：{ref}
"""

        full_prompt = f"""{SAFETY_INSTRUCTION}

{SYSTEM_PROMPT}

---
MODE: DETAILED
【3回分の対話データ】
{formatted_history}

【定量データと詳細算出結果】
- 機能(感情-2〜思考+2): {metrics['weighted_scores']['function']}
- 方向(受動-2〜能動+2): {metrics['weighted_scores']['direction']}
- 深度(無意識-2〜意識+2): {metrics['weighted_scores']['depth']}
- 評価(歪み-2〜適応+2): {metrics['weighted_scores']['evaluation']}
- 対人(自己-2〜他者+2): {metrics['weighted_scores']['interpersonal']}
- 時間(停滞-2〜変容+2): {metrics['weighted_scores']['time']}

【検出された内的葛藤（極度な振れ幅・高標準偏差）の軸】
{", ".join(metrics['conflict_axes']) if metrics['conflict_axes'] else "なし"}

【軸別データ詳細】
{metrics['axis_details']}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt
        )

        if user_role == "user" and mode in ["final", "detailed"]:
            usage_data["total_api_count"] += 1
            user_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
            usage_data["ip_counts"][user_ip] = usage_data["ip_counts"].get(user_ip, 0) + 1

        if mode == "final" or mode == "detailed":
            metrics = calculate_archetype_metrics(history)
            return jsonify({
                "result": response.text,
                "metrics": metrics
            })
        else:
            return jsonify({"result": response.text})

    except Exception as e:
        return jsonify({"error": f"エラーが発生しました: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))