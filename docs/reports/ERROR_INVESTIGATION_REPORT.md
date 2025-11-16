# エラー調査詳細レポート

**調査日時**: 2025-11-15
**調査対象**: BookWalker RSSエラー および JavaScript実行状況エラー

---

## 1. BookWalker RSSエラー

### 1.1 エラー内容
- **エラータイプ**: HTTP 404 Not Found / Timeout
- **問題のURL**: 複数の異なるURLが設定されている

### 1.2 現在の問題点

#### 設定ファイル内の異なるURL:

| 場所 | URL | ステータス |
|-----|-----|----------|
| `config/config.template.json` | `https://bookwalker.jp/rss/` | 403 Forbidden |
| `modules/manga_rss_enhanced.py` | `https://bookwalker.jp/series/rss/` | 404 Not Found |
| `scripts/integration_test.py` | `https://bookwalker.jp/rss/` | 403 Forbidden |
| エラーログ | `https://bookwalker.jp/rss/new-releases.xml` | 404 Not Found |

#### 正しいURL:
```
https://bookwalker.jp/rss/books.xml
```
- **ステータス**: HTTP 200 OK
- **Content-Type**: text/xml
- **Content-Length**: 482,392 bytes
- **Last-Modified**: 2025-11-14 16:10:20
- **確認方法**: BookWalkerのHTMLソースから発見

### 1.3 テスト結果

```bash
# 成功
curl -I https://bookwalker.jp/rss/books.xml
# HTTP/2 200 OK

# 失敗例
curl -I https://bookwalker.jp/series/rss/
# HTTP/2 404 Not Found

curl -I https://bookwalker.jp/rss/
# HTTP/2 403 Forbidden

curl -I https://bookwalker.jp/rss/new-releases.xml
# HTTP/2 404 Not Found
```

### 1.4 修正方法

以下のファイルのBookWalker URL を **`https://bookwalker.jp/rss/books.xml`** に変更する必要があります：

#### 1. `modules/manga_rss_enhanced.py`
```python
# 変更前
"bookwalker": MangaRSSFeedConfig(
    name="BOOK☆WALKER - マンガ新刊",
    url="https://bookwalker.jp/series/rss/",  # ← 404エラー
    category="manga",
    enabled=True,
    priority="high",
    timeout=20,
    parser_type="standard",
),

# 変更後
"bookwalker": MangaRSSFeedConfig(
    name="BOOK☆WALKER - マンガ新刊",
    url="https://bookwalker.jp/rss/books.xml",  # ← 正しいURL
    category="manga",
    enabled=True,
    priority="high",
    timeout=20,
    parser_type="standard",
),
```

#### 2. `config/config.template.json`
```json
{
  "name": "BookWalker",
  "url": "https://bookwalker.jp/rss/books.xml",
  "category": "manga",
  "enabled": true,
  "priority": "high"
}
```

#### 3. `scripts/integration_test.py`
```python
"BookWalker": "https://bookwalker.jp/rss/books.xml"
```

#### 4. `scripts/performance_validation.py`
```python
"https://bookwalker.jp/rss/books.xml"
```

#### 5. `scripts/operational_monitoring.py`
```python
("BookWalker RSS", "https://bookwalker.jp/rss/books.xml", "GET")
```

### 1.5 追加の推奨事項

1. **タイムアウト設定の調整**
   - 現在: 20秒
   - BookWalkerのレスポンスは約4-5秒
   - 推奨: 15秒で十分

2. **User-Agent設定の確認**
   - 現在: `MangaAnimeNotifier/1.0`
   - 推奨: より詳細なUser-Agent
   ```python
   "User-Agent": "MangaAnimeNotifier/1.0 (Python; RSS Reader)"
   ```

3. **リトライロジックの強化**
   ```python
   retry_count = 3
   retry_delay = 2  # 秒
   ```

---

## 2. JavaScript実行状況エラー

### 2.1 エラー内容
```
Cannot read properties of undefined (reading 'status')
```

### 2.2 根本原因

