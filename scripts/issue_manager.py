#!/usr/bin/env python3
"""
Issue自動管理システム

連続成功時に古いIssueを自動クローズ、重複Issueの統合、Issue数監視を行います。
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GitHubIssueManager:
    """GitHub Issue管理クラス"""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get('GITHUB_TOKEN')
        if not self.token:
            logger.warning("GITHUB_TOKEN が設定されていません")

    def _run_gh_command(self, cmd: List[str]) -> Dict:
        """GitHub CLIコマンドを実行"""
        try:
            result = subprocess.run(
                ['gh'] + cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, 'GH_TOKEN': self.token} if self.token else os.environ
            )

            if result.returncode == 0:
                return {
                    'success': True,
                    'output': result.stdout.strip(),
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'output': None,
                    'error': result.stderr.strip()
                }
        except Exception as e:
            logger.error(f"GitHub CLIコマンド実行エラー: {e}")
            return {
                'success': False,
                'output': None,
                'error': str(e)
            }

    def list_issues(self, label: str = 'auto-repair', state: str = 'open') -> List[Dict]:
        """Issueリストを取得"""
        result = self._run_gh_command([
            'issue', 'list',
            '--label', label,
            '--state', state,
            '--json', 'number,title,createdAt,updatedAt,labels,comments',
            '--limit', '100'
        ])

        if result['success']:
            try:
                return json.loads(result['output'])
            except json.JSONDecodeError:
                logger.error("Issue リストのJSON解析エラー")
                return []
        else:
            logger.error(f"Issue リスト取得失敗: {result['error']}")
            return []

    def close_issue(self, issue_number: int, comment: str = None) -> bool:
        """Issueをクローズ"""
        cmd = ['issue', 'close', str(issue_number)]

        if comment:
            cmd.extend(['--comment', comment])

        result = self._run_gh_command(cmd)

        if result['success']:
            logger.info(f"Issue #{issue_number} をクローズしました")
            return True
        else:
            logger.error(f"Issue #{issue_number} のクローズ失敗: {result['error']}")
            return False

    def add_label(self, issue_number: int, label: str) -> bool:
        """Issueにラベルを追加"""
        result = self._run_gh_command([
            'issue', 'edit', str(issue_number),
            '--add-label', label
        ])

        return result['success']

    def remove_label(self, issue_number: int, label: str) -> bool:
        """Issueからラベルを削除"""
        result = self._run_gh_command([
            'issue', 'edit', str(issue_number),
            '--remove-label', label
        ])

        return result['success']

    def comment_on_issue(self, issue_number: int, comment: str) -> bool:
        """Issueにコメント"""
        result = self._run_gh_command([
            'issue', 'comment', str(issue_number),
            '--body', comment
        ])

        return result['success']


class IssueAutoManager:
    """Issue自動管理ロジック"""

    def __init__(self, manager: GitHubIssueManager):
        self.manager = manager
        self.closed_count = 0
        self.consolidated_count = 0
        self.warning_count = 0

    def close_old_issues(self, days: int = 7) -> int:
        """古いIssueを自動クローズ"""
        logger.info(f"{days}日以上古いIssueをクローズします...")

        issues = self.manager.list_issues(state='open')
        cutoff_date = datetime.now() - timedelta(days=days)

        for issue in issues:
            updated_at = datetime.fromisoformat(issue['updatedAt'].replace('Z', '+00:00'))

            if updated_at < cutoff_date:
                comment = f"⏰ {days}日間更新がないため、自動的にクローズしました。"
                if self.manager.close_issue(issue['number'], comment):
                    self.manager.add_label(issue['number'], 'auto-closed-stale')
                    self.closed_count += 1
                    logger.info(f"古いIssue #{issue['number']} をクローズ")

        logger.info(f"{self.closed_count}個の古いIssueをクローズしました")
        return self.closed_count

    def consolidate_duplicate_issues(self) -> int:
        """重複Issueを統合"""
        logger.info("重複Issueをチェック中...")

        issues = self.manager.list_issues(state='open')

        # タイトルの類似度で重複を検出（簡易版）
        seen_titles = {}

        for issue in issues:
            # タイトルを正規化
            normalized_title = issue['title'].lower().replace('自動修復失敗', '').strip()

            if normalized_title in seen_titles:
                # 重複発見
                original_issue = seen_titles[normalized_title]

                comment = f"🔗 重複Issue: #{original_issue} に統合されました"
                if self.manager.close_issue(issue['number'], comment):
                    self.manager.add_label(issue['number'], 'duplicate')
                    self.consolidated_count += 1

                    # 元のIssueにコメント
                    self.manager.comment_on_issue(
                        original_issue,
                        f"関連Issue: #{issue['number']} が重複としてクローズされました"
                    )

                    logger.info(f"重複Issue #{issue['number']} を #{original_issue} に統合")
            else:
                seen_titles[normalized_title] = issue['number']

        logger.info(f"{self.consolidated_count}個の重複Issueを統合しました")
        return self.consolidated_count

    def check_issue_threshold(self, threshold: int = 10) -> bool:
        """Issue数が閾値を超えているかチェック"""
        issues = self.manager.list_issues(state='open')
        issue_count = len(issues)

        logger.info(f"現在のオープンIssue数: {issue_count}")

        if issue_count > threshold:
            self.warning_count += 1
            logger.warning(f"⚠️ オープンIssue数が閾値({threshold})を超えています: {issue_count}")

            # 警告Issue作成
            warning_msg = f"""
