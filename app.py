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

# 1行目メニューの文字拡大 ＆ 上部余白調整CSS
st.markdown("""
    <head><meta name="google" content="notranslate"></head>
    <style>
        html, body, [data-testid="stAppViewContainer"] { translate: no !important; }
        .block-container { padding-top: 3.5rem !important; padding-bottom: 0rem !important; }
        
        /* 1行目メニュー（タブ）：フォントサイズ1.8remへ巨大化 */
        button[data-baseweb="tab"] p {
            font-size: 1.8rem !important;
            font-weight: 900 !important;
            line-height: 1.2 !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px !important;
            border-bottom: 3px solid #555 !important;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 8px 16px !important;
        }
    </style>
""", unsafe_allow_html=True)

try:
    # データ読み込み
    df_raw_inventory = load_sheet_data("EC_Inventory")
    df_listing = load_sheet_data("T_Listing")
    df_purchase = load_sheet_data("T_Purchase")
    df_item = load_sheet_data("M_Item")
    df_sourcing = load_sheet_data("T_Sourcing")

    # 1行目：指定の5大メニュー
    tab_sourcing, tab_stock, tab_listing, tab_shipping, tab_finance = st.tabs([
        "🎯 リサーチ・仕入れ",
        "📦 在庫",
        "🚀 出品状況",
        "🚚 出荷状況",
        "💰 資金管理"
    ])

    # 1. リサーチ・仕入れ
    with tab_sourcing:
        render_tab4_sourcing(df_sourcing, df_purchase)

    # 2. 在庫（コンポーネントを正しく呼び出し）
    with tab_stock:
        render_tab1_inventory(df_raw_inventory)

    # 3. 出品状況
    with tab_listing:
        render_tab3_listing(df_listing)

    # 4. 出荷状況
    with tab_shipping:
        st.info("🚚 【出荷状況】モジュール準備中（発送ステータス管理・梱包リストを接続予定）")

    # 5. 資金管理
    with tab_finance:
        render_tab2_master(df_item, df_raw_inventory)

except Exception as e:
    st.error(f"システムエラーが発生しました: {e}")