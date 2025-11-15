/**
 * 通知・カレンダー連携実行状況表示UI - JavaScript (既存API対応版)
 * ファイル: notification-status.js
 */

(function() {
    'use strict';

    // 設定
    const CONFIG = {
        updateInterval: 60000, // 1分ごとに更新
        apiEndpoint: '/api/notification-status',
        enableCountdown: true,
        dateFormat: {
            locale: 'ja-JP',
            options: {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            }
        }
    };

    // グローバル変数
    let updateTimer = null;
    let countdownTimer = null;
    let lastData = null;

    /**
     * 相対時刻を計算（XX分前、XX時間前）
     */
    function getRelativeTime(dateString) {
        if (!dateString) return '未実行';

        const now = new Date();
        const target = new Date(dateString);
        const diffMs = now - target;
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);
        const diffDay = Math.floor(diffHour / 24);

        if (diffSec < 60) return `${diffSec}秒前`;
        if (diffMin < 60) return `${diffMin}分前`;
        if (diffHour < 24) return `${diffHour}時間前`;
        return `${diffDay}日前`;
    }

    /**
     * 次回実行までのカウントダウン計算
     */
    function getCountdown(dateString) {
        if (!dateString) return '未定';

        const now = new Date();
        const target = new Date(dateString);
        const diffMs = target - now;

        if (diffMs <= 0) return '実行予定';

        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);
        const hours = diffHour;
        const minutes = diffMin % 60;
        const seconds = diffSec % 60;

        return `${hours}時間 ${minutes}分 ${seconds}秒`;
    }

    /**
     * 日時をフォーマット
     */
    function formatDateTime(dateString) {
        if (!dateString) return '---';

        const date = new Date(dateString);
        return date.toLocaleString(CONFIG.dateFormat.locale, CONFIG.dateFormat.options);
    }

    /**
     * メール通知ステータスを更新
     */
    function updateNotificationStatus(data) {
        const container = document.getElementById('notification-status-container');
        if (!container) return;

        const notification = data.notification;
        const statusClass = notification.status === 'success' ? 'success' :
                          notification.status === 'error' ? 'error' : 'pending';
        const statusIcon = notification.status === 'success' ? 'bi-check-circle-fill' :
                         notification.status === 'error' ? 'bi-x-circle-fill' : 'bi-hourglass-split';
        const statusText = notification.status === 'success' ? '正常' :
                         notification.status === 'error' ? 'エラーあり' : '未実行';

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
        } else if (notification.status === 'success') {
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
                            <div class="stat-value">${notification.todayStats?.successCount || 0}</div>
                            <div class="stat-label">成功</div>
                        </div>
                        <div class="stat-item error">
                            <div class="stat-value">${notification.todayStats?.errorCount || 0}</div>
                            <div class="stat-label">エラー</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${notification.todayStats?.totalReleases || 0}</div>
                            <div class="stat-label">通知数</div>
                        </div>
                    </div>

                    ${errorsHtml}
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    /**
     * カレンダー連携ステータスを更新
     */
    function updateCalendarStatus(data) {
        const container = document.getElementById('calendar-status-container');
        if (!container) return;

        const calendar = data.calendar;
        const statusClass = calendar.status === 'success' ? 'success' :
                          calendar.status === 'error' ? 'error' : 'pending';
        const statusIcon = calendar.status === 'success' ? 'bi-check-circle-fill' :
                         calendar.status === 'error' ? 'bi-x-circle-fill' : 'bi-hourglass-split';
        const statusText = calendar.status === 'success' ? '正常' :
                         calendar.status === 'error' ? 'エラーあり' : '未実行';

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
        } else if (calendar.status === 'success') {
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
                            <div class="stat-value">${calendar.todayStats?.successCount || 0}</div>
                            <div class="stat-label">成功</div>
                        </div>
                        <div class="stat-item error">
                            <div class="stat-value">${calendar.todayStats?.errorCount || 0}</div>
                            <div class="stat-label">エラー</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${calendar.todayStats?.totalEvents || 0}</div>
                            <div class="stat-label">登録数</div>
                        </div>
                    </div>

                    ${errorsHtml}
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    /**
     * カウントダウンタイマーを更新
     */
    function updateCountdowns() {
        if (!lastData || !CONFIG.enableCountdown) return;

        // メール通知のカウントダウン
        const notificationCountdown = document.querySelector('#notification-countdown span');
        if (notificationCountdown && lastData.notification.nextScheduled) {
            notificationCountdown.textContent = getCountdown(lastData.notification.nextScheduled);
        }

        // カレンダーのカウントダウン
        const calendarCountdown = document.querySelector('#calendar-countdown span');
        if (calendarCountdown && lastData.calendar.nextScheduled) {
            calendarCountdown.textContent = getCountdown(lastData.calendar.nextScheduled);
        }
    }

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
            lastData = data;

            // データ更新
            updateNotificationStatus(data);
            updateCalendarStatus(data);

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

    /**
     * エラーメッセージを表示
     */
    function showError(message) {
        const containers = [
            document.getElementById('notification-status-container'),
            document.getElementById('calendar-status-container')
        ];

        containers.forEach(container => {
            if (container) {
                container.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle-fill"></i>
                        ${message}
                    </div>
                `;
            }
        });
    }

    /**
     * 定期更新を開始
     */
    function startAutoUpdate() {
        // 初回実行
        fetchStatus();

        // 定期更新タイマー設定
        updateTimer = setInterval(fetchStatus, CONFIG.updateInterval);

        // カウントダウンタイマー設定（1秒ごと）
        if (CONFIG.enableCountdown) {
            countdownTimer = setInterval(updateCountdowns, 1000);
        }

        console.log(`通知ステータス自動更新を開始（${CONFIG.updateInterval / 1000}秒間隔）`);
    }

    /**
     * 定期更新を停止
     */
    function stopAutoUpdate() {
        if (updateTimer) {
            clearInterval(updateTimer);
            updateTimer = null;
        }

        if (countdownTimer) {
            clearInterval(countdownTimer);
            countdownTimer = null;
        }

        console.log('通知ステータス自動更新を停止');
    }

    /**
     * 手動更新
     */
    function manualRefresh() {
        console.log('手動更新実行');
        fetchStatus();
    }

    /**
     * 初期化
     */
    function init() {
        // ページが完全に読み込まれてから実行
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', startAutoUpdate);
        } else {
            startAutoUpdate();
        }

        // ページ離脱時にタイマークリア
        window.addEventListener('beforeunload', stopAutoUpdate);

        // グローバル関数として公開（デバッグ用）
        window.NotificationStatus = {
            refresh: manualRefresh,
            start: startAutoUpdate,
            stop: stopAutoUpdate,
            getLastData: () => lastData
        };
    }

    // 初期化実行
    init();

})();
