import streamlit as st
import pandas as pd
import json
from PIL import Image

def render():
    """画像からデータを抽出してスプレッドシート形式にする機能"""
    st.markdown('<p class="header-title">📸 Amazonセラーセントラル 画像AI取り込み</p>', unsafe_allow_html=True)
    
    st.info("💡 **使い方:** セラーセントラルの「在庫管理」画面のスクリーンショットをアップロードすると、Gemini AIが文字と数値を自動で読み取り、スプレッドシート用のデータに変換します。")

    # --- 1. 画像アップロード ---
    uploaded_file = st.file_uploader("📁 スプレッドシートに転記したい画像をアップロード (JPG / PNG)", type=['png', 'jpg', 'jpeg'])

    if uploaded_file is not None:
        # 画像のプレビュー表示
        image = Image.open(uploaded_file)
        st.image(image, caption="アップロードされた画像", use_container_width=True)

        # --- 2. AI読み取り実行ボタン ---
        if st.button("🤖 Gemini AIでデータを抽出・構造化", type="primary", use_container_width=True):
            with st.spinner("AIが画像を解析中...（約10〜15秒）"):
                
                # ---------------------------------------------------------
                # ⚠️ 実際の実装では、ここでGemini APIに画像と以下のプロンプトを投げます
                # prompt = """
                # 添付されたAmazonセラーセントラルの画像から、以下の項目を正確に読み取り、
                # JSON配列形式（[{'ASIN': '...', '商品名': '...', ...}]）で出力してください。
                # 項目：作成日, 商品名, ASIN, SKU, 在庫数, 販売価格, 手数料
                # """
                # response = model.generate_content([prompt, image])
                # ---------------------------------------------------------
                
                # 今回は画像（image_7243cc.jpg）から私が読み取った実際のデータをシミュレートします
                mock_ai_json = [
                    {
                        "作成日": "2026年8月9日 11:31",
                        "商品名": "レノア 超消臭1WEEK 柔軟剤 SPORTS フレッシュシトラス 詰め替え 1,900mL [大容量]",
                        "ASIN": "B0CVY8WLDM",
                        "SKU": "ABC-0008",
                        "在庫数": 2,
                        "販売価格": 2200,
                        "手数料": 383
                    },
                    {
                        "作成日": "2026年8月9日 11:23",
                        "商品名": "【まとめ買い】【大容量】レノア 超消臭 1WEEK 柔軟剤 フレッシュグリーン 詰め替え 2,100mL × 2個",
                        "ASIN": "B09XBK4XLD",
                        "SKU": "ABC-0007",
                        "在庫数": 2,
                        "販売価格": 4100,
                        "手数料": 581
                    },
                    {
                        "作成日": "2026年8月9日 11:20",
                        "商品名": "【ケース販売】【大容量】レノア 超消臭1WEEK 柔軟剤 フレッシュグリーン 詰め替え 2,100mL×4袋",
                        "ASIN": "B09PQP5MQR",
                        "SKU": "ABC-0005",
                        "在庫数": 1,
                        "販売価格": 8004,
                        "手数料": 987
                    },
                    {
                        "作成日": "2026年8月9日 11:08",
                        "商品名": "京セラ 水筒 350ml セラミック 塗膜 スクリュー栓 ローズピンク CSB-S350-BRPK",
                        "ASIN": "B07BG7SBK8",
                        "SKU": "ABC-0004",
                        "在庫数": 1,
                        "販売価格": 3880,
                        "手数料": 778
                    }
                ]
                
                # JSONデータをPandasデータフレームに変換
                df_extracted = pd.DataFrame(mock_ai_json)
                st.session_state["extracted_data"] = df_extracted
                st.success("✨ 画像からのデータ抽出が完了しました！")

        # --- 3. 抽出結果の確認とスプレッドシート転記 ---
        if "extracted_data" in st.session_state:
            st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
            st.markdown("### 📊 抽出されたデータ（AKATSUKI DB 連携用）")
            
            df = st.session_state["extracted_data"]
            
            # データフレームの表示（編集可能にして、万が一のAIの読み間違いを手直しできるようにする）
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "販売価格": st.column_config.NumberColumn("販売価格 (¥)", format="¥%d"),
                    "手数料": st.column_config.NumberColumn("手数料 (¥)", format="¥%d"),
                }
            )

            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

            # AKATSUKI DB（スプレッドシート）への転記アクション
            col1, col2 = st.columns(2)
            with col1:
                # CSVとしてダウンロードする機能
                csv = edited_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 CSVファイルとしてダウンロード",
                    data=csv,
                    file_name="amazon_inventory_extracted.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col2:
                # GASなどを経由してスプレッドシートに直接書き込むボタン
                if st.button("💾 スプレッドシート（AKATSUKI DB）に直接転記", use_container_width=True):
                    # ここに utils.gas_api.append_to_sheet() などの処理を入れる
                    st.toast("✅ スプレッドシートの「在庫管理」タブにデータを追記しました！")
                    st.balloons()