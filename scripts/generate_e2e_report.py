#!/usr/bin/env python3
"""
E2Eテストレポート生成
HTML形式の詳細レポートを生成
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

project_root = Path(__file__).parent.parent


class E2EReportGenerator:
    """E2Eレポート生成"""

    def __init__(self):
        self.report_data = {
            'timestamp': datetime.now().isoformat(),
            'pages': [],
            'apis': [],
            'errors': [],
            'warnings': [],
            'summary': {}
        }

    def generate_html_report(self, output_path: Path = None):
        """HTMLレポート生成"""
        if output_path is None:
            output_path = project_root / 'reports' / f'e2e_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'

        output_path.parent.mkdir(parents=True, exist_ok=True)

        html_content = self._generate_html()
        output_path.write_text(html_content, encoding='utf-8')

        print(f"✅ HTMLレポート生成完了: {output_path}")
        return output_path

    def _generate_html(self) -> str:
        """HTML生成"""
        return f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E2Eテストレポート - {self.report_data['timestamp']}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
        body {{
            background-color: #f8f9fa;
            padding: 20px;
        }}
        .report-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .error-item {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
        }}
        .success-item {{
            background: #d1e7dd;
            border-left: 4px solid #198754;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
        }}
        .table-responsive {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="report-header">
            <h1><i class="bi bi-check2-circle"></i> E2E全階層テストレポート</h1>
            <p class="mb-0">生成日時: {self.report_data['timestamp']}</p>
        </div>

        <div class="row">
            <div class="col-md-3">
                <div class="stat-card text-center">
                    <h3 class="text-success">{len([p for p in self.report_data.get('pages', []) if p.get('status') == 'success'])}</h3>
                    <p>成功ページ</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card text-center">
                    <h3 class="text-danger">{len(self.report_data.get('errors', []))}</h3>
                    <p>エラー</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card text-center">
                    <h3 class="text-warning">{len(self.report_data.get('warnings', []))}</h3>
                    <p>警告</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card text-center">
                    <h3 class="text-info">{len(self.report_data.get('apis', []))}</h3>
                    <p>テスト済API</p>
                </div>
            </div>
        </div>

        <div class="table-responsive mt-4">
            <h2><i class="bi bi-file-earmark-text"></i> ページチェック結果</h2>
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>ページ</th>
                        <th>パス</th>
                        <th>ステータス</th>
                        <th>レスポンスタイム</th>
                    </tr>
                </thead>
                <tbody>
                    {self._generate_page_rows()}
                </tbody>
            </table>
        </div>

        <div class="table-responsive mt-4">
            <h2><i class="bi bi-code-slash"></i> APIエンドポイント結果</h2>
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>エンドポイント</th>
                        <th>メソッド</th>
                        <th>ステータスコード</th>
                        <th>結果</th>
                    </tr>
                </thead>
                <tbody>
                    {self._generate_api_rows()}
                </tbody>
            </table>
        </div>

        <div class="mt-4">
            <h2><i class="bi bi-exclamation-triangle"></i> エラー詳細</h2>
            {self._generate_error_items()}
        </div>

        <div class="mt-4">
            <h2><i class="bi bi-info-circle"></i> 推奨事項</h2>
            <div class="stat-card">
                <ul>
                    <li>すべてのエラーを修正してください</li>
                    <li>警告項目を確認し、必要に応じて対処してください</li>
                    <li>定期的にE2Eテストを実行してください</li>
                    <li>新機能追加時は必ずテストを追加してください</li>
                </ul>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

    def _generate_page_rows(self) -> str:
        """ページ結果行生成"""
        rows = []
        for page in self.report_data.get('pages', []):
            status_badge = 'success' if page.get('status') == 'success' else 'danger'
            rows.append(f'''
                <tr>
                    <td>{page.get('name', 'Unknown')}</td>
                    <td><code>{page.get('path', 'N/A')}</code></td>
                    <td><span class="badge bg-{status_badge}">{page.get('status_code', 'N/A')}</span></td>
                    <td>{page.get('response_time', 'N/A')}ms</td>
                </tr>
            ''')
        return ''.join(rows) if rows else '<tr><td colspan="4" class="text-center">データなし</td></tr>'

    def _generate_api_rows(self) -> str:
        """API結果行生成"""
        rows = []
        for api in self.report_data.get('apis', []):
            status_badge = 'success' if api.get('status_code') == 200 else 'danger'
            rows.append(f'''
                <tr>
                    <td><code>{api.get('path', 'N/A')}</code></td>
                    <td><span class="badge bg-secondary">{api.get('method', 'GET')}</span></td>
                    <td><span class="badge bg-{status_badge}">{api.get('status_code', 'N/A')}</span></td>
                    <td>{api.get('result', 'N/A')}</td>
                </tr>
            ''')
        return ''.join(rows) if rows else '<tr><td colspan="4" class="text-center">データなし</td></tr>'

    def _generate_error_items(self) -> str:
        """エラー項目生成"""
        items = []
        for error in self.report_data.get('errors', []):
            items.append(f'''
                <div class="error-item">
                    <strong><i class="bi bi-x-circle"></i> {error.get('title', 'エラー')}</strong>
                    <p class="mb-0 mt-2">{error.get('detail', 'N/A')}</p>
                </div>
            ''')
        return ''.join(items) if items else '<p class="text-muted">エラーはありません</p>'

    def add_page_result(self, name: str, path: str, status_code: int, response_time: float = 0):
        """ページ結果追加"""
        self.report_data['pages'].append({
            'name': name,
            'path': path,
            'status_code': status_code,
            'status': 'success' if status_code == 200 else 'error',
            'response_time': round(response_time * 1000, 2)
        })

    def add_api_result(self, path: str, method: str, status_code: int, result: str):
        """API結果追加"""
        self.report_data['apis'].append({
            'path': path,
            'method': method,
            'status_code': status_code,
            'result': result
        })

    def add_error(self, title: str, detail: str):
        """エラー追加"""
        self.report_data['errors'].append({
            'title': title,
            'detail': detail
        })

    def add_warning(self, title: str, detail: str):
        """警告追加"""
        self.report_data['warnings'].append({
            'title': title,
            'detail': detail
        })


def main():
    """デモ実行"""
    generator = E2EReportGenerator()

    # サンプルデータ追加
    generator.add_page_result('トップページ', '/', 200, 0.123)
    generator.add_page_result('リリース一覧', '/releases', 200, 0.456)
    generator.add_page_result('カレンダー', '/calendar', 200, 0.789)
    generator.add_page_result('設定', '/config', 404, 0.012)

    generator.add_api_result('/api/stats', 'GET', 200, 'OK')
    generator.add_api_result('/api/releases/recent', 'GET', 200, 'OK')
    generator.add_api_result('/api/unknown', 'GET', 404, 'Not Found')

    generator.add_error('404 Not Found', '/config ページが見つかりません')
    generator.add_warning('テンプレート警告', 'url_for() の使用に注意')

    # レポート生成
    report_path = generator.generate_html_report()
    print(f"\n📊 レポートパス: {report_path}")


if __name__ == '__main__':
    main()
