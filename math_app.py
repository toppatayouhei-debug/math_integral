import streamlit as st
import pandas as pd
import json
import glob

st.set_page_config(page_title="Integral Flash Card", layout="centered")

# --- 1. 自動で数学用のCSVファイル（math_*.csv）を探す関数 ---
def get_math_files():
    files = glob.glob("math_*.csv")
    if not files:
        return ["サンプルのCSVファイルがありません"]
    return sorted(files)

# --- 2. データの読み込み（高速版） ---
@st.cache_data
def load_math_data(file_path):
    try:
        # UTF-8で読み込み、欠損値を空文字に
        df = pd.read_csv(file_path).fillna("")
        # 最低4列を確保（問題, 解答, 問題番号, ヒント）
        while len(df.columns) < 4:
            df[f'col_{len(df.columns)}'] = ""
        
        # 扱いやすいようにJSON用辞書リストに変換
        prepared = []
        for item in df.values.tolist():
            prepared.append({
                "q": str(item[0]),     # 問題
                "a": str(item[1]),     # 解答
                "no": str(item[2]),    # 問題番号
                "hint": str(item[3])   # ヒント
            })
        return prepared
    except Exception as e:
        return [{"q": "Error", "a": f"ファイルの読み込みに失敗しました: {e}", "no": "❌", "hint": ""}]

# タイトル
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>📚積分解法フラッシュカード</h1>", unsafe_allow_html=True)

# ファイル選択ドロップダウン
math_options = get_math_files()
selected_file = st.selectbox("🗂️ 練習するカードセットを選択してください", math_options)

# 音声処理を挟まず、一瞬でデータをロード
card_data = load_math_data(selected_file)
tango_json = json.dumps(card_data)

# --- 3. メインUI（音声なし・数式表示に特化） ---
st.components.v1.html(f"""
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

    <div id="study-app" style="font-family: sans-serif; color: #444; max-width: 550px; margin: auto;">
        
        <div style="text-align: center; font-weight: bold; color: #7f8c8d; margin-bottom: 15px; font-size: 14px;">
            😋方針が即答できるところまで仕上げよう。
        </div>

        <div style="display: flex; gap: 8px; margin-bottom: 20px; justify-content: center;">
            <button id="btn-random" style="padding: 10px 20px; border-radius: 20px; border: 1px solid #ddd; background: #fff; color: #555; font-size: 12px; font-weight: bold; cursor: pointer; transition: 0.2s;">🔀 ランダム: OFF</button>
        </div>

        <div id="card" style="background: #ffffff; padding: 40px 25px; border-radius: 30px; text-align: center; min-height: 280px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 2px solid #eef2f5; position: relative;">
            
            <div id="question-no" style="position: absolute; top: 15px; left: 20px; font-size: 14px; font-weight: bold; color: #95a5a6;"></div>
            
            <div id="eng" style="font-size: 24px; margin-bottom: 15px; color: #2c3e50; min-height: 60px; display: flex; align-items: center; justify-content: center;"></div>
            
            <div id="jp-container" style="display: none;">
                <div style="font-size: 12px; color: #e74c3c; font-weight: bold; margin-top: 10px;">【計算結果】</div>
                <div id="jp" style="font-size: 22px; color: #e74c3c; margin-bottom: 15px; min-height: 50px; display: flex; align-items: center; justify-content: center;"></div>
                
                <div id="tango-extra" style="border-top: 1px solid #eee; margin-top: 20px; padding-top: 15px;">
                    <div style="font-size: 12px; color: #27ae60; font-weight: bold; text-align: left;">💡 解法のヒント / ワンポイント:</div>
                    <div id="ext" style="font-size: 15px; color: #27ae60; text-align: left; margin-top: 5px; line-height: 1.4;"></div>
                </div>
            </div>

            <button id="btn-show" style="margin: 25px auto 0; padding: 12px 30px; border-radius: 25px; border: none; background: #2c3e50; color: white; font-weight: bold; cursor: pointer; font-size: 14px; display: block; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">🔍 答え・ヒントをチェック</button>
        </div>

        <div id="nav-controls" style="margin-top: 30px; display: flex; gap: 20px; justify-content: center;">
            <button id="btn-prev" style="width: 70px; height: 70px; border-radius: 50%; background: #fff; border: 1px solid #eee; font-size: 28px; cursor: pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">⬅️</button>
            <button id="btn-next" style="width: 70px; height: 70px; border-radius: 50%; background: #fff; border: 1px solid #eee; font-size: 28px; cursor: pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">➡️</button>
        </div>

        <div style="margin-top: 30px; text-align: center;">
            <div id="status" style="font-size: 14px; color: #bdc3c7; font-weight: bold;"></div>
        </div>
    </div>

    <script>
        const tangoData = {tango_json};
        let index = 0;
        let isRandom = false;

        function updateCard() {{
            if(tangoData.length === 0) return;
            const item = tangoData[index];
            
            // データを表示にセット
            document.getElementById('question-no').innerText = item.no;
            document.getElementById('eng').innerText = item.q;
            document.getElementById('jp').innerText = item.a;
            document.getElementById('ext').innerText = item.hint;
            
            // 画面を「問題表面」の状態にリセット
            document.getElementById('jp-container').style.display = "none";
            document.getElementById('btn-show').style.display = "block";

            document.getElementById('status').innerText = (index + 1) + " / " + tangoData.length;

            // MathJaxに数式の再レンダリングを命令
            if (window.MathJax) {{
                MathJax.typesetPromise();
            }}
        }}

        function nextCard() {{
            if (isRandom && tangoData.length > 1) {{
                let nextIndex = index;
                while(nextIndex === index) {{
                    nextIndex = Math.floor(Math.random() * tangoData.length);
                }}
                index = nextIndex;
            }} else {{
                index = (index + 1) % tangoData.length;
            }}
            updateCard();
        }}

        // 答えを表示する処理
        document.getElementById('btn-show').onclick = () => {{
            document.getElementById('jp-container').style.display = "block";
            document.getElementById('btn-show').style.display = "none";
            if (window.MathJax) {{
                MathJax.typesetPromise();
            }}
        }};

        // ランダム切り替え
        document.getElementById('btn-random').onclick = () => {{
            isRandom = !isRandom;
            const btn = document.getElementById('btn-random');
            btn.innerText = isRandom ? "🔀 ランダム: ON" : "🔀 ランダム: OFF";
            btn.style.background = isRandom ? '#f39c12' : '#fff';
            btn.style.color = isRandom ? '#fff' : '#555';
        }};

        // 前へ・次へボタン
        document.getElementById('btn-next').onclick = () => {{ nextCard(); }};
        document.getElementById('btn-prev').onclick = () => {{ index = (index - 1 + tangoData.length) % tangoData.length; updateCard(); }};

        // 起動時に少しだけ待って数式を描画
        setTimeout(updateCard, 100);
    </script>
""", height=720)
