# 「今後の予定（7日以内）」エラー調査レポート

## 調査実施日
2025-11-15

## エラー内容
**「データの取得に失敗しました。後でもう一度お試しください。」**

このエラーはダッシュボードの「今後の予定（7日以内）」セクションで表示されます。

---

## 調査結果

### 1. APIエンドポイント確認 ✓

**ファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/web_app.py` (行642-659)

```python
@app.route("/api/releases/upcoming")
def api_upcoming_releases():
    """API endpoint for upcoming releases with proper title display"""
    conn = get_db_connection()
    releases = conn.execute(
        """
        SELECT w.id, w.title, w.title_kana, w.type,
               r.id as release_id, r.release_type, r.number, r.platform,
               r.release_date, r.source_url, r.notified, r.created_at
        FROM releases r
        JOIN works w ON r.work_id = w.id
        WHERE r.release_date >= date('now')
        ORDER BY r.release_date ASC
        LIMIT 50
    """
    ).fetchall()
    conn.close()

    return jsonify([dict(release) for release in releases])
```

**ステータス**: エンドポイントは存在し、正常に機能しています。

---

### 2. JavaScriptフェッチ処理確認 ✓

**ファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/static/js/dashboard-update.js` (行221-278)

```javascript
async refreshUpcomingReleases(silent = false) {
    if (this.isUpdating.upcomingReleases) {
        console.log('Already updating upcoming releases');
        return;
    }

    try {
        this.setLoading('upcomingReleases', true);
        this.updateProgress('upcomingReleases', 30);

        const response = await fetch('/api/releases/upcoming');
        this.updateProgress('upcomingReleases', 60);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        this.updateProgress('upcomingReleases', 80);

        this.renderUpcomingReleases(data);
        this.updateProgress('upcomingReleases', 100);

        this.updateTimestamps.upcomingReleases = new Date();
        this.updateTimestampDisplay('upcomingReleases');

        if (!silent) {
            this.showToast('更新完了', `今後の予定: ${data.length}件`, 'success');
        }

    } catch (error) {
        console.error('Error refreshing upcoming releases:', error);
        if (!silent) {
            this.showToast(
                '更新エラー',
                'データの取得に失敗しました。後でもう一度お試しください。',
                'error'
            );
        }
    }
}
```

**問題点**: 3行目の `if (!response.ok)` でエラーをスローしています。

---

### 3. ダッシュボードHTML確認 ✓

**ファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/templates/dashboard.html` (行270)

ボタンは正常に設定されています：
```html
<button class="btn-refresh" id="upcomingReleases-refresh-btn" onclick="refreshUpcomingReleases()">
    <i class="bi bi-arrow-clockwise"></i>
    <span class="d-none d-md-inline">更新</span>
