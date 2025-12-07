# 推奨修正コード集

このドキュメントには、QAテストで検出された問題の修正コードが含まれています。

---

## 修正1: `/works` エンドポイントの実装

### 優先度: 高 🔴
### ファイル: `app/web_app.py`

#### 追加するコード:

```python
@app.route("/works")
def works():
    """
    作品一覧ページ
    クエリパラメータ:
        type: 'anime' または 'manga' でフィルタリング
        page: ページ番号（デフォルト: 1）
        limit: 1ページあたりの件数（デフォルト: 20）
    """
    work_type = request.args.get('type', '')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    offset = (page - 1) * limit

    conn = get_db_connection()
    cursor = conn.cursor()

    # 総件数を取得
    if work_type:
        cursor.execute("SELECT COUNT(*) FROM works WHERE type = ?", (work_type,))
    else:
        cursor.execute("SELECT COUNT(*) FROM works")

    total_count = cursor.fetchone()[0]

    # ページネーション付きで作品を取得
    if work_type:
        cursor.execute(
            """
            SELECT w.*, COUNT(r.id) as release_count
            FROM works w
            LEFT JOIN releases r ON w.id = r.work_id
            WHERE w.type = ?
            GROUP BY w.id
            ORDER BY w.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (work_type, limit, offset)
        )
    else:
        cursor.execute(
            """
            SELECT w.*, COUNT(r.id) as release_count
            FROM works w
            LEFT JOIN releases r ON w.id = r.work_id
            GROUP BY w.id
            ORDER BY w.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )

    works_list = cursor.fetchall()
    conn.close()

    # ページネーション情報
    total_pages = (total_count + limit - 1) // limit

    return render_template(
        'works.html',
        works=works_list,
        work_type=work_type,
        page=page,
        total_pages=total_pages,
        total_count=total_count
    )


@app.route("/api/refresh-works", methods=["POST"])
def api_refresh_works():
    """
    作品リストを最新化するAPIエンドポイント
    """
    try:
        # 実際の更新ロジックをここに実装
        # 例: 各APIから最新データを取得

        return jsonify({
            "status": "success",
            "message": "作品リストを更新しました",
            "timestamp": datetime.now().isoformat(),
            "updated_count": 0  # 実際の更新件数
        })
    except Exception as e:
        logger.error(f"Works refresh failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
```

---

## 修正2: `templates/works.html` の作成

### 優先度: 高 🔴
### ファイル: `templates/works.html` (新規作成)

