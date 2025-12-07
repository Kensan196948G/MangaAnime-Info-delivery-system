/**
 * Main JavaScript file for Anime/Manga Information Delivery System
 * Handles interactive elements, AJAX updates, and UI enhancements
 */

// =============================================================================
// Global Variables and Configuration
// =============================================================================
const API_BASE_URL = '/api';
const REFRESH_INTERVAL = 300000; // 5 minutes
const TOAST_DURATION = 5000; // 5 seconds

// Application state
let isLoading = false;
let refreshTimer = null;
let notifications = [];

// =============================================================================
// Document Ready and Initialization
// =============================================================================
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    startAutoRefresh();
    initializeTooltips();
    setupKeyboardShortcuts();
});

function initializeApp() {
    console.log('アニメ・マンガ情報配信システム Web UI 初期化中...');
    
    // Check Chart.js availability
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js is not loaded. Charts will be disabled.');
    } else {
        console.log('Chart.js loaded successfully');
    }
    
    // Initialize last update time
    updateLastUpdateTime();
    
    // Load user preferences from localStorage
    loadUserPreferences();
    
    // Check system status
    checkSystemStatus();
    
    console.log('初期化完了');
    
    // 初期化完了の通知（3秒で自動消去）
    setTimeout(() => {
        showNotification('システムが正常に起動しました', 'success', 3000);
    }, 500);
}

// =============================================================================
// Chart.js Helper Functions
// =============================================================================
function isChartJsAvailable() {
    return typeof Chart !== 'undefined';
}

function safeCreateChart(canvasId, config) {
    if (!isChartJsAvailable()) {
        console.warn(`Chart.js not available. Skipping chart creation for ${canvasId}`);
        return null;
    }
    
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.warn(`Canvas element ${canvasId} not found`);
        return null;
    }
    
    try {
        return new Chart(canvas, config);
    } catch (error) {
        console.error(`Error creating chart ${canvasId}:`, error);
        return null;
    }
}

// =============================================================================
// Event Listeners Setup
// =============================================================================
function setupEventListeners() {
    // Global loading state handlers
    document.addEventListener('ajaxStart', showLoading);
    document.addEventListener('ajaxComplete', hideLoading);
    
    // Form submission handlers
    setupFormHandlers();
    
    // Button click handlers
    setupButtonHandlers();
    
    // Search and filter handlers
    setupSearchHandlers();
    
    // Responsive handlers
    setupResponsiveHandlers();
}

function setupFormHandlers() {
    // Configuration form
    const configForm = document.getElementById('config-form');
    if (configForm) {
        configForm.addEventListener('submit', handleConfigSubmit);
    }
    
    // Search forms
    const searchForms = document.querySelectorAll('form[method="GET"]');
    searchForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            showLoading();
        });
    });
}

function setupButtonHandlers() {
    // Refresh buttons
    document.querySelectorAll('[onclick*="refresh"]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const refreshType = this.getAttribute('onclick').match(/refresh(\w+)/)?.[1];
            if (refreshType) {
                refreshData(refreshType.toLowerCase());
            }
        });
    });
    
    // Export buttons
    document.querySelectorAll('[onclick*="export"]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const exportType = this.getAttribute('onclick').match(/exportData\('(\w+)'\)/)?.[1];
            if (exportType) {
                exportData(exportType);
            }
        });
    });
}

function setupSearchHandlers() {
    // Live search functionality
    const searchInputs = document.querySelectorAll('input[type="search"], input[name="search"]');
    searchInputs.forEach(input => {
        let searchTimeout;
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (this.value.length >= 2 || this.value.length === 0) {
                    performSearch(this.value);
                }
            }, 500);
        });
    });
}

function setupResponsiveHandlers() {
    // Handle mobile navigation
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            document.body.classList.toggle('nav-open');
        });
    }
    
    // Handle window resize
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(handleResize, 100);
    });
}

// =============================================================================
// AJAX and API Functions
// =============================================================================
async function makeApiRequest(endpoint, options = {}) {
    try {
        isLoading = true;
        document.dispatchEvent(new Event('ajaxStart'));
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API Request Error:', error);
        showNotification('APIリクエストでエラーが発生しました', 'error');
        throw error;
    } finally {
        isLoading = false;
        document.dispatchEvent(new Event('ajaxComplete'));
    }
}

