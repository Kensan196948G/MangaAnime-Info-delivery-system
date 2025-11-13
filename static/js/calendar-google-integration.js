/**
 * Google Calendar Integration - 全リリース個別登録機能
 * 各リリースを個別のGoogleカレンダーイベントとして登録
 */

(function() {
    'use strict';

    // グローバルに公開
    window.GoogleCalendarIntegration = {
        addSingleRelease,
        addAllReleases,
        addDayReleases,
        generateCalendarUrl
    };

    /**
     * 単一リリースをGoogleカレンダーに追加
     */
    function addSingleRelease(release) {
        const url = generateCalendarUrl(release);
        window.open(url, '_blank', 'width=800,height=600');
    }

    /**
     * 1日のリリース全てをGoogleカレンダーに追加
     */
    function addDayReleases(releases) {
        if (!releases || releases.length === 0) {
            alert('リリース情報がありません。');
            return;
        }

        const confirmed = confirm(
            `この日の${releases.length}件のリリースを個別にGoogleカレンダーに登録しますか？\n\n` +
            `各リリースが別々のタブで開かれます。\n` +
            `ブラウザのポップアップブロックを許可してください。`
        );

        if (!confirmed) return;

        // 各リリースを順次開く（500ms間隔）
        releases.forEach((release, index) => {
            setTimeout(() => {
                const url = generateCalendarUrl(release);
                window.open(url, `_blank_${index}`, 'width=800,height=600');
            }, index * 500);
        });

        // 完了メッセージ
        setTimeout(() => {
            alert(`${releases.length}件のGoogleカレンダー登録画面を開きました。\n各タブで「保存」をクリックしてください。`);
        }, releases.length * 500 + 500);
    }

    /**
     * 月の全リリースをGoogleカレンダーに追加
     */
    function addAllReleases() {
        if (!window.releasesData) {
            alert('リリースデータが読み込まれていません。');
            return;
        }

        // 全リリースを配列にまとめる
        const allReleases = [];
        Object.keys(window.releasesData).forEach(date => {
            window.releasesData[date].forEach(release => {
                allReleases.push({...release, release_date: date});
            });
        });

        if (allReleases.length === 0) {
            alert('登録するリリースがありません。');
            return;
        }

        // グローバル変数に保存（バッチ処理用）
        window.allReleasesForCalendar = allReleases;

        const confirmed = confirm(
            `今月の全リリース ${allReleases.length}件をGoogleカレンダーに個別登録しますか？\n\n` +
            `📌 各リリースが別々のイベントとして登録されます\n` +
            `⚠️ ${allReleases.length}個のタブが開きます\n` +
            `💡 10件ずつバッチ処理で登録します\n\n` +
            `続行しますか？`
        );

        if (!confirmed) return;

        // 確認: 一度に開く件数を制限
        const batchSize = 10;
        const batches = Math.ceil(allReleases.length / batchSize);

        alert(
            `📊 登録処理を開始します\n\n` +
            `総件数: ${allReleases.length}件\n` +
            `バッチ数: ${batches}回\n` +
            `1バッチ: 最大10件\n\n` +
            `まず最初の${Math.min(batchSize, allReleases.length)}件を開きます。`
        );

        // 最初のバッチを開く
        const firstBatch = allReleases.slice(0, batchSize);
        openReleaseBatch(firstBatch, 1, batches);
    }

    /**
     * リリースのバッチを開く
     */
    function openReleaseBatch(releases, currentBatch, totalBatches) {
        releases.forEach((release, index) => {
            setTimeout(() => {
                const url = generateCalendarUrl(release);
                window.open(url, `_blank_batch${currentBatch}_${index}`, 'width=800,height=600');
            }, index * 500);
        });

        // 次のバッチの確認
        if (currentBatch < totalBatches) {
            setTimeout(() => {
                const nextBatch = confirm(
                    `バッチ ${currentBatch}/${totalBatches} 完了。\n\n` +
                    `次の10件を登録しますか？`
                );

                if (nextBatch) {
                    const batchSize = 10;
                    const start = currentBatch * batchSize;
                    const nextReleases = window.allReleasesForCalendar.slice(start, start + batchSize);
                    openReleaseBatch(nextReleases, currentBatch + 1, totalBatches);
                }
            }, releases.length * 500 + 1000);
        }
    }

    /**
     * Googleカレンダー登録URL生成
     */
    function generateCalendarUrl(release) {
        const baseUrl = 'https://calendar.google.com/calendar/render?action=TEMPLATE';

        // タイトル生成（絵文字付き）
        const typeIcon = release.type === 'anime' ? '🎬' : '📚';
        const typeLabel = release.type === 'anime' ? 'アニメ' : 'マンガ';
        const platformIcon = getPlatformIcon(release.platform);
        const titleEmoji = getTitleEmoji(release.title);

        const title = `${typeIcon}【${typeLabel}】${titleEmoji}${release.title} ` +
                     `第${release.number}${release.release_type === 'episode' ? '話' : '巻'} | ` +
                     `${platformIcon}${release.platform}`;

        // 説明文生成
        const details = [
            `作品: ${release.title}`,
            `タイプ: ${typeLabel}`,
            `${release.release_type === 'episode' ? 'エピソード' : '巻'}: 第${release.number}${release.release_type === 'episode' ? '話' : '巻'}`,
            `配信プラットフォーム: ${release.platform}`,
            release.source_url ? `\nソースURL: ${release.source_url}` : '',
            release.official_url ? `公式サイト: ${release.official_url}` : '',
            `\n---`,
            `自動登録: MangaAnime情報配信システム`
        ].filter(Boolean).join('\n');

        // 日付フォーマット（YYYYMMDD）
        const dateStr = (release.release_date || release.date || '').replace(/-/g, '');

        // URL生成
        let url = baseUrl;
        url += `&text=${encodeURIComponent(title)}`;
        url += `&dates=${dateStr}/${dateStr}`;
        url += `&details=${encodeURIComponent(details)}`;
        url += `&location=${encodeURIComponent(release.platform)}`;

        // アニメとマンガで色を変える（オプション、一部ブラウザのみ対応）
        if (release.type === 'anime') {
            url += '&ctz=Asia/Tokyo';
        }

        return url;
    }

    /**
     * プラットフォームアイコン取得
     */
    function getPlatformIcon(platform) {
        if (!platform) return '';

        const key = platform.toLowerCase();
        for (const [keyword, icon] of Object.entries(window.PLATFORM_ICONS || {})) {
            if (key.includes(keyword.toLowerCase())) {
                return icon;
            }
        }

        return '';
    }

    /**
     * タイトル絵文字取得
     */
    function getTitleEmoji(title) {
        if (!title) return '';

        const titleLower = title.toLowerCase();
        for (const [keyword, emoji] of Object.entries(window.TITLE_EMOJIS || {})) {
            if (titleLower.includes(keyword.toLowerCase()) ||
                title.includes(keyword)) {
                return emoji;
            }
        }

        return '';
    }

    /**
     * ヘルパー: プラットフォーム別アイコン
     */
    const getPlatformIconHelper = (platform) => {
        const icons = {
            'netflix': '🎬',
            'amazon': '📺',
            'prime': '📺',
            'crunchyroll': '🌸',
            'dアニメ': '🎭',
            'bookwalker': '📚',
            'kindle': '📖',
            'ジャンプ': '⚡',
            'マガポケ': '📱',
            'hulu': '📹',
            'disney': '🎪',
            'abema': '📡',
            'funimation': '🎞️',
            'kobo': '📕'
        };

        const platformLower = (platform || '').toLowerCase();
        for (const [key, icon] of Object.entries(icons)) {
            if (platformLower.includes(key)) {
                return icon;
            }
        }
        return '📺';
    };

    /**
     * データから日付別リリース取得
     */
    function getReleasesByDate(date) {
        return window.releasesData && window.releasesData[date] ? window.releasesData[date] : [];
    }

    // === 5. その他のUI強化関数（既存のcalendar-enhanced.jsから移動） ===

    function addTodayHighlight() {
        const today = new Date().toISOString().split('T')[0];
        const todayCell = document.querySelector(`[data-date="${today}"]`);
        if (todayCell) {
            todayCell.classList.add('today');
        }
    }

    function enhanceReleaseItems() {
        const releaseItems = document.querySelectorAll('.release-item');

        releaseItems.forEach(item => {
            const platform = item.dataset.platform;
            const title = item.dataset.title;

            if (platform) {
                const icon = getPlatformIconHelper(platform);
                const titleDiv = item.querySelector('.release-title');
                if (titleDiv && icon) {
                    titleDiv.textContent = `${icon} ${titleDiv.textContent}`;
                }
            }

            if (title) {
                const emoji = getTitleEmoji(title);
                if (emoji) {
                    const titleDiv = item.querySelector('.release-title');
                    if (titleDiv) {
                        titleDiv.textContent = `${emoji}${titleDiv.textContent.replace(/^[🎬📺🌸🎭📚📖⚡📱📹🎪📡🎞️📕]\s*/, '')}`;
                    }
                }
            }
        });
    }

    function addSwipeNavigation() {
        let touchStartX = 0;
        let touchEndX = 0;

        document.addEventListener('touchstart', e => {
            touchStartX = e.changedTouches[0].screenX;
        }, {passive: true});

        document.addEventListener('touchend', e => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        }, {passive: true});

        function handleSwipe() {
            const swipeThreshold = 100;

            if (touchEndX < touchStartX - swipeThreshold) {
                // 左スワイプ - 次月
                const nextBtn = document.querySelector('a[href*="month="]');
                if (nextBtn && nextBtn.textContent.includes('次月')) {
                    window.location.href = nextBtn.href;
                }
            }

            if (touchEndX > touchStartX + swipeThreshold) {
                // 右スワイプ - 前月
                const prevBtn = document.querySelector('a[href*="month="]');
                if (prevBtn && prevBtn.textContent.includes('前月')) {
                    window.location.href = prevBtn.href;
                }
            }
        }
    }

    function addKeyboardNavigation() {
        document.addEventListener('keydown', e => {
            if (e.altKey) {
                if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    const prevBtn = document.querySelector('a.btn-outline-primary');
                    if (prevBtn) prevBtn.click();
                } else if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    const nextBtns = document.querySelectorAll('a.btn-outline-primary');
                    if (nextBtns[1]) nextBtns[1].click();
                }
            }
        });
    }

    function addTooltips() {
        const releaseItems = document.querySelectorAll('.release-item');
        releaseItems.forEach(item => {
            if (!item.hasAttribute('title')) {
                const title = item.dataset.title || '';
                const platform = item.dataset.platform || '';
                if (title && platform) {
                    item.setAttribute('title', `${title} - ${platform}`);
                }
            }
        });
    }

    /**
     * 日付詳細モーダルを表示（拡張版）
     */
    window.showDayDetailsEnhanced = function(date) {
        const releases = getReleasesByDate(date);

        if (releases.length === 0) {
            document.getElementById('modal-body').innerHTML =
                '<p class="text-muted text-center">この日にリリース予定はありません。</p>';
            return;
        }

        // フォーマット済み日付
        const dateObj = new Date(date + 'T00:00:00');
        const formattedDate = dateObj.toLocaleDateString('ja-JP', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            weekday: 'long'
        });

        document.getElementById('modal-date').textContent = formattedDate;

        // モーダルボディHTML生成
        let html = '<div class="list-group list-group-flush">';

        releases.forEach((release, index) => {
            const typeIcon = release.type === 'anime' ? '🎬' : '📚';
            const typeLabel = release.type === 'anime' ? 'アニメ' : 'マンガ';
            const typeClass = release.type === 'anime' ? 'primary' : 'success';
            const platformIcon = getPlatformIconHelper(release.platform);
            const titleEmoji = getTitleEmoji(release.title);
            const releaseText = release.release_type === 'episode' ? '話' : '巻';

            html += `
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <div class="d-flex align-items-center mb-2">
                                <span class="badge bg-${typeClass} me-2">
                                    ${typeIcon} ${typeLabel}
                                </span>
                                <h6 class="mb-0">${titleEmoji}${release.title}</h6>
                            </div>
                            <p class="mb-1">
                                <strong>第${release.number}${releaseText}</strong> ·
                                ${platformIcon}${release.platform}
                            </p>
                            ${release.source_url ?
                                `<small>
                                    <a href="${release.source_url}" target="_blank" class="text-decoration-none">
                                        <i class="bi bi-box-arrow-up-right me-1"></i>${release.platform}で見る
                                    </a>
                                </small>` : ''}
                        </div>
                        <div>
                            <button class="btn btn-sm btn-outline-primary"
                                    onclick="GoogleCalendarIntegration.addSingleRelease(${JSON.stringify(release).replace(/"/g, '&quot;')})"
                                    title="このリリースをGoogleカレンダーに追加">
                                <i class="bi bi-calendar-plus"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div>';

        // モーダルフッターのボタンを更新
        html += `
            <div class="d-grid gap-2 mt-3">
                <button class="btn btn-primary" onclick="GoogleCalendarIntegration.addDayReleases(window.releasesData['${date}'])">
                    <i class="bi bi-calendar-check me-2"></i>
                    この日の全リリース（${releases.length}件）をGoogleカレンダーに登録
                </button>
            </div>
        `;

        document.getElementById('modal-body').innerHTML = html;
    };

    // showDayDetailsのオーバーライド
    if (typeof window.showDayDetails === 'undefined') {
        window.showDayDetails = window.showDayDetailsEnhanced;
    }

    console.log('Google Calendar Integration: Loaded');

})();
