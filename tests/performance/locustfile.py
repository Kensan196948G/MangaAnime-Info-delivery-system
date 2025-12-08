"""
Locust負荷テストシナリオ
MangaAnime-Info-delivery-system用
"""

from locust import HttpUser, task, between, tag
from random import randint, choice
import json


class AnimeUserBehavior(HttpUser):
    """
    一般的なユーザー行動をシミュレート
    """

    wait_time = between(1, 5)  # リクエスト間隔: 1-5秒

    def on_start(self):
        """テスト開始時の初期化処理"""
        self.work_ids = []
        self.release_ids = []

        # ヘルスチェック
        with self.client.get("/api/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @tag("homepage")
    @task(10)
    def view_homepage(self):
        """ホームページ閲覧（最も頻繁な操作）"""
        self.client.get("/")

    @tag("works")
    @task(8)
    def view_works_list(self):
        """作品一覧閲覧"""
        params = {
            "page": randint(1, 5),
            "per_page": 20,
        }
        with self.client.get("/api/works", params=params, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "works" in data:
                    self.work_ids = [work["id"] for work in data["works"][:5]]
                    response.success()
                else:
                    response.failure("No works data in response")
            else:
                response.failure(f"Failed to get works: {response.status_code}")

    @tag("works", "detail")
    @task(5)
    def view_work_detail(self):
        """作品詳細閲覧"""
        if self.work_ids:
            work_id = choice(self.work_ids)
            self.client.get(f"/api/works/{work_id}")
        else:
            # フォールバック: ランダムID
            self.client.get(f"/api/works/{randint(1, 100)}")

    @tag("releases")
    @task(7)
    def view_releases_list(self):
        """リリース情報一覧閲覧"""
        params = {
            "page": randint(1, 10),
            "per_page": 20,
        }
        with self.client.get("/api/releases", params=params, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "releases" in data:
                    self.release_ids = [rel["id"] for rel in data["releases"][:5]]
                    response.success()
                else:
                    response.failure("No releases data in response")

    @tag("releases", "latest")
    @task(6)
    def view_latest_releases(self):
        """最新リリース情報閲覧"""
        self.client.get("/api/releases/latest")

    @tag("search")
    @task(4)
    def search_works(self):
        """作品検索"""
        search_terms = ["テスト", "アニメ", "マンガ", "新作", "人気"]
        params = {"q": choice(search_terms)}
        self.client.get("/api/search", params=params)

    @tag("filter")
    @task(3)
    def filter_by_type(self):
        """タイプフィルター"""
        work_type = choice(["anime", "manga"])
        params = {"type": work_type}
        self.client.get("/api/works", params=params)

    @tag("filter")
    @task(3)
    def filter_by_platform(self):
        """プラットフォームフィルター"""
        platforms = ["dアニメストア", "Netflix", "Amazon Prime", "BookWalker"]
        params = {"platform": choice(platforms)}
        self.client.get("/api/releases", params=params)

    @tag("calendar")
    @task(2)
    def view_calendar_events(self):
        """カレンダーイベント取得"""
        params = {"month": "2025-12"}
        self.client.get("/api/calendar/events", params=params)


class PowerUserBehavior(HttpUser):
    """
    パワーユーザー（高頻度利用者）の行動をシミュレート
    """

    wait_time = between(0.5, 2)  # より短い間隔

    def on_start(self):
        """テスト開始時の初期化"""
        self.token = None
        # 認証（モック）
        # 実際の環境では適切な認証処理を実装

    @tag("intensive")
    @task(5)
    def rapid_page_navigation(self):
        """高速なページ遷移"""
        endpoints = [
            "/",
            "/api/works",
            "/api/releases",
            "/api/releases/latest",
        ]
        for endpoint in endpoints:
            self.client.get(endpoint)

    @tag("intensive", "search")
    @task(3)
    def multiple_searches(self):
        """複数の検索を連続実行"""
        search_terms = ["人気", "新作", "続編", "完結", "話題"]
        for term in search_terms[:3]:
            self.client.get("/api/search", params={"q": term})

    @tag("intensive", "filter")
    @task(2)
    def complex_filtering(self):
        """複雑なフィルタリング"""
        params = {
            "type": "anime",
            "platform": "dアニメストア",
            "start_date": "2025-12-01",
            "end_date": "2025-12-31",
            "sort": "release_date_asc",
        }
        self.client.get("/api/releases", params=params)


class AdminUserBehavior(HttpUser):
    """
    管理者操作をシミュレート
    """

    wait_time = between(2, 10)

    def on_start(self):
        """管理者認証"""
        # 実際の認証処理
        pass

    @tag("admin", "write")
    @task(2)
    def create_work(self):
        """作品作成"""
        data = {
            "title": f"テスト作品{randint(1000, 9999)}",
            "type": choice(["anime", "manga"]),
            "official_url": "https://example.com/test",
        }
        headers = {"Content-Type": "application/json"}
        # 認証トークンが必要
        self.client.post("/api/works", json=data, headers=headers, catch_response=True)

    @tag("admin", "write")
    @task(3)
    def create_release(self):
        """リリース作成"""
        data = {
            "work_id": randint(1, 100),
            "release_type": choice(["episode", "volume"]),
            "number": str(randint(1, 12)),
            "platform": choice(["dアニメストア", "Netflix"]),
            "release_date": "2025-12-25",
        }
        headers = {"Content-Type": "application/json"}
        self.client.post("/api/releases", json=data, headers=headers, catch_response=True)

    @tag("admin", "read")
    @task(5)
    def view_dashboard(self):
        """管理ダッシュボード閲覧"""
        self.client.get("/admin/dashboard", catch_response=True)


class StressTestUser(HttpUser):
    """
    ストレステスト用の過負荷シナリオ
    """

    wait_time = between(0.1, 0.5)  # 非常に短い間隔

    @tag("stress")
    @task
    def stress_api(self):
        """APIに高負荷をかける"""
        endpoints = [
            "/api/health",
            "/api/works",
            "/api/releases",
            "/api/releases/latest",
        ]
        self.client.get(choice(endpoints))


class SpikeTestUser(HttpUser):
    """
    スパイクテスト用（急激な負荷増加）
    """

    wait_time = between(0, 0.1)

    @tag("spike")
    @task
    def spike_load(self):
        """急激な負荷"""
        self.client.get("/api/works")
        self.client.get("/api/releases")


# カスタムイベントフック
from locust import events


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """テスト開始時の処理"""
    print("=" * 60)
    print("負荷テスト開始")
    print(f"Target: {environment.host}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """テスト終了時の処理"""
    print("=" * 60)
    print("負荷テスト完了")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Failed requests: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print("=" * 60)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """各リクエストのログ"""
    if exception:
        print(f"Request failed: {name} - {exception}")


# カスタムテストシナリオ
class CustomLoadTest(HttpUser):
    """
    カスタム負荷テストシナリオ
    ユーザーのジャーニーをシミュレート
    """

    wait_time = between(1, 3)

    @task
    def user_journey(self):
        """
        ユーザージャーニー全体をシミュレート
        1. ホームページ訪問
        2. 作品一覧閲覧
        3. 作品詳細表示
        4. リリース情報確認
        5. 検索実行
        """
        # 1. ホームページ
        with self.client.get("/", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure("Homepage failed")
                return

        self.client.wait()  # 1-3秒待機

        # 2. 作品一覧
        with self.client.get("/api/works", catch_response=True) as resp:
            if resp.status_code == 200:
                works = resp.json().get("works", [])
                if works:
                    work_id = works[0]["id"]
                else:
                    resp.failure("No works found")
                    return
            else:
                resp.failure("Works list failed")
                return

        self.client.wait()

        # 3. 作品詳細
        with self.client.get(f"/api/works/{work_id}", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure("Work detail failed")
                return

        self.client.wait()

        # 4. リリース情報
        self.client.get("/api/releases/latest")

        self.client.wait()

        # 5. 検索
        self.client.get("/api/search", params={"q": "テスト"})
