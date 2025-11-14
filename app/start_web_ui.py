#!/usr/bin/env python3
"""
Web UI Startup Script for Anime/Manga Information Delivery System
This script provides an easy way to start the web interface.
"""

import os
import sys
import argparse
import socket
import json
from web_app import app


def get_local_ip():
    """Get the local IP address of the system"""
    try:
        # Create a socket connection to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        # Fallback to localhost if unable to determine IP
        return "127.0.0.1"


def load_server_config():
    """Load server configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("server", {})
    except Exception as e:
        print(f"Warning: Could not load server config: {e}")
    return {}


def save_server_config(host, port):
    """Save server configuration to config.json"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}

        if "server" not in config:
            config["server"] = {}

        config["server"]["host"] = host
        config["server"]["port"] = port
        config["server"]["last_ip"] = get_local_ip()

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not save server config: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Start the Anime/Manga Information Delivery System Web UI"
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Host to bind to (default: 0.0.0.0 or from config)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind to (default: 5000 or from config)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--no-auto-reload",
        action="store_true",
        help="Disable auto-reload in debug mode",
    )
    parser.add_argument(
        "--localhost-only",
        action="store_true",
        help="Bind to localhost only (127.0.0.1)"
    )

    args = parser.parse_args()

    # Load server configuration
    server_config = load_server_config()

    # Determine host and port
    if args.localhost_only:
        host = "127.0.0.1"
    elif args.host:
        host = args.host
    else:
        host = server_config.get("host", "0.0.0.0")

    port = args.port or server_config.get("port", 5000)

    # Get local IP for display
    local_ip = get_local_ip()

    # Save configuration
    save_server_config(host, port)

    print("=" * 70)
    print("     アニメ・マンガ情報配信システム Web UI")
    print("=" * 70)
    print(f"  サーバー起動情報:")
    print(f"    - バインドアドレス: {host}")
    print(f"    - ポート番号: {port}")
    print(f"    - デバッグモード: {'有効' if args.debug else '無効'}")
    print()
    print(f"  アクセスURL:")
    if host == "0.0.0.0":
        print(f"    - ローカル: http://localhost:{port}")
        print(f"    - ネットワーク: http://{local_ip}:{port}")
        print(f"    - 外部アクセス: http://<your-public-ip>:{port}")
    elif host == "127.0.0.1":
        print(f"    - ローカルのみ: http://localhost:{port}")
    else:
        print(f"    - カスタム: http://{host}:{port}")
    print()
    print("  環境変数オプション:")
    print("    - SERVER_HOST: サーバーホストを指定")
    print("    - SERVER_PORT: サーバーポートを指定")
    print("    - DEBUG_MODE: デバッグモードを有効化")
    print("=" * 70)
    print()

    # Check for required files
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    required_files = [
        os.path.join(base_dir, "db.sqlite3"),
        os.path.join(base_dir, "config.json")
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(os.path.basename(file))

    if missing_files:
        print("  ⚠️  警告: 以下のファイルが見つかりません:")
        for file in missing_files:
            print(f"      - {file}")
        print()
        print("  メインシステムを最初に実行してデータベースを初期化してください。")
        print("  Web UIは設定ファイルなしでも起動できますが、一部機能が制限されます。")
        print()

    # Apply environment variable overrides
    env_host = os.environ.get("SERVER_HOST")
    env_port = os.environ.get("SERVER_PORT")
    env_debug = os.environ.get("DEBUG_MODE", "").lower() in ("true", "1", "yes")

    if env_host:
        host = env_host
        print(f"  環境変数 SERVER_HOST を適用: {host}")

    if env_port:
        try:
            port = int(env_port)
            print(f"  環境変数 SERVER_PORT を適用: {port}")
        except ValueError:
            print(f"  警告: 無効な SERVER_PORT 値: {env_port}")

    if env_debug:
        args.debug = True
        print(f"  環境変数 DEBUG_MODE を適用: 有効")

    try:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(base_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)

        print()
        print("  サーバーを起動しています...")
        print()

        # Start the Flask application
        app.run(
            host=host,
            port=port,
            debug=args.debug,
            use_reloader=not args.no_auto_reload if args.debug else False,
            threaded=True,
        )

    except KeyboardInterrupt:
        print("\n")
        print("=" * 70)
        print("  Web UIを終了しています...")
        print("=" * 70)
        sys.exit(0)
    except OSError as e:
        if "Address already in use" in str(e):
            print("\n")
            print("=" * 70)
            print(f"  エラー: ポート {port} は既に使用されています。")
            print(f"  別のポートを指定してください: --port <ポート番号>")
            print("=" * 70)
        else:
            print(f"\n  OSエラーが発生しました: {e}")
        sys.exit(1)
    except Exception as e:
        print("\n")
        print("=" * 70)
        print(f"  エラーが発生しました: {e}")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
