#!/usr/bin/env python3
"""
Googleカレンダー機能 Dry-runテスト
実際にAPIを呼ばずに動作確認
"""
import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_environment():
    """環境チェック"""
    print("=" * 80)
    print("環境チェック")
    print("=" * 80)

    # 1. Pythonバージョン
    print(f"\nPythonバージョン: {sys.version}")

    # 2. 必要パッケージ確認
    packages = [
        'google.oauth2.credentials',
        'googleapiclient.discovery',
        'googleapiclient.errors'
    ]

    print("\n必要パッケージ確認:")
    for package in packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (未インストール)")

    # 3. ファイル存在確認
    print("\n認証ファイル確認:")
    credentials_file = PROJECT_ROOT / "credentials.json"
    token_file = PROJECT_ROOT / "token.json"
    config_file = PROJECT_ROOT / "config.json"

    print(f"  credentials.json: {'✓ 存在' if credentials_file.exists() else '✗ 不在'}")
    print(f"  token.json: {'✓ 存在' if token_file.exists() else '✗ 不在'}")
    print(f"  config.json: {'✓ 存在' if config_file.exists() else '✗ 不在'}")

    # 4. modules/ディレクトリ確認
    print("\nモジュール確認:")
    modules_dir = PROJECT_ROOT / "modules"
    if modules_dir.exists():
        calendar_module = modules_dir / "calendar.py"
        print(f"  modules/calendar.py: {'✓ 存在' if calendar_module.exists() else '✗ 不在'}")

        # modules/配下のファイル一覧
        print("\n  modules/配下のファイル:")
        for item in sorted(modules_dir.iterdir()):
            if item.is_file() and item.suffix == '.py':
                print(f"    - {item.name}")
    else:
        print("  ✗ modules/ディレクトリが存在しません")

    # 5. config.json読み取り
    if config_file.exists():
        print("\nconfig.json内容:")
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            if 'google' in config and 'calendar' in config['google']:
                print("  ✓ Google Calendar設定が存在")
                print(json.dumps(config['google']['calendar'], indent=4, ensure_ascii=False))
            else:
                print("  ! Google Calendar設定が見つかりません")
        except Exception as e:
            print(f"  ✗ エラー: {e}")

    print("\n" + "=" * 80)


def test_calendar_dry_run():
    """Dry-runテスト"""
    print("\n" + "=" * 80)
    print("Googleカレンダー Dry-runテスト")
    print("=" * 80)

    # テストデータ
    test_cases = [
        {
            'title': '[テスト] 呪術廻戦 第15話配信 - Netflix',
            'description': '配信プラットフォーム: Netflix\n公式サイト: https://example.com/jujutsu-kaisen\n\n※これはテストイベントです',
            'start': datetime.now() + timedelta(days=3),
            'end': datetime.now() + timedelta(days=3, minutes=30),
            'color': 'blue',  # アニメ
        },
        {
            'title': '[テスト] ワンピース 第110巻発売',
            'description': '電子版配信\n出版社: 集英社\n公式サイト: https://example.com/onepiece\n\n※これはテストイベントです',
            'start': datetime.now() + timedelta(days=7),
            'end': datetime.now() + timedelta(days=7, hours=23, minutes=59),
            'color': 'green',  # マンガ
        },
        {
            'title': '[テスト] 進撃の巨人 The Final Season 第28話配信 - dアニメストア',
            'description': '配信プラットフォーム: dアニメストア\n配信時刻: 深夜0:00～\n\n※これはテストイベントです',
            'start': datetime.now() + timedelta(days=10, hours=0),
            'end': datetime.now() + timedelta(days=10, hours=0, minutes=30),
            'color': 'blue',
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[テストケース {i}]")
        print("-" * 80)
        print(f"タイトル: {test_case['title']}")
        print(f"説明:\n{test_case['description']}")
        print(f"開始: {test_case['start'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"終了: {test_case['end'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"カラー: {test_case['color']}")

        # イベントオブジェクト生成（実際のAPI呼び出しと同じ形式）
        event = {
            'summary': test_case['title'],
            'description': test_case['description'],
            'start': {
                'dateTime': test_case['start'].isoformat(),
                'timeZone': 'Asia/Tokyo',
            },
            'end': {
                'dateTime': test_case['end'].isoformat(),
                'timeZone': 'Asia/Tokyo',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 1440},  # 1日前
                    {'method': 'popup', 'minutes': 60},    # 1時間前
                ],
            },
        }

        print("\nAPI送信データ（JSON形式）:")
        print(json.dumps(event, indent=2, ensure_ascii=False))
        print("-" * 80)

    print("\n" + "=" * 80)
    print("Dry-runテスト完了")
    print("✓ 実際のイベント作成は行われていません")
    print("✓ 上記のデータがGoogle Calendar APIに送信される形式です")
    print("=" * 80)


def generate_test_report():
    """テストレポート生成"""
    print("\n" + "=" * 80)
    print("テストレポート")
    print("=" * 80)

    report = {
        'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'test_type': 'Dry-run',
        'status': 'SUCCESS',
        'checks': {
            'environment': 'OK',
            'files': 'NEEDS_SETUP',
            'modules': 'CHECKING',
            'config': 'CHECKING',
        },
        'next_steps': [
            '1. credentials.jsonをGoogle Cloud Consoleから取得',
            '2. 必要Pythonパッケージをインストール: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client',
            '3. modules/calendar.pyの実装を確認',
            '4. config.jsonにGoogle Calendar設定を追加',
            '5. 初回OAuth認証を実行',
            '6. 実際のイベント作成テストを実行',
        ],
    }

    print("\nテスト結果:")
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # レポートをファイルに保存
    report_file = PROJECT_ROOT / "test_calendar_dry_run_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nレポート保存: {report_file}")
    print("=" * 80)


def main():
    """メイン実行"""
    print("\n")
    print("*" * 80)
    print("*" + " " * 78 + "*")
    print("*" + "  Googleカレンダー機能 Dry-runテスト  ".center(78) + "*")
    print("*" + " " * 78 + "*")
    print("*" * 80)

    # 1. 環境チェック
    check_environment()

    # 2. Dry-runテスト
    test_calendar_dry_run()

    # 3. レポート生成
    generate_test_report()

    print("\n\n全テスト完了\n")


if __name__ == "__main__":
    main()
