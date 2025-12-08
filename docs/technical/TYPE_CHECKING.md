# Python型チェックガイド

## 概要

このプロジェクトでは、Pythonの型ヒント（Type Hints）とmypyによる静的型チェックを導入しています。

## 型ヒント付きモジュール

以下のモジュールに型ヒントが追加されています：

### コアモジュール
- `modules/types_helper.py` - 型定義ヘルパー
- `modules/db_typed.py` - データベース操作
- `modules/config_typed.py` - 設定管理

### 外部連携モジュール
- `modules/mailer_typed.py` - Gmail送信
- `modules/calendar_typed.py` - Googleカレンダー連携
- `modules/anime_anilist_typed.py` - AniList API連携
- `modules/manga_rss_typed.py` - RSS収集

### ロジックモジュール
- `modules/filter_logic_typed.py` - フィルタリング

## セットアップ

### 必要なパッケージのインストール

```bash
# 開発用依存パッケージをインストール
pip install -e ".[dev]"

# または個別にインストール
pip install mypy types-requests
```

## 型チェックの実行

### 基本的な使い方

```bash
# 単一ファイルのチェック
mypy modules/db_typed.py

# 複数ファイルのチェック
mypy modules/db_typed.py modules/config_typed.py

# モジュール全体をチェック
mypy modules/
```

### 便利なスクリプト

#### 1. check_types.sh（シェルスクリプト）

```bash
# すべての型ヒント付きモジュールをチェック
bash scripts/check_types.sh
```

#### 2. generate_type_report.py（詳細レポート）

```bash
# 詳細なレポートを生成
python scripts/generate_type_report.py
```

レポートは以下の場所に保存されます：
- テキスト形式: `docs/reports/type_check_report.txt`
- JSON形式: `docs/reports/type_check_report.json`

## 型チェック設定

### mypy.ini

プロジェクトルートの`mypy.ini`に設定があります：

```ini
[mypy]
python_version = 3.10
warn_return_any = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
```

### pyproject.toml

`pyproject.toml`でも設定可能です（mypy.iniよりも優先度は低い）：

```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
disallow_untyped_defs = true
```

## 型ヒントの書き方

### 基本的な型

```python
from typing import List, Dict, Any, Optional

def greet(name: str) -> str:
    return f"Hello, {name}!"

def process_items(items: List[str]) -> Dict[str, int]:
    return {item: len(item) for item in items}

def find_item(item_id: int) -> Optional[str]:
    # Optionalは値がNoneの可能性がある場合に使用
    return None
```

### 複雑な型

```python
from typing import Union, Tuple, Callable

# Union: 複数の型のいずれか
def parse_value(value: Union[str, int, float]) -> str:
    return str(value)

# Tuple: タプル型
def get_coordinates() -> Tuple[float, float]:
    return (35.6762, 139.6503)

# Callable: 関数型
def apply_operation(
    value: int,
    operation: Callable[[int], int]
) -> int:
    return operation(value)
```

### TypedDict（辞書の型定義）

```python
from typing import TypedDict, Optional

class UserDict(TypedDict, total=False):
    id: int
    name: str
    email: Optional[str]

def get_user() -> UserDict:
    return {
        'id': 1,
        'name': 'Alice',
        'email': 'alice@example.com'
    }
```

### クラスの型ヒント

```python
class DataProcessor:
    def __init__(self, data: List[str]) -> None:
        self.data = data
        self.count: int = len(data)

    def process(self) -> Dict[str, int]:
        return {item: len(item) for item in self.data}

    @property
    def total_length(self) -> int:
        return sum(len(item) for item in self.data)
```

## よくあるエラーと対処法

### 1. Import エラー

**エラー:**
```
error: Cannot find implementation or library stub for module named 'requests'
```

**対処法:**
```bash
# 型スタブをインストール
pip install types-requests
```

または`mypy.ini`で無視：
```ini
[mypy-requests.*]
ignore_missing_imports = True
```

### 2. 型の不一致

**エラー:**
```
error: Argument 1 has incompatible type "str"; expected "int"
```

**対処法:**
```python
# 型変換を行う
value: str = "123"
number: int = int(value)

# または型アノテーションを修正
def process(value: Union[str, int]) -> None:
    pass
```

### 3. None型エラー

**エラー:**
```
error: Item "None" of "Optional[str]" has no attribute "upper"
```

**対処法:**
```python
def process(value: Optional[str]) -> str:
    # Noneチェックを追加
    if value is None:
        return ""
    return value.upper()
```

## CI/CDへの統合

### GitHub Actions

`.github/workflows/type-check.yml`:

```yaml
name: Type Check

on: [push, pull_request]

jobs:
  mypy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run mypy
        run: |
          mypy modules/
```

## 段階的な導入

### Phase 1: 基本モジュール（完了）
- ✓ db_typed.py
- ✓ config_typed.py
- ✓ types_helper.py

### Phase 2: 外部連携モジュール（完了）
- ✓ mailer_typed.py
- ✓ calendar_typed.py
- ✓ anime_anilist_typed.py
- ✓ manga_rss_typed.py

### Phase 3: ロジックモジュール（完了）
- ✓ filter_logic_typed.py

### Phase 4: アプリケーション層（今後）
- app/web_app.py
- app/cli.py

## 参考リンク

- [Python Type Hints公式ドキュメント](https://docs.python.org/ja/3/library/typing.html)
- [mypy公式ドキュメント](https://mypy.readthedocs.io/)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [PEP 585 - Type Hinting Generics In Standard Collections](https://www.python.org/dev/peps/pep-0585/)

## まとめ

型ヒントとmypyの導入により、以下のメリットがあります：

1. **バグの早期発見**: コンパイル前に型エラーを検出
2. **コードの可読性向上**: 関数の入出力が明確になる
3. **IDE支援の向上**: 自動補完やリファクタリングが正確になる
4. **ドキュメント化**: 型情報がコードの仕様書になる

定期的に型チェックを実行し、型エラーを修正していくことをおすすめします。
