# 🚀 クイックスタートガイド - 並列開発成果の活用

## 📦 今回の改善で追加された機能

### 1. 新しいバックエンドモジュール

#### インストール
```bash
# 新しい依存パッケージをインストール
pip install -r requirements-backend-enhanced.txt
```

#### 使い方

**しょぼいカレンダーAPI**:
```python
from modules.anime_syoboi import fetch_syoboi_programs_sync

# 日本国内のTV放送アニメ情報を取得
programs = fetch_syoboi_programs_sync()
print(f"取得した番組数: {len(programs)}")
```

**拡張マンガRSS**:
```python
from modules.manga_rss_enhanced import EnhancedMangaRSSCollector

collector = EnhancedMangaRSSCollector()
manga_releases = collector.collect_all_feeds()
print(f"マンガリリース数: {len(manga_releases)}")
```

**ストリーミングプラットフォーム**:
```python
from modules.streaming_platform_enhanced import EnhancedStreamingPlatformCollector

collector = EnhancedStreamingPlatformCollector()
streaming_info = collector.fetch_anilist_streaming()
```

**重複検出（強化版）**:
```python
from modules.data_normalizer_enhanced import EnhancedDataNormalizer

normalizer = EnhancedDataNormalizer()
duplicates = normalizer.find_duplicates(works, method='hybrid')
```

**フィルタリング（強化版）**:
```python
from modules.filter_logic_enhanced import EnhancedFilterLogic

filter_logic = EnhancedFilterLogic()
filtered = filter_logic.apply_filters(releases)
```

---

### 2. 新しいUI機能

#### 自動的に有効化
`templates/base.html`が更新されているため、Web UIを起動すれば自動的に新機能が使えます:

```bash
python web_app.py
```

#### 使える新機能

**通知システム**:
```javascript
// ブラウザコンソールで試せます
window.notificationManager.show('テストメッセージ', 'success');
window.notificationManager.show('警告メッセージ', 'warning');
window.notificationManager.show('エラーメッセージ', 'error');
```

**ローディング表示**:
```javascript
const loaderId = window.loadingManager.show('.card', 'データを読み込み中...');
// 処理実行...
window.loadingManager.hide(loaderId);
```

**キーボードショートカット**:
- `Ctrl+/`: ヘルプ表示
- `Ctrl+S`: 保存（対応フォーム）
- `Escape`: モーダルを閉じる

---

### 3. 改善されたテスト

#### 新しいテストを実行
```bash
# データベーステスト（100%合格）
pytest tests/test_database_fixed.py -v

# バックエンド統合テスト
pytest tests/test_enhanced_backend_integration.py -v

# カバレッジ付きで全テスト実行
pytest --cov=modules --cov-report=html
```

---

### 4. 新しいCI/CD

#### GitHub Actionsで自動テスト
`.github/workflows/ci-pipeline-improved.yml`が追加されています。

次回のgit pushで自動的に以下が実行されます:
- Python 3.10, 3.11, 3.12, 3.13でテスト
- Ubuntu + Windowsでテスト
- コード品質チェック（Black, Flake8, Bandit）
- カバレッジ測定（60%閾値）

---

## 🎯 最優先で実施すべきこと

### 1. RSS Feed設定（4時間）🔴

現在、マンガ情報収集が0件です。以下のファイルを編集してください:

#### `config.json`に追加:
```json
{
  "manga_rss_feeds": [
    {
      "name": "マガジンポケット",
      "url": "https://pocket.shonenmagazine.com/rss",
      "enabled": true
    },
    {
      "name": "BookWalker",
      "url": "https://bookwalker.jp/series/rss",
      "enabled": true
    },
    {
      "name": "楽天Kobo",
      "url": "https://books.rakuten.co.jp/rss/comics/",
      "enabled": true
    },
    {
      "name": "ジャンプBOOKストア",
      "url": "https://jumpbookstore.com/rss",
      "enabled": true
    },
    {
      "name": "マンガUP!",
      "url": "https://magazine.jp.square-enix.com/mangaup/rss",
      "enabled": true
    },
    {
      "name": "ComicWalker",
      "url": "https://comic-walker.com/rss",
      "enabled": true
    }
  ]
}
```

#### 実行:
```bash
python release_notifier.py
```

---

### 2. セキュリティ強化（4時間）🔴

#### トークンファイルのパーミッション設定:
```bash
# Linux/Mac
chmod 600 token.json
chmod 600 calendar_token.json

# Windows (PowerShell)
icacls token.json /inheritance:r /grant:r "%USERNAME%:F"
icacls calendar_token.json /inheritance:r /grant:r "%USERNAME%:F"
```

---

### 3. コード重複の解消（2時間）🔴

QAエージェントが特定した重複コードを修正:

#### `modules/manga_rss.py`と`modules/manga_rss_enhanced.py`を統合
```bash
# manga_rss_enhanced.pyを使用する場合
# release_notifier.pyのインポートを更新
# from modules.manga_rss import ...
# ↓
# from modules.manga_rss_enhanced import ...
```

---

## 📊 確認コマンド

### システムの状態確認
```bash
# データベース統計
python -c "from modules.db import get_db_stats; print(get_db_stats())"

# テストカバレッジ確認
pytest --cov=modules --cov-report=term

# コード品質チェック
black --check .
flake8 modules/ tests/
bandit -r modules/
```

---

## 📚 詳細ドキュメント

すべての詳細情報は以下のレポートを参照してください:

| レポート | 内容 |
|---------|------|
| `INTEGRATION_REPORT.md` | 全体統合レポート（本ファイル） |
| `CTO_COMPREHENSIVE_ARCHITECTURE_REPORT.md` | アーキテクチャ詳細 |
| `docs/UI_UX_IMPROVEMENT_REPORT.md` | UI改善詳細 |
| `docs/BACKEND_DEVELOPMENT_REPORT.md` | バックエンド詳細 |
| `CODE_REVIEW_REPORT.md` | コードレビュー詳細 |
| `SECURITY_AUDIT_REPORT.md` | セキュリティ監査 |
| `TEST_REPORT.md` | テスト詳細分析 |

---

## ❓ よくある質問

### Q1: 既存のコードは動きますか?
**A**: はい。すべての新機能は既存コードとの互換性を維持しています。

### Q2: すぐに本番環境で使えますか?
**A**: HIGH優先度タスク（RSS設定、セキュリティ強化）を完了すれば使用可能です。

### Q3: どのモジュールを優先的に使うべきですか?
**A**: 以下の順番で移行してください:
1. `modules/manga_rss_enhanced.py` (マンガ収集)
2. `modules/anime_syoboi.py` (日本国内TV放送)
3. `modules/data_normalizer_enhanced.py` (重複検出)
4. `modules/filter_logic_enhanced.py` (フィルタリング)

### Q4: テストは全部通っていますか?
**A**: 新規テストは100%合格していますが、既存テストの一部（23.2%）に失敗があります。`TEST_REPORT.md`を参照してください。

---

## 🎉 次のステップ

1. ✅ このガイドを読む
2. 🔴 RSS Feed設定を追加
3. 🔴 セキュリティ強化を実施
4. 🟡 テストを実行して確認
5. 🟡 本番環境にデプロイ

---

**作成日**: 2025年11月11日
**バージョン**: 1.0.0
