/**
 * Dashboard Data Update Functionality
 * Handles data refresh, auto-update, and status management
 */

// =============================================================================
// Constants and Configuration
// =============================================================================
const UPDATE_CHECK_INTERVAL = 30 * 60 * 1000; // 30 minutes in milliseconds
const LAST_VISIT_KEY = 'dashboard_last_visit';
const AUTO_REFRESH_KEY = 'dashboard_auto_refresh';

// =============================================================================
// State Management
// =============================================================================
let isUpdating = false;
let autoRefreshEnabled = true;
let autoRefreshModal = null;

// =============================================================================
// Initialization
// =============================================================================
document.addEventListener('DOMContentLoaded', function() {
    initializeUpdateFeature();
});

function initializeUpdateFeature() {
    // Initialize Bootstrap modal
    const modalElement = document.getElementById('autoRefreshModal');
    if (modalElement && typeof bootstrap !== 'undefined') {
        autoRefreshModal = new bootstrap.Modal(modalElement);
    }

    // Load auto-refresh preference
    const savedPref = localStorage.getItem(AUTO_REFRESH_KEY);
    if (savedPref !== null) {
        autoRefreshEnabled = savedPref === 'true';
        updateAutoRefreshUI();
    }

    // Check if data update is needed
    checkAndPromptDataUpdate();

    // Update last update time display
    updateLastUpdateTimeDisplay();

    // Set up periodic check
    setInterval(checkAndPromptDataUpdate, 5 * 60 * 1000); // Check every 5 minutes
}

// =============================================================================
// Auto-Refresh Check
// =============================================================================
function checkAndPromptDataUpdate() {
    if (!autoRefreshEnabled) {
        return;
    }

    const lastVisit = localStorage.getItem(LAST_VISIT_KEY);
    const now = Date.now();

    if (lastVisit) {
        const timeSinceLastVisit = now - parseInt(lastVisit);

        // If more than 30 minutes have passed, show confirmation dialog
        if (timeSinceLastVisit > UPDATE_CHECK_INTERVAL) {
            showAutoRefreshPrompt(timeSinceLastVisit);
        }
    }

    // Update last visit time
    localStorage.setItem(LAST_VISIT_KEY, now.toString());
}

function showAutoRefreshPrompt(timeSinceLastVisit) {
    // Calculate time elapsed
    const minutes = Math.floor(timeSinceLastVisit / (60 * 1000));
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    let timeElapsedText;
    if (days > 0) {
        const remainingHours = hours % 24;
        timeElapsedText = days + '日' + remainingHours + '時間';
    } else if (hours > 0) {
        const remainingMinutes = minutes % 60;
        timeElapsedText = hours + '時間' + remainingMinutes + '分';
    } else {
        timeElapsedText = minutes + '分';
    }

    // Update modal text
    const timeElapsedElement = document.getElementById('time-elapsed');
    if (timeElapsedElement) {
        timeElapsedElement.textContent = timeElapsedText;
    }

    // Show modal
    if (autoRefreshModal) {
        autoRefreshModal.show();
    }
}

function confirmAutoRefresh() {
    // Close modal
    if (autoRefreshModal) {
        autoRefreshModal.hide();
    }

    // Trigger data refresh
    refreshDashboardData();
}

