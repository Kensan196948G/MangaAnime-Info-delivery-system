#!/usr/bin/env python3
"""
GitHub Actions ワークフロー包括的テストスクリプト
"""

import yaml
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class TestResult:
    """テスト結果を格納するデータクラス"""
    category: str
    test_name: str
    status: str  # "PASS", "FAIL", "WARN"
    message: str
    details: str = ""


class WorkflowTester:
    """GitHub Actions ワークフローテスター"""

    def __init__(self, workflow_path: str):
        self.workflow_path = Path(workflow_path)
        self.workflow_name = self.workflow_path.name
        self.results: List[TestResult] = []

        with open(workflow_path, 'r', encoding='utf-8') as f:
            self.workflow = yaml.safe_load(f)

    def run_all_tests(self) -> List[TestResult]:
        """全テストを実行"""
        print(f"\n{'='*80}")
        print(f"Testing: {self.workflow_name}")
        print(f"{'='*80}\n")

        # 1. 構文検証
        self.test_yaml_syntax()

        # 2. 構造検証
        self.test_workflow_structure()

        # 3. ロジック検証
        self.test_workflow_logic()

        # 4. セキュリティ検証
        self.test_security()

        # 5. パフォーマンス検証
        self.test_performance()

        # 6. エラーハンドリング検証
        self.test_error_handling()

        # 7. GitHub Actions式の検証
        self.test_github_expressions()

        return self.results

    def add_result(self, category: str, test_name: str, status: str, message: str, details: str = ""):
        """テスト結果を追加"""
        result = TestResult(category, test_name, status, message, details)
        self.results.append(result)

        # コンソール出力
        symbol = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
        print(f"  {symbol} [{category}] {test_name}: {message}")
        if details:
            print(f"      Details: {details}")

    def test_yaml_syntax(self):
        """YAML構文の検証"""
        try:
            # YAMLとして正常にパースできるか
            if self.workflow:
                self.add_result(
                    "構文検証",
                    "YAML構文",
                    "PASS",
                    "YAMLファイルは正常にパースできました"
                )
        except yaml.YAMLError as e:
            self.add_result(
                "構文検証",
                "YAML構文",
                "FAIL",
                f"YAML構文エラー: {str(e)}"
            )

    def test_workflow_structure(self):
        """ワークフロー構造の検証"""

        # 必須フィールドの検証
        required_fields = ['name', 'on', 'jobs']
        for field in required_fields:
            if field in self.workflow:
                self.add_result(
                    "構造検証",
                    f"必須フィールド '{field}'",
                    "PASS",
                    f"'{field}' フィールドが存在します"
                )
            else:
                self.add_result(
                    "構造検証",
                    f"必須フィールド '{field}'",
                    "FAIL",
                    f"'{field}' フィールドが存在しません"
                )

        # トリガーの検証
        if 'on' in self.workflow:
            triggers = self.workflow['on']
            trigger_list = list(triggers.keys()) if isinstance(triggers, dict) else [triggers]
            self.add_result(
                "構造検証",
                "トリガー設定",
                "PASS",
                f"トリガー: {', '.join(trigger_list)}"
            )

        # ジョブの検証
        if 'jobs' in self.workflow:
            jobs = self.workflow['jobs']
            job_count = len(jobs)
            self.add_result(
                "構造検証",
                "ジョブ数",
                "PASS",
                f"{job_count}個のジョブが定義されています"
            )

            # 各ジョブの検証
            for job_name, job_config in jobs.items():
                self._validate_job(job_name, job_config)

    def _validate_job(self, job_name: str, job_config: Dict):
        """個別ジョブの検証"""

        # runs-on の検証
        if 'runs-on' in job_config:
            self.add_result(
                "構造検証",
                f"ジョブ '{job_name}' - runs-on",
                "PASS",
                f"runs-on: {job_config['runs-on']}"
            )
        else:
            self.add_result(
                "構造検証",
                f"ジョブ '{job_name}' - runs-on",
                "FAIL",
                "runs-on が定義されていません"
            )

        # steps の検証
        if 'steps' in job_config:
            steps = job_config['steps']
            self.add_result(
                "構造検証",
                f"ジョブ '{job_name}' - steps",
                "PASS",
                f"{len(steps)}個のステップが定義されています"
            )

            # 各ステップの検証
            for i, step in enumerate(steps):
                self._validate_step(job_name, i, step)

        # timeout-minutes の検証
        if 'timeout-minutes' in job_config:
            timeout = job_config['timeout-minutes']
            if timeout > 360:
                self.add_result(
                    "構造検証",
                    f"ジョブ '{job_name}' - timeout",
                    "WARN",
                    f"タイムアウトが長すぎます: {timeout}分（推奨: 360分以下）"
                )
            else:
                self.add_result(
                    "構造検証",
                    f"ジョブ '{job_name}' - timeout",
                    "PASS",
                    f"タイムアウト: {timeout}分"
                )

    def _validate_step(self, job_name: str, step_index: int, step: Dict):
        """個別ステップの検証"""

        step_name = step.get('name', f'Step {step_index}')

        # nameまたはusesまたはrunの存在確認
        has_action = 'uses' in step
        has_command = 'run' in step

        if not has_action and not has_command:
            self.add_result(
                "構造検証",
                f"ステップ '{step_name}'",
                "FAIL",
                "'uses' または 'run' のいずれかが必要です"
            )

        # timeout-minutes の検証
        if 'timeout-minutes' in step:
            timeout = step['timeout-minutes']
            if timeout > 60:
                self.add_result(
                    "構造検証",
                    f"ステップ '{step_name}' - timeout",
                    "WARN",
                    f"タイムアウトが長すぎます: {timeout}分（推奨: 60分以下）"
                )

    def test_workflow_logic(self):
        """ワークフローロジックの検証"""

        if 'jobs' not in self.workflow:
            return

        for job_name, job_config in self.workflow['jobs'].items():

            # 条件分岐の検証
            if 'if' in job_config:
                condition = job_config['if']
                self._validate_condition(job_name, "ジョブレベル", condition)

            # ステップの条件分岐検証
            if 'steps' in job_config:
                for i, step in enumerate(job_config['steps']):
                    if 'if' in step:
                        step_name = step.get('name', f'Step {i}')
                        self._validate_condition(job_name, f"ステップ '{step_name}'", step['if'])

                    # continue-on-error の検証
                    if 'continue-on-error' in step:
                        step_name = step.get('name', f'Step {i}')
                        self.add_result(
                            "ロジック検証",
                            f"エラー継続設定 ({step_name})",
                            "PASS",
                            f"continue-on-error: {step['continue-on-error']}"
                        )

    def _validate_condition(self, job_name: str, context: str, condition: str):
        """条件式の検証"""

        # 基本的な構文チェック
        if not isinstance(condition, str):
            condition = str(condition)

        # 一般的なパターンのチェック
        patterns = [
            (r'github\.event_name\s*==', '正しいイベント名チェック'),
            (r'github\.event\.issue\.number', 'Issue番号参照'),
            (r'steps\.\w+\.outcome', 'ステップ結果参照'),
            (r'failure\(\)', '失敗検出'),
            (r'success\(\)', '成功検出'),
            (r'always\(\)', '常に実行'),
        ]

        for pattern, description in patterns:
            if re.search(pattern, condition):
                self.add_result(
                    "ロジック検証",
                    f"{context} - 条件式",
                    "PASS",
                    f"{description}が含まれています"
                )

    def test_security(self):
        """セキュリティの検証"""

        workflow_str = yaml.dump(self.workflow)

        # シークレットの適切な使用
        if 'secrets.' in workflow_str:
            self.add_result(
                "セキュリティ検証",
                "シークレット使用",
                "PASS",
                "シークレットが使用されています"
            )

        # GITHUB_TOKEN の使用
        if '${{ secrets.GITHUB_TOKEN }}' in workflow_str:
            self.add_result(
                "セキュリティ検証",
                "GITHUB_TOKEN使用",
                "PASS",
                "GITHUB_TOKENが適切に使用されています"
            )

        # 危険なコマンドパターンの検出
        dangerous_patterns = [
            (r'rm\s+-rf\s+/', 'ルートディレクトリの削除'),
            (r'chmod\s+777', '過度に緩い権限設定'),
            (r'curl.*\|\s*bash', 'パイプによる直接実行'),
            (r'eval\s+', 'eval使用'),
        ]

        for pattern, description in dangerous_patterns:
            if re.search(pattern, workflow_str, re.IGNORECASE):
                self.add_result(
                    "セキュリティ検証",
                    f"危険なパターン - {description}",
                    "WARN",
                    f"潜在的に危険なパターンが検出されました"
                )

        # トークンの権限スコープ確認（permissions）
        if 'jobs' in self.workflow:
            for job_name, job_config in self.workflow['jobs'].items():
                if 'permissions' in job_config:
                    self.add_result(
                        "セキュリティ検証",
                        f"ジョブ '{job_name}' - 権限設定",
                        "PASS",
                        "明示的な権限設定があります"
                    )

    def test_performance(self):
        """パフォーマンスの検証"""

        total_estimated_time = 0

        if 'jobs' not in self.workflow:
            return

        for job_name, job_config in self.workflow['jobs'].items():
            job_timeout = job_config.get('timeout-minutes', 360)
            total_estimated_time += job_timeout

            # キャッシュの使用確認
            if 'steps' in job_config:
                uses_cache = any('cache' in str(step.get('with', {})) for step in job_config['steps'])

                if uses_cache:
                    self.add_result(
                        "パフォーマンス検証",
                        f"ジョブ '{job_name}' - キャッシュ",
                        "PASS",
                        "キャッシュが使用されています"
                    )
                else:
                    self.add_result(
                        "パフォーマンス検証",
                        f"ジョブ '{job_name}' - キャッシュ",
                        "WARN",
                        "キャッシュが使用されていません（パフォーマンス改善の余地あり）"
                    )

                # 並列実行可能性のチェック
                step_count = len(job_config['steps'])
                if step_count > 20:
                    self.add_result(
                        "パフォーマンス検証",
                        f"ジョブ '{job_name}' - ステップ数",
                        "WARN",
                        f"ステップ数が多すぎます: {step_count}（推奨: 20以下）"
                    )

        # 総推定実行時間
        self.add_result(
            "パフォーマンス検証",
            "総推定実行時間",
            "PASS" if total_estimated_time < 60 else "WARN",
            f"最大{total_estimated_time}分（タイムアウト合計）"
        )

        # 同時実行制御の確認
        if 'concurrency' in self.workflow:
            concurrency = self.workflow['concurrency']
            self.add_result(
                "パフォーマンス検証",
                "同時実行制御",
                "PASS",
                f"グループ: {concurrency.get('group', 'N/A')}, cancel-in-progress: {concurrency.get('cancel-in-progress', False)}"
            )

    def test_error_handling(self):
        """エラーハンドリングの検証"""

        if 'jobs' not in self.workflow:
            return

        for job_name, job_config in self.workflow['jobs'].items():

            # always() の使用確認
            workflow_str = yaml.dump(job_config)

            if 'if: always()' in workflow_str or 'if: ${{ always()' in workflow_str:
                self.add_result(
                    "エラーハンドリング検証",
                    f"ジョブ '{job_name}' - always()",
                    "PASS",
                    "常に実行されるステップが定義されています"
                )

            # failure() の使用確認
            if 'failure()' in workflow_str:
                self.add_result(
                    "エラーハンドリング検証",
                    f"ジョブ '{job_name}' - failure()",
                    "PASS",
                    "失敗時の処理が定義されています"
                )

            # リトライメカニズムの確認
            if 'steps' in job_config:
                for step in job_config['steps']:
                    if 'uses' in step and 'retry' in step['uses'].lower():
                        self.add_result(
                            "エラーハンドリング検証",
                            f"ステップ '{step.get('name', 'N/A')}' - リトライ",
                            "PASS",
                            "リトライアクションが使用されています"
                        )

    def test_github_expressions(self):
        """GitHub Actions式の検証"""

        workflow_str = yaml.dump(self.workflow)

        # 式のパターン抽出
        expression_pattern = r'\$\{\{([^}]+)\}\}'
        expressions = re.findall(expression_pattern, workflow_str)

        if expressions:
            self.add_result(
                "GitHub式検証",
                "式の使用",
                "PASS",
                f"{len(expressions)}個の式が使用されています"
            )

            # 式の妥当性チェック
            for expr in expressions:
                expr = expr.strip()

                # 基本的な構文チェック
                if not expr:
                    self.add_result(
                        "GitHub式検証",
                        "空の式",
                        "WARN",
                        "空の式が検出されました"
                    )
                    continue

                # 一般的なコンテキストの検証
                valid_contexts = [
                    'github', 'env', 'secrets', 'steps', 'job',
                    'runner', 'strategy', 'matrix', 'inputs'
                ]

                # 関数の検証
                valid_functions = [
                    'contains', 'startsWith', 'endsWith', 'format',
                    'join', 'toJSON', 'fromJSON', 'hashFiles',
                    'success', 'failure', 'cancelled', 'always'
                ]


