# MangaAnime情報配信システム - ドキュメント目次

アニメ・マンガの最新情報を自動で収集し、Gmail通知とGoogleカレンダー統合により、リアルタイムでユーザーに配信する完全自動化システムのドキュメント集です。

## クイックリンク

- [システム概要](./technical/システム概要.md) - システム全体の概要
- [クイックスタートガイド](./setup/QUICK_START_GUIDE.md) - 最速でシステムを起動
- [デプロイメントガイド](./setup/DEPLOYMENT_GUIDE.md) - 本番環境へのデプロイ手順
- [トラブルシューティング](./troubleshooting/トラブルシューティングガイド.md) - 問題解決ガイド

---

## 📁 ドキュメント構成

### 📦 setup/ - セットアップ・インストール

初期セットアップ、環境構築、認証設定に関するドキュメント

| ドキュメント | 説明 |
|------------|------|
| [QUICK_START_GUIDE.md](./setup/QUICK_START_GUIDE.md) | 並列開発成果の活用とクイックスタート |
| [DEPLOYMENT_GUIDE.md](./setup/DEPLOYMENT_GUIDE.md) | 本番環境へのデプロイメント手順 |
| [GMAIL_SETUP_GUIDE.md](./setup/GMAIL_SETUP_GUIDE.md) | Gmail App Password設定ガイド |
| [README_AUTH_SETUP.md](./setup/README_AUTH_SETUP.md) | API認証セットアップ |
| [GIT_SETUP_GUIDE.md](./setup/GIT_SETUP_GUIDE.md) | Git環境のセットアップ |
| [INSTALL_GITHUB_CLI.md](./setup/INSTALL_GITHUB_CLI.md) | GitHub CLI インストール手順 |
| [PRODUCTION_CONFIG.md](./setup/PRODUCTION_CONFIG.md) | 本番環境設定ガイド |
| [SECURITY_CONFIGURATION.md](./setup/SECURITY_CONFIGURATION.md) | セキュリティ設定 |
| [設定ガイド.md](./setup/設定ガイド.md) | システム全般の設定手順 |

### 📖 usage/ - 利用手順・操作ガイド

システムの使い方、Web UIの操作方法に関するドキュメント

| ドキュメント | 説明 |
|------------|------|
| [WEB_UI_README.md](./usage/WEB_UI_README.md) | Web UIの使い方 |
| [WEBUI_COMPLETE.md](./usage/WEBUI_COMPLETE.md) | Web UI完全ガイド |
| [EDGE_ACCESS.md](./usage/EDGE_ACCESS.md) | Edgeブラウザでのアクセス方法 |
| [利用手順書.md](./usage/利用手順書.md) | システム利用手順書 |

### 🔧 technical/ - 技術仕様・アーキテクチャ

システムアーキテクチャ、技術仕様、API仕様に関するドキュメント

| ドキュメント | 説明 |
|------------|------|
| [システム概要.md](./technical/システム概要.md) | システム全体の概要 |
| [システム構成図.md](./technical/システム構成図.md) | システムアーキテクチャ図 |
| [技術仕様書.md](./technical/技術仕様書.md) | 詳細技術仕様 |
| [API仕様書.md](./technical/API仕様書.md) | REST API仕様書 |
| [architecture.md](./technical/architecture.md) | アーキテクチャ設計 |
| [architectural_guidelines.md](./technical/architectural_guidelines.md) | アーキテクチャガイドライン |
| [UI_ARCHITECTURE.md](./technical/UI_ARCHITECTURE.md) | UI設計とアーキテクチャ |
| [BACKEND_ENHANCEMENTS.md](./technical/BACKEND_ENHANCEMENTS.md) | バックエンド強化機能 |
| [BACKEND_ENHANCEMENTS_SUMMARY.md](./technical/BACKEND_ENHANCEMENTS_SUMMARY.md) | バックエンド強化サマリー |
| [SYSTEM_REQUIREMENTS.md](./technical/SYSTEM_REQUIREMENTS.md) | システム要件 |
| [WORKFLOW_FIX_REPORT.md](./technical/WORKFLOW_FIX_REPORT.md) | ワークフロー修正レポート |
| [AGENT_TASK_ASSIGNMENTS.md](./technical/AGENT_TASK_ASSIGNMENTS.md) | エージェントタスク割り当て |
| [security_guidelines.md](./technical/security_guidelines.md) | セキュリティガイドライン |
| [メール配信システム概要.md](./technical/メール配信システム概要.md) | メール配信システムの詳細 |