```html
{% extends "base.html" %}

{% block title %}作品一覧{% if work_type %} - {{ work_type }}{% endif %} - MangaAnime Info Delivery{% endblock %}

{% block content %}
<div class="container mt-4">
    <!-- ヘッダー -->
    <div class="row mb-4">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center">
                <h1>
                    <i class="bi bi-collection me-2"></i>
                    作品一覧
                    {% if work_type %}
                        <span class="badge bg-{{ 'success' if work_type == 'anime' else 'info' }}">
                            {{ work_type }}
                        </span>
                    {% endif %}
                </h1>
                <div>
                    <button class="btn btn-primary" onclick="refreshWorks()" id="refreshBtn">
                        <i class="bi bi-arrow-clockwise"></i> 更新
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- プログレスバー -->
    <div id="progressContainer" class="mb-3" style="display: none;">
        <div class="progress">
            <div class="progress-bar progress-bar-striped progress-bar-animated"
                 role="progressbar"
                 style="width: 100%"
                 aria-valuenow="100"
                 aria-valuemin="0"
                 aria-valuemax="100">
                更新中...
            </div>
        </div>
    </div>

    <!-- フィルター -->
    <div class="row mb-3">
        <div class="col-12">
            <div class="btn-group" role="group" aria-label="作品タイプフィルター">
                <a href="{{ url_for('works') }}"
                   class="btn btn-outline-secondary {% if not work_type %}active{% endif %}">
                    すべて
                </a>
                <a href="{{ url_for('works', type='anime') }}"
                   class="btn btn-outline-success {% if work_type == 'anime' %}active{% endif %}">
                    アニメ
                </a>
                <a href="{{ url_for('works', type='manga') }}"
                   class="btn btn-outline-info {% if work_type == 'manga' %}active{% endif %}">
                    マンガ
                </a>
            </div>

            <span class="ms-3 text-muted">
                全 {{ total_count }} 件
            </span>
        </div>
    </div>

    <!-- 作品リスト -->
    <div class="row" id="worksList">
        {% if works %}
            {% for work in works %}
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">
                            {{ work.title }}
                            <span class="badge bg-{{ 'success' if work.type == 'anime' else 'info' }} float-end">
                                {{ work.type }}
                            </span>
                        </h5>

                        {% if work.title_kana %}
                        <p class="card-text text-muted small">
                            <i class="bi bi-justify"></i> {{ work.title_kana }}
                        </p>
                        {% endif %}

                        {% if work.title_en %}
                        <p class="card-text text-muted small">
                            <i class="bi bi-globe"></i> {{ work.title_en }}
                        </p>
                        {% endif %}

                        <div class="mt-3">
                            <span class="badge bg-secondary">
                                <i class="bi bi-calendar-event"></i>
                                {{ work.release_count }} 件のリリース
                            </span>
                        </div>

                        {% if work.official_url %}
                        <div class="mt-2">
                            <a href="{{ work.official_url }}"
                               target="_blank"
                               class="btn btn-sm btn-outline-primary">
                                <i class="bi bi-link-45deg"></i> 公式サイト
                            </a>
                        </div>
                        {% endif %}
                    </div>

                    <div class="card-footer text-muted small">
                        <i class="bi bi-clock"></i>
                        登録日: {{ work.created_at[:10] }}
                    </div>
                </div>
            </div>
            {% endfor %}
        {% else %}
            <div class="col-12">
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i>
                    作品が見つかりませんでした。
                </div>
            </div>
        {% endif %}
    </div>

    <!-- ページネーション -->
    {% if total_pages > 1 %}
    <nav aria-label="作品一覧ページネーション">
        <ul class="pagination justify-content-center">
            {% if page > 1 %}
            <li class="page-item">
                <a class="page-link"
                   href="{{ url_for('works', type=work_type, page=page-1) }}"
                   aria-label="前へ">
                    <span aria-hidden="true">&laquo;</span>
                </a>
            </li>
            {% endif %}

            {% for p in range(1, total_pages + 1) %}
                {% if p == page %}
                <li class="page-item active">
                    <span class="page-link">{{ p }}</span>
                </li>
                {% elif (p - page)|abs <= 2 or p == 1 or p == total_pages %}
                <li class="page-item">
                    <a class="page-link" href="{{ url_for('works', type=work_type, page=p) }}">
                        {{ p }}
                    </a>
                </li>
                {% elif (p - page)|abs == 3 %}
                <li class="page-item disabled">
                    <span class="page-link">...</span>
                </li>
                {% endif %}
            {% endfor %}

            {% if page < total_pages %}
            <li class="page-item">
                <a class="page-link"
                   href="{{ url_for('works', type=work_type, page=page+1) }}"
                   aria-label="次へ">
                    <span aria-hidden="true">&raquo;</span>
                </a>
            </li>
            {% endif %}
        </ul>
    </nav>
    {% endif %}

    <!-- 最終更新時刻 -->
    <div class="row mt-4">
        <div class="col-12 text-center text-muted small">
            <i class="bi bi-clock-history"></i>
            最終更新: <span id="lastUpdateTime">{{ now }}</span>
        </div>
    </div>
</div>

<script>
function refreshWorks() {
    const btn = document.getElementById('refreshBtn');
    const progressContainer = document.getElementById('progressContainer');

    // ボタンを無効化
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>更新中...';

    // プログレスバーを表示
    progressContainer.style.display = 'block';

    // API呼び出し
    fetch('/api/refresh-works', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Refresh response:', data);

        // 成功メッセージを表示
        const alert = document.createElement('div');
        alert.className = 'alert alert-success alert-dismissible fade show';
        alert.innerHTML = `
            <i class="bi bi-check-circle"></i>
            ${data.message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.container').prepend(alert);

        // 最終更新時刻を更新
        document.getElementById('lastUpdateTime').textContent = new Date().toLocaleString('ja-JP');

        // ページをリロード
        setTimeout(() => {
            location.reload();
        }, 1500);
    })
    .catch(error => {
        console.error('Refresh error:', error);

        // エラーメッセージを表示
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            <i class="bi bi-exclamation-triangle"></i>
            更新中にエラーが発生しました。
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.container').prepend(alert);
    })
    .finally(() => {
        // ボタンを有効化
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> 更新';

        // プログレスバーを非表示
        progressContainer.style.display = 'none';
    });
}

