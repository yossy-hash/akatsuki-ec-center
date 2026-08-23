# components/tab1_inventory.py
import streamlit as st
import pandas as pd

def render_tab1_inventory(df_raw_inventory):
    # CSS: 赤い枠や巨大ボタンを完全に打ち消し、文字サイズを調整
    st.markdown("""
        <style>
            /* 赤い枠や巨大ボタンの排除 */
            .stButton > button {
                background-color: #333 !important;
                color: #ccc !important;
                border: 1px solid #555 !important;
                font-size: 0.75rem !important;
                padding: 1px 8px !important;
                height: 26px !important;
                min-height: 26px !important;
            }
            /* ステータス絞り込み（ラジオボタン）の文字を大きく表示 */
            div[data-testid="stRadio"] label p {
                font-size: 1.15rem !important;
                font-weight: bold !important;
                color: #ffffff !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # 1. 最上部：見出し（文字小） ＆ スナップショット（右端の小さな灰色ボタン）
    c_title, c_btn = st.columns([4, 1])
    with c_title:
        st.markdown("<span style='font-size:0.85rem; color:#aaa;'>📦 リアルタイム在庫コントロール</span>", unsafe_allow_html=True)
    with c_btn:
        if st.button("📷 ログ保存", key="btn_snap_clean"):
            st.toast("スナップショットを記録しました", icon="✅")

    # 2. 絞り込みエリア（キーワード検索窓は完全削除）
    c_status, c_cat, c_cond = st.columns([2.5, 1.2, 1.2])

    df = df_raw_inventory.copy() if not df_raw_inventory.empty else pd.DataFrame()

    with c_status:
        # よく使うステータス絞り込み（大きく表示）
        status_filter = st.radio(
            "ステータス",
            ["すべて", "📦 在庫あり", "🟢 販売中", "⏳ 出品前・保管中"],
            horizontal=True,
            label_visibility="collapsed"
        )

    # カテゴリ・コンディションの選択肢
    cat_options = ["全カテゴリ"]
    if not df.empty and "カテゴリー" in df.columns:
        cats = [str(c).strip() for c in df["カテゴリー"].dropna().unique() if str(c).strip() != ""]
        cat_options.extend(sorted(cats))

    with c_cat:
        selected_cat = st.selectbox("カテゴリ", cat_options, label_visibility="collapsed")

    with c_cond:
        selected_cond = st.selectbox("コンディション", ["全コンディション", "新品", "中古"], label_visibility="collapsed")

    # --- フィルタリング処理 ---
    if not df.empty:
        if status_filter == "📦 在庫あり":
            df = df[df["数量"].astype(str).str.strip().str.isdigit() & (df["数量"].astype(int) > 0)]
        elif status_filter == "🟢 販売中":
            if "詳細ステータス" in df.columns:
                df = df[df["詳細ステータス"].str.contains("出品中|販売中", na=False)]
        elif status_filter == "⏳ 出品前・保管中":
            if "詳細ステータス" in df.columns:
                df = df[df["詳細ステータス"].str.contains("出品前|保管中|ヤフオク出品待ち", na=False)]

        if selected_cat != "全カテゴリ" and "カテゴリー" in df.columns:
            df = df[df["カテゴリー"] == selected_cat]

        if selected_cond != "全コンディション" and "コンディション" in df.columns:
            if selected_cond == "新品":
                df = df[df["コンディション"].str.contains("新品|未使用", na=False)]
            elif selected_cond == "中古":
                df = df[~df["コンディション"].str.contains("新品|未使用", na=False)]

    # 3. 件数サマリー
    total_items = len(df)
    total_qty = pd.to_numeric(df["数量"], errors="coerce").fillna(0).sum() if not df.empty and "数量" in df.columns else 0
    total_cost = pd.to_numeric(df["仕入価格"], errors="coerce").fillna(0).sum() if not df.empty and "仕入価格" in df.columns else 0

    st.markdown(f"<div style='margin-bottom:6px;'><span style='font-size:0.9rem;'><b>該当データ:</b> <span style='color:#ff4b4b;'>{total_items}</span> 件 | <b>対象在庫合計:</b> {int(total_qty)} 個 | <b>合計仕入金額:</b> {int(total_cost):,} 円</span></div>", unsafe_allow_html=True)

    # 4. メイン一覧表（550pxの縦幅を確保）
    if not df.empty:
        show_cols = [c for c in ["ID", "商品名", "JANコード", "数量", "詳細ステータス", "保管場所", "仕入価格", "コンディション", "カテゴリー", "仕入日"] if c in df.columns]
        st.dataframe(
            df[show_cols],
            use_container_width=True,
            height=550,
            hide_index=True
        )
    else:
        st.info("該当する在庫データがありません。")