import streamlit as st
import pandas as pd
from utils.gas_api import load_sheet_data

SHEET_TX = "T_Transactions"

def categorize_transaction(row):
    """取引データから 収入（給与/物販/投資）・経費・生活費 を判定分類"""
    src = str(row.get("source", ""))
    cat = str(row.get("category", ""))
    orig_name = str(row.get("original_name", ""))
    
    # 1. 収入判定
    if "sales" in src or any(k in orig_name for k in ["売上", "メルカリ", "ヤフオク", "Amazon"]):
        return "1_収入", "物販売上"
    elif "給与" in cat or "給与" in orig_name:
        return "1_収入", "給与収入"
    elif any(k in cat or k in orig_name for k in ["投資", "配当", "利息", "暗号資産", "ビットコイン"]):
        return "1_収入", "投資・その他"
    
    # 2. 事業経費判定
    elif cat in ["仕入高", "旅費交通費", "通信費", "接待交際費", "消耗品費", "会議費", "地代家賃", "広告宣伝費"] or "経費" in cat:
        return "2_事業経費", f"経費 ({cat})"
    
    # 3. プライベート生活費判定
    else:
        return "3_生活費", f"生活費 ({cat if cat != '未分類' else 'その他・生活'})"

def render_tab12_summary_matrix():
    st.title("📊 月別・収支構造サマリー（損益・生活費マトリクス）")
    st.write("取り込んだデータを『収入（給与/物販/投資）』『事業経費』『生活費』に分類して月別に横断集計します。")

    df_tx = load_sheet_data(SHEET_TX)

    if df_tx.empty:
        st.info("データがまだありません。CSV取り込み画面から取引データを登録してください。")
        return

    # 日付から YYYY-MM を作成
    df_tx["month"] = df_tx["date"].astype(str).str.slice(0, 7)
    df_tx["amount"] = pd.to_numeric(df_tx["amount"], errors="coerce").fillna(0)

    # 取引の分類を付与
    df_tx[["group", "sub_group"]] = df_tx.apply(categorize_transaction, axis=1, result_type="expand")

    # ピボットテーブル集計 (縦軸: グループ/サブグループ, 横軸: 月)
    pivot_df = pd.pivot_table(
        df_tx,
        index=["group", "sub_group"],
        columns="month",
        values="amount",
        aggfunc="sum",
        fill_value=0
    )

    st.subheader("📈 月別・項目別収支表")
    
    # カラム名を綺麗にフォーマット
    st.dataframe(
        pivot_df.style.format("￥{:,.0f}"),
        use_container_width=True
    )

    st.markdown("---")
    
    # 月別の合計サマリーグラフ表示
    st.subheader("📊 月別収支推移")
    summary_by_month = df_tx.groupby(["month", "group"])["amount"].sum().unstack(fill_value=0)
    st.bar_chart(summary_by_month)