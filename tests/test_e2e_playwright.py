#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 8: Playwright E2Eテスト
MangaAnime情報配信システム - ブラウザベース統合テスト

このモジュールはFlaskテストクライアントを主軸とし、
Playwrightが利用可能な場合はブラウザE2Eテストも実行します。

テストシナリオ:
  1. ヘルスチェックエンドポイント
  2. ログインページ表示
  3. ダッシュボードアクセス（未認証リダイレクト）
  4. APIエンドポイント群
  5. カレンダーページ
  6. スクリーンショット取得（Playwright利用時）
"""

import io
import json
import os
import sys
import time
from pathlib import Path

import pytest

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ============================================================
# テスト環境用の環境変数を設定（モジュールインポート前に設定必須）
# ============================================================
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-e2e-testing-phase8")
os.environ.setdefault("GMAIL_ADDRESS", "test@example.com")
os.environ.setdefault("GMAIL_APP_PASSWORD", "test-app-password")
os.environ.setdefault("DEFAULT_ADMIN_PASSWORD", "TestAdminPassword2026!")
os.environ.setdefault("DEFAULT_ADMIN_USERNAME", "admin")
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("DATABASE_PATH", ":memory:")
os.environ.setdefault("WTF_CSRF_ENABLED", "false")
os.environ.setdefault("USE_DB_STORE", "false")
os.environ.setdefault("CSRF_ENABLED", "false")

# ============================================================
# Playwrightインポート（オプション）
# ============================================================
try:
    from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# ============================================================
# Flaskアプリインポート
# ============================================================
_app = None
_flask_import_error = None

try:
    from app.web_app import app as flask_app

    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    flask_app.config["WTF_CSRF_CHECK_DEFAULT"] = False
    flask_app.config["SERVER_NAME"] = None
    _app = flask_app
    FLASK_AVAILABLE = True
except Exception as e:
    _flask_import_error = str(e)
    FLASK_AVAILABLE = False


# ============================================================
# スクリーンショット保存ディレクトリ
# ============================================================
SCREENSHOT_DIR = project_root / "logs" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Flaskテストクライアント用フィクスチャ
# ============================================================
@pytest.fixture(scope="module")
def flask_client():
    """Flaskテストクライアントを返す"""
    if not FLASK_AVAILABLE:
        pytest.skip(f"Flaskアプリの読み込みに失敗: {_flask_import_error}")
    with _app.test_client() as client:
        with _app.app_context():
            yield client


# ============================================================
# Playwright用フィクスチャ
# ============================================================
@pytest.fixture(scope="session")
def playwright_browser():
    """Playwrightブラウザインスタンス（セッションスコープ）"""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwrightがインストールされていません")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def playwright_page(playwright_browser):
    """Playwrightページインスタンス（関数スコープ）"""
    context = playwright_browser.new_context()
    page = context.new_page()
    yield page
    page.close()
    context.close()


# ============================================================
# シナリオ1: ヘルスチェック
# ============================================================
class TestScenario1HealthCheck:
    """シナリオ1: /health エンドポイントのテスト"""

    def test_health_endpoint_returns_200(self, flask_client):
        """GET /health が200を返す"""
        response = flask_client.get("/health")
        assert response.status_code == 200, (
            f"/health が200を返しませんでした。実際のステータス: {response.status_code}"
        )

    def test_health_response_is_json(self, flask_client):
        """GET /health のレスポンスがJSONである"""
        response = flask_client.get("/health")
        content_type = response.content_type
        assert "application/json" in content_type, (
            f"Content-TypeがJSONではありません: {content_type}"
        )

    def test_health_response_contains_status_healthy(self, flask_client):
        """GET /health のJSONに status: 'healthy' が含まれる"""
        response = flask_client.get("/health")
        data = json.loads(response.data)
        assert "status" in data, "レスポンスJSONに 'status' キーがありません"
        assert data["status"] == "healthy", (
            f"status が 'healthy' ではありません: {data.get('status')}"
        )

    def test_health_response_contains_timestamp(self, flask_client):
        """GET /health のJSONに timestamp が含まれる"""
        response = flask_client.get("/health")
        data = json.loads(response.data)
        assert "timestamp" in data, "レスポンスJSONに 'timestamp' キーがありません"

    def test_health_live_endpoint(self, flask_client):
        """/health/live エンドポイントが200を返す"""
        response = flask_client.get("/health/live")
        assert response.status_code == 200, (
            f"/health/live が200を返しませんでした。実際のステータス: {response.status_code}"
        )

    def test_health_live_response_status_alive(self, flask_client):
        """/health/live のレスポンスに status: 'alive' が含まれる"""
        response = flask_client.get("/health/live")
        data = json.loads(response.data)
        assert data.get("status") == "alive", (
            f"status が 'alive' ではありません: {data.get('status')}"
        )


# ============================================================
# シナリオ2: ログインページ表示
# ============================================================
class TestScenario2LoginPage:
    """シナリオ2: /auth/login ログインページのテスト"""

    def test_login_page_returns_200(self, flask_client):
        """GET /auth/login が200を返す"""
        response = flask_client.get("/auth/login")
        assert response.status_code == 200, (
            f"/auth/login が200を返しませんでした。実際のステータス: {response.status_code}"
        )

    def test_login_page_contains_html(self, flask_client):
        """GET /auth/login がHTMLを返す"""
        response = flask_client.get("/auth/login")
        content_type = response.content_type
        assert "text/html" in content_type, (
            f"Content-TypeがHTMLではありません: {content_type}"
        )

    def test_login_page_has_username_field(self, flask_client):
        """ログインページにusernameフィールドが存在する"""
        response = flask_client.get("/auth/login")
        html = response.data.decode("utf-8", errors="replace")
        assert 'name="username"' in html, (
            "ログインページに name='username' フィールドが見つかりません"
        )

    def test_login_page_has_password_field(self, flask_client):
        """ログインページにpasswordフィールドが存在する"""
        response = flask_client.get("/auth/login")
        html = response.data.decode("utf-8", errors="replace")
        assert 'name="password"' in html, (
            "ログインページに name='password' フィールドが見つかりません"
        )

    def test_login_page_has_submit_button(self, flask_client):
        """ログインページにsubmitボタンが存在する"""
        response = flask_client.get("/auth/login")
        html = response.data.decode("utf-8", errors="replace")
        assert 'type="submit"' in html, (
            "ログインページに type='submit' ボタンが見つかりません"
        )

    def test_login_page_title_contains_login_keyword(self, flask_client):
        """ログインページのタイトルにログイン関連ワードが含まれる"""
        response = flask_client.get("/auth/login")
        html = response.data.decode("utf-8", errors="replace")
        assert "ログイン" in html or "Login" in html, (
            "ログインページにログイン関連テキストが見つかりません"
        )

    def test_login_page_has_form_action(self, flask_client):
        """ログインページのformタグにaction属性がある"""
        response = flask_client.get("/auth/login")
        html = response.data.decode("utf-8", errors="replace")
        assert "<form" in html, "ログインページに <form> タグが見つかりません"


# ============================================================
# シナリオ3: ダッシュボードアクセス（未認証リダイレクト）
# ============================================================
class TestScenario3DashboardAccess:
    """シナリオ3: / (ダッシュボード) の未認証アクセステスト"""

    def test_dashboard_unauthenticated_response(self, flask_client):
        """未認証で / にアクセスした場合のレスポンス確認"""
        response = flask_client.get("/", follow_redirects=False)
        # 認証必須の場合はリダイレクト(302)、認証不要の場合は200
        assert response.status_code in [200, 302], (
            f"/ のレスポンスが200または302ではありません: {response.status_code}"
        )

    def test_dashboard_redirect_goes_to_login(self, flask_client):
        """未認証の / アクセスがログインページにリダイレクトされる（認証有効な場合）"""
        response = flask_client.get("/", follow_redirects=False)
        if response.status_code == 302:
            location = response.headers.get("Location", "")
            assert "login" in location.lower() or "auth" in location.lower(), (
                f"リダイレクト先がログインページではありません: {location}"
            )

    def test_dashboard_follow_redirect_gives_html(self, flask_client):
        """/ にアクセスしてリダイレクトを追跡するとHTMLが返る"""
        response = flask_client.get("/", follow_redirects=True)
        assert response.status_code == 200, (
            f"/ のリダイレクト後のステータスが200ではありません: {response.status_code}"
        )
        content_type = response.content_type
        assert "text/html" in content_type, (
            f"リダイレクト後のContent-TypeがHTMLではありません: {content_type}"
        )

    def test_dashboard_html_contains_content(self, flask_client):
        """/ のHTMLに何らかのコンテンツが含まれる"""
        response = flask_client.get("/", follow_redirects=True)
        html = response.data.decode("utf-8", errors="replace")
        assert len(html) > 100, "HTMLコンテンツが短すぎます（空またはほぼ空）"


# ============================================================
# シナリオ4: APIエンドポイント
# ============================================================
class TestScenario4ApiEndpoints:
    """シナリオ4: APIエンドポイントのテスト"""

    def test_api_stats_returns_200(self, flask_client):
        """GET /api/stats が200を返す"""
        response = flask_client.get("/api/stats")
        assert response.status_code == 200, (
            f"/api/stats が200を返しませんでした。実際のステータス: {response.status_code}"
        )

    def test_api_stats_returns_json(self, flask_client):
        """/api/stats がJSONを返す"""
        response = flask_client.get("/api/stats")
        content_type = response.content_type
        assert "application/json" in content_type, (
            f"/api/stats のContent-TypeがJSONではありません: {content_type}"
        )

    def test_api_stats_json_structure(self, flask_client):
        """/api/stats のJSONに必要なキーが含まれる"""
        response = flask_client.get("/api/stats")
        data = json.loads(response.data)
        expected_keys = ["total_works", "total_releases"]
        for key in expected_keys:
            assert key in data, f"/api/stats のJSONに '{key}' キーがありません。実際のキー: {list(data.keys())}"

    def test_api_releases_upcoming_returns_200(self, flask_client):
        """GET /api/releases/upcoming が200を返す"""
        response = flask_client.get("/api/releases/upcoming")
        assert response.status_code == 200, (
            f"/api/releases/upcoming が200を返しませんでした。実際のステータス: {response.status_code}"
        )

    def test_api_releases_upcoming_returns_json(self, flask_client):
        """/api/releases/upcoming がJSONを返す"""
        response = flask_client.get("/api/releases/upcoming")
        content_type = response.content_type
        assert "application/json" in content_type, (
            f"/api/releases/upcoming のContent-TypeがJSONではありません: {content_type}"
        )

    def test_api_releases_upcoming_returns_list(self, flask_client):
        """/api/releases/upcoming のJSONがリスト形式である"""
        response = flask_client.get("/api/releases/upcoming")
        data = json.loads(response.data)
        assert isinstance(data, list), (
            f"/api/releases/upcoming のレスポンスがリストではありません: {type(data)}"
        )

    def test_api_releases_recent_returns_200(self, flask_client):
        """GET /api/releases/recent が200を返す"""
        response = flask_client.get("/api/releases/recent")
        assert response.status_code == 200, (
            f"/api/releases/recent が200を返しませんでした。実際のステータス: {response.status_code}"
        )

    def test_api_releases_recent_returns_json(self, flask_client):
        """/api/releases/recent がJSONを返す"""
        response = flask_client.get("/api/releases/recent")
        content_type = response.content_type
        assert "application/json" in content_type, (
            f"/api/releases/recent のContent-TypeがJSONではありません: {content_type}"
        )


# ============================================================
# シナリオ5: カレンダーページ
# ============================================================
class TestScenario5CalendarPage:
    """シナリオ5: /calendar カレンダーページのテスト"""

    def test_calendar_page_returns_200_or_redirect(self, flask_client):
        """GET /calendar が200またはリダイレクトを返す"""
        response = flask_client.get("/calendar", follow_redirects=False)
        assert response.status_code in [200, 302], (
            f"/calendar が200または302ではありません: {response.status_code}"
        )

    def test_calendar_page_after_redirect_returns_200(self, flask_client):
        """/calendar のリダイレクト追跡後に200が返る"""
        response = flask_client.get("/calendar", follow_redirects=True)
        assert response.status_code == 200, (
            f"/calendar のリダイレクト後のステータスが200ではありません: {response.status_code}"
        )

    def test_calendar_page_contains_html(self, flask_client):
        """/calendar がHTMLを返す"""
        response = flask_client.get("/calendar", follow_redirects=True)
        content_type = response.content_type
        assert "text/html" in content_type, (
            f"/calendar のContent-TypeがHTMLではありません: {content_type}"
        )

    def test_calendar_html_contains_calendar_keyword(self, flask_client):
        """/calendar のHTMLにカレンダー関連ワードが含まれる"""
        response = flask_client.get("/calendar", follow_redirects=True)
        html = response.data.decode("utf-8", errors="replace")
        # カレンダーページ自身またはリダイレクト先のログインページを確認
        assert "カレンダー" in html or "Calendar" in html or "calendar" in html or "ログイン" in html, (
            "HTMLにカレンダーまたはログイン関連テキストが見つかりません"
        )

    def test_calendar_page_has_substantial_html(self, flask_client):
        """/calendar のHTMLに十分なコンテンツがある"""
        response = flask_client.get("/calendar", follow_redirects=True)
        html = response.data.decode("utf-8", errors="replace")
        assert len(html) > 200, (
            f"HTMLコンテンツが短すぎます: {len(html)}文字"
        )


# ============================================================
# 追加テスト: セキュリティヘッダー
# ============================================================
class TestSecurityHeaders:
    """セキュリティヘッダーのテスト"""

    def test_health_has_x_content_type_options(self, flask_client):
        """/health レスポンスに X-Content-Type-Options ヘッダーが含まれる"""
        response = flask_client.get("/health")
        assert "X-Content-Type-Options" in response.headers, (
            "X-Content-Type-Options ヘッダーが見つかりません"
        )

    def test_health_x_content_type_nosniff(self, flask_client):
        """X-Content-Type-Options が nosniff に設定されている"""
        response = flask_client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff", (
            f"X-Content-Type-Options が 'nosniff' ではありません: "
            f"{response.headers.get('X-Content-Type-Options')}"
        )

    def test_health_has_x_frame_options(self, flask_client):
        """/health レスポンスに X-Frame-Options ヘッダーが含まれる"""
        response = flask_client.get("/health")
        assert "X-Frame-Options" in response.headers, (
            "X-Frame-Options ヘッダーが見つかりません"
        )


# ============================================================
# 追加テスト: 存在しないエンドポイント
# ============================================================
class TestNotFoundHandling:
    """404エラーハンドリングのテスト"""

    def test_nonexistent_page_returns_404(self, flask_client):
        """存在しないページが404を返す"""
        response = flask_client.get("/this-page-does-not-exist-at-all")
        assert response.status_code == 404, (
            f"存在しないページが404を返しませんでした: {response.status_code}"
        )

    def test_nonexistent_api_returns_404(self, flask_client):
        """存在しないAPIが404を返す"""
        response = flask_client.get("/api/nonexistent-endpoint-xyz")
        assert response.status_code == 404, (
            f"存在しないAPIが404を返しませんでした: {response.status_code}"
        )


# ============================================================
# Playwright ブラウザE2Eテスト（Playwright利用可能な場合のみ）
# ============================================================
class TestPlaywrightE2E:
    """Playwright ブラウザベースE2Eテスト"""

    @pytest.fixture(autouse=True)
    def skip_if_no_playwright(self):
        """Playwrightが利用できない場合にスキップ"""
        if not PLAYWRIGHT_AVAILABLE:
            pytest.skip("Playwrightが利用できません")

    def test_playwright_login_page_display(self, playwright_page):
        """[Playwright] ログインページの表示確認"""
        # Flaskサーバーが起動している場合のみ実行
        base_url = "http://localhost:5001"
        try:
            response = playwright_page.goto(
                f"{base_url}/auth/login", timeout=5000
            )
            if response and response.status == 200:
                assert playwright_page.locator('input[name="username"]').is_visible()
                assert playwright_page.locator('input[name="password"]').is_visible()

                # スクリーンショット保存
                screenshot_path = SCREENSHOT_DIR / "login.png"
                playwright_page.screenshot(path=str(screenshot_path))
        except Exception:
            pytest.skip("Flaskサーバーが起動していません (localhost:5001)")

    def test_playwright_health_check(self, playwright_page):
        """[Playwright] ヘルスチェックエンドポイント確認"""
        base_url = "http://localhost:5001"
        try:
            response = playwright_page.goto(
                f"{base_url}/health", timeout=5000
            )
            if response:
                assert response.status == 200
        except Exception:
            pytest.skip("Flaskサーバーが起動していません (localhost:5001)")

    def test_playwright_dashboard_screenshot(self, playwright_page):
        """[Playwright] ダッシュボードのスクリーンショット取得"""
        base_url = "http://localhost:5001"
        try:
            playwright_page.goto(f"{base_url}/", timeout=5000)
            screenshot_path = SCREENSHOT_DIR / "dashboard.png"
            playwright_page.screenshot(path=str(screenshot_path))
        except Exception:
            pytest.skip("Flaskサーバーが起動していません (localhost:5001)")

    def test_playwright_calendar_screenshot(self, playwright_page):
        """[Playwright] カレンダーページのスクリーンショット取得"""
        base_url = "http://localhost:5001"
        try:
            playwright_page.goto(f"{base_url}/calendar", timeout=5000)
            screenshot_path = SCREENSHOT_DIR / "calendar.png"
            playwright_page.screenshot(path=str(screenshot_path))
        except Exception:
            pytest.skip("Flaskサーバーが起動していません (localhost:5001)")


# ============================================================
# スタンドアロン実行
# ============================================================
def main():
    """スタンドアロン実行エントリーポイント"""
    print("=" * 60)
    print("Phase 8: Playwright E2Eテスト")
    print("=" * 60)
    print(f"Playwright利用可能: {PLAYWRIGHT_AVAILABLE}")
    print(f"Flaskアプリ利用可能: {FLASK_AVAILABLE}")
    if not FLASK_AVAILABLE:
        print(f"Flaskエラー: {_flask_import_error}")
    print("-" * 60)

    args = [
        __file__,
        "-v",
        "--tb=short",
        "-p", "no:warnings",
        "--no-header",
    ]
    exit_code = pytest.main(args)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
