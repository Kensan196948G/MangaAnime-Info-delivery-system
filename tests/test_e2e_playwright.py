#!/usr/bin/env python3
"""
Playwright E2Eテスト
ブラウザベースの統合テスト
"""

import pytest
import time
import sys
from pathlib import Path
from typing import Generator

# プロジェクトルート
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Playwrightインポート（オプション）
try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwrightがインストールされていません")
    print("   インストール: pip install playwright && playwright install")


@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    """ブラウザインスタンス"""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not available")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser: Browser) -> Generator[Page, None, None]:
    """ページインスタンス"""
    context = browser.new_context()
    page = context.new_page()
    yield page
    page.close()
    context.close()


@pytest.fixture(scope="session")
def base_url() -> str:
    """ベースURL"""
    return "http://localhost:5000"


class TestE2EPlaywright:
    """Playwright E2Eテスト"""

    def test_home_page(self, page: Page, base_url: str):
        """トップページアクセス"""
        page.goto(base_url)
        assert page.title() != ""
        print(f"✓ ページタイトル: {page.title()}")

    def test_navigation(self, page: Page, base_url: str):
        """ナビゲーション動作"""
        page.goto(base_url)

        # リリースページへ
        page.click('a[href="/releases"]')
        page.wait_for_load_state('networkidle')
        assert "/releases" in page.url
        print("✓ リリースページ遷移成功")

        # カレンダーページへ
        page.click('a[href="/calendar"]')
        page.wait_for_load_state('networkidle')
        assert "/calendar" in page.url
        print("✓ カレンダーページ遷移成功")

    def test_login_form(self, page: Page, base_url: str):
        """ログインフォーム表示"""
        page.goto(f"{base_url}/auth/login")

        # フォーム要素確認
        assert page.locator('input[name="username"]').is_visible()
        assert page.locator('input[name="password"]').is_visible()
        assert page.locator('button[type="submit"]').is_visible()
        print("✓ ログインフォーム表示確認")

    def test_api_endpoints(self, page: Page, base_url: str):
        """APIエンドポイント"""
        # /api/stats
        response = page.goto(f"{base_url}/api/stats")
        assert response.status == 200
        print("✓ /api/stats アクセス成功")

        # /api/releases/recent
        response = page.goto(f"{base_url}/api/releases/recent")
        assert response.status == 200
        print("✓ /api/releases/recent アクセス成功")

    def test_health_check(self, page: Page, base_url: str):
        """ヘルスチェック"""
        response = page.goto(f"{base_url}/health")
        assert response.status == 200
        print("✓ /health アクセス成功")

    def test_javascript_errors(self, page: Page, base_url: str):
        """JavaScriptエラー検出"""
        errors = []

        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url)
        page.wait_for_load_state('networkidle')

        if errors:
            print(f"⚠️  JavaScriptエラー検出: {len(errors)}件")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✓ JavaScriptエラーなし")

        assert len(errors) == 0, f"JavaScriptエラーが検出されました: {errors}"

    def test_console_warnings(self, page: Page, base_url: str):
        """コンソール警告検出"""
        warnings = []

        page.on("console", lambda msg:
            warnings.append(msg.text) if msg.type == "warning" else None)

        page.goto(base_url)
        page.wait_for_load_state('networkidle')

        if warnings:
            print(f"⚠️  コンソール警告: {len(warnings)}件")
            for warning in warnings:
                print(f"  - {warning}")
        else:
            print("✓ コンソール警告なし")

    def test_network_errors(self, page: Page, base_url: str):
        """ネットワークエラー検出"""
        failed_requests = []

        page.on("requestfailed", lambda request:
            failed_requests.append(f"{request.method} {request.url}"))

        page.goto(base_url)
        page.wait_for_load_state('networkidle')

        if failed_requests:
            print(f"⚠️  失敗したリクエスト: {len(failed_requests)}件")
            for req in failed_requests:
                print(f"  - {req}")
        else:
            print("✓ ネットワークエラーなし")

        assert len(failed_requests) == 0, f"ネットワークエラーが検出されました: {failed_requests}"

    def test_response_time(self, page: Page, base_url: str):
        """レスポンスタイム計測"""
        start_time = time.time()
        page.goto(base_url)
        page.wait_for_load_state('networkidle')
        end_time = time.time()

        response_time = end_time - start_time
        print(f"✓ ページロード時間: {response_time:.2f}秒")

        assert response_time < 5.0, f"ページロードが遅すぎます: {response_time}秒"

    def test_accessibility(self, page: Page, base_url: str):
        """アクセシビリティチェック（基本）"""
        page.goto(base_url)

        # alt属性なし画像チェック
        images_without_alt = page.locator('img:not([alt])').count()
        if images_without_alt > 0:
            print(f"⚠️  alt属性のない画像: {images_without_alt}個")
        else:
            print("✓ すべての画像にalt属性あり")

        # フォームラベルチェック
        inputs_without_label = page.locator('input:not([type="hidden"]):not([aria-label]):not([aria-labelledby])').count()
        if inputs_without_label > 0:
            print(f"⚠️  ラベルのない入力欄: {inputs_without_label}個")
        else:
            print("✓ すべての入力欄にラベルあり")


def main():
    """スタンドアロン実行"""
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwrightがインストールされていません")
        print("   インストール方法:")
        print("   pip install playwright")
        print("   playwright install")
        return 1

    pytest.main([__file__, '-v', '--tb=short'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
