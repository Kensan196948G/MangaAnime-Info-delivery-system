/**
 * API Client for MangaAnime Info Delivery System
 *
 * This module provides helper functions for interacting with the backend API
 * using the standardized response format.
 */

class ApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    /**
     * Make a GET request to an API endpoint
     *
     * @param {string} endpoint - API endpoint path
     * @param {Object} options - Additional fetch options
     * @returns {Promise<ApiResponse>}
     */
    async get(endpoint, options = {}) {
        return this._request('GET', endpoint, null, options);
    }

    /**
     * Make a POST request to an API endpoint
     *
     * @param {string} endpoint - API endpoint path
     * @param {Object} data - Request body data
     * @param {Object} options - Additional fetch options
     * @returns {Promise<ApiResponse>}
     */
    async post(endpoint, data = null, options = {}) {
        return this._request('POST', endpoint, data, options);
    }

    /**
     * Make a PUT request to an API endpoint
     *
     * @param {string} endpoint - API endpoint path
     * @param {Object} data - Request body data
     * @param {Object} options - Additional fetch options
     * @returns {Promise<ApiResponse>}
     */
    async put(endpoint, data = null, options = {}) {
        return this._request('PUT', endpoint, data, options);
    }

    /**
     * Make a DELETE request to an API endpoint
     *
     * @param {string} endpoint - API endpoint path
     * @param {Object} options - Additional fetch options
     * @returns {Promise<ApiResponse>}
     */
    async delete(endpoint, options = {}) {
        return this._request('DELETE', endpoint, null, options);
    }

    /**
     * Internal request method
     *
     * @private
     */
    async _request(method, endpoint, data = null, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            method,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (data && (method === 'POST' || method === 'PUT')) {
            config.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, config);
            const result = await response.json();

            // Return standardized response
            return new ApiResponse(result, response.status);

        } catch (error) {
            // Network error or JSON parse error
            return new ApiResponse({
                success: false,
                message: '通信エラーが発生しました',
                data: null,
                error: {
                    message: '通信エラーが発生しました',
                    details: error.message,
                    code: 'NETWORK_ERROR'
                }
            }, 0);
        }
    }
}

/**
 * API Response wrapper class
 *
 * Provides convenient methods for handling API responses
 */
class ApiResponse {
    constructor(data, statusCode) {
        this.success = data.success;
        this.message = data.message;
        this.data = data.data;
        this.error = data.error;
        this.statusCode = statusCode;
    }

    /**
     * Check if the request was successful
     * @returns {boolean}
     */
    isSuccess() {
        return this.success === true;
    }

    /**
     * Check if the request failed
     * @returns {boolean}
     */
    isError() {
        return this.success === false;
    }

    /**
     * Get the response data
     * @returns {Object|null}
     */
    getData() {
        return this.data;
    }

    /**
     * Get error information
     * @returns {Object|null}
     */
    getError() {
        return this.error;
    }

    /**
     * Get error code
     * @returns {string|null}
     */
    getErrorCode() {
        return this.error ? this.error.code : null;
    }

    /**
     * Get error message
     * @returns {string|null}
     */
    getErrorMessage() {
        return this.error ? this.error.message : null;
    }

    /**
     * Get error details
     * @returns {string|null}
     */
    getErrorDetails() {
        return this.error ? this.error.details : null;
    }

    /**
     * Get the main message
     * @returns {string}
     */
    getMessage() {
        return this.message;
    }
}

/**
 * Create a default API client instance
 */
const apiClient = new ApiClient();

/**
 * Convenience functions for common API operations
 */
const API = {
    /**
     * Refresh data by calling the backend script
     * @returns {Promise<ApiResponse>}
     */
    async refreshData() {
        return apiClient.get('/api/refresh-data');
    },

    /**
     * Get data status information
     * @returns {Promise<ApiResponse>}
     */
    async getDataStatus() {
        return apiClient.get('/api/data-status');
    },

    /**
     * Get statistics
     * @returns {Promise<ApiResponse>}
     */
    async getStats() {
        return apiClient.get('/api/stats');
    },

    /**
     * Get collection status
     * @returns {Promise<ApiResponse>}
     */
    async getCollectionStatus() {
        return apiClient.get('/api/collection-status');
    },

    /**
     * Get works list
     * @param {Object} params - Query parameters
     * @returns {Promise<ApiResponse>}
     */
    async getWorks(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `/api/works?${queryString}` : '/api/works';
        return apiClient.get(endpoint);
    },

    /**
     * Get work details by ID
     * @param {number} workId - Work ID
     * @returns {Promise<ApiResponse>}
     */
    async getWork(workId) {
        return apiClient.get(`/api/works/${workId}`);
    },

    /**
     * Add work to watchlist
     * @param {Object} data - Work data
     * @returns {Promise<ApiResponse>}
     */
    async addToWatchlist(data) {
        return apiClient.post('/api/watchlist/add', data);
    },

    /**
     * Trigger manual collection
     * @param {Object} data - Collection parameters
     * @returns {Promise<ApiResponse>}
     */
    async triggerCollection(data) {
        return apiClient.post('/api/manual-collection', data);
    },

    /**
     * Test notification
     * @param {Object} data - Notification test data
     * @returns {Promise<ApiResponse>}
     */
    async testNotification(data) {
        return apiClient.post('/api/test-notification', data);
    },

    /**
     * Test configuration
     * @param {Object} data - Configuration test data
     * @returns {Promise<ApiResponse>}
     */
    async testConfiguration(data) {
        return apiClient.post('/api/test-configuration', data);
    }
};

/**
 * Display alert based on API response
 *
 * @param {ApiResponse} response - API response
 * @param {Object} options - Display options
 */
function displayApiAlert(response, options = {}) {
    const {
        successTitle = '成功',
        errorTitle = 'エラー',
        container = document.body,
        autoClose = true,
        closeDelay = 5000
    } = options;

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${response.isSuccess() ? 'success' : 'danger'} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');

    let content = `<strong>${response.isSuccess() ? successTitle : errorTitle}:</strong> ${response.getMessage()}`;

    if (response.isError() && response.getErrorDetails()) {
        content += `<br><small>${response.getErrorDetails()}</small>`;
    }

    if (response.getErrorCode()) {
        content += `<br><small>エラーコード: ${response.getErrorCode()}</small>`;
    }

    content += `
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    alertDiv.innerHTML = content;
    container.insertBefore(alertDiv, container.firstChild);

    if (autoClose && response.isSuccess()) {
        setTimeout(() => {
            alertDiv.remove();
        }, closeDelay);
    }
}

/**
 * Example usage:
 *
 * // Using the convenience API object
 * const response = await API.refreshData();
 * if (response.isSuccess()) {
 *     console.log('Data refreshed!', response.getData());
 * } else {
 *     console.error('Error:', response.getErrorMessage());
 *     console.error('Details:', response.getErrorDetails());
 * }
 *
 * // Using the API client directly
 * const client = new ApiClient();
 * const response = await client.get('/api/stats');
 *
 * // Display alert
 * displayApiAlert(response, {
 *     container: document.getElementById('alerts-container')
 * });
 */

// Export for use in modules (if using ES modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ApiClient, ApiResponse, API, displayApiAlert };
}
