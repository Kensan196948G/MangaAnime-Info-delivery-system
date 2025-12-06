# コードスタイルと規約

## 命名規則
- **クラス名**: PascalCase（例: `DatabaseManager`, `AniListClient`）
- **関数/メソッド名**: snake_case（例: `get_connection`, `create_work`）
- **変数名**: snake_case（例: `db_path`, `max_connections`）
- **プライベートメソッド**: 先頭にアンダースコア（例: `_create_connection`）
- **定数**: UPPER_SNAKE_CASE（例: `NG_KEYWORDS`）

## 型ヒント
- 全ての関数/メソッドで型ヒントを使用
- `Optional[T]`、`List[T]`、`Dict[K, V]` を使用
- 戻り値の型も必ず指定

```python
def get_work_by_title(
    self, title: str, work_type: Optional[str] = None
) -> Optional[Dict[str, Any]]:
```

## Docstrings
- Google スタイルのdocstringsを使用
- Args、Returns、Raises を記載

```python
def create_work(
    self,
    title: str,
    work_type: str,
    title_kana: Optional[str] = None,
) -> int:
    """
    Create new work entry.

    Args:
        title: Work title (required)
        work_type: 'anime' or 'manga' (required)
        title_kana: Katakana reading (optional)

    Returns:
        work_id of created work

    Raises:
        ValueError: If work_type is invalid
    """
```

## インポート順序
1. 標準ライブラリ
2. サードパーティライブラリ
3. ローカルモジュール

## エラーハンドリング
- 具体的な例外クラスを使用
- ロギングでエラー内容を記録
- コンテキストマネージャー（`with`）を活用

## データベース操作
- コンテキストマネージャー（`get_connection`）を使用
- トランザクションは `get_transaction` を使用
- プリペアドステートメント（`?`プレースホルダー）を使用

## ログ出力
- `logging` モジュールを使用
- 適切なログレベル（DEBUG, INFO, WARNING, ERROR）を選択
