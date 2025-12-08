#!/usr/bin/env python3
"""
Google Calendar API デモスクリプト
Phase 17: カレンダー統合実装

使用方法:
    python examples/calendar_demo.py

注意:
    - 事前に OAuth2.0 認証が必要です
    - auth/calendar_token.json が存在することを確認してください
"""

import sys
import os
from datetime import datetime, timedelta
import logging

# パスを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.calendar_api import (
    GoogleCalendarAPI,
    GoogleCalendarAPIError,
    AuthenticationError,
    create_reminder,
    format_event_summary
)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_basic_operations():
    """基本操作のデモ"""
    print("\n" + "=" * 60)
    print("デモ1: 基本操作")
    print("=" * 60)

    try:
        # カレンダーAPI初期化
        calendar = GoogleCalendarAPI()
        logger.info("GoogleCalendarAPI initialized successfully")

        # カレンダー情報の取得
        print("\n[1] カレンダー情報の取得")
        info = calendar.get_calendar_info()
        print(f"  カレンダー: {info.get('summary')}")
        print(f"  タイムゾーン: {info.get('timeZone')}")

        # イベントの作成
        print("\n[2] テストイベントの作成")
        test_event = calendar.create_event(
            summary='[テスト] カレンダーAPI動作確認',
            start_time=datetime.now() + timedelta(hours=1),
            duration_minutes=30,
            description='これはテストイベントです。後で削除されます。',
            color_id='9',  # ブルー
            reminders=[create_reminder('popup', 15)]
        )
        event_id = test_event['id']
        print(f"  作成成功: {test_event['summary']}")
        print(f"  イベントID: {event_id}")

        # イベントの取得
        print("\n[3] イベントの取得")
        retrieved_event = calendar.get_event(event_id)
        print(f"  タイトル: {retrieved_event['summary']}")
        print(f"  開始: {retrieved_event['start']['dateTime']}")

        # イベントの更新
        print("\n[4] イベントの更新")
        updated_event = calendar.update_event(
            event_id,
            {'summary': '[テスト] 更新されたイベント'}
        )
        print(f"  更新後: {updated_event['summary']}")

        # イベントの削除
        print("\n[5] イベントの削除")
        result = calendar.delete_event(event_id)
        if result:
            print("  削除成功")

        print("\n基本操作デモ完了!")

    except AuthenticationError as e:
        logger.error(f"認証エラー: {e}")
        print("\nエラー: OAuth2.0トークンが見つかりません")
        print("先に認証セットアップを実行してください")
        return False

    except GoogleCalendarAPIError as e:
        logger.error(f"APIエラー: {e}")
        return False

    return True


def demo_event_listing():
    """イベント一覧・検索のデモ"""
    print("\n" + "=" * 60)
    print("デモ2: イベント一覧・検索")
    print("=" * 60)

    try:
        calendar = GoogleCalendarAPI()

        # 今後1週間のイベントを取得
        print("\n[1] 今後1週間のイベント")
        events = calendar.list_events(
            time_min=datetime.now(),
            time_max=datetime.now() + timedelta(days=7),
            max_results=10
        )
        print(f"  取得件数: {len(events)}件")

        if events:
            for i, event in enumerate(events[:5], 1):
                print(f"  {i}. {event['summary']}")
                print(f"     開始: {event['start'].get('dateTime', event['start'].get('date'))}")
        else:
            print("  イベントが見つかりませんでした")

        # キーワード検索
        print("\n[2] キーワード検索（'テスト'）")
        search_results = calendar.search_events('テスト')
        print(f"  検索結果: {len(search_results)}件")

        if search_results:
            for i, event in enumerate(search_results[:3], 1):
                print(f"  {i}. {event['summary']}")

        print("\nイベント一覧デモ完了!")

    except GoogleCalendarAPIError as e:
        logger.error(f"APIエラー: {e}")
        return False

    return True


def demo_batch_operations():
    """バッチ操作のデモ"""
    print("\n" + "=" * 60)
    print("デモ3: バッチ操作")
    print("=" * 60)

    try:
        calendar = GoogleCalendarAPI()

        # テストイベントデータを作成
        print("\n[1] バッチイベント作成（3件）")
        base_time = datetime.now() + timedelta(days=1)

        events_data = [
            {
                'summary': format_event_summary('テストアニメ1', '第1話'),
                'start_time': base_time,
                'duration_minutes': 30,
                'description': 'バッチ処理テスト',
                'color_id': '9'
            },
            {
                'summary': format_event_summary('テストアニメ2', '第2話'),
                'start_time': base_time + timedelta(hours=1),
                'duration_minutes': 30,
                'description': 'バッチ処理テスト',
                'color_id': '9'
            },
            {
                'summary': format_event_summary('テストアニメ3', '第3話'),
                'start_time': base_time + timedelta(hours=2),
                'duration_minutes': 30,
                'description': 'バッチ処理テスト',
                'color_id': '9'
            }
        ]

        success, failed, errors = calendar.batch_create_events(
            events_data,
            batch_size=50
        )

        print(f"  成功: {success}件")
        print(f"  失敗: {failed}件")

        if errors:
            print("  エラー詳細:")
            for error in errors:
                print(f"    - {error}")

        # 作成したイベントを検索
        print("\n[2] 作成したイベントを検索")
        created_events = calendar.search_events('テストアニメ')
        print(f"  検索結果: {len(created_events)}件")

        # 作成したイベントを削除
        if created_events:
            print("\n[3] 作成したイベントを削除")
            event_ids = [event['id'] for event in created_events]
            success, failed = calendar.batch_delete_events(event_ids)
            print(f"  削除成功: {success}件")
            print(f"  削除失敗: {failed}件")

        print("\nバッチ操作デモ完了!")

    except GoogleCalendarAPIError as e:
        logger.error(f"APIエラー: {e}")
        return False

    return True