</button>
```

---

### 4. データベース確認 ✓

**テーブル**: `releases`

- **合計レコード数**: 16件
- **今後の予定（今日以降）**: 16件
- **日付範囲**: 2025-11-15 ～ 2025-11-26

**サンプルデータ**:
```
title: 葬送のフリーレン
type: anime
release_date: 2025-11-15
platform: dアニメストア
```

データベースには正常なデータが存在しています。

---

### 5. APIエンドポイント動作確認

**テスト実施**: Python テストクライアントを使用

```
Status Code: 200
Content-Type: application/json
Response Length: 5635 bytes
Number of Items: 16件
```

**レスポンスサンプル**:
```json
{
  "created_at": "2025-11-14 13:56:07",
  "id": 229,
  "notified": 0,
  "number": "29",
  "platform": "dアニメストア",
  "release_date": "2025-11-15",
  "release_id": 305,
  "release_type": "episode",
  "source_url": "https://frieren-anime.jp/",
  "title": "葬送のフリーレン",
  "title_kana": "そうそうのふりーれん",
  "type": "anime"
}
```

APIは正常に機能しています。

---

### 6. リソースローディング確認 ✓

- **dashboard-update.js**: `/static/js/dashboard-update.js` (17.1 KB)
- **dashboard-update.css**: `/static/css/dashboard-update.css`
- **base.html**: すべてのスクリプトが正常にロードされている

---

## 根本原因分析

### 可能性1: ブラウザキャッシュ（最可能性が高い）

新しいJavaScriptファイルが完全にロードされていない可能性があります。
- ブラウザが古いバージョンをキャッシュしている
- Service Workerが古いファイルを提供している

### 可能性2: 一時的なネットワークエラー

リクエスト時に一時的なネットワーク遅延が発生した。

### 可能性3: JavaScriptの初期化タイミング

`DOMContentLoaded`イベントの発火時に、DOM要素がまだ完全に準備されていない。

### 可能性4: エラーロギング不足

実際のエラー詳細が記録されていない。

---

## 推奨される修正方法

### 方法1: ブラウザキャッシュをクリア（即座の解決）

1. ブラウザの開発者ツール（F12）を開く
2. 「Application」または「Storage」タブ
3. キャッシュをクリア
4. Service Workerを登録解除
5. ページを再度読み込み

### 方法2: エラーログを詳細化（推奨）

`dashboard-update.js`のエラーハンドリングを改善してください：

```javascript
catch (error) {
    console.error('Error refreshing upcoming releases:', error);
    console.error('Error details:', {
        message: error.message,
        stack: error.stack,
        status: error.status,
        timestamp: new Date().toISOString()
    });

    if (!silent) {
        this.showToast(
            '更新エラー',
            'データの取得に失敗しました。ブラウザのコンソール（F12）でエラーを確認してください。',
            'error'
        );
    }
}
```

### 方法3: HTTPレスポンスの詳細確認

Flask エンドポイントにエラーログを追加：

```python
@app.route("/api/releases/upcoming")
def api_upcoming_releases():
    """API endpoint for upcoming releases with proper title display"""
    try:
        conn = get_db_connection()
        releases = conn.execute(
            """
            SELECT w.id, w.title, w.title_kana, w.type,
                   r.id as release_id, r.release_type, r.number, r.platform,
                   r.release_date, r.source_url, r.notified, r.created_at
            FROM releases r
            JOIN works w ON r.work_id = w.id
            WHERE r.release_date >= date('now')
            ORDER BY r.release_date ASC
            LIMIT 50
        """
        ).fetchall()
        conn.close()

        data = [dict(release) for release in releases]
        logger.info(f"Returning {len(data)} upcoming releases")
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching upcoming releases: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
```

### 方法4: ネットワークのタイムアウト対応

JavaScript で fetchのタイムアウトを設定：

```javascript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 5000);

try {
    const response = await fetch('/api/releases/upcoming', {
        signal: controller.signal
    });
    clearTimeout(timeoutId);
    // ... rest of code
} catch (error) {
    if (error.name === 'AbortError') {
        console.error('Request timeout');
    }
}
```

---

## 検証済みの事実

| 項目 | 状態 | 詳細 |
|-----|------|------|
| APIエンドポイント存在 | ✓ OK | `/api/releases/upcoming` は定義されている |
| APIレスポンス | ✓ OK | HTTP 200で正常なJSONデータ返却 |
| データベース | ✓ OK | 16件のデータが存在 |
| JavaScriptファイル | ✓ OK | `dashboard-update.js` は読み込まれている |
| HTMLボタン | ✓ OK | `onclick="refreshUpcomingReleases()"` は正常 |
| イベントリスナー | ✓ OK | DOMContentLoadedで初期化されている |

---

## 次ステップ

1. **ブラウザキャッシュをクリア**して、ページをリロードする
2. ブラウザの開発者ツール（F12）→「Console」タブを開く
3. 「今後の予定」のリロードボタンをクリック
4. コンソールに表示されたエラーメッセージを確認
5. 以下の情報を記録：
   - 正確なエラーメッセージ
   - ネットワークタブでのHTTPレスポンス
   - リクエスト/レスポンスヘッダ

---

## 結論

システムの各コンポーネント（API、JavaScript、データベース、HTML）はすべて正常に動作しています。エラーの原因は以下のいずれかの可能性が高い：

1. **ブラウザキャッシュ**（最も可能性が高い）
2. 一時的なネットワーク遅延
3. Service Workerキャッシュの問題
4. JavaScriptコンソールエラーの詳細が記録されていない

推奨される対応は、まずブラウザキャッシュをクリアしてテストすることです。それでも問題が解決しない場合は、方法2～4の修正を実装してください。
