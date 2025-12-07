/**
 * Dashboard Update Manager
 * リリース情報の更新、UIフィードバック、エラーハンドリング
 */

class DashboardUpdateManager {
    constructor() {
        this.updateTimestamps = {
            recentReleases: null,
            upcomingReleases: null,
            releaseHistory: null
        };
        this.isUpdating = {
            recentReleases: false,
            upcomingReleases: false,
            releaseHistory: false
        };
        this.init();
    }

    init() {
        console.log('DashboardUpdateManager initialized');
        this.updateAllTimestamps();
        this.setupAutoRefresh();
    }

    /**
     * 最終更新時刻をすべて現在時刻に設定
     */
    updateAllTimestamps() {
        const now = new Date();
        Object.keys(this.updateTimestamps).forEach(key => {
            this.updateTimestamps[key] = now;
            this.updateTimestampDisplay(key);
        });
    }

    /**
     * 最終更新時刻の表示を更新
     */
    updateTimestampDisplay(section) {
        const badge = document.getElementById(`${section}-timestamp`);
        if (!badge) return;

        const timestamp = this.updateTimestamps[section];
        if (!timestamp) return;

        const formatted = this.formatTimestamp(timestamp);
        const timeElement = badge.querySelector('.time-text');
        if (timeElement) {
            timeElement.textContent = formatted;
        }
    }

    /**
     * タイムスタンプのフォーマット
     */
    formatTimestamp(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);

