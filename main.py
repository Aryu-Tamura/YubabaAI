# main.py
import os
import openai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn # ASGIサーバー
from dotenv import load_dotenv # 環境変数を読み込む

# .envファイルから環境変数を読み込む (任意)
# .envファイルに OPENAI_API_KEY=sk-your_api_key のように記述
load_dotenv()

# --- OpenAI APIキーの設定 ---
# 環境変数 'OPENAI_API_KEY' からキーを取得
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OpenAI APIキーが環境変数に設定されていません。'OPENAI_API_KEY' を設定してください。")

# OpenAIクライアントの初期化
try:
    client = openai.OpenAI(api_key=openai_api_key)
    print("OpenAIクライアントが正常に初期化されました。")
except Exception as e:
    print(f"OpenAIクライアントの初期化に失敗しました: {e}")
    # 必要に応じてプログラムを終了させるか、エラー処理を行う
    exit()


# --- リクエスト/レスポンスモデルの定義 (Pydantic) ---
class NameInput(BaseModel):
    """リクエストボディのモデル"""
    name: str

class NameOutput(BaseModel):
    """レスポンスボディのモデル"""
    new_name: str

# --- FastAPIアプリケーションの初期化 ---
app = FastAPI(
    title="湯婆婆AI API",
    description="入力された名前を湯婆婆風の短い名前に変換するAPIです。",
    version="1.0.0"
)

# --- CORS (Cross-Origin Resource Sharing) の設定 ---
# フロントエンドからのリクエストを許可するために必要
# '*' は全てのオリジンを許可。本番環境ではより厳密な設定を推奨。
origins = [
    "*", # 開発中は '*' で許可することが多い
    # 例: "http://localhost:8000", # フロントエンドが動作するオリジン
    # 例: "http://127.0.0.1:5500", # Live Serverなどのデフォルトポート
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # 全てのHTTPメソッドを許可 (GET, POSTなど)
    allow_headers=["*"], # 全てのHTTPヘッダーを許可
)


# --- 名前生成関数 (Gradioコードから移植) ---
def generate_yubaba_name(name: str) -> str:
    """OpenAI APIを使って、入力された名前を湯婆婆風の短い名前に変換する"""
    prompt = f"""あなたは銭婆の姉である湯婆婆です。贅沢な名前「{name}」を入力されたら、その名前から短く呼びやすい新しい名前を与えてください。新しい名前は、元の名前の漢字一文字（読みは元の名前に近いもの、または音読み）、または作中に登場する「千（セン）」や「ハク」のように非常に短い名前にしてください。新しい短い名前には読み仮名を（）で添えてください。

以下に名前変換の例を示します。

* 入力：山田太郎 → 出力：山（サン）
* 入力：佐藤花子 → 出力：花（ハナ）
* 入力：木村美咲 → 出力：咲（サキ）
* 入力：高橋健太 → 出力：橋（キョウ）
* 入力：渡辺優子 → 出力：優（ユウ）
* 入力：萩野千尋 → 出力：千（セン）
* 入力：伊藤さくら → 出力：藤（トウ）
* 入力：ニギハヤミコハクヌシ → 出力：ハク（ハク）

入力された名前に基づき、新しい短い名前（読み）のみを返してください。

入力例：
名前：{name}

出力例：
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # または "gpt-4o-mini"
            messages=[
                {"role": "system", "content": "あなたは湯婆婆です。"},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API呼び出し中にエラーが発生しました: {e}")
        # API呼び出し失敗時はエラーを発生させる
        raise HTTPException(status_code=500, detail=f"名前の生成に失敗しました: {e}")


# --- APIエンドポイントの定義 ---
@app.post("/api/generate-name", response_model=NameOutput)
async def create_new_name(name_input: NameInput):
    """
    POSTリクエストを受け取り、名前を生成して返すエンドポイント
    """
    original_name = name_input.name
    if not original_name:
        raise HTTPException(status_code=400, detail="名前が入力されていません。")

    try:
        new_name = generate_yubaba_name(original_name)
        return NameOutput(new_name=new_name)
    except HTTPException as http_exc:
        # generate_yubaba_name内で発生したHTTPExceptionをそのまま返す
        raise http_exc
    except Exception as e:
        # その他の予期せぬエラー
        print(f"予期せぬエラーが発生しました: {e}")
        raise HTTPException(status_code=500, detail="サーバー内部でエラーが発生しました。")

# --- ルートエンドポイント (動作確認用) ---
@app.get("/")
async def read_root():
    return {"message": "湯婆婆AI APIへようこそ！ /api/generate-name にPOSTリクエストを送ってください。"}

# --- サーバーの実行 (開発用) ---
# このファイルが直接実行された場合にUvicornサーバーを起動
if __name__ == "__main__":
    # uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    # 上記はコマンドラインから `uvicorn main:app --reload --port 8000` を実行するのと同じ
    print("サーバーを起動するには、ターミナルで以下のコマンドを実行してください:")
    print("uvicorn main:app --reload --port 8000")
    print("APIドキュメントは http://127.0.0.1:8000/docs で確認できます。")

