#!/usr/bin/env python3
"""
web_app.py に @login_required デコレータを追加するスクリプト
"""

import re
import sys
from pathlib import Path

def add_login_decorators(file_path):
    """
    web_app.py に認証デコレータを追加
    """
    logger.info(f"📝 読み込み: {file_path}")


    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 1. インポート文の追加
    logger.info("✅ ステップ1: インポート文を追加")

    # flask_login のインポートを追加
    if 'from flask_login import' not in content:
        import_pattern = r'(from flask_cors import CORS\n)'
        import_replacement = r'\1from flask_login import login_required, current_user\n'
        content = re.sub(import_pattern, import_replacement, content)
        logger.info("  - flask_login インポート追加")
    else:
        logger.info("  - flask_login インポート: すでに存在")

    # 2. ルートに @login_required を追加
    logger.info("\n✅ ステップ2: @login_required デコレータを追加")

    # 保護が必要なルート定義
    protected_routes = [
        # 設定管理
        (r"(@app\.route\('/config',.*methods=\['POST'\]\))\ndef update_config", "設定更新"),

        # データソース管理
        (r"(@app\.route\('/api/sources',.*methods=\['POST'\]\))\ndef create_source", "データソース作成"),
        (r"(@app\.route\('/api/sources/<int:source_id>',.*methods=\['PUT'\]\))\ndef update_source", "データソース更新"),
        (r"(@app\.route\('/api/sources/<int:source_id>',.*methods=\['DELETE'\]\))\ndef delete_source", "データソース削除"),

        # RSS フィード管理
        (r"(@app\.route\('/api/rss-feeds',.*methods=\['POST'\]\))\ndef create_rss_feed", "RSS作成"),
        (r"(@app\.route\('/api/rss-feeds/<int:feed_id>',.*methods=\['DELETE'\]\))\ndef delete_rss_feed", "RSS削除"),
        (r"(@app\.route\('/api/rss-feeds/<int:feed_id>',.*methods=\['PUT'\]\))\ndef update_rss_feed", "RSS更新"),

        # 通知管理
        (r"(@app\.route\('/api/notifications',.*methods=\['POST'\]\))\ndef create_notification", "通知作成"),
        (r"(@app\.route\('/api/notifications/<int:notification_id>',.*methods=\['DELETE'\]\))\ndef delete_notification", "通知削除"),

        # データ削除
        (r"(@app\.route\('/api/works/<int:work_id>',.*methods=\['DELETE'\]\))\ndef delete_work", "作品削除"),
        (r"(@app\.route\('/api/releases/<int:release_id>',.*methods=\['DELETE'\]\))\ndef delete_release", "リリース削除"),
    ]

    added_count = 0
    for pattern, description in protected_routes:
        # すでに @login_required がある場合はスキップ
        if re.search(pattern, content):
            route_match = re.search(pattern, content)
            if route_match:
                route_start = content.rfind('@app.route', 0, route_match.start())
                route_end = route_match.end()
                route_section = content[route_start:route_end]

                if '@login_required' not in route_section:
                    # @login_required を追加
                    replacement = r'\1\n@login_required\ndef ' + pattern.split('def ')[-1].rstrip('"')
                    content = re.sub(pattern, replacement, content)
                    logger.info(f"  ✓ {description}")
                    added_count += 1
                else:
                    logger.info(f"  - {description}: すでに保護されています")

    logger.info(f"\n📊 {added_count} 個のルートに @login_required を追加しました")

    # 3. バックアップと保存
    if content != original_content:
        backup_path = file_path + '.backup'
        logger.info(f"\n💾 バックアップ作成: {backup_path}")
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)

        logger.info(f"💾 更新を保存: {file_path}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info("\n✅ 完了!")
        logger.info("\n⚠️  次のステップ:")
        logger.info("1. python3 app/web_app.py でインポートエラーがないか確認")
        logger.info("2. pytest tests/ でテスト実行")
        logger.info("3. git diff app/web_app.py で変更内容を確認")
        logger.info("4. 問題があれば app/web_app.py.backup から復元可能")
    else:
        logger.info("\n✅ 変更不要: すべてのルートがすでに保護されています")

    return True

if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    web_app_path = project_root / 'app' / 'web_app.py'

    if not web_app_path.exists():
        logger.info(f"❌ エラー: {web_app_path} が見つかりません")
        sys.exit(1)

    try:
        add_login_decorators(web_app_path)
    except Exception as e:
        logger.info(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
