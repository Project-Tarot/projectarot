# ProTaro Project (ProTaro-Core)

> **A Dual-Black-Box Control Framework for Safe AI Self-Counseling via Symbolic Projection (Tarot) and Generative LLM**  
> **タロットの象徴的投影とLLM受容対話による「二重のブラックボックス」制御型AIセルフカウンセリング・フレームワーク**

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
* **Rate-Limiting Logic（過剰利用防止）:** ブラウザストレージおよびアクセス制御により、同一ユーザーによる無制限な連打（ループ利用）を抑制。依存防止という臨床的意義と、API運用コストの最小化を同時に達成。

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
   └── Rate-Limiting Controller (1-Session Rule)
         │
         ▼
 [ 3. Iterative Dialogue (Max 3 Loops) ]
         │
         ▼
 [ 4. Intersection Extraction & Self-Insight ] ─── [ Anonymous Evaluation ]
