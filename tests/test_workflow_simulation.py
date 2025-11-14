#!/usr/bin/env python3
"""
GitHub Actions ワークフロー シミュレーションテスト
エラーシナリオとパフォーマンスのシミュレーション
"""

import yaml
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
import json


@dataclass
class SimulationResult:
    """シミュレーション結果"""
    scenario: str
    status: str
    duration_minutes: float
    details: str
    issues_found: List[str]


class WorkflowSimulator:
    """ワークフローシミュレーター"""

    def __init__(self, workflow_path: str):
        self.workflow_path = Path(workflow_path)
        self.workflow_name = self.workflow_path.name

        with open(workflow_path, 'r', encoding='utf-8') as f:
            self.workflow_data = yaml.safe_load(f)

        # YAMLファイル全体を文字列として読み込み（`on`キーワードの確認用）
        with open(workflow_path, 'r', encoding='utf-8') as f:
            self.raw_content = f.read()

    def run_simulations(self) -> List[SimulationResult]:
        """全シミュレーションを実行"""
        print(f"\n{'='*80}")
        print(f"シミュレーション対象: {self.workflow_name}")
        print(f"{'='*80}\n")

        results = []

        # 1. 正常系シミュレーション
        results.append(self.simulate_success_scenario())

        # 2. Python環境セットアップ失敗シナリオ
        results.append(self.simulate_python_setup_failure())

        # 3. 依存関係インストール失敗シナリオ
        results.append(self.simulate_dependency_install_failure())

        # 4. 修復ループタイムアウトシナリオ
        results.append(self.simulate_repair_loop_timeout())

        # 5. 並列実行競合シナリオ
        results.append(self.simulate_concurrency_conflict())

        # 6. Issue作成失敗シナリオ
        results.append(self.simulate_issue_creation_failure())

        # 7. アーティファクトアップロード失敗シナリオ
        results.append(self.simulate_artifact_upload_failure())

        # 8. リトライメカニズムテスト（v2のみ）
        if 'v2' in self.workflow_name:
            results.append(self.simulate_retry_mechanism())

        return results

    def get_job_config(self) -> Dict:
        """ジョブ設定を取得"""
        jobs = self.workflow_data.get('jobs', {})
        if 'error-detection-and-repair' in jobs:
            return jobs['error-detection-and-repair']
        return {}

    def simulate_success_scenario(self) -> SimulationResult:
        """正常系シナリオのシミュレーション"""
        print("🟢 正常系シナリオをシミュレーション中...")

        job_config = self.get_job_config()
        timeout = job_config.get('timeout-minutes', 30)

        # ステップ数を取得
        steps = job_config.get('steps', [])
        step_count = len(steps)

        # 推定実行時間（各ステップ平均2分と仮定）
        estimated_duration = min(step_count * 2, timeout)

        issues = []

        # キャッシュの確認
        has_cache = any('cache' in str(step.get('with', {})) for step in steps)
        if has_cache:
            estimated_duration *= 0.7  # キャッシュにより30%高速化

        print(f"  ✓ 推定実行時間: {estimated_duration:.1f}分")
        print(f"  ✓ タイムアウト: {timeout}分")
        print(f"  ✓ ステップ数: {step_count}")

        return SimulationResult(
            scenario="正常系",
            status="SUCCESS",
            duration_minutes=estimated_duration,
            details=f"全{step_count}ステップが正常に完了",
            issues_found=issues
        )

    def simulate_python_setup_failure(self) -> SimulationResult:
        """Python環境セットアップ失敗シナリオ"""
        print("🔴 Python環境セットアップ失敗シナリオをシミュレーション中...")

        job_config = self.get_job_config()
        steps = job_config.get('steps', [])

        # Python環境セットアップステップを探す
        python_step_index = None
        for i, step in enumerate(steps):
            if 'uses' in step and 'setup-python' in step['uses']:
                python_step_index = i
                break

        issues = []

        if python_step_index is not None:
            # このステップで失敗した場合の影響を分析
            remaining_steps = len(steps) - python_step_index - 1
            issues.append(f"Python環境セットアップ失敗により、残り{remaining_steps}ステップがスキップされます")

            # always()条件のステップは実行される
            always_steps = [
                step.get('name', f'Step {i}')
                for i, step in enumerate(steps)
                if 'if' in step and 'always()' in str(step['if'])
            ]

            if always_steps:
                issues.append(f"以下のステップは実行されます: {', '.join(always_steps)}")
            else:
                issues.append("クリーンアップステップが実行されない可能性があります")

        print(f"  ✗ 検出された問題: {len(issues)}件")

        return SimulationResult(
            scenario="Python環境セットアップ失敗",
            status="FAILURE",
            duration_minutes=2.0,
            details="Python環境セットアップで失敗",
            issues_found=issues
        )

    def simulate_dependency_install_failure(self) -> SimulationResult:
        """依存関係インストール失敗シナリオ"""
        print("🔴 依存関係インストール失敗シナリオをシミュレーション中...")

        job_config = self.get_job_config()
        steps = job_config.get('steps', [])

        issues = []

        # リトライメカニズムの確認
        has_retry = any('retry' in step.get('uses', '').lower() for step in steps)

        if has_retry:
            issues.append("✓ リトライメカニズムが設定されています（最大3回試行）")
            estimated_duration = 15.0  # 3回試行する場合
        else:
            issues.append("⚠ リトライメカニズムが設定されていません")
            estimated_duration = 5.0

        # タイムアウト設定の確認
        for step in steps:
            if 'timeout-minutes' in step and ('pip install' in str(step.get('run', '')) or 'インストール' in step.get('name', '')):
                timeout = step['timeout-minutes']
                issues.append(f"✓ インストールステップにタイムアウト設定あり: {timeout}分")

        print(f"  ⚠ 検出された問題: {len(issues)}件")

        return SimulationResult(
            scenario="依存関係インストール失敗",
            status="FAILURE" if not has_retry else "RETRY_SUCCESS",
            duration_minutes=estimated_duration,
            details="依存関係インストールでエラー" + (" → リトライで成功" if has_retry else ""),
            issues_found=issues
        )

    def simulate_repair_loop_timeout(self) -> SimulationResult:
        """修復ループタイムアウトシナリオ"""
        print("🟡 修復ループタイムアウトシナリオをシミュレーション中...")

        job_config = self.get_job_config()
        steps = job_config.get('steps', [])

        issues = []

        # 修復ループステップを探す
        repair_step = None
        for step in steps:
            if '修復ループ' in step.get('name', '') or 'repair-loop' in step.get('id', ''):
                repair_step = step
                break

        if repair_step:
            timeout = repair_step.get('timeout-minutes', 15)
            continue_on_error = repair_step.get('continue-on-error', False)

            issues.append(f"修復ループのタイムアウト: {timeout}分")

            if continue_on_error:
                issues.append("✓ continue-on-error が設定されており、後続ステップは実行されます")
            else:
                issues.append("⚠ continue-on-error が未設定のため、ワークフロー全体が失敗します")

            # always()条件のステップをカウント
            cleanup_steps = [
                step.get('name', 'Unknown')
                for step in steps
                if 'if' in step and 'always()' in str(step['if'])
            ]

            if cleanup_steps:
                issues.append(f"✓ クリーンアップステップ({len(cleanup_steps)}個)は実行されます")

        print(f"  ⚠ 検出された問題: {len(issues)}件")

        return SimulationResult(
            scenario="修復ループタイムアウト",
            status="TIMEOUT",
            duration_minutes=timeout if repair_step else 15,
            details="修復ループがタイムアウトしました",
            issues_found=issues
        )

    def simulate_concurrency_conflict(self) -> SimulationResult:
        """並列実行競合シナリオ"""
        print("🟡 並列実行競合シナリオをシミュレーション中...")

        issues = []

        # concurrency設定を確認
        concurrency = self.workflow_data.get('concurrency', {})

        if concurrency:
            group = concurrency.get('group', 'N/A')
            cancel_in_progress = concurrency.get('cancel-in-progress', False)

            issues.append(f"✓ 並列実行制御グループ: {group}")

            if cancel_in_progress:
                issues.append("✓ 実行中のワークフローはキャンセルされます")
                status = "CANCELLED"
            else:
                issues.append("⚠ 実行中のワークフローは待機します（キューイング）")
                status = "QUEUED"
        else:
            issues.append("⚠ 並列実行制御が設定されていません（複数実行のリスク）")
            status = "CONFLICT"

        print(f"  ⚠ 検出された問題: {len(issues)}件")

        return SimulationResult(
            scenario="並列実行競合",
            status=status,
            duration_minutes=0.5,
            details="別のワークフロー実行が進行中",
            issues_found=issues
        )

    def simulate_issue_creation_failure(self) -> SimulationResult:
        """Issue作成失敗シナリオ"""
        print("🔴 Issue作成失敗シナリオをシミュレーション中...")

        job_config = self.get_job_config()
        steps = job_config.get('steps', [])

        issues = []

        # Issue作成ステップを探す
        issue_steps = [
            step for step in steps
            if 'Issue' in step.get('name', '') and 'github-script' in step.get('uses', '')
        ]

        if issue_steps:
            for step in issue_steps:
                step_name = step.get('name', 'Unknown')
                has_condition = 'if' in step

                if has_condition:
                    condition = step['if']
                    if 'failure()' in str(condition):
                        issues.append(f"✓ '{step_name}' は失敗時のみ実行されます")
                    elif 'success()' in str(condition):
                        issues.append(f"✓ '{step_name}' は成功時のみ実行されます")

                # GitHub API権限の確認
                issues.append(f"⚠ '{step_name}' はGITHUB_TOKENの権限が必要です")

            # エラーハンドリングの確認
            has_error_handling = any('try' in str(step.get('with', {}).get('script', '')) for step in issue_steps)

            if has_error_handling:
                issues.append("✓ Issue作成時のエラーハンドリングが実装されています")
            else:
                issues.append("⚠ Issue作成エラーのハンドリングが不十分な可能性があります")

        print(f"  ⚠ 検出された問題: {len(issues)}件")

        return SimulationResult(
            scenario="Issue作成失敗",
            status="FAILURE",
            duration_minutes=1.0,
            details="GitHub API エラーによりIssue作成失敗",
            issues_found=issues
        )

    def simulate_artifact_upload_failure(self) -> SimulationResult:
        """アーティファクトアップロード失敗シナリオ"""
        print("🟡 アーティファクトアップロード失敗シナリオをシミュレーション中...")

        job_config = self.get_job_config()
        steps = job_config.get('steps', [])

        issues = []

        # アーティファクトアップロードステップを探す
        artifact_steps = [
            step for step in steps
            if 'upload-artifact' in step.get('uses', '')
        ]

        if artifact_steps:
            for step in artifact_steps:
                step_name = step.get('name', 'Unknown')
                retention_days = step.get('with', {}).get('retention-days', 90)

                issues.append(f"アーティファクト '{step_name}' の保持期間: {retention_days}日")

                # always()条件の確認
                if 'if' in step and 'always()' in str(step['if']):
                    issues.append(f"✓ '{step_name}' は失敗時も実行されます")
                else:
                    issues.append(f"⚠ '{step_name}' は失敗時にスキップされる可能性があります")

            # アーティファクトサイズの確認（ワークフローからは推定不可）
            issues.append("⚠ アーティファクトサイズが大きい場合、アップロードに時間がかかります")

        print(f"  ⚠ 検出された問題: {len(issues)}件")

        return SimulationResult(
            scenario="アーティファクトアップロード失敗",
            status="FAILURE",
            duration_minutes=2.0,
            details="ネットワークエラーによりアップロード失敗",
            issues_found=issues
        )

    def simulate_retry_mechanism(self) -> SimulationResult:
        """リトライメカニズムテスト"""
        print("🔄 リトライメカニズムをシミュレーション中...")

        job_config = self.get_job_config()
        steps = job_config.get('steps', [])

        issues = []

        # リトライステップを探す
        retry_steps = [
            step for step in steps
            if 'retry' in step.get('uses', '').lower()
        ]

        if retry_steps:
            for step in retry_steps:
                step_name = step.get('name', 'Unknown')
                step_with = step.get('with', {})

                max_attempts = step_with.get('max_attempts', 1)
                timeout_minutes = step_with.get('timeout_minutes', 5)
                retry_wait_seconds = step_with.get('retry_wait_seconds', 10)

                issues.append(f"✓ '{step_name}': 最大{max_attempts}回試行")
                issues.append(f"  - タイムアウト: {timeout_minutes}分")
                issues.append(f"  - 再試行間隔: {retry_wait_seconds}秒")

                # 最大実行時間を計算
                max_duration = timeout_minutes * max_attempts + (retry_wait_seconds * (max_attempts - 1)) / 60
                issues.append(f"  - 最大実行時間: {max_duration:.1f}分")

            status = "SUCCESS"
            duration = max_duration
        else:
            issues.append("⚠ リトライメカニズムが設定されていません")
            status = "NOT_CONFIGURED"
            duration = 0

        print(f"  ⚠ 検出された問題: {len(issues)}件")

        return SimulationResult(
            scenario="リトライメカニズム",
            status=status,
            duration_minutes=duration,
            details=f"リトライメカニズムのシミュレーション",
            issues_found=issues
        )


