/**
 * UI/UX Enhancement JavaScript Module
 * Advanced interaction enhancements for MangaAnime Information Delivery System
 * Focus: Accessibility, Smooth Animations, Better UX
 */

(function() {
    'use strict';

    // =============================================================================
    // Enhanced Notification System
    // =============================================================================
    class NotificationManager {
        constructor() {
            this.container = this.getOrCreateContainer();
            this.notifications = new Map();
            this.defaultDuration = 5000;
        }

        getOrCreateContainer() {
            let container = document.getElementById('notification-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'notification-container';
                container.className = 'position-fixed top-0 end-0 p-3';
                container.style.zIndex = '9999';
                container.setAttribute('role', 'region');
                container.setAttribute('aria-label', '通知エリア');
                container.setAttribute('aria-live', 'polite');
                document.body.appendChild(container);
            }
            return container;
        }

        show(message, type = 'info', duration = this.defaultDuration) {
            const id = Date.now() + Math.random();
            const notification = this.createNotification(id, message, type);

            this.container.appendChild(notification);
            this.notifications.set(id, notification);

            // Trigger animation
            requestAnimationFrame(() => {
                notification.classList.add('show');
            });

            // Auto-remove
            if (duration > 0) {
                setTimeout(() => this.remove(id), duration);
            }

            return id;
        }

        createNotification(id, message, type) {
            const alertClass = {
                'success': 'alert-success',
                'error': 'alert-danger',
                'warning': 'alert-warning',
                'info': 'alert-info'
            }[type] || 'alert-info';

            const icon = {
                'success': 'bi-check-circle-fill',
                'error': 'bi-exclamation-circle-fill',
                'warning': 'bi-exclamation-triangle-fill',
                'info': 'bi-info-circle-fill'
            }[type] || 'bi-info-circle-fill';

            const notification = document.createElement('div');
            notification.className = `alert ${alertClass} alert-dismissible fade`;
            notification.setAttribute('role', 'alert');
            notification.setAttribute('data-notification-id', id);

            notification.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="bi ${icon} me-2 flex-shrink-0"></i>
                    <div class="flex-grow-1">${this.escapeHtml(message)}</div>
                    <button type="button" class="btn-close" aria-label="閉じる"></button>
                </div>
            `;

            const closeBtn = notification.querySelector('.btn-close');
            closeBtn.addEventListener('click', () => this.remove(id));

            return notification;
        }

        remove(id) {
            const notification = this.notifications.get(id);
            if (!notification) return;

            notification.classList.remove('show');
            notification.classList.add('fade-out');

            setTimeout(() => {
                notification.remove();
                this.notifications.delete(id);
            }, 300);
        }

        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    }

    // =============================================================================
    // Enhanced Loading States
    // =============================================================================
    class LoadingManager {
        constructor() {
            this.activeLoaders = new Set();
        }

        show(target = 'body', message = '読み込み中...') {
            const loader = this.createLoader(message);
            const targetElement = typeof target === 'string'
                ? document.querySelector(target)
                : target;

            if (!targetElement) return null;

            const id = Date.now() + Math.random();
            loader.setAttribute('data-loader-id', id);

            // Add position relative if needed
            const position = window.getComputedStyle(targetElement).position;
            if (position === 'static') {
                targetElement.style.position = 'relative';
            }

            targetElement.appendChild(loader);
            this.activeLoaders.add(id);

            requestAnimationFrame(() => {
                loader.classList.add('show');
            });

            return id;
        }

        createLoader(message) {
            const loader = document.createElement('div');
            loader.className = 'loading-overlay fade';
            loader.setAttribute('role', 'status');
            loader.setAttribute('aria-live', 'polite');
            loader.setAttribute('aria-label', message);

            loader.innerHTML = `
                <div class="text-center">
                    <div class="spinner mb-3"></div>
                    <div class="text-muted">${message}</div>
                </div>
            `;

            return loader;
        }

        hide(id) {
            if (!id) {
                // Remove all loaders
                this.activeLoaders.forEach(loaderId => this.hide(loaderId));
                return;
            }

            const loader = document.querySelector(`[data-loader-id="${id}"]`);
            if (!loader) return;

            loader.classList.remove('show');

            setTimeout(() => {
                loader.remove();
                this.activeLoaders.delete(id);
            }, 300);
        }
    }

    // =============================================================================
    // Enhanced Form Validation
    // =============================================================================
    class FormValidator {
        constructor(form, options = {}) {
            this.form = form;
            this.options = {
                validateOnInput: true,
                validateOnBlur: true,
                ...options
            };
            this.errors = new Map();
            this.init();
        }

        init() {
            const inputs = this.form.querySelectorAll('input, select, textarea');

            inputs.forEach(input => {
                if (this.options.validateOnInput) {
                    input.addEventListener('input', () => this.validateField(input));
                }
                if (this.options.validateOnBlur) {
                    input.addEventListener('blur', () => this.validateField(input));
                }
            });

            this.form.addEventListener('submit', (e) => {
                if (!this.validateForm()) {
                    e.preventDefault();
                    this.focusFirstError();
                }
            });
        }

        validateField(field) {
            const errors = [];

            // Required validation
            if (field.hasAttribute('required') && !field.value.trim()) {
                errors.push('このフィールドは必須です');
            }

            // Email validation
            if (field.type === 'email' && field.value) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(field.value)) {
                    errors.push('有効なメールアドレスを入力してください');
                }
            }

            // Number validation
            if (field.type === 'number') {
                const value = parseFloat(field.value);
                if (field.hasAttribute('min') && value < parseFloat(field.min)) {
                    errors.push(`${field.min}以上の値を入力してください`);
                }
                if (field.hasAttribute('max') && value > parseFloat(field.max)) {
                    errors.push(`${field.max}以下の値を入力してください`);
                }
            }

            // Update field state
            this.updateFieldState(field, errors);
            return errors.length === 0;
        }

        validateForm() {
            const inputs = this.form.querySelectorAll('input, select, textarea');
            let isValid = true;

            inputs.forEach(input => {
                if (!this.validateField(input)) {
                    isValid = false;
                }
            });

            return isValid;
        }

        updateFieldState(field, errors) {
            const feedbackId = `${field.id}-feedback`;
            let feedback = document.getElementById(feedbackId);

            // Remove existing feedback
            if (feedback) {
                feedback.remove();
            }

            // Remove validation classes
            field.classList.remove('is-valid', 'is-invalid');

            if (errors.length > 0) {
                // Add invalid state
                field.classList.add('is-invalid');
                this.errors.set(field, errors);

                // Create feedback element
                feedback = document.createElement('div');
                feedback.id = feedbackId;
                feedback.className = 'invalid-feedback';
                feedback.textContent = errors[0];
                field.parentNode.appendChild(feedback);

                // Update ARIA
                field.setAttribute('aria-invalid', 'true');
                field.setAttribute('aria-describedby', feedbackId);
            } else {
                // Add valid state
                if (field.value) {
                    field.classList.add('is-valid');
                }
                this.errors.delete(field);
                field.removeAttribute('aria-invalid');
                field.removeAttribute('aria-describedby');
            }
        }

        focusFirstError() {
            const firstErrorField = this.form.querySelector('.is-invalid');
            if (firstErrorField) {
                firstErrorField.focus();
                firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }

    // =============================================================================
    // Enhanced Table Features
    // =============================================================================
    class TableEnhancer {
        constructor(table, options = {}) {
            this.table = table;
            this.options = {
                sortable: true,
                searchable: true,
                ...options
            };
            this.init();
        }

        init() {
            if (this.options.sortable) {
                this.enableSorting();
            }
            if (this.options.searchable) {
                this.enableSearch();
            }
            this.enhanceAccessibility();
        }

        enableSorting() {
            const headers = this.table.querySelectorAll('th[data-sortable]');

            headers.forEach((header, index) => {
                header.style.cursor = 'pointer';
                header.setAttribute('role', 'button');
                header.setAttribute('tabindex', '0');

                // Add sort indicator
                const indicator = document.createElement('span');
                indicator.className = 'sort-indicator ms-1';
                indicator.innerHTML = '<i class="bi bi-arrow-down-up text-muted"></i>';
                header.appendChild(indicator);

                header.addEventListener('click', () => this.sortColumn(index, header));
                header.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        this.sortColumn(index, header);
                    }
                });
            });
        }

        sortColumn(columnIndex, header) {
            const tbody = this.table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const currentOrder = header.getAttribute('data-sort-order') || 'none';
            const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';

            // Sort rows
            rows.sort((a, b) => {
                const aValue = a.children[columnIndex].textContent.trim();
                const bValue = b.children[columnIndex].textContent.trim();

                // Try to sort as numbers
                const aNum = parseFloat(aValue);
                const bNum = parseFloat(bValue);

                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return newOrder === 'asc' ? aNum - bNum : bNum - aNum;
                }

                // Sort as strings
                return newOrder === 'asc'
                    ? aValue.localeCompare(bValue, 'ja')
                    : bValue.localeCompare(aValue, 'ja');
            });

            // Update DOM
            rows.forEach(row => tbody.appendChild(row));

            // Update header states
            this.table.querySelectorAll('th[data-sortable]').forEach(th => {
                th.setAttribute('data-sort-order', 'none');
                const indicator = th.querySelector('.sort-indicator i');
                if (indicator) {
                    indicator.className = 'bi bi-arrow-down-up text-muted';
                }
            });

            header.setAttribute('data-sort-order', newOrder);
            const indicator = header.querySelector('.sort-indicator i');
            if (indicator) {
                indicator.className = newOrder === 'asc'
                    ? 'bi bi-arrow-up text-primary'
                    : 'bi bi-arrow-down text-primary';
            }
        }

        enableSearch() {
            // This would be implemented based on specific requirements
            console.log('Table search functionality enabled');
        }

        enhanceAccessibility() {
            // Add ARIA attributes
            this.table.setAttribute('role', 'table');

            const thead = this.table.querySelector('thead');
            if (thead) {
                thead.setAttribute('role', 'rowgroup');
            }

            const tbody = this.table.querySelector('tbody');
            if (tbody) {
                tbody.setAttribute('role', 'rowgroup');
            }
        }
    }

    // =============================================================================
    // Smooth Scroll Enhancement
    // =============================================================================
    class SmoothScroller {
        static scrollTo(target, options = {}) {
            const element = typeof target === 'string'
                ? document.querySelector(target)
                : target;

            if (!element) return;

            const offset = options.offset || 0;
            const behavior = options.behavior || 'smooth';

            const elementPosition = element.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - offset;

            window.scrollTo({
                top: offsetPosition,
                behavior: behavior
            });
        }

        static init() {
            // Handle anchor links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function(e) {
                    const href = this.getAttribute('href');
                    if (href === '#') return;

                    e.preventDefault();
                    const target = document.querySelector(href);
                    if (target) {
                        SmoothScroller.scrollTo(target, { offset: 80 });

                        // Update URL without jumping
                        history.pushState(null, null, href);

                        // Focus target for accessibility
                        target.setAttribute('tabindex', '-1');
                        target.focus();
                    }
                });
            });
        }
    }

    // =============================================================================
    // Keyboard Navigation Enhancement
    // =============================================================================
    class KeyboardNavigationManager {
        constructor() {
            this.shortcuts = new Map();
            this.init();
        }

        init() {
            document.addEventListener('keydown', (e) => this.handleKeyPress(e));
        }

        register(key, callback, options = {}) {
            const shortcutKey = this.createShortcutKey(key, options);
            this.shortcuts.set(shortcutKey, callback);
        }

        createShortcutKey(key, options) {
            const parts = [];
            if (options.ctrl) parts.push('ctrl');
            if (options.shift) parts.push('shift');
            if (options.alt) parts.push('alt');
            if (options.meta) parts.push('meta');
            parts.push(key.toLowerCase());
            return parts.join('+');
        }

        handleKeyPress(e) {
            const key = e.key.toLowerCase();
            const shortcutKey = this.createShortcutKey(key, {
                ctrl: e.ctrlKey,
                shift: e.shiftKey,
                alt: e.altKey,
                meta: e.metaKey
            });

            const callback = this.shortcuts.get(shortcutKey);
            if (callback) {
                e.preventDefault();
                callback(e);
            }
        }
    }

    // =============================================================================
    // Tooltip Enhancement
    // =============================================================================
    class TooltipManager {
        constructor() {
            this.tooltips = new Map();
            this.init();
        }

        init() {
            document.querySelectorAll('[data-tooltip]').forEach(element => {
                this.attach(element);
            });
        }

        attach(element) {
            const message = element.getAttribute('data-tooltip');
            const placement = element.getAttribute('data-tooltip-placement') || 'top';

            element.addEventListener('mouseenter', () => this.show(element, message, placement));
            element.addEventListener('mouseleave', () => this.hide(element));
            element.addEventListener('focus', () => this.show(element, message, placement));
            element.addEventListener('blur', () => this.hide(element));
        }

        show(element, message, placement) {
            const tooltip = this.createTooltip(message, placement);
            document.body.appendChild(tooltip);
            this.tooltips.set(element, tooltip);

            // Position tooltip
            requestAnimationFrame(() => {
                this.position(tooltip, element, placement);
                tooltip.classList.add('show');
            });
        }

        createTooltip(message, placement) {
            const tooltip = document.createElement('div');
            tooltip.className = `tooltip bs-tooltip-${placement}`;
            tooltip.setAttribute('role', 'tooltip');

            tooltip.innerHTML = `
                <div class="tooltip-arrow"></div>
                <div class="tooltip-inner">${message}</div>
            `;

            return tooltip;
        }

        position(tooltip, element, placement) {
            const rect = element.getBoundingClientRect();
            const tooltipRect = tooltip.getBoundingClientRect();

            let top, left;

            switch(placement) {
                case 'top':
                    top = rect.top - tooltipRect.height - 8;
                    left = rect.left + (rect.width - tooltipRect.width) / 2;
                    break;
                case 'bottom':
                    top = rect.bottom + 8;
                    left = rect.left + (rect.width - tooltipRect.width) / 2;
                    break;
                case 'left':
                    top = rect.top + (rect.height - tooltipRect.height) / 2;
                    left = rect.left - tooltipRect.width - 8;
                    break;
                case 'right':
                    top = rect.top + (rect.height - tooltipRect.height) / 2;
                    left = rect.right + 8;
                    break;
            }

            tooltip.style.top = `${top + window.pageYOffset}px`;
            tooltip.style.left = `${left + window.pageXOffset}px`;
        }

        hide(element) {
            const tooltip = this.tooltips.get(element);
            if (!tooltip) return;

            tooltip.classList.remove('show');
            setTimeout(() => {
                tooltip.remove();
                this.tooltips.delete(element);
            }, 150);
        }
    }

    // =============================================================================
    // Initialize All Enhancements
    // =============================================================================
    function initializeEnhancements() {
        // Create global instances
        window.notificationManager = new NotificationManager();
        window.loadingManager = new LoadingManager();
        window.keyboardNav = new KeyboardNavigationManager();
        window.tooltipManager = new TooltipManager();

        // Initialize smooth scrolling
        SmoothScroller.init();

        // Initialize form validation
        document.querySelectorAll('form[data-validate]').forEach(form => {
            new FormValidator(form);
        });

        // Initialize table enhancements
        document.querySelectorAll('table[data-enhance]').forEach(table => {
            new TableEnhancer(table);
        });

        // Register keyboard shortcuts
        window.keyboardNav.register('/', () => {
            const searchInput = document.querySelector('input[type="search"], input[name="search"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        });

        window.keyboardNav.register('Escape', () => {
            // Close modals, dropdowns, etc.
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modalInstance = bootstrap.Modal.getInstance(openModal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            }
        });

        console.log('UI Enhancements initialized successfully');
    }

    // =============================================================================
    // Export to Global Scope
    // =============================================================================
    window.UIEnhancements = {
        NotificationManager,
        LoadingManager,
        FormValidator,
        TableEnhancer,
        SmoothScroller,
        KeyboardNavigationManager,
        TooltipManager
    };

    // Auto-initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeEnhancements);
    } else {
        initializeEnhancements();
    }
})();