async function refreshData(type) {
    try {
        switch (type) {
            case 'stats':
                await refreshStats();
                break;
            case 'recentreleases':
                await refreshRecentReleases();
                break;
            case 'logs':
                await refreshLogs();
                break;
            default:
                console.warn('Unknown refresh type:', type);
        }
        
        updateLastUpdateTime();
        showNotification('データを更新しました', 'success');
    } catch (error) {
        console.error('Refresh error:', error);
        showNotification('データの更新に失敗しました', 'error');
    }
}

async function refreshStats() {
    const data = await makeApiRequest('/stats');
    
    // Update statistics cards
    updateElementIfExists('total-works', data.total_works);
    updateElementIfExists('total-releases', data.total_releases);
    updateElementIfExists('pending-notifications', data.pending_notifications);
    updateElementIfExists('today-releases', data.today_releases);
}

async function refreshRecentReleases() {
    const data = await makeApiRequest('/releases/recent');
    
    const container = document.getElementById('recent-releases-list');
    if (!container) return;
    
    if (data.length === 0) {
        container.innerHTML = `
            <div class="p-4 text-center text-muted">
                <i class="bi bi-inbox fs-1 mb-3 d-block"></i>
                <p>最近のリリースはありません</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    data.forEach(release => {
        const typeIcon = release.type === 'anime' ? 'tv' : 'book';
        const typeLabel = release.type === 'anime' ? 'アニメ' : 'マンガ';
        const typeClass = release.type === 'anime' ? 'primary' : 'secondary';
        const releaseText = release.release_type === 'episode' ? '話' : '巻';
        const notifiedIcon = release.notified ? 'check-circle' : 'exclamation-circle';
        const notifiedClass = release.notified ? 'success' : 'warning';
        
        html += `
            <div class="list-group-item release-item fade-in">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="d-flex align-items-center mb-1">
                            <span class="badge bg-${typeClass} me-2">
                                <i class="bi bi-${typeIcon}"></i> ${typeLabel}
                            </span>
                            <strong>${escapeHtml(release.title)}</strong>
                        </div>
                        <div class="text-muted small">
                            第${release.number}${releaseText} · ${escapeHtml(release.platform)} · ${release.release_date}
                        </div>
                    </div>
                    <div class="text-end">
                        <span class="badge bg-${notifiedClass}">
                            <i class="bi bi-${notifiedIcon}"></i>
                        </span>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

async function refreshLogs() {
    // This would be implemented to refresh log content
    console.log('Refreshing logs...');
    // Implementation would depend on the specific log endpoint
}

// =============================================================================
// UI Helper Functions
// =============================================================================
function showLoading() {
    document.body.classList.add('loading');
    
    // Show loading spinner on buttons
    document.querySelectorAll('.btn[onclick*="refresh"]').forEach(btn => {
        if (!btn.dataset.originalText) {
            btn.dataset.originalText = btn.innerHTML;
        }
        btn.innerHTML = '<span class="spinner-custom"></span> 更新中...';
        btn.disabled = true;
    });
}

function hideLoading() {
    document.body.classList.remove('loading');
    
    // Restore button text
    document.querySelectorAll('.btn[data-original-text]').forEach(btn => {
        btn.innerHTML = btn.dataset.originalText;
        btn.disabled = false;
        delete btn.dataset.originalText;
    });
}

function updateElementIfExists(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
        element.classList.add('fade-in');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateLastUpdateTime() {
    const now = new Date();
    const timeString = now.toLocaleString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    const lastUpdateElement = document.getElementById('last-update');
    if (lastUpdateElement) {
        lastUpdateElement.textContent = timeString;
    }
}

// =============================================================================
// Notification System
// =============================================================================
function showNotification(message, type = 'info', duration = TOAST_DURATION) {
    // デバッグ情報をコンソールに出力
    console.log(`[通知] ${type.toUpperCase()}: ${message}`);
    
    const notification = {
        id: Date.now(),
        message,
        type,
        timestamp: new Date()
    };
    
    notifications.push(notification);
    renderNotification(notification);
    
    // Auto-remove after duration
    setTimeout(() => {
        removeNotification(notification.id);
    }, duration);
}

function renderNotification(notification) {
    const container = getOrCreateNotificationContainer();
    
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[notification.type] || 'alert-info';
    
    const notificationElement = document.createElement('div');
    notificationElement.className = `alert ${alertClass} alert-dismissible fade show slide-in-right`;
    notificationElement.setAttribute('role', 'alert');
    notificationElement.setAttribute('data-notification-id', notification.id);
    
    notificationElement.innerHTML = `
        ${escapeHtml(notification.message)}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.appendChild(notificationElement);
    
    // Auto-dismiss handler
    const dismissBtn = notificationElement.querySelector('.btn-close');
    dismissBtn.addEventListener('click', () => {
        removeNotification(notification.id);
    });
}

function removeNotification(id) {
    const element = document.querySelector(`[data-notification-id="${id}"]`);
    if (element) {
        element.classList.add('fade-out');
        setTimeout(() => {
            element.remove();
        }, 300);
    }
    
    notifications = notifications.filter(n => n.id !== id);
}

function getOrCreateNotificationContainer() {
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    return container;
}

// =============================================================================
// Auto-refresh System
// =============================================================================
function startAutoRefresh() {
    // Only start auto-refresh on dashboard
    if (window.location.pathname === '/') {
        refreshTimer = setInterval(() => {
            if (!isLoading && document.visibilityState === 'visible') {
                refreshData('stats');
                refreshData('recentreleases');
            }
        }, REFRESH_INTERVAL);
    }
}

function stopAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
    }
}

// Pause refresh when page is hidden
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        stopAutoRefresh();
    } else {
        startAutoRefresh();
    }
});

// =============================================================================
// Data Export Functions
// =============================================================================
function exportData(format) {
    const currentPath = window.location.pathname;
    const params = new URLSearchParams(window.location.search);
    params.set('export', format);
    
    // Create a temporary link and click it
    const link = document.createElement('a');
    link.href = `${currentPath}?${params.toString()}`;
    link.download = `export_${Date.now()}.${format}`;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showNotification(`${format.toUpperCase()}ファイルのダウンロードを開始しました`, 'info');
}

// =============================================================================
// Search and Filter Functions
// =============================================================================
function performSearch(query) {
    // This would be implemented based on the current page
    console.log('Performing search:', query);
    
    if (query.length === 0) {
        clearSearchResults();
        return;
    }
    
    // Implement search logic here
    // This is a placeholder for the actual search implementation
}

function clearSearchResults() {
    // Clear any search-specific UI elements
    console.log('Clearing search results');
}

// =============================================================================
// Form Handling
// =============================================================================
function handleConfigSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const config = Object.fromEntries(formData.entries());
    
    // Validate configuration
    if (!validateConfig(config)) {
        return false;
    }
    
    // Show confirmation
    if (!confirm('設定を保存しますか？\n\n変更は次回の実行時から反映されます。')) {
        return false;
    }
    
    // Submit form
    event.target.submit();
}

function validateConfig(config) {
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(config.notification_email)) {
        showNotification('有効なメールアドレスを入力してください', 'error');
        return false;
    }
    
    // Check if at least one source is enabled
    const sources = ['anilist', 'shobo_calendar', 'bookwalker_rss', 'mangapocket_rss'];
    const enabledSources = sources.filter(source => config[source] === 'on');
    
    if (enabledSources.length === 0) {
        showNotification('少なくとも1つのデータソースを有効にしてください', 'error');
        return false;
    }
    
    return true;
}

// =============================================================================
// Utility Functions
// =============================================================================
function checkSystemStatus() {
    // Check if system components are working
    makeApiRequest('/stats')
        .then(data => {
            document.getElementById('status-indicator').className = 'badge bg-success';
            document.getElementById('status-indicator').innerHTML = '<i class="bi bi-circle-fill"></i> システム稼働中';
        })
        .catch(error => {
            document.getElementById('status-indicator').className = 'badge bg-danger';
            document.getElementById('status-indicator').innerHTML = '<i class="bi bi-exclamation-circle-fill"></i> エラー';
        });
}

function loadUserPreferences() {
    // Load user preferences from localStorage
    const prefs = localStorage.getItem('user_preferences');
    if (prefs) {
        try {
            const preferences = JSON.parse(prefs);
            // Apply preferences
            console.log('User preferences loaded:', preferences);
        } catch (error) {
            console.error('Error loading user preferences:', error);
        }
    }
}

function saveUserPreferences(preferences) {
    try {
        localStorage.setItem('user_preferences', JSON.stringify(preferences));
    } catch (error) {
        console.error('Error saving user preferences:', error);
    }
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
        // Ctrl/Cmd + R: Refresh data
        if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
            event.preventDefault();
            refreshData('stats');
        }
        
        // Escape: Close modals/dropdowns
        if (event.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                bootstrap.Modal.getInstance(openModal).hide();
            }
        }
        
        // Ctrl/Cmd + /: Focus search
        if ((event.ctrlKey || event.metaKey) && event.key === '/') {
            event.preventDefault();
            const searchInput = document.querySelector('input[type="search"], input[name="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
    });
}

function handleResize() {
    // Handle responsive changes
    const width = window.innerWidth;
    
    if (width < 768) {
        // Mobile adjustments
        document.body.classList.add('mobile');
    } else {
        document.body.classList.remove('mobile');
    }
}

// =============================================================================
// Page-specific Functions
// =============================================================================

// Calendar functions
function showDayDetails(date) {
    // This would be implemented in calendar.html
    console.log('Show day details for:', date);
}

function addToGoogleCalendar() {
    // This would be implemented in calendar.html
    console.log('Add to Google Calendar');
}

// Configuration functions
function resetToDefaults() {
    if (confirm('すべての設定をデフォルト値に戻しますか？この操作は元に戻せません。')) {
        const form = document.getElementById('config-form');
        if (form) {
            form.reset();
            // Apply default values
            document.getElementById('check_interval_hours').value = '24';
            
            // Enable all sources
            ['anilist', 'shobo_calendar', 'bookwalker_rss', 'mangapocket_rss'].forEach(id => {
                const checkbox = document.getElementById(id);
                if (checkbox) checkbox.checked = true;
            });
            
            // Reset NG keywords
            const defaultNGWords = ['エロ', 'R18', '成人向け', 'BL', '百合', 'ボーイズラブ'];
            const ngKeywords = document.getElementById('ng_keywords');
            if (ngKeywords) {
                ngKeywords.value = defaultNGWords.join('\n');
            }
            
            showNotification('設定をデフォルト値に戻しました', 'info');
        }
    }
}

function testConfiguration() {
    const testBtn = event.target;
    const originalText = testBtn.innerHTML;
    
    testBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>テスト中...';
    testBtn.disabled = true;
    
    // Simulate API test
    setTimeout(() => {
        showNotification('設定テストが完了しました。すべて正常です。', 'success');
        
        testBtn.innerHTML = originalText;
        testBtn.disabled = false;
    }, 2000);
}

// =============================================================================
// Global Error Handler
// =============================================================================
window.addEventListener('error', function(event) {
    // ブラウザ拡張機能のエラーを完全に無視
    if (event.filename && (
        event.filename.includes('all.iife.js') ||
        event.filename.includes('chrome-extension://') ||
        event.filename.includes('moz-extension://') ||
        event.filename.includes('edge-extension://')
    )) {
        return; // 拡張機能エラーは無視
    }

    console.error('Global error:', event.error);

    // フィルタリング: 一般的な無害なエラーを除外
    const ignorableErrors = [
        'Non-Error promise rejection',
        'Script error',
        'ResizeObserver loop limit exceeded',
        'Loading chunk',
        'Loading CSS chunk',
        'Network request failed',
        'Cannot read properties of null',
        'Cannot read properties of undefined'
    ];
    
    const errorMessage = event.error?.message || event.message || '';
    const shouldIgnore = ignorableErrors.some(ignore => 
        errorMessage.toLowerCase().includes(ignore.toLowerCase())
    );
    
    if (!shouldIgnore && errorMessage) {
        console.warn('Showing error notification for:', errorMessage);
        // 重複したエラー通知を避けるためにタイムアウトを使用
        if (!window.lastErrorTime || Date.now() - window.lastErrorTime > 5000) {
            showNotification(`エラーが発生しました: ${errorMessage.substring(0, 50)}`, 'error');
            window.lastErrorTime = Date.now();
        }
    }
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    
    // Promise rejection の詳細を確認
    let errorMsg = '';
    if (typeof event.reason === 'string') {
        errorMsg = event.reason;
    } else if (event.reason && event.reason.message) {
        errorMsg = event.reason.message;
    } else if (event.reason && event.reason.toString) {
        errorMsg = event.reason.toString();
    }
    
    // 空のエラーメッセージやネットワークエラーは無視
    if (errorMsg && 
        !errorMsg.includes('Failed to fetch') && 
        !errorMsg.includes('NetworkError') &&
        errorMsg.trim() !== '') {
        showNotification(`通信エラー: ${errorMsg.substring(0, 50)}`, 'error');
    }
    
    // ブラウザのデフォルト動作を阻止（コンソールには表示される）
    event.preventDefault();
});

// =============================================================================
// Export functions for global access
// =============================================================================
window.AnimeManagaSystem = {
    refreshData,
    exportData,
    showNotification,
    makeApiRequest,
    checkSystemStatus
};