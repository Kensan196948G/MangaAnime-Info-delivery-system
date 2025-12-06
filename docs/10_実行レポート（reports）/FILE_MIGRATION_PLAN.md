# ファイル移動計画書

**作成日**: 2025-11-14
**作成者**: DevOps Agent
**目的**: ルートディレクトリに散在するシェルスクリプトを整理し、保守性を向上させる

---

## 1. 現状の問題点

### 問題
- ルートディレクトリに20個のシェルスクリプトが散在
- scripts/ディレクトリにも19個のスクリプトが存在
- カテゴリ分けが不明確で、どのスクリプトを使うべきか分かりにくい
- 機能的な重複がある可能性

### 影響
- 新規開発者のオンボーディングが困難
- メンテナンス性の低下
- 誤ったスクリプトの実行リスク

---

## 2. 移動計画

### 2.1 ディレクトリ構造

```
scripts/
├── setup/          # 初期セットアップ関連
├── operations/     # 運用・起動関連
├── automation/     # 自動化・修復関連
├── maintenance/    # バックアップ・検証関連
└── development/    # 開発支援ツール
```

### 2.2 ファイル分類

#### setup/ (初期セットアップ)
- `setup_env.sh` - 環境変数セットアップ
- `setup_email.sh` - メール設定
- `setup_cron.sh` - cron設定
- `install_auto_startup.sh` - 自動起動インストール
- `install_webui_autostart.sh` - WebUI自動起動

#### operations/ (日常運用)
- `quick_start.sh` - クイックスタート
- `run_now.sh` - 即時実行
- `start_mangaanime_web.sh` - WebUI起動
- `start_webui_manual.sh` - WebUI手動起動
- `show_webui_access.sh` - アクセス情報表示

#### automation/ (自動化・修復)
- `start-automation.sh` - 自動化システム起動
- `start-local-repair.sh` - ローカル修復起動
- `start-repair-background.sh` - バックグラウンド修復
- `local-repair-system.sh` - ローカル修復システム
- `test-repair-demo.sh` - 修復デモ

#### maintenance/ (保守・検証)
- `backup_full.sh` - フルバックアップ
- `check_tests.sh` - テスト確認
- `run_validation.sh` - 検証実行

#### development/ (開発支援)
- `run_claude_autoloop.sh` - Claude自動ループ
- `start_integrated_ai_development.sh` - AI統合開発

---

## 3. 実行手順

### Phase 1: ディレクトリ作成
```bash
mkdir -p scripts/{setup,operations,automation,maintenance,development}
```

### Phase 2: ファイル移動（git mvで履歴保持）

#### setup/
```bash
git mv setup_env.sh scripts/setup/
git mv setup_email.sh scripts/setup/
git mv setup_cron.sh scripts/setup/
git mv install_auto_startup.sh scripts/setup/
git mv install_webui_autostart.sh scripts/setup/
```

#### operations/
```bash
git mv quick_start.sh scripts/operations/
git mv run_now.sh scripts/operations/
git mv start_mangaanime_web.sh scripts/operations/
git mv start_webui_manual.sh scripts/operations/
git mv show_webui_access.sh scripts/operations/
```

#### automation/
```bash
git mv start-automation.sh scripts/automation/
git mv start-local-repair.sh scripts/automation/
git mv start-repair-background.sh scripts/automation/
git mv local-repair-system.sh scripts/automation/
git mv test-repair-demo.sh scripts/automation/
```

#### maintenance/
```bash
git mv backup_full.sh scripts/maintenance/
git mv check_tests.sh scripts/maintenance/
git mv run_validation.sh scripts/maintenance/
```

#### development/
```bash
git mv run_claude_autoloop.sh scripts/development/
git mv start_integrated_ai_development.sh scripts/development/
```

### Phase 3: パス参照の更新

以下のファイルでパス参照を更新:
- README.md
- docs/setup/*.md
- docs/operations/*.md
- .github/workflows/*.yml
- その他のスクリプトからの相対パス

---

## 4. 検証項目

- [ ] 全ファイルが正しく移動された
- [ ] git履歴が保持されている
- [ ] パス参照が全て更新された
- [ ] スクリプトが正常に実行できる
- [ ] ドキュメントのリンクが切れていない

---

## 5. ロールバック計画

移動に問題があった場合:
```bash
git reset --hard HEAD
```

---

## 6. 期待される効果

- プロジェクト構造が明確化
- 新規開発者のオンボーディング時間が50%削減
- メンテナンス性の向上
- スクリプト実行の間違いを防止