### 👨‍💻 development/ - 開発者向け

開発手順、AI開発環境、技術優先順位に関するドキュメント

| ドキュメント | 説明 |
|------------|------|
| [AI_DEVELOPMENT_GUIDE.md](./development/AI_DEVELOPMENT_GUIDE.md) | AI開発環境ガイド（ClaudeCode + Claude-Flow） |
| [TECHNICAL_PRIORITIES_ROADMAP.md](./development/TECHNICAL_PRIORITIES_ROADMAP.md) | 技術優先順位とロードマップ |
| [frontend_enhancement_plan.md](./development/frontend_enhancement_plan.md) | フロントエンド強化計画 |
| [ui_design_analysis.md](./development/ui_design_analysis.md) | UI設計分析 |
| [qa_processes.md](./development/qa_processes.md) | 品質保証プロセス |

### 🔄 operations/ - 運用・保守

日常運用、DevOps、自動化、バックアップに関するドキュメント

| ドキュメント | 説明 |
|------------|------|
| [運用マニュアル.md](./operations/運用マニュアル.md) | システム運用マニュアル |
| [運用手順書.md](./operations/運用手順書.md) | 日常運用手順 |
| [AUTO_SYSTEM_GUIDE.md](./operations/AUTO_SYSTEM_GUIDE.md) | 自動化システムガイド |
| [AUTOMATION_README.md](./operations/AUTOMATION_README.md) | 自動化機能の概要 |
| [AUTO_ERROR_REPAIR_SYSTEM.md](./operations/AUTO_ERROR_REPAIR_SYSTEM.md) | 自動エラー修復システム |
| [AUTO_REPAIR_7X_SYSTEM.md](./operations/AUTO_REPAIR_7X_SYSTEM.md) | 7倍速自動修復システム |
| [DEVOPS_IMPROVEMENTS.md](./operations/DEVOPS_IMPROVEMENTS.md) | DevOps改善レポート |
| [DEVOPS_QUICKSTART.md](./operations/DEVOPS_QUICKSTART.md) | DevOpsクイックスタート |
| [GITHUB_ACTIONS_GUIDE.md](./operations/GITHUB_ACTIONS_GUIDE.md) | GitHub Actions設定ガイド |
| [GITHUB_NOTIFICATION_DISABLE_GUIDE.md](./operations/GITHUB_NOTIFICATION_DISABLE_GUIDE.md) | GitHub通知の無効化 |
| [GITHUB_SECRETS_SETUP.md](./operations/GITHUB_SECRETS_SETUP.md) | GitHub Secrets設定 |
| [backup_strategy.md](./operations/backup_strategy.md) | バックアップ戦略 |

### 📊 reports/ - レポート・分析

各種開発レポート、品質レポート、セキュリティ監査レポート

