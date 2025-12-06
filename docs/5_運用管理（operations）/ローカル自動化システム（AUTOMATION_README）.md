# 🤖 ローカル自動化システム

## 概要
GitHub Actions の代替として動作する完全ローカル自動化システムです。  
プライベートリポジトリの無料プラン制限を回避し、ローカル環境で CI/CD パイプラインを実現します。

## 🚨 重要：GitHub Actions について
- **状態**: 全ワークフロー無効化済み
- **理由**: プライベートリポジトリの無料プラン制限（月2000分）超過
- **代替**: このローカル自動化システムを使用

## 📋 機能一覧

### 自動実行タスク（30分サイクル）
1. **テスト実行**
   - npm test / pytest 自動実行
   - 失敗時の自動修復

2. **Lint・フォーマット**
   - ESLint / Prettier / Black 自動適用
   - 修正内容の自動コミット

3. **ビルド**
   - npm build 自動実行
   - ビルドエラーの自動修復

4. **メンテナンス**
   - 古いログファイル削除
   - Git GC 実行
   - ディスク使用量監視

## 🚀 起動方法

### 簡単起動（推奨）
```bash
./start-automation.sh
```
対話的メニューから実行モードを選択

### 直接起動
```bash
# バックグラウンド実行
nohup ./scripts/local-automation-system.sh start &

# フォアグラウンド実行（デバッグ用）
./scripts/local-automation-system.sh start

# 単発実行
./scripts/local-automation-system.sh once
```

### systemd サービスとして登録（オプション）
```bash
# サービスファイルをコピー
sudo cp local-automation.service /etc/systemd/system/

# サービス有効化
sudo systemctl enable local-automation
sudo systemctl start local-automation

# 状態確認
sudo systemctl status local-automation
```

## 📊 状態確認

```bash
# システム状態表示
./scripts/local-automation-system.sh status

# ログ確認
tail -f logs/automation/system-*.log

# プロセス確認
ps aux | grep local-automation-system
```

## 🔧 設定ファイル

### 状態管理
- `.automation-state.json`: 自動化システムの実行状態
- `logs/automation/`: ログファイル格納ディレクトリ

### ログファイル
- `system-YYYYMMDD.log`: 日次システムログ
- `test-*.log`: テスト実行ログ
- `eslint-*.log`: ESLint実行ログ
- `build-*.log`: ビルドログ

## 🛑 停止方法

```bash
# プロセスIDを確認
cat .automation-daemon.pid

# プロセスを停止
kill $(cat .automation-daemon.pid)

# または
pkill -f 'local-automation-system.sh'
```

## 📝 トラブルシューティング

### Q: GitHub Actions が動作しない
A: 意図的に無効化しています。このローカルシステムを使用してください。

### Q: テストが失敗する
A: システムが自動的に以下を試みます：
- 依存関係の再インストール
- キャッシュのクリア
- 環境の再構築

### Q: ビルドが失敗する
A: 自動修復機能が動作します：
- dist/build ディレクトリのクリーンアップ
- npm cache clean --force
- 依存関係の更新

## 🔄 移行ガイド

### GitHub Actions から移行する場合

1. **ワークフロー無効化**（完了済み）
   ```bash
   gh workflow disable --all
   ```

2. **ローカルシステム起動**
   ```bash
   ./start-automation.sh
   ```

3. **監視継続**
   ```bash
   watch -n 60 './scripts/local-automation-system.sh status'
   ```

## 📈 今後の拡張予定

- [ ] Slack/Discord 通知連携
- [ ] 複数プロジェクト管理
- [ ] Web UI ダッシュボード
- [ ] Docker コンテナ化
- [ ] 分散実行サポート

## 💡 Tips

- ログは自動的に7日後に削除されます
- 30分サイクルは `CYCLE_INTERVAL` で調整可能
- エラー時は Issue が自動作成される場合があります

---
*このシステムは GitHub Actions の制限を回避するために作成されました*  
*最終更新: 2025-08-17*