# app.py
import streamlit as st
from utils.gas_api import load_sheet_data
from components.tab1_inventory import render_tab1_inventory
from components.tab2_master import render_tab2_master
from components.tab3_listing import render_tab3_listing
from components.tab4_sourcing import render_tab4_sourcing

st.set_page_config(
    page_title="AKATSUKI 統合ECコマンドセンター",
    page_icon="📦",
    layout="wide"
)

st.markdown("""
    <head><meta name="google" content="notranslate"></head>
    <style>html, body, [data-testid="stAppViewContainer"] { translate: no !important; }</style>
""", unsafe_allow_html=True)

st.title("📦 AKATSUKI 統合ECコマンドセンター")

try:
    df_raw_inventory = load_sheet_data("EC_Inventory")
    df_listing = load_sheet_data("T_Listing")
    df_purchase = load_sheet_data("T_Purchase")
    df_item = load_sheet_data("M_Item")
    df_sourcing = load_sheet_data("T_Sourcing")

    raw_inventory_list = df_raw_inventory.to_dict(orient="records") if not df_raw_inventory.empty else []
    total_raw_cnt = len(raw_inventory_list)
    stock_hold_cnt = len([r for r in raw_inventory_list if str(r.get('数量', r.get('quantity', 1))).strip() not in ["0", ""]])
    active_listing_cnt = len(df_listing[df_listing["listing_status"] == "出品中"]) if not df_listing.empty and "listing_status" in df_listing.columns else len(df_listing)
    sourcing_cnt = len(df_sourcing) if not df_sourcing.empty else len(df_purchase)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("📦 総登録データ数", f"{total_raw_cnt} 件")
    col_m2.metric("📦 在庫保持アイテム", f"{stock_hold_cnt} 件")
    col_m3.metric("🚀 アクティブ出品数", f"{active_listing_cnt} 件")
    col_m4.metric("🎯 仕入リサーチ候補", f"{sourcing_cnt} 件")

    st.divider()

    tab_pur, tab_stock, tab_site_list, tab_sourcing = st.tabs([
        "📦 リアルタイム在庫一覧 ＆ 仕入金額推移",
        "📊 商品マスター ＆ Keepa分析",
        "🏢 サイト別 出品リスト ＆ 模擬プレビュー",
        "🎯 仕入・リサーチ候補"
    ])

    with tab_pur:
        render_tab1_inventory(df_raw_inventory)

    with tab_stock:
        render_tab2_master(df_item, df_raw_inventory)

    with tab_site_list:
        render_tab3_listing(df_listing)

    with tab_sourcing:
        render_tab4_sourcing(df_sourcing, df_purchase)

except Exception as e:
    st.error(f"システムエラーが発生しました: {e}")