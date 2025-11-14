#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ドキュメント参照整合性チェックツール
すべてのMarkdownファイルの参照をスキャンし、リンク切れを検出
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict
import json

# Windows環境でのUTF-8出力設定
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

class DocumentReferenceChecker:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.issues = []
        self.all_md_files = set()
        self.references = []

    def find_all_markdown_files(self):
        """すべてのMarkdownファイルを検索"""
        for md_file in self.root_dir.rglob("*.md"):
            # .gitディレクトリを除外
            if '.git' not in md_file.parts:
                relative_path = md_file.relative_to(self.root_dir)
                self.all_md_files.add(str(relative_path))

        print(f"✅ {len(self.all_md_files)} 個のMarkdownファイルを検出")

    def extract_markdown_links(self, file_path: Path) -> List[Tuple[str, int, str]]:
        """Markdownファイルからリンクを抽出"""
        links = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    # [text](path.md) 形式のリンク
                    matches = re.finditer(r'\[([^\]]+)\]\(([^)]+\.md[^)]*)\)', line)
                    for match in matches:
                        text = match.group(1)
                        link = match.group(2)
                        links.append((link, line_num, text))

                    # 直接パス参照: docs/xxx.md
                    matches = re.finditer(r'(?:^|[:\s`])([a-zA-Z0-9_\-./]+\.md)(?:[:\s`]|$)', line)
                    for match in matches:
                        path = match.group(1)
                        if not path.startswith('http'):
                            links.append((path, line_num, f"直接参照: {path}"))

        except Exception as e:
            print(f"⚠️ ファイル読み込みエラー: {file_path}: {e}")

        return links

    def check_link_validity(self, source_file: Path, link: str) -> Tuple[bool, str]:
        """リンクの有効性をチェック"""
        # URLリンクはスキップ
        if link.startswith(('http://', 'https://', '#')):
            return True, "外部リンク"

        # アンカーを除去
        link_path = link.split('#')[0]

        if not link_path:
            return True, "アンカーのみ"

        # 絶対パスと相対パスの両方をチェック
        source_dir = source_file.parent

        # 相対パス解決
        if link_path.startswith('./') or link_path.startswith('../'):
            target = (source_dir / link_path).resolve()
        elif link_path.startswith('/'):
            target = (self.root_dir / link_path.lstrip('/')).resolve()
        else:
            # 相対パスとして試行
            target = (source_dir / link_path).resolve()

            # 見つからなければルートからも試行
            if not target.exists():
                target = (self.root_dir / link_path).resolve()

        # ファイルの存在確認
        if target.exists():
            return True, str(target.relative_to(self.root_dir))
        else:
            return False, f"ファイルが見つかりません: {link_path}"

    def scan_all_documents(self):
        """すべてのドキュメントをスキャン"""
        print("\n🔍 ドキュメント参照をスキャン中...")

        for md_file_str in sorted(self.all_md_files):
            md_file = self.root_dir / md_file_str
            links = self.extract_markdown_links(md_file)

            for link, line_num, text in links:
                is_valid, message = self.check_link_validity(md_file, link)

                ref_info = {
                    'source': str(md_file_str),
                    'line': line_num,
                    'link': link,
                    'text': text,
                    'valid': is_valid,
                    'message': message
                }

                self.references.append(ref_info)

                if not is_valid:
                    self.issues.append(ref_info)
                    print(f"❌ {md_file_str}:{line_num} -> {link}")
                    print(f"   理由: {message}")

    def generate_report(self) -> Dict:
        """レポートを生成"""
        report = {
            'summary': {
                'total_md_files': len(self.all_md_files),
                'total_references': len(self.references),
                'broken_links': len(self.issues),
                'integrity': f"{((len(self.references) - len(self.issues)) / len(self.references) * 100):.1f}%" if self.references else "N/A"
            },
            'broken_links': self.issues,
            'all_references': self.references
        }

        return report

    def print_summary(self, report: Dict):
        """サマリーを表示"""
        print("\n" + "=" * 70)
        print("📊 ドキュメント参照整合性チェック結果")
        print("=" * 70)
        print(f"総Markdownファイル数: {report['summary']['total_md_files']}")
        print(f"総参照数: {report['summary']['total_references']}")
        print(f"リンク切れ数: {report['summary']['broken_links']}")
        print(f"整合性: {report['summary']['integrity']}")
        print("=" * 70)

        if report['summary']['broken_links'] > 0:
            print("\n⚠️ 修正が必要な参照:")
            for issue in self.issues:
                print(f"\n  ファイル: {issue['source']}:{issue['line']}")
                print(f"  リンク: {issue['link']}")
                print(f"  理由: {issue['message']}")
        else:
            print("\n✅ すべての参照が有効です!")

def main():
    # 現在のスクリプトのディレクトリをルートとする
    script_dir = Path(__file__).parent.resolve()
    checker = DocumentReferenceChecker(str(script_dir))

    # ステップ1: すべてのMarkdownファイルを検索
    checker.find_all_markdown_files()

    # ステップ2: ドキュメント参照をスキャン
    checker.scan_all_documents()

    # ステップ3: レポートを生成
    report = checker.generate_report()

    # ステップ4: サマリーを表示
    checker.print_summary(report)

    # ステップ5: JSONレポートを保存
    report_file = script_dir / 'DOC_REFERENCE_REPORT.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n💾 詳細レポートを保存: {report_file}")

    return len(checker.issues)

if __name__ == '__main__':
    exit_code = main()
    exit(exit_code)
