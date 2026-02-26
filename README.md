# Life-WBS-Manager

> **"Average is a fine. Status Quo is a debt."**
> 人生を100億円の巨大プロジェクトと定義し、現状維持による「機会損失」を可視化する、行動喚起型予実管理ツール。

## 📖 Philosophy (背景)

「何もチャレンジしないことは、毎月1000万円の罰金を払っているのと同じである」という概念に基づき開発されました。

人間は利益よりも損失を恐れる（損失回避性）生き物です。このアプリは、日々の「何もしなかった時間」を**PL（損益計算書）上の巨額赤字**として可視化することで、強制的にコンフォートゾーンからの脱却を促します。

## 🚀 Key Features (機能)

1. **Valuation (初期査定機能)**
* 年齢による「サンクコスト（埋没費用）」を自動償却。
* 過去の人生を変えるような挑戦（Big Win）を「資産」として評価し、スタート時の残存価値（Valuation）を算出します。


2. **Stateless WBS Management**
* 人生のマイルストーンをWBS（Work Breakdown Structure）形式で管理。
* サーバーレス・データベースレス。全てのデータはローカルのCSVファイルで管理され、ユーザーに完全なオーナーシップがあります。


3. **Strict PL Tracking (厳格な損益管理)**
* 毎月の行動結果に対し、以下の基準で容赦なく資産を増減させます。
* **Status Quo (現状維持):** `▲ 1,000万円` (罰金)
* **Challenge (挑戦):** `± 0円` (資産保全)
* **Big Win (大勝利):** `+ 5,000万円` (特別利益)



## 🛠 Tech Stack

* **Frontend/Backend:** Python (Streamlit)
* **Data Manipulation:** Pandas
* **Data Storage:** CSV (Client-side management)

## ⚡ Quick Start

エンジニアの方は、以下のコマンドで即座にローカル環境で起動できます。

```bash
# 1. Clone the repository
git clone https://github.com/your-username/life-wbs-manager.git
cd life-wbs-manager

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
streamlit run app.py

```

### Dependencies (`requirements.txt`)

```txt
streamlit>=1.28.0
pandas>=2.0.0

```

## 📊 Logic Definition (計算ロジック)

### 1. Initial Valuation (初期資産)

開始時点の資産は、以下の式で算出されます。

$$Current Asset = Initial(100億) - TimeCost + Goodwill$$

* **TimeCost (時間コスト):** `年齢 × 1.2億円`
* **Goodwill (のれん代/救済):** `過去の挑戦数 × 3.6億円` (※1回の挑戦で3年分の損失をカバー)

### 2. Monthly PL (月次損益)

毎月の判定日（月末）に、自己申告に基づき以下の処理が行われます。

| Action | Status | Impact | Description |
| --- | --- | --- | --- |
| **Status Quo** | 🔴 Lost | **-10,000,000 JPY** | 何も変化を起こさなかった代償。 |
| **Challenge** | 🟢 Kept | **±0 JPY** | 失敗しても良い。行動したことで資産は守られる。 |
| **Big Win** | 🔵 Profit | **+50,000,000 JPY** | 人生ステージが変わる成果。過去の損失を補填できる。 |

## 📂 Data Structure (CSV)

データは階層型WBS構造を持つCSVとして保存されます。

```csv
ID,Parent,Task,Status,PL,Memo
1,0,Project: My Life,In Progress,8400000000,Initial Val.
1.1,1,Past Cost (0-30yo),Lost,-3600000000,Sunk Cost
1.2,1,Due Diligence,Bonus,2000000000,Past Achievements
2,0,FY2026,In Progress,0,Current Year
2.1,2,2026-02 Action,Status Quo,-10000000,No output produced.

```

## 🗺 Roadmap

* [ ] **Visualizer:** 資産残高の推移グラフと「破産予測線」の描画
* [ ] **AI Auditor:** Google Gemini APIを用いた「その行動は本当に挑戦か？」の自動監査機能
* [ ] **Portfolio Export:** 実績（Win）のみを抽出した職務経歴書の自動生成

## 👤 Author

* **Yuto** (Engineer / Consultant)
* Specialized in: ERP/SAP, Web Development
* Focus: Maximizing personal valuation through continuous challenges.

## 📄 License

MIT License