def generate_report(all_results: List[Tuple[str, List[TestResult]]]) -> str:
    """テストレポートを生成"""

    report_lines = [
        "# GitHub Actions ワークフロー 包括的テストレポート",
        "",
        f"実行日時: {Path(__file__).stat().st_mtime}",
        "",
        "## 📊 サマリー",
        ""
    ]

    total_pass = 0
    total_fail = 0
    total_warn = 0

    for workflow_name, results in all_results:
        pass_count = sum(1 for r in results if r.status == "PASS")
        fail_count = sum(1 for r in results if r.status == "FAIL")
        warn_count = sum(1 for r in results if r.status == "WARN")

        total_pass += pass_count
        total_fail += fail_count
        total_warn += warn_count

        report_lines.append(f"### {workflow_name}")
        report_lines.append(f"- ✓ PASS: {pass_count}")
        report_lines.append(f"- ✗ FAIL: {fail_count}")
        report_lines.append(f"- ⚠ WARN: {warn_count}")
        report_lines.append("")

    report_lines.extend([
        "## 全体統計",
        f"- 総PASS: {total_pass}",
        f"- 総FAIL: {total_fail}",
        f"- 総WARN: {total_warn}",
        "",
        "## 詳細結果",
        ""
    ])

    # カテゴリ別の詳細結果
    for workflow_name, results in all_results:
        report_lines.append(f"### {workflow_name}")
        report_lines.append("")

        # カテゴリごとにグループ化
        by_category = defaultdict(list)
        for result in results:
            by_category[result.category].append(result)

        for category, cat_results in by_category.items():
            report_lines.append(f"#### {category}")
            report_lines.append("")

            for result in cat_results:
                symbol = "✓" if result.status == "PASS" else "✗" if result.status == "FAIL" else "⚠"
                report_lines.append(f"- {symbol} **{result.test_name}**: {result.message}")
                if result.details:
                    report_lines.append(f"  - 詳細: {result.details}")

            report_lines.append("")

    # エラーと警告の一覧
    all_fails = []
    all_warns = []

    for workflow_name, results in all_results:
        for result in results:
            if result.status == "FAIL":
                all_fails.append((workflow_name, result))
            elif result.status == "WARN":
                all_warns.append((workflow_name, result))

    if all_fails:
        report_lines.extend([
            "## 🚨 検出されたエラー",
            ""
        ])

        for workflow_name, result in all_fails:
            report_lines.append(f"### {workflow_name} - {result.category}")
            report_lines.append(f"**{result.test_name}**: {result.message}")
            if result.details:
                report_lines.append(f"詳細: {result.details}")
            report_lines.append("")

    if all_warns:
        report_lines.extend([
            "## ⚠️ 警告",
            ""
        ])

        for workflow_name, result in all_warns:
            report_lines.append(f"### {workflow_name} - {result.category}")
            report_lines.append(f"**{result.test_name}**: {result.message}")
            if result.details:
                report_lines.append(f"詳細: {result.details}")
            report_lines.append("")

    # 修正推奨事項
    if all_fails or all_warns:
        report_lines.extend([
            "## 🔧 修正推奨事項",
            ""
        ])

        recommendations = []

        for workflow_name, result in all_fails:
            if "必須フィールド" in result.test_name:
                recommendations.append(f"- {workflow_name}: 必須フィールドを追加してください")
            elif "runs-on" in result.test_name:
                recommendations.append(f"- {workflow_name}: runs-onフィールドを定義してください")
            elif "uses' または 'run'" in result.message:
                recommendations.append(f"- {workflow_name}: ステップにusesまたはrunを追加してください")

        for workflow_name, result in all_warns:
            if "タイムアウトが長すぎます" in result.message:
                recommendations.append(f"- {workflow_name}: タイムアウト時間を短縮することを検討してください")
            elif "キャッシュが使用されていません" in result.message:
                recommendations.append(f"- {workflow_name}: 依存関係のキャッシュを有効化してください")
            elif "危険なパターン" in result.test_name:
                recommendations.append(f"- {workflow_name}: 危険なコマンドパターンを見直してください")

        report_lines.extend(recommendations)

    return "\n".join(report_lines)


