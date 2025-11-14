#!/usr/bin/env python3
"""
テスト通知機能 統合テストレポート生成スクリプト

全てのテスト結果を統合して包括的なレポートを生成します。

使用方法:
    python3 tests/generate_test_report.py

出力:
    - docs/reports/test_notification_report_YYYYMMDD_HHMMSS.md
    - docs/reports/test_notification_report_YYYYMMDD_HHMMSS.html
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestReportGenerator:
    """テストレポート生成クラス"""

    def __init__(self):
        self.project_root = project_root
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.report_dir = self.project_root / 'docs' / 'reports'
        self.report_dir.mkdir(parents=True, exist_ok=True)

        self.results = {
            'pytest': {},
            'curl': {},
            'playwright': {},
            'manual_checks': []
        }

    def run_pytest_tests(self):
        """Pytestテストを実行"""
        print("=" * 80)
        print("Pytest テスト実行中...")
        print("=" * 80)

        test_file = self.project_root / 'tests' / 'test_notification_comprehensive.py'

        if not test_file.exists():
            self.results['pytest'] = {
                'status': 'skipped',
                'reason': 'テストファイルが見つかりません'
            }
            return

        try:
            # JSON形式でレポート出力
            result = subprocess.run(
                ['pytest', str(test_file), '-v', '--json-report', '--json-report-file=/tmp/pytest_report.json'],
                capture_output=True,
                text=True,
                timeout=120
            )

            # JSON レポートが生成されない場合は通常の出力を解析
            if os.path.exists('/tmp/pytest_report.json'):
                with open('/tmp/pytest_report.json', 'r') as f:
                    pytest_data = json.load(f)
                    self.results['pytest'] = {
                        'status': 'completed',
                        'total': pytest_data.get('summary', {}).get('total', 0),
                        'passed': pytest_data.get('summary', {}).get('passed', 0),
                        'failed': pytest_data.get('summary', {}).get('failed', 0),
                        'duration': pytest_data.get('duration', 0),
                        'output': result.stdout
                    }
            else:
                # 通常の実行
                result = subprocess.run(
                    ['pytest', str(test_file), '-v', '--tb=short'],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                # 出力から結果を解析
                output = result.stdout + result.stderr
                passed = output.count(' PASSED')
                failed = output.count(' FAILED')
                total = passed + failed

                self.results['pytest'] = {
                    'status': 'completed',
                    'total': total,
                    'passed': passed,
                    'failed': failed,
                    'return_code': result.returncode,
                    'output': output
                }

        except subprocess.TimeoutExpired:
            self.results['pytest'] = {
                'status': 'timeout',
                'reason': 'テスト実行がタイムアウトしました'
            }
        except Exception as e:
            self.results['pytest'] = {
                'status': 'error',
                'reason': str(e)
            }

    def run_curl_tests(self):
        """curlテストを実行"""
        print("\n" + "=" * 80)
        print("curl APIテスト実行中...")
        print("=" * 80)

        test_script = self.project_root / 'tests' / 'test_notification_api.sh'

        if not test_script.exists():
            self.results['curl'] = {
                'status': 'skipped',
                'reason': 'テストスクリプトが見つかりません'
            }
            return

        try:
            result = subprocess.run(
                ['bash', str(test_script)],
                capture_output=True,
                text=True,
                timeout=300
            )

            output = result.stdout + result.stderr

            # 結果を解析
            passed = output.count('✅ PASSED')
            failed = output.count('❌ FAILED')
            total = passed + failed

            self.results['curl'] = {
                'status': 'completed',
                'total': total,
                'passed': passed,
                'failed': failed,
                'return_code': result.returncode,
                'output': output
            }

        except subprocess.TimeoutExpired:
            self.results['curl'] = {
                'status': 'timeout',
                'reason': 'テスト実行がタイムアウトしました'
            }
        except Exception as e:
            self.results['curl'] = {
                'status': 'error',
                'reason': str(e)
            }

    def run_playwright_tests(self):
        """Playwrightテストを実行"""
        print("\n" + "=" * 80)
        print("Playwright E2Eテスト実行中...")
        print("=" * 80)

        test_file = self.project_root / 'tests' / 'test_notification_ui.spec.ts'

        if not test_file.exists():
            self.results['playwright'] = {
                'status': 'skipped',
                'reason': 'テストファイルが見つかりません'
            }
            return

        # package.jsonの存在確認
        if not (self.project_root / 'package.json').exists():
            self.results['playwright'] = {
                'status': 'skipped',
                'reason': 'Node.js環境が設定されていません'
            }
            return

        try:
            result = subprocess.run(
                ['npx', 'playwright', 'test', str(test_file), '--reporter=json'],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.project_root)
            )

            output = result.stdout + result.stderr

            # 結果を解析
            passed = output.count('passed')
            failed = output.count('failed')

            self.results['playwright'] = {
                'status': 'completed',
                'passed': passed,
                'failed': failed,
                'return_code': result.returncode,
                'output': output
            }

        except subprocess.TimeoutExpired:
            self.results['playwright'] = {
                'status': 'timeout',
                'reason': 'テスト実行がタイムアウトしました'
            }
        except FileNotFoundError:
            self.results['playwright'] = {
                'status': 'skipped',
                'reason': 'Playwrightがインストールされていません'
            }
        except Exception as e:
            self.results['playwright'] = {
                'status': 'error',
                'reason': str(e)
            }

    def generate_markdown_report(self):
        """Markdownレポートを生成"""
        report_file = self.report_dir / f'test_notification_report_{self.timestamp}.md'

        content = f"""# テスト通知機能 包括的テストレポート

