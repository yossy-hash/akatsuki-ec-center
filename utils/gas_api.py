import requests
import pandas as pd
import streamlit as st

def call_gas_action(action_name: str, payload: dict = None):
    """GASの各種アクション（init_sheetsなど）を呼び出す共通関数"""
    gas_url = st.secrets.get("GAS_API_URL")
    if not gas_url:
        st.error("secrets.toml に GAS_API_URL が未設定です。")
        return None
    
    data = {"action": action_name}
    if payload:
        data.update(payload)
        
    try:
        response = requests.post(gas_url, json=data, timeout=15)
        return response.json()
    except Exception as e:
        st.error(f"GAS呼び出し通信エラー: {e}")
        return None

def load_sheet_data(sheet_name: str) -> pd.DataFrame:
    """シートデータの読み込み（GETリクエスト経由）"""
    gas_url = st.secrets.get("GAS_API_URL")
    if not gas_url:
        return pd.DataFrame()
    
    try:
        response = requests.get(gas_url, params={"sheet": sheet_name}, timeout=15)
        data = response.json()
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict) and data.get("status") == "success":
            return pd.DataFrame(data.get("result", []))
        return pd.DataFrame()
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return pd.DataFrame()

def append_sheet_data(sheet_name: str, rows: list) -> bool:
    """シートへ行追記（POSTリクエスト経由）"""
    res = call_gas_action("append_data", {"sheet": sheet_name, "data": rows})
    return bool(res and res.get("status") == "success")