        if (diffSec < 10) return '今';
        if (diffSec < 60) return `${diffSec}秒前`;
        if (diffMin < 60) return `${diffMin}分前`;
        if (diffHour < 24) return `${diffHour}時間前`;

        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${hours}:${minutes}`;
    }

    /**
     * 自動更新のセットアップ (5分ごと)
     */
    setupAutoRefresh() {
        setInterval(() => {
            this.updateAllTimestamps();
        }, 60000); // 1分ごとに表示を更新

        // 5分ごとに自動データ更新
        setInterval(() => {
            console.log('Auto-refresh triggered');
            this.refreshRecentReleases(true);
            this.refreshUpcomingReleases(true);
        }, 300000);
    }

    /**
     * ローディング状態の設定
     */
    setLoading(section, isLoading) {
        this.isUpdating[section] = isLoading;

        const button = document.getElementById(`${section}-refresh-btn`);
        const badge = document.getElementById(`${section}-timestamp`);
        const card = document.getElementById(`${section}-card`);
        const overlay = document.getElementById(`${section}-overlay`);

        if (button) {
            button.disabled = isLoading;
            button.classList.toggle('loading', isLoading);
        }

        if (badge) {
            badge.classList.toggle('updating', isLoading);
        }

        if (card) {
            card.classList.toggle('updating', isLoading);
        }

        if (overlay) {
            overlay.classList.toggle('active', isLoading);
        }
    }

    /**
     * プログレスバーの更新
     */
    updateProgress(section, percent) {
        const progressBar = document.getElementById(`${section}-progress`);
        if (progressBar) {
            progressBar.style.width = `${percent}%`;
        }
    }

    /**
     * トースト通知の表示
     */
    showToast(title, message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            console.warn('Toast container not found');
            return;
        }

        const toastId = `toast-${Date.now()}`;
        const iconMap = {
            success: 'check-circle-fill',
            error: 'exclamation-triangle-fill',
            info: 'info-circle-fill',
            warning: 'exclamation-circle-fill'
        };

        const bgMap = {
            success: 'bg-success',
            error: 'bg-danger',
            info: 'bg-primary',
            warning: 'bg-warning'
        };

        const toastHtml = `
            <div id="${toastId}" class="toast update-toast" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header ${bgMap[type]}">
                    <i class="bi bi-${iconMap[type]} me-2"></i>
                    <strong class="me-auto">${title}</strong>
                    <small>今</small>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="閉じる"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);

        const toastElement = document.getElementById(toastId);
        const bsToast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: 5000
        });

        bsToast.show();

        // トースト削除
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    /**
     * 最近のリリース情報を更新
     */
    async refreshRecentReleases(silent = false) {
        if (this.isUpdating.recentReleases) {
            console.log('Already updating recent releases');
            return;
        }

        try {
            this.setLoading('recentReleases', true);
            this.updateProgress('recentReleases', 30);

            const response = await fetch('/api/releases/recent');
            this.updateProgress('recentReleases', 60);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.updateProgress('recentReleases', 80);

            this.renderRecentReleases(data);
            this.updateProgress('recentReleases', 100);

            this.updateTimestamps.recentReleases = new Date();
            this.updateTimestampDisplay('recentReleases');

            if (!silent) {
                this.showToast(
                    '更新完了',
                    `最近のリリース: ${data.length}件`,
                    'success'
                );
            }

        } catch (error) {
            console.error('Error refreshing recent releases:', error);
            console.error('Error details:', {
                message: error.message,
                stack: error.stack,
                timestamp: new Date().toISOString()
            });

            if (!silent) {
                const errorMsg = error.message.includes('HTTP error')
                    ? 'サーバーからのレスポンスエラーが発生しました。ページを再度読み込んでください。'
                    : 'データの取得に失敗しました。後でもう一度お試しください。';

                this.showToast(
                    '更新エラー',
                    errorMsg,
                    'error'
                );
            }
        } finally {
            setTimeout(() => {
                this.setLoading('recentReleases', false);
                this.updateProgress('recentReleases', 0);
            }, 300);
        }
    }

    /**
     * 今後の予定を更新
     */
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
                this.showToast(
                    '更新完了',
                    `今後の予定: ${data.length}件`,
                    'success'
                );
            }

        } catch (error) {
            console.error('Error refreshing upcoming releases:', error);
            console.error('Error details:', {
                message: error.message,
                stack: error.stack,
                timestamp: new Date().toISOString()
            });

            if (!silent) {
                const errorMsg = error.message.includes('HTTP error')
                    ? 'サーバーからのレスポンスエラーが発生しました。ページを再度読み込んでください。'
                    : 'データの取得に失敗しました。後でもう一度お試しください。';

                this.showToast(
                    '更新エラー',
                    errorMsg,
                    'error'
                );
            }
        } finally {
            setTimeout(() => {
                this.setLoading('upcomingReleases', false);
                this.updateProgress('upcomingReleases', 0);
            }, 300);
        }
    }

    /**
     * リリース履歴を更新
     */
    async refreshReleaseHistory(silent = false) {
        if (this.isUpdating.releaseHistory) {
            console.log('Already updating release history');
            return;
        }

        try {
            this.setLoading('releaseHistory', true);
            this.updateProgress('releaseHistory', 30);

            const response = await fetch('/api/releases/history');
            this.updateProgress('releaseHistory', 60);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.updateProgress('releaseHistory', 80);

            this.renderReleaseHistory(data);
            this.updateProgress('releaseHistory', 100);

            this.updateTimestamps.releaseHistory = new Date();
            this.updateTimestampDisplay('releaseHistory');

            if (!silent) {
                this.showToast(
                    '更新完了',
                    `リリース履歴: ${data.length}件`,
                    'success'
                );
            }

        } catch (error) {
            console.error('Error refreshing release history:', error);
            console.error('Error details:', {
                message: error.message,
                stack: error.stack,
                timestamp: new Date().toISOString()
            });

            if (!silent) {
                const errorMsg = error.message.includes('HTTP error')
                    ? 'サーバーからのレスポンスエラーが発生しました。ページを再度読み込んでください。'
                    : 'データの取得に失敗しました。後でもう一度お試しください。';

                this.showToast(
                    '更新エラー',
                    errorMsg,
                    'error'
                );
            }
        } finally {
            setTimeout(() => {
                this.setLoading('releaseHistory', false);
                this.updateProgress('releaseHistory', 0);
            }, 300);
        }
    }

    /**
     * 最近のリリースをレンダリング
     */
    renderRecentReleases(releases) {
        const container = document.getElementById('recent-releases-list');
        if (!container) return;

        if (releases.length === 0) {
            container.innerHTML = `
                <div class="p-4 text-center text-muted">
                    <i class="bi bi-inbox fs-1 mb-3 d-block"></i>
                    <p>最近のリリースはありません</p>
                </div>
            `;
            return;
        }

        const html = releases.map(release => `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="d-flex align-items-center mb-1">
                            ${release.type === 'anime'
                                ? '<span class="badge bg-primary me-2"><i class="bi bi-tv"></i> アニメ</span>'
                                : '<span class="badge bg-secondary me-2"><i class="bi bi-book"></i> マンガ</span>'
                            }
                            <strong>${this.escapeHtml(release.title_kana || release.title)}</strong>
                        </div>
                        <div class="text-muted small">
                            ${release.release_type === 'episode' ? '第' + release.number + '話' : '第' + release.number + '巻'}
                            · ${this.escapeHtml(release.platform)}
                            · ${release.release_date}
                        </div>
                    </div>
                    <div class="text-end">
                        ${release.notified
                            ? '<span class="badge bg-success"><i class="bi bi-check-circle"></i></span>'
                            : '<span class="badge bg-warning"><i class="bi bi-exclamation-circle"></i></span>'
                        }
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    /**
     * 今後の予定をレンダリング
     */
    renderUpcomingReleases(releases) {
        const container = document.getElementById('upcoming-releases-list');
        if (!container) return;

        if (releases.length === 0) {
            container.innerHTML = `
                <div class="p-4 text-center text-muted">
                    <i class="bi bi-calendar-x fs-1 mb-3 d-block"></i>
                    <p>今後の予定はありません</p>
                </div>
            `;
            return;
        }

        const html = releases.map(release => `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="d-flex align-items-center mb-1">
                            ${release.type === 'anime'
                                ? '<span class="badge bg-primary me-2"><i class="bi bi-tv"></i> アニメ</span>'
                                : '<span class="badge bg-secondary me-2"><i class="bi bi-book"></i> マンガ</span>'
                            }
                            <strong>${this.escapeHtml(release.title_kana || release.title)}</strong>
                        </div>
                        <div class="text-muted small">
                            ${release.release_type === 'episode' ? '第' + release.number + '話' : '第' + release.number + '巻'}
                            · ${this.escapeHtml(release.platform)}
                        </div>
                    </div>
                    <div class="text-end">
                        <small class="text-muted">${release.release_date}</small>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    /**
     * リリース履歴をレンダリング
     */
    renderReleaseHistory(releases) {
        const container = document.getElementById('release-history-list');
        if (!container) return;

        if (releases.length === 0) {
            container.innerHTML = `
                <div class="p-4 text-center text-muted">
                    <i class="bi bi-archive fs-1 mb-3 d-block"></i>
                    <p>リリース履歴はありません</p>
                </div>
            `;
            return;
        }

        const html = releases.map(release => `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="d-flex align-items-center mb-1">
                            ${release.type === 'anime'
                                ? '<span class="badge bg-primary me-2"><i class="bi bi-tv"></i> アニメ</span>'
                                : '<span class="badge bg-secondary me-2"><i class="bi bi-book"></i> マンガ</span>'
                            }
                            <strong>${this.escapeHtml(release.title_kana || release.title)}</strong>
                        </div>
                        <div class="text-muted small">
                            ${release.release_type === 'episode' ? '第' + release.number + '話' : '第' + release.number + '巻'}
                            · ${this.escapeHtml(release.platform)}
                            · ${release.release_date}
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    /**
     * HTMLエスケープ
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// グローバルインスタンス
let dashboardUpdateManager;

// DOM読み込み完了時に初期化
document.addEventListener('DOMContentLoaded', () => {
    dashboardUpdateManager = new DashboardUpdateManager();

    // グローバル関数として公開（既存のコードとの互換性のため）
    window.refreshRecentReleases = () => dashboardUpdateManager.refreshRecentReleases();
    window.refreshUpcomingReleases = () => dashboardUpdateManager.refreshUpcomingReleases();
    window.refreshReleaseHistory = () => dashboardUpdateManager.refreshReleaseHistory();
});
