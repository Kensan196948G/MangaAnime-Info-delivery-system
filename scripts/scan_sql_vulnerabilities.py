#!/usr/bin/env python3
"""
SQLインジェクション脆弱性スキャナー

プロジェクト全体でSQLインジェクションの脆弱性パターンを検出します。
"""
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# 脆弱性パターン定義
VULNERABLE_PATTERNS = [
    # f-string パターン
    (
        r'cursor\.execute\s*\(\s*f["\'].*?SELECT.*?\{.*?\}',
        'F-STRING_SQL',
        'f-stringによるSQL構築（危険）'
    ),
    (
        r'cursor\.execute\s*\(\s*f["\'].*?INSERT.*?\{.*?\}',
        'F-STRING_SQL',
        'f-stringによるSQL構築（危険）'
    ),
    (
        r'cursor\.execute\s*\(\s*f["\'].*?UPDATE.*?\{.*?\}',
        'F-STRING_SQL',
        'f-stringによるSQL構築（危険）'
    ),
    (
        r'cursor\.execute\s*\(\s*f["\'].*?DELETE.*?\{.*?\}',
        'F-STRING_SQL',
        'f-stringによるSQL構築（危険）'
    ),

    # 文字列結合パターン
    (
        r'cursor\.execute\s*\(\s*["\'].*?SELECT.*?["\']?\s*\+',
        'STRING_CONCAT_SQL',
        '文字列結合によるSQL構築（危険）'
    ),
    (
        r'cursor\.execute\s*\(\s*["\'].*?INSERT.*?["\']?\s*\+',
        'STRING_CONCAT_SQL',
        '文字列結合によるSQL構築（危険）'
    ),
    (
        r'cursor\.execute\s*\(\s*["\'].*?UPDATE.*?["\']?\s*\+',
        'STRING_CONCAT_SQL',
        '文字列結合によるSQL構築（危険）'
    ),
    (
        r'cursor\.execute\s*\(\s*["\'].*?DELETE.*?["\']?\s*\+',
        'STRING_CONCAT_SQL',
        '文字列結合によるSQL構築（危険）'
    ),

    # format() パターン
    (
        r'cursor\.execute\s*\(.*?\.format\s*\(',
        'FORMAT_SQL',
        'format()によるSQL構築（危険）'
    ),

    # % フォーマット
    (
        r'cursor\.execute\s*\(\s*["\'].*?SELECT.*?%[sd]',
        'PERCENT_FORMAT_SQL',
        '%フォーマットによるSQL構築（危険）'
    ),
]

# 除外パターン（安全なケース）
SAFE_PATTERNS = [
    r'PRAGMA',  # PRAGMA文は安全
    r'sqlite_master',  # システムテーブルは安全
    r'#.*cursor\.execute',  # コメント行
]


def scan_file(file_path: Path) -> List[Dict]:
    """ファイルをスキャンして脆弱性を検出"""
    vulnerabilities = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            # 安全なパターンに一致する場合はスキップ
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in SAFE_PATTERNS):
                continue

            # 脆弱性パターンをチェック
            for pattern, vuln_type, description in VULNERABLE_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE | re.DOTALL):
                    vulnerabilities.append({
                        'file': str(file_path),
                        'line': line_num,
                        'type': vuln_type,
                        'description': description,
                        'code': line.strip(),
                    })

    except Exception as e:
        logger.info(f"⚠️  エラー: {file_path}: {e}", file=sys.stderr)

    return vulnerabilities


def scan_project(project_root: Path) -> Dict[str, List[Dict]]:
    """プロジェクト全体をスキャン"""
    results = {}

    # スキャン対象ファイルパターン
    patterns = [
        '**/*.py',
    ]

    # 除外ディレクトリ
    exclude_dirs = {
        '.git', '__pycache__', 'venv', 'env', '.venv',
        'node_modules', '.pytest_cache', '.tox'
    }

    python_files = []
    for pattern in patterns:
        for file_path in project_root.glob(pattern):
            # 除外ディレクトリをスキップ
            if any(exc_dir in file_path.parts for exc_dir in exclude_dirs):
                continue

            if file_path.is_file():
                python_files.append(file_path)

    logger.info(f"🔍 スキャン中... ({len(python_files)}ファイル)")

    for file_path in python_files:
        vulnerabilities = scan_file(file_path)
        if vulnerabilities:
            results[str(file_path)] = vulnerabilities

    return results


