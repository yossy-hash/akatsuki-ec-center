import streamlit as st
import pandas as pd

def render(filtered_df: pd.DataFrame):
    """売上管理サマリー表示"""
    st.markdown("**【📊 売上管理サマリー】**")
    
    total_count = len(filtered_df)
    price_col = "buyout_price" if "buyout_price" in filtered_df.columns else ("start_price" if "start_price" in filtered_df.columns else "出品価格")
    total_price = pd.to_numeric(filtered_df[price_col], errors="coerce").fillna(0).astype(int).sum() if price_col in filtered_df.columns else 0
    
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("見込み売上総額", f"¥{total_price:,}")
    with col_s2:
        st.metric("確定取引件数", f"{total_count:,} 件")
    with col_s3:
        st.metric("平均販売単価", f"¥{int(total_price / total_count):,}" if total_count > 0 else "¥0")

    st.dataframe(filtered_df, height=180, use_container_width=True, hide_index=True)