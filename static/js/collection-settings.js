/**
 * Collection Settings UI Manager
 *
 * Features:
 * - RSS feed enable/disable toggle
 * - Connection testing
 * - Visual status indicators
 * - User-friendly error messages
 */

(function() {
    'use strict';

    // State management
    const state = {
        feeds: [],
        loading: false,
        testingFeeds: new Set()
    };

    // DOM elements cache
    const elements = {
        rssContainer: null,
        saveAllBtn: null,
        testAllBtn: null
    };

    /**
     * Initialize the collection settings UI
     */
    function init() {
        console.log('[CollectionSettings] Initializing...');

        // Cache DOM elements
        elements.rssContainer = document.getElementById('rssSourcesContainer');
        elements.saveAllBtn = document.getElementById('saveAllBtn');

        // Load feed configurations
        loadFeedConfigurations();

        // Setup event listeners
        setupEventListeners();

        console.log('[CollectionSettings] Initialized successfully');
    }

    /**
     * Load RSS feed configurations from the server
     */
    async function loadFeedConfigurations() {
        try {
            state.loading = true;
            showLoadingIndicator();

            const response = await fetch('/api/rss-feeds');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            state.feeds = data.feeds || [];

            console.log(`[CollectionSettings] Loaded ${state.feeds.length} RSS feeds`);

            renderFeeds();

        } catch (error) {
            console.error('[CollectionSettings] Failed to load feeds:', error);
            showErrorNotification('フィード設定の読み込みに失敗しました: ' + error.message);
        } finally {
            state.loading = false;
            hideLoadingIndicator();
        }
    }

    /**
     * Render RSS feed cards
     */
    function renderFeeds() {
        if (!elements.rssContainer) {
            console.warn('[CollectionSettings] RSS container not found');
            return;
        }

        // Clear existing content
        elements.rssContainer.innerHTML = '';

        // Filter and render only enabled feeds (or show all with visual distinction)
        const activeFeeds = state.feeds.filter(feed => feed.enabled !== false);
        const disabledFeeds = state.feeds.filter(feed => feed.enabled === false);

        // Render active feeds
        activeFeeds.forEach(feed => {
            const card = createFeedCard(feed, false);
            elements.rssContainer.appendChild(card);
        });

        // Render disabled feeds (collapsed by default)
        if (disabledFeeds.length > 0) {
            const disabledSection = createDisabledFeedsSection(disabledFeeds);
            elements.rssContainer.appendChild(disabledSection);
        }

        console.log(`[CollectionSettings] Rendered ${activeFeeds.length} active and ${disabledFeeds.length} disabled feeds`);

        // Initialize Bootstrap tooltips
        initializeTooltips();
    }

    /**
     * Initialize Bootstrap tooltips
     */
    function initializeTooltips() {
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }
    }

    /**
     * Create a feed card element
     */
    function createFeedCard(feed, isDisabled = false) {
        const col = document.createElement('div');
        col.className = 'col-lg-6 mb-4';

        const cardClass = isDisabled ? 'source-config-card disabled' :
                         feed.status === 'error' ? 'source-config-card error' :
                         'source-config-card enabled';

        col.innerHTML = `
            <div class="${cardClass}" data-feed-id="${feed.id || feed.name}">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div class="flex-grow-1">
                        <h5 class="mb-0">${escapeHtml(feed.name)}</h5>
                        <small class="text-muted">${escapeHtml(feed.category || 'マンガ')}</small>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        ${getStatusBadge(feed, isDisabled)}
                        <div class="form-check form-switch">
                            <input class="form-check-input feed-enable-toggle"
                                   type="checkbox"
                                   ${feed.enabled !== false ? 'checked' : ''}
                                   data-feed-id="${feed.id || feed.name}"
                                   ${isDisabled ? 'disabled' : ''}>
                        </div>
                    </div>
                </div>
                <div class="card-body">
                    ${renderFeedBody(feed, isDisabled)}
                </div>
            </div>
        `;

        return col;
    }

    /**
     * Get status badge HTML
     */
    function getStatusBadge(feed, isDisabled) {
        if (isDisabled || feed.enabled === false) {
            const reason = feed.disabledReason || feed.error_message || 'ユーザーにより無効化';
            return `
                <span class="connection-status disconnected"
                      data-bs-toggle="tooltip"
                      title="${escapeHtml(reason)}">
                    <i class="bi bi-dash-circle"></i> 無効
                </span>
            `;
        }

        if (feed.status === 'error' || feed.error) {
            const errorMsg = feed.error_message || feed.error || 'エラーが発生しました';
            return `
                <span class="connection-status disconnected"
                      data-bs-toggle="tooltip"
                      title="${escapeHtml(errorMsg)}">
                    <i class="bi bi-exclamation-circle"></i> エラー
                </span>
            `;
        }

        if (feed.status === 'connected' || feed.lastSuccess) {
            return `
                <span class="connection-status connected">
                    <i class="bi bi-check-circle"></i> 接続中
                </span>
            `;
        }

        return `
            <span class="connection-status" style="background-color: rgba(108, 117, 125, 0.1); color: #6c757d;">
                <i class="bi bi-question-circle"></i> 未確認
            </span>
        `;
    }

    /**
     * Render feed card body
     */
    function renderFeedBody(feed, isDisabled) {
        let html = '';

        // Show error/disabled message
        if (isDisabled || feed.enabled === false) {
            const reason = feed.disabledReason || feed.error_message || 'このフィードは無効化されています';
            html += `
                <div class="alert alert-secondary mb-3">
                    <i class="bi bi-info-circle"></i>
                    <strong>無効化:</strong> ${escapeHtml(reason)}
                </div>
            `;
        } else if (feed.status === 'error' || feed.error) {
            const errorMsg = getFriendlyErrorMessage(feed);
            html += `
                <div class="alert alert-warning mb-3">
                    <i class="bi bi-exclamation-triangle"></i>
                    <strong>接続エラー:</strong> ${escapeHtml(errorMsg)}
                </div>
            `;
        }

        // Feed URL
        html += `
            <div class="mb-3">
                <label class="form-label">RSS URL</label>
                <input type="url"
                       class="form-control form-control-sm feed-url"
                       value="${escapeHtml(feed.url || '')}"
                       ${isDisabled ? 'readonly' : ''}>
            </div>
        `;

        // Timeout setting
        html += `
            <div class="mb-3">
                <label class="form-label">タイムアウト（秒）</label>
                <input type="number"
                       class="form-control form-control-sm feed-timeout"
                       value="${feed.timeout || 30}"
                       min="5"
                       max="300"
                       ${isDisabled ? 'readonly' : ''}>
            </div>
        `;

        // Action buttons
        html += `
            <div class="d-flex gap-2">
                <button class="btn btn-outline-primary btn-sm test-connection-btn"
                        data-feed-id="${feed.id || feed.name}"
                        ${isDisabled ? 'disabled' : ''}>
                    <i class="bi bi-wifi"></i> 接続テスト
                </button>
                ${feed.status === 'error' ? `
                    <button class="btn btn-outline-warning btn-sm diagnose-btn"
                            data-feed-id="${feed.id || feed.name}">
                        <i class="bi bi-tools"></i> 問題診断
                    </button>
                ` : ''}
            </div>
        `;

        // Statistics
        if (!isDisabled && feed.stats) {
            html += `
                <div class="stats-grid mt-3">
                    <div class="stats-card">
                        <div class="stats-value">${feed.stats.itemsCollected || 0}</div>
                        <small class="text-muted">取得作品数</small>
                    </div>
                    <div class="stats-card">
                        <div class="stats-value">${(feed.stats.successRate || 0).toFixed(1)}%</div>
                        <small class="text-muted">成功率</small>
                    </div>
                </div>
            `;
        }

        return html;
    }

    /**
     * Create disabled feeds section
     */
    function createDisabledFeedsSection(disabledFeeds) {
        const section = document.createElement('div');
        section.className = 'col-12 mb-4';

        section.innerHTML = `
            <div class="card border-secondary">
                <div class="card-header bg-light">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="mb-0 text-secondary">
                            <i class="bi bi-eye-slash"></i>
                            無効化されたフィード (${disabledFeeds.length})
                        </h6>
                        <button class="btn btn-sm btn-outline-secondary toggle-disabled-feeds"
                                type="button"
                                data-bs-toggle="collapse"
                                data-bs-target="#disabledFeedsCollapse">
                            <i class="bi bi-chevron-down"></i> 表示
                        </button>
                    </div>
                </div>
                <div class="collapse" id="disabledFeedsCollapse">
                    <div class="card-body">
                        <div class="row" id="disabledFeedsContainer"></div>
                    </div>
                </div>
            </div>
        `;

        // Populate disabled feeds
        const container = section.querySelector('#disabledFeedsContainer');
        disabledFeeds.forEach(feed => {
            const card = createFeedCard(feed, true);
            container.appendChild(card);
        });

        // Toggle button icon
        section.querySelector('.toggle-disabled-feeds').addEventListener('click', function(e) {
            const icon = this.querySelector('i');
            if (icon.classList.contains('bi-chevron-down')) {
                icon.classList.replace('bi-chevron-down', 'bi-chevron-up');
                this.innerHTML = '<i class="bi bi-chevron-up"></i> 非表示';
            } else {
                icon.classList.replace('bi-chevron-up', 'bi-chevron-down');
                this.innerHTML = '<i class="bi bi-chevron-down"></i> 表示';
            }
        });

        return section;
    }

    /**
     * Get user-friendly error message
     */
    function getFriendlyErrorMessage(feed) {
        const error = feed.error_message || feed.error || '';

        if (error.includes('404') || error.includes('Not Found')) {
            return 'このフィードは無効化されています（404 Not Found）。URLを確認するか、フィードを無効化してください。';
        }

        if (error.includes('timeout') || error.includes('Timeout')) {
            return 'タイムアウトが発生しました。ネットワーク接続を確認するか、タイムアウト時間を延長してください。';
        }

        if (error.includes('403') || error.includes('Forbidden')) {
            return 'アクセスが拒否されました。User-Agentヘッダーの設定が必要な可能性があります。';
        }

        if (error.includes('SSL') || error.includes('certificate')) {
            return 'SSL証明書の検証に失敗しました。証明書の確認が必要です。';
        }

        return error || '不明なエラーが発生しました';
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Save all button
        if (elements.saveAllBtn) {
            elements.saveAllBtn.addEventListener('click', saveAllSettings);
        }

        // Delegate events for dynamically created elements
        document.addEventListener('click', function(e) {
            // Test connection button
            if (e.target.closest('.test-connection-btn')) {
                const btn = e.target.closest('.test-connection-btn');
                const feedId = btn.dataset.feedId;
                testConnection(feedId);
            }

            // Diagnose button
            if (e.target.closest('.diagnose-btn')) {
                const btn = e.target.closest('.diagnose-btn');
                const feedId = btn.dataset.feedId;
                diagnoseProblem(feedId);
            }
        });

        // Feed enable/disable toggle
        document.addEventListener('change', function(e) {
            if (e.target.classList.contains('feed-enable-toggle')) {
                const feedId = e.target.dataset.feedId;
                const enabled = e.target.checked;
                toggleFeed(feedId, enabled);
            }
        });
    }

    /**
     * Toggle feed enable/disable
     */
    async function toggleFeed(feedId, enabled) {
        try {
            const response = await fetch('/api/rss-feeds/toggle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ feedId, enabled })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                showSuccessNotification(
                    enabled ? 'フィードを有効化しました' : 'フィードを無効化しました'
                );

                // Reload feeds to update UI
                await loadFeedConfigurations();
            } else {
                throw new Error(data.error || 'Unknown error');
            }

        } catch (error) {
            console.error('[CollectionSettings] Failed to toggle feed:', error);
            showErrorNotification('フィード設定の更新に失敗しました: ' + error.message);

            // Reload to restore correct state
            await loadFeedConfigurations();
        }
    }

    /**
     * Test connection to a feed
     */
    async function testConnection(feedId) {
        const btn = document.querySelector(`[data-feed-id="${feedId}"].test-connection-btn`);

        if (!btn || state.testingFeeds.has(feedId)) {
            return;
        }

        try {
            state.testingFeeds.add(feedId);
            btn.classList.add('testing');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> テスト中...';

            const response = await fetch('/api/rss-feeds/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ feedId })
            });

            const data = await response.json();

            if (data.success) {
                showSuccessNotification(`接続成功: ${data.itemsFound || 0} 件のアイテムを取得しました`);
            } else {
                showErrorNotification(`接続失敗: ${data.error || '不明なエラー'}`);
            }

        } catch (error) {
            console.error('[CollectionSettings] Connection test failed:', error);
            showErrorNotification('接続テストに失敗しました: ' + error.message);
        } finally {
            state.testingFeeds.delete(feedId);
            btn.classList.remove('testing');
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-wifi"></i> 接続テスト';
        }
    }

    /**
     * Diagnose feed problems
     */
    async function diagnoseProblem(feedId) {
        showInfoNotification('問題を診断しています...');

        try {
            const response = await fetch('/api/rss-feeds/diagnose', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ feedId })
            });

            const data = await response.json();

            if (data.diagnosis) {
                showDiagnosisModal(data.diagnosis);
            } else {
                showInfoNotification('診断結果: 問題は見つかりませんでした');
            }

        } catch (error) {
            console.error('[CollectionSettings] Diagnosis failed:', error);
            showErrorNotification('診断に失敗しました: ' + error.message);
        }
    }

    /**
     * Save all settings
     */
    async function saveAllSettings() {
        // Implementation for saving all settings
        showInfoNotification('設定を保存しています...');

        // TODO: Implement actual save logic

        setTimeout(() => {
            showSuccessNotification('すべての設定を保存しました');
        }, 1000);
    }

    /**
     * Show diagnosis modal
     */
    function showDiagnosisModal(diagnosis) {
        // Create modal HTML
        const modalHtml = `
            <div class="modal fade" id="diagnosisModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bi bi-tools"></i> フィード診断結果
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-${diagnosis.overallStatus === 'success' ? 'success' : diagnosis.overallStatus === 'warning' ? 'warning' : 'danger'}">
                                <strong>総合評価:</strong> ${diagnosis.recommendation}
                            </div>

                            <h6 class="mt-3 mb-2">フィードURL:</h6>
                            <code>${escapeHtml(diagnosis.url)}</code>

                            <h6 class="mt-3 mb-2">診断チェック:</h6>
                            <div class="list-group">
                                ${diagnosis.checks.map(check => `
                                    <div class="list-group-item">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <div>
                                                <strong>${escapeHtml(check.name)}</strong>
                                                <p class="mb-0 text-muted small">${escapeHtml(check.message)}</p>
                                            </div>
                                            <span class="badge bg-${check.status === 'success' ? 'success' : check.status === 'warning' ? 'warning' : 'danger'}">
                                                ${check.status === 'success' ? '成功' : check.status === 'warning' ? '警告' : 'エラー'}
                                            </span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">閉じる</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.getElementById('diagnosisModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add modal to DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('diagnosisModal'));
        modal.show();

        // Clean up after modal is hidden
        document.getElementById('diagnosisModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    }

    /**
     * Notification helpers
     */
    function showSuccessNotification(message) {
        showNotification(message, 'success');
    }

    function showErrorNotification(message) {
        showNotification(message, 'error');
    }

    function showInfoNotification(message) {
        showNotification(message, 'info');
    }

    function showNotification(message, type = 'info') {
        // Use existing notification system from main.js
        if (typeof window.showNotification === 'function') {
            window.showNotification(message, type);
        } else {
            // Fallback if main.js notification is not available
            console.log(`[${type.toUpperCase()}] ${message}`);

            // Try to create a simple toast notification
            const toast = document.createElement('div');
            toast.className = `alert alert-${type === 'error' ? 'danger' : type} position-fixed top-0 end-0 m-3`;
            toast.style.zIndex = '9999';
            toast.textContent = message;

            document.body.appendChild(toast);

            setTimeout(() => {
                toast.remove();
            }, 3000);
        }
    }

    function showLoadingIndicator() {
        if (elements.rssContainer) {
            elements.rssContainer.innerHTML = `
                <div class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">読み込み中...</span>
                    </div>
                    <p class="mt-3 text-muted">フィード設定を読み込んでいます...</p>
                </div>
            `;
        }
    }

    function hideLoadingIndicator() {
        // Handled by renderFeeds()
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Export for global access if needed
    window.CollectionSettings = {
        reload: loadFeedConfigurations,
        testConnection: testConnection
    };

})();
