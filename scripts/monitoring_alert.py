#!/usr/bin/env python3
"""
CI/CD監視・アラートシステム

修復成功率のトラッキング、異常検知、アラート通知を行います。
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MetricsCollector:
    """メトリクス収集クラス"""

    def __init__(self, log_dir: Path = Path('logs')):
        self.log_dir = log_dir
        self.metrics = defaultdict(list)

    def collect_repair_metrics(self) -> Dict:
        """修復メトリクスを収集"""
        metrics = {
            'total_repairs': 0,
            'successful_repairs': 0,
            'failed_repairs': 0,
            'success_rate': 0.0,
            'average_loops': 0.0,
            'error_reduction_rate': 0.0,
            'recent_failures': []
        }

        # repair_summary.json を読み込み
        summary_files = list(self.log_dir.glob('repair_summary_*.json'))
        summary_files.append(Path('repair_summary.json'))

        valid_summaries = []

        for summary_file in summary_files:
            if summary_file.exists():
                try:
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        valid_summaries.append(data)
                except Exception as e:
                    logger.warning(f"{summary_file}の読み込みエラー: {e}")

        if not valid_summaries:
            logger.warning("メトリクス用のサマリーファイルが見つかりません")
            return metrics

        # メトリクス計算
        total_success = 0
        total_failed = 0
        total_loops = 0
        total_reduction = 0.0

        for summary in valid_summaries:
            final_status = summary.get('final_status', '')

            if final_status in ['success', 'partial_success', 'improved']:
                total_success += 1
            elif final_status == 'failed':
                total_failed += 1
                # 最近の失敗を記録
                if len(metrics['recent_failures']) < 10:
                    metrics['recent_failures'].append({
                        'timestamp': summary.get('timestamp', ''),
                        'loops': summary.get('total_loops', 0),
                        'errors': len(summary.get('detected_errors', []))
                    })

            total_loops += summary.get('total_loops', 0)
            total_reduction += summary.get('error_reduction_rate', 0.0)

        metrics['total_repairs'] = len(valid_summaries)
        metrics['successful_repairs'] = total_success
        metrics['failed_repairs'] = total_failed
        metrics['success_rate'] = (total_success / len(valid_summaries) * 100) if valid_summaries else 0
        metrics['average_loops'] = total_loops / len(valid_summaries) if valid_summaries else 0
        metrics['error_reduction_rate'] = total_reduction / len(valid_summaries) if valid_summaries else 0

        return metrics

    def collect_ci_metrics(self) -> Dict:
        """CI/CDメトリクスを収集"""
        metrics = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'average_duration': 0.0,
            'recent_runs': []
        }

        # GitHub Actions の実行履歴を取得（gh CLI使用）
        try:
            result = subprocess.run(
                ['gh', 'run', 'list', '--limit', '50', '--json',
                 'conclusion,status,createdAt,updatedAt,name,databaseId'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                runs = json.loads(result.stdout)

                for run in runs:
                    conclusion = run.get('conclusion', '')

                    if conclusion == 'success':
                        metrics['successful_runs'] += 1
                    elif conclusion in ['failure', 'timed_out', 'cancelled']:
                        metrics['failed_runs'] += 1

                    metrics['total_runs'] += 1

                    # 最近の実行を記録
                    if len(metrics['recent_runs']) < 10:
                        metrics['recent_runs'].append({
                            'name': run.get('name', ''),
                            'conclusion': conclusion,
                            'created_at': run.get('createdAt', '')
                        })

                # 成功率計算
                if metrics['total_runs'] > 0:
                    metrics['success_rate'] = (
                        metrics['successful_runs'] / metrics['total_runs'] * 100
                    )

        except Exception as e:
            logger.error(f"CI メトリクス収集エラー: {e}")

        return metrics


class AnomalyDetector:
    """異常検知クラス"""

    def __init__(self, metrics: Dict):
        self.metrics = metrics
        self.anomalies = []

    def detect_continuous_failures(self, threshold: int = 10) -> bool:
        """連続失敗を検知"""
        recent_failures = self.metrics.get('recent_failures', [])

        if len(recent_failures) >= threshold:
            self.anomalies.append({
                'type': 'continuous_failures',
                'severity': 'critical',
                'message': f'直近{len(recent_failures)}回の修復が失敗しています',
                'threshold': threshold
            })
            return True

        return False

    def detect_low_success_rate(self, threshold: float = 50.0) -> bool:
        """成功率低下を検知"""
        success_rate = self.metrics.get('success_rate', 0.0)

        if success_rate < threshold:
            self.anomalies.append({
                'type': 'low_success_rate',
                'severity': 'high',
                'message': f'修復成功率が低下しています: {success_rate:.1f}%',
                'threshold': threshold,
                'current_value': success_rate
            })
            return True

        return False

    def detect_high_loop_count(self, threshold: int = 8) -> bool:
        """ループ回数増加を検知"""
        avg_loops = self.metrics.get('average_loops', 0.0)

        if avg_loops > threshold:
            self.anomalies.append({
                'type': 'high_loop_count',
                'severity': 'medium',
                'message': f'平均ループ回数が増加しています: {avg_loops:.1f}',
                'threshold': threshold,
                'current_value': avg_loops
            })
            return True

        return False

    def detect_all_anomalies(self) -> List[Dict]:
        """すべての異常を検知"""
        self.detect_continuous_failures(threshold=5)
        self.detect_low_success_rate(threshold=60.0)
        self.detect_high_loop_count(threshold=7)

        logger.info(f"{len(self.anomalies)}個の異常を検出しました")
        return self.anomalies


class AlertNotifier:
    """アラート通知クラス"""

    def __init__(self):
        self.notifications = []

    def send_github_notification(self, anomalies: List[Dict], metrics: Dict) -> bool:
        """GitHub Issue/Discussion に通知"""
        if not anomalies:
            logger.info("異常がないため、通知をスキップします")
            return True

        # 異常の重大度別に分類
        critical_anomalies = [a for a in anomalies if a['severity'] == 'critical']
        high_anomalies = [a for a in anomalies if a['severity'] == 'high']
        medium_anomalies = [a for a in anomalies if a['severity'] == 'medium']

        # Issue本文を作成
        issue_body = f"""
