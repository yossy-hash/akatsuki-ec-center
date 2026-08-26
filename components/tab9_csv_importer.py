import streamlit as st
import pandas as pd
import json
from io import StringIO
from datetime import datetime
from utils.gas_api import append_sheet_data, load_sheet_data

SHEET_RULES = "M_Rules"

def clean_amount(val):
    if pd.isna(val) or val is None:
        return 0
    val_str = str(val).replace("￥", "").replace("¥", "").replace(",", "").strip()
    try:
        return abs(int(float(val_str)))
    except ValueError:
        return 0

def format_date_str(val):
    val_str = str(val).strip().replace("/", "-")
    val_parts = val_str.split(" ")[0].split(".")
    val_clean = val_parts[0]
    
    if len(val_clean) == 10 and val_clean.count("-") == 2:
        return val_clean
    elif len(val_clean) == 6 and val_clean.isdigit():
        return f"20{val_clean[:2]}-{val_clean[2:4]}-{val_clean[4:6]}"
    elif len(val_clean) == 8 and val_clean.isdigit():
        return f"{val_clean[:4]}-{val_clean[4:6]}-{val_clean[6:8]}"
    return val_clean

def apply_cleansing_rules(original_name, rules_df):
    if rules_df.empty or "keyword" not in rules_df.columns:
        return original_name, "未分類", 100

    for _, rule in rules_df.iterrows():
        kw = str(rule.get("keyword", "")).strip()
        if kw and kw in original_name:
            c_name = str(rule.get("clean_name", original_name)).strip()
            cat = str(rule.get("category", "未分類")).strip()
            try:
                rat = int(rule.get("ratio", 100))
            except ValueError:
                rat = 100
            return c_name if c_name else original_name, cat, rat

    return original_name, "未分類", 100

def parse_csv_by_source(uploaded_file, source_type):
    try:
        uploaded_file.seek(0)
        content = uploaded_file.read().decode("cp932", errors="ignore")
    except Exception:
        uploaded_file.seek(0)
        content = uploaded_file.read().decode("utf-8", errors="ignore")

    lines = [line for line in content.splitlines() if line.strip()]

    records = []

    # 🏦 銀行明細（イオン銀行等）専用パーサー
    if source_type in ["bank_status", "bank_aeon"]:
        df_raw = pd.read_csv(StringIO(content))
        for _, row in df_raw.iterrows():
            date_raw = str(row.get("日付", ""))
            name_val = str(row.get("お取引内容", row.get("摘要", row.get("内容", ""))))
            
            # 引出し／預入れの金額判定
            out_val = clean_amount(row.get("お引出し", row.get("引出金額", 0)))
            in_val = clean_amount(row.get("お預入れ", row.get("預入金額", 0)))
            balance_val = clean_amount(row.get("残高（お借入れはマイナス表示）", row.get("残高", 0)))
            
            amount_val = in_val if in_val > 0 else out_val
            date_clean = format_date_str(date_raw)

            # 口座間移動・振替・カード落ちの自動判定
            is_transfer = "FALSE"
            if any(k in name_val for k in ["振込セグチ", "フリカエ", "イオンフイナンシヤル", "チャージ", "振替"]):
                is_transfer = "TRUE"

            if date_raw and date_raw != "nan" and name_val and name_val != "nan" and amount_val > 0:
                records.append({
                    "date": date_clean,
                    "original_name": name_val,
                    "amount": amount_val,
                    "category": "資金移動・振替" if is_transfer == "TRUE" else "未分類",
                    "is_transfer": is_transfer,
                    "balance": balance_val
                })
        return pd.DataFrame(records), df_raw

    # 📊 MFデータパーサー
    elif source_type == "mf_status":
        df_raw = pd.read_csv(StringIO(content))
        for _, row in df_raw.iterrows():
            date_raw = str(row.get("日付", ""))
            name_val = str(row.get("内容", ""))
            amount_raw = row.get("金額（円）", 0)
            is_transfer_val = str(row.get("振替", "0")).strip()
            mf_cat = str(row.get("中項目", row.get("大項目", "未分類")))
            
            date_clean = format_date_str(date_raw)
            amount_val = clean_amount(amount_raw)

            if date_raw and date_raw != "nan" and name_val and name_val != "nan":
                records.append({
                    "date": date_clean,
                    "original_name": name_val,
                    "amount": amount_val,
                    "category": mf_cat if mf_cat != "nan" else "未分類",
                    "is_transfer": "TRUE" if is_transfer_val in ["1", "TRUE", "True"] else "FALSE"
                })
        return pd.DataFrame(records), df_raw

    # 💳 カード明細パーサー
    elif source_type == "card_aeon":
        start_idx = 0
        for i, line in enumerate(lines):
            if any(k in line for k in ["ご利用日", "利用日", "ご利用先", "利用店名"]):
                start_idx = i
                break
        
        clean_csv_text = "\n".join(lines[start_idx:])
        df_clean = pd.read_csv(StringIO(clean_csv_text))

        for _, row in df_clean.iterrows():
            date_raw = str(row.get("ご利用日", row.get("利用日", "")))
            name_val = str(row.get("ご利用先", row.get("利用店名・商品名", "")))
            amount_val = clean_amount(row.get("ご利用金額(円)", row.get("ご利用金額", row.get("利用金額", 0))))
            date_clean = format_date_str(date_raw)

            if (date_raw and date_raw != "nan" and name_val and name_val != "nan" 
                and "ご利用日" not in date_raw and "支払回数" not in name_val and amount_val > 0):
                records.append({
                    "date": date_clean,
                    "original_name": name_val,
                    "amount": amount_val,
                    "category": "未分類",
                    "is_transfer": "FALSE"
                })
        return pd.DataFrame(records), df_clean

    else:
        df_raw = pd.read_csv(StringIO(content))
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
                    "amount": amount_val,
                    "category": "未分類",
                    "is_transfer": "FALSE"
                })
        return pd.DataFrame(records), df_raw

