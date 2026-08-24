import requests
import json
import pandas as pd
import streamlit as st

def call_gas_action(action_name: str, payload: dict = None):
    gas_url = st.secrets.get("GAS_API_URL")
    if not gas_url:
        st.error("secrets.toml に GAS_API_URL が未設定です。")
        return None
    
    data = {"action": action_name}
    if payload:
        data.update(payload)
        
    try:
        # タイムアウトを60秒に延長
        response = requests.post(gas_url, json=data, timeout=60)
        return response.json()
    except Exception as e:
        st.error(f"GAS呼び出し通信エラー: {e}")
        return None

def load_sheet_data(sheet_name: str) -> pd.DataFrame:
    gas_url = st.secrets.get("GAS_API_URL")
    if not gas_url:
        return pd.DataFrame()
    
    try:
        response = requests.get(gas_url, params={"sheet": sheet_name}, timeout=30, allow_redirects=True)
        if response.status_code != 200:
            return pd.DataFrame()
            
        res_text = response.text.strip()
        if not res_text:
            return pd.DataFrame()
            
        data = json.loads(res_text)
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            if data.get("status") == "success":
                return pd.DataFrame(data.get("result", []))
                
        return pd.DataFrame()
            
    except Exception:
        return pd.DataFrame()

def append_sheet_data(sheet_name: str, rows: list) -> bool:
    res = call_gas_action("append_data", {"sheet": sheet_name, "data": rows})
    return bool(res and res.get("status") == "success")