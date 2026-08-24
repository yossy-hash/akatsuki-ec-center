# インポート追加
from components.tab10_rules import render_tab10_rules

# NAV_ITEMS に追加
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
    ("⚙️ 名寄せルール設定", "tab_rules")  # 👈 🆕 追加！
]

# (ルーティングの末尾に追加)
elif selected_tab == "⚙️ 名寄せルール設定":
    render_tab10_rules()