#### APIレスポンス構造 (`app/web_app.py`)
```json
{
  "email": {
    "lastExecuted": "...",
    "status": "success",
    "todayStats": {...}
  },
  "calendar": {
    "lastExecuted": "...",
    "status": "success",
    "todayStats": {...}
  },
  "overall": {...}
}
```

#### JavaScriptの期待構造 (`static/js/notification-status.js`)
```javascript
// 期待しているキー名
const notification = data.notification;  // ← undefined!
const calendar = data.calendar;          // ← これは存在する

// 実際に返されているキー名
// data.email (notification ではない)
// data.calendar (これは一致)
```

### 2.3 問題のコード箇所

**ファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/static/js/notification-status.js`

#### 現在のコード（エラー発生）:
```javascript
function updateNotificationStatus(data) {
    const container = document.getElementById('notification-status-container');
    if (!container) return;

    const notification = data.notification;  // ← undefined!
    const statusClass = notification.status === 'success' ? 'success' :
                      notification.status === 'error' ? 'error' : 'pending';
    // エラー: Cannot read properties of undefined (reading 'status')
}
```

### 2.4 修正方法

#### オプション1: JavaScript側を修正（推奨）

APIレスポンスに合わせてJavaScriptを修正する方が、APIの後方互換性が保たれます。

```javascript
function updateNotificationStatus(data) {
    const container = document.getElementById('notification-status-container');
    if (!container) return;

    // 修正: data.email を使用
    const notification = data.email || data.notification;

    // エラーハンドリング追加
    if (!notification) {
        console.error('通知データが見つかりません:', data);
        showError('通知データの取得に失敗しました');
        return;
    }

    const statusClass = notification.status === 'success' ? 'success' :
                      notification.status === 'error' ? 'error' : 'pending';
    // 以下同じ...
}

function updateCalendarStatus(data) {
    const container = document.getElementById('calendar-status-container');
    if (!container) return;

    // calendarキーは一致しているため変更不要
    const calendar = data.calendar;

    // エラーハンドリング追加
    if (!calendar) {
        console.error('カレンダーデータが見つかりません:', data);
        showError('カレンダーデータの取得に失敗しました');
        return;
    }

    // 以下同じ...
}
```

#### オプション2: API側を修正（影響範囲大）

APIレスポンスを変更してJavaScriptの期待に合わせる。

**ファイル**: `app/web_app.py`

```python
# 変更前
response = {
    'email': {...},
    'calendar': {...},
    'overall': {...}
}

# 変更後（互換性維持）
response = {
    'notification': {...},  # emailから名前変更
    'email': {...},         # 後方互換性のため残す
    'calendar': {...},
    'overall': {...}
}
```

### 2.5 推奨される修正（最小影響）

**JavaScript側のみを修正** - エラーハンドリングを強化

```javascript
/**
 * APIからデータを取得
 */
async function fetchStatus() {
    try {
        // 更新中インジケーター表示
        const indicators = document.querySelectorAll('.update-indicator');
        indicators.forEach(ind => {
            ind.classList.add('updating');
        });

        const response = await fetch(CONFIG.apiEndpoint);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // データ構造の検証
        if (!data) {
            throw new Error('APIレスポンスが空です');
        }

        // email/notification の互換性チェック
        if (!data.email && !data.notification) {
            throw new Error('通知データが見つかりません');
        }

        if (!data.calendar) {
            throw new Error('カレンダーデータが見つかりません');
        }

        lastData = data;

        // データ更新（互換性を持たせる）
        updateNotificationStatus({
            notification: data.email || data.notification,
            calendar: data.calendar
        });

        updateCalendarStatus({
            calendar: data.calendar
        });

        // 更新中インジケーター非表示
        setTimeout(() => {
            indicators.forEach(ind => {
                ind.classList.remove('updating');
            });
        }, 500);

    } catch (error) {
        console.error('ステータス取得エラー:', error);
        showError('ステータスの取得に失敗しました: ' + error.message);
    }
}
```

---

## 3. 代替案の提示

### 3.1 BookWalker RSS代替ソース

BookWalkerのRSSが不安定な場合の代替案：

1. **Amazon Kindle RSS**
   - URL: `https://www.amazon.co.jp/gp/rss/bestsellers/digital-text/` (要確認)

