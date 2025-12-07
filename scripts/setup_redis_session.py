#!/usr/bin/env python3
"""
Redis セッションストア設定スクリプト
Flask-SessionをRedisバックエンドで動作させるための設定
"""
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_redis_connection():
    """Redis接続確認"""
    try:
        import redis
        
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        client = redis.from_url(redis_url)
        
        # PING テスト
        response = client.ping()
        if response:
            print(f"✅ Redis接続成功: {redis_url}")
            return True
        else:
            print(f"❌ Redis接続失敗: PINGレスポンスなし")
            return False
    
    except ImportError:
        print("❌ redisパッケージがインストールされていません")
        print("   インストール: pip install redis")
        return False
    
    except Exception as e:
        print(f"❌ Redis接続エラー: {e}")
        print("   Redisサーバーが起動していることを確認してください")
        return False


def setup_flask_session_redis():
    """Flask-Session Redis設定を確認"""
    print("\n=== Flask-Session Redis設定 ===")
    
    # Flask-Sessionインストール確認
    try:
        import flask_session
        print(f"✅ Flask-Session {flask_session.__version__} インストール済み")
    except ImportError:
        print("❌ Flask-Sessionがインストールされていません")
        print("   インストール: pip install Flask-Session")
        return False
    
    # redisパッケージ確認
    try:
        import redis
        print(f"✅ redis {redis.__version__} インストール済み")
    except ImportError:
        print("❌ redisパッケージがインストールされていません")
        print("   インストール: pip install redis")
        return False
    
    return True


def print_configuration_example():
    """設定例を表示"""
    print("\n=== app/web_app.py 設定例 ===")
    print("""
from flask_session import Session
import redis

# Redis接続
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

# Flask-Session設定
app.config.update(
    SESSION_TYPE='redis',
    SESSION_REDIS=redis_client,
    SESSION_PERMANENT=False,
    SESSION_USE_SIGNER=True,
    SESSION_KEY_PREFIX='mangaanime:session:'
)

# セッション初期化
Session(app)
""")


def main():
    print("=" * 60)
    print("Redis セッションストア設定")
    print("=" * 60)
    
    # 1. Redis接続確認
    print("\n1. Redis接続確認")
    redis_ok = check_redis_connection()
    
    # 2. Flask-Session確認
    print("\n2. Flask-Session確認")
    flask_session_ok = setup_flask_session_redis()
    
    # 3. 設定例表示
    print_configuration_example()
    
    # 4. 最終判定
    print("\n=" * 60)
    if redis_ok and flask_session_ok:
        print("✅ Redis セッションストアの準備が完了しました")
        print("\n次のステップ:")
        print("  1. app/web_app.py に上記の設定を追加")
        print("  2. アプリケーションを再起動")
        print("  3. セッションがRedisに保存されることを確認")
    else:
        print("❌ セットアップに問題があります")
        print("\n修正が必要な項目:")
        if not redis_ok:
            print("  - Redisサーバーの起動")
        if not flask_session_ok:
            print("  - 必要なパッケージのインストール")
    
    print("=" * 60)
    
    return 0 if (redis_ok and flask_session_ok) else 1


if __name__ == '__main__':
    sys.exit(main())