def demo_anime_schedule():
    """アニメ配信スケジュール登録のデモ"""
    print("\n" + "=" * 60)
    print("デモ4: アニメ配信スケジュール登録（実用例）")
    print("=" * 60)

    try:
        calendar = GoogleCalendarAPI()

        # サンプルアニメデータ
        anime_schedule = [
            {
                'title': '呪術廻戦',
                'episode': 10,
                'broadcast_time': datetime(2025, 12, 15, 23, 0),
                'platform': 'dアニメストア',
                'url': 'https://anime.dmkt-sp.jp/'
            },
            {
                'title': 'SPY×FAMILY',
                'episode': 5,
                'broadcast_time': datetime(2025, 12, 16, 22, 30),
                'platform': 'dアニメストア',
                'url': 'https://anime.dmkt-sp.jp/'
            },
            {
                'title': 'チェンソーマン',
                'episode': 8,
                'broadcast_time': datetime(2025, 12, 17, 23, 30),
                'platform': 'dアニメストア',
                'url': 'https://anime.dmkt-sp.jp/'
            }
        ]

        print("\n[1] アニメ配信スケジュールを登録")
        events_data = []

        for anime in anime_schedule:
            event_data = {
                'summary': format_event_summary(
                    anime['title'],
                    f"第{anime['episode']}話"
                ),
                'start_time': anime['broadcast_time'],
                'duration_minutes': 30,
                'description': (
                    f"配信プラットフォーム: {anime['platform']}\n"
                    f"URL: {anime['url']}"
                ),
                'color_id': '9',  # ブルー
                'reminders': [
                    create_reminder('popup', 30)  # 30分前に通知
                ]
            }
            events_data.append(event_data)

        # バッチ登録
        success, failed, errors = calendar.batch_create_events(events_data)

        print(f"  登録成功: {success}件")
        print(f"  登録失敗: {failed}件")

        if success > 0:
            print("\n  登録されたイベント:")
            for anime in anime_schedule:
                print(f"    - {anime['title']} 第{anime['episode']}話")
                print(f"      配信: {anime['broadcast_time'].strftime('%Y-%m-%d %H:%M')}")

        # 確認のため検索
        print("\n[2] 登録されたイベントを確認")
        for anime in anime_schedule[:1]:  # 最初の1件だけ確認
            events = calendar.search_events(anime['title'])
            print(f"  {anime['title']}: {len(events)}件のイベント")

        print("\nアニメスケジュール登録デモ完了!")
        print("\n※ 作成されたイベントは手動で削除してください")

    except GoogleCalendarAPIError as e:
        logger.error(f"APIエラー: {e}")
        return False

    return True


def main():
    """メイン関数"""
    print("=" * 60)
    print("Google Calendar API デモスクリプト")
    print("=" * 60)

    # 認証確認
    token_file = 'auth/calendar_token.json'
    if not os.path.exists(token_file):
        print(f"\nエラー: トークンファイルが見つかりません: {token_file}")
        print("\n事前準備:")
        print("  1. Google Cloud Console で OAuth2.0 認証情報を作成")
        print("  2. Google Calendar API を有効化")
        print("  3. 認証フローを実行してトークンを取得")
        print("\n詳細は docs/CALENDAR_API_USAGE.md を参照してください")
        sys.exit(1)

    # デモの選択
    print("\n実行するデモを選択してください:")
    print("  1. 基本操作（作成・取得・更新・削除）")
    print("  2. イベント一覧・検索")
    print("  3. バッチ操作")
    print("  4. アニメ配信スケジュール登録（実用例）")
    print("  5. すべて実行")
    print("  0. 終了")

    try:
        choice = input("\n選択 (0-5): ").strip()

        if choice == '0':
            print("終了します")
            return

        elif choice == '1':
            demo_basic_operations()

        elif choice == '2':
            demo_event_listing()

        elif choice == '3':
            demo_batch_operations()

        elif choice == '4':
            demo_anime_schedule()

        elif choice == '5':
            print("\nすべてのデモを実行します...")
            if demo_basic_operations():
                input("\nEnterキーを押して次のデモへ...")
            if demo_event_listing():
                input("\nEnterキーを押して次のデモへ...")
            if demo_batch_operations():
                input("\nEnterキーを押して次のデモへ...")
            demo_anime_schedule()

        else:
            print("無効な選択です")
            return

        print("\n" + "=" * 60)
        print("デモ終了")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        logger.error(f"予期しないエラー: {e}", exc_info=True)


if __name__ == '__main__':
    main()
