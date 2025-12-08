#!/usr/bin/env python3
"""
ウォッチリスト通知実行スクリプト
作成日: 2025-12-07

ウォッチリストに登録された作品の新規リリースをユーザーに通知
cron等で定期実行することを想定
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from datetime import datetime
from modules.watchlist_notifier import WatchlistNotifier
from modules.mailer import GmailSender  # 既存のメール送信モジュールを想定

# ログ設定
log_dir = project_root / 'logs'
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f'watchlist_notifications_{datetime.now().strftime("%Y%m%d")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)


def main():
    """メイン処理"""
    logger.info("=" * 60)
    logger.info("ウォッチリスト通知処理を開始")
    logger.info("=" * 60)

    try:
        # ウォッチリスト通知管理インスタンス
        notifier = WatchlistNotifier()

        # 過去7日間の新規リリースを取得
        logger.info("新規リリースを取得中...")
        user_releases = notifier.get_new_releases_for_watchlist(days_back=7)

        if not user_releases:
            logger.info("通知対象のリリースがありません")
            return

        logger.info(f"通知対象: {len(user_releases)}人のユーザー")

        # メール送信準備
        try:
            mailer = GmailSender()
        except Exception as e:
            logger.error(f"メーラー初期化エラー: {str(e)}")
            logger.warning("メール送信をスキップします")
            mailer = None

        # ユーザーごとに通知送信
        total_sent = 0
        total_failed = 0
        all_notified_release_ids = []

        for user_id, releases in user_releases.items():
            logger.info(f"\n処理中: ユーザー {user_id} ({len(releases)}件のリリース)")

            # ユーザー情報取得
            user_info = notifier.get_user_info(user_id)
            if not user_info:
                logger.warning(f"ユーザー情報が取得できません: {user_id}")
                continue

            if not user_info.get('email'):
                logger.warning(f"メールアドレスが設定されていません: {user_id}")
                continue

            if not user_info.get('email_verified'):
                logger.warning(f"メールアドレスが未検証です: {user_id}")
                # 未検証でも送信する場合はこの行をコメントアウト
                # continue

            # メール内容生成
            subject, html_body = notifier.format_notification_email(user_info, releases)

            # メール送信
            if mailer:
                try:
                    mailer.send_html_email(
                        to_address=user_info['email'],
                        subject=subject,
                        html_body=html_body
                    )
                    logger.info(f"メール送信成功: {user_info['email']}")
                    total_sent += 1

                    # 通知済みとしてマーク
                    release_ids = [r['release_id'] for r in releases]
                    all_notified_release_ids.extend(release_ids)

                except Exception as e:
                    logger.error(f"メール送信エラー ({user_info['email']}): {str(e)}")
                    total_failed += 1
            else:
                logger.info(f"メール送信スキップ（テストモード）: {user_info['email']}")
                logger.info(f"件名: {subject}")

        # 通知済みマーク
        if all_notified_release_ids:
            marked_count = notifier.mark_as_notified(all_notified_release_ids)
            logger.info(f"\n通知済みマーク: {marked_count}件のリリース")

        # サマリー
        logger.info("\n" + "=" * 60)
        logger.info("処理完了サマリー")
        logger.info("=" * 60)
        logger.info(f"対象ユーザー数: {len(user_releases)}")
        logger.info(f"送信成功: {total_sent}件")
        logger.info(f"送信失敗: {total_failed}件")
        logger.info(f"通知済みリリース: {len(all_notified_release_ids)}件")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"予期しないエラー: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
