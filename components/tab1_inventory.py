# components/tab1_inventory.py
import pandas as pd
import streamlit as st
from utils.gas_api import save_full_inventory_table_snapshot_via_gas

def safe_int(val, default=0):
    try:
        if isinstance(val, str):
            val = val.replace(",", "").replace("$", "").replace("¥", "").strip()
        return int(float(val))
    except (ValueError, TypeError):
        return default

def render_tab1_inventory(df_raw_inventory):
    st.subheader("📦 リアルタイム在庫コントロール")

    raw_inventory_list = df_raw_inventory.to_dict(orient="records") if not df_raw_inventory.empty else []

    pur_list = []
    for r in raw_inventory_list:
        row_id = str(r.get("ID", r.get("id", "")))
        item_name = str(r.get("商品名", r.get("item_name", "未設定商品")))
        jan = str(r.get("JANコード", r.get("jan_code", "")))
        price = safe_int(r.get("仕入価格", r.get("purchase_price", 0)))
        qty = safe_int(r.get("数量", r.get("quantity", 1)))
        date_str = str(r.get("撮影日", r.get("仕入日", "2026-08-23"))).strip()
        storage = str(r.get("保管場所", "未設定"))
        sale_status = str(r.get("販売状態", r.get("ステータス", "出品前"))).strip()

        if sale_status in ["出品中", "販売中"]:
            cat_status = "販売中"
        elif sale_status in ["出品前", "保管中", "未出品", "未設定", "解析済"]:
            cat_status = "販売前"
        else:
            cat_status = "その他"

        pur_list.append({
            "ID": row_id,
            "商品名": item_name,
            "JANコード": jan,
            "仕入日": date_str,
            "仕入価格": price,
            "保管場所": storage,
            "コンディション": str(r.get("備考", "通常")),
            "詳細ステータス": sale_status,
            "区分": cat_status,
            "在庫数": qty
        })

    df_inventory = pd.DataFrame(pur_list)

    if df_inventory.empty:
        st.info("💡 在庫データが読み込まれていません。")
        return

    # 1. ログ保存スナップショットボタン
    with st.container(border=True):
        col_btn_action, col_btn_desc = st.columns([2, 3])
        with col_btn_action:
            if st.button("📸 全在庫一覧表を `EC_Inventory_Logs` へスナップショット保存", type="primary", use_container_width=True):
                cnt = save_full_inventory_table_snapshot_via_gas(pur_list)
                st.success(f"🟢 「EC_Inventory_Logs」タブへ全{cnt}件の在庫明細を保存しました！")
        with col_btn_desc:
            st.write("💡 **月末・定期記録用:** 押すとAppSheetで登録された最新在庫を含む全リストがログ蓄積されます。")

    st.markdown("---")

    # 2. 条件絞り込みラジオボタン
    status_filter = st.radio(
        "🔍 絞り込み条件を選択してください:",
        ["すべて表示", "📦 在庫ありのみ (在庫数 1個以上)", "🟢 販売中のみ", "⏳ 出品前・保管中のみ"],
        horizontal=True
    )

    search_kw = st.text_input("🔍 キーワード検索 (商品名・JAN・保管場所・ID):", placeholder="例: レノア、キュキュット...")

    df_filtered = df_inventory.copy()

    if status_filter == "📦 在庫ありのみ (在庫数 1個以上)":
        df_filtered = df_filtered[df_filtered["在庫数"] >= 1]
    elif status_filter == "🟢 販売中のみ":
        df_filtered = df_filtered[(df_filtered["区分"] == "販売中") & (df_filtered["在庫数"] >= 1)]
    elif status_filter == "⏳ 出品前・保管中のみ":
        df_filtered = df_filtered[(df_filtered["区分"] == "販売前") & (df_filtered["在庫数"] >= 1)]

    if search_kw:
        kw = search_kw.lower()
        df_filtered = df_filtered[
            df_filtered["商品名"].astype(str).str.lower().str.contains(kw) |
            df_filtered["JANコード"].astype(str).str.lower().str.contains(kw) |
            df_filtered["保管場所"].astype(str).str.lower().str.contains(kw) |
            df_filtered["ID"].astype(str).str.lower().str.contains(kw)
        ]

    # 3. 動的集計表示
    sum_qty = df_filtered['在庫数'].sum()
    sum_price = df_filtered['仕入価格'].sum()
    st.write(f"**該当データ:** {len(df_filtered)} 件 ｜ **対象在庫合計:** {sum_qty} 個 ｜ **合計仕入金額:** {sum_price:,} 円")
    
    st.dataframe(
        df_filtered[["ID", "商品名", "JANコード", "在庫数", "詳細ステータス", "保管場所", "仕入価格", "コンディション", "仕入日"]],
        use_container_width=True,
        height=350,
        hide_index=True
    )

    st.divider()

    # 4. 日付別仕入金額推移積層グラフ
    st.subheader("📈 日付別 仕入金額の推移（内訳：販売前 vs 販売中）")
    df_chart_source = df_filtered[df_filtered["区分"].isin(["販売前", "販売中"])].copy()

    if not df_chart_source.empty:
        chart_data = df_chart_source.groupby(["仕入日", "区分"])["仕入価格"].sum().unstack(fill_value=0)
        for c in ["販売前", "販売中"]:
            if c not in chart_data.columns:
                chart_data[c] = 0
        chart_data = chart_data[["販売前", "販売中"]]
        st.bar_chart(chart_data, height=280, use_container_width=True)
    else:
        st.info("💡 表示対象の仕入データがありません。")