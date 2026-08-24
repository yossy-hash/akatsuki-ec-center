import streamlit as st
from utils.gas_api import load_sheet_data
from components.tab1_inventory import render_tab1_inventory
from components.tab3_listing import render_tab3_listing
from components import tab2_master, tab4_sourcing, tab5_doc_generator
from components.listing import sub_sold_pending, sub_sold_shipped, sub_sales_mgmt
from components.tab8_import_matrix import render_tab8_import_matrix
# 🆕 CSV取り込みモジュールのインポート
from components.tab9_csv_importer import render_tab9_csv_importer

st.set_page_config(page_title="AKATSUKI 統合ECコマンドセンター", layout="wide")

# (CSS等の設定はそのまま) ...

# ナビゲーションメニュー定義（CSV取り込みを追加）
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
    ("📥 CSV一括取り込み", "tab_csv_importer")  # 👈 🆕 追加！
]

# (ボタン生成ループ処理はそのまま) ...

selected_tab = st.session_state["current_tab"]

# (既存の if / elif ルーティング処理はそのまま) ...

elif selected_tab == "📋 取り込み進捗（星取り表）":
    render_tab8_import_matrix()

# 🆕 【追加画面】CSV取り込み画面の描画処理
elif selected_tab == "📥 CSV一括取り込み":
    render_tab9_csv_importer()