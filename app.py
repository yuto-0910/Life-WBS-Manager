"""
Life WBS Manager
「平均的に過ごすことは、毎月1000万円の罰金である」

人生を100億円の巨大プロジェクトと定義し、
現状維持による「機会損失」を金融的負債として可視化する行動喚起型予実管理ツール。
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# ========================================
# 固定パラメータ（ハードコード値：変更禁止）
# ========================================
INITIAL_CAPITAL = 10_000_000_000   # 初期資本: 100億円
DEPRECIATION_RATE = 120_000_000    # 年間機会損失: 1.2億円/年
GOODWILL_RATE = 360_000_000        # のれん代: 3.6億円/回

PL_STATUS_QUO = -10_000_000        # 現状維持: ▲1,000万円
PL_CHALLENGE = 0                   # 挑戦: ±0円
PL_BIG_WIN = 50_000_000            # 大勝利: +5,000万円

# ステータス内部ID → PL値マッピング
STATUS_PL_MAP = {
    "Status Quo": PL_STATUS_QUO,
    "Challenge": PL_CHALLENGE,
    "Big Win": PL_BIG_WIN,
}

# UI表示用ラベル → 内部ステータスID
STATUS_LABELS = {
    "現状維持 (罰金)": "Status Quo",
    "挑戦 (維持)": "Challenge",
    "大勝利 (資産増)": "Big Win",
}

# CSV必須カラム
REQUIRED_COLUMNS = ["ID", "Parent", "Task", "Status", "PL", "Memo"]


# ========================================
# ユーティリティ関数
# ========================================
def format_yen(amount: int) -> str:
    """金額を¥カンマ区切り表記にフォーマット"""
    amount = int(amount)
    if amount >= 0:
        return f"¥{amount:,}"
    else:
        return f"▲¥{abs(amount):,}"


def format_yen_readable(amount: int) -> str:
    """金額を億/万円単位の日本語読みやすい表記にフォーマット"""
    amount = int(amount)
    abs_val = abs(amount)
    prefix = "▲" if amount < 0 else ""

    if abs_val >= 100_000_000:  # 1億以上
        oku = abs_val // 100_000_000
        remainder = abs_val % 100_000_000
        man = remainder // 10_000
        if man > 0:
            return f"{prefix}{oku}億{man:,}万円"
        return f"{prefix}{oku}億円"
    elif abs_val >= 10_000:  # 1万以上
        man = abs_val // 10_000
        return f"{prefix}{man:,}万円"
    elif abs_val > 0:
        return f"{prefix}{abs_val:,}円"
    else:
        return "±0円"


def calculate_valuation(age: int, wins: int) -> dict:
    """
    初期資産評価ロジック
    計算式: 現在資産 = 初期資本(100億) - 時間コスト(年齢×1.2億) + のれん代(挑戦数×3.6億)
    ※のれん代の上限は時間コストまで（初期資本100億を超えない）
    """
    depreciation = age * DEPRECIATION_RATE
    raw_goodwill = wins * GOODWILL_RATE
    goodwill = min(raw_goodwill, depreciation)  # 上限キャップ
    initial_asset = INITIAL_CAPITAL - depreciation + goodwill

    return {
        "depreciation": depreciation,
        "goodwill": goodwill,
        "initial_asset": initial_asset,
    }


def generate_initial_wbs(
    age: int, wins: int, valuation: dict, win_details: list[str] = None
) -> pd.DataFrame:
    """
    初期WBS行（Genesis Row）を生成
    - Row 1: ルートプロジェクト（基本資本100億円）
    - Row 1.1: 過去の時間コスト（マイナス）
    - Row 1.2: のれん代サマリー（プラス）※挑戦回数 > 0 の場合のみ
    - Row 1.2.x: 各挑戦の詳細行（PL=0、内訳表示用）
    - Row 2: 現年度フェーズ（月次アクションの親）
    """
    year = datetime.now().year

    rows = [
        {
            "ID": "1",
            "Parent": "0",
            "Task": "プロジェクト：人生",
            "Status": "In Progress",
            "PL": INITIAL_CAPITAL,
            "Memo": "初期資本 100億円",
        },
        {
            "ID": "1.1",
            "Parent": "1",
            "Task": f"過去コスト（0〜{age}歳）",
            "Status": "Lost",
            "PL": -valuation["depreciation"],
            "Memo": f"年齢{age} × 1.2億円",
        },
    ]

    # のれん代は挑戦回数が1以上の場合のみ計上
    if wins > 0:
        rows.append({
            "ID": "1.2",
            "Parent": "1",
            "Task": "デューデリジェンス（過去の実績）",
            "Status": "Bonus",
            "PL": valuation["goodwill"],
            "Memo": f"{wins}回の挑戦 × 3.6億円",
        })

        # 各挑戦の詳細行（内訳表示用、PL=0で合計に影響しない）
        if win_details:
            for i, detail in enumerate(win_details, start=1):
                rows.append({
                    "ID": f"1.2.{i}",
                    "Parent": "1.2",
                    "Task": detail,
                    "Status": "Bonus",
                    "PL": 0,
                    "Memo": f"挑戦 #{i}",
                })

    # 現年度フェーズ（月次アクションの格納先）
    rows.append({
        "ID": "2",
        "Parent": "0",
        "Task": f"FY{year}",
        "Status": "In Progress",
        "PL": 0,
        "Memo": "現年度",
    })

    df = pd.DataFrame(rows)
    df["PL"] = df["PL"].astype(int)
    return df


def sort_wbs(df: pd.DataFrame) -> pd.DataFrame:
    """WBS IDの階層順（1, 1.1, 1.2, 2, 2.1, ...）でDataFrameをソート"""
    df = df.copy()
    df["_sort_key"] = df["ID"].apply(
        lambda x: tuple(int(n) for n in x.split("."))
    )
    df = df.sort_values("_sort_key").drop(columns="_sort_key").reset_index(drop=True)
    return df


def get_next_action_id(df: pd.DataFrame, parent_id: str) -> str:
    """
    次のアクションIDを自動採番
    親ID配下の子タスク数をカウントし、ParentID.連番 を返す
    """
    children = df[df["Parent"] == parent_id]
    next_num = len(children) + 1
    return f"{parent_id}.{next_num}"


def get_phase_ids(df: pd.DataFrame) -> list[str]:
    """年度フェーズ（Parent="0" かつ ID≠"1"）のID一覧を返す"""
    phases = df[(df["Parent"] == "0") & (df["ID"] != "1")]
    return phases["ID"].tolist()


def find_or_create_year_phase(df: pd.DataFrame, year: int) -> tuple:
    """
    指定された年のフェーズ行を探す。なければ新規作成してDataFrameに追加する。
    戻り値: (更新後のDataFrame, 該当フェーズのID)
    """
    phase_name = f"FY{year}"

    # 既存フェーズからタスク名で検索
    match = df[df["Task"] == phase_name]
    if not match.empty:
        return df, match.iloc[0]["ID"]

    # 新規フェーズID = 既存のルート直下IDの最大値 + 1
    root_children = df[df["Parent"] == "0"]
    max_id = max(int(row["ID"]) for _, row in root_children.iterrows())
    new_phase_id = str(max_id + 1)

    new_phase = pd.DataFrame([{
        "ID": new_phase_id,
        "Parent": "0",
        "Task": phase_name,
        "Status": "In Progress",
        "PL": 0,
        "Memo": f"{year}年度",
    }])
    df = pd.concat([df, new_phase], ignore_index=True)
    df["PL"] = df["PL"].astype(int)
    df = sort_wbs(df)

    return df, new_phase_id


def calculate_kpis(df: pd.DataFrame) -> dict:
    """
    KPI（主要業績指標）を計算
    - 現在資産: 全行のPL合計
    - 累計損失: PLがマイナスの行の合計（絶対値表示用）
    - アクション数: 全年度フェーズ配下の子タスク数
    """
    current_asset = int(df["PL"].sum())
    total_loss = int(df[df["PL"] < 0]["PL"].sum())
    # 全年度フェーズ配下のアクション数を合計
    phase_ids = get_phase_ids(df)
    action_count = len(df[df["Parent"].isin(phase_ids)])

    return {
        "current_asset": current_asset,
        "total_loss": total_loss,
        "action_count": action_count,
    }


def validate_csv(df: pd.DataFrame) -> tuple:
    """アップロードされたCSVの必須カラム検証"""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        return False, f"必須カラムが不足しています: {', '.join(missing)}"
    return True, ""


# ========================================
# Streamlit ページ設定
# ========================================
st.set_page_config(
    page_title="Life WBS Manager",
    page_icon="📊",
    layout="wide",
    menu_items={
        "Get help": None,
        "Report a Bug": None,
        "About": (
            "### Life WBS Manager\n"
            "「平均的に過ごすことは、毎月1000万円の罰金である」\n\n"
            "人生を100億円の巨大プロジェクトと定義し、"
            "現状維持による機会損失を可視化する行動喚起型予実管理ツール。"
        ),
    },
)

# ========================================
# セッションステート初期化
# ========================================
if "wbs_data" not in st.session_state:
    st.session_state.wbs_data = None


# ========================================
# サイドバー
# ========================================
with st.sidebar:
    if st.button("Life WBS Manager", type="tertiary", use_container_width=True):
        st.session_state.wbs_data = None
        st.rerun()
    st.caption("「平均的に過ごすことは、毎月1000万円の罰金である」")
    st.divider()

    if st.session_state.wbs_data is not None:
        # --- データ管理セクション ---
        st.subheader("データ管理")

        # CSVダウンロード
        csv_bytes = st.session_state.wbs_data.to_csv(
            index=False
        ).encode("utf-8")
        today_str = datetime.now().strftime("%Y%m%d")
        st.download_button(
            label="CSVをダウンロード",
            data=csv_bytes,
            file_name=f"life_wbs_{today_str}.csv",
            mime="text/csv",
        )

        st.divider()

        # データリセット
        if st.button("データをリセット"):
            st.session_state.wbs_data = None
            st.rerun()

    else:
        st.info("プロジェクトを作成するか、CSVを読み込んでください。")


# ========================================
# メイン画面
# ========================================

if st.session_state.wbs_data is None:
    # ============================================================
    # 初期化画面（オンボーディング）
    # ============================================================
    st.title("Life WBS Manager")
    st.markdown(
        "人生を **100億円** の巨大プロジェクトと定義し、"
        "現状維持による「機会損失」を金融的負債として可視化します。"
    )
    st.divider()

    tab_new, tab_csv = st.tabs(["新規プロジェクト作成", "CSVから読込"])

    # --- 新規プロジェクト作成 ---
    with tab_new:
        st.subheader("初期資産評価（バリュエーション）")
        st.info(
            "**計算式:** 現在資産 = 初期資本(100億) "
            "− 時間コスト(年齢 × 1.2億) "
            "+ のれん代(挑戦数 × 3.6億)"
        )

        # Step 1: 基本情報（フォーム外で動的UI更新を可能にする）
        col_age, col_wins = st.columns(2)

        with col_age:
            age = st.number_input(
                "現在の年齢",
                min_value=1,
                max_value=120,
                value=30,
                step=1,
            )
        with col_wins:
            wins = st.number_input(
                "過去の大きな挑戦の回数",
                min_value=0,
                max_value=100,
                value=0,
                step=1,
                help="転職・起業・海外移住・受賞など、人生のステージが変わった回数",
            )

        # Step 2: 挑戦の詳細入力（回数に応じて動的に入力欄を表示）
        win_details = []
        if wins > 0:
            st.markdown("---")
            st.markdown("**過去の挑戦の内容を記入してください**")
            for i in range(1, wins + 1):
                detail = st.text_input(
                    f"挑戦 #{i}",
                    placeholder="例: 海外転職、起業、資格取得など",
                    key=f"win_detail_{i}",
                )
                win_details.append(detail)

        # 査定プレビュー
        preview_val = calculate_valuation(age, wins)
        st.markdown("---")
        st.markdown("**査定プレビュー**")
        pc1, pc2, pc3 = st.columns(3)
        pc1.metric("時間コスト", format_yen_readable(preview_val["depreciation"]))
        pc2.metric("のれん代", format_yen_readable(preview_val["goodwill"]))
        pc3.metric("開始資産", format_yen_readable(preview_val["initial_asset"]))

        # 開始ボタン
        if st.button("プロジェクトを開始する", type="primary"):
            # 未入力の挑戦は「挑戦 #N」をデフォルト名にする
            filled_details = []
            for i, d in enumerate(win_details, start=1):
                filled_details.append(d.strip() if d and d.strip() else f"挑戦 #{i}")

            valuation = calculate_valuation(age, wins)
            df = generate_initial_wbs(age, wins, valuation, filled_details)
            st.session_state.wbs_data = df
            st.rerun()

    # --- CSV読込 ---
    with tab_csv:
        st.subheader("既存データの読込")
        st.markdown("過去にエクスポートしたCSVファイルをアップロードしてください。")

        uploaded = st.file_uploader("CSVファイルを選択", type=["csv"])

        if uploaded is not None:
            try:
                df = pd.read_csv(
                    uploaded,
                    encoding="utf-8",
                    dtype={"ID": str, "Parent": str},
                )
                is_valid, error_msg = validate_csv(df)

                if is_valid:
                    df["PL"] = df["PL"].astype(int)
                    st.session_state.wbs_data = df
                    st.success("CSVの読込に成功しました。")
                    st.rerun()
                else:
                    st.error(error_msg)
            except Exception as e:
                st.error(f"CSV読込エラー: {e}")

else:
    # ============================================================
    # ダッシュボード（メインループ）
    # ============================================================
    df = st.session_state.wbs_data
    kpis = calculate_kpis(df)

    # --- 残り人生ゲージ ---
    asset = kpis["current_asset"]
    pct = max(0, min(100, asset / INITIAL_CAPITAL * 100))

    # 残高に応じたゲージ色
    if asset < 0:
        bar_color = "#FF0000"
        status_text = "破産"
    elif asset < 3_000_000_000:
        bar_color = "#FF4B4B"
        status_text = "危険水域"
    elif asset < 5_000_000_000:
        bar_color = "#FFA500"
        status_text = "注意"
    else:
        bar_color = "#00CC66"
        status_text = "健全"

    st.markdown(
        f"""
        <div style="margin-bottom:4px; display:flex; justify-content:space-between; font-size:14px;">
            <span>残り人生資産 — <b>{status_text}</b></span>
            <span><b>{format_yen_readable(asset)}</b> / {format_yen_readable(INITIAL_CAPITAL)}</span>
        </div>
        <div style="background:#333; border-radius:8px; height:28px; width:100%; overflow:hidden;">
            <div style="background:{bar_color}; width:{pct:.1f}%; height:100%; border-radius:8px;
                        display:flex; align-items:center; justify-content:center;
                        color:#fff; font-weight:bold; font-size:13px; min-width:40px;">
                {pct:.0f}%
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")  # スペーサー

    # --- アラート判定 ---
    if asset < 0:
        st.error(
            "🚨 **破産（Bankruptcy）** — "
            "資産残高がマイナスに転落しました。直ちに行動を変えてください。"
        )
    elif asset < 3_000_000_000:
        st.warning(
            "⚠️ **危険水域（Critical）** — "
            "資産残高が30億円を下回りました。猶予はわずかです。"
        )

    # --- KPI 表示 ---
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("現在資産", format_yen_readable(kpis["current_asset"]))
    kpi2.metric("累計損失額", format_yen_readable(abs(kpis["total_loss"])))
    kpi3.metric("記録アクション数", f"{kpis['action_count']} 件")

    st.divider()

    # --- 月次アクション記録フォーム ---
    st.subheader("月次アクション記録")

    # 年度フェーズの存在確認（ID≠"1"でParent="0"のフェーズが1つ以上あること）
    if get_phase_ids(df):

        with st.form("action_form", clear_on_submit=True):
            form_c1, form_c2 = st.columns(2)

            with form_c1:
                action_date = st.date_input(
                    "対象年月",
                    value=datetime.now(),
                )
                task_name = st.text_input(
                    "タスク名（何をしたか / しなかったか）",
                    placeholder="例: 副業プロジェクトを立ち上げた",
                )

            with form_c2:
                status_label = st.selectbox(
                    "ステータス",
                    options=list(STATUS_LABELS.keys()),
                )
                memo = st.text_input(
                    "備考（任意）",
                    placeholder="成果物URL、振り返りメモなど",
                )

            # ステータス別PL一覧を常時表示
            st.markdown(
                "| ステータス | 損益影響 | 判定基準 |\n"
                "|:---|:---|:---|\n"
                "| 現状維持 (罰金) | **▲1,000万円** | 新しいアウトプットなし |\n"
                "| 挑戦 (維持) | **±0円** | アウトプットあり（失敗OK） |\n"
                "| 大勝利 (資産増) | **+5,000万円** | 人生を変える成果 |"
            )

            record_btn = st.form_submit_button("記録する", type="primary")

        # フォーム送信時の処理（フォーム外で実行）
        if record_btn:
            if not task_name or not task_name.strip():
                st.error("タスク名を入力してください。")
            else:
                # PL値の決定
                selected_status = STATUS_LABELS[status_label]
                pl_value = STATUS_PL_MAP[selected_status]

                # 対象年度のフェーズを取得（なければ自動作成）
                action_year = action_date.year
                df, phase_id = find_or_create_year_phase(df, action_year)

                # ID採番（該当年度フェーズ配下）
                new_id = get_next_action_id(df, phase_id)
                date_str = action_date.strftime("%Y-%m")

                # 新規行の作成
                new_row = pd.DataFrame([{
                    "ID": new_id,
                    "Parent": phase_id,
                    "Task": f"{date_str} {task_name.strip()}",
                    "Status": selected_status,
                    "PL": pl_value,
                    "Memo": memo if memo else "",
                }])

                # DataFrameに追加・ソートしてセッション更新
                updated = pd.concat([df, new_row], ignore_index=True)
                updated["PL"] = updated["PL"].astype(int)
                st.session_state.wbs_data = sort_wbs(updated)
                st.rerun()

    else:
        st.warning(
            "年度フェーズが見つかりません。"
            "CSVデータにFY行（Parent=0）が含まれていることを確認してください。"
        )

    st.divider()

    # --- WBS台帳 ---
    st.subheader("WBS台帳")

    # 表示用DataFrameの作成
    display_df = df.copy()

    # WBS階層に応じたインデント
    display_df["タスク"] = display_df.apply(
        lambda row: "　" * row["ID"].count(".") + row["Task"],
        axis=1,
    )

    # ステータス日本語表示
    status_display_map = {
        "Status Quo": "🔴 現状維持",
        "Challenge": "🟢 挑戦",
        "Big Win": "🔵 大勝利",
        "In Progress": "⚪ 進行中",
        "Lost": "🔴 損失計上",
        "Bonus": "🔵 資産計上",
    }
    display_df["ステータス"] = (
        display_df["Status"]
        .map(status_display_map)
        .fillna(display_df["Status"])
    )

    # 損益額フォーマット
    display_df["損益額"] = display_df["PL"].apply(format_yen)

    # テーブル表示
    st.dataframe(
        display_df[["ID", "タスク", "ステータス", "損益額", "Memo"]].rename(
            columns={"ID": "WBS ID", "Memo": "備考"}
        ),
        use_container_width=True,
        hide_index=True,
    )

    # --- 既存行の編集 ---
    # 編集対象: 全年度フェーズ配下のアクション行
    phase_ids = get_phase_ids(df)
    action_rows = df[df["Parent"].isin(phase_ids)]

    if not action_rows.empty:
        st.divider()
        st.subheader("既存アクションの編集")

        # 内部ステータスID → UI表示ラベルの逆引き
        STATUS_LABELS_REV = {v: k for k, v in STATUS_LABELS.items()}

        # 編集対象の選択肢を作成
        edit_options = {
            f"{row['ID']} | {row['Task']}": idx
            for idx, row in action_rows.iterrows()
        }
        selected_label = st.selectbox(
            "編集する行を選択",
            options=list(edit_options.keys()),
        )
        selected_idx = edit_options[selected_label]
        selected_row = df.loc[selected_idx]

        with st.form("edit_form"):
            ec1, ec2 = st.columns(2)

            with ec1:
                edit_task = st.text_input(
                    "タスク名",
                    value=selected_row["Task"],
                )
            with ec2:
                # 現在のステータスをデフォルト選択にする
                current_label = STATUS_LABELS_REV.get(
                    selected_row["Status"], list(STATUS_LABELS.keys())[0]
                )
                label_list = list(STATUS_LABELS.keys())
                edit_status = st.selectbox(
                    "ステータス",
                    options=label_list,
                    index=label_list.index(current_label),
                )

            edit_memo = st.text_input(
                "備考",
                value=selected_row["Memo"] if pd.notna(selected_row["Memo"]) else "",
            )

            ec_btn1, ec_btn2 = st.columns(2)
            with ec_btn1:
                save_btn = st.form_submit_button("保存する", type="primary")
            with ec_btn2:
                delete_btn = st.form_submit_button("この行を削除する")

        if save_btn:
            if not edit_task or not edit_task.strip():
                st.error("タスク名を入力してください。")
            else:
                new_status = STATUS_LABELS[edit_status]
                new_pl = STATUS_PL_MAP[new_status]
                st.session_state.wbs_data.at[selected_idx, "Task"] = edit_task.strip()
                st.session_state.wbs_data.at[selected_idx, "Status"] = new_status
                st.session_state.wbs_data.at[selected_idx, "PL"] = new_pl
                st.session_state.wbs_data.at[selected_idx, "Memo"] = edit_memo
                st.rerun()

        if delete_btn:
            st.session_state.wbs_data = sort_wbs(df.drop(index=selected_idx))
            st.rerun()
