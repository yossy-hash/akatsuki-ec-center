import streamlit as st
import pandas as pd

def render(df: pd.DataFrame):
    """SOLD 発送前アイテムの表示"""
    st.markdown("**【📦 SOLD 発送前アイテム一覧】**")
    status_target = "status" if "status" in df.columns else ("ステータス" if "ステータス" in df.columns else None)
    
    if status_target:
        sold_df = df[df[status_target].astype(str).str.contains("発送前|未発送|SOLD", na=False)]
    else:
        sold_df = pd.DataFrame()

    if not sold_df.empty:
        st.dataframe(sold_df, height=200, use_container_width=True, hide_index=True)
    else:
        st.info("現在、発送待ちのSOLD商品はありません。")