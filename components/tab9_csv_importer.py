import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime
from utils.gas_api import append_sheet_data, load_sheet_data

def clean_amount(val):
    """金額文字列（¥1,234 や 1,234 形式）を数値に変換"""
    if pd.isna(val) or val is None:
        return 0
    val_str = str(val).replace("￥", "").replace("¥", "").replace(",", "").strip()
    try:
        return int(float(val_str))
    except ValueError:
        return 0

def parse_csv_by_source(uploaded_file, source_type):
    """各データ種別のCSV特有フォーマットを吸収して標準化データフレームを返す"""
    # 1. エンコーディング判定
    try:
        uploaded_file.seek(0)
        df_raw = pd.read_csv(uploaded_file, encoding="utf-8")
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        df_raw = pd.read_csv(uploaded_file, encoding="cp932")

    records = []

    # イオンカード：ヘッダー上部スキップ処理
    if source_type == "card_aeon":
        uploaded_file.seek(0)
        # 「ご利用日」または「利用日」が含まれる行を探す
        lines = uploaded_file.read().decode("cp932", errors="ignore").splitlines()
        skip_rows = 0
        for i, line in enumerate(lines):
            if "ご利用日" in line or "利用日" in line:
                skip_rows = i
                break
        
        uploaded_file.seek(0)
        df_clean = pd.read_csv(uploaded_file, skiprows=skip_rows, encoding="cp932")
        
        for _, row in df_clean.iterrows():
            date_val = str(row.get("ご利用日", row.get("利用日", "")))
            name_val = str(row.get("ご利用先", row.get("利用店名・商品名", "")))
            amount_val = clean_amount(row.get("ご利用金額(円)", row.get("利用金額", 0)))
            
            if date_val and name_val and amount_val > 0:
                records.append({
                    "date": date_val,
                    "original_name": name_val,
                    "amount": amount_val
                })

    # 汎用処理（その他のカード・売上CSV）
    else:
        for _, row in df_raw.iterrows():
            # 日付・店名・金額の自動抽出
            date_val, name_val, amount_val = "", "", 0
            for col in df_raw.columns:
                col_str = str(col)
                if any(k in col_str for k in ["日付", "利用日", "取引日", "年月日"]):
                    date_val = str(row[col])
                elif any(k in col_str for k in ["内容", "利用店名", "摘要", "商品名", "ご利用先"]):
                    name_val = str(row[col])
                elif any(k in col_str for k in ["金額", "利用金額", "支払金額", "売上"]):
                    amount_val = clean_amount(row[col])
            
            if name_val or amount_val > 0:
                records.append({
                    "date": date_val if date_val else datetime.now().strftime("%Y-%m-%d"),
                    "original_name": name_val if name_val else "名称未設定",
                    "amount": amount_val
                })

    return pd.DataFrame(records), df_raw

def render_tab9_csv_importer():
    st.title("📥 CSV一括取り込み・データ変換")
    st.write("各プラットフォームやカード明細のCSVを自動クレンジングして書き込みます。")

    col1, col2 = st.columns([1, 2])
    
    with col1:
        source_type = st.selectbox(
            "データ種別を選択",
            [
                "card_aeon", "card_rakuten_pri", "card_rakuten_biz", "card_amazon",
                "sales_amazon", "sales_ebay", "sales_mercari", "sales_yahoo",
                "bank_status"
            ],
            format_func=lambda x: {
                "card_aeon": "💳 イオンカード",
                "card_rakuten_pri": "💳 楽天(個)",
                "card_rakuten_biz": "💳 楽天(公)",
                "card_amazon": "💳 Amazonカード",
                "sales_amazon": "🛍️ Amazon売上",
                "sales_ebay": "🛍️ eBay売上",
                "sales_mercari": "🛍️ メルカリ売上",
                "sales_yahoo": "🛍️ ヤフオク売上",
                "bank_status": "🏦 銀行明細"
            }.get(x, x)
        )
        
        target_month = st.selectbox("対象年月", [f"2026-{m:02d}" for m in range(1, 13)], index=7)

    uploaded_file = st.file_uploader("CSVファイルをドロップしてください", type=["csv"])

    if uploaded_file is not None:
        try:
            df_parsed, df_raw = parse_csv_by_source(uploaded_file, source_type)

            st.success(f"解析成功: {len(df_parsed)} 件の有効な取引データを抽出しました！")
            st.subheader("👀 クレンジング後プレビュー（先頭5件）")
            st.dataframe(df_parsed.head(), use_container_width=True)

            if st.button("🚀 データを確定してスプレッドシートへ取り込む", type="primary"):
                with st.spinner("スプレッドシートへ登録中..."):
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    raw_id = f"RAW_{datetime.now().strftime('%Y%m%d%H%M%S')}"

                    # 1. T_RawData へのバックアップ保存用レコード
                    raw_record = {
                        "raw_id": raw_id,
                        "import_date": now_str,
                        "source_type": source_type,
                        "target_month": target_month,
                        "raw_text_json": json.dumps(df_raw.head(30).to_dict(orient="records"), ensure_ascii=False)
                    }

                    # 2. T_Transactions への整列済みレコード作成
                    tx_records = []
                    for idx, row in df_parsed.iterrows():
                        tx_records.append({
                            "transaction_id": f"TX_{raw_id}_{idx+1:04d}",
                            "date": str(row.get("date", "")),
                            "source": source_type,
                            "original_name": str(row.get("original_name", "")),
                            "clean_name": str(row.get("original_name", "")),
                            "category": "未分類",
                            "amount": int(row.get("amount", 0)),
                            "is_transfer": "FALSE",
                            "ratio": 100,
                            "raw_id_ref": raw_id,
                            "receipt_url": "",
                            "notes": f"自動取込: {target_month}"
                        })

                    # 3. 書き込み実行
                    res_raw = append_sheet_data("T_RawData", [raw_record])
                    res_tx = append_sheet_data("T_Transactions", tx_records)

                    # 4. 星取り表 (T_ImportStatus) の更新
                    status_record = {
                        "month": target_month,
                        "last_updated": now_str,
                        source_type: "OK"
                    }
                    res_status = append_sheet_data("T_ImportStatus", [status_record])

                    if res_tx:
                        st.balloons()
                        st.success(f"🎉 登録完了！ [{target_month}] に {len(tx_records)} 件の取引データを登録しました！")
                    else:
                        st.error("書き込みに失敗しました。")

        except Exception as e:
            st.error(f"解析エラー: {e}")