## 🚨 CI/CD異常検知アラート

**検知時刻**: {datetime.now().isoformat()}

### 異常サマリー
- **クリティカル**: {len(critical_anomalies)}
- **高**: {len(high_anomalies)}
- **中**: {len(medium_anomalies)}

### 検出された異常

"""

        for anomaly in anomalies:
            severity_emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡'
            }.get(anomaly['severity'], '⚪')

            issue_body += f"""
#### {severity_emoji} {anomaly['type'].replace('_', ' ').title()}
- **メッセージ**: {anomaly['message']}
- **重大度**: {anomaly['severity']}
"""

            if 'threshold' in anomaly:
                issue_body += f"- **閾値**: {anomaly['threshold']}\n"

            if 'current_value' in anomaly:
                issue_body += f"- **現在値**: {anomaly['current_value']:.1f}\n"

        # メトリクス情報を追加
        issue_body += f"""

### 📊 現在のメトリクス

| 項目 | 値 |
|------|-----|
| 総修復回数 | {metrics.get('total_repairs', 0)} |
| 成功回数 | {metrics.get('successful_repairs', 0)} |
| 失敗回数 | {metrics.get('failed_repairs', 0)} |
| 成功率 | {metrics.get('success_rate', 0):.1f}% |
| 平均ループ回数 | {metrics.get('average_loops', 0):.1f} |
| エラー削減率 | {metrics.get('error_reduction_rate', 0):.1f}% |

