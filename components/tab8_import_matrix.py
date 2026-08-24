import streamlit as st
import pandas as pd
from datetime import datetime
from utils.gas_api import load_sheet_data, append_sheet_data, call_gas_action

SHEET_STATUS = "T_ImportStatus"
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

    # 1. T_Transactions（実際の取引データ）と T_ImportStatus（手動ステータス）の両方を読み込む
    df_tx = load_sheet_data(SHEET_TX)
    df_status = load_sheet_data(SHEET_STATUS)

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

    # A) T_Transactions の実データから自動検知（2026-MM形式の日付と source を判定）
    if not df_tx.empty and "date" in df_tx.columns and "source" in df_tx.columns:
        for _, row in df_tx.iterrows():
            d_str = str(row.get("date", "")).strip()
            src_str = str(row.get("source", "")).strip()
            
            # 日付から YYYY-MM を抽出
            if len(d_str) >= 7 and d_str[:7] in status_records:
                month_key = d_str[:7]
                if src_str in targets:
                    status_records[month_key][src_str] = "✅ OK"

    # B) T_ImportStatus の手動フラグも重ね合わせて反映
    if not df_status.empty and "month" in df_status.columns:
        for _, row in df_status.iterrows():
            m = str(row.get("month", "")).strip()
            if m in status_records:
                for key in targets.keys():
                    val = str(row.get(key, "")).strip().upper()
                    if val in ["OK", "✅ OK", "TRUE"]:
                        status_records[m][key] = "✅ OK"

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
            if append_sheet_data(SHEET_STATUS, [row_data]):
                st.success(f"[{selected_month}] {targets[source_key]} を『✅ OK』に更新しました！")
                st.rerun()
            else:
                st.error("更新に失敗しました。")