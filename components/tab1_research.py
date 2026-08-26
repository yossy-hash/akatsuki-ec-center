import streamlit as st
import pandas as pd
from datetime import datetime
from utils.gas_api import load_sheet_data, append_sheet_data

SHEET_ITEM = "M_Item"

def render_tab1_research():
    st.title("🔍 マルチプラットフォーム・リサーチ＆ストック")
    st.write("各プラットフォーム・Keepa・セラー情報からリサーチを行い、見込み商品を『M_Item』へ保存します。")

    # 既存の保存済み商品マスター（M_Item）を読み込み
    df_items = load_sheet_data(SHEET_ITEM)

    # =========================================================================
    # 【上半分】マルチリサーチ・データ収集ゾーン
    # =========================================================================
    st.markdown("### 1. 情報収集＆相場分析")
    
    tab_keepa, tab_ebay, tab_jp, tab_seller = st.tabs([
        "📈 Keepa / Amazon", 
        "🌏 eBay / テラピーク", 
        "🔨 ヤフオク・メルカリ・オークタウン", 
        "👤 マーク中セラー追跡"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: Keepa / Amazon
    # -------------------------------------------------------------------------
    with tab_keepa:
        col_k1, col_k2 = st.columns([1, 2])
        with col_k1:
            k_jan = st.text_input("JAN / ASIN / 商品ID", value="4901301407764", key="k_jan")
            k_title = st.text_input("商品名（仮）", value="花王 UVカットローション 3個セット", key="k_title")
            k_supplier = st.text_input("仕入れ候補・購入先メモ", value="マツモトキヨシ 名古屋駅前店", key="k_supplier")
            k_buy_price = st.number_input("想定仕入額 (円)", value=2100, step=100, key="k_buy")
            k_sell_price = st.number_input("Amazon想定販売額 (円)", value=3980, step=100, key="k_sell")
            
            k_profit = int(k_sell_price - k_buy_price - (k_sell_price * 0.15) - 500)
            st.metric("見込み純利益 (概算)", f"￥{k_profit:,}")

        with col_k2:
            st.caption("📷 Keepaデータ＆グラフプレビュー")
            st.info("📈 **[Keepa Data]** 現在最安値: ¥3,980 | 過去90日平均BSR: 1,450位 | FBA出品者数: 4名")
            st.markdown("---")
            if st.button("➕ この商品を『M_Item』へストック保存 (Amazon向け)", type="primary", key="save_keepa"):
                now_str = datetime.now().strftime("%Y%m%d%H%M%S")
                new_item = {
                    "item_id": f"ITM-{now_str[-6:]}",
                    "jan_asin": k_jan,
                    "item_name": k_title,
                    "category": "ドラッグストア",
                    "supplier": k_supplier,
                    "target_platform": "Amazon",
                    "purchase_status": "購入前",
                    "est_purchase_price": k_buy_price,
                    "est_sale_price": k_sell_price,
                    "est_profit": k_profit,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if append_sheet_data(SHEET_ITEM, [new_item]):
                    st.success("M_Itemへ正常保存しました！")
                    st.rerun()
                else:
                    st.error("保存に失敗しました。")

    # -------------------------------------------------------------------------
    # TAB 2: eBay / テラピーク
    # -------------------------------------------------------------------------
    with tab_ebay:
        col_e1, col_e2 = st.columns([1, 2])
        with col_e1:
            e_id = st.text_input("商品識別コード / 型番", value="NIKON-D750-BODY", key="e_id")
            e_title = st.text_input("英語商品名 / 型番", value="Nikon D750 Body Excellent+", key="e_title")
            e_supplier = st.text_input("仕入れ候補 URL / 店舗名", value="ヤフオク (Seller: camera_shop)", key="e_supplier")
            e_buy_price = st.number_input("メルカリ/ヤフオク仕入想定額 (円)", value=38000, step=1000, key="e_buy")
            e_sell_usd = st.number_input("eBay想定販売額 ($)", value=380.0, step=10.0, key="e_sell")
            e_rate = st.number_input("想定為替レート (円/$)", value=150.0, step=1.0, key="e_rate")
            
            e_sell_jpy = int(e_sell_usd * e_rate)
            e_profit = int(e_sell_jpy - e_buy_price - (e_sell_jpy * 0.15) - 3000)
            st.metric("見込み純利益 (概算)", f"￥{e_profit:,} (売上: ￥{e_sell_jpy:,})")

        with col_e2:
            st.caption("🌏 テラピーク・相場サマリー")
            st.info("📊 **[eBay SOLD 相場]** 直近90日落札平均: $385.00 | 落札率: 78% | 売れ筋コンディション: Excellent+")
            st.markdown("---")
            if st.button("➕ この商品を『M_Item』へストック保存 (eBay向け)", type="primary", key="save_ebay"):
                now_id = datetime.now().strftime("%Y%m%d%H%M%S")
                new_item = {
                    "item_id": f"ITM-{now_id[-6:]}",
                    "jan_asin": e_id,
                    "item_name": e_title,
                    "category": "中古カメラ",
                    "supplier": e_supplier,
                    "target_platform": "eBay",
                    "purchase_status": "購入前",
                    "est_purchase_price": e_buy_price,
                    "est_sale_price": e_sell_jpy,
                    "est_profit": e_profit,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if append_sheet_data(SHEET_ITEM, [new_item]):
                    st.success("M_Itemへ正常保存しました！")
                    st.rerun()
                else:
                    st.error("保存に失敗しました。")

    # -------------------------------------------------------------------------
    # TAB 3: ヤフオク・メルカリ・オークタウン
    # -------------------------------------------------------------------------
    with tab_jp:
        col_j1, col_j2 = st.columns([1, 2])
        with col_j1:
            j_title = st.text_input("国内検索キーワード", value="ニコン D750 ボディ 美品", key="j_title")
            j_buy_limit = st.number_input("仕入れ上限価格 (円)", value=32000, step=1000, key="j_limit")
            st.caption("💡 この価格以下でオークション落札/フリマ購入できれば利益確定")

        with col_j2:
            st.write("🔗 **外部ツール・相場確認リンク**")
            st.markdown("- [オークファンで相場確認](https://aucfan.com/)")
            st.markdown("- [オークタウンで一括出品準備](https://auktown.jp/)")
            st.markdown("- [メルカリで検索](https://jp.mercari.com/)")

    # -------------------------------------------------------------------------
    # TAB 4: セラー追跡
    # -------------------------------------------------------------------------
    with tab_seller:
        st.subheader("👤 マーク中神セラー・追跡リスト")
        col_s1, col_s2 = st.columns([1, 1])
        with col_s1:
            st.selectbox("ターゲットセラー選択", [
                "【eBay】Camera_Japan_Store (評価: 1,500)", 
                "【Amazon】ドラッグストア格安堂 (評価: 98%)",
                "【メルカリ】カメラ専門☆即購入OK"
            ])
            st.button("🔍 選択セラーの最新出品を取得 (ダミー)", key="btn_fetch_seller")
        with col_s2:
            st.text_input("新規セラーID/URLを追加メモ", placeholder="Seller IDを入力...", key="new_seller")
            st.button("➕ セラーを記憶", key="btn_save_seller")

    # =========================================================================
    # 【下半分】気になるアイテム保存リスト（M_Item ワークスペース）
    # =========================================================================
    st.markdown("---")
    st.markdown("### 2. 気になるアイテム保存リスト (`M_Item`)")
    st.write("仕入れ候補・価格・購入状況（購入前/予定/済）を統合管理するワークスペースです。")

    if not df_items.empty:
        # カラムが存在しない場合の初期補正
        if "purchase_status" not in df_items.columns:
            df_items["purchase_status"] = "購入前"
        if "jan_asin" not in df_items.columns:
            df_items["jan_asin"] = "-"

        disp_cols = [
            "item_id", 
            "jan_asin", 
            "item_name", 
            "supplier", 
            "purchase_status", 
            "est_purchase_price", 
            "est_sale_price", 
            "est_profit", 
            "target_platform"
        ]
        available_cols = [c for c in disp_cols if c in df_items.columns]

        st.dataframe(
            df_items[available_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "item_id": "管理ID",
                "jan_asin": "JAN/ASIN/固有ID",
                "item_name": "商品名",
                "supplier": "仕入れ候補（店舗/URL）",
                "purchase_status": st.column_config.SelectboxColumn(
                    "購入ステータス",
                    options=["購入前", "購入予定", "購入済"],
                    required=True
                ),
                "est_purchase_price": st.column_config.NumberColumn("想定仕入額", format="￥%d"),
                "est_sale_price": st.column_config.NumberColumn("想定販売額", format="￥%d"),
                "est_profit": st.column_config.NumberColumn("見込み純利益", format="￥%d"),
                "target_platform": "販売予定先"
            }
        )
    else:
        st.info("現在保存されているリサーチ候補はありません。上部のタブから商品を追加してください。")