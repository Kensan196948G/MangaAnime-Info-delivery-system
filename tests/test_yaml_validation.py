#!/usr/bin/env python3
"""
YAML構文検証スクリプト
GitHub Actions式構文の検証も含む
"""

import yaml
import re
import json
import sys
from pathlib import Path


class GitHubActionsValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []

    def validate_yaml_syntax(self, file_path):
        """YAML構文検証"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                yaml.safe_load(content)
            self.info.append(f"✓ YAML構文: 正常 ({file_path})")
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"✗ YAML構文エラー: {e}")
            return False

    def validate_expression_syntax(self, file_path):
        """GitHub Actions式構文の検証"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # ${{ ... }} 式を抽出
        expression_pattern = r'\$\{\{\s*(.+?)\s*\}\}'
        expressions = re.findall(expression_pattern, content)

        expression_errors = []
        expression_warnings = []

        for expr in expressions:
            # 未閉じの括弧チェック
            if expr.count('(') != expr.count(')'):
                expression_errors.append(f"未閉じの括弧: {expr}")

            # 不正な演算子チェック
            if '===' in expr or '!==' in expr:
                expression_errors.append(f"不正な演算子 (===, !==): {expr}")

            # 文字列リテラルのクォートチェック
            if "'" in expr and expr.count("'") % 2 != 0:
                expression_errors.append(f"未閉じのシングルクォート: {expr}")

            # secrets/env/inputs の正しい参照
            if 'secrets.' in expr and not re.search(r'secrets\.\w+', expr):
                expression_warnings.append(f"secrets参照の形式確認: {expr}")

            # 論理演算子の確認
            if ' or ' in expr.lower() or ' and ' in expr.lower():
                if not ('||' in expr or '&&' in expr):
                    expression_warnings.append(f"論理演算子はPython風ではなくJavaScript風 (||, &&) を使用: {expr}")

        if expression_errors:
            self.errors.extend(expression_errors)
        if expression_warnings:
            self.warnings.extend(expression_warnings)

        self.info.append(f"✓ 式構文検証: {len(expressions)}個の式を検証")
        return len(expression_errors) == 0

    def validate_environment_variables(self, file_path):
        """環境変数とシークレットの検証"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)

        env_vars = set()
        secrets_used = set()
        inputs_used = set()

        # 使用されている変数を収集
        content_str = str(content)

        # secrets検出
        secrets_pattern = r'secrets\.(\w+)'
        secrets_used.update(re.findall(secrets_pattern, content_str))

        # inputs検出
        inputs_pattern = r'inputs\.(\w+)'
        inputs_used.update(re.findall(inputs_pattern, content_str))

        # env検出
        env_pattern = r'env\.(\w+)'
        env_vars.update(re.findall(env_pattern, content_str))

        # inputs定義の確認
        if 'on' in content and 'workflow_dispatch' in content['on']:
            dispatch_config = content['on']['workflow_dispatch']
            if 'inputs' in dispatch_config:
                defined_inputs = set(dispatch_config['inputs'].keys())
                undefined_inputs = inputs_used - defined_inputs
                if undefined_inputs:
                    self.warnings.append(f"未定義のinputs使用: {undefined_inputs}")

        self.info.append(f"✓ 環境変数検証: secrets={len(secrets_used)}, inputs={len(inputs_used)}, env={len(env_vars)}")
        return True

    def validate_timeouts(self, file_path):
        """タイムアウト設定の妥当性検証"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)

        if 'jobs' not in content:
            self.warnings.append("jobs定義が見つかりません")
            return False

        for job_name, job_config in content['jobs'].items():
            # ジョブレベルのタイムアウト
            job_timeout = job_config.get('timeout-minutes', 360)  # デフォルト6時間

            # ステップレベルのタイムアウト合計
            total_step_timeout = 0
            if 'steps' in job_config:
                for step in job_config['steps']:
                    if 'timeout-minutes' in step:
                        total_step_timeout += step['timeout-minutes']
                    elif 'uses' in step and 'retry-action' in step['uses']:
                        # retry-actionの場合
                        if 'with' in step and 'timeout_minutes' in step['with']:
                            total_step_timeout += step['with']['timeout_minutes']

            # タイムアウト警告
            if total_step_timeout > job_timeout:
                self.warnings.append(
                    f"ジョブ '{job_name}': ステップの合計タイムアウト({total_step_timeout}分) > "
                    f"ジョブのタイムアウト({job_timeout}分)"
                )

            if job_timeout > 60:
                self.info.append(f"ジョブ '{job_name}': タイムアウト={job_timeout}分 (長時間実行)")

        return True

    def validate_error_handling(self, file_path):
        """エラーハンドリングの網羅性検証"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)

        if 'jobs' not in content:
            return False

        for job_name, job_config in content['jobs'].items():
            has_error_handling = False

            if 'steps' in job_config:
                for step in job_config['steps']:
                    # continue-on-error, if: always(), if: failure() などの確認
                    if step.get('continue-on-error'):
                        has_error_handling = True
                    if 'if' in step:
                        if_condition = step['if']
                        if 'always()' in str(if_condition) or 'failure()' in str(if_condition):
                            has_error_handling = True

            if has_error_handling:
                self.info.append(f"✓ ジョブ '{job_name}': エラーハンドリングあり")
            else:
                self.warnings.append(f"ジョブ '{job_name}': エラーハンドリングが設定されていません")

        return True

    def run_all_validations(self, file_path):
        """すべての検証を実行"""
        print(f"\n{'='*60}")
        print(f"検証対象: {file_path}")
        print(f"{'='*60}\n")

        validations = [
            self.validate_yaml_syntax,
            self.validate_expression_syntax,
            self.validate_environment_variables,
            self.validate_timeouts,
            self.validate_error_handling
        ]

        for validation in validations:
            validation(file_path)

        # 結果出力
        print("\n【エラー】")
        if self.errors:
            for error in self.errors:
                print(f"  ✗ {error}")
        else:
            print("  なし")

        print("\n【警告】")
        if self.warnings:
            for warning in self.warnings:
                print(f"  ⚠ {warning}")
        else:
            print("  なし")

        print("\n【情報】")
        for info in self.info:
            print(f"  {info}")

        return len(self.errors) == 0


def main():
    workflows = [
        "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/.github/workflows/auto-error-detection-repair-v2.yml",
        "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/.github/workflows/auto-error-detection-repair.yml"
    ]

    all_valid = True
    results = {}

    for workflow in workflows:
        validator = GitHubActionsValidator()
        valid = validator.run_all_validations(workflow)
        all_valid = all_valid and valid

        results[Path(workflow).name] = {
            "valid": valid,
            "errors": validator.errors,
            "warnings": validator.warnings,
            "info": validator.info
        }

    # JSON形式で結果を保存
    output_file = "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/qa_test_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"テストレポート: {output_file}")
    print(f"{'='*60}")

    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
