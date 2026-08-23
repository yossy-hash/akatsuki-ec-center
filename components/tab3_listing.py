import streamlit as st
import pandas as pd
import time
import json
import os
import google.generativeai as genai

from components.listing import sub_listing_main
from streamlit_paste_button import paste_image_button

# スプレッドシート連携関数のインポート
try:
    from utils.gas_api import append_sheet_data, load_sheet_data
except ImportError:
    append_sheet_data = None
    load_sheet_data = None


def clean_dataframe_for_arrow(df_raw: pd.DataFrame) -> pd.DataFrame:
    """ Streamlit/PyArrowの型エラー防止用データクレンジング """
    if df_raw is None or df_raw.empty:
        return df_raw
    
    df_clean = df_raw.copy()
    
    numeric_cols = [
        "price", "buyout_price", "start_price", "reserve_price", 
        "current_price", "bid_count", "stock", "在庫数", "販売価格", "手数料"
    ]
    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(0)
            
    string_cols = [
        "listing_id", "item_id", "purchase_id", "platform", "title", 
        "description", "listing_type", "JANコード", "ASIN", "SKU", "category", "condition"
    ]
    for col in string_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).replace(["nan", "None", "<NA>"], "")
            
    return df_clean


def render_tab3_listing(df: pd.DataFrame):
    """
    出品状況画面（出品モニタリング専用）
    """
    if df is None or df.empty:
        st.warning("表示できる出品データがありません。")
        return

    df_safe = clean_dataframe_for_arrow(df)

    col1, col2 = st.columns([8, 2])
    with col1:
        st.markdown('<p class="header-title">🚀 出品状況コントロール</p>', unsafe_allow_html=True)
    with col2:
        if st.button("📷 ログ保存", key="btn_log_save_listing", help="現在のスナップショットをログとして保存します"):
            st.toast("出品状況のスナップショットを保存しました。")

    st.markdown("<hr style='margin: 5px 0 15px 0;'>", unsafe_allow_html=True)
    
    if "ocr_active_platform" not in st.session_state:
        st.session_state.ocr_active_platform = None
    if "ocr_extracted_df" not in st.session_state:
        st.session_state.ocr_extracted_df = None

    st.markdown("**📸 各ECサイトの最新データ画像取り込み (AI OCR)**")
    
    cols = st.columns(4)
    platforms = [
        {"name": "Amazon", "color": "#F87171", "icon": "🔴"},
        {"name": "メルカリ", "color": "#4ADE80", "icon": "🟢"},
        {"name": "ヤフオク", "color": "#FBBF24", "icon": "🟠"},
        {"name": "eBay", "color": "#60A5FA", "icon": "🔵"}
    ]
    
    for i, plat in enumerate(platforms):
        p_name = plat["name"]
        p_icon = plat["icon"]
        with cols[i]:
            if st.button(f"{p_icon} {p_name}用 取込", width="stretch"):
                if st.session_state.ocr_active_platform == p_name:
                    st.session_state.ocr_active_platform = None
                else:
                    st.session_state.ocr_active_platform = p_name
                    st.session_state.ocr_extracted_df = None
                st.rerun()

    if st.session_state.ocr_active_platform:
        active_p = st.session_state.ocr_active_platform
        
        st.markdown(f"""
        <div style='background-color:#1e1e1e; padding: 20px; border-radius: 8px; border: 1px dashed #666; margin-bottom: 20px;'>
            <h4 style='margin-top:0;'>{active_p} の管理画面スクリーンショットをアップロード</h4>
            <p style='font-size: 0.9em; color: #aaa;'>スクショを撮った後、下のボタンをクリックするだけで自動で貼り付けられます。</p>
        """, unsafe_allow_html=True)
        
        paste_result = paste_image_button(
            label=f"📋 ここをクリックしてクリップボードから画像を貼り付け",
            background_color="#FF4B4B",
            hover_background_color="#FF6B6B",
            key=f"paste_btn_{active_p}"
        )
        
        if paste_result.image_data is not None:
            st.image(paste_result.image_data, caption="読み込んだ画像", width="stretch")
            
            if st.button(f"🤖 {active_p}の最新データを解析", type="primary", width="stretch"):
                with st.spinner(f"Gemini AIが{active_p}の画像を解析中...（約5〜10秒）"):
                    try:
                        api_key = os.environ.get("GEMINI_API_KEY")
                        if not api_key and "GEMINI_API_KEY" in st.secrets:
                            api_key = st.secrets["GEMINI_API_KEY"]
                        
                        if not api_key:
                            st.error("⚠️ APIキーが見つかりません。")
                            st.stop()
                                
                        genai.configure(api_key=api_key)
                        
                        valid_model_names = [
                            'gemini-2.5-flash',
                            'gemini-1.5-flash-8b',
                            'gemini-2.0-flash',
                            'gemini-1.5-pro-latest'
                        ]
                        
                        prompt = f"""
                        この画像は{active_p}の出品管理画面のスクリーンショットです。
                        画像から出品されている商品の情報を読み取り、以下のキーを持つJSON配列形式で出力してください。
                        JSON以外のテキストや記号(```json 等)は一切含めないでください。
                        
                        必要なキー:
                        - "platform": "{active_p}"
                        - "title": 商品名
                        - "description": 商品説明または状態のサマリ（読み取れなければ空文字）
                        - "listing_type": "定額・即決" または "オークション"
                        - "buyout_price": 販売価格（数値のみ）
                        - "start_price": 開始価格（数値のみ、無ければbuyout_priceと同じ値）
                        - "reserve_price": 最低落札価格（数値のみ、無ければ0）
                        - "current_price": 現在の価格（数値のみ、無ければbuyout_priceと同じ値）
                        """

                        response = None
                        for m_name in valid_model_names:
                            try:
                                model = genai.GenerativeModel(m_name)
                                response = model.generate_content([prompt, paste_result.image_data])
                                break
                            except Exception:
                                continue

                        if response is None:
                            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                            for m_name in available_models:
                                try:
                                    model = genai.GenerativeModel(m_name)
                                    response = model.generate_content([prompt, paste_result.image_data])
                                    break
                                except Exception:
                                    continue

                        if response is None:
                            raise Exception("利用可能なGeminiモデルの自動接続に失敗しました。")

                        result_text = response.text.strip()
                        result_text = result_text.replace("```json", "").replace("```", "").strip()
                        
                        extracted_json = json.loads(result_text)
                        
                        current_max_id = 0
                        if df_safe is not None and not df_safe.empty and "listing_id" in df_safe.columns:
                            ids = df_safe["listing_id"].astype(str).str.replace("LST", "").str.extract(r'(\d+)')[0].dropna().astype(int)
                            if not ids.empty:
                                current_max_id = ids.max()
                        
                        for i, item in enumerate(extracted_json):
                            new_num = current_max_id + i + 1
                            item["listing_id"] = f"LST{new_num:03d}"
                            item["item_id"] = f"ITM{new_num:03d}"
                            item["purchase_id"] = f"PUR{new_num:03d}"
                            item["bid_count"] = 0
                            item["start_date"] = time.strftime("%Y-%m-%d %H:%M:%S")

                        df_extracted = pd.DataFrame(extracted_json)
                        st.session_state.ocr_extracted_df = clean_dataframe_for_arrow(df_extracted)
                        
                        st.toast("✨ データの抽出が完了しました！内容を確認して保存してください。")

                    except Exception as e:
                        st.error(f"🚨 解析中にエラーが発生しました: {e}")

        # 🌟 抽出結果の表示 ＆ スプレッドシート直接送信処理（成功時のみ自動リロード）
        if st.session_state.ocr_extracted_df is not None:
            st.markdown("### 📊 抽出結果（手修正可能です）")
            
            edited_extracted_df = st.data_editor(
                st.session_state.ocr_extracted_df,
                width="stretch",
                num_rows="dynamic",
                key="ocr_data_editor"
            )
            
            col_save1, col_save2 = st.columns(2)
            with col_save1:
                if st.button("💾 この内容でスプレッドシート（T_Listing）を更新", type="primary", width="stretch"):
                    with st.spinner("Googleスプレッドシートへ書き込み中..."):
                        try:
                            if append_sheet_data:
                                cleaned_save_df = clean_dataframe_for_arrow(edited_extracted_df)
                                records_to_save = cleaned_save_df.to_dict(orient="records")
                                
                                # GAS APIへ送信
                                success = append_sheet_data("T_Listing", records_to_save)
                                if success:
                                    st.success("✅ スプレッドシート（T_Listing）への追記保存が完了しました！")
                                    st.session_state.ocr_extracted_df = None
                                    st.session_state.ocr_active_platform = None
                                    time.sleep(2)
                                    st.rerun()
                                # 💡 エラー時は画面をリロードせずエラーを表示したまま停止します
                            else:
                                st.error("⚠️ append_sheet_data 関数が読み込めません。")
                        except Exception as save_err:
                            st.error(f"🚨 スプレッドシートへの保存時にエラーが発生しました: {save_err}")
                            
            with col_save2:
                if st.button("❌ キャンセル", width="stretch"):
                    st.session_state.ocr_extracted_df = None
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr style='margin: 10px 0 20px 0;'>", unsafe_allow_html=True)

    sub_listing_main.render(df_safe)


def render(df=None):
    if df is None:
        try:
            if load_sheet_data:
                df = load_sheet_data("T_Listing")
            else:
                df = pd.DataFrame()
        except Exception:
            df = pd.DataFrame()
    render_tab3_listing(df)