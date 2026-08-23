# components/tab3_listing.py
import streamlit as st

def render_tab3_listing(df_listing):
    st.subheader("🏢 モール別 出品一覧（T_Listing 連動）")
    if not df_listing.empty:
        st.dataframe(df_listing, use_container_width=True, height=400, hide_index=True)
    else:
        st.info("💡 出品データがありません。")