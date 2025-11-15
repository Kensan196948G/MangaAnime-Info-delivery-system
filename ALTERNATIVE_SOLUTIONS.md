# 代替ソリューション提案

BookWalkerのRSSフィードおよびJavaScriptエラーに対する代替的なアプローチを提案します。

---

## 目次
1. [BookWalker RSS代替ソース](#1-bookwalker-rss代替ソース)
2. [JavaScriptアーキテクチャ改善](#2-javascriptアーキテクチャ改善)
3. [APIレスポンス構造の標準化](#3-apiレスポンス構造の標準化)
4. [フィード健全性監視システム](#4-フィード健全性監視システム)
5. [エラー通知システム](#5-エラー通知システム)

---

## 1. BookWalker RSS代替ソース

### 1.1 複数RSSソースの統合

BookWalkerの単一RSSに依存せず、複数のソースから情報を収集する。

#### 実装例

```python
# modules/manga_rss_multi_source.py

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import logging


@dataclass
class MultiSourceConfig:
    """複数ソース設定"""
    primary_url: str
    fallback_urls: List[str]
    priority: int = 1


class MultiSourceRSSCollector:
    """複数ソースからRSS収集を行うクラス"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sources = {
            "bookwalker": MultiSourceConfig(
                primary_url="https://bookwalker.jp/rss/books.xml",
                fallback_urls=[
                    "https://bookwalker.jp/rss/series.xml",  # 仮のフォールバック
                    "https://bookwalker.jp/api/feed/",  # 仮のAPI
                ],
                priority=1
            )
        }

    def collect_from_multi_source(self, source_name: str) -> List[Dict[str, Any]]:
        """
        複数ソースから収集（フォールバック機能付き）

        Args:
            source_name: ソース名

        Returns:
            収集したデータ
        """
        config = self.sources.get(source_name)
        if not config:
            self.logger.error(f"Unknown source: {source_name}")
            return []

        # プライマリURLを試行
        items = self._try_fetch(config.primary_url, source_name)
        if items:
            self.logger.info(f"Primary source成功: {source_name}")
            return items

        # フォールバックURLを順次試行
        for i, fallback_url in enumerate(config.fallback_urls, 1):
            self.logger.warning(
                f"Primary source失敗。Fallback {i}を試行: {fallback_url}"
            )
            items = self._try_fetch(fallback_url, source_name)
            if items:
                self.logger.info(f"Fallback {i}成功: {source_name}")
                return items

        self.logger.error(
            f"All sources失敗: {source_name} (試行数: {1 + len(config.fallback_urls)})"
        )
        return []

    def _try_fetch(self, url: str, source_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        単一URLからデータ取得を試行

        Args:
            url: RSS URL
            source_name: ソース名

        Returns:
            取得したデータ、失敗時はNone
        """
        try:
            import requests
            import feedparser

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            feed = feedparser.parse(response.content)
            if not feed.entries:
                return None

            # データ変換処理
            items = []
            for entry in feed.entries:
                item = {
                    "title": entry.get("title"),
                    "link": entry.get("link"),
                    "published": entry.get("published"),
                    "source": source_name,
                    "source_url": url,
                }
                items.append(item)

            return items

        except Exception as e:
            self.logger.warning(f"Fetch failed for {url}: {e}")
            return None
```

### 1.2 Webスクレイピング（最終手段）

RSSが利用できない場合のHTMLスクレイピング。

#### 実装例

```python
# modules/manga_scraper.py

from bs4 import BeautifulSoup
import requests
from typing import List, Dict, Any
import logging


class BookWalkerScraper:
    """BookWalkerのWebスクレイピングクラス（RSSが使えない場合の代替）"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://bookwalker.jp"
        self.new_releases_url = f"{self.base_url}/new-releases/"

    def scrape_new_releases(self) -> List[Dict[str, Any]]:
        """
        新刊情報をスクレイピング

        Returns:
            新刊情報リスト
        """
        try:
            response = requests.get(
                self.new_releases_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36"
                },
                timeout=15
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # 書籍情報を抽出（実際のHTML構造に合わせて調整が必要）
            books = []
            for book_elem in soup.select(".book-item"):  # 仮のセレクタ
                try:
                    title = book_elem.select_one(".book-title").text.strip()
                    link = book_elem.select_one("a")["href"]
                    # 相対URLを絶対URLに変換
                    if not link.startswith("http"):
                        link = f"{self.base_url}{link}"

                    books.append({
                        "title": title,
                        "link": link,
                        "source": "BookWalker (Scraping)",
                    })

                except Exception as e:
                    self.logger.warning(f"Failed to parse book element: {e}")
                    continue

            self.logger.info(f"Scraped {len(books)} books from BookWalker")
            return books

        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            return []

    def is_allowed_by_robots_txt(self) -> bool:
        """
        robots.txtでスクレイピングが許可されているか確認

        Returns:
            許可されている場合True
        """
        try:
            from urllib.robotparser import RobotFileParser

            rp = RobotFileParser()
            rp.set_url(f"{self.base_url}/robots.txt")
            rp.read()

            return rp.can_fetch("*", self.new_releases_url)

        except Exception as e:
            self.logger.warning(f"robots.txt check failed: {e}")
            return False
```

**注意**: Webスクレイピングを使用する場合は、必ず以下を確認してください：
1. 利用規約の確認
2. robots.txtの確認
3. 過度なリクエストの禁止（レート制限の実装）
4. User-Agentの明示

---

## 2. JavaScriptアーキテクチャ改善

### 2.1 TypeScript化

型安全性を向上させ、実行時エラーを防ぐ。

#### 実装例: `static/js/notification-status.ts`

```typescript
// TypeScript版

interface NotificationData {
    lastExecuted: string | null;
    status: 'success' | 'error' | 'unknown';
    todayStats?: {
        successCount: number;
        errorCount: number;
        totalReleases: number;
    };
    recentErrors?: Array<{
        time: string;
        message: string;
    }>;
    checkIntervalHours?: number;
    nextScheduled?: string;
}

interface CalendarData {
    lastExecuted: string | null;
    status: 'success' | 'error' | 'unknown';
    todayStats?: {
        successCount: number;
        errorCount: number;
        totalEvents: number;
    };
    recentErrors?: Array<{
        time: string;
        message: string;
    }>;
    checkIntervalHours?: number;
    nextScheduled?: string;
}

interface APIResponse {
    email?: NotificationData;
    notification?: NotificationData;
    calendar?: CalendarData;
    overall?: {
        healthStatus: string;
        lastUpdate: string;
    };
}

class NotificationStatusManager {
    private config = {
        updateInterval: 60000,
        apiEndpoint: '/api/notification-status',
    };

    private lastData: APIResponse | null = null;
    private updateTimer: number | null = null;

    async fetchStatus(): Promise<void> {
        try {
            const response = await fetch(this.config.apiEndpoint);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data: APIResponse = await response.json();

            // データ検証
            this.validateData(data);

            this.lastData = data;

            // UI更新
            this.updateNotificationStatus(data);
            this.updateCalendarStatus(data);

        } catch (error) {
            console.error('Status fetch error:', error);
            this.showError(error instanceof Error ? error.message : 'Unknown error');
        }
    }

    private validateData(data: APIResponse): void {
        const hasNotification = !!(data.email || data.notification);
        const hasCalendar = !!data.calendar;

        if (!hasNotification) {
            throw new Error('Notification data not found in API response');
        }

        if (!hasCalendar) {
            throw new Error('Calendar data not found in API response');
        }
    }

    private updateNotificationStatus(data: APIResponse): void {
        const notification = data.notification || data.email;
        if (!notification) return;

        // UI更新処理（型安全）
        const status = notification.status || 'unknown';
        // ...
    }

    private updateCalendarStatus(data: APIResponse): void {
        const calendar = data.calendar;
        if (!calendar) return;

        // UI更新処理（型安全）
        const status = calendar.status || 'unknown';
        // ...
    }

    private showError(message: string): void {
        // エラー表示処理
        console.error(message);
    }
}

// 初期化
const statusManager = new NotificationStatusManager();
statusManager.fetchStatus();
```

### 2.2 React/Vue.jsへの移行

より堅牢なフロントエンドフレームワークを使用。

#### React実装例

```tsx
// components/NotificationStatus.tsx

import React, { useState, useEffect } from 'react';

interface NotificationData {
    lastExecuted: string | null;
    status: 'success' | 'error' | 'unknown';
    todayStats?: {
        successCount: number;
        errorCount: number;
        totalReleases: number;
    };
}

interface APIResponse {
    email?: NotificationData;
    notification?: NotificationData;
    calendar?: NotificationData;
}

const NotificationStatus: React.FC = () => {
    const [data, setData] = useState<APIResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                setLoading(true);
                const response = await fetch('/api/notification-status');

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const result: APIResponse = await response.json();

                // データ検証
                if (!result.email && !result.notification) {
                    throw new Error('Notification data not found');
                }

                if (!result.calendar) {
                    throw new Error('Calendar data not found');
                }

                setData(result);
                setError(null);

            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error');
            } finally {
                setLoading(false);
            }
        };

        fetchStatus();

        // 定期更新
        const interval = setInterval(fetchStatus, 60000);
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div>Loading...</div>;
    if (error) return <div className="alert alert-danger">{error}</div>;
    if (!data) return null;

    const notification = data.notification || data.email;

    return (
        <div className="notification-status">
            <h3>メール通知実行状況</h3>
            <div className={`status-badge ${notification?.status}`}>
                {notification?.status}
            </div>
            <div className="stats">
                <p>成功: {notification?.todayStats?.successCount || 0}</p>
                <p>エラー: {notification?.todayStats?.errorCount || 0}</p>
                <p>通知数: {notification?.todayStats?.totalReleases || 0}</p>
            </div>
        </div>
    );
};

export default NotificationStatus;
```

---

## 3. APIレスポンス構造の標準化

### 3.1 一貫したレスポンスフォーマット

すべてのAPIエンドポイントで統一されたフォーマットを使用。

#### 実装例: `app/api_response.py`

```python
from typing import Any, Dict, Optional
from datetime import datetime
from flask import jsonify


class APIResponse:
    """標準化されたAPIレスポンス"""

    @staticmethod
    def success(data: Any, message: Optional[str] = None) -> Dict[str, Any]:
        """
        成功レスポンス

        Args:
            data: レスポンスデータ
            message: オプションのメッセージ

        Returns:
            標準化されたレスポンス
        """
        response = {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        if message:
            response["message"] = message

        return response

    @staticmethod
    def error(message: str, code: str = "UNKNOWN_ERROR", details: Optional[Any] = None) -> Dict[str, Any]:
        """
        エラーレスポンス

        Args:
            message: エラーメッセージ
            code: エラーコード
            details: 詳細情報

        Returns:
            標準化されたエラーレスポンス
        """
        response = {
            "success": False,
            "error": {
                "message": message,
                "code": code,
                "timestamp": datetime.now().isoformat(),
            }
        }

        if details:
            response["error"]["details"] = details

        return response


# 使用例
@app.route("/api/notification-status")
def api_notification_status():
    try:
        # データ取得
        notification_data = get_notification_data()
        calendar_data = get_calendar_data()

        # 標準化されたレスポンス
        return jsonify(APIResponse.success({
            "notification": notification_data,  # 統一されたキー名
            "calendar": calendar_data,
            "overall": {
                "healthStatus": "healthy",
                "lastUpdate": datetime.now().isoformat()
            }
        }))

    except Exception as e:
        return jsonify(APIResponse.error(
            message=str(e),
            code="NOTIFICATION_STATUS_ERROR"
        )), 500
```

### 3.2 バージョニング

APIの後方互換性を維持しながら新機能を追加。

```python
# app/web_app.py

@app.route("/api/v1/notification-status")
def api_v1_notification_status():
    """API v1 - 旧形式（email/calendar）"""
    return jsonify({
        "email": {...},
        "calendar": {...}
    })


@app.route("/api/v2/notification-status")
@app.route("/api/notification-status")  # デフォルトはv2
def api_v2_notification_status():
    """API v2 - 新形式（notification/calendar）"""
    return jsonify({
        "notification": {...},
        "calendar": {...},
        "version": "2.0"
    })
```

---

## 4. フィード健全性監視システム

### 4.1 自動健全性チェック

```python
# modules/feed_health_monitor.py

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List
import sqlite3


class FeedHealthMonitor:
    """RSSフィード健全性監視システム"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feed_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_name TEXT NOT NULL,
                feed_url TEXT NOT NULL,
                status_code INTEGER,
                response_time REAL,
                success INTEGER,
                error_message TEXT,
                checked_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def check_feed(self, feed_name: str, feed_url: str) -> Dict:
        """
        フィードの健全性をチェック

        Args:
            feed_name: フィード名
            feed_url: フィードURL

        Returns:
            チェック結果
        """
        start_time = time.time()
        result = {
            "feed_name": feed_name,
            "feed_url": feed_url,
            "checked_at": datetime.now().isoformat(),
        }

        try:
            response = requests.head(feed_url, timeout=10)
            response_time = time.time() - start_time

            result.update({
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code == 200,
                "error_message": None,
            })

        except Exception as e:
            result.update({
                "status_code": None,
                "response_time": time.time() - start_time,
                "success": False,
                "error_message": str(e),
            })

        # データベースに記録
        self._save_result(result)

        return result

    def _save_result(self, result: Dict):
        """チェック結果をデータベースに保存"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO feed_health (
                feed_name, feed_url, status_code, response_time, success, error_message
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            result["feed_name"],
            result["feed_url"],
            result["status_code"],
            result["response_time"],
            1 if result["success"] else 0,
            result["error_message"]
        ))
        conn.commit()
        conn.close()

    def get_health_report(self, feed_name: str, hours: int = 24) -> Dict:
        """
        過去N時間の健全性レポートを取得

        Args:
            feed_name: フィード名
            hours: 過去何時間分

        Returns:
            健全性レポート
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        since = datetime.now() - timedelta(hours=hours)

        rows = conn.execute("""
            SELECT * FROM feed_health
            WHERE feed_name = ? AND checked_at >= ?
            ORDER BY checked_at DESC
        """, (feed_name, since.isoformat())).fetchall()

        conn.close()

        if not rows:
            return {"feed_name": feed_name, "data": []}

        total = len(rows)
        success_count = sum(1 for row in rows if row["success"])
        avg_response_time = sum(row["response_time"] for row in rows) / total

        return {
            "feed_name": feed_name,
            "total_checks": total,
            "success_count": success_count,
            "failure_count": total - success_count,
            "success_rate": success_count / total,
            "average_response_time": avg_response_time,
            "health_score": self._calculate_health_score(success_count, total, avg_response_time),
        }

    def _calculate_health_score(self, success: int, total: int, avg_time: float) -> float:
        """
        ヘルススコアを計算（0.0-1.0）

        Args:
            success: 成功回数
            total: 合計回数
            avg_time: 平均応答時間

        Returns:
            ヘルススコア
        """
        success_rate = success / total if total > 0 else 0
        time_penalty = min(avg_time / 10.0, 0.5)  # 10秒で50%ペナルティ
        score = success_rate - time_penalty
        return max(0.0, min(1.0, score))
```

---

## 5. エラー通知システム

### 5.1 即座のエラーアラート

```python
# modules/alert_system.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
import logging


class AlertSystem:
    """エラー通知システム"""

    def __init__(self, smtp_config: dict, recipients: List[str]):
        self.smtp_config = smtp_config
        self.recipients = recipients
        self.logger = logging.getLogger(__name__)

    def send_rss_feed_alert(self, feed_name: str, error_message: str):
        """
        RSSフィードエラーアラートを送信

        Args:
            feed_name: フィード名
            error_message: エラーメッセージ
        """
        subject = f"[ALERT] RSS Feed Error: {feed_name}"
        body = f"""
RSS Feed Error Detected

Feed Name: {feed_name}
Error Message: {error_message}
Timestamp: {datetime.now().isoformat()}

Please check the feed configuration and availability.
        """

        self._send_email(subject, body)

    def send_javascript_error_alert(self, error_details: str):
        """
        JavaScriptエラーアラートを送信

        Args:
            error_details: エラー詳細
        """
        subject = "[ALERT] JavaScript Error Detected"
        body = f"""
JavaScript Error Detected

Error Details:
{error_details}

Timestamp: {datetime.now().isoformat()}

Please check the browser console and application logs.
        """

        self._send_email(subject, body)

    def _send_email(self, subject: str, body: str):
        """
        メール送信

        Args:
            subject: 件名
            body: 本文
        """
        try:
            msg = MIMEMultipart()
            msg["From"] = self.smtp_config["from_address"]
            msg["To"] = ", ".join(self.recipients)
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"]) as server:
                server.starttls()
                server.login(
                    self.smtp_config["username"],
                    self.smtp_config["password"]
                )
                server.send_message(msg)

            self.logger.info(f"Alert email sent: {subject}")

        except Exception as e:
            self.logger.error(f"Failed to send alert email: {e}")
```

---

## 6. 実装優先順位

### 高優先度
1. フィード健全性監視システム（即座に価値を提供）
2. APIレスポンス構造の標準化（長期的な保守性向上）

### 中優先度
3. 複数RSSソースの統合（BookWalkerの代替）
4. TypeScript化（型安全性の向上）

### 低優先度
5. React/Vue.jsへの移行（大規模リファクタリング）
6. Webスクレイピング（最終手段）

---

**ドキュメント作成日**: 2025-11-15
**次のステップ**: 優先順位に基づいた実装計画の策定
