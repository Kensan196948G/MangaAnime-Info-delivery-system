#!/usr/bin/env python3
"""
エラーシナリオ検証スクリプト
意図的にエラー条件を作り出して動作を確認
"""

import requests
import json
import os
import shutil
import time

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

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

BASE_URL = "http://localhost:3030"
API_ENDPOINT = "/api/refresh-data"
PROJECT_ROOT = "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"

def test_scenario_1_missing_script():
    """シナリオ1: スクリプトファイルが存在しない場合"""
    print_header("エラーシナリオ1: スクリプトファイルが存在しない")

    script_path = os.path.join(PROJECT_ROOT, "insert_sample_data.py")
    backup_path = script_path + ".backup_test"

    # スクリプトをバックアップ
    if os.path.exists(script_path):
        print_info("スクリプトを一時的にリネームします...")
        shutil.move(script_path, backup_path)

    try:
        print_info("APIを呼び出します...")
        response = requests.get(f"{BASE_URL}{API_ENDPOINT}", timeout=30)

        print_info(f"ステータスコード: {response.status_code}")
        print_info(f"レスポンス: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

        if response.status_code == 404:
            print_success("404エラーが正しく返されました")
        else:
            print_error(f"予期しないステータスコード: {response.status_code}")

    except Exception as e:
        print_error(f"エラー: {e}")
    finally:
        # スクリプトを復元
        if os.path.exists(backup_path):
            print_info("スクリプトを復元します...")
            shutil.move(backup_path, script_path)
            print_success("スクリプトを復元しました")

def test_scenario_2_script_error():
    """シナリオ2: スクリプト実行エラー"""
    print_header("エラーシナリオ2: スクリプト実行エラー")

    error_script_path = os.path.join(PROJECT_ROOT, "test_error_script.py")

    # エラーを起こすスクリプトを作成
    with open(error_script_path, "w") as f:
        f.write("""#!/usr/bin/env python3
import sys
print("This script will fail")
sys.exit(1)  # エラー終了
""")

    print_info("エラースクリプトを作成しました")

    # 元のスクリプトをバックアップ
    script_path = os.path.join(PROJECT_ROOT, "insert_sample_data.py")
    backup_path = script_path + ".backup_test2"

    if os.path.exists(script_path):
        shutil.move(script_path, backup_path)
        shutil.copy(error_script_path, script_path)

    try:
        print_info("APIを呼び出します...")
        response = requests.get(f"{BASE_URL}{API_ENDPOINT}", timeout=30)

        print_info(f"ステータスコード: {response.status_code}")
        data = response.json()
        print_info(f"レスポンス: {json.dumps(data, ensure_ascii=False, indent=2)}")

        if response.status_code == 500 and not data.get('success'):
            print_success("500エラーが正しく返され、エラーメッセージが含まれています")
        else:
            print_error(f"予期しない動作: ステータス={response.status_code}, success={data.get('success')}")

    except Exception as e:
        print_error(f"エラー: {e}")
    finally:
        # 復元
        if os.path.exists(backup_path):
            print_info("スクリプトを復元します...")
            if os.path.exists(script_path):
                os.remove(script_path)
            shutil.move(backup_path, script_path)
        if os.path.exists(error_script_path):
            os.remove(error_script_path)
        print_success("クリーンアップ完了")

def test_scenario_3_response_headers():
    """シナリオ3: レスポンスヘッダー詳細確認"""
    print_header("レスポンスヘッダー詳細確認")

    try:
        print_info("APIを呼び出します...")
        response = requests.get(f"{BASE_URL}{API_ENDPOINT}", timeout=30)

        print_info("\n【全レスポンスヘッダー】")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")

        print_info("\n【重要なヘッダー確認】")

        # Content-Type確認
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            print_success(f"Content-Type: {content_type} ✓")
        else:
            print_error(f"Content-Type: {content_type} (application/jsonではない)")

        # CORS確認
        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        if cors_origin:
            print_success(f"CORS設定あり: {cors_origin}")
        else:
            print_error("CORS設定なし（フロントエンドで問題が起きる可能性）")

        # Caching確認
        cache_control = response.headers.get('Cache-Control')
        if cache_control:
            print_info(f"Cache-Control: {cache_control}")
        else:
            print_info("Cache-Control: 未設定")

    except Exception as e:
        print_error(f"エラー: {e}")

def test_scenario_4_json_parsing():
    """シナリオ4: JSONパース確認"""
    print_header("JSONレスポンスパース確認")

    try:
        print_info("APIを呼び出します...")
        response = requests.get(f"{BASE_URL}{API_ENDPOINT}", timeout=30)

        print_info("レスポンステキスト（生データ）:")
        print(f"  {response.text[:200]}")

        print_info("\nJSONパース試行...")
        data = response.json()

        print_info("\n【JSONフィールド確認】")
        expected_fields = ['success', 'message', 'timestamp']
        for field in expected_fields:
            if field in data:
                print_success(f"  ✓ {field}: {data[field]}")
            else:
                print_error(f"  ✗ {field}: 存在しません")

        # 追加フィールド確認
        if 'output' in data:
            print_info(f"  output フィールドあり (長さ: {len(data['output'])})")

        if 'error' in data:
            print_info(f"  error フィールドあり: {data['error']}")

    except json.JSONDecodeError as e:
        print_error(f"JSONパースエラー: {e}")
        print_info(f"レスポンステキスト: {response.text}")
    except Exception as e:
        print_error(f"エラー: {e}")

def test_scenario_5_multiple_rapid_requests():
    """シナリオ5: 高速連続リクエスト"""
    print_header("高速連続リクエストテスト")

    print_info("5回連続でAPIを呼び出します...")

    results = []
    for i in range(5):
        try:
            start = time.time()
            response = requests.get(f"{BASE_URL}{API_ENDPOINT}", timeout=30)
            elapsed = time.time() - start

            data = response.json()
            results.append({
                'index': i + 1,
                'status': response.status_code,
                'success': data.get('success'),
                'elapsed': elapsed
            })

            print_info(f"  リクエスト{i+1}: ステータス={response.status_code}, "
                      f"success={data.get('success')}, 時間={elapsed:.2f}秒")

            # 短い待機
            time.sleep(0.5)

        except Exception as e:
            print_error(f"  リクエスト{i+1}: エラー - {e}")
            results.append({
                'index': i + 1,
                'error': str(e)
            })

    # 結果サマリー
    print_info("\n【結果サマリー】")
    success_count = sum(1 for r in results if r.get('success'))
    avg_time = sum(r.get('elapsed', 0) for r in results) / len(results)

    print_info(f"  成功回数: {success_count}/{len(results)}")
    print_info(f"  平均応答時間: {avg_time:.2f}秒")

    if success_count == len(results):
        print_success("全てのリクエストが成功しました")
    else:
        print_error(f"{len(results) - success_count}件のリクエストが失敗しました")

def main():
    """メイン処理"""
    print_header("エラーシナリオ検証スクリプト")

    print("\n注意: このスクリプトは意図的にエラーを発生させます。")
    print("テスト終了後、全てのファイルは元の状態に戻されます。\n")

    input("Enterキーを押して開始...")

    test_scenario_3_response_headers()
    test_scenario_4_json_parsing()
    test_scenario_5_multiple_rapid_requests()
    test_scenario_1_missing_script()
    test_scenario_2_script_error()

    print_header("全テスト完了")
    print_success("全てのエラーシナリオテストが完了しました")

if __name__ == "__main__":
    main()
