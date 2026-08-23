import streamlit as st
import pandas as pd

def render(df: pd.DataFrame) -> pd.DataFrame:
    """5項目フィルターとメイン一覧表示"""
    c_ec, c_title, c_cat, c_cond, c_type = st.columns([2, 3, 2, 2, 2])
    
    ec_col = "platform" if "platform" in df.columns else "出品先"
    title_col = "title" if "title" in df.columns else "商品名"
    cat_col = "category" if "category" in df.columns else ("カテゴリ" if "カテゴリ" in df.columns else None)
    cond_col = "condition" if "condition" in df.columns else ("コンディション" if "コンディション" in df.columns else None)
    type_col = "listing_type" if "listing_type" in df.columns else "販売形式"

    with c_ec:
        ec_list = ["全ECサイト"] + sorted(df[ec_col].dropna().unique().tolist()) if ec_col in df.columns else ["全ECサイト"]
        selected_ec = st.selectbox("ECサイト名", ec_list, label_visibility="collapsed", key="lst_ec_filter")
        
    with c_title:
        title_list = ["全商品名"] + sorted(df[title_col].dropna().unique().tolist()) if title_col in df.columns else ["全商品名"]
        selected_title = st.selectbox("商品名", title_list, label_visibility="collapsed", key="lst_title_filter")

    with c_cat:
        cat_list = ["全カテゴリ"] + sorted(df[cat_col].dropna().unique().tolist()) if (cat_col and cat_col in df.columns) else ["全カテゴリ"]
        selected_cat = st.selectbox("カテゴリ", cat_list, label_visibility="collapsed", key="lst_cat_filter")

    with c_cond:
        cond_list = ["全コンディション"] + sorted(df[cond_col].dropna().unique().tolist()) if (cond_col and cond_col in df.columns) else ["全コンディション"]
        selected_cond = st.selectbox("新旧品", cond_list, label_visibility="collapsed", key="lst_cond_filter")

    with c_type:
        type_list = ["全販売形式"] + sorted(df[type_col].dropna().unique().tolist()) if type_col in df.columns else ["全販売形式"]
        selected_type = st.selectbox("定価/オークション", type_list, label_visibility="collapsed", key="lst_type_filter")

    # フィルタリング処理
    filtered_df = df.copy()
    if selected_ec != "全ECサイト" and ec_col in filtered_df.columns:
        filtered_df = filtered_df[filtered_df[ec_col] == selected_ec]
    if selected_title != "全商品名" and title_col in filtered_df.columns:
        filtered_df = filtered_df[filtered_df[title_col] == selected_title]
    if selected_cat != "全カテゴリ" and cat_col and cat_col in filtered_df.columns:
        filtered_df = filtered_df[filtered_df[cat_col] == selected_cat]
    if selected_cond != "全コンディション" and cond_col and cond_col in filtered_df.columns:
        filtered_df = filtered_df[filtered_df[cond_col] == selected_cond]
    if selected_type != "全販売形式" and type_col in filtered_df.columns:
        filtered_df = filtered_df[filtered_df[type_col] == selected_type]

    # サマリー表示
    total_count = len(filtered_df)
    price_col = "buyout_price" if "buyout_price" in filtered_df.columns else ("start_price" if "start_price" in filtered_df.columns else "出品価格")
    total_price = pd.to_numeric(filtered_df[price_col], errors="coerce").fillna(0).astype(int).sum() if price_col in filtered_df.columns else 0

    st.markdown(f"**該当件数:** {total_count:,} 件 | **出品総額:** ¥{total_price:,}")
    
    st.dataframe(filtered_df, height=380, use_container_width=True, hide_index=True)
    return filtered_df