def analyze_performance(results: List[SimulationResult]) -> Dict:
    """パフォーマンス分析"""
    total_scenarios = len(results)
    success_count = sum(1 for r in results if r.status in ["SUCCESS", "RETRY_SUCCESS"])
    failure_count = sum(1 for r in results if r.status == "FAILURE")
    timeout_count = sum(1 for r in results if r.status == "TIMEOUT")

    avg_duration = sum(r.duration_minutes for r in results) / total_scenarios if total_scenarios > 0 else 0
    max_duration = max((r.duration_minutes for r in results), default=0)

    total_issues = sum(len(r.issues_found) for r in results)

    return {
        "total_scenarios": total_scenarios,
        "success_count": success_count,
        "failure_count": failure_count,
        "timeout_count": timeout_count,
        "avg_duration_minutes": round(avg_duration, 2),
        "max_duration_minutes": round(max_duration, 2),
        "total_issues": total_issues
    }


def generate_simulation_report(all_results: Dict[str, List[SimulationResult]]) -> str:
    """シミュレーションレポートを生成"""
    lines = [
        "# GitHub Actions ワークフロー シミュレーションレポート",
        "",
        "## 📊 エグゼクティブサマリー",
        ""
    ]

    for workflow_name, results in all_results.items():
        perf = analyze_performance(results)

        lines.extend([
            f"### {workflow_name}",
            f"- 総シナリオ数: {perf['total_scenarios']}",
            f"- 成功: {perf['success_count']}",
            f"- 失敗: {perf['failure_count']}",
            f"- タイムアウト: {perf['timeout_count']}",
            f"- 平均実行時間: {perf['avg_duration_minutes']}分",
            f"- 最大実行時間: {perf['max_duration_minutes']}分",
            f"- 検出された問題総数: {perf['total_issues']}",
            ""
        ])

    lines.extend([
        "## 📝 シナリオ詳細",
        ""
    ])

    for workflow_name, results in all_results.items():
        lines.extend([
            f"### {workflow_name}",
            ""
        ])

        for result in results:
            status_emoji = {
                "SUCCESS": "✅",
                "FAILURE": "❌",
                "TIMEOUT": "⏱️",
                "RETRY_SUCCESS": "🔄✅",
                "QUEUED": "⏳",
                "CANCELLED": "🚫",
                "CONFLICT": "⚠️",
                "NOT_CONFIGURED": "❓"
            }.get(result.status, "❓")

            lines.extend([
                f"#### {status_emoji} {result.scenario}",
                f"- **ステータス**: {result.status}",
                f"- **実行時間**: {result.duration_minutes:.1f}分",
                f"- **詳細**: {result.details}",
                ""
            ])

            if result.issues_found:
                lines.append("**検出された問題・所見:**")
                for issue in result.issues_found:
                    lines.append(f"  - {issue}")
                lines.append("")

    # ボトルネック分析
    lines.extend([
        "## 🔍 ボトルネック分析",
        ""
    ])

    for workflow_name, results in all_results.items():
        # 最も時間がかかるシナリオ
        slowest = max(results, key=lambda r: r.duration_minutes)

        lines.extend([
            f"### {workflow_name}",
            f"- **最も時間がかかるシナリオ**: {slowest.scenario} ({slowest.duration_minutes:.1f}分)",
            ""
        ])

    # 推奨事項
    lines.extend([
        "## 💡 推奨事項",
        ""
    ])

    all_issues = []
    for workflow_name, results in all_results.items():
        for result in results:
            for issue in result.issues_found:
                if issue.startswith("⚠"):
                    all_issues.append((workflow_name, result.scenario, issue))

    if all_issues:
        lines.append("### 改善が推奨される項目")
        for workflow_name, scenario, issue in all_issues:
            lines.append(f"- **{workflow_name}** ({scenario}): {issue}")
    else:
        lines.append("現時点で改善が必要な項目は検出されませんでした。")

    lines.extend([
        "",
        "---",
        "*このレポートはシミュレーションに基づいて生成されました*"
    ])

    return "\n".join(lines)


