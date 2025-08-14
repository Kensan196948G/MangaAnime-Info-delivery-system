#!/usr/bin/env python3
"""
Web UI Startup Script for Anime/Manga Information Delivery System
This script provides an easy way to start the web interface.
"""

import os
import sys
import argparse
from web_app import app

def main():
    parser = argparse.ArgumentParser(description='Start the Anime/Manga Information Delivery System Web UI')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-auto-reload', action='store_true', help='Disable auto-reload in debug mode')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("アニメ・マンガ情報配信システム Web UI")
    print("=" * 60)
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Debug: {args.debug}")
    print(f"URL: http://{args.host}:{args.port}")
    print("=" * 60)
    print()
    
    # Check for required files
    required_files = [
        'db.sqlite3',
        'config.json'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("⚠️  警告: 以下のファイルが見つかりません:")
        for file in missing_files:
            print(f"   - {file}")
        print()
        print("メインシステムを最初に実行してデータベースを初期化してください。")
        print("Web UIは設定ファイルなしでも起動できますが、一部機能が制限されます。")
        print()
    
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Start the Flask application
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            use_reloader=not args.no_auto_reload if args.debug else False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n\nWeb UIを終了しています...")
        sys.exit(0)
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()