# GitHub Actions ワークフロー 包括的テストレポート

実行日時: 1763133456.9474864

## 📊 サマリー

### auto-error-detection-repair.yml
- ✓ PASS: 21
- ✗ FAIL: 1
- ⚠ WARN: 0

### auto-error-detection-repair-v2.yml
- ✓ PASS: 22
- ✗ FAIL: 1
- ⚠ WARN: 0

## 全体統計
- 総PASS: 43
- 総FAIL: 2
- 総WARN: 0

## 詳細結果

### auto-error-detection-repair.yml

#### 構文検証

- ✓ **YAML構文**: YAMLファイルは正常にパースできました

#### 構造検証

- ✓ **必須フィールド 'name'**: 'name' フィールドが存在します
- ✗ **必須フィールド 'on'**: 'on' フィールドが存在しません
- ✓ **必須フィールド 'jobs'**: 'jobs' フィールドが存在します
- ✓ **ジョブ数**: 1個のジョブが定義されています
- ✓ **ジョブ 'error-detection-and-repair' - runs-on**: runs-on: ubuntu-latest
- ✓ **ジョブ 'error-detection-and-repair' - steps**: 8個のステップが定義されています
- ✓ **ジョブ 'error-detection-and-repair' - timeout**: タイムアウト: 30分

#### ロジック検証

- ✓ **ジョブレベル - 条件式**: 正しいイベント名チェックが含まれています
- ✓ **ステップ '修復結果サマリー作成' - 条件式**: 常に実行が含まれています
- ✓ **ステップ '修復ログをアーティファクトとして保存' - 条件式**: 常に実行が含まれています
- ✓ **ステップ '失敗時にIssue作成' - 条件式**: 失敗検出が含まれています
- ✓ **ステップ '成功時にIssueコメント' - 条件式**: Issue番号参照が含まれています
- ✓ **ステップ '成功時にIssueコメント' - 条件式**: 成功検出が含まれています

#### セキュリティ検証

- ✓ **シークレット使用**: シークレットが使用されています
- ✓ **GITHUB_TOKEN使用**: GITHUB_TOKENが適切に使用されています

#### パフォーマンス検証

- ✓ **ジョブ 'error-detection-and-repair' - キャッシュ**: キャッシュが使用されています
- ✓ **総推定実行時間**: 最大30分（タイムアウト合計）
- ✓ **同時実行制御**: グループ: auto-repair-system, cancel-in-progress: False

#### エラーハンドリング検証

- ✓ **ジョブ 'error-detection-and-repair' - always()**: 常に実行されるステップが定義されています
- ✓ **ジョブ 'error-detection-and-repair' - failure()**: 失敗時の処理が定義されています

#### GitHub式検証

- ✓ **式の使用**: 5個の式が使用されています

### auto-error-detection-repair-v2.yml

#### 構文検証

- ✓ **YAML構文**: YAMLファイルは正常にパースできました

#### 構造検証

- ✓ **必須フィールド 'name'**: 'name' フィールドが存在します
- ✗ **必須フィールド 'on'**: 'on' フィールドが存在しません
- ✓ **必須フィールド 'jobs'**: 'jobs' フィールドが存在します
- ✓ **ジョブ数**: 1個のジョブが定義されています
- ✓ **ジョブ 'error-detection-and-repair' - runs-on**: runs-on: ubuntu-latest
- ✓ **ジョブ 'error-detection-and-repair' - steps**: 10個のステップが定義されています
- ✓ **ジョブ 'error-detection-and-repair' - timeout**: タイムアウト: 25分

#### ロジック検証

- ✓ **ジョブレベル - 条件式**: 正しいイベント名チェックが含まれています
- ✓ **エラー継続設定 (エラー検知・修復ループ実行)**: continue-on-error: True
- ✓ **ステップ '修復ステータスを判定' - 条件式**: 常に実行が含まれています
- ✓ **ステップ '修復結果サマリー作成' - 条件式**: 常に実行が含まれています
- ✓ **ステップ '修復ログをアーティファクトとして保存' - 条件式**: 常に実行が含まれています
- ✓ **ステップ '成功時にIssueコメント' - 条件式**: Issue番号参照が含まれています
- ✓ **ステップ '修復結果に基づく終了判定' - 条件式**: 常に実行が含まれています

#### セキュリティ検証

- ✓ **シークレット使用**: シークレットが使用されています
- ✓ **GITHUB_TOKEN使用**: GITHUB_TOKENが適切に使用されています

#### パフォーマンス検証

- ✓ **ジョブ 'error-detection-and-repair' - キャッシュ**: キャッシュが使用されています
- ✓ **総推定実行時間**: 最大25分（タイムアウト合計）
- ✓ **同時実行制御**: グループ: auto-repair-system, cancel-in-progress: False

#### エラーハンドリング検証

- ✓ **ジョブ 'error-detection-and-repair' - always()**: 常に実行されるステップが定義されています
- ✓ **ステップ '依存関係インストール（リトライ付き）' - リトライ**: リトライアクションが使用されています

#### GitHub式検証

- ✓ **式の使用**: 6個の式が使用されています

## 🚨 検出されたエラー

### auto-error-detection-repair.yml - 構造検証
**必須フィールド 'on'**: 'on' フィールドが存在しません

### auto-error-detection-repair-v2.yml - 構造検証
**必須フィールド 'on'**: 'on' フィールドが存在しません

## 🔧 修正推奨事項

- auto-error-detection-repair.yml: 必須フィールドを追加してください
- auto-error-detection-repair-v2.yml: 必須フィールドを追加してください