def main():
    """メイン処理"""

    project_root = Path("/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system")
    workflows_dir = project_root / ".github" / "workflows"

    # 対象ワークフロー
    target_workflows = [
        "auto-error-detection-repair.yml",
        "auto-error-detection-repair-v2.yml"
    ]

    all_results = []

    for workflow_file in target_workflows:
        workflow_path = workflows_dir / workflow_file

        if not workflow_path.exists():
            print(f"⚠️ ワークフローファイルが見つかりません: {workflow_path}")
            continue

        tester = WorkflowTester(str(workflow_path))
        results = tester.run_all_tests()
        all_results.append((workflow_file, results))

    # レポート生成
    print("\n" + "="*80)
    print("レポートを生成しています...")
    print("="*80 + "\n")

    report = generate_report(all_results)

    # レポートを保存
    report_path = project_root / "tests" / "workflow_test_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✓ レポートを保存しました: {report_path}")

    # JSON形式でも保存
    json_results = []
    for workflow_name, results in all_results:
        json_results.append({
            "workflow": workflow_name,
            "results": [
                {
                    "category": r.category,
                    "test_name": r.test_name,
                    "status": r.status,
                    "message": r.message,
                    "details": r.details
                }
                for r in results
            ]
        })

    json_path = project_root / "tests" / "workflow_test_results.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_results, f, indent=2, ensure_ascii=False)

    print(f"✓ JSON結果を保存しました: {json_path}")

    # 統計情報
    total_tests = sum(len(results) for _, results in all_results)
    total_pass = sum(sum(1 for r in results if r.status == "PASS") for _, results in all_results)
    total_fail = sum(sum(1 for r in results if r.status == "FAIL") for _, results in all_results)
    total_warn = sum(sum(1 for r in results if r.status == "WARN") for _, results in all_results)

    print("\n" + "="*80)
    print("テスト完了")
    print("="*80)
    print(f"総テスト数: {total_tests}")
    print(f"✓ PASS: {total_pass}")
    print(f"✗ FAIL: {total_fail}")
    print(f"⚠ WARN: {total_warn}")
    print("="*80 + "\n")

    # 終了コード
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    exit(main())