## ⚠️ Issue数警告

現在のオープンIssue数が閾値を超えています。

**オープンIssue数**: {issue_count} / {threshold}

### 推奨アクション
1. 古いIssueを手動で確認してクローズ
2. 重複Issueを統合
3. 閾値の見直し

### 最近のIssue
{self._format_recent_issues(issues[:5])}

---
🤖 自動生成された警告
            """

            # 同じ警告Issueが既に存在するかチェック
            warning_issues = [i for i in issues if 'Issue数警告' in i['title']]

            if not warning_issues:
                # 新規警告Issue作成
                subprocess.run(
                    ['gh', 'issue', 'create',
                     '--title', f'⚠️ Issue数警告 - {datetime.now().strftime("%Y-%m-%d")}',
                     '--body', warning_msg,
                     '--label', 'auto-repair,warning'],
                    capture_output=True,
                    text=True,
                    env={**os.environ, 'GH_TOKEN': self.manager.token} if self.manager.token else os.environ
                )

            return False
        else:
            logger.info("✅ Issue数は正常範囲内です")
            return True

    def _format_recent_issues(self, issues: List[Dict]) -> str:
        """最近のIssueをフォーマット"""
        lines = []
        for issue in issues:
            lines.append(f"- #{issue['number']}: {issue['title']} ({issue['updatedAt'][:10]})")
        return '\n'.join(lines)

    def close_issues_after_success(self, success_count: int = 3) -> int:
        """連続成功後にIssueをクローズ"""
        logger.info(f"{success_count}回連続成功した後、関連Issueをクローズします...")

        # repair_summary.json から成功履歴を確認
        if not Path('repair_summary.json').exists():
            logger.warning("修復サマリーが見つかりません")
            return 0

        try:
            with open('repair_summary.json', 'r', encoding='utf-8') as f:
                summary = json.load(f)

            final_status = summary.get('final_status', '')

            if final_status in ['success', 'partial_success', 'improved']:
                # 成功時に関連Issueをクローズ
                issues = self.manager.list_issues(label='auto-repair', state='open')

                for issue in issues:
                    # クリティカルでないIssueをクローズ
                    labels = [label['name'] for label in issue.get('labels', [])]

                    if 'critical' not in labels:
                        comment = f"✅ 自動修復が成功したため、このIssueをクローズします（ステータス: {final_status}）"
                        if self.manager.close_issue(issue['number'], comment):
                            self.manager.add_label(issue['number'], 'auto-closed-success')
                            self.closed_count += 1
                            logger.info(f"成功により Issue #{issue['number']} をクローズ")

        except Exception as e:
            logger.error(f"成功後のIssueクローズエラー: {e}")

        return self.closed_count


def main():
    parser = argparse.ArgumentParser(description='Issue自動管理システム')
    parser.add_argument('--close-old', type=int, metavar='DAYS',
                        help='指定日数以上古いIssueをクローズ')
    parser.add_argument('--consolidate-duplicates', action='store_true',
                        help='重複Issueを統合')
    parser.add_argument('--check-threshold', type=int, metavar='COUNT',
                        help='Issue数の閾値をチェック')
    parser.add_argument('--close-on-success', type=int, metavar='COUNT',
                        help='連続成功回数の後にIssueをクローズ')
    parser.add_argument('--all', action='store_true',
                        help='すべての管理タスクを実行')

    args = parser.parse_args()

    # GitHub Issue Manager初期化
    manager_gh = GitHubIssueManager()
    manager = IssueAutoManager(manager_gh)

    results = {
        'closed_old': 0,
        'consolidated': 0,
        'warnings': 0,
        'closed_success': 0
    }

    # すべての管理タスクを実行
    if args.all:
        results['closed_old'] = manager.close_old_issues(days=7)
        results['consolidated'] = manager.consolidate_duplicate_issues()
        manager.check_issue_threshold(threshold=10)
        results['closed_success'] = manager.close_issues_after_success(success_count=3)

    # 個別タスク実行
    if args.close_old:
        results['closed_old'] = manager.close_old_issues(days=args.close_old)

    if args.consolidate_duplicates:
        results['consolidated'] = manager.consolidate_duplicate_issues()

    if args.check_threshold:
        manager.check_issue_threshold(threshold=args.check_threshold)

    if args.close_on_success:
        results['closed_success'] = manager.close_issues_after_success(
            success_count=args.close_on_success
        )

    # サマリー出力
    logger.info("\n" + "="*60)
    logger.info("Issue自動管理完了")
    logger.info(f"  クローズした古いIssue: {results['closed_old']}")
    logger.info(f"  統合した重複Issue: {results['consolidated']}")
    logger.info(f"  成功によりクローズ: {results['closed_success']}")
    logger.info("="*60)

    # 結果をJSONで保存
    with open('issue_management_summary.json', 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f, indent=2, ensure_ascii=False)

    sys.exit(0)


if __name__ == '__main__':
    main()
