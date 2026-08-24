import streamlit as st
import pandas as pd
import json
from datetime import datetime
from utils.gas_api import append_sheet_data, load_sheet_data

def render_tab9_csv_importer():
    st.title("📥 CSV一括取り込み・データ変換")
    st.write("各プラットフォームやカード明細のCSVを読み込み、統一フォーマットへ変換して書き込みます。")

    col1, col2 = st.columns([1, 2])
    
    with col1:
        # データ種別の選択
        source_type = st.selectbox(
            "データ種別を選択",
            [
                "sales_amazon", "sales_ebay", "sales_mercari", "sales_yahoo",
                "card_aeon", "card_rakuten_pri", "card_rakuten_biz", "card_amazon",
                "bank_status"
            ],
            format_func=lambda x: {
                "sales_amazon": "🛍️ Amazon売上",
                "sales_ebay": "🛍️ eBay売上",
                "sales_mercari": "🛍️ メルカリ売上",
                "sales_yahoo": "🛍️ ヤフオク売上",
                "card_aeon": "💳 イオンカード",
                "card_rakuten_pri": "💳 楽天(個)",
                "card_rakuten_biz": "💳 楽天(公)",
                "card_amazon": "💳 Amazonカード",
                "bank_status": "🏦 銀行明細"
            }.get(x, x)
        )
        
        target_month = st.selectbox("対象年月", [f"2026-{m:02d}" for m in range(1, 13)], index=7)

    # ファイルアップローダー
    uploaded_file = st.file_uploader("CSVファイルをドロップしてください", type=["csv"])

    if uploaded_file is not None:
        try:
            # エンコーディング自動判定（Shift-JIS / UTF-8）
            try:
                df_raw = pd.read_csv(uploaded_file, encoding="utf-8")
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df_raw = pd.read_csv(uploaded_file, encoding="cp932")

            st.success(f"ファイル読み込み成功: {len(df_raw)} 行")
            st.subheader("👀 読み込みプレビュー（先頭5件）")
            st.dataframe(df_raw.head(), use_container_width=True)

            if st.button("🚀 データを変換してスプレッドシートへ取り込む", type="primary"):
                with st.spinner("データ変換および登録処理中..."):
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    raw_id = f"RAW_{datetime.now().strftime('%Y%m%d%H%M%S')}"

                    # 1. T_RawData への生データ保存用レコード作成
                    raw_record = {
                        "raw_id": raw_id,
                        "import_date": now_str,
                        "source_type": source_type,
                        "target_month": target_month,
                        "raw_text_json": json.dumps(df_raw.head(50).to_dict(orient="records"), ensure_ascii=False)
                    }

                    # 2. T_Transactions への標準化レコード生成（簡易クレンジング）
                    tx_records = []
                    for idx, row in df_raw.iterrows():
                        # 列名の自動推測処理
                        date_val = str(row.get("日付", row.get("利用日", row.get("取引日", now_str[:10]))))
                        name_val = str(row.get("内容", row.get("利用店名・商品名", row.get("摘要", "名称不明"))))
                        amount_val = row.get("金額", row.get("利用金額(円)", row.get("支払金額", 0)))

                        tx_records.append({
                            "transaction_id": f"TX_{raw_id}_{idx+1:04d}",
                            "date": date_val,
                            "source": source_type,
                            "original_name": name_val,
                            "clean_name": name_val,
                            "category": "未分類",
                            "amount": amount_val,
                            "is_transfer": "FALSE",
                            "ratio": 100,
                            "raw_id_ref": raw_id,
                            "receipt_url": "",
                            "notes": f"自動取込: {target_month}"
                        })

                    # 3. スプレッドシートへの書き込み実行
                    res_raw = append_sheet_data("T_RawData", [raw_record])
                    res_tx = append_sheet_data("T_Transactions", tx_records)

                    # 4. 星取り表 (T_ImportStatus) の自動更新
                    status_record = {
                        "month": target_month,
                        "last_updated": now_str,
                        source_type: "OK"
                    }
                    res_status = append_sheet_data("T_ImportStatus", [status_record])

                    if res_tx:
                        st.balloons()
                        st.success(f"🎉 取込完了！ [{target_month}] に {len(tx_records)} 件の取引データを追加し、星取り表を更新しました！")
                    else:
                        st.error("書き込みに失敗しました。")

        except Exception as e:
            st.error(f"ファイル処理エラー: {e}")