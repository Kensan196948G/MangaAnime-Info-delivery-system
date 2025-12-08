/**
 * E2Eテスト用フィクスチャデータ
 */

export const testWorks = {
  anime: {
    id: 1,
    title: 'テストアニメ作品',
    title_kana: 'てすとあにめさくひん',
    title_en: 'Test Anime Work',
    type: 'anime',
    official_url: 'https://example.com/anime',
  },
  manga: {
    id: 2,
    title: 'テストマンガ作品',
    title_kana: 'てすとまんがさくひん',
    title_en: 'Test Manga Work',
    type: 'manga',
    official_url: 'https://example.com/manga',
  },
};

export const testReleases = {
  episode: {
    id: 1,
    work_id: 1,
    release_type: 'episode',
    number: '1',
    platform: 'dアニメストア',
    release_date: '2025-12-25',
    source: 'anilist',
    source_url: 'https://anilist.co/anime/1',
    notified: 0,
  },
  volume: {
    id: 2,
    work_id: 2,
    release_type: 'volume',
    number: '5',
    platform: 'BookWalker',
    release_date: '2025-12-30',
    source: 'rss',
    source_url: 'https://bookwalker.jp/series/1',
    notified: 0,
  },
};

export const testUsers = {
  admin: {
    email: 'admin@example.com',
    password: 'Admin123!',
    role: 'admin',
  },
  user: {
    email: 'user@example.com',
    password: 'User123!',
    role: 'user',
  },
};

export const testApiResponses = {
  healthCheck: {
    status: 'ok',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
  },
  worksList: {
    total: 2,
    page: 1,
    per_page: 20,
    works: [testWorks.anime, testWorks.manga],
  },
  releasesList: {
    total: 2,
    page: 1,
    per_page: 20,
    releases: [testReleases.episode, testReleases.volume],
  },
};
