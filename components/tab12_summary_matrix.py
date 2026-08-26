import streamlit as st
import pandas as pd
import re
from utils.gas_api import load_sheet_data

SHEET_TX = "T_Transactions"

def categorize_transaction(row):
    """取引データから 収入（給与/物販/投資）・経費・生活費 を判定分類"""
    src = str(row.get("source", ""))
    cat = str(row.get("category", ""))
    orig_name = str(row.get("original_name", ""))
    
    if "sales" in src or any(k in orig_name for k in ["売上", "メルカリ", "ヤフオク", "Amazon"]):
        return "1_収入", "物販売上"
    elif "給与" in cat or "給与" in orig_name:
        return "1_収入", "給与収入"
    elif any(k in cat or k in orig_name for k in ["投資", "配当", "利息", "暗号資産", "ビットコイン"]):
        return "1_収入", "投資・その他"
    elif cat in ["仕入高", "旅費交通費", "通信費", "接待交際費", "消耗品費", "会議費", "地代家賃", "広告宣伝費"] or "経費" in cat:
        return "2_事業経費", f"経費 ({cat})"
    else:
        return "3_生活費", f"生活費 ({cat if cat != '未分類' else 'その他・生活'})"

def render_tab12_summary_matrix():
    st.title("📊 月別・収支構造サマリー（損益・生活費マトリクス）")
    st.write("取り込んだデータを『収入（給与/物販/投資）』『事業経費』『生活費』に分類して月別に横断集計します。")

    df_tx = load_sheet_data(SHEET_TX)

    if df_tx.empty:
        st.info("データがまだありません。CSV取り込み画面から取引データを登録してください。")
        return

    df_tx["date_str"] = df_tx["date"].astype(str).str.strip()
    df_tx["month"] = df_tx["date_str"].str.slice(0, 7)
    df_tx["amount"] = pd.to_numeric(df_tx["amount"], errors="coerce").fillna(0)

    df_valid = df_tx[df_tx["month"].str.match(r"^\d{4}-\d{2}$")].copy()

    if df_valid.empty:
        st.warning("有効な日付フォーマット（YYYY-MM-DD）の取引データが見つかりませんでした。")
        return

    df_valid[["group", "sub_group"]] = df_valid.apply(categorize_transaction, axis=1, result_type="expand")

    pivot_df = pd.pivot_table(
        df_valid,
        index=["group", "sub_group"],
        columns="month",
        values="amount",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    st.subheader("📈 月別・項目別収支表")

    # 全体での最大値を計算（バーの最大スケール用）
    month_cols = [c for c in pivot_df.columns if c not in ["group", "sub_group"]]
    max_amount = int(pivot_df[month_cols].values.max()) if month_cols else 1000000

    # Streamlit標準のプログレスバー設定（崩れゼロ）
    column_config = {}
    for col in month_cols:
        column_config[col] = st.column_config.ProgressColumn(
            col,
            format="￥%d",
            min_value=0,
            max_value=max_amount
        )

    st.dataframe(
        pivot_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")
    
    st.subheader("📊 月別収支推移")
    summary_by_month = df_valid.groupby(["month", "group"])["amount"].sum().unstack(fill_value=0)
    st.bar_chart(summary_by_month)

    st.markdown("---")

    st.subheader("🏦 月末・銀行残高推移")

    def extract_balance(notes_str):
        match = re.search(r"残高:\s*￥?([0-9,]+)", str(notes_str))
        if match:
            return int(match.group(1).replace(",", ""))
        return None

    df_valid["extracted_balance"] = df_valid["notes"].apply(extract_balance)
    df_bank = df_valid[df_valid["extracted_balance"].notnull()].copy()

    if not df_bank.empty:
        df_bank = df_bank.sort_values("date_str")
        monthly_balance = df_bank.groupby("month")["extracted_balance"].last()

        col_b1, col_b2 = st.columns([1, 2])
        with col_b1:
            st.write("**月末残高一覧**")
            df_bal_show = pd.DataFrame(monthly_balance).rename(columns={"extracted_balance": "月末残高"}).reset_index()
            
            max_bal = int(df_bal_show["月末残高"].max()) if not df_bal_show.empty else 1000000
            st.dataframe(
                df_bal_show,
                column_config={
                    "月末残高": st.column_config.ProgressColumn("月末残高", format="￥%d", min_value=0, max_value=max_bal)
                },
                use_container_width=True,
                hide_index=True
            )
        
        with col_b2:
            st.write("**残高推移チャート**")
            st.line_chart(monthly_balance)
    else:
        st.info("💡 イオン銀行等の残高情報付きCSVを取り込むと、ここに月末残高の推移グラフが表示されます。")