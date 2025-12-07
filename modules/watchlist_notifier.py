"""
ウォッチリスト連携通知モジュール
作成日: 2025-12-07

ウォッチリストに登録された作品の新エピソード/巻をユーザーに通知
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import json

logger = logging.getLogger(__name__)

DB_PATH = 'db.sqlite3'


class WatchlistNotifier:
    """ウォッチリストベースの通知管理"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def get_db_connection(self):
        """データベース接続を取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_new_releases_for_watchlist(
        self,
        days_back: int = 7
    ) -> Dict[str, List[Dict]]:
        """
        ウォッチリスト登録作品の新規リリースを取得

        Args:
            days_back: 何日前までのリリースを対象とするか

        Returns:
            ユーザーID別の新規リリースリスト
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        query = """
        SELECT
            w.user_id,
            w.work_id,
            w.notify_new_episodes,
            w.notify_new_volumes,
            works.title,
            works.title_en,
            works.type,
            works.official_url,
            r.id as release_id,
            r.release_type,
            r.number,
            r.platform,
            r.release_date,
            r.source,
            r.source_url,
            r.notified
        FROM watchlist w
        JOIN works ON w.work_id = works.id
        JOIN releases r ON works.id = r.work_id
        WHERE r.release_date >= ?
          AND r.notified = 0
          AND (
              (r.release_type = 'episode' AND w.notify_new_episodes = 1)
              OR (r.release_type = 'volume' AND w.notify_new_volumes = 1)
          )
        ORDER BY w.user_id, r.release_date DESC, works.title
        """

        cursor.execute(query, (cutoff_date,))
        rows = cursor.fetchall()

        # ユーザー別にグループ化
        user_releases = {}
        for row in rows:
            user_id = row['user_id']
            if user_id not in user_releases:
                user_releases[user_id] = []

            user_releases[user_id].append({
                'work_id': row['work_id'],
                'work_title': row['title'],
                'work_title_en': row['title_en'],
                'work_type': row['type'],
                'official_url': row['official_url'],
                'release_id': row['release_id'],
                'release_type': row['release_type'],
                'number': row['number'],
                'platform': row['platform'],
                'release_date': row['release_date'],
                'source': row['source'],
                'source_url': row['source_url']
            })

        conn.close()

        logger.info(f"ウォッチリスト新規リリース取得: {len(user_releases)}人のユーザー、"
                   f"合計{sum(len(releases) for releases in user_releases.values())}件")

        return user_releases

    def mark_as_notified(self, release_ids: List[int]) -> int:
        """
        リリースを通知済みとしてマーク

        Args:
            release_ids: リリースIDのリスト

        Returns:
            更新された件数
        """
        if not release_ids:
            return 0

        conn = self.get_db_connection()
        cursor = conn.cursor()

        placeholders = ','.join('?' * len(release_ids))
        query = f"""
        UPDATE releases
        SET notified = 1
        WHERE id IN ({placeholders})
        """

        cursor.execute(query, release_ids)
        conn.commit()
        updated_count = cursor.rowcount

        conn.close()

        logger.info(f"通知済みマーク: {updated_count}件のリリース")

        return updated_count

    def get_user_info(self, user_id: str) -> Dict:
        """
        ユーザー情報を取得

        Args:
            user_id: ユーザーID

        Returns:
            ユーザー情報
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, username, email, email_verified
            FROM users
            WHERE id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row['id'],
                'username': row['username'],
                'email': row['email'],
                'email_verified': bool(row['email_verified'])
            }
        return None

    def format_notification_email(
        self,
        user_info: Dict,
        releases: List[Dict]
    ) -> Tuple[str, str]:
        """
        通知メールのHTMLを生成

        Args:
            user_info: ユーザー情報
            releases: リリース情報のリスト

        Returns:
            (subject, html_body)
        """
        # 作品別にグループ化
        works_map = {}
        for release in releases:
            work_id = release['work_id']
            if work_id not in works_map:
                works_map[work_id] = {
                    'title': release['work_title'],
                    'title_en': release['work_title_en'],
                    'type': release['work_type'],
                    'official_url': release['official_url'],
                    'episodes': [],
                    'volumes': []
                }

            if release['release_type'] == 'episode':
                works_map[work_id]['episodes'].append(release)
            else:
                works_map[work_id]['volumes'].append(release)

        # 件数集計
        total_episodes = sum(len(w['episodes']) for w in works_map.values())
        total_volumes = sum(len(w['volumes']) for w in works_map.values())

        # 件名
        subject_parts = []
        if total_episodes > 0:
            subject_parts.append(f"新エピソード{total_episodes}件")
        if total_volumes > 0:
            subject_parts.append(f"新刊{total_volumes}件")

        subject = f"【ウォッチリスト】{' / '.join(subject_parts)} - MangaAnime Info"

        # HTML本文
        html_body = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .container {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px 10px 0 0;
            margin: -30px -30px 20px -30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .work-card {{
            background: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }}
        .work-card.manga {{
            border-left-color: #28a745;
        }}
        .work-title {{
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .release-item {{
            background: white;
            padding: 10px;
            margin: 8px 0;
            border-radius: 4px;
            border: 1px solid #dee2e6;
        }}
        .release-type {{
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 12px;
            margin-right: 8px;
        }}
        .release-type.volume {{
            background: #28a745;
        }}
        .release-info {{
            color: #6c757d;
            font-size: 14px;
        }}
        .btn {{
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 10px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            color: #6c757d;
            font-size: 14px;
        }}
        .stats {{
            background: #e7f3ff;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ウォッチリスト更新通知</h1>
            <p style="margin: 10px 0 0 0;">あなたのお気に入り作品に新しいリリースがあります</p>
        </div>

        <p>こんにちは、{user_info['username']}さん</p>

        <div class="stats">
            <strong>{len(works_map)}作品</strong> に
            <strong>{total_episodes + total_volumes}件</strong> の新規リリース
            <br>
            <small>(エピソード: {total_episodes}件 / 巻: {total_volumes}件)</small>
        </div>
"""

        # 作品ごとの詳細
        for work_id, work in works_map.items():
            type_class = 'manga' if work['type'] == 'manga' else 'anime'
            type_label = 'マンガ' if work['type'] == 'manga' else 'アニメ'

            html_body += f"""
        <div class="work-card {type_class}">
            <div class="work-title">
                <span style="background: {'#28a745' if work['type'] == 'manga' else '#007bff'};
                             color: white; padding: 2px 8px; border-radius: 3px; font-size: 14px; margin-right: 8px;">
                    {type_label}
                </span>
                {work['title']}
            </div>
"""

            if work['title_en']:
                html_body += f"<div style='color: #6c757d; font-size: 14px; margin-bottom: 10px;'>{work['title_en']}</div>"

            # エピソード
            for ep in work['episodes']:
                html_body += f"""
            <div class="release-item">
                <span class="release-type">エピソード</span>
                <strong>第{ep['number']}話</strong>
                <div class="release-info">
                    配信日: {ep['release_date']} | プラットフォーム: {ep['platform'] or '未定'}
                </div>
                {f"<a href='{ep['source_url']}' class='btn' style='font-size: 12px; padding: 5px 10px;'>視聴する</a>" if ep['source_url'] else ""}
            </div>
"""

            # 巻
            for vol in work['volumes']:
                html_body += f"""
            <div class="release-item">
                <span class="release-type volume">巻</span>
                <strong>第{vol['number']}巻</strong>
                <div class="release-info">
                    発売日: {vol['release_date']} | {vol['source']}
                </div>
                {f"<a href='{vol['source_url']}' class='btn' style='font-size: 12px; padding: 5px 10px; background: #28a745;'>詳細を見る</a>" if vol['source_url'] else ""}
            </div>
"""

            if work['official_url']:
                html_body += f"""
            <a href="{work['official_url']}" class="btn" target="_blank">公式サイトへ</a>
"""

            html_body += """
        </div>
"""

        html_body += f"""
        <div class="footer">
            <p>この通知は、あなたのウォッチリストに基づいて送信されています</p>
            <p>
                <a href="https://your-domain.com/watchlist" style="color: #007bff;">ウォッチリストを管理</a> |
                <a href="https://your-domain.com/settings" style="color: #007bff;">設定を変更</a>
            </p>
            <p style="margin-top: 20px; font-size: 12px;">
                &copy; 2025 MangaAnime Info Delivery System
            </p>
        </div>
    </div>
</body>
</html>
"""

        return subject, html_body

    def get_watchlist_summary(self, user_id: str) -> Dict:
        """
        ユーザーのウォッチリスト概要を取得

        Args:
            user_id: ユーザーID

        Returns:
            概要情報
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN works.type = 'anime' THEN 1 ELSE 0 END) as anime_count,
                SUM(CASE WHEN works.type = 'manga' THEN 1 ELSE 0 END) as manga_count,
                SUM(notify_new_episodes) as notify_episodes_count,
                SUM(notify_new_volumes) as notify_volumes_count
            FROM watchlist w
            JOIN works ON w.work_id = works.id
            WHERE w.user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        return {
            'total': row['total'] or 0,
            'anime': row['anime_count'] or 0,
            'manga': row['manga_count'] or 0,
            'notify_episodes': row['notify_episodes_count'] or 0,
            'notify_volumes': row['notify_volumes_count'] or 0
        }


if __name__ == '__main__':
    # テスト実行
    logging.basicConfig(level=logging.INFO)

    notifier = WatchlistNotifier()

    # 新規リリース取得
    releases = notifier.get_new_releases_for_watchlist(days_back=7)

    for user_id, user_releases in releases.items():
        print(f"\n--- ユーザー: {user_id} ---")
        print(f"新規リリース: {len(user_releases)}件")

        user_info = notifier.get_user_info(user_id)
        if user_info:
            subject, html = notifier.format_notification_email(user_info, user_releases)
            print(f"件名: {subject}")
            print(f"メール長: {len(html)} bytes")
