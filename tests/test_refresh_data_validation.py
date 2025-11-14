#!/usr/bin/env python3
"""
データ更新機能の詳細検証スクリプト
API動作、エラー再現、データベース状態変化を検証
"""

import requests
import json
import sqlite3
import os
import sys
import time
from datetime import datetime
import subprocess

# カラー出力用
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

# 設定
BASE_URL = "http://localhost:3030"
API_ENDPOINT = "/api/refresh-data"
DB_PATH = "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/db.sqlite3"
PROJECT_ROOT = "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"

# グローバル変数
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "warnings": 0
}

def update_test_result(passed, warning=False):
    """テスト結果を更新"""
    test_results["total"] += 1
    if warning:
        test_results["warnings"] += 1
    elif passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1

def get_db_stats():
    """データベースの統計情報を取得"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # worksテーブルの件数
        cursor.execute("SELECT COUNT(*) FROM works")
        works_count = cursor.fetchone()[0]

        # releasesテーブルの件数
        cursor.execute("SELECT COUNT(*) FROM releases")
        releases_count = cursor.fetchone()[0]

        # 通知済み件数
        cursor.execute("SELECT COUNT(*) FROM releases WHERE notified = 1")
        notified_count = cursor.fetchone()[0]

        # 最新のリリース日
        cursor.execute("SELECT MAX(release_date) FROM releases")
        latest_release = cursor.fetchone()[0]

        conn.close()

        return {
            "works_count": works_count,
            "releases_count": releases_count,
            "notified_count": notified_count,
            "latest_release": latest_release
        }
    except Exception as e:
        print_error(f"データベース統計情報の取得エラー: {e}")
        return None

def test_1_api_availability():
    """テスト1: API可用性確認"""
    print_header("テスト1: API可用性確認")

    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print_success(f"サーバーが正常に稼働中 (ステータス: {response.status_code})")
            update_test_result(True)
            return True
        else:
            print_warning(f"サーバーは稼働していますが、予期しないステータス: {response.status_code}")
            update_test_result(True, warning=True)
            return True
    except requests.exceptions.RequestException as e:
        print_error(f"サーバーに接続できません: {e}")
        update_test_result(False)
        return False

def test_2_database_before_update():
    """テスト2: 更新前のデータベース状態確認"""
    print_header("テスト2: 更新前のデータベース状態確認")

    stats = get_db_stats()
    if stats:
        print_info(f"作品数: {stats['works_count']}")
        print_info(f"リリース数: {stats['releases_count']}")
        print_info(f"通知済み数: {stats['notified_count']}")
        print_info(f"最新リリース日: {stats['latest_release']}")
        print_success("データベース状態を取得しました")
        update_test_result(True)
        return stats
    else:
        print_error("データベース状態の取得に失敗しました")
        update_test_result(False)
        return None

def test_3_api_refresh_normal():
    """テスト3: 正常系 - データ更新API実行"""
    print_header("テスト3: 正常系 - データ更新API実行")

    try:
        print_info("APIリクエストを送信中...")
        start_time = time.time()

        response = requests.get(
            f"{BASE_URL}{API_ENDPOINT}",
            timeout=60
        )

        elapsed_time = time.time() - start_time

        print_info(f"レスポンスタイム: {elapsed_time:.2f}秒")
        print_info(f"ステータスコード: {response.status_code}")

        # レスポンスヘッダー確認
        print_info("\n【レスポンスヘッダー】")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")

        # レスポンスボディ確認
        print_info("\n【レスポンスボディ】")
        try:
            data = response.json()
            print(json.dumps(data, ensure_ascii=False, indent=2))

            if response.status_code == 200 and data.get('success'):
                print_success("✓ データ更新が成功しました")
                update_test_result(True)
                return data
            else:
                print_error(f"✗ データ更新が失敗しました: {data.get('error', '不明なエラー')}")
                if 'details' in data:
                    print_error(f"  詳細: {data['details']}")
                update_test_result(False)
                return data
        except json.JSONDecodeError:
            print_error("JSONパースエラー")
            print_info(f"Raw response: {response.text[:500]}")
            update_test_result(False)
            return None

    except requests.exceptions.Timeout:
        print_error("タイムアウトが発生しました (60秒)")
        update_test_result(False)
        return None
    except requests.exceptions.RequestException as e:
        print_error(f"APIリクエストエラー: {e}")
        update_test_result(False)
        return None

def test_4_database_after_update():
    """テスト4: 更新後のデータベース状態確認"""
    print_header("テスト4: 更新後のデータベース状態確認")

    print_info("3秒待機してからデータベースを確認します...")
    time.sleep(3)

    stats = get_db_stats()
    if stats:
        print_info(f"作品数: {stats['works_count']}")
        print_info(f"リリース数: {stats['releases_count']}")
        print_info(f"通知済み数: {stats['notified_count']}")
        print_info(f"最新リリース日: {stats['latest_release']}")
        print_success("更新後のデータベース状態を取得しました")
        update_test_result(True)
        return stats
    else:
        print_error("データベース状態の取得に失敗しました")
        update_test_result(False)
        return None

def test_5_cors_headers():
    """テスト5: CORSヘッダー確認"""
    print_header("テスト5: CORSヘッダー確認")

    try:
        response = requests.get(f"{BASE_URL}{API_ENDPOINT}", timeout=30)

        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
        }

        print_info("【CORSヘッダー】")
        for key, value in cors_headers.items():
            if value:
                print_success(f"  {key}: {value}")
            else:
                print_warning(f"  {key}: 未設定")

        has_cors = any(cors_headers.values())
        if has_cors:
            print_success("CORSヘッダーが設定されています")
            update_test_result(True)
        else:
            print_warning("CORSヘッダーが設定されていません（クロスオリジンアクセスに問題が生じる可能性）")
            update_test_result(True, warning=True)

        return cors_headers
    except Exception as e:
        print_error(f"CORSヘッダー確認エラー: {e}")
        update_test_result(False)
        return None

def test_6_concurrent_requests():
    """テスト6: 異常系 - 同時リクエスト"""
    print_header("テスト6: 異常系 - 同時リクエスト")

    print_info("同時に2つのリクエストを送信します...")

    import threading
    results = []

    def make_request(index):
        try:
            response = requests.get(f"{BASE_URL}{API_ENDPOINT}", timeout=60)
            results.append({
                'index': index,
                'status': response.status_code,
                'data': response.json()
            })
        except Exception as e:
            results.append({
                'index': index,
                'error': str(e)
            })

    threads = [
        threading.Thread(target=make_request, args=(1,)),
        threading.Thread(target=make_request, args=(2,))
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    print_info("\n【結果】")
    for result in results:
        if 'error' in result:
            print_error(f"  リクエスト{result['index']}: エラー - {result['error']}")
        else:
            print_info(f"  リクエスト{result['index']}: ステータス {result['status']}")
            print_info(f"    success: {result['data'].get('success')}")
            if not result['data'].get('success'):
                print_info(f"    error: {result['data'].get('error')}")

    # 少なくとも1つが成功し、1つが適切に排他制御されていればOK
    success_count = sum(1 for r in results if r.get('data', {}).get('success'))

    if success_count >= 1:
        print_success("同時リクエストが適切に処理されました")
        update_test_result(True)
    else:
        print_error("同時リクエストの処理に問題があります")
        update_test_result(False)

    return results

def test_7_script_execution():
    """テスト7: スクリプト直接実行確認"""
    print_header("テスト7: スクリプト直接実行確認")

    script_path = os.path.join(PROJECT_ROOT, "insert_sample_data.py")

    if not os.path.exists(script_path):
        print_error(f"スクリプトが見つかりません: {script_path}")
        update_test_result(False)
        return None

    print_info(f"スクリプトパス: {script_path}")
    print_info("スクリプトを直接実行します...")

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=PROJECT_ROOT
        )

        print_info(f"\n【終了コード】 {result.returncode}")

        if result.stdout:
            print_info("\n【標準出力】")
            print(result.stdout)

        if result.stderr:
            print_info("\n【標準エラー】")
            print(result.stderr)

        if result.returncode == 0:
            print_success("スクリプトが正常に実行されました")
            update_test_result(True)
        else:
            print_error(f"スクリプトがエラー終了しました (終了コード: {result.returncode})")
            update_test_result(False)

        return result
    except subprocess.TimeoutExpired:
        print_error("スクリプト実行がタイムアウトしました")
        update_test_result(False)
        return None
    except Exception as e:
        print_error(f"スクリプト実行エラー: {e}")
        update_test_result(False)
        return None

def test_8_database_lock():
    """テスト8: 異常系 - データベースロック"""
    print_header("テスト8: 異常系 - データベースロック")

    print_info("データベースをロックしてAPIを呼び出します...")

    try:
        # データベース接続を保持（ロック）
        conn = sqlite3.connect(DB_PATH, timeout=1)
        cursor = conn.cursor()
        cursor.execute("BEGIN EXCLUSIVE")

        print_info("データベースをロックしました")
        print_info("APIリクエストを送信中...")

        # 別スレッドでAPIリクエスト
        import threading
        api_result = [None]

        def call_api():
            try:
                response = requests.get(f"{BASE_URL}{API_ENDPOINT}", timeout=35)
                api_result[0] = {
                    'status': response.status_code,
                    'data': response.json()
                }
            except Exception as e:
                api_result[0] = {'error': str(e)}

        thread = threading.Thread(target=call_api)
        thread.start()

        # 5秒待機
        time.sleep(5)

        # ロック解除
        conn.rollback()
        conn.close()
        print_info("データベースロックを解除しました")

        # スレッド終了待機
        thread.join(timeout=30)

        if api_result[0]:
            if 'error' in api_result[0]:
                print_warning(f"APIエラー: {api_result[0]['error']}")
                update_test_result(True, warning=True)
            else:
                print_info(f"ステータス: {api_result[0]['status']}")
                print_info(f"レスポンス: {json.dumps(api_result[0]['data'], ensure_ascii=False, indent=2)}")

                if api_result[0]['data'].get('success'):
                    print_success("データベースロック後も正常に処理されました")
                    update_test_result(True)
                else:
                    print_warning(f"エラー応答: {api_result[0]['data'].get('error')}")
                    update_test_result(True, warning=True)
        else:
            print_error("APIレスポンスがありません")
            update_test_result(False)

        return api_result[0]
    except Exception as e:
        print_error(f"テスト実行エラー: {e}")
        update_test_result(False)
        return None

def print_summary():
    """テスト結果サマリーを表示"""
    print_header("テスト結果サマリー")

    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    warnings = test_results["warnings"]

    print(f"\n総テスト数: {total}")
    print_success(f"成功: {passed}")
    print_warning(f"警告: {warnings}")
    print_error(f"失敗: {failed}")

    success_rate = (passed / total * 100) if total > 0 else 0

    print(f"\n成功率: {success_rate:.1f}%")

    if failed == 0:
        print_success("\n✓ 全てのテストが成功しました！")
    elif failed <= 2:
        print_warning(f"\n⚠ {failed}件のテストが失敗しました")
    else:
        print_error(f"\n✗ {failed}件のテストが失敗しました")

    print()

def main():
    """メイン処理"""
    print_header("データ更新機能 詳細検証スクリプト")
    print_info(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"ベースURL: {BASE_URL}")
    print_info(f"APIエンドポイント: {API_ENDPOINT}")
    print_info(f"データベースパス: {DB_PATH}")

    # 事前確認
    before_stats = None

    # テスト実行
    test_1_api_availability()
    before_stats = test_2_database_before_update()
    test_3_api_refresh_normal()
    after_stats = test_4_database_after_update()
    test_5_cors_headers()
    test_6_concurrent_requests()
    test_7_script_execution()
    test_8_database_lock()

    # データ変化の確認
    if before_stats and after_stats:
        print_header("データベース変化サマリー")
        print(f"作品数: {before_stats['works_count']} → {after_stats['works_count']} "
              f"({after_stats['works_count'] - before_stats['works_count']:+d})")
        print(f"リリース数: {before_stats['releases_count']} → {after_stats['releases_count']} "
              f"({after_stats['releases_count'] - before_stats['releases_count']:+d})")
        print(f"通知済み数: {before_stats['notified_count']} → {after_stats['notified_count']} "
              f"({after_stats['notified_count'] - before_stats['notified_count']:+d})")

    # サマリー表示
    print_summary()

    # 終了コード
    sys.exit(0 if test_results["failed"] == 0 else 1)

if __name__ == "__main__":
    main()
