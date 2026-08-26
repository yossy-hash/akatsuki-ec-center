import streamlit as st
import pandas as pd

def render_tab1_inventory(df_inventory: pd.DataFrame):
    st.subheader("📦 リアルタイム在庫コントロール")

    if df_inventory.empty:
        st.warning("表示できる在庫データがありません。")
        return

    # データ型の安全化処理（空文字や文字列を 0 に変換して PyArrow エラーを防止）
    df = df_inventory.copy()
    
    # 1. 数値列の型変換
    num_cols = ["仕入価格", "数量", "Amazon新品最安値", "Amazonカート価格", "ヤフオク最安値"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # 2. 必須列の存在チェックとデフォルト補完
    if "ステータス" not in df.columns:
        df["ステータス"] = "在庫あり"

    # --- フィルターエリア ---
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        status_filter = st.radio(
            "表示フィルタ",
            ["すべて", "在庫あり", "販売中", "出品前・保管中"],
            horizontal=True
        )
    
    with col2:
        categories = ["全カテゴリ"] + sorted(list(df["カテゴリ"].dropna().unique())) if "カテゴリ" in df.columns else ["全カテゴリ"]
        selected_cat = st.selectbox("カテゴリ絞り込み", categories)

    with col3:
        conditions = ["全コンディション"] + sorted(list(df["コンディション"].dropna().unique())) if "コンディション" in df.columns else ["全コンディション"]
        selected_cond = st.selectbox("状態絞り込み", conditions)

    # フィルタリング適用
    if status_filter != "すべて":
        df = df[df["ステータス"] == status_filter]
    if selected_cat != "全カテゴリ" and "カテゴリ" in df.columns:
        df = df[df["カテゴリ"] == selected_cat]
    if selected_cond != "全コンディション" and "コンディション" in df.columns:
        df = df[df["コンディション"] == selected_cond]

    # メトリクス表示
    total_count = len(df)
    total_qty = df["数量"].sum() if "数量" in df.columns else 0
    total_cost = (df["仕入価格"] * df["数量"]).sum() if "仕入価格" in df.columns and "数量" in df.columns else 0

    st.markdown(f"**該当件数**: `{total_count} 件` | **対象在庫合計個数**: `{total_qty} 個` | **合計仕入金額**: `￥{total_cost:,}`")

    # --- データフレーム表示 ---
    disp_cols = ["ID", "商品画像", "撮影日", "JANコード", "商品名", "仕入価格", "数量", "ステータス", "AI解析生データ"]
    available_cols = [c for c in disp_cols if c in df.columns]

    st.dataframe(
        df[available_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "仕入価格": st.column_config.NumberColumn("仕入価格", format="￥%d"),
            "数量": st.column_config.NumberColumn("数量", format="%d 個"),
        }
    )