import streamlit as st
import pandas as pd
from utils.gas_api import load_sheet_data, update_sheet_data

SHEET_TX = "T_Transactions"
SHEET_SALE = "T_Sale"

def render_tab11_transactions():
    st.title("📑 整備済み取引データ一覧（仕訳帳・売上帳）")
    st.write("取り込み・クレンジング済みの明細を閲覧・編集・確定できます。")

    # 画面上部でデータドメイン（資金・経費 vs EC売上）を選択
    view_mode = st.radio(
        "表示する帳簿を選択",
        ["🏦 資金・経費明細 (T_Transactions)", "🛍️ EC売上明細 (T_Sale)"],
        horizontal=True
    )

    sheet_name = SHEET_TX if "資金・経費" in view_mode else SHEET_SALE
    df_data = load_sheet_data(sheet_name)

    if df_data.empty:
        st.info(f"[{sheet_name}] に登録されているデータはまだありません。CSV取り込み画面から登録してください。")
        return

    # ----------------------------------------------------
    # 1. 資金・経費明細 (T_Transactions) の表示・編集ロジック
    # ----------------------------------------------------
    if sheet_name == SHEET_TX:
        df_data["month"] = df_data["date"].astype(str).str.slice(0, 7)
        df_data["amount"] = pd.to_numeric(df_data["amount"], errors="coerce").fillna(0).astype(int)

        # 絞り込みフィルター
        col1, col2, col3 = st.columns(3)
        with col1:
            months = sorted([m for m in df_data["month"].unique() if m and m != "nan"], reverse=True)
            selected_month = st.selectbox("対象月で絞り込み", ["すべて"] + months)
        with col2:
            sources = sorted([s for s in df_data["source"].unique() if s and s != "nan"])
            selected_source = st.selectbox("データ種別で絞り込み", ["すべて"] + sources)
        with col3:
            categories = sorted([c for c in df_data["category"].unique() if c and c != "nan"]) if "category" in df_data.columns else []
            selected_cat = st.selectbox("勘定科目で絞り込み", ["すべて"] + categories)

        # フィルタリング処理
        df_filtered = df_data.copy()
        if selected_month != "すべて":
            df_filtered = df_filtered[df_filtered["month"] == selected_month]
        if selected_source != "すべて":
            df_filtered = df_filtered[df_filtered["source"] == selected_source]
        if selected_cat != "すべて" and "category" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["category"] == selected_cat]

        st.markdown("---")

        # 集計サマリー
        total_count = len(df_filtered)
        total_amount = df_filtered["amount"].sum()

        m1, m2 = st.columns(2)
        m1.metric("表示中の取引件数", f"{total_count} 件")
        m2.metric("合計金額", f"￥{total_amount:,}")

        st.subheader("📋 取引明細（編集可能）")
        st.caption("💡 勘定科目や変換後名称はセルを直接ダブルクリックして変更できます。変更後は下の「更新」ボタンを押してください。")

        # 表示用・編集用カラムの設定
        disp_cols = ["transaction_id", "date", "source", "original_name", "clean_name", "category", "amount", "notes"]
        available_cols = [c for c in disp_cols if c in df_filtered.columns]

        # st.data_editor を使用して画面上での編集を可能にする
        edited_df = st.data_editor(
            df_filtered[available_cols],
            use_container_width=True,
            hide_index=True,
            disabled=["transaction_id", "date", "source", "original_name", "amount"], # IDや金額など重要項目は編集不可
            column_config={
                "transaction_id": "取引ID",
                "date": "取引日",
                "source": "種別",
                "original_name": "変換前名称",
                "clean_name": "変換後名称（編集可）",
                "category": st.column_config.SelectboxColumn(
                    "勘定科目（編集可）",
                    options=["物販売上", "給与収入", "投資・その他", "仕入高", "旅費交通費", "通信費", "接待交際費", "消耗品費", "会議費", "地代家賃", "広告宣伝費", "資金移動・振替", "未分類"],
                    required=True
                ),
                "amount": st.column_config.NumberColumn("金額(円)", format="￥%d"),
                "notes": "備考（編集可）"
            },
            key="tx_editor"
        )

        # 変更保存ボタン
        if st.button("💾 変更内容をスプレッドシートへ保存", type="primary"):
            with st.spinner("更新データを保存中..."):
                # 元の df_data に編集結果を反映
                for idx, row in edited_df.iterrows():
                    tx_id = row["transaction_id"]
                    match_idx = df_data[df_data["transaction_id"] == tx_id].index
                    if not match_idx.empty:
                        df_data.loc[match_idx[0], "clean_name"] = row["clean_name"]
                        df_data.loc[match_idx[0], "category"] = row["category"]
                        df_data.loc[match_idx[0], "notes"] = row["notes"]

                # 一括更新 API の呼び出し
                update_records = df_data.drop(columns=["month"], errors="ignore").to_dict(orient="records")
                res = update_sheet_data(SHEET_TX, update_records)
                if res:
                    st.success("🎉 スプレッドシートの更新が完了しました！")
                    st.rerun()
                else:
                    st.error("更新処理に失敗しました。")

    # ----------------------------------------------------
    # 2. EC売上明細 (T_Sale) の表示ロジック
    # ----------------------------------------------------
    else:
        df_data["sold_price"] = pd.to_numeric(df_data["sold_price"], errors="coerce").fillna(0).astype(int)
        
        st.markdown("---")
        total_count = len(df_data)
        total_sales = df_data["sold_price"].sum()

        m1, m2 = st.columns(2)
        m1.metric("総販売件数", f"{total_count} 件")
        m2.metric("総売上金額", f"￥{total_sales:,}")

        st.subheader("🛍️ EC売上データ一覧")
        
        disp_cols = ["sale_id", "listing_id", "item_id", "sale_date", "sold_price", "shipping_fee_paid", "is_returned"]
        available_cols = [c for c in disp_cols if c in df_data.columns]

        st.dataframe(
            df_data[available_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "sale_id": "販売ID",
                "listing_id": "出品ID",
                "item_id": "商品ID",
                "sale_date": "販売日時",
                "sold_price": st.column_config.NumberColumn("販売価格", format="￥%d"),
                "shipping_fee_paid": st.column_config.NumberColumn("受領送料", format="￥%d"),
                "is_returned": "返品フラグ"
            }
        )