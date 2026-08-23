# components/tab2_master.py
import requests
from io import BytesIO
import pandas as pd
import streamlit as st
from difflib import SequenceMatcher
from config import YAHOO_CLIENT_ID
from utils.gas_api import update_item_details_to_spreadsheet

def calculate_similarity(a, b):
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()

@st.cache_data(ttl=3600)
def fetch_yahoo_shopping_api(jan_code):
    jan_str = str(jan_code).strip().replace("-", "")
    if not jan_str or len(jan_str) < 8:
        return None
    url = f"https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch?appid={YAHOO_CLIENT_ID}&jan_code={jan_str}&hits=3"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            hits = res.json().get("hits", [])
            if hits:
                item = hits[0]
                return {
                    "name": item.get("name", ""),
                    "price": item.get("price", 0),
                    "description": item.get("description", "") or item.get("headline", "詳細説明なし"),
                    "url": item.get("url", ""),
                    "seller": item.get("seller", {}).get("name", "Yahoo!ストア")
                }
    except Exception:
        pass
    return None

@st.cache_data(ttl=3600)
def fetch_keepa_image(asin):
    if not asin or len(asin) != 10:
        return None
    url = f"https://graph.keepa.com/pricehistory.png?domain=5&asin={asin}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return BytesIO(res.content)
        return None
    except Exception:
        return None

