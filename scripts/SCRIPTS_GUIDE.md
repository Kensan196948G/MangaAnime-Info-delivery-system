# Scripts Directory Guide

**更新日**: 2025-11-14
**整理完了**: DevOps Agent

---

## ディレクトリ構造

```
scripts/
├── setup/          # 初期セットアップスクリプト
├── operations/     # 日常運用スクリプト
├── automation/     # 自動化・修復スクリプト
├── maintenance/    # 保守・検証スクリプト
└── development/    # 開発支援スクリプト
```

---

## 1. setup/ - 初期セットアップ

初回インストール時や環境構築時に使用するスクリプト群

### スクリプト一覧

| ファイル名 | 用途 | 実行タイミング |
|-----------|------|--------------|
| `setup_env.sh` | 環境変数のセットアップ | 初回のみ |
| `setup_email.sh` | Gmail API設定 | 初回のみ |
| `setup_cron.sh` | cron定期実行設定 | 初回のみ |
| `install_auto_startup.sh` | システム自動起動設定 | オプション |
| `install_webui_autostart.sh` | WebUI自動起動設定 | オプション |

### 使用例

```bash
# 基本セットアップ
cd scripts/setup
./setup_env.sh
./setup_email.sh
./setup_cron.sh

# 自動起動が必要な場合
./install_auto_startup.sh
./install_webui_autostart.sh
```

---

## 2. operations/ - 日常運用

システムの起動や日常的な操作に使用するスクリプト群

### スクリプト一覧

| ファイル名 | 用途 | 使用頻度 |
|-----------|------|---------|
| `quick_start.sh` | クイックスタート（推奨） | 毎日 |
| `run_now.sh` | 情報収集の即時実行 | 必要時 |
| `start_mangaanime_web.sh` | WebUI起動 | 毎日 |
| `start_webui_manual.sh` | WebUI手動起動 | 必要時 |
| `show_webui_access.sh` | アクセス情報表示 | 必要時 |

### 使用例

```bash
# システム起動（最も簡単な方法）
cd scripts/operations
./quick_start.sh

# WebUI起動
./start_mangaanime_web.sh

# アクセス情報確認
./show_webui_access.sh
```

---

## 3. automation/ - 自動化・修復

自動修復システムや継続的な監視に使用するスクリプト群

### スクリプト一覧

| ファイル名 | 用途 | 実行モード |
|-----------|------|-----------|
| `start-automation.sh` | 自動化システム起動 | バックグラウンド |
| `start-local-repair.sh` | ローカル修復起動 | バックグラウンド |
| `start-repair-background.sh` | バックグラウンド修復 | デーモン |
| `local-repair-system.sh` | ローカル修復システム | 手動/自動 |
| `test-repair-demo.sh` | 修復デモ（テスト用） | 手動 |

### 使用例

```bash
# 自動修復システム起動
cd scripts/automation
./start-automation.sh

# バックグラウンドで継続監視
./start-repair-background.sh

# 修復機能のテスト
./test-repair-demo.sh
```

---

## 4. maintenance/ - 保守・検証

システムメンテナンスや定期検証に使用するスクリプト群

### スクリプト一覧

| ファイル名 | 用途 | 実行頻度 |
|-----------|------|---------|
| `backup_full.sh` | フルバックアップ | 週次推奨 |
| `check_tests.sh` | テスト確認 | 必要時 |
| `run_validation.sh` | システム検証 | 必要時 |

### 使用例

```bash
# 週次バックアップ
cd scripts/maintenance
./backup_full.sh

# テスト実行確認
./check_tests.sh

# システム整合性検証
./run_validation.sh
```

---

## 5. development/ - 開発支援

AI開発やデバッグに使用するスクリプト群

### スクリプト一覧

| ファイル名 | 用途 | 対象者 |
|-----------|------|-------|
| `run_claude_autoloop.sh` | Claude自動ループ | 開発者 |
| `start_integrated_ai_development.sh` | AI統合開発 | 開発者 |

### 使用例

```bash
# Claude統合開発環境起動
cd scripts/development
./start_integrated_ai_development.sh

# Claude自動ループ実行
./run_claude_autoloop.sh
```

---

## クイックリファレンス

### 初回セットアップ（新規インストール時）
```bash
# 1. 環境構築
cd scripts/setup
./setup_env.sh
./setup_email.sh
./setup_cron.sh

# 2. システム起動
cd ../operations
./quick_start.sh
```

### 日常運用
```bash
# システム起動
cd scripts/operations
./quick_start.sh

# WebUI起動
./start_mangaanime_web.sh
```

### トラブル発生時
```bash
# 1. 自動修復を試行
cd scripts/automation
./start-local-repair.sh

# 2. システム検証
cd ../maintenance
./run_validation.sh

# 3. バックアップから復元（最終手段）
./backup_full.sh --restore
```

---

## 注意事項

1. **権限エラーが出る場合**
   ```bash
   chmod +x scripts/**/*.sh
   ```

2. **パスの指定**
   - プロジェクトルートからの相対パスで実行
   - 例: `./scripts/operations/quick_start.sh`

3. **ログの確認**
   ```bash
   tail -f logs/app.log
   ```

4. **Git履歴の保持**
   - 全ファイルは`git mv`で移動済み
   - 変更履歴は完全に保持されています

---

**整理完了**: 2025-11-14
**担当**: DevOps Agent
**移動ファイル数**: 20個