**生成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}

---

## 概要

テスト通知機能の包括的なテスト結果をまとめたレポートです。

### テスト実施環境

- **プロジェクト**: MangaAnime-Info-delivery-system
- **テスト対象**: テスト通知API (`/api/test-notification`)
- **実施日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## テスト結果サマリー

"""

        # Pytestテスト結果
        content += "### 1. Pytest 単体テスト\n\n"
        if self.results['pytest'].get('status') == 'completed':
            pytest_data = self.results['pytest']
            success_rate = (pytest_data['passed'] / pytest_data['total'] * 100) if pytest_data['total'] > 0 else 0

            content += f"""
- **ステータス**: ✅ 完了
- **総テスト数**: {pytest_data['total']}
- **成功**: {pytest_data['passed']}
- **失敗**: {pytest_data['failed']}
- **成功率**: {success_rate:.1f}%

"""
            if pytest_data['failed'] == 0:
                content += "✅ **全てのテストが成功しました！**\n\n"
            else:
                content += f"⚠️ **{pytest_data['failed']}個のテストが失敗しました**\n\n"

        else:
            content += f"""
- **ステータス**: ⚠️ {self.results['pytest'].get('status', 'unknown')}
- **理由**: {self.results['pytest'].get('reason', '不明')}

"""

        # curlテスト結果
        content += "### 2. curl APIテスト\n\n"
        if self.results['curl'].get('status') == 'completed':
            curl_data = self.results['curl']
            success_rate = (curl_data['passed'] / curl_data['total'] * 100) if curl_data['total'] > 0 else 0

            content += f"""
- **ステータス**: ✅ 完了
- **総テスト数**: {curl_data['total']}
- **成功**: {curl_data['passed']}
- **失敗**: {curl_data['failed']}
- **成功率**: {success_rate:.1f}%

"""
            if curl_data['failed'] == 0:
                content += "✅ **全てのAPIテストが成功しました！**\n\n"
            else:
                content += f"⚠️ **{curl_data['failed']}個のテストが失敗しました**\n\n"

        else:
            content += f"""
- **ステータス**: ⚠️ {self.results['curl'].get('status', 'unknown')}
- **理由**: {self.results['curl'].get('reason', '不明')}

"""

        # Playwrightテスト結果
        content += "### 3. Playwright E2Eテスト\n\n"
        if self.results['playwright'].get('status') == 'completed':
            playwright_data = self.results['playwright']

            content += f"""
- **ステータス**: ✅ 完了
- **成功**: {playwright_data['passed']}
- **失敗**: {playwright_data['failed']}

"""
            if playwright_data['failed'] == 0:
                content += "✅ **全てのE2Eテストが成功しました！**\n\n"
            else:
                content += f"⚠️ **{playwright_data['failed']}個のテストが失敗しました**\n\n"

        else:
            content += f"""
- **ステータス**: ⚠️ {self.results['playwright'].get('status', 'unknown')}
- **理由**: {self.results['playwright'].get('reason', '不明')}

"""

        # 総合評価
        content += """---

## 総合評価

"""

        total_passed = 0
        total_failed = 0

        if self.results['pytest'].get('status') == 'completed':
            total_passed += self.results['pytest']['passed']
            total_failed += self.results['pytest']['failed']

        if self.results['curl'].get('status') == 'completed':
            total_passed += self.results['curl']['passed']
            total_failed += self.results['curl']['failed']

        total_tests = total_passed + total_failed

        if total_tests > 0:
            overall_success_rate = (total_passed / total_tests * 100)

            content += f"""