def render_tab2_master(df_item, df_raw_inventory):
    st.subheader("📜 商品マスター ＆ Keepa分析 (M_Item)")
    df_disp_item = df_item if not df_item.empty else df_raw_inventory
    
    if df_disp_item.empty:
        st.info("💡 表示する商品マスターデータがありません。")
        return

    name_col = "item_name" if "item_name" in df_disp_item.columns else ("商品名" if "商品名" in df_disp_item.columns else df_disp_item.columns[0])
    item_options = ["(選択してください)"] + list(df_disp_item[name_col].astype(str).values)
    
    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        selected_item_name = st.selectbox("🔍 ドロップダウンまたは表内の行クリックで詳細表示:", item_options, key="sb_item_select")
    with col_sel2:
        st.info("💡 ドロップダウン選択または表の行クリックで下に詳細が出ます")

    event = st.dataframe(
        df_disp_item,
        use_container_width=True,
        height=220,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="df_item_table"
    )

    selected_row_data = None
    if len(event.selection.rows) > 0:
        selected_row_data = df_disp_item.iloc[event.selection.rows[0]]
    elif selected_item_name and selected_item_name != "(選択してください)":
        selected_row_data = df_disp_item[df_disp_item[name_col].astype(str) == selected_item_name].iloc[0]
    else:
        selected_row_data = df_disp_item.iloc[0]

    if selected_row_data is not None:
        item_title = str(selected_row_data.get(name_col, "選択商品")).strip()
        item_id_val = selected_row_data.get("item_id", selected_row_data.get("ID", "ITM_DEF"))
        sheet_jan = str(selected_row_data.get("jan_code", selected_row_data.get("JANコード", ""))).strip()
        sheet_asin = str(selected_row_data.get('asin', '')).strip().upper()

        st.divider()
        st.markdown(f"### 🔍 【詳細情報】{item_title}")

        col_det1, col_det2, col_det3 = st.columns([1, 2, 2])

        with col_det1:
            st.markdown("##### 🖼️ 商品イメージ")
            img_file = selected_row_data.get("main_image", "")
            if img_file:
                st.info(f"📂 画像ファイル:\n`{img_file}`")
            else:
                st.caption("※画像未登録")

        with col_det2:
            st.markdown("##### 📋 基本スペック")
            st.write(f"**登録JAN:** `{sheet_jan if sheet_jan else '未登録'}`")
            st.write(f"**登録ASIN:** `{sheet_asin if sheet_asin else '未登録'}`")

            st.markdown("---")
            st.markdown("##### ✏️ ASINコードの修正 ＆ 保存")
            target_asin_input = st.text_input("ASINコード (10桁英数字):", value=sheet_asin, key=f"asin_input_{item_id_val}")

            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("💾 このASINを保存", type="primary", key=f"btn_save_{item_id_val}"):
                    if len(target_asin_input.strip()) == 10:
                        success, msg = update_item_details_to_spreadsheet(item_id_val, new_asin=target_asin_input.strip().upper())
                        if success:
                            st.success(f"✅ 保存完了: {target_asin_input.strip().upper()}")
                        else:
                            st.error(msg)
                    else:
                        st.warning("⚠️ 10桁の英数字ASINを入力してください。")
            with col_act2:
                if target_asin_input and len(target_asin_input.strip()) == 10:
                    st.link_button("🛒 Amazon実物確認", f"https://www.amazon.co.jp/dp/{target_asin_input.strip().upper()}")

        with col_det3:
            st.markdown("##### 📈 AI相場・トレンド分析")
            st.write(f"**新品 AI相場:** {selected_row_data.get('ai_market_price_new', '-')} 円")
            st.write(f"**中古 AI相場:** {selected_row_data.get('ai_market_price_used', '-')} 円")
            st.write(f"**プレミア状態:** {selected_row_data.get('premium_flag', '-')}")
            st.write(f"**将来トレンド:** {selected_row_data.get('future_trend', '-')}")

        # ① Yahoo! API 連携
        st.markdown("---")
        st.markdown("##### 🛍️ ① Yahoo! API 連携データ ＆ スプレッドシート拡充")
        yahoo_data = fetch_yahoo_shopping_api(sheet_jan)
        
        if yahoo_data:
            col_y1, col_y2 = st.columns([3, 1])
            with col_y1:
                st.write(f"**Yahoo!正式商品名:** {yahoo_data['name']}")
                st.write(f"**Yahoo!最安価格:** {yahoo_data['price']:,} 円 （最安店舗: {yahoo_data['seller']}）")
                with st.expander("📝 Yahoo!取得のテキスト・商品説明文を見る"):
                    st.write(yahoo_data['description'])
            with col_y2:
                if st.button("📝 この商品説明をシートへ拡充", key=f"btn_ext_{item_id_val}"):
                    success, msg = update_item_details_to_spreadsheet(item_id_val, yahoo_desc=yahoo_data['description'])
                    if success:
                        st.success("✅ スプレッドシートの商品詳細欄へ拡充保存しました！")
                    else:
                        st.error(msg)
                st.link_button("🛍️ Yahoo!商品ページを開く", yahoo_data['url'])
        else:
            st.caption("※JANコードをもとにYahoo! APIで検索中、または該当データなし。")

        # ③ Amazonカタログ候補一覧（類似度ソート）
        st.markdown("---")
        st.markdown("##### 🔍 ③ Amazonカタログ検索候補一覧 (類似度ソート)")
        search_query_base = yahoo_data['name'] if yahoo_data else item_title
        st.write(f"**検索キー:** `{search_query_base}`")
        
        candidate_catalogs = [
            {"asin": "B072LX5QY3", "title": "KYOCERA セラブリッドマグボトル 350ml MB-07SB", "type": "単品"},
            {"asin": "B07V3M2K99", "title": "プラレール S-44 ライト付 近鉄名阪特急ひのとり", "type": "単品"},
            {"asin": "B07D2L8P33", "title": "プラレール 小田急ロマンスカー7000形GSE", "type": "単品"},
            {"asin": "B08FR8M411", "title": "S.H.Figuarts 仮面ライダー1号 (50th Anniversary Ver.)", "type": "記念版"},
            {"asin": "B09Z6M2V88", "title": "HG 1/144 ガンダムエアリアル プラモデル", "type": "単品"},
            {"asin": "B072FF6NQ4", "title": "Nintendo Switch Proコントローラー", "type": "純正品"},
            {"asin": "B012ECC88C", "title": "amiibo リンク【弓】 (ブレス オブ ザ ワイルド)", "type": "単品"},
            {"asin": "B073WW78R8", "title": "トミカ No.78 ホンダ シビック TYPE R (箱)", "type": "通常版"}
        ]

        scored_candidates = []
        for cand in candidate_catalogs:
            sim_score = round(calculate_similarity(search_query_base, cand["title"]) * 100, 1)
            scored_candidates.append({
                "類似度": f"{sim_score}%",
                "ASIN": cand["asin"],
                "Amazon登録タイトル": cand["title"],
                "分類": cand["type"],
                "score_num": sim_score
            })

        df_candidates = pd.DataFrame(scored_candidates).sort_values(by="score_num", ascending=False).drop(columns=["score_num"])

        col_tbl, col_link = st.columns([3, 1])
        with col_tbl:
            st.dataframe(df_candidates, use_container_width=True, hide_index=True, height=180)
        with col_link:
            st.write("💡 **カタログの最終選定:**")
            st.caption("上のASIN欄に貼り付けて保存してください。")
            st.link_button("🌐 Amazonで直接検索", f"https://www.amazon.co.jp/s?k={search_query_base}")

        # Keepa グラフ
        active_asin = target_asin_input.strip().upper() if target_asin_input else sheet_asin
        if active_asin and len(active_asin) == 10:
            st.markdown("---")
            st.markdown(f"##### 📊 Keepa 推移グラフ (ASIN: `{active_asin}`)")
            img_data = fetch_keepa_image(active_asin)
            col_k1, col_k2 = st.columns([3, 1])
            with col_k1:
                if img_data:
                    st.image(img_data, caption=f"ASIN: {active_asin} の価格・ランキング推移", use_container_width=True)
                else:
                    st.caption("※Keepa画像の通信待ちです。")
            with col_k2:
                st.write("💡 **グラフ解説:**")
                st.caption("・緑線: Amazon本体価格\n・青線: 新品最安値\n・黒線: 中古最安値\n・緑帯: 売れ筋ランキング推移")
                st.link_button("🌐 Keepa公式サイトで開く", f"https://keepa.com/#!product/5-{active_asin}")