// ページロード時に最終更新時刻を設定
document.addEventListener('DOMContentLoaded', function() {
    if (!document.getElementById('lastUpdateTime').textContent) {
        document.getElementById('lastUpdateTime').textContent = new Date().toLocaleString('ja-JP');
    }
});
</script>
{% endblock %}
```

---

## 修正3: 設定アクセサー関数

### 優先度: 中 🟡
### ファイル: `app/web_app.py`

```python
def get_config_value(config, *keys, default=None):
    """
    ネストされた設定値を安全に取得するユーティリティ関数

    使用例:
        ng_keywords = get_config_value(config, 'filters', 'ng_keywords', default=[])
        email = get_config_value(config, 'google', 'gmail', 'to_email', default='')

    Args:
        config: 設定辞書
        *keys: キーのパス
        default: デフォルト値

    Returns:
        取得した値またはデフォルト値
    """
    value = config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value


def get_ng_keywords(config):
    """NGキーワードを取得（後方互換性あり）"""
    # 新しい構造
    keywords = get_config_value(config, 'filters', 'ng_keywords')
    if keywords:
        return keywords

    # 古い構造（フォールバック）
    return config.get('ng_keywords', [])


def get_notification_email(config):
    """通知先メールアドレスを取得（後方互換性あり）"""
    # 新しい構造
    email = get_config_value(config, 'google', 'gmail', 'to_email')
    if email:
        return email

    # 古い構造（フォールバック）
    return config.get('notification_email', '')


def get_check_interval(config):
    """チェック間隔を取得（後方互換性あり）"""
    # 新しい構造
    interval = get_config_value(config, 'scheduler', 'check_interval_hours')
    if interval is not None:
        return interval

    # 古い構造（フォールバック）
    return config.get('check_interval_hours', 24)
```

---

## 修正4: API レスポンス構造の標準化

### 優先度: 中 🟡
### ファイル: `app/web_app.py`

```python
@app.route("/api/collection-status")
def collection_status():
    """
    収集状況を返す（標準化されたレスポンス構造）
    """
    # キャッシュチェック
    current_time = time.time()
    if (api_status_cache["data"] and
        current_time - api_status_cache["timestamp"] < CACHE_DURATION):
        cached_data = api_status_cache["data"]

        # トップレベルフィールドを追加
        return jsonify({
            "last_check": cached_data.get("timestamp", datetime.now().isoformat()),
            "status": "cached",
            "apiStatus": cached_data.get("apiStatus", {}),
            "metrics": cached_data.get("metrics", {})
        })

    # 実際のAPI接続テスト
    api_status = test_api_connections()

    # メトリクスの取得
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM releases WHERE notified = 0")
    pending_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM releases WHERE DATE(created_at) = DATE('now')")
    today_collected = cursor.fetchone()[0]

    conn.close()

    # システムアップタイム（簡易計算）
    uptime_seconds = int(current_time - api_status_cache.get("start_time", current_time))
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_str = f"{hours}時間{minutes}分"

    metrics = {
        "pendingCount": pending_count,
        "todayCollected": today_collected,
        "errorCount": sum(1 for status in api_status.values() if status["status"] == "error"),
        "systemUptime": uptime_str
    }

    # レスポンスデータ
    response_data = {
        "last_check": datetime.now().isoformat(),
        "status": "active",
        "apiStatus": api_status,
        "metrics": metrics
    }

    # キャッシュを更新
    api_status_cache["data"] = response_data
    api_status_cache["timestamp"] = current_time
    if "start_time" not in api_status_cache:
        api_status_cache["start_time"] = current_time

    return jsonify(response_data)
```

---

## 修正5: ホームページの更新ボタン強化

### 優先度: 低 🟢
### ファイル: `static/js/main.js` (新規または追加)

```javascript
/**
 * 今後の予定を更新する
 */
