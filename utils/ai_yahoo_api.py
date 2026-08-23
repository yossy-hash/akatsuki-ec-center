import urllib.parse
import json
import requests
import os
import streamlit as st
import google.generativeai as genai

# --- Yahoo! Shopping API 設定 ---
YAHOO_CLIENT_ID = "dmVyPTIwMjUwNyZpZD1yYmFwNnlwSXFmJmhhc2g9TURBMk1EaGpOamxpWmpka05UWmlZUQ"

# --- Gemini API Key 設定 ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    try:
        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        GEMINI_API_KEY = ""

def search_yahoo_shopping(jan_code: str = None, item_name: str = None) -> dict:
    """
    Yahoo!ショッピングAPI v3 で商品を検索する関数
    """
    url = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"
    
    params = {
        "appid": YAHOO_CLIENT_ID,
        "results": 1
    }

    clean_jan = ""
    if jan_code and str(jan_code).lower() not in ["nan", "none", ""]:
        clean_jan = str(jan_code).replace(".0", "").strip()

    if clean_jan.isdigit() and len(clean_jan) in [8, 13]:
        params["jan_code"] = clean_jan
    elif item_name and str(item_name).strip() != "":
        clean_name = item_name.replace("【新品】", "").replace("【美品】", "").replace("【中古】", "").strip()
        params["query"] = clean_name
    else:
        return {"found": False, "message": "検索用の有効なJANコードまたは商品名がありません。"}

    try:
        response = requests.get(url, params=params, timeout=6)
        
        if response.status_code == 200:
            data = response.json()
            hits = data.get("hits", [])
            if hits:
                item = hits[0]
                return {
                    "found": True,
                    "title": item.get("name"),
                    "price": item.get("price"),
                    "image_url": item.get("image", {}).get("medium"),
                    "category": item.get("genreCategory", {}).get("name"),
                    "url": item.get("url"),
                    "jan": item.get("janCode", clean_jan)
                }
            else:
                return {"found": False, "message": "Yahoo!ショッピングで該当商品が見つかりませんでした。"}
                
        elif response.status_code == 403:
            return {
                "found": False, 
                "error_403": True, 
                "message": "🚫 Yahoo! APIアクセス拒否 (HTTP 403): AppIDの設定を確認してください。"
            }
        elif response.status_code == 400:
            try:
                err_msg = response.json().get("Error", {}).get("Message", "パラメータが不正です")
            except:
                err_msg = "Bad Request"
            return {"found": False, "message": f"Yahoo! APIエラー (HTTP 400): {err_msg}"}
        else:
            return {"found": False, "message": f"Yahoo! APIエラー: HTTP {response.status_code}"}

    except Exception as e:
        return {"found": False, "message": f"通信エラーが発生しました: {str(e)}"}


def generate_listing_docs_with_gemini(item_data: dict) -> dict:
    """
    Gemini API を使用して各ECモール向け最適化文章を自動一括生成
    """
    if not GEMINI_API_KEY:
        return {"error": "APIキーが設定されていません。"}

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        target_model_name = None
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                if "flash" in m.name:
                    target_model_name = m.name.replace("models/", "")
                    break
        
        if not target_model_name:
            for m in genai.list_models():
                if "generateContent" in m.supported_generation_methods:
                    target_model_name = m.name.replace("models/", "")
                    break

        if not target_model_name:
             return {"error": "利用可能なGeminiモデルが見つかりません。APIキーの権限を確認してください。"}

        # 🌟 プロンプトを改良：絶対に「1つの文字列」で返すように強く指示 🌟
        prompt = f"""
以下の商品情報を元に、各ECモール（メルカリ、Amazon、ヤフオク、eBay）に最適化した「商品説明文」を作成し、JSON形式で返してください。

【商品情報】
商品名: {item_data.get('title')}
カテゴリ: {item_data.get('category')}
参考価格: {item_data.get('price')}円

【出力要件（厳守）】
- 値は必ず「1つの文字列（平文）」にしてください。辞書型（JSONの中にさらにJSON）には絶対にしないでください。
- 文章の改行には必ず改行コード（\\n）を使用してください。
- メルカリ: 絵文字やハッシュタグを使用し、親しみやすい文体に。
- Amazon: 規約に準拠し、簡潔で信頼性の高い文体に。
- ヤフオク: 状態や配送をアピールする文体に。
- eBay: 海外バイヤー向けに正確な英語表現（Direct from Japan等）に。

【JSONフォーマット例】
{{
  "メルカリ": "ご覧いただきありがとうございます！\\n新品未開封です。\\n#メルカリ",
  "Amazon": "【新品・未開封品】\\n迅速丁寧に発送いたします。",
  "ヤフオク": "【美品・送料無料】\\n動作確認済みです。\\nよろしくお願いいたします。",
  "eBay": "Brand New.\\nDirect from Japan.\\nFree Express Shipping!"
}}
"""
        model = genai.GenerativeModel(target_model_name)
        response = model.generate_content(prompt)

        res_text = response.text.replace("```json", "").replace("```", "").strip()
        res_dict = json.loads(res_text)

        # 🌟 安全対策：もしAIが指示を無視して辞書型を返してきたら、Pythonで強制的に改行テキストに直す 🌟
        for key, val in res_dict.items():
            if isinstance(val, dict):
                # 辞書の中身を連結して改行付きの1つの文字列にする
                res_dict[key] = "\n\n".join([f"【{k}】\n{v}" for k, v in val.items()])
            elif isinstance(val, list):
                res_dict[key] = "\n".join([str(x) for x in val])

        return res_dict

    except Exception as e:
        return {"error": f"Gemini文章生成エラー: {str(e)}"}