def main():
    """メイン処理"""
    project_root = Path("/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system")
    workflows_dir = project_root / ".github" / "workflows"

    target_workflows = [
        "auto-error-detection-repair.yml",
        "auto-error-detection-repair-v2.yml"
    ]

    all_results = {}

    for workflow_file in target_workflows:
        workflow_path = workflows_dir / workflow_file

        if not workflow_path.exists():
            print(f"⚠️ ワークフローファイルが見つかりません: {workflow_path}")
            continue

        simulator = WorkflowSimulator(str(workflow_path))
        results = simulator.run_simulations()
        all_results[workflow_file] = results

    # レポート生成
    print("\n" + "="*80)
    print("シミュレーションレポートを生成しています...")
    print("="*80 + "\n")

    report = generate_simulation_report(all_results)

    # レポート保存
    report_path = project_root / "tests" / "workflow_simulation_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✓ シミュレーションレポートを保存しました: {report_path}")

    # JSON形式でも保存
    json_results = {
        workflow_name: [
            {
                "scenario": r.scenario,
                "status": r.status,
                "duration_minutes": r.duration_minutes,
                "details": r.details,
                "issues_found": r.issues_found
            }
            for r in results
        ]
        for workflow_name, results in all_results.items()
    }

    # パフォーマンス分析も追加
    json_results["performance_analysis"] = {
        workflow_name: analyze_performance(results)
        for workflow_name, results in all_results.items()
    }

    json_path = project_root / "tests" / "workflow_simulation_results.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_results, f, indent=2, ensure_ascii=False)

    print(f"✓ JSON結果を保存しました: {json_path}")

    # 統計出力
    print("\n" + "="*80)
    print("シミュレーション完了")
    print("="*80)

    for workflow_name, results in all_results.items():
        perf = analyze_performance(results)
        print(f"\n{workflow_name}:")
        print(f"  総シナリオ: {perf['total_scenarios']}")
        print(f"  成功: {perf['success_count']}")
        print(f"  失敗: {perf['failure_count']}")
        print(f"  平均実行時間: {perf['avg_duration_minutes']}分")
        print(f"  検出された問題: {perf['total_issues']}件")

    print("="*80 + "\n")


if __name__ == "__main__":
    main()
