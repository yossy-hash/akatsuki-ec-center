import streamlit as st
import pandas as pd
from utils.gas_api import load_sheet_data, append_sheet_data

SHEET_RULES = "M_Rules"

def render_tab10_rules():
    st.title("⚙️ 自動名寄せ・勘定科目ルール設定 (`M_Rules`)")
    st.write("取引名に含まれるキーワードから、綺麗な名称（`clean_name`）や勘定科目（`category`）を自動付与するルールを管理します。")

    df_rules = load_sheet_data(SHEET_RULES)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("➕ ルールの新規登録")
        with st.form("add_rule_form"):
            keyword = st.text_input("検索キーワード（例: マックスバリュ）", help="CSVの取引名に含まれる文字")
            clean_name = st.text_input("変換後の名称（例: マックスバリュ）", help="統一後のきれいな店舗名・取引先名")
            category = st.selectbox(
                "勘定科目",
                ["仕入高", "旅費交通費", "通信費", "接待交際費", "消耗品費", "会議費", "地代家賃", "雑費", "事業主貸", "未分類"]
            )
            ratio = st.number_input("経費計上割合 (%)", min_value=0, max_value=100, value=100, step=10)
            
            submitted = st.form_submit_button("🚀 ルールを追加", type="primary")

            if submitted:
                if not keyword:
                    st.error("キーワードを入力してください。")
                else:
                    new_rule = {
                        "rule_id": f"RULE_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}",
                        "keyword": keyword.strip(),
                        "clean_name": clean_name.strip() if clean_name else keyword.strip(),
                        "category": category,
                        "ratio": ratio
                    }
                    if append_sheet_data(SHEET_RULES, [new_rule]):
                        st.success(f"ルール「{keyword}」を追加しました！")
                        st.rerun()
                    else:
                        st.error("ルールの追加に失敗しました。")

    with col2:
        st.subheader("📋 登録済みルール一覧")
        if not df_rules.empty:
            st.dataframe(df_rules, use_container_width=True, hide_index=True)
        else:
            st.info("現在登録されているルールはありません。左のフォームから追加してください。")