def render_tab9_csv_importer():
    st.title("📥 CSV一括取り込み・データ変換")

    df_rules = load_sheet_data(SHEET_RULES)

    col1, col2 = st.columns([1, 2])
    with col1:
        source_type = st.selectbox(
            "データ種別を選択",
            ["mf_status", "bank_status", "card_aeon", "card_rakuten_pri", "card_rakuten_biz", "card_amazon", "sales_amazon", "sales_ebay", "sales_mercari", "sales_yahoo"],
            format_func=lambda x: {
                "mf_status": "📊 MFデータ（マネーフォワード）",
                "bank_status": "🏦 銀行明細（イオン銀行等）",
                "card_aeon": "💳 イオンカード", "card_rakuten_pri": "💳 楽天(個)", "card_rakuten_biz": "💳 楽天(公)",
                "card_amazon": "💳 Amazonカード", "sales_amazon": "🛍️ Amazon売上", "sales_ebay": "🛍️ eBay売上",
                "sales_mercari": "🛍️ メルカリ売上", "sales_yahoo": "🛍️ ヤフオク売上"
            }.get(x, x)
        )
        target_month = st.selectbox("対象年月", [f"2026-{m:02d}" for m in range(1, 13)], index=7)

    uploaded_file = st.file_uploader("CSVファイルをドロップしてください", type=["csv"])

    if uploaded_file is not None:
        try:
            df_parsed, df_raw = parse_csv_by_source(uploaded_file, source_type)

            st.success(f"🎉 解析成功: {len(df_parsed)} 件の取引データを抽出しました！")
            st.subheader("👀 クレンジング後プレビュー（先頭5件）")
            st.dataframe(df_parsed.head(), use_container_width=True)

            if len(df_parsed) > 0 and st.button("🚀 データを確定してスプレッドシートへ取り込む", type="primary"):
                with st.spinner("スプレッドシートへデータを取り込み中..."):

                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    raw_id = f"RAW_{datetime.now().strftime('%Y%m%d%H%M%S')}"

                    raw_record = {
                        "raw_id": raw_id,
                        "import_date": now_str,
                        "source_type": source_type,
                        "target_month": target_month,
                        "raw_text_json": json.dumps(df_raw.head(30).to_dict(orient="records"), ensure_ascii=False)
                    }

                    tx_records = []
                    for idx, row in df_parsed.iterrows():
                        d_val = str(row.get("date", ""))
                        orig_name = str(row.get("original_name", ""))
                        a_val = int(row.get("amount", 0))
                        parsed_cat = str(row.get("category", "未分類"))
                        is_trans = str(row.get("is_transfer", "FALSE"))
                        bal_val = row.get("balance", "")

                        clean_name, category, ratio = apply_cleansing_rules(orig_name, df_rules)
                        if category == "未分類" and parsed_cat != "未分類":
                            category = parsed_cat

                        tx_records.append({
                            "transaction_id": f"TX_{raw_id}_{idx+1:04d}",
                            "date": d_val,
                            "source": source_type,
                            "original_name": orig_name,
                            "clean_name": clean_name,
                            "category": category,
                            "amount": a_val,
                            "is_transfer": is_trans,
                            "ratio": ratio,
                            "raw_id_ref": raw_id,
                            "receipt_url": "",
                            "notes": f"自動取込: {target_month} | 残高: ￥{bal_val:,}" if bal_val != "" else f"自動取込: {target_month}"
                        })

                    append_sheet_data("T_RawData", [raw_record])
                    res_tx = append_sheet_data("T_Transactions", tx_records)

                    status_record = {"month": target_month, "last_updated": now_str, source_type: "OK"}
                    append_sheet_data("T_ImportStatus", [status_record])

                    if res_tx:
                        st.balloons()
                        st.success(f"🎉 登録完了！ [{target_month}] に {len(tx_records)} 件のデータを正常登録しました！")
                    else:
                        st.error("書き込みに失敗しました。")

        except Exception as e:
            st.error(f"解析エラー: {e}")