| ドキュメント | 説明 |
|------------|------|
| [CTO_ARCHITECTURE_VALIDATION_REPORT.md](./reports/CTO_ARCHITECTURE_VALIDATION_REPORT.md) | CTOアーキテクチャ検証レポート |
| [CTO_COMPREHENSIVE_ARCHITECTURE_REPORT.md](./reports/CTO_COMPREHENSIVE_ARCHITECTURE_REPORT.md) | CTO包括的アーキテクチャレポート |
| [cto_architecture_summary.md](./reports/cto_architecture_summary.md) | CTOアーキテクチャサマリー |
| [INTEGRATION_REPORT.md](./reports/INTEGRATION_REPORT.md) | 統合レポート |
| [CODE_REVIEW_REPORT.md](./reports/CODE_REVIEW_REPORT.md) | コードレビューレポート |
| [CODE_QUALITY_REPORT.md](./reports/CODE_QUALITY_REPORT.md) | コード品質レポート |
| [SECURITY_AUDIT_REPORT.md](./reports/SECURITY_AUDIT_REPORT.md) | セキュリティ監査レポート |
| [BACKEND_DEVELOPMENT_REPORT.md](./reports/BACKEND_DEVELOPMENT_REPORT.md) | バックエンド開発レポート |
| [UI_UX_IMPROVEMENT_REPORT.md](./reports/UI_UX_IMPROVEMENT_REPORT.md) | UI/UX改善レポート |
| [calendar-ui-enhancement-report.md](./reports/calendar-ui-enhancement-report.md) | カレンダーUI強化レポート |
| [PHASE2_IMPLEMENTATION_REPORT.md](./reports/PHASE2_IMPLEMENTATION_REPORT.md) | フェーズ2実装レポート |
| [PHASE2_TEST_QUALITY_REPORT.md](./reports/PHASE2_TEST_QUALITY_REPORT.md) | フェーズ2テスト品質レポート |
| [TESTING_STRATEGY_REPORT.md](./reports/TESTING_STRATEGY_REPORT.md) | テスト戦略レポート |
| [TESTING_STRATEGY_IMPLEMENTATION_REPORT.md](./reports/TESTING_STRATEGY_IMPLEMENTATION_REPORT.md) | テスト戦略実装レポート |
| [TEST_REPORT.md](./reports/TEST_REPORT.md) | テストレポート |
| [TEST_IMPROVEMENTS_SUMMARY.md](./reports/TEST_IMPROVEMENTS_SUMMARY.md) | テスト改善サマリー |
| [TEST_FIX_REPORT.md](./reports/TEST_FIX_REPORT.md) | テスト修正レポート |
| [E2E_TEST_IMPLEMENTATION_REPORT.md](./reports/E2E_TEST_IMPLEMENTATION_REPORT.md) | E2Eテスト実装レポート |
| [PRODUCTION_READINESS_REPORT.md](./reports/PRODUCTION_READINESS_REPORT.md) | 本番準備レポート |
| [DEVELOPMENT_SUMMARY.md](./reports/DEVELOPMENT_SUMMARY.md) | 開発サマリー |
| [DEVOPS_SUMMARY.md](./reports/DEVOPS_SUMMARY.md) | DevOpsサマリー |
| [LINT_FIX_SUMMARY.md](./reports/LINT_FIX_SUMMARY.md) | Lint修正サマリー |
| [FINAL_REPORT.md](./reports/FINAL_REPORT.md) | 最終レポート |
| [SETUP_REPORT_20250815_174754.md](./reports/SETUP_REPORT_20250815_174754.md) | セットアップレポート |
| [database_optimization_report.md](./reports/database_optimization_report.md) | データベース最適化レポート |
| [development_schedule.md](./reports/development_schedule.md) | 開発スケジュール |

### 🔍 troubleshooting/ - トラブルシューティング

エラー対処、問題解決、制限事項に関するドキュメント

| ドキュメント | 説明 |
|------------|------|
| [トラブルシューティングガイド.md](./troubleshooting/トラブルシューティングガイド.md) | 包括的なトラブルシューティング |
| [トラブルシューティング.md](./troubleshooting/トラブルシューティング.md) | 一般的な問題解決 |
| [ERROR_NOTIFICATION_GUIDE.md](./troubleshooting/ERROR_NOTIFICATION_GUIDE.md) | エラー通知ガイド |
| [REPAIR_REPORT.md](./troubleshooting/REPAIR_REPORT.md) | 修復レポート |
| [BROWSER_CACHE_CLEAR.md](./troubleshooting/BROWSER_CACHE_CLEAR.md) | ブラウザキャッシュクリア手順 |
| [GOOGLE_CALENDAR_LIMITATIONS.md](./troubleshooting/GOOGLE_CALENDAR_LIMITATIONS.md) | Googleカレンダーの制限事項 |

---

## 🚀 はじめに

1. **初めてのセットアップ**: [クイックスタートガイド](./setup/QUICK_START_GUIDE.md)から始めてください
2. **本番環境デプロイ**: [デプロイメントガイド](./setup/DEPLOYMENT_GUIDE.md)を参照
3. **問題が発生**: [トラブルシューティングガイド](./troubleshooting/トラブルシューティングガイド.md)で解決

## 🤖 AI開発環境

本プロジェクトは **ClaudeCode（12体のSubAgent）+ Claude-Flow（Swarm並列開発）+ Context7** の統合AI開発環境に対応しています。

詳細は [AI開発ガイド](./development/AI_DEVELOPMENT_GUIDE.md) を参照してください。

## 📝 ドキュメント規約

- 全ドキュメントはMarkdown形式
- 相対パスでリンクを記述
- 日本語と英語のドキュメントが混在

## 🔄 最終更新

- ドキュメント構造整理: 2025-11-14
- 総ドキュメント数: 73ファイル
- カテゴリ数: 7カテゴリ

---

**MangaAnime情報配信システム開発チーム**
