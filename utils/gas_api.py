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
        response = requests.post(gas_url, json=data, timeout=15)
        return response.json()
    except Exception as e:
        st.error(f"GAS呼び出し通信エラー: {e}")
        return None

def load_sheet_data(sheet_name: str) -> pd.DataFrame:
    gas_url = st.secrets.get("GAS_API_URL")
    if not gas_url:
        st.error("【診断】GAS_API_URLがsecretsに存在しません。")
        return pd.DataFrame()
    
    try:
        # リダイレクトを許可してGETリクエスト
        response = requests.get(gas_url, params={"sheet": sheet_name}, timeout=15, allow_redirects=True)
        
        # ステータスコードと生テキストの確認
        if response.status_code != 200:
            st.error(f"【診断エラー】HTTPステータス: {response.status_code}")
            return pd.DataFrame()
            
        res_text = response.text.strip()
        
        # もし中身が空の場合
        if not res_text:
            st.error("【診断エラー】GASから返ってきたレスポンスが空文字(0バイト)です。")
            return pd.DataFrame()
            
        # JSON変換を試行
        try:
            data = json.loads(res_text)
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                if data.get("status") == "success":
                    return pd.DataFrame(data.get("result", []))
            return pd.DataFrame()
            
        except json.JSONDecodeError as json_err:
            # 返ってきた生データを画面に表示して原因特定
            st.error(f"【診断：JSONパース失敗】返ってきた先頭100文字: {res_text[:100]}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"【通信例外エラー】: {e}")
        return pd.DataFrame()

def append_sheet_data(sheet_name: str, rows: list) -> bool:
    res = call_gas_action("append_data", {"sheet": sheet_name, "data": rows})
    return bool(res and res.get("status") == "success")