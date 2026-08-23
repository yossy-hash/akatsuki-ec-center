import streamlit as st
import pandas as pd
import plotly.express as px

def render():
    """資金管理画面（月別費用グラフ＆財務サマリー）"""
    st.markdown('<p class="header-title">💰 資金管理コントロール</p>', unsafe_allow_html=True)
    
    # データの安全取得
    df_expenses = None
    try:
        from utils.gas_api import load_sheet_data
        df_expenses = load_sheet_data("M_Expenses")
    except Exception:
        df_expenses = None

    # フォールバック（スプレッドシート未設定や取得失敗時のデフォルトデータ）
    if df_expenses is None or df_expenses.empty:
        data = {
            "年月": ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"],
            "仕入代金": [450000, 520000, 380000, 610000, 490000, 550000],
            "送料代金": [35000, 42000, 31000, 48000, 39000, 44000],
            "サブスク費": [15000, 15000, 15000, 18000, 18000, 18000],
            "固定費": [80000, 80000, 80000, 80000, 80000, 80000]
        }
        df_cost = pd.DataFrame(data)
    else:
        df_cost = df_expenses.copy()

    # --- 「年月」カラムの自動検出 ＆ 自動生成ロジック（KeyError対策） ---
    if "年月" not in df_cost.columns:
        # 日付系の可能性のあるカラムを探す
        date_candidates = [c for c in df_cost.columns if c in ["日付", "date", "Date", "DATE", "発生日", "登録日"]]
        if date_candidates:
            df_cost["年月"] = pd.to_datetime(df_cost[date_candidates[0]], errors="coerce").dt.strftime("%Y-%m")
            df_cost["年月"] = df_cost["年月"].fillna("2026-01")
        else:
            # 日付カラム自体が存在しない場合はデフォルト値を補填
            df_cost["年月"] = "2026-01"

    # 数値列の安全変換（存在しない項目は0で自動生成）
    for col in ["仕入代金", "送料代金", "サブスク費", "固定費"]:
        if col in df_cost.columns:
            df_cost[col] = pd.to_numeric(df_cost[col], errors="coerce").fillna(0).astype(int)
        else:
            df_cost[col] = 0

    # 1行サマリー表示（最新月のコスト計算）
    latest_month = df_cost["年月"].iloc[-1] if not df_cost.empty else "N/A"
    latest_row = df_cost[df_cost["年月"] == latest_month].iloc[0] if not df_cost.empty else {}
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("最新月仕入代金", f"¥{int(latest_row.get('仕入代金', 0)):,}")
    with col_m2:
        st.metric("最新月送料代金", f"¥{int(latest_row.get('送料代金', 0)):,}")
    with col_m3:
        st.metric("最新月サブスク費", f"¥{int(latest_row.get('サブスク費', 0)):,}")
    with col_m4:
        st.metric("最新月固定費", f"¥{int(latest_row.get('固定費', 0)):,}")

    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    st.markdown("**📊 月別 費用内訳推移（仕入・送料・サブスク・固定費）**")

    # Plotly表示用にロングフォーマットへ変換
    df_melted = df_cost.melt(
        id_vars=["年月"],
        value_vars=["仕入代金", "送料代金", "サブスク費", "固定費"],
        var_name="費用項目",
        value_name="金額"
    )

    # 積み上げ棒グラフの作成
    fig = px.bar(
        df_melted,
        x="年月",
        y="金額",
        color="費用項目",
        labels={"年月": "年月", "金額": "支出金額 (円)", "費用項目": "項目"},
        color_discrete_map={
            "仕入代金": "#3b82f6",  # ブルー
            "送料代金": "#10b981",  # エメラルドグリーン
            "サブスク費": "#f59e0b", # アンバー
            "固定費": "#ef4444"   # レッド
        },
        barmode="stack"
    )

    fig.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title=None,
        yaxis_title="金額 (円)"
    )

    st.plotly_chart(fig, use_container_width=True)

    # 月別詳細データテーブル
    st.markdown("**【月別費用内訳 明細表】**")
    st.dataframe(df_cost, height=200, use_container_width=True, hide_index=True)