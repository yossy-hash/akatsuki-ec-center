import streamlit as st
import pandas as pd
from datetime import datetime
from utils.gas_api import load_sheet_data, call_gas_action

SHEET_RAW = "T_RawData"
SHEET_TX = "T_Transactions"

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

    # RawデータとTransactionsデータを読み込み
    df_raw = load_sheet_data(SHEET_RAW)
    df_tx = load_sheet_data(SHEET_TX)

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

    status_records = {m: {key: "❌ 未登録" for key in targets.keys()} for m in all_months}

    # A) T_RawDataの「target_month」と「source_type」から正確に判定
    if not df_raw.empty and "target_month" in df_raw.columns and "source_type" in df_raw.columns:
        for _, row in df_raw.iterrows():
            tm = str(row.get("target_month", "")).strip()
            stype = str(row.get("source_type", "")).strip()
            if tm in status_records and stype in targets:
                status_records[tm][stype] = "✅ OK"

    # B) T_Transactionsの「notes（自動取込: YYYY-MM）」からも念のため正確判定
    if not df_tx.empty and "notes" in df_tx.columns and "source" in df_tx.columns:
        for _, row in df_tx.iterrows():
            notes = str(row.get("notes", ""))
            src = str(row.get("source", "")).strip()
            if "自動取込: " in notes:
                tm = notes.replace("自動取込: ", "").strip()
                if tm in status_records and src in targets:
                    status_records[tm][src] = "✅ OK"

    # マトリクス表示用データの作成
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