import streamlit as st
import pandas as pd
from datetime import datetime
from utils.gas_api import load_sheet_data, append_sheet_data, call_gas_action

SHEET_NAME = "T_ImportStatus"

def render_tab8_import_matrix():
    st.title("📋 データ取り込み進捗（星取り表）")
    st.write("売上・決済・銀行データの取り込み状況を一元管理します。")

    with st.expander("⚙️ スプレッドシート初期化（初回のみ）"):
        st.write("ボタンを押すと、確定申告・会計に必要な全タブとヘッダー列が全自動で作成されます。")
        if st.button("🚀 会計用シートを全自動作成する", type="secondary"):
            with st.spinner("スプレッドシートに新しいタブを作成中..."):
                res = call_gas_action("init_sheets")
                if res and res.get("status") == "success":
                    st.success(res.get("result"))
                    st.rerun()
                else:
                    st.error("作成に失敗しました。")

    st.markdown("---")

    df = load_sheet_data(SHEET_NAME)
    all_months = [f"2026-{m:02d}" for m in range(1, 13)]
    
    targets = {
        "card_aeon": "💳 イオンカード",
        "card_rakuten_pri": "💳 楽天(個)",
        "card_rakuten_biz": "💳 楽天(公)",
        "card_amazon": "💳 Amazonカード",
        "sales_amazon": "🛍️ Amazon売上",
        "sales_ebay": "🛍️ eBay売上",
        "sales_mercari": "🛍️ メルカリ売上",
        "sales_yahoo": "🛍️ ヤフオク売上",
        "mf_status": "📊 MFデータ",
        "bank_status": "🏦 銀行明細",
        "receipt_status": "🧾 固定費・領収書"
    }

    # 各月のステータス初期化
    status_records = {m: {key: "❌ 未登録" for key in targets.keys()} for m in all_months}

    if not df.empty and "month" in df.columns:
        for _, row in df.iterrows():
            m = str(row.get("month", "")).strip()
            if m in status_records:
                for key in targets.keys():
                    val = str(row.get(key, "")).strip().upper()
                    if val in ["OK", "✅ OK", "TRUE"]:
                        status_records[m][key] = "✅ OK"

    display_data = []
    for m in all_months:
        row_disp = {"対象年月": m}
        all_ok = True
        for key, name in targets.items():
            val = status_records[m][key]
            row_disp[name] = val
            if val != "✅ OK":
                all_ok = False
        
        row_disp["全体進捗"] = "🎉 完了" if all_ok else "⚠️ 未完了"
        display_data.append(row_disp)

    st.subheader("📊 取り込み進捗マトリクス")
    st.dataframe(pd.DataFrame(display_data), use_container_width=True, hide_index=True)

    st.markdown("---")

    st.subheader("📥 ステータス手動更新")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_month = st.selectbox("対象月", all_months, index=6)
    with col2:
        source_key = st.selectbox("データ種別", list(targets.keys()), format_func=lambda x: targets[x])
    with col3:
        st.write("")
        st.write("")
        submit_btn = st.button("🚀 取り込みOKとして登録", type="primary")

    if submit_btn:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_data = {
            "month": selected_month,
            "last_updated": now_str,
            source_key: "OK"
        }
        
        with st.spinner("スプレッドシート更新中..."):
            if append_sheet_data(SHEET_NAME, [row_data]):
                st.success(f"[{selected_month}] {targets[source_key]} を『✅ OK』に更新しました！")
                st.rerun()
            else:
                st.error("更新に失敗しました。")