- **総実施テスト数**: {total_tests}
- **総成功数**: {total_passed}
- **総失敗数**: {total_failed}
- **総合成功率**: {overall_success_rate:.1f}%

"""

            if total_failed == 0:
                content += "### 🎉 評価: 優秀\n\n"
                content += "全てのテストが成功しました！テスト通知機能は正常に動作しています。\n\n"
            elif overall_success_rate >= 80:
                content += "### ✅ 評価: 良好\n\n"
                content += "大部分のテストが成功しています。一部の失敗については修正が推奨されます。\n\n"
            elif overall_success_rate >= 60:
                content += "### ⚠️ 評価: 要改善\n\n"
                content += "多数のテストが失敗しています。早急な修正が必要です。\n\n"
            else:
                content += "### ❌ 評価: 不合格\n\n"
                content += "半数以上のテストが失敗しています。機能の見直しが必要です。\n\n"

        # 推奨事項
        content += """---

## 推奨事項

"""

        if total_failed > 0:
            content += "### 修正が必要な項目\n\n"
            content += "1. 失敗したテストケースの詳細を確認\n"
            content += "2. エラーログを分析\n"
            content += "3. 該当コードを修正\n"
            content += "4. 再テストを実施\n\n"

        content += """### 継続的な改善

1. **テストカバレッジの向上**: 現在のカバレッジを維持・向上
2. **自動テストの定期実行**: CI/CDパイプラインへの統合
3. **パフォーマンステスト**: レスポンスタイムの監視
4. **セキュリティテスト**: 定期的な脆弱性スキャン

---

## 詳細ログ

### Pytest詳細出力

```
"""
        if self.results['pytest'].get('output'):
            content += self.results['pytest']['output'][:2000]  # 最初の2000文字
            if len(self.results['pytest']['output']) > 2000:
                content += "\n... (省略) ...\n"
        else:
            content += "なし"

        content += """
```

### curl詳細出力

```
"""
        if self.results['curl'].get('output'):
            content += self.results['curl']['output'][:2000]
            if len(self.results['curl']['output']) > 2000:
                content += "\n... (省略) ...\n"
        else:
            content += "なし"

        content += """
```

---

## 付録

### テストケース一覧

#### 正常系テスト
1. 基本的なテスト通知送信
2. カスタムメッセージでの送信
3. デフォルトメッセージでの送信
4. 長いメッセージの送信
5. 特殊文字を含むメッセージ

#### 異常系テスト
6. メールアドレス未設定エラー
7. Gmailアプリパスワード未設定エラー
8. 不正な認証情報エラー
9. ネットワークエラー
10. タイムアウトエラー

#### 入力検証テスト
11. 空のJSONボディ
12. 不正なJSONフォーマット
13. GETメソッドでのアクセス

### 関連ドキュメント

- [動作確認手順書](test_notification_manual.md)
- [システム詳細仕様書](../CLAUDE.md)
- [API仕様書](api_specification.md)

---

*このレポートは自動生成されました - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        # ファイルに書き込み
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"\n✅ Markdownレポートを生成しました: {report_file}")
        return report_file

    def generate_html_report(self, md_file):
        """HTMLレポートを生成（オプション）"""
        html_file = md_file.with_suffix('.html')

        try:
            # pandocがインストールされていれば使用
            subprocess.run(
                ['pandoc', str(md_file), '-o', str(html_file), '--standalone', '--css=style.css'],
                check=True,
                timeout=30
            )
            print(f"✅ HTMLレポートを生成しました: {html_file}")
            return html_file

        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ pandocが見つかりません。HTMLレポートの生成をスキップします。")
            return None

    def run_all_tests(self):
        """全てのテストを実行してレポートを生成"""
        print("\n" + "=" * 80)
        print("テスト通知機能 包括的テスト開始")
        print("=" * 80)

        # 各テストを実行
        self.run_pytest_tests()
        self.run_curl_tests()
        self.run_playwright_tests()

        # レポート生成
        print("\n" + "=" * 80)
        print("テストレポート生成中...")
        print("=" * 80)

        md_file = self.generate_markdown_report()
        self.generate_html_report(md_file)

        print("\n" + "=" * 80)
        print("テスト完了")
        print("=" * 80)

        return md_file


def main():
    """メイン関数"""
    generator = TestReportGenerator()
    report_file = generator.run_all_tests()

    print(f"\n📊 レポートファイル: {report_file}")
    print("\nレポートを確認してください。")


if __name__ == '__main__':
    main()
