#!/usr/bin/env python3
"""
修復サマリーレポート生成スクリプト

repair_summary.jsonを読み込んでMarkdown形式のレポートを生成します。
"""

import json
import sys


def format_duration(seconds: float) -> str:
    """秒数を読みやすい形式に変換"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}時間"


def generate_summary_report(summary_file: str) -> str:
    """サマリーレポートを生成"""

    try:
        with open(summary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return "⚠️ 修復サマリーファイルが見つかりません"
    except json.JSONDecodeError:
        return "⚠️ 修復サマリーファイルの形式が不正です"

    # 基本情報
    timestamp = data.get('timestamp', 'N/A')
    duration = data.get('duration_seconds', 0)
    total_loops = data.get('total_loops', 0)
    max_loops = data.get('max_loops', 10)
    successful_repairs = data.get('successful_repairs', 0)
    failed_repairs = data.get('failed_repairs', 0)
    final_status = data.get('final_status', 'unknown')

    # ステータスアイコン
    status_icon = '✅' if final_status == 'success' else '❌'

    report = """
### {status_icon} 実行サマリー

| 項目 | 値 |
|------|-----|
| **実行日時** | {timestamp} |
| **実行時間** | {format_duration(duration)} |
| **ループ数** | {total_loops} / {max_loops} |
| **成功した修復** | {successful_repairs} |
| **失敗した修復** | {failed_repairs} |
| **最終ステータス** | {status_icon} {final_status.upper()} |

"""

    # 検出されたエラー
    detected_errors = data.get('detected_errors', [])

    if detected_errors:
        report += "### 🔍 検出されたエラー\n\n"

        # エラータイプ別に集計
        error_by_type = {}
        for error in detected_errors:
            error_type = error.get('type', 'Unknown')
            if error_type not in error_by_type:
                error_by_type[error_type] = []
            error_by_type[error_type].append(error)

        for error_type, errors in error_by_type.items():
            severity_icon = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }

            report += f"#### {error_type} ({len(errors)}個)\n\n"

            for i, error in enumerate(errors[:5], 1):  # 最大5個表示
                severity = error.get('severity', 'unknown')
                icon = severity_icon.get(severity, '⚪')
                message = error.get('message', 'N/A')

                report += f"{i}. {icon} {message[:100]}...\n"

            if len(errors) > 5:
                report += f"\n... 他 {len(errors) - 5} 個\n"

            report += "\n"
    else:
        report += "### ✅ 検出されたエラー\n\nエラーは検出されませんでした\n\n"

    # 修復試行履歴
    repair_attempts = data.get('repair_attempts', [])
    if repair_attempts:
        report += "### 🔧 修復試行履歴\n\n"

        for i, attempt in enumerate(repair_attempts[:10], 1):  # 最大10個表示
            timestamp = attempt.get('timestamp', 'N/A')
            error_type = attempt.get('error_type', 'Unknown')
            action = attempt.get('action', 'N/A')
            success = attempt.get('success', False)
            status_icon = '✅' if success else '❌'

            report += f"**{i}. {status_icon} {error_type}** ({timestamp})\n"
            report += f"   - アクション: {action}\n"

            output = attempt.get('output', '')
            if output and len(output) > 0:
                report += f"   - 出力: {output[:100]}...\n"

            report += "\n"

        if len(repair_attempts) > 10:
            report += f"... 他 {len(repair_attempts) - 10} 個の試行\n\n"

    # 推奨アクション
    recommendations = data.get('recommendations', [])
    if recommendations:
        report += "### 💡 推奨アクション\n\n"
        for rec in recommendations:
            report += f"- {rec}\n"
        report += "\n"

    # フッター
    report += "---\n"
    report += "🤖 このレポートは自動生成されました\n"

    return report


def main():
    if len(sys.argv) < 2:
        logger.info("使用方法: python generate_repair_summary.py <summary_file>")
        sys.exit(1)

    summary_file = sys.argv[1]
    report = generate_summary_report(summary_file)
    logger.info(report)


if __name__ == '__main__':
    main()