### 推奨アクション
1. 直近の失敗ログを確認
2. 修復スクリプトのロジックを見直し
3. テスト環境で再現確認
4. 必要に応じて手動介入

---
🤖 自動生成されたアラート
"""

        # GitHub Issue作成
        try:
            result = subprocess.run(
                ['gh', 'issue', 'create',
                 '--title', f'🚨 CI/CD異常検知 - {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                 '--body', issue_body,
                 '--label', 'alert,monitoring,auto-repair'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info("GitHub Issue アラートを作成しました")
                return True
            else:
                logger.error(f"GitHub Issue 作成失敗: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"GitHub 通知エラー: {e}")
            return False

    def send_slack_notification(self, anomalies: List[Dict], webhook_url: str) -> bool:
        """Slack Webhook に通知（オプション）"""
        if not webhook_url:
            logger.info("Slack Webhook URLが設定されていません")
            return False

        try:
            import requests

            critical_count = len([a for a in anomalies if a['severity'] == 'critical'])

            payload = {
                'text': f'🚨 CI/CD異常検知: {len(anomalies)}個の異常を検出',
                'blocks': [
                    {
                        'type': 'section',
                        'text': {
                            'type': 'mrkdwn',
                            'text': f'*CI/CD異常検知アラート*\n{len(anomalies)}個の異常を検出しました（クリティカル: {critical_count}）'
                        }
                    }
                ]
            }

            for anomaly in anomalies[:5]:  # 最初の5個のみ
                payload['blocks'].append({
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': f"*{anomaly['type']}*: {anomaly['message']}"
                    }
                })

            response = requests.post(webhook_url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info("Slack通知を送信しました")
                return True
            else:
                logger.error(f"Slack通知失敗: {response.status_code}")
                return False

        except ImportError:
            logger.warning("requests ライブラリがインストールされていません")
            return False
        except Exception as e:
            logger.error(f"Slack通知エラー: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='CI/CD監視・アラートシステム')
    parser.add_argument('--collect-metrics', action='store_true',
                        help='メトリクスを収集')
    parser.add_argument('--detect-anomalies', action='store_true',
                        help='異常を検知')
    parser.add_argument('--send-alerts', action='store_true',
                        help='アラートを送信')
    parser.add_argument('--slack-webhook', type=str,
                        help='Slack Webhook URL')
    parser.add_argument('--all', action='store_true',
                        help='すべての監視タスクを実行')

    args = parser.parse_args()

    # メトリクス収集
    collector = MetricsCollector()
    repair_metrics = collector.collect_repair_metrics()
    ci_metrics = collector.collect_ci_metrics()

    combined_metrics = {**repair_metrics, **ci_metrics}

    logger.info("\n" + "="*60)
    logger.info("メトリクス収集完了")
    logger.info(f"  総修復回数: {repair_metrics['total_repairs']}")
    logger.info(f"  成功率: {repair_metrics['success_rate']:.1f}%")
    logger.info(f"  平均ループ回数: {repair_metrics['average_loops']:.1f}")
    logger.info("="*60)

    # 異常検知
    if args.detect_anomalies or args.all:
        detector = AnomalyDetector(combined_metrics)
        anomalies = detector.detect_all_anomalies()

        # アラート送信
        if (args.send_alerts or args.all) and anomalies:
            notifier = AlertNotifier()
            notifier.send_github_notification(anomalies, combined_metrics)

            # Slack通知（オプション）
            slack_webhook = args.slack_webhook or os.environ.get('SLACK_WEBHOOK_URL')
            if slack_webhook:
                notifier.send_slack_notification(anomalies, slack_webhook)

    # 結果をJSONで保存
    output = {
        'timestamp': datetime.now().isoformat(),
        'metrics': combined_metrics,
        'anomalies': detector.anomalies if args.detect_anomalies or args.all else []
    }

    with open('monitoring_report.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info("監視レポートを monitoring_report.json に保存しました")

    sys.exit(0)


if __name__ == '__main__':
    main()
