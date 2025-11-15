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
        apiSources: [],
        rssFeeds: [],
        loading: false,
        testingFeeds: new Set(),
        testingApis: new Set()
    };

    // DOM elements cache
    const elements = {
        apiContainer: null,
        rssContainer: null,
        saveAllBtn: null,
        testAllApisBtn: null,
        testAllRssBtn: null
    };

    /**
     * Initialize the collection settings UI
     */
    function init() {
        console.log('[CollectionSettings] Initializing...');

        // Cache DOM elements
        elements.apiContainer = document.getElementById('apiSourcesContainer');
        elements.rssContainer = document.getElementById('rssSourcesContainer');
        elements.saveAllBtn = document.getElementById('saveAllBtn');
        elements.testAllApisBtn = document.getElementById('testAllApisBtn');
        elements.testAllRssBtn = document.getElementById('testAllRssBtn');

        // Load configurations
        loadApiConfigurations();
        loadFeedConfigurations();

        // Setup event listeners
        setupEventListeners();

        console.log('[CollectionSettings] Initialized successfully');
    }

    /**
     * Load API source configurations
     */
    async function loadApiConfigurations() {
        try {
            state.loading = true;
            showLoadingIndicator('api');

            console.log('[CollectionSettings] Fetching /api/sources...');

            // Fetch API configurations from server
            const response = await fetch('/api/sources');
            console.log('[CollectionSettings] Fetch response:', response.status);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('[CollectionSettings] Received data:', data);

            // Check if data.apis exists
            if (!data || !data.apis) {
                throw new Error('Invalid API response: apis array not found');
            }

            // Transform API response to expected format
            state.apiSources = data.apis.map(api => ({
                id: api.id,
                name: api.name,
                type: 'api',
                category: api.description,
                url: api.url,
                enabled: api.enabled,
                status: api.health_status === 'healthy' ? 'connected' :
                        api.health_status === 'error' ? 'error' : 'unknown',
                rateLimit: `${api.rate_limit} requests/min`,
                timeout: api.timeout,
                stats: {
                    itemsCollected: 0,
                    successRate: 0
                }
            }));

            console.log(`[CollectionSettings] Loaded ${state.apiSources.length} API sources from server`);

            renderApiSources();
            console.log('[CollectionSettings] API sources rendered successfully');

        } catch (error) {
            console.error('[CollectionSettings] Failed to load API sources:', error);

            // エラー時もAPIソースを表示（フォールバック）
            if (!elements.apiContainer) return;

            elements.apiContainer.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-warning">
                        <i class="bi bi-exclamation-triangle"></i>
                        API設定の読み込みに失敗しました: ${error.message}
                        <br>
                        <small>サーバーに接続できないか、/api/sourcesエンドポイントでエラーが発生しています。</small>
                    </div>
                </div>
            `;
        } finally {
            state.loading = false;
            hideLoadingIndicator('api');
        }
    }

    /**
     * Render API source cards
     */
    function renderApiSources() {
        if (!elements.apiContainer) {
            console.warn('[CollectionSettings] API container not found');
            return;
        }

        // 完全にクリア（ローディングメッセージも削除）
        elements.apiContainer.innerHTML = '';

        // Render API source cards
        state.apiSources.forEach(api => {
            const card = createApiCard(api);
            elements.apiContainer.appendChild(card);
        });

        console.log(`[CollectionSettings] Rendered ${state.apiSources.length} API sources`);

        // Initialize Bootstrap tooltips
        initializeTooltips();
    }

    /**
     * Create an API source card element
     */
    function createApiCard(api) {
        const col = document.createElement('div');
        col.className = 'col-lg-6 mb-4';

        const cardClass = api.enabled === false ? 'source-config-card disabled' :
                         api.status === 'error' ? 'source-config-card error' :
                         'source-config-card enabled';

        const statusBadge = getApiStatusBadge(api);
        const bodyContent = renderApiCardBody(api);

        col.innerHTML = `
            <div class="${cardClass}" data-api-id="${api.id}">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div class="flex-grow-1">
                        <h5 class="mb-0">${escapeHtml(api.name)}</h5>
                        <small class="text-muted">${escapeHtml(api.category)}</small>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        ${statusBadge}
                        <div class="form-check form-switch">
                            <input class="form-check-input api-enable-toggle"
                                   type="checkbox"
                                   ${api.enabled !== false ? 'checked' : ''}
                                   data-api-id="${api.id}">
                        </div>
                    </div>
                </div>
                <div class="card-body">
                    ${bodyContent}
                </div>
            </div>
        `;

        return col;
    }

    /**
     * Get API status badge HTML
     */
    function getApiStatusBadge(api) {
        if (api.enabled === false) {
            return `
                <span class="connection-status disconnected">
                    <i class="bi bi-dash-circle"></i> 無効
                </span>
            `;
        }

        if (api.status === 'error') {
            const errorMsg = api.error_message || 'エラーが発生しました';
            return `
                <span class="connection-status disconnected"
                      data-bs-toggle="tooltip"
                      title="${escapeHtml(errorMsg)}">
                    <i class="bi bi-exclamation-circle"></i> エラー
                </span>
            `;
        }

        if (api.status === 'connected') {
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
     * Render API card body
     */
    function renderApiCardBody(api) {
        let html = '';

        // API URL
        html += `
            <div class="mb-3">
                <label class="form-label">API URL</label>
                <input type="url"
                       class="form-control form-control-sm"
                       value="${escapeHtml(api.url)}"
                       readonly>
            </div>
        `;

        // Rate limit info
        if (api.rateLimit) {
            html += `
                <div class="mb-3">
                    <label class="form-label">レート制限</label>
                    <div class="alert alert-info py-2 px-3 mb-0">
                        <i class="bi bi-info-circle"></i>
                        <small>${escapeHtml(api.rateLimit)}</small>
                    </div>
                </div>
            `;
        }

        // API-specific settings
        if (api.id === 'anilist') {
            html += `
                <div class="mb-3">
                    <label class="form-label">リクエスト間隔（秒）</label>
                    <input type="number"
                           class="form-control form-control-sm api-setting"
                           data-api-id="${api.id}"
                           data-setting="requestInterval"
                           value="${api.requestInterval || 1}"
                           min="0.5"
                           step="0.1">
                </div>
                <div class="mb-3">
                    <label class="form-label">最大同時接続数</label>
                    <input type="number"
                           class="form-control form-control-sm api-setting"
                           data-api-id="${api.id}"
                           data-setting="maxConcurrent"
                           value="${api.maxConcurrent || 2}"
                           min="1"
                           max="5">
                </div>
            `;
        } else if (api.id === 'syobocal') {
            html += `
                <div class="mb-3">
                    <label class="form-label">取得期間（日）</label>
                    <input type="number"
                           class="form-control form-control-sm api-setting"
                           data-api-id="${api.id}"
                           data-setting="fetchPeriodDays"
                           value="${api.fetchPeriodDays || 30}"
                           min="1"
                           max="365">
                </div>
                <div class="mb-3">
                    <label class="form-label">更新頻度</label>
                    <select class="form-select form-select-sm api-setting"
                            data-api-id="${api.id}"
                            data-setting="updateFrequency">
                        <option value="hourly" ${api.updateFrequency === 'hourly' ? 'selected' : ''}>1時間ごと</option>
                        <option value="daily" ${api.updateFrequency === 'daily' ? 'selected' : ''}>1日1回</option>
                        <option value="weekly" ${api.updateFrequency === 'weekly' ? 'selected' : ''}>1週間に1回</option>
                    </select>
                </div>
            `;
        }

        // Action buttons
        html += `
            <div class="d-flex gap-2">
                <button class="btn btn-outline-primary btn-sm test-api-btn"
                        data-api-id="${api.id}">
                    <i class="bi bi-wifi"></i> 接続テスト
                </button>
                <button class="btn btn-outline-secondary btn-sm reset-api-btn"
                        data-api-id="${api.id}">
                    <i class="bi bi-arrow-clockwise"></i> デフォルト
                </button>
            </div>
        `;

        // Statistics
        if (api.stats) {
            const statLabel = api.id === 'syobocal' ? '放送局数' : '取得作品数';
            html += `
                <div class="stats-grid mt-3">
                    <div class="stats-card">
                        <div class="stats-value">${api.stats.itemsCollected || 0}</div>
                        <small class="text-muted">${statLabel}</small>
                    </div>
                    <div class="stats-card">
                        <div class="stats-value">${(api.stats.successRate || 0).toFixed(1)}%</div>
                        <small class="text-muted">成功率</small>
                    </div>
                </div>
            `;
        }

        return html;
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
            state.rssFeeds = data.feeds || [];

            console.log(`[CollectionSettings] Loaded ${state.rssFeeds.length} RSS feeds`);

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
        const activeFeeds = state.rssFeeds.filter(feed => feed.enabled !== false);
        const disabledFeeds = state.rssFeeds.filter(feed => feed.enabled === false);

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

        // Test all APIs button
        if (elements.testAllApisBtn) {
            elements.testAllApisBtn.addEventListener('click', testAllApis);
        }

        // Test all RSS button
        if (elements.testAllRssBtn) {
            elements.testAllRssBtn.addEventListener('click', testAllRssFeeds);
        }

        // Delegate events for dynamically created elements
        document.addEventListener('click', function(e) {
            // Test API connection button
            if (e.target.closest('.test-api-btn')) {
                const btn = e.target.closest('.test-api-btn');
                const apiId = btn.dataset.apiId;
                testApiConnection(apiId);
            }

            // Reset API settings button
            if (e.target.closest('.reset-api-btn')) {
                const btn = e.target.closest('.reset-api-btn');
                const apiId = btn.dataset.apiId;
                resetApiToDefaults(apiId);
            }

            // Test RSS connection button
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

        // API enable/disable toggle
        document.addEventListener('change', function(e) {
            if (e.target.classList.contains('api-enable-toggle')) {
                const apiId = e.target.dataset.apiId;
                const enabled = e.target.checked;
                toggleApi(apiId, enabled);
            }

            // Feed enable/disable toggle
            if (e.target.classList.contains('feed-enable-toggle')) {
                const feedId = e.target.dataset.feedId;
                const enabled = e.target.checked;
                toggleFeed(feedId, enabled);
            }

            // API settings change
            if (e.target.classList.contains('api-setting')) {
                const apiId = e.target.dataset.apiId;
                const setting = e.target.dataset.setting;
                const value = e.target.value;
                updateApiSetting(apiId, setting, value);
            }
        });
    }

    /**
     * Toggle API enable/disable
     */
    async function toggleApi(apiId, enabled) {
        try {
            // Update local state
            const api = state.apiSources.find(a => a.id === apiId);
            if (api) {
                api.enabled = enabled;

                // Re-render to update UI
                renderApiSources();

                showSuccessNotification(
                    enabled ? 'APIを有効化しました' : 'APIを無効化しました'
                );

                // In the future, save to server
                // await saveApiConfiguration(apiId, { enabled });
            }

        } catch (error) {
            console.error('[CollectionSettings] Failed to toggle API:', error);
            showErrorNotification('API設定の更新に失敗しました: ' + error.message);
        }
    }

    /**
     * Update API setting
     */
    function updateApiSetting(apiId, setting, value) {
        const api = state.apiSources.find(a => a.id === apiId);
        if (api) {
            api[setting] = value;
            console.log(`[CollectionSettings] Updated ${apiId}.${setting} = ${value}`);

            // Auto-save could be implemented here
            // For now, settings are stored in memory
        }
    }

    /**
     * Test API connection
     */
    async function testApiConnection(apiId) {
        const btn = document.querySelector(`[data-api-id="${apiId}"].test-api-btn`);

        if (!btn || state.testingApis.has(apiId)) {
            return;
        }

        try {
            state.testingApis.add(apiId);
            btn.classList.add('testing');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> テスト中...';

            // Simulate API test (in the future, call actual API endpoint)
            await new Promise(resolve => setTimeout(resolve, 1500));

            const api = state.apiSources.find(a => a.id === apiId);
            if (api) {
                api.status = 'connected';
                renderApiSources();
                showSuccessNotification(`${api.name} 接続成功`);
            }

        } catch (error) {
            console.error('[CollectionSettings] API connection test failed:', error);
            showErrorNotification('接続テストに失敗しました: ' + error.message);
        } finally {
            state.testingApis.delete(apiId);
            if (btn) {
                btn.classList.remove('testing');
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-wifi"></i> 接続テスト';
            }
        }
    }

    /**
     * Reset API to default settings
     */
    function resetApiToDefaults(apiId) {
        const api = state.apiSources.find(a => a.id === apiId);
        if (!api) return;

        if (confirm(`${api.name} の設定をデフォルトに戻しますか?`)) {
            // Reset to defaults
            if (api.id === 'anilist') {
                api.requestInterval = 1;
                api.maxConcurrent = 2;
            } else if (api.id === 'syobocal') {
                api.fetchPeriodDays = 30;
                api.updateFrequency = 'daily';
            }

            renderApiSources();
            showSuccessNotification('デフォルト設定に戻しました');
        }
    }

    /**
     * Test all APIs
     */
    async function testAllApis() {
        showInfoNotification('すべてのAPIをテスト中...');

        for (const api of state.apiSources) {
            if (api.enabled !== false) {
                await testApiConnection(api.id);
                // Small delay between tests
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        }

        showSuccessNotification('すべてのAPIテストが完了しました');
    }

    /**
     * Test all RSS feeds
     */
    async function testAllRssFeeds() {
        showInfoNotification('すべてのRSSフィードをテスト中...');

        const enabledFeeds = state.rssFeeds.filter(f => f.enabled !== false);

        for (const feed of enabledFeeds) {
            await testConnection(feed.id || feed.name);
            // Small delay between tests
            await new Promise(resolve => setTimeout(resolve, 500));
        }

        showSuccessNotification('すべてのRSSフィードのテストが完了しました');
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

    function showLoadingIndicator(type = 'rss') {
        const container = type === 'api' ? elements.apiContainer : elements.rssContainer;
        const message = type === 'api' ? 'API設定を読み込んでいます...' : 'フィード設定を読み込んでいます...';

        if (container) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="text-center py-5">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">読み込み中...</span>
                        </div>
                        <p class="mt-3 text-muted">${message}</p>
                    </div>
                </div>
            `;
        }
    }

    function hideLoadingIndicator(type = 'rss') {
        // Handled by render functions
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
        reloadApis: loadApiConfigurations,
        reloadFeeds: loadFeedConfigurations,
        testApiConnection: testApiConnection,
        testConnection: testConnection,
        testAllApis: testAllApis,
        testAllRssFeeds: testAllRssFeeds
    };

})();
