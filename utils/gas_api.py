import os
import requests
import json
import pandas as pd
import streamlit as st

SPREADSHEET_ID = "1Il6v8VWvSoNAyCP2V0Xk_4UnyOQZ0M6phGyExFfKeOs"

def get_gas_url() -> str:
    if hasattr(st, "secrets"):
        for key in ["GAS_API_URL", "GAS_URL"]:
            if key in st.secrets:
                return st.secrets[key]
    return os.environ.get("GAS_API_URL") or os.environ.get("GAS_URL") or ""

GAS_API_URL = get_gas_url()
GAS_URL = GAS_API_URL

def load_sheet_data(sheet_name: str) -> pd.DataFrame:
    """CSV直で高速読み込み"""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(url)
        return df.dropna(how="all").dropna(axis=1, how="all")
    except Exception:
        return pd.DataFrame()

def append_sheet_data(sheet_name: str, records: list) -> bool:
    """GAS Web APIへPOSTしてスプレッドシートへ直接行追加"""
    target_url = get_gas_url()
    if not target_url:
        st.error("⚠️ GAS_API_URL が設定されていません。secrets.toml を確認してください。")
        return False
        
    try:
        payload = {
            "action": "append",
            "sheet": sheet_name,
            "data": records
        }
        headers = {"Content-Type": "application/json"}
        
        # 🌟 allow_redirects=True を追加してGASのリダイレクトを自動追従
        response = requests.post(
            target_url, 
            data=json.dumps(payload), 
            headers=headers, 
            timeout=15,
            allow_redirects=True
        )
        
        if response.status_code == 200:
            try:
                res_json = response.json()
                if isinstance(res_json, dict) and res_json.get("status") == "error":
                    st.error(f"🚨 GAS側の実行エラー: {res_json.get('result')}")
                    return False
                return True
            except Exception:
                # GASからのレスポンスがJSON形式でない場合の安全ガード
                if "success" in response.text.lower():
                    return True
                st.error(f"🚨 レスポンス解析エラー: {response.text[:200]}")
                return False
        else:
            st.error(f"🚨 スプレッドシート通信エラー (HTTP Status: {response.status_code})")
            return False
            
    except Exception as e:
        st.error(f"🚨 スプレッドシート通信例外エラー: {e}")
        return False