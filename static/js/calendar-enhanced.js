/**
 * Calendar Enhanced UI - JavaScript
 * アニメ・マンガ情報配信システム
 */

(function() {
    'use strict';

    // === 1. プラットフォーム別アイコンマッピング ===
    const PLATFORM_ICONS = {
        'netflix': '🎬',
        'amazon': '📺',
        'amazon prime': '📺',
        'prime video': '📺',
        'crunchyroll': '🌸',
        'dアニメストア': '🎭',
        'danime': '🎭',
        'bookwalker': '📚',
        'kindle': '📖',
        'ジャンプ+': '⚡',
        'jump+': '⚡',
        'マガポケ': '📱',
        'magapoke': '📱',
        'hulu': '📹',
        'disney+': '🎪',
        'u-next': '🎦',
        'abema': '📡'
    };

    // === 2. 作品タイトル別絵文字（人気作品） ===
    const TITLE_EMOJIS = {
        'one piece': '👒',
        'ワンピース': '👒',
        'naruto': '🍥',
        'ナルト': '🍥',
        '呪術廻戦': '⚡',
        'jujutsu kaisen': '⚡',
        '鬼滅の刃': '⚔️',
        'demon slayer': '⚔️',
        '進撃の巨人': '🗡️',
        'attack on titan': '🗡️',
        'ヒロアカ': '💥',
        '僕のヒーローアカデミア': '💥',
        'my hero academia': '💥',
        'チェンソーマン': '⛓️',
        'chainsaw man': '⛓️',
        'スパイファミリー': '🕵️',
        'spy family': '🕵️',
        '東京リベンジャーズ': '⏱️',
        'tokyo revengers': '⏱️',
        'ブルーロック': '⚽',
        'blue lock': '⚽'
    };

    // === 3. 初期化処理 ===
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Calendar Enhanced UI: Initializing...');

        enhanceCalendar();
        addTodayHighlight();
        enhanceReleaseItems();
        addSwipeNavigation();
        addKeyboardNavigation();
        addTooltips();

        console.log('Calendar Enhanced UI: Initialization complete');
    });

    // === 4. カレンダー全体の機能強化 ===
    function enhanceCalendar() {
        const calendarDays = document.querySelectorAll('.calendar-day');

        calendarDays.forEach(day => {
            const date = day.dataset.date;
            if (!date) return;

            const releases = getReleasesByDate(date);

            // リリースがある日はクリック可能に
            if (releases.length > 0) {
                day.style.cursor = 'pointer';
                day.setAttribute('role', 'button');
                day.setAttribute('tabindex', '0');
                day.setAttribute('aria-label', `${date}のリリース ${releases.length}件`);

                // クリックイベント
                day.addEventListener('click', function() {
                    showDayDetails(date);
                    const modal = new bootstrap.Modal(document.getElementById('dayModal'));
                    modal.show();
                });

                // Enterキーでもモーダルを開く
                day.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        day.click();
                    }
                });

                // 件数バッジを追加
                addReleaseBadge(day, releases.length);
            }
        });
    }

    // === 5. 今日の日付をハイライト ===
    function addTodayHighlight() {
        const today = new Date();
        const todayStr = formatDate(today);

        const todayCell = document.querySelector(`.calendar-day[data-date="${todayStr}"]`);
        if (todayCell) {
            todayCell.classList.add('today');
            const dayHeader = todayCell.querySelector('.day-header');
            if (dayHeader) {
                const badge = document.createElement('span');
                badge.className = 'day-badge';
                badge.textContent = '今日';
                badge.setAttribute('aria-label', '本日');
                dayHeader.appendChild(badge);
            }
        }
    }

    // === 6. リリースアイテムの強化 ===
    function enhanceReleaseItems() {
        const releaseItems = document.querySelectorAll('.release-item');

        releaseItems.forEach(item => {
            // タイトルからプラットフォームを取得
            const platformText = item.title || item.textContent;
            const platform = extractPlatform(platformText);

            // プラットフォーム別クラスを追加
            if (platform) {
                const platformClass = `platform-${platform.toLowerCase().replace(/\s+/g, '-').replace(/\+/g, 'plus')}`;
                item.classList.add(platformClass);
            }

            // アイコンを追加
            addPlatformIcon(item, platform);
            addTitleEmoji(item);

            // カテゴリバッジを追加
            addCategoryBadge(item);

            // アクセシビリティ向上
            item.setAttribute('role', 'button');
            item.setAttribute('tabindex', '0');
        });
    }

    // === 7. プラットフォーム抽出 ===
    function extractPlatform(text) {
        if (!text) return null;

        const lowerText = text.toLowerCase();

        for (const [platform, icon] of Object.entries(PLATFORM_ICONS)) {
            if (lowerText.includes(platform.toLowerCase())) {
                return platform;
            }
        }

        return null;
    }

    // === 8. プラットフォームアイコン追加 ===
    function addPlatformIcon(item, platform) {
        if (!platform) return;

        const icon = PLATFORM_ICONS[platform.toLowerCase()] || '📺';
        const titleElement = item.querySelector('.release-title');

        if (titleElement && !titleElement.querySelector('.release-icon')) {
            const iconSpan = document.createElement('span');
            iconSpan.className = 'release-icon';
            iconSpan.textContent = icon;
            iconSpan.setAttribute('aria-hidden', 'true');
            titleElement.insertBefore(iconSpan, titleElement.firstChild);
        }
    }

    // === 9. タイトル絵文字追加 ===
    function addTitleEmoji(item) {
        const titleElement = item.querySelector('.release-title');
        if (!titleElement) return;

        const titleText = titleElement.textContent.toLowerCase();

        for (const [title, emoji] of Object.entries(TITLE_EMOJIS)) {
            if (titleText.includes(title.toLowerCase())) {
                const emojiSpan = document.createElement('span');
                emojiSpan.className = 'release-icon';
                emojiSpan.textContent = emoji;
                emojiSpan.setAttribute('aria-hidden', 'true');
                titleElement.insertBefore(emojiSpan, titleElement.firstChild);
                break;
            }
        }
    }

    // === 10. カテゴリバッジ追加 ===
    function addCategoryBadge(item) {
        const titleElement = item.querySelector('.release-title');
        if (!titleElement) return;

        // 第1話または第1巻なら「新作」バッジ
        const detailsText = item.textContent || '';
        if (detailsText.includes('第1話') || detailsText.includes('第1巻')) {
            const badge = document.createElement('span');
            badge.className = 'category-badge badge-new';
            badge.textContent = 'NEW';
            badge.setAttribute('aria-label', '新作');
            titleElement.appendChild(badge);
        }
        // 第10話以上なら「継続」バッジ
        else if (detailsText.match(/第(1[0-9]|[2-9][0-9])話/) || detailsText.match(/第(1[0-9]|[2-9][0-9])巻/)) {
            const badge = document.createElement('span');
            badge.className = 'category-badge badge-ongoing';
            badge.textContent = '継続';
            badge.setAttribute('aria-label', '継続中');
            titleElement.appendChild(badge);
        }
    }

    // === 11. リリース件数バッジ追加 ===
    function addReleaseBadge(dayCell, count) {
        const dayHeader = dayCell.querySelector('.day-header');
        if (!dayHeader) return;

        const badge = document.createElement('span');
        badge.className = 'day-badge';
        badge.textContent = count;
        badge.setAttribute('aria-label', `${count}件のリリース`);
        dayHeader.appendChild(badge);
    }

    // === 12. スワイプナビゲーション（モバイル） ===
    function addSwipeNavigation() {
        if (!isTouchDevice()) return;

        let touchStartX = 0;
        let touchEndX = 0;

        const calendar = document.querySelector('.calendar-table');
        if (!calendar) return;

        calendar.addEventListener('touchstart', function(e) {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });

        calendar.addEventListener('touchend', function(e) {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        }, { passive: true });

        function handleSwipe() {
            const swipeThreshold = 50;
            const diff = touchStartX - touchEndX;

            if (Math.abs(diff) > swipeThreshold) {
                if (diff > 0) {
                    // 左スワイプ: 次月
                    const nextBtn = document.querySelector('a[href*="month="]');
                    if (nextBtn && nextBtn.textContent.includes('次月')) {
                        nextBtn.click();
                    }
                } else {
                    // 右スワイプ: 前月
                    const prevBtn = document.querySelector('a[href*="month="]');
                    if (prevBtn && prevBtn.textContent.includes('前月')) {
                        prevBtn.click();
                    }
                }
            }
        }
    }

    // === 13. キーボードナビゲーション ===
    function addKeyboardNavigation() {
        document.addEventListener('keydown', function(e) {
            // 矢印キーでのカレンダーナビゲーション
            if (e.key === 'ArrowLeft' && e.altKey) {
                // Alt + Left: 前月
                const prevBtn = document.querySelector('a[href*="month="]');
                if (prevBtn && prevBtn.textContent.includes('前月')) {
                    prevBtn.click();
                }
            } else if (e.key === 'ArrowRight' && e.altKey) {
                // Alt + Right: 次月
                const nextBtn = document.querySelector('a[href*="month="]');
                if (nextBtn && nextBtn.textContent.includes('次月')) {
                    nextBtn.click();
                }
            }
        });
    }

    // === 14. ツールチップ追加 ===
    function addTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // === 15. Googleカレンダー登録機能の強化 ===
    window.addToGoogleCalendar = function() {
        if (!window.selectedReleases || window.selectedReleases.length === 0) {
            showNotification('この日にリリース予定はありません。', 'warning');
            return;
        }

        const releases = window.selectedReleases;
        const date = window.selectedDate;

        // 複数のイベントを個別に作成
        releases.forEach(release => {
            const icon = getPlatformIcon(release.platform);
            const emoji = getTitleEmoji(release.title);
            const typeIcon = release.type === 'anime' ? '🎬' : '📚';
            const typeLabel = release.type === 'anime' ? 'アニメ' : 'マンガ';
            const releaseText = release.release_type === 'episode' ? '話' : '巻';

            // タイトル: "🎬【アニメ】ONE PIECE 第1234話 | Netflix"
            const title = `${typeIcon}【${typeLabel}】${emoji}${release.title} 第${release.number}${releaseText} | ${icon}${release.platform}`;

            // 説明文
            let details = `作品: ${release.title}\n`;
            details += `種別: ${typeLabel}\n`;
            details += `エピソード/巻: 第${release.number}${releaseText}\n`;
            details += `配信プラットフォーム: ${release.platform}\n\n`;

            if (release.source_url) {
                details += `ソース: ${release.source_url}\n`;
            }

            if (release.official_url) {
                details += `公式サイト: ${release.official_url}\n`;
            }

            details += '\n📅 このイベントは「アニメ・マンガ情報配信システム」により自動登録されました。';

            // Google Calendar URL生成
            let calendarUrl = 'https://calendar.google.com/calendar/render?action=TEMPLATE';
            calendarUrl += `&text=${encodeURIComponent(title)}`;
            calendarUrl += `&dates=${date.replace(/-/g, '')}/${date.replace(/-/g, '')}`;
            calendarUrl += `&details=${encodeURIComponent(details)}`;

            // カラー設定（colorIdはURLでは設定不可のため、タイトルで識別）

            // 新しいタブで開く
            window.open(calendarUrl, '_blank');
        });

        showNotification(`${releases.length}件のイベントをGoogleカレンダーに追加します。`, 'success');
    };

    // === 16. ヘルパー関数 ===
    function getPlatformIcon(platform) {
        if (!platform) return '📺';
        return PLATFORM_ICONS[platform.toLowerCase()] || '📺';
    }

    function getTitleEmoji(title) {
        if (!title) return '';

        const lowerTitle = title.toLowerCase();
        for (const [titleKey, emoji] of Object.entries(TITLE_EMOJIS)) {
            if (lowerTitle.includes(titleKey.toLowerCase())) {
                return emoji;
            }
        }
        return '';
    }

    function formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    function isTouchDevice() {
        return ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
    }

    function showNotification(message, type = 'info') {
        // Bootstrap Alertを使用
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.top = '20px';
        alertDiv.style.right = '20px';
        alertDiv.style.zIndex = '9999';
        alertDiv.setAttribute('role', 'alert');
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(alertDiv);

        // 5秒後に自動削除
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 300);
        }, 5000);
    }

    // === 17. モーダル表示関数の拡張（チェックボックス対応） ===
    window.showDayDetails = function(date) {
        window.selectedDate = date;
        const releases = getReleasesByDate(date);
        window.selectedReleases = releases;

        // 日付フォーマット
        const dateObj = new Date(date + 'T00:00:00');
        const formattedDate = dateObj.toLocaleDateString('ja-JP', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            weekday: 'long'
        });

        document.getElementById('modal-date').textContent = formattedDate;

        // モーダルコンテンツ生成
        let html = '';
        if (releases.length === 0) {
            html = '<p class="text-muted text-center">この日にリリース予定はありません。</p>';
        } else {
            // 全選択/全解除ボタン
            html += `
                <div class="d-flex justify-content-between align-items-center mb-3 p-3 bg-light rounded">
                    <div>
                        <strong><i class="bi bi-list-check me-2"></i>${releases.length}件のリリース</strong>
                    </div>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="selectAllReleases()">
                            <i class="bi bi-check-all me-1"></i>全選択
                        </button>
                        <button class="btn btn-outline-secondary" onclick="deselectAllReleases()">
                            <i class="bi bi-x-square me-1"></i>全解除
                        </button>
                    </div>
                </div>
            `;

            html += '<div class="list-group list-group-flush" id="releases-list">';
            releases.forEach((release, index) => {
                const typeIcon = release.type === 'anime' ? '🎬' : '📚';
                const typeLabel = release.type === 'anime' ? 'アニメ' : 'マンガ';
                const typeClass = release.type === 'anime' ? 'primary' : 'success';
                const releaseText = release.release_type === 'episode' ? '話' : '巻';
                const platformIcon = getPlatformIcon(release.platform);
                const titleEmoji = getTitleEmoji(release.title);
                const releaseJson = JSON.stringify({...release, release_date: date}).replace(/"/g, '&quot;');

                html += `
                    <div class="list-group-item">
                        <div class="d-flex align-items-start">
                            <!-- チェックボックス -->
                            <div class="form-check me-3 mt-2">
                                <input class="form-check-input release-checkbox"
                                       type="checkbox"
                                       id="release-${index}"
                                       value="${index}"
                                       data-release='${releaseJson}'
                                       checked>
                                <label class="form-check-label" for="release-${index}"></label>
                            </div>

                            <!-- リリース情報 -->
                            <div class="flex-grow-1">
                                <div class="d-flex align-items-center mb-2">
                                    <span class="badge bg-${typeClass} me-2">
                                        ${typeIcon} ${typeLabel}
                                    </span>
                                    <h6 class="mb-0">${titleEmoji} ${release.title}</h6>
                                </div>
                                <p class="mb-1">
                                    <strong>第${release.number}${releaseText}</strong> ·
                                    ${platformIcon} ${release.platform}
                                </p>
                                ${release.source_url ? `<small><a href="${release.source_url}" target="_blank" class="text-decoration-none"><i class="bi bi-box-arrow-up-right me-1"></i>${release.platform}で見る</a></small>` : ''}
                            </div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';

            // 登録ボタン
            html += `
                <div class="d-grid gap-2 mt-3">
                    <button class="btn btn-success btn-lg" onclick="addSelectedToGoogleCalendar()" id="add-selected-btn">
                        <i class="bi bi-calendar-check me-2"></i>
                        選択した項目をGoogleカレンダーに登録
                    </button>
                </div>
            `;
        }

        document.getElementById('modal-body').innerHTML = html;
    };

    // === 18. getReleasesByDate関数（グローバル関数として定義） ===
    window.getReleasesByDate = function(date) {
        // サーバーから渡されたデータを使用
        if (window.releasesData && window.releasesData[date]) {
            return window.releasesData[date];
        }
        return [];
    };

    // === 19. パフォーマンス最適化 ===
    // 画像遅延読み込み
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        observer.unobserve(img);
                    }
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    // === 20. エラーハンドリング ===
    window.addEventListener('error', function(e) {
        console.error('Calendar Enhanced UI Error:', e.error);
    });

    // === 21. グローバル関数として公開（チェックボックス機能用） ===
    window.selectAllReleases = function() {
        document.querySelectorAll('.release-checkbox').forEach(cb => cb.checked = true);
    };

    window.deselectAllReleases = function() {
        document.querySelectorAll('.release-checkbox').forEach(cb => cb.checked = false);
    };

    window.addSelectedToGoogleCalendar = function() {
        const checkboxes = document.querySelectorAll('.release-checkbox:checked');

        if (checkboxes.length === 0) {
            alert('登録する項目を選択してください。');
            return;
        }

        const selectedReleases = Array.from(checkboxes).map(cb => {
            try {
                return JSON.parse(cb.dataset.release.replace(/&quot;/g, '"'));
            } catch (e) {
                console.error('Parse error:', e);
                return null;
            }
        }).filter(r => r !== null);

        if (selectedReleases.length === 0) {
            alert('選択された項目のデータを読み込めませんでした。');
            return;
        }

        const confirmed = confirm(
            `選択した${selectedReleases.length}件をGoogleカレンダーに個別登録しますか？\n\n` +
            `📌 各リリースが別々のイベントとして登録されます\n` +
            `⚠️ ${selectedReleases.length}個のタブが開きます\n` +
            `💡 ポップアップブロックを許可してください`
        );

        if (!confirmed) return;

        // 各リリースを順次タブで開く
        selectedReleases.forEach((release, index) => {
            setTimeout(() => {
                // GoogleCalendarIntegrationが利用可能か確認
                if (window.GoogleCalendarIntegration && window.GoogleCalendarIntegration.generateCalendarUrl) {
                    const url = window.GoogleCalendarIntegration.generateCalendarUrl(release);
                    window.open(url, `gcal_${index}`, 'width=800,height=600');
                } else {
                    // フォールバック: 基本的なURL生成
                    const url = generateBasicCalendarUrl(release);
                    window.open(url, `gcal_${index}`, 'width=800,height=600');
                }
            }, index * 600); // 600ms間隔
        });

        // 完了メッセージ
        setTimeout(() => {
            alert(`✅ ${selectedReleases.length}件のGoogleカレンダー登録画面を開きました！\n\n各タブで「保存」をクリックしてください。`);
        }, selectedReleases.length * 600 + 1000);
    };

    // 基本的なカレンダーURL生成（フォールバック用）
    function generateBasicCalendarUrl(release) {
        const baseUrl = 'https://calendar.google.com/calendar/render?action=TEMPLATE';
        const typeIcon = release.type === 'anime' ? '🎬' : '📚';
        const typeLabel = release.type === 'anime' ? 'アニメ' : 'マンガ';
        const title = `${typeIcon}【${typeLabel}】${release.title} 第${release.number}${release.release_type === 'episode' ? '話' : '巻'} | ${release.platform}`;
        const dateStr = (release.release_date || '').replace(/-/g, '');
        const details = `作品: ${release.title}\nプラットフォーム: ${release.platform}\n${release.source_url ? 'URL: ' + release.source_url : ''}`;

        return `${baseUrl}&text=${encodeURIComponent(title)}&dates=${dateStr}/${dateStr}&details=${encodeURIComponent(details)}`;
    }

    console.log('Calendar Enhanced UI: Script loaded');
})();
