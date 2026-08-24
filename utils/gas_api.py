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
    """シートデータの読み込み（既存のGAS doGet互換）"""
    gas_url = st.secrets.get("GAS_API_URL")
    if not gas_url:
        return pd.DataFrame()
    
    try:
        # GASのdoGetへパラメータを送信
        response = requests.get(gas_url, params={"sheet": sheet_name}, timeout=15)
        
        # レスポンス文字列のパース（安全処理）
        res_text = response.text.strip()
        if not res_text:
            return pd.DataFrame()
            
        data = json.loads(res_text)
        
        # 配列で返ってきた場合（通常パターン）
        if isinstance(data, list):
            return pd.DataFrame(data)
        # オブジェクトで返ってきた場合
        elif isinstance(data, dict):
            if data.get("status") == "success":
                result = data.get("result", [])
                if isinstance(result, list):
                    return pd.DataFrame(result)
            elif data.get("status") == "error":
                # エラーメッセージ表示（データなしの場合は無視）
                if "Sheet not found" not in str(data.get("result")):
                    st.warning(f"シート [{sheet_name}] 読み込み注意: {data.get('result')}")
                return pd.DataFrame()
                
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return pd.DataFrame()

def append_sheet_data(sheet_name: str, rows: list) -> bool:
    """シートへ行追記（既存のGAS doPost互換）"""
    res = call_gas_action("append_data", {"sheet": sheet_name, "data": rows})
    return bool(res and res.get("status") == "success")