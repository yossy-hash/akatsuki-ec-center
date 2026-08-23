# components/tab4_sourcing.py
import streamlit as st

def render_tab4_sourcing(df_sourcing, df_purchase):
    st.subheader("🎯 価格差・電脳仕入れリサーチ候補（T_Sourcing / T_Purchase）")
    df_disp_sourcing = df_sourcing if not df_sourcing.empty else df_purchase
    if not df_disp_sourcing.empty:
        st.dataframe(df_disp_sourcing, use_container_width=True, height=400, hide_index=True)
    else:
        st.info("💡 仕入候補データがありません。")