2. **楽天Kobo RSS**
   - URL: `https://books.rakuten.co.jp/rss/` (要確認)

3. **直接API利用**
   - BookWalkerの非公式API（存在する場合）
   - スクレイピング（最終手段、利用規約要確認）

### 3.2 エラー監視の強化

```python
# modules/manga_rss.py に追加
class FeedHealthMonitor:
    """RSS フィード健全性監視"""

    def __init__(self):
        self.health_scores = {}

    def check_feed_health(self, url: str) -> Dict[str, Any]:
        """フィードの健全性をチェック"""
        try:
            start = time.time()
            response = requests.head(url, timeout=5)
            response_time = time.time() - start

            return {
                'url': url,
                'status_code': response.status_code,
                'response_time': response_time,
                'healthy': response.status_code == 200,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'healthy': False,
                'timestamp': datetime.now().isoformat()
            }
```

---

## 4. テスト計画

### 4.1 BookWalker RSS修正後のテスト

```bash
# 1. URL接続テスト
curl -I https://bookwalker.jp/rss/books.xml

# 2. RSS取得テスト
curl -s https://bookwalker.jp/rss/books.xml | head -50

# 3. Python統合テスト
python3 -c "
import feedparser
feed = feedparser.parse('https://bookwalker.jp/rss/books.xml')
print(f'Entries: {len(feed.entries)}')
print(f'First title: {feed.entries[0].title if feed.entries else \"None\"}')
"

# 4. アプリケーションテスト
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
python3 -m pytest tests/ -k "bookwalker" -v
```

### 4.2 JavaScript修正後のテスト

```javascript
// ブラウザコンソールでテスト
// 1. APIレスポンス確認
fetch('/api/notification-status')
  .then(r => r.json())
  .then(data => {
    console.log('API Response:', data);
    console.log('Has email?', !!data.email);
    console.log('Has notification?', !!data.notification);
    console.log('Has calendar?', !!data.calendar);
  });

// 2. 手動リフレッシュ
NotificationStatus.refresh();

// 3. データ取得確認
console.log('Last data:', NotificationStatus.getLastData());
```

---

## 5. 実装優先順位

### 高優先度（即座に修正）
1. JavaScript エラーハンドリング追加（`static/js/notification-status.js`）
2. BookWalker URL修正（`modules/manga_rss_enhanced.py`）

### 中優先度（次回更新時）
3. 設定ファイルのURL統一（`config/*.json`, `scripts/*.py`）
4. タイムアウト設定の最適化
5. User-Agent文字列の改善

### 低優先度（将来的な改善）
6. フィード健全性監視機能の実装
7. 代替RSSソースの追加
8. エラー通知機能の強化

---

## 6. 修正ファイルリスト

### 必須修正
- [ ] `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/static/js/notification-status.js`
- [ ] `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/modules/manga_rss_enhanced.py`

### 推奨修正
- [ ] `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config/config.template.json`
- [ ] `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/scripts/integration_test.py`
- [ ] `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/scripts/performance_validation.py`
- [ ] `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/scripts/operational_monitoring.py`

---

## 7. まとめ

### BookWalker RSSエラー
- **原因**: 404 Not Found（URLが間違っている）
- **正しいURL**: `https://bookwalker.jp/rss/books.xml`
- **修正箇所**: 6ファイル
- **影響範囲**: マンガRSS収集機能

### JavaScriptエラー
- **原因**: API レスポンスキー名の不一致（`email` vs `notification`）
- **発生場所**: `static/js/notification-status.js`
- **修正方法**: エラーハンドリング追加 + 互換性対応
- **影響範囲**: 通知実行状況UI表示

### 推奨アクション
1. JavaScript修正（即座）
2. BookWalker URL修正（即座）
3. 設定ファイル統一（次回更新）
4. テスト実行（修正後）

---

**調査完了日時**: 2025-11-15
**次回アクション**: 修正実装とテスト実行
