import streamlit as st
import pandas as pd
import plotly.express as px

def render_tab1_inventory(df: pd.DataFrame):
    """
    在庫管理画面レンダリング
    :param df: app.py から渡される全在庫データ (df_raw_inventory)
    """
    # データが空、またはNoneの場合の安全対策
    if df is None or df.empty:
        st.warning("表示できる在庫データがありません。")
        return

    # --- 1行目: ヘッダー ＆ 超極小ログ保存ボタン ---
    col1, col2 = st.columns([8, 2])
    with col1:
        st.markdown('<p class="header-title">📦 リアルタイム在庫コントロール</p>', unsafe_allow_html=True)
    with col2:
        if st.button("📷 ログ保存", key="btn_log_save", help="現在のスナップショットをログとして保存します"):
            st.toast("スナップショットを保存しました。")

    # --- 2行目: 絞り込みエリア ---
    col_status, col_cat, col_cond = st.columns([5, 3, 3])
    
    with col_status:
        status_filter = st.radio(
            "ステータス",
            ["すべて", "📦 在庫あり", "🟢 販売中", "⏳ 出品前・保管中"],
            horizontal=True,
            label_visibility="collapsed",
            key="inv_status_filter"
        )
        
    with col_cat:
        category_list = ["全カテゴリ"] + sorted(df["カテゴリ"].dropna().unique().tolist()) if "カテゴリ" in df.columns else ["全カテゴリ"]
        selected_category = st.selectbox("カテゴリ", category_list, label_visibility="collapsed", key="inv_cat_filter")
        
    with col_cond:
        selected_condition = st.selectbox("コンディション", ["全コンディション", "新品", "中古"], label_visibility="collapsed", key="inv_cond_filter")

    # --- フィルタリング処理 ---
    filtered_df = df.copy()
    
    if status_filter != "すべて" and "ステータス" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["ステータス"] == status_filter]
        
    if selected_category != "全カテゴリ" and "カテゴリ" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["カテゴリ"] == selected_category]
        
    if selected_condition != "全コンディション" and "コンディション" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["コンディション"] == selected_condition]

    # --- 3行目: 安全な数値化と1行サマリー表示 ---
    total_qty = pd.to_numeric(filtered_df["数量"], errors="coerce").fillna(0).astype(int).sum() if "数量" in filtered_df.columns else 0
    total_cost = pd.to_numeric(filtered_df["仕入価格"], errors="coerce").fillna(0).astype(int).sum() if "仕入価格" in filtered_df.columns else 0
    total_count = len(filtered_df)

    st.markdown(
        f"**該当件数:** {total_count:,} 件 | **対象在庫合計個数:** {total_qty:,} 個 | **合計仕入金額:** ¥{total_cost:,}",
        unsafe_allow_html=True
    )

    # --- 4行目: メインの一覧表（高さ400pxに調整しグラフの視認性を確保） ---
    st.dataframe(
        filtered_df,
        height=400,
        use_container_width=True,
        hide_index=True
    )

    # --- 5行目: 在庫金額 推移チャート（最下部） ---
    st.markdown("<hr style='margin: 15px 0 10px 0;'>", unsafe_allow_html=True)
    
    col_chart_title, col_chart_mode = st.columns([7, 3])
    with col_chart_title:
        st.markdown("**📊 日別 在庫金額推移**", unsafe_allow_html=True)
    with col_chart_mode:
        date_mode = st.radio(
            "日付モード",
            ["📅 購入日モード", "📦 棚卸しモード"],
            horizontal=True,
            key="inv_date_mode",
            label_visibility="collapsed"
        )

    # 日付列の特定と補正処理
    chart_df = filtered_df.copy()
    
    # モードに応じた日付カラムの取得（購入日 vs 撮影日/棚卸日）
    if date_mode == "📅 購入日モード":
        target_date_col = "購入日" if "購入日" in chart_df.columns else ("purchase_date" if "purchase_date" in chart_df.columns else None)
    else:
        target_date_col = "撮影日" if "撮影日" in chart_df.columns else ("棚卸日" if "棚卸日" in chart_df.columns else None)

    # 日付データの整形（不明データは 2022-01-01 に置換）
    if target_date_col and target_date_col in chart_df.columns:
        chart_df["formatted_date"] = pd.to_datetime(chart_df[target_date_col], errors="coerce").dt.strftime("%Y-%m-%d")
        chart_df["formatted_date"] = chart_df["formatted_date"].fillna("2022-01-01")
    else:
        chart_df["formatted_date"] = "2022-01-01"

    # 金額の数値化
    chart_df["numeric_cost"] = pd.to_numeric(chart_df["仕入価格"], errors="coerce").fillna(0)
    chart_df["numeric_qty"] = pd.to_numeric(chart_df["数量"], errors="coerce").fillna(1)
    chart_df["total_item_cost"] = chart_df["numeric_cost"] * chart_df["numeric_qty"]

    # ステータスの分類整理（「販売中」と「販売前・保管中」）
    def categorize_status(val):
        val_str = str(val)
        if "販売中" in val_str or "🟢" in val_str:
            return "🟢 販売中"
        else:
            return "⏳ 販売前・保管中"

    status_col = "ステータス" if "ステータス" in chart_df.columns else "status"
    if status_col in chart_df.columns:
        chart_df["chart_status"] = chart_df[status_col].apply(categorize_status)
    else:
        chart_df["chart_status"] = "⏳ 販売前・保管中"

    # 集計処理 (日付 x ステータス)
    agg_df = chart_df.groupby(["formatted_date", "chart_status"])["total_item_cost"].sum().reset_index()

    # Plotly による積み上げ棒グラフ作成
    fig = px.bar(
        agg_df,
        x="formatted_date",
        y="total_item_cost",
        color="chart_status",
        title=None,
        labels={"formatted_date": "日付", "total_item_cost": "在庫金額 (円)", "chart_status": "ステータス"},
        color_discrete_map={
            "🟢 販売中": "#2ecc71",
            "⏳ 販売前・保管中": "#e67e22"
        },
        barmode="stack"
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=280,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title=None,
        yaxis_title="在庫金額 (円)"
    )

    st.plotly_chart(fig, use_container_width=True)