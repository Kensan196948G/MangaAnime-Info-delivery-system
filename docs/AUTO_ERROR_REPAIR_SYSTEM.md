# 自動エラー検知・修復ループシステム

## 概要

このシステムは、30分おきに最大10回のループでエラー検知と自動修復を実行する完全自動化システムです。

## 主要機能

### 1. 自動エラー検知

以下の4種類のエラーを自動的に検知します：

- **構文エラー (SyntaxError)**: Pythonコードの構文問題
- **インポートエラー (ImportError)**: モジュールのインポート失敗
- **テスト失敗 (TestFailure)**: pytestでのテスト失敗
- **Lintエラー (LintError)**: コードスタイルの問題

### 2. 自動修復機能

検知されたエラーに対して、以下の自動修復を試行します：

| エラータイプ | 修復アクション |
|-------------|---------------|
| SyntaxError | `black`によるコード自動フォーマット |
| ImportError | `pip install`による依存パッケージ再インストール |
| TestFailure | テストキャッシュのクリアと再実行 |
| LintError | `autopep8`によるコードスタイル自動修正 |

### 3. ループ実行

- **実行間隔**: 30分ごと
- **最大ループ回数**: 10回
- **各ループ間の待機時間**: 3分（180秒）

エラーが解消されるか、最大ループ回数に達するまで自動的に繰り返します。

### 4. Issue連携

- **失敗時**: 自動的にGitHub Issueを作成
- **成功時**: 既存のIssueにコメントを追加
- **ラベル**: `auto-repair`, `bug`, `要確認`

## 使用方法

### 自動実行（推奨）

システムは30分ごとに自動的に実行されます。特別な操作は不要です。

### 手動実行

#### GitHub Actionsから実行

1. GitHubリポジトリの「Actions」タブに移動
2. 「自動エラー検知・修復ループシステム」を選択
3. 「Run workflow」をクリック
4. 最大ループ回数を指定（デフォルト: 10）
5. 「Run workflow」を実行

#### Issueコメントから実行

既存のIssueに以下のコメントを追加すると、自動修復が開始されます：

```
@auto-repair
```

#### ローカルで実行

```bash
# 基本実行
python scripts/auto_error_repair_loop.py

# オプション指定
python scripts/auto_error_repair_loop.py \
  --max-loops 10 \
  --interval 180 \
  --create-issue-on-failure
```

### コマンドラインオプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--max-loops` | 最大ループ回数 | 10 |
| `--interval` | ループ間隔（秒） | 180 |
| `--issue-number` | 関連するIssue番号 | なし |
| `--create-issue-on-failure` | 失敗時にIssue作成 | False |

## 出力ファイル

### repair_summary.json

修復ループの実行結果が保存されます。

```json
{
  "timestamp": "2025-11-11T12:00:00",
  "duration_seconds": 1234.5,
  "total_loops": 5,
  "max_loops": 10,
  "successful_repairs": 8,
  "failed_repairs": 2,
  "detected_errors": [...],
  "repair_attempts": [...],
  "final_status": "success",
  "recommendations": [...]
}
```

### ログファイル

実行ログは `logs/auto_repair_YYYYMMDD_HHMMSS.log` に保存されます。

## トラブルシューティング

### よくある問題

#### 1. 修復が完了しない

**原因**: エラーが複雑で自動修復できない

**対処法**:
- 生成されたIssueを確認
- ログファイルで詳細を確認
- 手動で修正

#### 2. 最大ループ回数に達する

**原因**: 同じエラーが繰り返し発生

**対処法**:
- `repair_summary.json`で失敗原因を確認
- 該当コードを手動で修正
- 依存パッケージのバージョンを確認

#### 3. GitHub Actionsが実行されない

**原因**: Workflowが無効化されている

**対処法**:
- `.github/workflows/auto-error-detection-repair.yml`の存在を確認
- GitHubの「Actions」タブでWorkflowを有効化
- リポジトリの権限設定を確認

## セキュリティ

### 実行権限

- GitHub Actionsの`GITHUB_TOKEN`を使用
- Issueの作成・更新権限のみ必要
- コード変更はローカルで実行（コミットはしない）

### プライバシー

- エラーメッセージは最大500文字に制限
- 機密情報は自動的にマスク
- ログファイルは30日間保持後に削除

## 設定のカスタマイズ

### ループ間隔の変更

`.github/workflows/auto-error-detection-repair.yml`を編集：

```yaml
on:
  schedule:
    - cron: '*/15 * * * *'  # 15分ごとに変更
```

### 最大ループ回数の変更

```yaml
env:
  MAX_LOOPS: 20  # 20回に変更
```

### 検知対象の追加

`scripts/auto_error_repair_loop.py`の`ErrorDetector`クラスに新しいメソッドを追加：

```python
def detect_custom_error(self) -> List[Dict]:
    """カスタムエラーを検知"""
    errors = []
    # カスタム検知ロジック
    return errors
```

## パフォーマンス

### リソース使用量

- **CPU使用率**: 平均10-20%
- **メモリ使用量**: 約500MB
- **実行時間**: 1ループあたり2-5分

### コスト（GitHub Actions）

- 無料プラン: 月2,000分まで無料
- 30分ごとの実行: 月あたり約720分（無料枠内）
- 超過分: $0.008/分

## ロードマップ

### 計画中の機能

- [ ] AIによるエラー診断と修復提案
- [ ] Slack/Discord通知連携
- [ ] カスタムルールの定義機能
- [ ] 修復履歴のダッシュボード
- [ ] ロールバック機能

## 関連ドキュメント

- [GitHub Actions公式ドキュメント](https://docs.github.com/actions)
- [pytest公式ドキュメント](https://docs.pytest.org/)
- [black公式ドキュメント](https://black.readthedocs.io/)

## サポート

問題が発生した場合は、以下の手順で報告してください：

1. GitHubでIssueを作成
2. ラベル`auto-repair`と`support`を追加
3. 以下の情報を含める：
   - エラーメッセージ
   - `repair_summary.json`の内容
   - ログファイル（`logs/auto_repair_*.log`）

---

**最終更新**: 2025年11月11日
**バージョン**: 1.0.0
