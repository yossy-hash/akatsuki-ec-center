import streamlit as st
import pandas as pd

def render(df: pd.DataFrame):
    """SOLD 発送完了アイテムの表示"""
    st.markdown("**【✅ SOLD 発送完了アイテム履歴】**")
    status_target = "status" if "status" in df.columns else ("ステータス" if "ステータス" in df.columns else None)
    
    if status_target:
        completed_df = df[df[status_target].astype(str).str.contains("完了|発送済|済", na=False)]
    else:
        completed_df = pd.DataFrame()

    if not completed_df.empty:
        st.dataframe(completed_df, height=200, use_container_width=True, hide_index=True)
    else:
        st.info("発送完了済みのデータはありません。")