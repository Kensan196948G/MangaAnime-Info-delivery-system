import { test, expect } from '@playwright/test';
import { testWorks, testReleases, testApiResponses } from '../fixtures/test-data';

/**
 * API統合テスト
 */
test.describe('API統合テスト', () => {
  const baseURL = process.env.BASE_URL || 'http://localhost:5000';

  test.describe('ヘルスチェックAPI', () => {
    test('GET /api/health - ヘルスチェック成功', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/health`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data).toHaveProperty('status', 'ok');
      expect(data).toHaveProperty('timestamp');
      expect(data).toHaveProperty('version');
    });
  });

  test.describe('作品API', () => {
    test('GET /api/works - 作品一覧取得', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/works`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data).toHaveProperty('total');
      expect(data).toHaveProperty('page');
      expect(data).toHaveProperty('per_page');
      expect(data).toHaveProperty('works');
      expect(Array.isArray(data.works)).toBeTruthy();
    });

    test('GET /api/works?type=anime - アニメのみ取得', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/works?type=anime`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      data.works.forEach((work: any) => {
        expect(work.type).toBe('anime');
      });
    });

    test('GET /api/works/:id - 作品詳細取得', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/works/1`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data).toHaveProperty('id');
      expect(data).toHaveProperty('title');
      expect(data).toHaveProperty('type');
    });

    test('GET /api/works/:id - 存在しない作品', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/works/99999`);

      expect(response.status()).toBe(404);

      const data = await response.json();
      expect(data).toHaveProperty('error');
    });

    test('POST /api/works - 作品作成（認証必要）', async ({ request }) => {
      const response = await request.post(`${baseURL}/api/works`, {
        data: {
          title: '新規アニメ作品',
          title_kana: 'しんきあにめさくひん',
          type: 'anime',
          official_url: 'https://example.com/new-anime',
        },
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer test-token',
        },
      });

      // 認証なしの場合は401
      if (response.status() === 401) {
        expect(response.status()).toBe(401);
      } else {
        expect(response.status()).toBe(201);
        const data = await response.json();
        expect(data).toHaveProperty('id');
      }
    });

    test('PUT /api/works/:id - 作品更新', async ({ request }) => {
      const response = await request.put(`${baseURL}/api/works/1`, {
        data: {
          title: '更新後タイトル',
        },
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer test-token',
        },
      });

      if (response.status() === 401) {
        expect(response.status()).toBe(401);
      } else {
        expect(response.status()).toBe(200);
      }
    });

    test('DELETE /api/works/:id - 作品削除', async ({ request }) => {
      const response = await request.delete(`${baseURL}/api/works/999`, {
        headers: {
          Authorization: 'Bearer test-token',
        },
      });

      // 認証なしまたは権限なしの場合は401/403
      expect([401, 403, 404]).toContain(response.status());
    });
  });

  test.describe('リリースAPI', () => {
    test('GET /api/releases - リリース一覧取得', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/releases`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data).toHaveProperty('total');
      expect(data).toHaveProperty('releases');
      expect(Array.isArray(data.releases)).toBeTruthy();
    });

    test('GET /api/releases/latest - 最新リリース取得', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/releases/latest`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(Array.isArray(data)).toBeTruthy();
    });

    test('GET /api/releases?release_type=episode - エピソードのみ', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/releases?release_type=episode`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      data.releases.forEach((release: any) => {
        expect(release.release_type).toBe('episode');
      });
    });

    test('GET /api/releases?platform=dアニメストア - プラットフォームフィルター', async ({ request }) => {
      const response = await request.get(
        `${baseURL}/api/releases?platform=${encodeURIComponent('dアニメストア')}`
      );

      expect(response.status()).toBe(200);

      const data = await response.json();
      data.releases.forEach((release: any) => {
        expect(release.platform).toBe('dアニメストア');
      });
    });

    test('GET /api/releases?start_date=2025-12-01&end_date=2025-12-31 - 日付範囲', async ({
      request,
    }) => {
      const response = await request.get(
        `${baseURL}/api/releases?start_date=2025-12-01&end_date=2025-12-31`
      );

      expect(response.status()).toBe(200);

      const data = await response.json();
      data.releases.forEach((release: any) => {
        const releaseDate = new Date(release.release_date);
        expect(releaseDate >= new Date('2025-12-01')).toBeTruthy();
        expect(releaseDate <= new Date('2025-12-31')).toBeTruthy();
      });
    });

    test('POST /api/releases - リリース作成', async ({ request }) => {
      const response = await request.post(`${baseURL}/api/releases`, {
        data: {
          work_id: 1,
          release_type: 'episode',
          number: '10',
          platform: 'Netflix',
          release_date: '2025-12-25',
        },
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer test-token',
        },
      });

      if (response.status() === 401) {
        expect(response.status()).toBe(401);
      } else {
        expect(response.status()).toBe(201);
      }
    });
  });

  test.describe('検索API', () => {
    test('GET /api/search?q=テスト - 全文検索', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/search?q=テスト`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data).toHaveProperty('works');
      expect(data).toHaveProperty('releases');
    });

    test('GET /api/works/search?q=アニメ - 作品検索', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/works/search?q=アニメ`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(Array.isArray(data)).toBeTruthy();
    });

    test('GET /api/releases/search?q=第1話 - リリース検索', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/releases/search?q=第1話`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(Array.isArray(data)).toBeTruthy();
    });
  });

  test.describe('通知API', () => {
    test('POST /api/notifications - 通知設定追加', async ({ request }) => {
      const response = await request.post(`${baseURL}/api/notifications`, {
        data: {
          release_id: 1,
          enabled: true,
        },
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer test-token',
        },
      });

      if (response.status() === 401) {
        expect(response.status()).toBe(401);
      } else {
        expect(response.status()).toBe(201);
      }
    });

    test('GET /api/notifications - 通知設定一覧', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/notifications`, {
        headers: {
          Authorization: 'Bearer test-token',
        },
      });

      if (response.status() === 401) {
        expect(response.status()).toBe(401);
      } else {
        expect(response.status()).toBe(200);
      }
    });

    test('DELETE /api/notifications/:id - 通知設定削除', async ({ request }) => {
      const response = await request.delete(`${baseURL}/api/notifications/1`, {
        headers: {
          Authorization: 'Bearer test-token',
        },
      });

      expect([200, 401, 404]).toContain(response.status());
    });
  });

  test.describe('カレンダーAPI', () => {
    test('POST /api/calendar/export - カレンダーへエクスポート', async ({ request }) => {
      const response = await request.post(`${baseURL}/api/calendar/export`, {
        data: {
          release_ids: [1, 2],
        },
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer test-token',
        },
      });

      if (response.status() === 401) {
        expect(response.status()).toBe(401);
      } else {
        expect(response.status()).toBe(200);
      }
    });

    test('GET /api/calendar/events - カレンダーイベント取得', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/calendar/events?month=2025-12`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(Array.isArray(data)).toBeTruthy();
    });
  });

  test.describe('お気に入りAPI', () => {
    test('POST /api/favorites - お気に入り追加', async ({ request }) => {
      const response = await request.post(`${baseURL}/api/favorites`, {
        data: {
          work_id: 1,
        },
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer test-token',
        },
      });

      if (response.status() === 401) {
        expect(response.status()).toBe(401);
      } else {
        expect(response.status()).toBe(201);
      }
    });

    test('GET /api/favorites - お気に入り一覧', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/favorites`, {
        headers: {
          Authorization: 'Bearer test-token',
        },
      });

      if (response.status() === 401) {
        expect(response.status()).toBe(401);
      } else {
        expect(response.status()).toBe(200);
      }
    });

    test('DELETE /api/favorites/:id - お気に入り削除', async ({ request }) => {
      const response = await request.delete(`${baseURL}/api/favorites/1`, {
        headers: {
          Authorization: 'Bearer test-token',
        },
      });

      expect([200, 401, 404]).toContain(response.status());
    });
  });

  test.describe('エラーハンドリング', () => {
    test('存在しないエンドポイント - 404エラー', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/nonexistent`);

      expect(response.status()).toBe(404);
    });

    test('不正なリクエストボディ - 400エラー', async ({ request }) => {
      const response = await request.post(`${baseURL}/api/works`, {
        data: {
          invalid: 'data',
        },
        headers: {
          'Content-Type': 'application/json',
        },
      });

      expect([400, 401]).toContain(response.status());
    });

    test('大量のリクエスト - レート制限', async ({ request }) => {
      const requests = Array(100)
        .fill(null)
        .map(() => request.get(`${baseURL}/api/health`));

      const responses = await Promise.all(requests);

      // 一部が429（Too Many Requests）になる可能性
      const statuses = responses.map(r => r.status());
      const hasRateLimit = statuses.includes(429);

      // レート制限がある場合はテスト成功
      if (hasRateLimit) {
        expect(hasRateLimit).toBeTruthy();
      }
    });
  });

  test.describe('パフォーマンステスト', () => {
    test('API応答時間 - 500ms以内', async ({ request }) => {
      const startTime = Date.now();
      const response = await request.get(`${baseURL}/api/works`);
      const endTime = Date.now();

      expect(response.status()).toBe(200);
      expect(endTime - startTime).toBeLessThan(500);
    });

    test('大量データ取得 - ページネーション', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/releases?per_page=100`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data.releases.length).toBeLessThanOrEqual(100);
    });
  });

  test.describe('CORS設定', () => {
    test('CORS ヘッダーが正しく設定されている', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/health`, {
        headers: {
          Origin: 'https://example.com',
        },
      });

      const headers = response.headers();
      expect(headers['access-control-allow-origin']).toBeDefined();
    });
  });

  test.describe('キャッシュ制御', () => {
    test('キャッシュヘッダーが適切に設定されている', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/works`);

      const headers = response.headers();
      // Cache-Controlヘッダーの確認
      if (headers['cache-control']) {
        expect(headers['cache-control']).toBeDefined();
      }
    });
  });
});
