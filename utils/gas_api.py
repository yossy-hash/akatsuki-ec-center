import requests
import json
import pandas as pd
import streamlit as st

def call_gas_action(action_name: str, payload: dict = None):
    """GASへのPOST通信（init_sheets / append_data 用）"""
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
    """GASからのデータ取得（純粋な配列JSON対応版）"""
    gas_url = st.secrets.get("GAS_API_URL")
    if not gas_url:
        return pd.DataFrame()
    
    try:
        # GASへリクエスト
        response = requests.get(gas_url, params={"sheet": sheet_name}, timeout=15)
        
        if response.status_code != 200 or not response.text.strip():
            return pd.DataFrame()
            
        # JSONをパース
        data = response.json()
        
        # 1. 画像で確認できた「配列型JSON」の処理（メイン経路）
        if isinstance(data, list):
            return pd.DataFrame(data)
            
        # 2. 万が一辞書型で返ってきた場合の安全処理
        elif isinstance(data, dict):
            if data.get("status") == "success":
                res_list = data.get("result", [])
                if isinstance(res_list, list):
                    return pd.DataFrame(res_list)
            return pd.DataFrame()
            
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return pd.DataFrame()

def append_sheet_data(sheet_name: str, rows: list) -> bool:
    """シートへ行追記"""
    res = call_gas_action("append_data", {"sheet": sheet_name, "data": rows})
    return bool(res and res.get("status") == "success")