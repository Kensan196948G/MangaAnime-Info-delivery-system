#!/usr/bin/env python3
"""
CORS対応パッチスクリプト
web_app.py に CORS ヘッダーを追加します
"""

import os
import sys

def apply_cors_patch():
    """web_app.py に CORS 対応を追加"""

    web_app_path = "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/web_app.py"

    if not os.path.exists(web_app_path):
        print(f"❌ ファイルが見つかりません: {web_app_path}")
        return False

    print(f"📄 ファイルを読み込み中: {web_app_path}")

    with open(web_app_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 既にCORS対応済みか確認
    if 'flask_cors' in content or 'Access-Control-Allow-Origin' in content:
        print("✅ 既にCORS対応済みです")
        return True

    print("🔧 CORSパッチを適用中...")

    # インポート文を追加
    import_section = content.find("from flask import")
    if import_section == -1:
        print("❌ Flask インポート文が見つかりません")
        return False

    # CORS インポートを追加
    cors_import = "\nfrom flask_cors import CORS\n"

    # app = Flask(__name__) の後に CORS を追加
    app_creation = content.find("app = Flask(__name__)")
    if app_creation == -1:
        print("❌ Flask アプリ作成文が見つかりません")
        return False

    # 改行位置を見つける
    next_line = content.find("\n", app_creation)

    cors_config = """
# CORS設定
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
"""

    # パッチ適用方法を表示（自動適用は行わない）
    print("\n" + "="*80)
    print("【CORSパッチ適用方法】")
    print("="*80)

    print("\n1. flask-cors パッケージをインストール:")
    print("   pip install flask-cors")

    print("\n2. web_app.py の冒頭のインポート部分に以下を追加:")
    print("   " + cors_import.strip())

    print("\n3. app = Flask(__name__) の直後に以下を追加:")
    print(cors_config)

    print("\n4. または、個別のエンドポイントに追加:")
    print("""
@app.route("/api/refresh-data", methods=["GET"])
def api_refresh_data():
    # 既存の処理...
    response = jsonify({...})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
""")

    print("\n" + "="*80)
    print("✅ パッチ適用方法を表示しました")
    print("="*80)

    return True

def main():
    """メイン処理"""
    print("=" * 80)
    print("CORS対応パッチスクリプト")
    print("=" * 80)
    print()

    success = apply_cors_patch()

    if success:
        print("\n✅ 完了しました")
        return 0
    else:
        print("\n❌ エラーが発生しました")
        return 1

if __name__ == "__main__":
    sys.exit(main())
