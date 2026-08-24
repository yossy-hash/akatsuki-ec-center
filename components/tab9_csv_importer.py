import streamlit as st
import pandas as pd
import json
from io import StringIO
from datetime import datetime
from utils.gas_api import append_sheet_data

def clean_amount(val):
    if pd.isna(val) or val is None:
        return 0
    val_str = str(val).replace("￥", "").replace("¥", "").replace(",", "").strip()
    try:
        return int(float(val_str))
    except ValueError:
        return 0

def format_date_str(val):
    val_str = str(val).strip().split(".")[0]
    if len(val_str) == 6 and val_str.isdigit():
        return f"20{val_str[:2]}-{val_str[2:4]}-{val_str[4:6]}"
    elif len(val_str) == 8 and val_str.isdigit():
        return f"{val_str[:4]}-{val_str[4:6]}-{val_str[6:8]}"
    return val_str

def parse_csv_by_source(uploaded_file, source_type):
    try:
        uploaded_file.seek(0)
        content = uploaded_file.read().decode("cp932", errors="ignore")
    except Exception:
        uploaded_file.seek(0)
        content = uploaded_file.read().decode("utf-8", errors="ignore")

    lines = [line for line in content.splitlines() if line.strip()]

    with st.expander("🔍 CSV解析データの詳細・検証情報（クリックで開閉）"):
        st.write(" **CSVの生の先頭10行:**")
        st.code("\n".join(lines[:10]))

    records = []

    if source_type == "card_aeon":
        start_idx = 0
        for i, line in enumerate(lines):
            if any(k in line for k in ["ご利用日", "利用日", "ご利用先", "利用店名"]):
                start_idx = i
                break
        
        clean_csv_text = "\n".join(lines[start_idx:])
        df_clean = pd.read_csv(StringIO(clean_csv_text))

        with st.expander("🔍 CSV解析データの詳細・検証情報（クリックで開閉）"):
            st.write(" **認識されたヘッダー列名:**", list(df_clean.columns))

        for _, row in df_clean.iterrows():
            date_raw = str(row.get("ご利用日", row.get("利用日", "")))
            name_val = str(row.get("ご利用先", row.get("利用店名・商品名", "")))
            amount_val = clean_amount(row.get("ご利用金額(円)", row.get("ご利用金額", row.get("利用金額", 0))))
            
            date_clean = format_date_str(date_raw)

            # 有効な明細行のみ抽出（「ご利用日」「支払回数」などのフッター・ヘッダーゴミ行を除外）
            if (date_raw and date_raw != "nan" and name_val and name_val != "nan" 
                and "ご利用日" not in date_raw and "支払回数" not in name_val and amount_val > 0):
                records.append({
                    "date": date_clean,
                    "original_name": name_val,
                    "amount": amount_val
                })
        return pd.DataFrame(records), df_clean

    else:
        df_raw = pd.read_csv(StringIO(content))
        with st.expander("🔍 CSV解析データの詳細・検証情報（クリックで開閉）"):
            st.write(" **認識されたヘッダー列名:**", list(df_raw.columns))

        for _, row in df_raw.iterrows():
            date_val, name_val, amount_val = "", "", 0
            for col in df_raw.columns:
                c_str = str(col)
                if any(k in c_str for k in ["ご利用日", "利用日", "日付", "取引日"]):
                    date_val = format_date_str(row[col])
                elif any(k in c_str for k in ["ご利用先", "利用店", "内容", "摘要"]):
                    name_val = str(row[col])
                elif any(k in c_str for k in ["ご利用金額", "金額", "支払", "売上"]):
                    amount_val = clean_amount(row[col])
            
            if name_val and name_val != "nan" and amount_val > 0:
                records.append({
                    "date": date_val if date_val else datetime.now().strftime("%Y-%m-%d"),
                    "original_name": name_val,
                    "amount": amount_val
                })
        return pd.DataFrame(records), df_raw

def render_tab9_csv_importer():
    st.title("📥 CSV一括取り込み・データ変換")

    col1, col2 = st.columns([1, 2])
    with col1:
        source_type = st.selectbox(
            "データ種別を選択",
            ["card_aeon", "card_rakuten_pri", "card_rakuten_biz", "card_amazon", "sales_amazon", "sales_ebay", "sales_mercari", "sales_yahoo", "bank_status"],
            format_func=lambda x: {
                "card_aeon": "💳 イオンカード", "card_rakuten_pri": "💳 楽天(個)", "card_rakuten_biz": "💳 楽天(公)",
                "card_amazon": "💳 Amazonカード", "sales_amazon": "🛍️ Amazon売上", "sales_ebay": "🛍️ eBay売上",
                "sales_mercari": "🛍️ メルカリ売上", "sales_yahoo": "🛍️ ヤフオク売上", "bank_status": "🏦 銀行明細"
            }.get(x, x)
        )
        target_month = st.selectbox("対象年月", [f"2026-{m:02d}" for m in range(1, 13)], index=6)

    uploaded_file = st.file_uploader("CSVファイルをドロップしてください", type=["csv"])

    if uploaded_file is not None:
        try:
            df_parsed, df_raw = parse_csv_by_source(uploaded_file, source_type)

            st.success(f"🎉 解析成功: {len(df_parsed)} 件の取引データを抽出しました！")
            st.subheader("👀 クレンジング後プレビュー（先頭5件）")
            st.dataframe(df_parsed.head(), use_container_width=True)

            if len(df_parsed) > 0 and st.button("🚀 データを確定してスプレッドシートへ取り込む", type="primary"):
                with st.spinner("スプレッドシートへ登録中..."):
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    raw_id = f"RAW_{datetime.now().strftime('%Y%m%d%H%M%S')}"

                    # T_RawData レコード（GAS配列渡し用の並び順保証）
                    raw_record = {
                        "raw_id": raw_id,
                        "import_date": now_str,
                        "source_type": source_type,
                        "target_month": target_month,
                        "raw_text_json": json.dumps(df_raw.head(30).to_dict(orient="records"), ensure_ascii=False)
                    }

                    # T_Transactions レコード
                    tx_records = []
                    for idx, row in df_parsed.iterrows():
                        d_val = str(row.get("date", ""))
                        n_val = str(row.get("original_name", ""))
                        a_val = int(row.get("amount", 0))

                        tx_records.append({
                            "transaction_id": f"TX_{raw_id}_{idx+1:04d}",
                            "date": d_val,
                            "source": source_type,
                            "original_name": n_val,
                            "clean_name": n_val,
                            "category": "未分類",
                            "amount": a_val,
                            "is_transfer": "FALSE",
                            "ratio": 100,
                            "raw_id_ref": raw_id,
                            "receipt_url": "",
                            "notes": f"自動取込: {target_month}"
                        })

                    # スプレッドシートへ追加
                    append_sheet_data("T_RawData", [raw_record])
                    res_tx = append_sheet_data("T_Transactions", tx_records)

                    status_record = {"month": target_month, "last_updated": now_str, source_type: "OK"}
                    append_sheet_data("T_ImportStatus", [status_record])

                    if res_tx:
                        st.balloons()
                        st.success(f"🎉 登録完了！ [{target_month}] に {len(tx_records)} 件の取引データを登録しました！")
                    else:
                        st.error("書き込みに失敗しました。")

        except Exception as e:
            st.error(f"解析エラー: {e}")