import streamlit as st
import pandas as pd
from utils.gas_api import load_sheet_data

SHEET_TX = "T_Transactions"

def render_tab11_transactions():
    st.title("📑 整備済み取引データ一覧（仕訳帳）")
    st.write("取り込み・クレンジング済みの取引明細を閲覧・確認できます。")

    df_tx = load_sheet_data(SHEET_TX)

    if df_tx.empty:
        st.info("登録されている取引データはまだありません。CSV取り込み画面から登録してください。")
        return

    # 絞り込みフィルター
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 対象月絞り込み
        df_tx["month"] = df_tx["date"].astype(str).str.slice(0, 7)
        months = sorted(list(df_tx["month"].unique()), reverse=True)
        selected_month = st.selectbox("対象月で絞り込み", ["すべて"] + months)
        
    with col2:
        # データ種別絞り込み
        sources = sorted(list(df_tx["source"].unique()))
        selected_source = st.selectbox("データ種別で絞り込み", ["すべて"] + sources)

    with col3:
        # 勘定科目絞り込み
        categories = sorted(list(df_tx["category"].unique())) if "category" in df_tx.columns else []
        selected_cat = st.selectbox("勘定科目で絞り込み", ["すべて"] + categories)

    # フィルタリング処理
    df_filtered = df_tx.copy()
    if selected_month != "すべて":
        df_filtered = df_filtered[df_filtered["month"] == selected_month]
    if selected_source != "すべて":
        df_filtered = df_filtered[df_filtered["source"] == selected_source]
    if selected_cat != "すべて" and "category" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["category"] == selected_cat]

    st.markdown("---")

    # 集計サマリー表示
    total_count = len(df_filtered)
    total_amount = df_filtered["amount"].astype(int).sum() if "amount" in df_filtered.columns else 0

    m1, m2 = st.columns(2)
    m1.metric("表示中の取引件数", f"{total_count} 件")
    m2.metric("合計金額", f"￥{total_amount:,}")

    st.subheader("📋 取引明細データ")
    
    # 表示用カラムの選定
    disp_cols = ["date", "source", "original_name", "clean_name", "category", "amount", "notes"]
    available_cols = [c for c in disp_cols if c in df_filtered.columns]

    st.dataframe(
        df_filtered[available_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "date": "取引日",
            "source": "種別",
            "original_name": "変換前名称",
            "clean_name": "変換後名称",
            "category": "勘定科目",
            "amount": st.column_config.NumberColumn("金額(円)", format="￥%d"),
            "notes": "備考"
        }
    )