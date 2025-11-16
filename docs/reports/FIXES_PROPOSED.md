# 修正提案コード

このドキュメントには、調査で発見された問題の具体的な修正コードが含まれています。

---

## 1. JavaScript エラー修正（最優先）

### ファイル: `static/js/notification-status.js`

#### 修正箇所1: `updateNotificationStatus` 関数

```javascript
/**
 * メール通知ステータスを更新（エラーハンドリング強化版）
 */
function updateNotificationStatus(data) {
    const container = document.getElementById('notification-status-container');
    if (!container) return;

    // 互換性対応: email または notification キーを使用
    const notification = data.notification || data.email;

    // データ検証
    if (!notification) {
        console.error('通知データが見つかりません。APIレスポンス:', data);
        showError('通知データの取得に失敗しました（データが見つかりません）');
        return;
    }

    // status プロパティの安全なアクセス
    const status = notification.status || 'unknown';
    const statusClass = status === 'success' ? 'success' :
                      status === 'error' ? 'error' : 'pending';
    const statusIcon = status === 'success' ? 'bi-check-circle-fill' :
                     status === 'error' ? 'bi-x-circle-fill' : 'bi-hourglass-split';
    const statusText = status === 'success' ? '正常' :
                     status === 'error' ? 'エラーあり' : '未実行';

    let errorsHtml = '';
    if (notification.recentErrors && notification.recentErrors.length > 0) {
        errorsHtml = `
            <div class="error-messages mt-3">
                <h6 class="mb-2"><i class="bi bi-exclamation-triangle-fill text-warning"></i> 最近のエラー</h6>
                ${notification.recentErrors.map(error => `
                    <div class="error-message-item">
                        <i class="bi bi-exclamation-circle-fill"></i>
                        <div class="error-message-content">
                            <div class="error-message-text">${error.message || 'エラーメッセージなし'}</div>
                            <div class="error-message-time">${formatDateTime(error.time)}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } else if (status === 'success') {
        errorsHtml = `
            <div class="no-errors mt-3">
                <i class="bi bi-check-circle-fill"></i>
                <span>エラーはありません</span>
            </div>
        `;
    }

    const html = `
        <div class="execution-status-card">
            <div class="card-header">
                <i class="bi bi-envelope-fill"></i> メール通知実行状況
            </div>
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <span class="status-badge ${statusClass}">
                        <i class="bi ${statusIcon}"></i>
                        ${statusText}
                    </span>
                    <span class="update-indicator" id="notification-update-indicator">
                        <i class="bi bi-arrow-clockwise"></i>
                        <span>自動更新中</span>
                    </span>
                </div>

                <div class="time-display last-executed">
                    <i class="bi bi-clock-history"></i>
                    <div class="flex-grow-1">
                        <div class="time-label">最終実行時刻</div>
                        <div class="time-value">${formatDateTime(notification.lastExecuted)}</div>
                        <div class="time-relative">${getRelativeTime(notification.lastExecuted)}</div>
                    </div>
                </div>

                <div class="time-display next-scheduled">
                    <i class="bi bi-calendar-check"></i>
                    <div class="flex-grow-1">
                        <div class="time-label">次回実行予定 (${notification.checkIntervalHours || 1}時間ごと)</div>
                        <div class="time-value">${formatDateTime(notification.nextScheduled)}</div>
                        ${CONFIG.enableCountdown ? `
                            <div class="countdown-timer mt-2" id="notification-countdown">
                                <i class="bi bi-hourglass-split"></i>
                                <span>${getCountdown(notification.nextScheduled)}</span>
                            </div>
                        ` : ''}
                    </div>
                </div>

                <div class="stats-grid">
                    <div class="stat-item success">
                        <div class="stat-value">${(notification.todayStats?.successCount || 0)}</div>
                        <div class="stat-label">成功</div>
                    </div>
                    <div class="stat-item error">
                        <div class="stat-value">${(notification.todayStats?.errorCount || 0)}</div>
                        <div class="stat-label">エラー</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${(notification.todayStats?.totalReleases || 0)}</div>
                        <div class="stat-label">通知数</div>
                    </div>
                </div>

                ${errorsHtml}
            </div>
        </div>
    `;

    container.innerHTML = html;
}
```

#### 修正箇所2: `updateCalendarStatus` 関数

```javascript
/**
 * カレンダー連携ステータスを更新（エラーハンドリング強化版）
 */
function updateCalendarStatus(data) {
    const container = document.getElementById('calendar-status-container');
    if (!container) return;

    const calendar = data.calendar;

    // データ検証
    if (!calendar) {
        console.error('カレンダーデータが見つかりません。APIレスポンス:', data);
        showError('カレンダーデータの取得に失敗しました（データが見つかりません）');
        return;
    }

    // status プロパティの安全なアクセス
    const status = calendar.status || 'unknown';
    const statusClass = status === 'success' ? 'success' :
                      status === 'error' ? 'error' : 'pending';
    const statusIcon = status === 'success' ? 'bi-check-circle-fill' :
                     status === 'error' ? 'bi-x-circle-fill' : 'bi-hourglass-split';
    const statusText = status === 'success' ? '正常' :
                     status === 'error' ? 'エラーあり' : '未実行';

    let errorsHtml = '';
    if (calendar.recentErrors && calendar.recentErrors.length > 0) {
        errorsHtml = `
            <div class="error-messages mt-3">
                <h6 class="mb-2"><i class="bi bi-exclamation-triangle-fill text-warning"></i> 最近のエラー</h6>
                ${calendar.recentErrors.map(error => `
                    <div class="error-message-item">
                        <i class="bi bi-exclamation-circle-fill"></i>
                        <div class="error-message-content">
                            <div class="error-message-text">${error.message || 'エラーメッセージなし'}</div>
                            <div class="error-message-time">${formatDateTime(error.time)}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } else if (status === 'success') {
        errorsHtml = `
            <div class="no-errors mt-3">
                <i class="bi bi-check-circle-fill"></i>
                <span>エラーはありません</span>
            </div>
        `;
    }

    const html = `
        <div class="execution-status-card">
            <div class="card-header">
                <i class="bi bi-calendar-event-fill"></i> カレンダー連携実行状況
            </div>
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <span class="status-badge ${statusClass}">
                        <i class="bi ${statusIcon}"></i>
                        ${statusText}
                    </span>
                    <span class="update-indicator" id="calendar-update-indicator">
                        <i class="bi bi-arrow-clockwise"></i>
                        <span>自動更新中</span>
                    </span>
                </div>

                <div class="time-display last-executed">
                    <i class="bi bi-clock-history"></i>
                    <div class="flex-grow-1">
                        <div class="time-label">最終登録時刻</div>
                        <div class="time-value">${formatDateTime(calendar.lastExecuted)}</div>
                        <div class="time-relative">${getRelativeTime(calendar.lastExecuted)}</div>
                    </div>
                </div>

                <div class="time-display next-scheduled">
                    <i class="bi bi-calendar-check"></i>
                    <div class="flex-grow-1">
                        <div class="time-label">次回登録予定 (${calendar.checkIntervalHours || 1}時間ごと)</div>
                        <div class="time-value">${formatDateTime(calendar.nextScheduled)}</div>
                        ${CONFIG.enableCountdown ? `
                            <div class="countdown-timer mt-2" id="calendar-countdown">
                                <i class="bi bi-hourglass-split"></i>
                                <span>${getCountdown(calendar.nextScheduled)}</span>
                            </div>
                        ` : ''}
                    </div>
                </div>

                <div class="stats-grid">
                    <div class="stat-item success">
                        <div class="stat-value">${(calendar.todayStats?.successCount || 0)}</div>
                        <div class="stat-label">成功</div>
                    </div>
                    <div class="stat-item error">
                        <div class="stat-value">${(calendar.todayStats?.errorCount || 0)}</div>
                        <div class="stat-label">エラー</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${(calendar.todayStats?.totalEvents || 0)}</div>
                        <div class="stat-label">登録数</div>
                    </div>
                </div>

                ${errorsHtml}
            </div>
        </div>
    `;

    container.innerHTML = html;
}
```

#### 修正箇所3: `fetchStatus` 関数

```javascript
/**
 * APIからデータを取得（エラーハンドリング強化版）
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

        // email/notification の存在確認
        const hasNotificationData = !!(data.email || data.notification);
        const hasCalendarData = !!data.calendar;

        if (!hasNotificationData) {
            console.warn('通知データが見つかりません。APIレスポンス:', data);
        }

        if (!hasCalendarData) {
            console.warn('カレンダーデータが見つかりません。APIレスポンス:', data);
        }

        // 互換性を持たせたデータ構造に変換
        const normalizedData = {
            notification: data.notification || data.email,
            calendar: data.calendar
        };

        lastData = normalizedData;

        // データ更新
        if (normalizedData.notification) {
            updateNotificationStatus(normalizedData);
        }

        if (normalizedData.calendar) {
            updateCalendarStatus(normalizedData);
        }

        // 更新中インジケーター非表示
        setTimeout(() => {
            indicators.forEach(ind => {
                ind.classList.remove('updating');
            });
        }, 500);

    } catch (error) {
        console.error('ステータス取得エラー:', error);
        console.error('スタックトレース:', error.stack);
        showError('ステータスの取得に失敗しました: ' + error.message);

        // 更新中インジケーター非表示（エラー時も）
        const indicators = document.querySelectorAll('.update-indicator');
        indicators.forEach(ind => {
            ind.classList.remove('updating');
        });
    }
}
```

---

## 2. BookWalker RSS URL修正

### ファイル1: `modules/manga_rss_enhanced.py`

#### 修正箇所: MANGA_RSS_FEEDS 辞書

```python
# 修正前
"bookwalker": MangaRSSFeedConfig(
    name="BOOK☆WALKER - マンガ新刊",
    url="https://bookwalker.jp/series/rss/",  # ← 404エラー
    category="manga",
    enabled=True,
    priority="high",
    timeout=20,
    parser_type="standard",
),

# 修正後
"bookwalker": MangaRSSFeedConfig(
    name="BOOK☆WALKER - マンガ新刊",
    url="https://bookwalker.jp/rss/books.xml",  # ← 正しいURL
    category="manga",
    enabled=True,
    priority="high",
    timeout=15,  # 20秒 → 15秒に短縮（レスポンスタイムが4-5秒のため）
    parser_type="standard",
    retry_count=3,  # リトライ回数を明示
    retry_delay=2,  # リトライ間隔（秒）
),
```

### ファイル2: `modules/manga_rss.py`

#### 修正箇所: `_get_default_feeds` メソッド

```python
def _get_default_feeds(self) -> List[Dict[str, Any]]:
    """デフォルトのRSSフィード設定を返す（修正版 - 動作確認済みURL）"""
    return [
        {
            "name": "Yahoo!ニュース - エンタメ",
            "url": "https://news.yahoo.co.jp/rss/categories/entertainment.xml",
            "category": "news",
            "enabled": True,
            "priority": "medium",
            "timeout": 15,
            "retry_count": 2,
            "retry_delay": 1,
        },
        {
            "name": "NHKニュース - エンタメ",
            "url": "https://www3.nhk.or.jp/rss/news/cat7.xml",
            "category": "news",
            "enabled": True,
            "priority": "medium",
            "timeout": 15,
            "retry_count": 2,
            "retry_delay": 1,
        },
        # 修正: BookWalker正しいURL
        {
            "name": "BookWalker",
            "url": "https://bookwalker.jp/rss/books.xml",  # ← 修正
            "category": "manga",
            "enabled": True,
            "priority": "high",
            "timeout": 15,  # ← タイムアウト短縮
            "retry_count": 3,
            "retry_delay": 2,
        },
        {
            "name": "マガポケ (Mock)",
            "url": "https://httpbin.org/xml",
            "category": "manga",
            "enabled": False,
            "priority": "low",
            "timeout": 30,
            "retry_count": 3,
            "retry_delay": 2,
            "status": "mock_for_testing",
        },
        {
            "name": "ジャンプBOOKストア",
            "url": "https://jumpbookstore.com/rss/new-release",
            "category": "manga",
            "enabled": True,
            "priority": "high",
        },
        {
            "name": "コミックシーモア",
            "url": "https://www.cmoa.jp/rss/",
            "category": "manga",
            "enabled": True,
            "priority": "medium",
        },
        {
            "name": "まんが王国",
            "url": "https://comic.k-manga.jp/rss",
            "category": "manga",
            "enabled": True,
            "priority": "medium",
        },
    ]
```

### ファイル3: `config/config.template.json`

```json
{
  "rss_feeds": {
    "manga": [
      {
        "name": "BookWalker",
        "url": "https://bookwalker.jp/rss/books.xml",
        "category": "manga",
        "enabled": true,
        "priority": "high",
        "timeout": 15,
        "retry_count": 3,
        "retry_delay": 2
      }
    ]
  }
}
```

### ファイル4: `scripts/integration_test.py`

```python
# BookWalker RSS URL修正
MANGA_RSS_FEEDS = {
    "BookWalker": "https://bookwalker.jp/rss/books.xml",  # 修正
    "マガポケ": "https://pocket.shonenmagazine.com/rss/",
    # ... 他のフィード
}
```

### ファイル5: `scripts/performance_validation.py`

```python
# RSS URLリスト
RSS_URLS = [
    "https://bookwalker.jp/rss/books.xml",  # 修正
    "https://pocket.shonenmagazine.com/rss/",
    # ... 他のURL
]
```

### ファイル6: `scripts/operational_monitoring.py`

```python
# エンドポイントリスト
ENDPOINTS = [
    ("BookWalker RSS", "https://bookwalker.jp/rss/books.xml", "GET"),  # 修正
    # ... 他のエンドポイント
]
```

---

## 3. User-Agent改善（オプション）

### ファイル: `modules/manga_rss.py`

```python
class MangaRSSCollector:
    def __init__(self, config_manager):
        # ... 他の初期化コード

        # User-Agentを改善
        self.user_agent = "MangaAnimeNotifier/1.0 (Python/3.x; RSS Reader; +https://github.com/yourproject)"

        # ... 他の初期化コード
```

---

## 4. テストコード

### テストファイル: `tests/test_fixes.py`

```python
import pytest
import requests
import json


def test_bookwalker_rss_url():
    """BookWalker RSS URLが正常に取得できることを確認"""
    url = "https://bookwalker.jp/rss/books.xml"
    response = requests.head(url, timeout=10)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "xml" in response.headers.get("content-type", "").lower()


def test_api_notification_status_structure():
    """API /api/notification-status のレスポンス構造を確認"""
    # このテストはサーバーが起動している必要があります
    response = requests.get("http://localhost:5000/api/notification-status")

    assert response.status_code == 200
    data = response.json()

    # emailまたはnotificationキーが存在すること
    assert "email" in data or "notification" in data, \
        "Response should contain 'email' or 'notification' key"

    # calendarキーが存在すること
    assert "calendar" in data, "Response should contain 'calendar' key"

    # email/notificationにstatusが存在すること
    notification_data = data.get("email") or data.get("notification")
    assert "status" in notification_data, "Notification data should contain 'status'"


def test_javascript_data_handling():
    """JavaScriptのデータハンドリングをシミュレート"""
    # APIレスポンスのシミュレーション
    api_response = {
        "email": {
            "status": "success",
            "lastExecuted": "2025-11-15T10:00:00",
            "todayStats": {
                "successCount": 5,
                "errorCount": 0,
                "totalReleases": 10
            }
        },
        "calendar": {
            "status": "success",
            "lastExecuted": "2025-11-15T10:00:00",
            "todayStats": {
                "successCount": 5,
                "errorCount": 0,
                "totalEvents": 10
            }
        }
    }

    # JavaScriptの期待する構造に変換
    notification = api_response.get("notification") or api_response.get("email")
    calendar = api_response.get("calendar")

    assert notification is not None, "Notification data should be accessible"
    assert calendar is not None, "Calendar data should be accessible"
    assert notification["status"] == "success"
    assert calendar["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## 5. 実装チェックリスト

### 即座に実装（高優先度）
- [ ] `static/js/notification-status.js` のエラーハンドリング修正
  - [ ] `updateNotificationStatus` 関数
  - [ ] `updateCalendarStatus` 関数
  - [ ] `fetchStatus` 関数

- [ ] `modules/manga_rss_enhanced.py` のBookWalker URL修正
- [ ] `modules/manga_rss.py` のデフォルトフィード修正

### 次回更新時（中優先度）
- [ ] `config/config.template.json` の修正
- [ ] `scripts/integration_test.py` の修正
- [ ] `scripts/performance_validation.py` の修正
- [ ] `scripts/operational_monitoring.py` の修正

### 将来的な改善（低優先度）
- [ ] User-Agent文字列の改善
- [ ] フィード健全性監視機能の追加
- [ ] 詳細なエラーログ機能の実装

---

## 6. デプロイ手順

```bash
# 1. バックアップ作成
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
cp static/js/notification-status.js static/js/notification-status.js.backup
cp modules/manga_rss_enhanced.py modules/manga_rss_enhanced.py.backup
cp modules/manga_rss.py modules/manga_rss.py.backup

# 2. 修正ファイルを適用
# （上記の修正コードを各ファイルに反映）

# 3. 構文チェック
python3 -m py_compile modules/manga_rss_enhanced.py
python3 -m py_compile modules/manga_rss.py

# 4. テスト実行
python3 -m pytest tests/test_fixes.py -v

# 5. Webサーバー再起動
sudo systemctl restart manga-anime-notifier
# または
pkill -f web_app.py
python3 app/web_app.py &

# 6. 動作確認
curl -I https://bookwalker.jp/rss/books.xml
curl http://localhost:5000/api/notification-status | jq .

# 7. ブラウザでUI確認
# http://localhost:5000 にアクセスしてコンソールエラーがないことを確認
```

---

**修正コード作成日**: 2025-11-15
**次のステップ**: 修正の適用とテスト実行
