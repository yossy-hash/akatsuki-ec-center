import streamlit as st
import pandas as pd
from utils.gas_api import load_sheet_data
from components.tab1_inventory import render_tab1_inventory
from components.tab3_listing import render_tab3_listing
from components import tab2_master, tab4_sourcing, tab5_doc_generator
from components.listing import sub_sold_pending, sub_sold_shipped, sub_sales_mgmt
from components.tab8_import_matrix import render_tab8_import_matrix
from components.tab9_csv_importer import render_tab9_csv_importer
from components.tab10_rules import render_tab10_rules
from components.tab11_transactions import render_tab11_transactions
from components.tab12_summary_matrix import render_tab12_summary_matrix

st.set_page_config(page_title="AKATSUKI 統合ECコマンドセンター", layout="wide")

# --- UI/UX CSS ---
st.markdown("""
<style>
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .header-title {
        font-size: 1.15rem;
        font-weight: bold;
        line-height: 1.4;
        margin: 0;
        padding: 0;
    }
    section[data-testid="stSidebar"] {
        background-color: #1a1c23 !important;
    }
    .sidebar-brand {
        font-size: 1.3rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        letter-spacing: 1px;
        margin-bottom: 1.2rem;
        padding-left: 0.2rem;
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 0.5rem;
    }
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100% !important;
        height: 3.5rem !important;
        background: #252836 !important;
        border: 1px solid #363b4e !important;
        border-radius: 8px !important;
        color: #c5c9d6 !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        text-align: left !important;
        padding-left: 1rem !important;
        margin-bottom: 0.3rem !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
    }
    section[data-testid="stSidebar"] div.stButton > button:hover {
        background: #2d3245 !important;
        border-color: #60a5fa !important;
        color: #ffffff !important;
        transform: translateY(-2px) !important;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        border-color: #60a5fa !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

if "current_tab" not in st.session_state:
    st.session_state["current_tab"] = "📦 在庫管理"

st.sidebar.markdown('<div class="sidebar-brand">⚡ AKATSUKI 統合EC</div>', unsafe_allow_html=True)

NAV_ITEMS = [
    ("🔍 リサーチ・仕入れ", "tab_sourcing"),
    ("📦 在庫管理", "tab_inventory"),
    ("📄 出品Docs作成", "tab_doc_gen"),
    ("🚀 出品状況", "tab_listing"),
    ("📦 SOLD 発送前", "tab_sold_pending"),
    ("✅ SOLD 発送完了", "tab_sold_shipped"),
    ("📊 売上管理", "tab_sales_mgmt"),
    ("💰 資金管理", "tab_master"),
    ("📋 取り込み進捗（星取り表）", "tab_import_matrix"),
    ("📥 CSV一括取り込み", "tab_csv_importer"),
    ("📑 整備済み取引データ", "tab_transactions"),
    ("📊 月別収支サマリー", "tab_summary_matrix"),
    ("⚙️ 名寄せルール設定", "tab_rules")
]

for label, key_id in NAV_ITEMS:
    is_selected = (st.session_state["current_tab"] == label)
    btn_type = "primary" if is_selected else "secondary"
    
    if st.sidebar.button(label, key=f"nav_btn_{key_id}", type=btn_type, use_container_width=True):
        st.session_state["current_tab"] = label
        st.rerun()

selected_tab = st.session_state["current_tab"]

# 🔍 状況把握用デバッグ表示（展開して確認可能）
with st.expander("🛠️ データ読み込み診断モニター（状況把握用）", expanded=False):
    st.write(f"**現在の選択タブ**: `{selected_tab}`")

# ルーティング切替
if selected_tab == "🔍 リサーチ・仕入れ":
    if hasattr(tab4_sourcing, "render"):
        tab4_sourcing.render()

elif selected_tab == "📦 在庫管理":
    target_sheet = "EC_Inventory"
    df_raw_inventory = load_sheet_data(target_sheet)
    
    # 診断ログの表示
    st.caption(f"🔍 参照シート: `{target_sheet}` | 取得件数: {len(df_raw_inventory)} 行 | 取得列: {list(df_raw_inventory.columns)}")
    
    render_tab1_inventory(df_raw_inventory)

elif selected_tab == "📄 出品Docs作成":
    df_raw_inventory = load_sheet_data("EC_Inventory")
    tab5_doc_generator.render(df_raw_inventory)

elif selected_tab == "🚀 出品状況":
    df_raw_listing = load_sheet_data("T_Listing")
    render_tab3_listing(df_raw_listing)

elif selected_tab == "📦 SOLD 発送前":
    df_raw_listing = load_sheet_data("T_Listing")
    st.markdown('<p class="header-title">📦 SOLD 発送前コントロール</p>', unsafe_allow_html=True)
    sub_sold_pending.render(df_raw_listing)

elif selected_tab == "✅ SOLD 発送完了":
    df_raw_listing = load_sheet_data("T_Listing")
    st.markdown('<p class="header-title">✅ SOLD 発送完了履歴</p>', unsafe_allow_html=True)
    sub_sold_shipped.render(df_raw_listing)

elif selected_tab == "📊 売上管理":
    df_raw_listing = load_sheet_data("T_Listing")
    st.markdown('<p class="header-title">📊 統合売上管理サマリー</p>', unsafe_allow_html=True)
    sub_sales_mgmt.render(df_raw_listing)

elif selected_tab == "💰 資金管理":
    if hasattr(tab2_master, "render"):
        tab2_master.render()

elif selected_tab == "📋 取り込み進捗（星取り表）":
    render_tab8_import_matrix()

elif selected_tab == "📥 CSV一括取り込み":
    render_tab9_csv_importer()

elif selected_tab == "📑 整備済み取引データ":
    render_tab11_transactions()

elif selected_tab == "📊 月別収支サマリー":
    render_tab12_summary_matrix()

elif selected_tab == "⚙️ 名寄せルール設定":
    render_tab10_rules()