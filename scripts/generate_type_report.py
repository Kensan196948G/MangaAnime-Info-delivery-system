#!/usr/bin/env python3
"""
型チェックレポート生成スクリプト
"""
import subprocess
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


def run_mypy_on_file(file_path: str) -> Dict[str, Any]:
    """
    個別ファイルに対してmypyを実行

    Args:
        file_path: チェック対象ファイルのパス

    Returns:
        Dict[str, Any]: チェック結果
    """
    try:
        result = subprocess.run(
            ['mypy', '--show-error-codes', '--no-error-summary', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        output = result.stdout + result.stderr
        error_lines = [line for line in output.split('\n') if 'error:' in line]

        return {
            'file': file_path,
            'success': result.returncode == 0,
            'error_count': len(error_lines),
            'errors': error_lines[:10],  # 最初の10個のエラーのみ
            'full_output': output
        }

    except subprocess.TimeoutExpired:
        return {
            'file': file_path,
            'success': False,
            'error_count': -1,
            'errors': ['タイムアウト'],
            'full_output': ''
        }
    except Exception as e:
        return {
            'file': file_path,
            'success': False,
            'error_count': -1,
            'errors': [str(e)],
            'full_output': ''
        }


def generate_report(results: List[Dict[str, Any]]) -> str:
    """
    レポートを生成

    Args:
        results: チェック結果のリスト

    Returns:
        str: レポート文字列
    """
    report = []
    report.append("=" * 80)
    report.append("Python型チェックレポート")
    report.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    report.append("")

    # サマリー
    total_files = len(results)
    success_files = sum(1 for r in results if r['success'])
    total_errors = sum(r['error_count'] for r in results if r['error_count'] > 0)

    report.append("【サマリー】")
    report.append(f"  総ファイル数: {total_files}")
    report.append(f"  成功: {success_files} / {total_files}")
    report.append(f"  エラー総数: {total_errors}")
    report.append("")

    # 成功率
    success_rate = (success_files / total_files * 100) if total_files > 0 else 0
    report.append(f"  型チェック成功率: {success_rate:.1f}%")
    report.append("")

    # 詳細結果
    report.append("-" * 80)
    report.append("【詳細結果】")
    report.append("-" * 80)

    for result in results:
        file_name = Path(result['file']).name
        status = "✓ 成功" if result['success'] else f"✗ 失敗 ({result['error_count']}エラー)"

        report.append("")
        report.append(f"ファイル: {result['file']}")
        report.append(f"ステータス: {status}")

        if not result['success'] and result['errors']:
            report.append("エラー詳細:")
            for error in result['errors'][:5]:  # 最初の5個のみ表示
                report.append(f"  - {error.strip()}")

            if len(result['errors']) > 5:
                report.append(f"  ... 他 {len(result['errors']) - 5} 件")

    report.append("")
    report.append("=" * 80)

    return "\n".join(report)


def main() -> int:
    """
    メイン処理

    Returns:
        int: 終了コード
    """
    # チェック対象ファイルのリスト
    typed_modules = [
        "modules/types_helper.py",
        "modules/config_typed.py",
        "modules/mailer_typed.py",
        "modules/calendar_typed.py",
        "modules/anime_anilist_typed.py",
        "modules/manga_rss_typed.py",
        "modules/filter_logic_typed.py",
    ]

    # プロジェクトルートに移動
    project_root = Path(__file__).parent.parent
    print(f"プロジェクトルート: {project_root}")

    # 各ファイルをチェック
    results: List[Dict[str, Any]] = []

    print("\n型チェック実行中...")
    for module in typed_modules:
        module_path = project_root / module
        if module_path.exists():
            print(f"  チェック中: {module}")
            result = run_mypy_on_file(str(module_path))
            results.append(result)
        else:
            print(f"  警告: {module} が見つかりません")
            results.append({
                'file': module,
                'success': False,
                'error_count': 0,
                'errors': ['ファイルが存在しません'],
                'full_output': ''
            })

    # レポート生成
    report_text = generate_report(results)

    # コンソール出力
    print("\n" + report_text)

    # ファイル出力
    report_path = project_root / "docs" / "reports" / "type_check_report.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"\nレポートを保存しました: {report_path}")

    # JSON形式でも保存
    json_path = project_root / "docs" / "reports" / "type_check_report.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f, indent=2, ensure_ascii=False)

    print(f"JSON形式も保存しました: {json_path}")

    # 終了コード
    all_success = all(r['success'] for r in results)
    return 0 if all_success else 1


if __name__ == '__main__':
    sys.exit(main())
