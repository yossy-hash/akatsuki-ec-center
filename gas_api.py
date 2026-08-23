# utils/gas_api.py
import pandas as pd
import requests
import streamlit as st
from config import SHEET_ID, GAS_WEBAPP_URL

@st.cache_data(ttl=5)
def load_sheet_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        df = pd.read_csv(url)
        return df.fillna("")
    except Exception:
        return pd.DataFrame()

def save_full_inventory_table_snapshot_via_gas(pur_list):
    if "YOUR_GAS_DEPLOYMENT_ID" in GAS_WEBAPP_URL:
        st.cache_data.clear()
        return len(pur_list)
    try:
        payload = {"action": "snapshot", "rows": pur_list}
        res = requests.post(GAS_WEBAPP_URL, json=payload, timeout=10)
        st.cache_data.clear()
        return len(pur_list)
    except Exception:
        st.cache_data.clear()
        return len(pur_list)

def update_item_details_to_spreadsheet(item_id, new_asin=None, yahoo_desc=None):
    if "YOUR_GAS_DEPLOYMENT_ID" in GAS_WEBAPP_URL:
        st.cache_data.clear()
        return True, "ローカル保存準備完了 (GAS URL設定後に本番反映されます)"
    try:
        payload = {
            "action": "update_item",
            "item_id": item_id,
            "asin": new_asin,
            "description": yahoo_desc
        }
        res = requests.post(GAS_WEBAPP_URL, json=payload, timeout=10)
        st.cache_data.clear()
        if res.status_code == 200:
            return True, "スプレッドシートへ更新・書き込みました！"
        else:
            return False, f"書き込みエラー: Status {res.status_code}"
    except Exception as e:
        return False, f"通信エラー: {e}"