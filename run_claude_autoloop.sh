#!/bin/bash

echo "🔄 MangaAnime開発システム - Claude並列開発を開始します..."

# プロジェクトディレクトリに移動
cd "/media/kensan/LinuxHDD/MangaAnime-Info-delivery-system" || exit 1

# 環境変数設定
export CLAUDE_PROJECT="MangaAnime-Info-Delivery"
export PYTHONPATH="${PWD}:${PYTHONPATH}"

echo "📁 作業ディレクトリ: $(pwd)"
echo "🤖 Agent構成: CTO, DevAPI, DevUI, QA, Tester"
echo "📋 フェーズ管理: workflows/batch.yaml"
echo "🎯 実行制限: 最大7回のイテレーション"
echo ""

# Claude Code実行（基本コマンド）
claude --dangerously-skip-permissions \
       "Phase 1から順番に5体のAgentで並列開発を実行してください。

このプロジェクトはアニメ・マンガ情報配信システムです。
CLAUDE.mdファイルに詳細仕様が記載されています。

Agent構成:
- MangaAnime-CTO: システム全体設計・技術判断・統合レビュー  
- MangaAnime-DevAPI: バックエンド・API・データベース実装
- MangaAnime-DevUI: Web UI開発（将来拡張機能）
- MangaAnime-QA: セキュリティ・品質保証・レビュー  
- MangaAnime-Tester: 自動テスト生成・CI/CD・パフォーマンステスト

開発フェーズ:
Phase 1: 基盤設計・DB設計（CTO、DevAPI、QA、Tester）
Phase 2: 情報収集機能実装（DevAPI、Tester、QA）  
Phase 3: 通知・連携機能実装（DevAPI、Tester、QA）
Phase 4: 統合・エラーハンドリング強化（全Agent）
Phase 5: 最終テスト・デプロイ準備（全Agent）

.claude/agents/ディレクトリのAgent定義ファイルを参照して、
各Agentの役割に従って並列で作業を進めてください。
Python + SQLite + Gmail API + Google Calendar APIで実装してください。"

echo ""
echo "✅ Claude並列開発が完了しました。"
echo "📊 結果確認:"
echo "  - ログファイル: logs/"
echo "  - 生成されたコード: modules/"
echo "  - テストファイル: tests/"
echo ""
echo "🔄 次回実行時は以下のコマンド:"
echo "  ./run_claude_autoloop.sh"