// =============================================================================
// Data Refresh Function
// =============================================================================
function refreshDashboardData() {
    if (isUpdating) {
        showStatusMessage('既にデータ更新中です...', 'warning');
        return;
    }

    isUpdating = true;

    // Update button state
    const refreshBtn = document.getElementById('refresh-data-btn');
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>更新中...';
    }

    // Show progress bar
    showProgressBar();
    updateProgress(10);
    showStatusMessage('データ更新を開始しています...', 'info');

    // Create AbortController for timeout handling
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout

    console.log('[Dashboard Update] データ更新リクエスト開始');

    // Call API with timeout
    fetch('/api/refresh-data', {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        signal: controller.signal
    })
        .then(response => {
            clearTimeout(timeoutId);
            updateProgress(50);

            console.log('[Dashboard Update] レスポンス受信:', {
                status: response.status,
                statusText: response.statusText,
                ok: response.ok,
                headers: {
                    'content-type': response.headers.get('content-type')
                }
            });

            // Check if response is JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('[Dashboard Update] 無効なContent-Type:', contentType);
                throw new Error('サーバーから無効なレスポンス形式が返されました (expected JSON, got ' + contentType + ')');
            }

            // Clone response for logging
            return response.clone().json().then(data => {
                console.log('[Dashboard Update] JSONパース成功:', data);

                // Check HTTP status
                if (!response.ok) {
                    console.error('[Dashboard Update] HTTP error:', {
                        status: response.status,
                        statusText: response.statusText,
                        data: data
                    });

                    // Handle both old and new error formats
                    let errorMessage;
                    if (data.error && typeof data.error === 'object') {
                        errorMessage = data.error.message || data.error.details || JSON.stringify(data.error);
                    } else {
                        errorMessage = data.error || data.details || data.message || response.statusText;
                    }
                    throw new Error('HTTP ' + response.status + ': ' + errorMessage);
                }

                return data;
            });
        })
        .then(data => {
            updateProgress(80);

            console.log('[Dashboard Update] データ検証中:', {
                success: data.success,
                hasMessage: !!data.message,
                hasError: !!data.error,
                timestamp: data.timestamp
            });

            // Check success flag
            if (data.success === true) {
                console.log('[Dashboard Update] データ更新成功');
                showStatusMessage('データ更新が完了しました。ページをリロードしています...', 'success');
                updateProgress(100);

                // Update last update time
                updateLastUpdateTimeDisplay();

                // Reload page after short delay
                setTimeout(() => {
                    console.log('[Dashboard Update] ページをリロードします');
                    window.location.reload();
                }, 1500);
            } else if (data.success === false) {
                // Explicit failure from server - handle nested error format
                let errorDetail;
                if (data.error && typeof data.error === 'object') {
                    errorDetail = data.error.message || data.error.details || JSON.stringify(data.error);
                } else {
                    errorDetail = data.error || data.details || data.message || 'サーバーがエラーを返しました';
                }
                console.error('[Dashboard Update] サーバーエラー:', errorDetail);
                throw new Error(errorDetail);
            } else {
                // Unexpected response format
                console.error('[Dashboard Update] 予期しないレスポンス形式:', data);
                throw new Error('サーバーから予期しないレスポンスが返されました (success フィールドが存在しません)');
            }
        })
        .catch(error => {
            clearTimeout(timeoutId);

            // Determine error type
            let errorMessage;
            let errorType = 'unknown';

            if (error.name === 'AbortError') {
                errorType = 'timeout';
                errorMessage = 'データ更新がタイムアウトしました (60秒以上応答なし)';
                console.error('[Dashboard Update] タイムアウトエラー');
            } else if (error instanceof TypeError) {
                errorType = 'network';
                errorMessage = 'ネットワークエラー: サーバーに接続できません';
                console.error('[Dashboard Update] ネットワークエラー:', error);
            } else {
                errorType = 'server';
                errorMessage = error.message || '不明なエラーが発生しました';
                console.error('[Dashboard Update] サーバーエラー:', error);
            }

            console.error('[Dashboard Update] エラー詳細:', {
                type: errorType,
                message: errorMessage,
                error: error,
                stack: error.stack
            });

            // Show user-friendly error message
            showStatusMessage('データ更新に失敗しました: ' + errorMessage, 'danger');
            updateProgress(0);
            hideProgressBar();

            // Reset button
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i>データ更新';
            }

            isUpdating = false;
        });
}

// =============================================================================
// Auto-Refresh Toggle
// =============================================================================
function toggleAutoRefresh() {
    autoRefreshEnabled = !autoRefreshEnabled;
    localStorage.setItem(AUTO_REFRESH_KEY, autoRefreshEnabled.toString());
    updateAutoRefreshUI();

    const message = autoRefreshEnabled
        ? '自動更新が有効になりました'
        : '自動更新が無効になりました';
    showStatusMessage(message, 'info');

    setTimeout(() => {
        hideStatusMessage();
    }, 3000);
}

function updateAutoRefreshUI() {
    const icon = document.getElementById('auto-refresh-icon');
    const text = document.getElementById('auto-refresh-text');

    if (icon && text) {
        if (autoRefreshEnabled) {
            icon.className = 'bi bi-toggle-on me-1';
            text.textContent = '自動更新: ON';
        } else {
            icon.className = 'bi bi-toggle-off me-1';
            text.textContent = '自動更新: OFF';
        }
    }
}

// =============================================================================
// UI Update Functions
// =============================================================================
function showProgressBar() {
    const progressBar = document.getElementById('update-progress-bar');
    if (progressBar) {
        progressBar.style.display = 'block';
    }
}

function hideProgressBar() {
    const progressBar = document.getElementById('update-progress-bar');
    if (progressBar) {
        progressBar.style.display = 'none';
    }
}

function updateProgress(percentage) {
    const progress = document.getElementById('update-progress');
    if (progress) {
        progress.style.width = percentage + '%';
        progress.setAttribute('aria-valuenow', percentage);
    }
}

function showStatusMessage(message, type) {
    const messageElement = document.getElementById('update-status-message');
    const textElement = document.getElementById('update-status-text');

    if (messageElement && textElement) {
        textElement.textContent = message;
        messageElement.className = 'alert alert-' + type + ' mt-3 mb-0 py-2';
        messageElement.style.display = 'block';
    }
}

function hideStatusMessage() {
    const messageElement = document.getElementById('update-status-message');
    if (messageElement) {
        messageElement.style.display = 'none';
    }
}

function updateLastUpdateTimeDisplay() {
    const timeElement = document.getElementById('last-update-time');
    if (timeElement) {
        const now = new Date();
        const formattedTime = now.toLocaleString('ja-JP', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        timeElement.textContent = formattedTime;
    }
}

// =============================================================================
// Accessibility Enhancements
// =============================================================================
document.addEventListener('keydown', function(event) {
    // Ctrl+Shift+R or Cmd+Shift+R to refresh data (but not reload page)
    if ((event.ctrlKey || event.metaKey) && event.key === 'R' && event.shiftKey) {
        event.preventDefault();
        refreshDashboardData();
    }
});
