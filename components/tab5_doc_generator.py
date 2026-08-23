import streamlit as st
import pandas as pd
import random
from utils import ai_yahoo_api

def render(df_inventory: pd.DataFrame = None):
    """出品用Documents作成画面（トレンド最上段配置・スマートレイアウト版）"""
    st.markdown('<p class="header-title">📄 出品用Documents作成（AIアシスタント）</p>', unsafe_allow_html=True)

    if df_inventory is None or df_inventory.empty:
        try:
            from utils.gas_api import load_sheet_data
            df_inventory = load_sheet_data("EC_Inventory")
        except Exception:
            df_inventory = pd.DataFrame()

    if "last_selected_item" not in st.session_state:
        st.session_state["last_selected_item"] = None

    # --- 1行目: 商品選択 ＆ 赤いGeminiボタン ---
    col_sel, col_btn = st.columns([7, 3])
    
    with col_sel:
        if not df_inventory.empty and "商品名" in df_inventory.columns:
            item_list = df_inventory["商品名"].dropna().tolist()
            selected_item_name = st.selectbox("📦 対象商品を選択してください", item_list, key="doc_gen_item_select")
            
            selected_row = df_inventory[df_inventory["商品名"] == selected_item_name].iloc[0]
            current_jan = selected_row.get("JANコード", selected_row.get("jan_code", None))
        else:
            selected_item_name = "KYOCERA CERABRID セラブリッド マグボトル 350ml ローズピンク"
            current_jan = "4960664846917"
            st.selectbox("📦 対象商品を選択してください", [selected_item_name], key="doc_gen_item_select_demo")

    if st.session_state["last_selected_item"] != selected_item_name:
        with st.spinner("🔵 商品の変更を検知しました。Yahoo! APIからデータを自動取得中..."):
            yahoo_result = ai_yahoo_api.search_yahoo_shopping(jan_code=current_jan, item_name=selected_item_name)
            
            if yahoo_result.get("found"):
                st.session_state["yahoo_data"] = yahoo_result
                st.toast(f"✅ Yahoo! APIデータ自動取得成功: {yahoo_result['title']}")
            else:
                st.warning(yahoo_result.get("message", "Yahoo! APIで検索できませんでした。"))
                st.session_state["yahoo_data"] = {}
                
            st.session_state["generated_docs"] = {}
            st.session_state["last_selected_item"] = selected_item_name
            st.rerun() 

    with col_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        generate_btn = st.button("🔴 Geminiで各モール最適化文を生成", type="primary", use_container_width=True)

    if generate_btn:
        y_data_current = st.session_state.get("yahoo_data", {})
        with st.spinner("🔴 Gemini AIが文章を生成中..."):
            ai_input_title = y_data_current.get("title", selected_item_name)
            ai_input_price = y_data_current.get("price", 3500)
            ai_input_cat = y_data_current.get("category", "未分類")
            
            ai_docs = ai_yahoo_api.generate_listing_docs_with_gemini(
                {"title": ai_input_title, "price": ai_input_price, "category": ai_input_cat}
            )
            
            if "error" in ai_docs:
                st.error(f"🚨 Gemini APIエラーが発生しました: {ai_docs['error']}")
            else:
                st.session_state["generated_docs"] = ai_docs
                st.success("✨ AI最適化文の生成が完了しました！")

    # --- 数値・価格データの事前計算 ---
    y_data = st.session_state.get("yahoo_data", {})
    a_docs = st.session_state.get("generated_docs", {})
    
    raw_price = y_data.get('price', 3500)
    try:
        base_price = int(raw_price)
    except:
        base_price = 3500
        
    amz_price = int(base_price * 1.32) # デモ用プレ値計算
    diff = amz_price - base_price
    ratio = int((amz_price / base_price) * 100) if base_price > 0 else 100

    # 🌟 結論ファースト：最上段に1行でコンパクトに配置するAIトレンド予測 🌟
    trend_banner_html = f"""
    <div style='background: linear-gradient(90deg, #1e3a8a 0%, #1e40af 100%); border-left: 4px solid #60a5fa; padding: 8px 15px; border-radius: 4px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); display: flex; align-items: center; color: #e5e7eb; font-size: 0.95em;'>
        <span style='font-size: 1.2em; margin-right: 10px;'>🤖</span>
        <b>AIトレンド予測：</b>&nbsp; メーカー完売傾向。定価を {ratio}% 上回るプレミアム価格で推移中。今後さらに相場が高騰する可能性大。 (*SAMPLE)
    </div>
    """
    st.markdown(trend_banner_html, unsafe_allow_html=True)

    # 🌟 対象商品名の遠慮ない巨大化（アイキャッチ）🌟
    st.markdown(f"""
    <div style='padding: 0px 0 15px 0;'>
        <div style='font-size: 0.95em; color: #9CA3AF; font-weight: bold; margin-bottom: 5px;'>📦 分析・出力対象</div>
        <div style='font-size: 1.8em; font-weight: 900; color: #60A5FA; line-height: 1.4; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);'>
            {selected_item_name}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 変数の準備（マトリクス用） ---
    ym = "🔵" if y_data else ""  
    am = "🔴" if a_docs else ""  

    disp_title = y_data.get('title', selected_item_name)
    disp_cat = y_data.get('category', '未取得')
    disp_price = f"¥{base_price:,}" if y_data else "¥3,500（未取得）"
    
    img_url = y_data.get('image_url', '')
    def get_img_html(url):
        if url:
            return f'<img src="{url}" style="width:110px; height:auto; border-radius:6px; box-shadow: 0 2px 5px rgba(0,0,0,0.5);">'
        return '<span style="color:#888;">🚫 画像なし</span>'
    img_html = get_img_html(img_url)

    def format_text(text):
        if not isinstance(text, str):
            text = str(text)
        text = text.replace("\\n", "\n")
        return text.replace("\n", "<br>")

    ai_mercari = format_text(a_docs.get('メルカリ', '（赤いボタンを押すとAIが文章を作成します）'))
    ai_amazon = format_text(a_docs.get('Amazon', '（赤いボタンを押すとAIが文章を作成します）'))
    ai_yahoo = format_text(a_docs.get('ヤフオク', '（赤いボタンを押すとAIが文章を作成します）'))
    ai_ebay = format_text(a_docs.get('eBay', '(Press button to generate)'))

    # --- 2行目: 出品下書きマトリクス ---
    st.markdown(f"**【1. 出品下書きマトリクス】**")
    st.caption("※ 🔵 = Yahoo! API自動取得データ / 🔴 = Gemini AI生成データ")

    html_table = f"""
    <style>
    .doc-matrix {{ width: 100%; border-collapse: collapse; color: #E0E0E0; font-size: 14px; background-color: #1E1E1E; }}
    .doc-matrix th, .doc-matrix td {{ border: 1px solid #444; padding: 12px; vertical-align: top; line-height: 1.6; word-wrap: break-word; }}
    .doc-matrix th {{ background-color: #2D2D2D; font-weight: bold; width: 12%; text-align: left; }}
    .doc-matrix td {{ width: 22%; }}
    .doc-matrix .ai-text {{ color: #FF9999; }}
    .doc-matrix .api-text {{ color: #99CCFF; }}
    </style>
    <table class="doc-matrix">
      <tr>
        <th>項目</th>
        <th>メルカリ</th>
        <th>Amazon</th>
        <th>ヤフオク</th>
        <th>eBay</th>
      </tr>
      <tr>
        <th>📷 写真</th>
        <td>{img_html}</td>
        <td>{img_html}</td>
        <td>{img_html}</td>
        <td>{img_html}</td>
      </tr>
      <tr>
        <th>📝 タイトル</th>
        <td><span class="ai-text">{am} 【新品】{disp_title}</span></td>
        <td><span class="api-text">{ym} {disp_title}</span></td>
        <td><span class="ai-text">{am} 【送料無料】{disp_title}</span></td>
        <td><span class="ai-text">{am} Japan Import: {disp_title}</span></td>
      </tr>
      <tr>
        <th>🏷️ ジャンル</th>
        <td><span class="api-text">{ym} {disp_cat}</span></td>
        <td><span class="api-text">{ym} {disp_cat}</span></td>
        <td><span class="api-text">{ym} {disp_cat}</span></td>
        <td><span class="api-text">{ym} {disp_cat}</span></td>
      </tr>
      <tr>
        <th>✨ 状態</th>
        <td>新品、未使用</td>
        <td>新品</td>
        <td>中古（ほぼ新品）</td>
        <td>Brand New</td>
      </tr>
      <tr>
        <th>💰 希望価格</th>
        <td><span class="api-text">{ym} {disp_price}</span></td>
        <td><span class="api-text">{ym} {disp_price}</span></td>
        <td><span class="api-text">{ym} {disp_price}</span></td>
        <td><span class="api-text">{ym} $29.99 (予想)</span></td>
      </tr>
      <tr>
        <th>📄 説明文</th>
        <td><span class="ai-text">{am} {ai_mercari}</span></td>
        <td><span class="ai-text">{am} {ai_amazon}</span></td>
        <td><span class="ai-text">{am} {ai_yahoo}</span></td>
        <td><span class="ai-text">{am} {ai_ebay}</span></td>
      </tr>
    </table>
    """
    st.markdown(html_table, unsafe_allow_html=True)

    # --- 3行目: 視覚化ダッシュボード ---
    st.markdown("<hr style='margin: 20px 0 10px 0;'>", unsafe_allow_html=True)
    st.markdown(f"**【2. リアルタイム市場リサーチ ＆ 競合分析】**")

    # プレミアム率メーター
    bar_width_pct = min(ratio / 2, 100) 
    bar_color = "linear-gradient(90deg, #3b82f6, #4ade80)" if ratio <= 100 else "linear-gradient(90deg, #3b82f6, #4ade80 50%, #fbbf24 75%, #ef4444 100%)"
        
    gauge_html = f"""
    <div style="margin-top: 15px; margin-bottom: 50px; padding: 0 15px;">
        <div style="width: 100%; background-color: #252836; border-radius: 8px; position: relative; height: 32px; border: 1px solid #363b4e; box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);">
            <div style="width: {bar_width_pct}%; background: {bar_color}; height: 100%; border-radius: 7px; transition: width 1s ease-in-out;"></div>
            <div style="position: absolute; left: 50%; top: -6px; bottom: -6px; width: 3px; background-color: #ffffff; z-index: 10; border-radius: 2px; box-shadow: 0 0 5px rgba(255,255,255,0.8);"></div>
            <div style="position: absolute; right: 15px; top: 4px; color: #ffffff; font-weight: 800; font-size: 15px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">現在: ¥{amz_price:,} ({ratio}%)</div>
            <div style="position: absolute; left: 0%; top: 38px; transform: translateX(0%); color: #9ca3af; font-size: 12px; font-weight: bold;">0%</div>
            <div style="position: absolute; left: 25%; top: 38px; transform: translateX(-50%); color: #9ca3af; font-size: 12px;">50%</div>
            <div style="position: absolute; left: 50%; top: 38px; transform: translateX(-50%); color: #e5e7eb; font-size: 13px; font-weight: bold; background: #1f2937; padding: 2px 8px; border-radius: 4px; border: 1px solid #4b5563;">100% (定価)</div>
            <div style="position: absolute; left: 75%; top: 38px; transform: translateX(-50%); color: #9ca3af; font-size: 12px;">150%</div>
            <div style="position: absolute; left: 100%; top: 38px; transform: translateX(-100%); color: #ef4444; font-size: 12px; font-weight: bold;">200% MAX</div>
        </div>
    </div>
    """
    st.markdown(gauge_html, unsafe_allow_html=True)

    # 🌟 メトリクス（数値自体に *SAMPLE を付与してスッキリ化） 🌟
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric(label="🏷️ 新品時メーカー定価", value=f"¥{base_price:,}")
    with col_m2:
        st.metric(label="📦 Amazon最安値 (現在)", value=f"¥{amz_price:,}", delta=f"+¥{diff:,} (プレ値)", delta_color="normal")
    with col_m3:
        st.metric(label="📊 Keepaランキング", value="8,420位 (*SAMPLE)", delta="📈 上昇トレンド", delta_color="inverse")
    with col_m4:
        st.metric(label="⏳ 発売経過", value="約1年6ヶ月 (*SAMPLE)", delta="廃盤・品薄の可能性", delta_color="off")

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    col_chart, col_status = st.columns([6, 4])
    
    with col_chart:
        st.markdown("<div style='font-size:0.85em; color:#9ca3af; margin-bottom:5px;'>📈 過去30日間の価格推移 (*SAMPLE / Keepa予測モック)</div>", unsafe_allow_html=True)
        dates = pd.date_range(end=pd.Timestamp.today(), periods=30)
        trend_prices = [base_price + int((i/30)*diff) + random.randint(-150, 150) for i in range(30)]
        df_chart = pd.DataFrame({"Amazonカート価格 (円)": trend_prices}, index=dates)
        st.line_chart(df_chart, height=180, use_container_width=True)

    with col_status:
        st.markdown("<div style='font-size:0.85em; color:#9ca3af; margin-bottom:5px;'>🚨 各ECモール在庫状況 (*SAMPLE)</div>", unsafe_allow_html=True)
        # 🌟 1行にまとめたスマートな在庫状況パネル 🌟
        st.markdown(f"""
        <div style='background-color: #1e1e1e; border: 1px dashed #444; padding: 18px 10px; border-radius: 8px; opacity: 0.8; display: flex; flex-wrap: wrap; justify-content: center; gap: 15px; font-size: 0.9em;'>
            <div><span style='color: #4ADE80; font-weight: bold;'>🟢 メルカリ</span>: 在庫あり (¥{base_price:,}〜)</div>
            <div style='color: #555;'>|</div>
            <div><span style='color: #FBBF24; font-weight: bold;'>🟠 ヤフオク</span>: 残りわずか (¥{int(base_price*0.85):,})</div>
            <div style='color: #555;'>|</div>
            <div><span style='color: #F87171; font-weight: bold;'>🔴 Amazon</span>: 枯渇気味 (FBA: 3名)</div>
        </div>
        """, unsafe_allow_html=True)

    # --- 4行目: 参照用詳細データ（コピペ用） ---
    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
    st.markdown("**📋 商品スペック・詳細データ（出品・発送時 参照用）**")
    st.caption("※ 説明文の追記や、発送時のサイズ確認などにご活用ください。セルをクリックでコピー可能です。")
    
    spec_data = {
        "項目": [
            "🔢 JANコード / ASIN",
            "📏 本体サイズ (WxDxH)",
            "⚖️ 重量 (本体 / 発送時)",
            "📦 梱包サイズ",
            "🏢 メーカー / ブランド"
        ],
        "詳細情報": [
            f"JAN: {current_jan if current_jan else '取得不可'} ｜ ASIN: B08XXXX123 (*SAMPLE)",
            "41.0 cm × 7.0 cm × 4.0 cm (*SAMPLE)",
            "約 280g (梱包時推定 350g) (*SAMPLE)",
            "60サイズ（ダンボール梱包・宅急便コンパクト要確認）",
            "KYOCERA / タカラトミー 等 (*SAMPLE)"
        ]
    }
    
    st.dataframe(
        pd.DataFrame(spec_data),
        use_container_width=True,
        hide_index=True,
        height=210
    )

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # --- アクションボタン ---
    c_exp1, c_exp2 = st.columns([5, 5])
    with c_exp1:
        st.button("📋 各モール用テキストを一括コピー", key="btn_copy_docs", use_container_width=True)
    with c_exp2:
        st.button("💾 スプレッドシートへ下書き保存", key="btn_save_docs", use_container_width=True)