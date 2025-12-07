/**
 * ウォッチリスト機能のフロントエンドスクリプト
 * 作成日: 2025-12-07
 */

class WatchlistManager {
    constructor() {
        this.watchlistCache = new Set();
        this.init();
    }

    /**
     * 初期化
     */
    init() {
        this.loadWatchlistStatus();
        this.attachEventHandlers();
    }

    /**
     * ウォッチリスト状態を一括取得
     */
    async loadWatchlistStatus() {
        try {
            const response = await fetch('/watchlist/api/list');
            const data = await response.json();

            if (data.success) {
                this.watchlistCache.clear();
                data.watchlist.forEach(item => {
                    this.watchlistCache.add(item.work_id);
                });
                this.updateAllButtons();
            }
        } catch (error) {
            console.error('ウォッチリスト状態の取得に失敗:', error);
        }
    }

    /**
     * イベントハンドラを設定
     */
    attachEventHandlers() {
        // ウォッチリストボタンのクリックイベント
        $(document).on('click', '.watchlist-btn', (e) => {
            e.preventDefault();
            const button = $(e.currentTarget);
            const workId = button.data('work-id');
            this.toggleWatchlist(workId, button);
        });

        // ページロード時にボタンを更新
        this.updateAllButtons();
    }

    /**
     * ウォッチリストのトグル
     */
    async toggleWatchlist(workId, button) {
        const inWatchlist = this.watchlistCache.has(workId);

        // ボタンを無効化
        button.prop('disabled', true);

        try {
            if (inWatchlist) {
                await this.removeFromWatchlist(workId, button);
            } else {
                await this.addToWatchlist(workId, button);
            }
        } catch (error) {
            console.error('ウォッチリスト操作エラー:', error);
            this.showToast('error', 'エラーが発生しました');
        } finally {
            button.prop('disabled', false);
        }
    }

    /**
     * ウォッチリストに追加
     */
    async addToWatchlist(workId, button) {
        try {
            const response = await fetch('/watchlist/api/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ work_id: workId })
            });

            const data = await response.json();

            if (data.success) {
                this.watchlistCache.add(workId);
                this.updateButton(button, true);
                this.showToast('success', data.message);
                this.updateWatchlistCount(1);
            } else {
                this.showToast('error', data.error);
            }
        } catch (error) {
            throw error;
        }
    }

    /**
     * ウォッチリストから削除
     */
    async removeFromWatchlist(workId, button) {
        try {
            const response = await fetch(`/watchlist/api/remove/${workId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                this.watchlistCache.delete(workId);
                this.updateButton(button, false);
                this.showToast('success', data.message);
                this.updateWatchlistCount(-1);
            } else {
                this.showToast('error', data.error);
            }
        } catch (error) {
            throw error;
        }
    }

    /**
     * 単一ボタンの状態を更新
     */
    updateButton(button, inWatchlist) {
        const icon = button.find('i');
        const text = button.find('.btn-text');

        if (inWatchlist) {
            button.removeClass('btn-outline-warning').addClass('btn-warning');
            icon.removeClass('bi-star').addClass('bi-star-fill');
            if (text.length) {
                text.text('お気に入り登録済み');
            }
            button.attr('title', 'ウォッチリストから削除');
        } else {
            button.removeClass('btn-warning').addClass('btn-outline-warning');
            icon.removeClass('bi-star-fill').addClass('bi-star');
            if (text.length) {
                text.text('お気に入りに追加');
            }
            button.attr('title', 'ウォッチリストに追加');
        }
    }

    /**
     * 全ボタンの状態を更新
     */
    updateAllButtons() {
        $('.watchlist-btn').each((index, element) => {
            const button = $(element);
            const workId = button.data('work-id');
            const inWatchlist = this.watchlistCache.has(workId);
            this.updateButton(button, inWatchlist);
        });
    }

    /**
     * ウォッチリストカウントを更新
     */
    updateWatchlistCount(delta) {
        const countBadge = $('#watchlistCount');
        if (countBadge.length) {
            const currentCount = parseInt(countBadge.text()) || 0;
            const newCount = Math.max(0, currentCount + delta);
            countBadge.text(newCount);

            // アニメーション効果
            countBadge.addClass('pulse');
            setTimeout(() => countBadge.removeClass('pulse'), 500);
        }
    }

    /**
     * トースト通知を表示
     */
    showToast(type, message) {
        const bgClass = type === 'success' ? 'bg-success' : 'bg-danger';
        const icon = type === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle';

        const toast = $(`
            <div class="toast align-items-center text-white ${bgClass} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi ${icon}"></i> ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `);

        let container = $('.toast-container');
        if (container.length === 0) {
            container = $('<div class="toast-container position-fixed top-0 end-0 p-3"></div>');
            $('body').append(container);
        }

        container.append(toast);
        const bsToast = new bootstrap.Toast(toast[0]);
        bsToast.show();

        toast.on('hidden.bs.toast', function() {
            $(this).remove();
        });
    }

    /**
     * 特定作品のウォッチリスト状態を確認
     */
    async checkStatus(workId) {
        try {
            const response = await fetch(`/watchlist/api/check/${workId}`);
            const data = await response.json();

            if (data.success) {
                return data.in_watchlist;
            }
            return false;
        } catch (error) {
            console.error('ウォッチリスト状態確認エラー:', error);
            return false;
        }
    }
}

// グローバルインスタンス
let watchlistManager;

// ページロード時に初期化
$(document).ready(function() {
    watchlistManager = new WatchlistManager();

    // CSSアニメーションを追加
    if (!$('#watchlist-styles').length) {
        $('head').append(`
            <style id="watchlist-styles">
                .pulse {
                    animation: pulse 0.5s ease-in-out;
                }

                @keyframes pulse {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.2); }
                }

                .watchlist-btn {
                    transition: all 0.3s ease;
                }

                .watchlist-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }

                .watchlist-btn i {
                    transition: all 0.2s ease;
                }

                .watchlist-btn:hover i {
                    transform: scale(1.2);
                }
            </style>
        `);
    }
});