async function refreshUpcoming() {
    const btn = document.getElementById('refreshUpcomingBtn');
    const progressContainer = document.getElementById('upcomingProgressContainer');

    if (!btn) return;

    // ボタンを無効化
    btn.disabled = true;
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>更新中...';

    // プログレスバーを表示
    if (progressContainer) {
        progressContainer.style.display = 'block';
    }

    try {
        const response = await fetch('/api/refresh-upcoming', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();

        if (response.ok) {
            showNotification('success', data.message || '今後の予定を更新しました');

            // データをリロード
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            throw new Error(data.message || '更新に失敗しました');
        }
    } catch (error) {
        console.error('Refresh error:', error);
        showNotification('error', 'エラー: ' + error.message);
    } finally {
        // ボタンを復元
        btn.disabled = false;
        btn.innerHTML = originalHTML;

        // プログレスバーを非表示
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
    }
}

/**
 * リリース履歴を更新する
 */
async function refreshHistory() {
    const btn = document.getElementById('refreshHistoryBtn');
    const progressContainer = document.getElementById('historyProgressContainer');

    if (!btn) return;

    // ボタンを無効化
    btn.disabled = true;
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>更新中...';

    // プログレスバーを表示
    if (progressContainer) {
        progressContainer.style.display = 'block';
    }

    try {
        const response = await fetch('/api/refresh-history', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();

        if (response.ok) {
            showNotification('success', data.message || 'リリース履歴を更新しました');

            // データをリロード
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            throw new Error(data.message || '更新に失敗しました');
        }
    } catch (error) {
        console.error('Refresh error:', error);
        showNotification('error', 'エラー: ' + error.message);
    } finally {
        // ボタンを復元
        btn.disabled = false;
        btn.innerHTML = originalHTML;

        // プログレスバーを非表示
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
    }
}

/**
 * 通知を表示する
 */
function showNotification(type, message) {
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const iconClass = type === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle';

    const alert = document.createElement('div');
    alert.className = `alert ${alertClass} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alert.style.zIndex = '9999';
    alert.innerHTML = `
        <i class="bi ${iconClass} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(alert);

    // 5秒後に自動で削除
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

/**
 * 最終更新時刻を更新する
 */
function updateLastUpdateTime() {
    const elements = document.querySelectorAll('[data-last-update]');
    const now = new Date().toLocaleString('ja-JP');

    elements.forEach(el => {
        el.textContent = now;
    });
}

// ページロード時に最終更新時刻を設定
document.addEventListener('DOMContentLoaded', function() {
    updateLastUpdateTime();

    // 30秒ごとに更新
    setInterval(updateLastUpdateTime, 30000);
});
```

---

## テスト実行手順

### 1. ユニットテストの実行

```bash
# 新機能テストを実行
python -m pytest tests/test_new_features.py -v

# すべてのテストを実行
python -m pytest tests/ -v --tb=short

# カバレッジ付きで実行
python -m pytest tests/ --cov=app --cov-report=html
```

### 2. E2Eテストの実行

```bash
# Playwright テストを実行
npx playwright test tests/e2e/test_ui_features.py

# ヘッド付きモードで実行（ブラウザを表示）
npx playwright test tests/e2e/test_ui_features.py --headed

# 特定のブラウザでテスト
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### 3. 手動テスト

```bash
# Webサーバーを起動
python app/web_app.py

# ブラウザで以下のURLにアクセス
# http://localhost:5001/
# http://localhost:5001/works
# http://localhost:5001/config
```

---

## デプロイメントチェックリスト

- [ ] すべてのユニットテストが成功
- [ ] E2Eテストが成功
- [ ] 手動テストで主要機能を確認
- [ ] `/works` エンドポイントが正常に動作
- [ ] 更新ボタンが正常に動作
- [ ] プログレスバーが表示される
- [ ] エラーハンドリングが適切
- [ ] レスポンシブデザインが正常
- [ ] モバイルで正常に表示
- [ ] パフォーマンスが基準を満たす
- [ ] セキュリティチェック完了
- [ ] ドキュメント更新完了

---

**更新日**: 2025-11-15
**作成者**: QA Automation Agent
**承認**: Pending
