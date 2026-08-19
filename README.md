# ProTaro Project (ProTaro-Core)

[![DOI](https://zenodo.org/badge/1335480489.svg)](https://doi.org/10.5281/zenodo.22005942)

> **A Dual-Black-Box Control Framework for Safe AI Self-Counseling via Symbolic Projection (Tarot) and Generative LLM**

---

## 📄 Overview（概要）
ProTaro は、大規模言語モデル（LLM）とタロットカードの象徴的イメージ（投影法）を統合し、ユーザーの安全な心理的自己リフレクション（Self-insight）を促進するセルフカウンセリング・アプリケーションの構築モデルおよびリファレンス実装です。

従来型の「AI占い」や直感的な「アドバイス型チャットボット」が抱えるハルシネーション（誤情報の出力）や過度な依存、表層的・断定的な説教リスクを排し、ゲシュタルト療法における投影（projection）機序および臨床心理学における「臨床の知」に基づいた独自の制御アルゴリズムを導入しています。

---

## 🧠 Theoretical Background（理論的背景）
本フレームワークは、以下の心理臨床理論および構造的課題の再解釈に基づき設計されています。

* **投影機序（Projection Mechanism）の活用**  
  パールズ（Perls, 1947/1969）の定義に基づき、意識化されにくい内面的な感情やモヤモヤを、タロットカードという「多義的で非意図的な象徴（外界の対象）」へと安全に視覚化・外在化させます（Au-Yeung, 2025）。

* **「二重のブラックボックス」の再定義**  
  本システムは構造的に、① 象徴の多義性と選出の不確実性（タロット） と ② 内部決定プロセスの非追跡性/不透明性（LLM） という「二重のブラックボックス」を内包しています。  
  本プロジェクトでは、この不確実性を単に排除・抑制するのではなく、適切な臨床的ガードレール（安全弁）を施すことで、ユーザーの意味付けを邪魔しないオープンな「心の鏡」としての心理的効果へと昇華させています。

---

## 🚀 Novelty & Algorithm Design（アルゴリズムの新規性と特徴）

### 1. 臨床的ガードレール（Clinical Guardrails）の構造化
* **事前文脈（プロンプト）の非意図的選出:** カード選出前に詳細な事前文脈をAIに与えないことで、AIによる断定や先入観に基づく説教を構造的に排除。
* **鏡映的問いかけ（Mirroring Facilitation）:** AIは解決策や未来の予言を「提示」するのではなく、ユーザーがカードのイメージから何を感じ取ったかを問い返す受容的対話ロジック（Gemini API等に最適化されたプロンプト制約）を実装。
* **3回反復による交点抽出:** 対話を3回（3ステップ）のシークエンスに限定し、対話の無限ループ（依存）を防ぎつつ、思考の「交点（核心的な気づき）」を抽出。

### 2. インフラ・API経費抑制と安全性の両立
* **Rate-Limiting Logic（過剰利用防止）:** IP単位および全体アクセス制御により、同一ユーザーによる無制限な連打（ループ利用）を抑制。依存防止という臨床的意義と、API運用コストの最小化を同時に達成。

---

## 🏗️ System Architecture（システム構成）

```text
[ User Input / Trigger ]
         │
         ▼
 [ 1. Symbolic Selection ] ─── (Tarot Card / Archetype Image)
         │
         ▼ (No Prior Context Overload)
 [ 2. Clinical Guardrail Engine ]
   ├── Prompt Constraints (Non-judgmental / Mirroring)
   ├── Gemini API (LLM Session)
   └── Rate-Limiting Controller (Daily Limits & Circuit Breaker)
         │
         ▼
 [ 3. Iterative Dialogue (Max 3 Loops) ]
         │
         ▼
 [ 4. Intersection Extraction & Self-Insight ] ─── [ Anonymous Evaluation ]
```

## 🛠️ Tech Stack（使用技術）

    Backend Framework: Python 3.10+ / Flask
    AI Engine: Google Gemini API (gemini-2.5-flash)
    Infrastructure / Hosting: Render
    Security & Auth: Environment Variables Management (API Keys, Session Secret Key, Hash Passwords)

## 💻 Getting Started（開発環境での実行方法）

1. Repository Clone
```bash
git clone https://github.com/Project-Tarot/projectarot.git
cd projectarot
```

2. Dependencies Installation
```bash
pip install -r requirements.txt
```

3. Environment Variables Setting
動作に必要な以下の環境変数を設定してください（.env またはホスティング環境）。
```bash
    GEMINI_API_KEY: Google Gemini API Key
    SECRET_KEY: Flask Session Signature Key
    ADMIN_PASSWORD: Administrator Password
    USER_PASSWORD: General User Password
```

5. Local Run
```bash
python app.py
```
ブラウザで http://localhost:5000 にアクセスします。

## 🔬 Research & Ethics（研究と倫理）

本プロジェクトは、高等教育機関や一般ユーザーを対象とした学術実証研究として展開されています。
    インフォームド・コンセントの組み込み: アプリケーション初期起動時に、研究目的およびデータ提供の任意性についての説明・同意UIを完備。
    プライバシーと匿名性: 対話ログおよび評価アンケートデータは完全に匿名化（Anonymized）処理され、個人のプライバシーを厳重に保護します。

## ✒️ Citation / How to Cite（引用表記）

本リポジトリのコードやアルゴリズムの概念を論文・学会等で引用される場合は、以下の表記をご使用ください。

```text
@misc{Izumi2026ProTaro,
  author       = {Mitsunori Izumi},
  title        = {ProTaro: A Dual-Black-Box Control Framework for Safe AI Self-Counseling via Symbolic Projection},
  year         = {2026},
  publisher    = {GitHub},
  journal      = {GitHub repository},
  howpublished = {\url{[https://github.com/](https://github.com/)[YOUR_GITHUB_USERNAME]/[YOUR_REPOSITORY_NAME]}}
}
```

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