def generate_report(results: Dict[str, List[Dict]]) -> None:
    """レポートを生成"""
    logger.info("\n" + "=" * 80)
    logger.info("🛡️  SQLインジェクション脆弱性スキャン結果")
    logger.info("=" * 80)

    if not results:
        logger.info("\n✅ 脆弱性は検出されませんでした！")
        return

    total_vulnerabilities = sum(len(vulns) for vulns in results.values())

    logger.info(f"\n⚠️  {total_vulnerabilities}件の脆弱性を検出しました")
    logger.info(f"📁 影響を受けるファイル: {len(results)}件\n")

    # ファイルごとに表示
    for file_path, vulnerabilities in sorted(results.items()):
        logger.info("-" * 80)
        logger.info(f"📄 {file_path}")
        logger.info(f"   脆弱性: {len(vulnerabilities)}件\n")

        for vuln in vulnerabilities:
            logger.info(f"   🔴 行 {vuln['line']}: {vuln['description']}")
            logger.info(f"      種類: {vuln['type']}")
            logger.info(f"      コード: {vuln['code'][:80]}")
            logger.info()

    # サマリー
    logger.info("\n" + "=" * 80)
    logger.info("📊 脆弱性タイプ別集計")
    logger.info("=" * 80)

    type_counts = {}
    for vulnerabilities in results.values():
        for vuln in vulnerabilities:
            vuln_type = vuln['type']
            type_counts[vuln_type] = type_counts.get(vuln_type, 0) + 1

    for vuln_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {vuln_type}: {count}件")

    # 推奨事項
    logger.info("\n" + "=" * 80)
    logger.info("💡 修正方法")
    logger.info("=" * 80)
    logger.info("""
1. パラメータ化クエリを使用:
   ❌ cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
   ✅ cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

2. 複数パラメータの場合:
   ✅ cursor.execute("SELECT * FROM users WHERE name = ? AND age > ?", (name, age))

3. テーブル名の動的使用は検証を徹底:
   ✅ ALLOWED_TABLES = {'users', 'works', 'releases'}
   ✅ if table_name not in ALLOWED_TABLES:
   ✅     raise ValueError("Invalid table")
   ✅ cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (user_id,))

4. PRAGMA文は安全（ただし入力検証は必須）:
   ✅ cursor.execute(f"PRAGMA table_info({table_name})")
      ※ table_nameはsqlite_masterから取得した値など信頼できるソースのみ
""")


def generate_markdown_report(results: Dict[str, List[Dict]], output_path: Path) -> None:
    """Markdown形式のレポートを生成"""
    with open(output_path, 'w', encoding='utf-8') as f:

        f.write("# SQLインジェクション脆弱性スキャン結果\n\n")
        f.write(f"**スキャン日時**: {Path.cwd()}\n\n")

        if not results:
            f.write("## ✅ 結果\n\n")
            f.write("脆弱性は検出されませんでした。\n")
            return

        total_vulnerabilities = sum(len(vulns) for vulns in results.values())

        f.write("## ⚠️ 検出結果\n\n")
        f.write(f"- **総脆弱性数**: {total_vulnerabilities}件\n")
        f.write(f"- **影響ファイル数**: {len(results)}件\n\n")

        f.write("## 📋 詳細\n\n")

        for file_path, vulnerabilities in sorted(results.items()):
            f.write(f"### 📄 `{file_path}`\n\n")
            f.write(f"脆弱性: **{len(vulnerabilities)}件**\n\n")

            for vuln in vulnerabilities:
                f.write(f"#### 🔴 行 {vuln['line']}\n\n")
                f.write(f"- **種類**: {vuln['type']}\n")
                f.write(f"- **説明**: {vuln['description']}\n")
                f.write(f"- **コード**:\n")
                f.write(f"  ```python\n")
                f.write(f"  {vuln['code']}\n")
                f.write(f"  ```\n\n")

        # 修正方法
        f.write("## 💡 修正方法\n\n")
        f.write("### パラメータ化クエリの使用\n\n")
        f.write("```python\n")
        f.write("# ❌ 危険\n")
        f.write('cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")\n\n')
        f.write("# ✅ 安全\n")
        f.write('cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))\n')
        f.write("```\n\n")

    logger.info(f"\n📝 詳細レポートを生成: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='SQLインジェクション脆弱性スキャナー')
    parser.add_argument(
        '--project-root',
        default='.',
        help='プロジェクトルートディレクトリ（デフォルト: カレントディレクトリ）'
    )
    parser.add_argument(
        '--output',
        default='docs/SQL_INJECTION_SCAN_REPORT.md',
        help='レポート出力先（デフォルト: docs/SQL_INJECTION_SCAN_REPORT.md）'
    )

    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    output_path = Path(args.output)

    logger.info(f"📂 プロジェクトルート: {project_root}")

    results = scan_project(project_root)
    generate_report(results)

    # Markdownレポート生成
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generate_markdown_report(results, output_path)

    # 終了コード
    sys.exit(1 if results else 0)
