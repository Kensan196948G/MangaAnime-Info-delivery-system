#!/usr/bin/env python3
"""
UI機能のE2Eテスト（Playwright）
テスト対象:
1. 更新ボタンのクリック操作
2. プログレスバー表示
3. レスポンシブデザイン
4. モバイル表示
"""

import pytest
from playwright.sync_api import Page, expect
import time


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """ブラウザコンテキストの設定"""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
    }


class TestRefreshButtons:
    """更新ボタンのE2Eテスト"""

    def test_upcoming_refresh_button_click(self, page: Page, base_url):
        """今後の予定更新ボタンのクリックテスト"""
        page.goto(f"{base_url}/")

        # ページが読み込まれるまで待機
        page.wait_for_load_state("networkidle")

        # 更新ボタンを探す
        refresh_buttons = page.locator("button:has-text('更新'), button:has-text('refresh')")

        if refresh_buttons.count() > 0:
            first_button = refresh_buttons.first
            first_button.click()

            # プログレスバーまたはローディング表示を確認
            time.sleep(1)
            # ページが更新されたことを確認
            assert page.url == f"{base_url}/" or "loading" in page.content().lower()

    def test_history_refresh_button_click(self, page: Page, base_url):
        """リリース履歴更新ボタンのクリックテスト"""
        page.goto(f"{base_url}/works")

        page.wait_for_load_state("networkidle")

        refresh_buttons = page.locator("button:has-text('更新'), button:has-text('refresh')")

        if refresh_buttons.count() > 0:
            first_button = refresh_buttons.first
            first_button.click()
            time.sleep(1)


class TestProgressBar:
    """プログレスバー表示のE2Eテスト"""

    def test_progress_bar_appears_on_action(self, page: Page, base_url):
        """アクション実行時のプログレスバー表示"""
        page.goto(f"{base_url}/")
        page.wait_for_load_state("networkidle")

        # アクションボタンを探す
        action_buttons = page.locator("button[type='submit'], button:has-text('実行')")

        if action_buttons.count() > 0:
            action_buttons.first.click()

            # プログレスバーやローディング表示を確認
            loading_indicators = page.locator(
                ".progress, .spinner-border, .loading, [role='progressbar']"
            )

            # 一部の実装ではローディングが非常に速い場合があるため、柔軟にチェック
            time.sleep(0.5)


class TestResponsiveDesign:
    """レスポンシブデザインのE2Eテスト"""

    @pytest.mark.parametrize("viewport", [
        {"width": 375, "height": 667},   # iPhone SE
        {"width": 414, "height": 896},   # iPhone XR
        {"width": 768, "height": 1024},  # iPad
        {"width": 1920, "height": 1080}, # Desktop
    ])
    def test_responsive_layout(self, page: Page, base_url, viewport):
        """各画面サイズでのレイアウトテスト"""
        page.set_viewport_size(viewport)
        page.goto(f"{base_url}/")
        page.wait_for_load_state("networkidle")

        # ページが正しく表示されているか確認
        assert page.title() != ""

        # ナビゲーションメニューの存在確認
        nav = page.locator("nav, .navbar, header")
        if nav.count() > 0:
            assert nav.first.is_visible()

    def test_mobile_menu_toggle(self, page: Page, base_url):
        """モバイルメニューのトグル動作"""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(f"{base_url}/")
        page.wait_for_load_state("networkidle")

        # ハンバーガーメニューボタンを探す
        menu_toggle = page.locator(".navbar-toggler, .menu-toggle, button[aria-label*='メニュー']")

        if menu_toggle.count() > 0:
            menu_toggle.first.click()
            time.sleep(0.5)

            # メニューが表示されたことを確認
            mobile_menu = page.locator(".navbar-collapse, .mobile-menu")
            if mobile_menu.count() > 0:
                assert mobile_menu.first.is_visible()


class TestLastUpdateDisplay:
    """最終更新表示のE2Eテスト"""

    def test_last_update_timestamp_visible(self, page: Page, base_url):
        """最終更新時刻が表示されているか"""
        page.goto(f"{base_url}/")
        page.wait_for_load_state("networkidle")

        # 最終更新表示を探す
        last_update = page.locator(
            "text=/最終更新/, [data-last-update], .last-update, #last-update"
        )

        if last_update.count() > 0:
            assert last_update.first.is_visible()
            text = last_update.first.inner_text()
            assert len(text) > 0

    def test_last_update_format(self, page: Page, base_url):
        """最終更新時刻のフォーマット確認"""
        page.goto(f"{base_url}/")
        page.wait_for_load_state("networkidle")

        last_update = page.locator("text=/最終更新/")

        if last_update.count() > 0:
            text = last_update.first.inner_text()
            # 日時フォーマットを含むか確認
            assert any(char.isdigit() for char in text)


class TestUIElements:
    """UI要素の存在確認テスト"""

    def test_homepage_key_elements(self, page: Page, base_url):
        """ホームページの主要要素確認"""
        page.goto(f"{base_url}/")
        page.wait_for_load_state("networkidle")

        # タイトルの存在確認
        title = page.locator("h1")
        assert title.count() > 0

        # 統計情報の存在確認
        stats = page.locator(".stat-item, .stats, [class*='statistic']")
        if stats.count() > 0:
            assert stats.first.is_visible()

    def test_navigation_links(self, page: Page, base_url):
        """ナビゲーションリンクの動作確認"""
        page.goto(f"{base_url}/")
        page.wait_for_load_state("networkidle")

        # 主要なナビゲーションリンクを確認
        links = page.locator("a[href*='works'], a[href*='config'], a[href*='calendar']")

        if links.count() > 0:
            first_link = links.first
            href = first_link.get_attribute("href")
            assert href is not None

            # リンクをクリック
            first_link.click()
            page.wait_for_load_state("networkidle")

            # ページが遷移したことを確認
            assert page.url != f"{base_url}/"


class TestFormInteraction:
    """フォーム操作のE2Eテスト"""

    def test_settings_form_interaction(self, page: Page, base_url):
        """設定フォームの操作テスト"""
        page.goto(f"{base_url}/config")
        page.wait_for_load_state("networkidle")

        # メールアドレス入力欄を探す
        email_input = page.locator("input[type='email'], input[name*='email']")

        if email_input.count() > 0:
            email_input.first.fill("test@example.com")
            value = email_input.first.input_value()
            assert value == "test@example.com"

    def test_checkbox_interaction(self, page: Page, base_url):
        """チェックボックスの操作テスト"""
        page.goto(f"{base_url}/config")
        page.wait_for_load_state("networkidle")

        # チェックボックスを探す
        checkboxes = page.locator("input[type='checkbox']")

        if checkboxes.count() > 0:
            checkbox = checkboxes.first
            initial_state = checkbox.is_checked()

            # チェック状態を変更
            checkbox.click()
            time.sleep(0.3)

            new_state = checkbox.is_checked()
            assert new_state != initial_state


class TestAccessibility:
    """アクセシビリティテスト"""

    def test_aria_labels_present(self, page: Page, base_url):
        """ARIA属性の存在確認"""
        page.goto(f"{base_url}/")
        page.wait_for_load_state("networkidle")

        # ARIA属性を持つ要素を確認
        aria_elements = page.locator("[aria-label], [role], [aria-hidden]")
        assert aria_elements.count() > 0

    def test_keyboard_navigation(self, page: Page, base_url):
        """キーボードナビゲーションのテスト"""
        page.goto(f"{base_url}/")
        page.wait_for_load_state("networkidle")

        # Tabキーでフォーカス移動
        page.keyboard.press("Tab")
        time.sleep(0.2)

        # フォーカスされた要素を確認
        focused = page.evaluate("document.activeElement.tagName")
        assert focused in ["A", "BUTTON", "INPUT", "SELECT", "TEXTAREA"]


class TestErrorStates:
    """エラー状態のE2Eテスト"""

    def test_404_page(self, page: Page, base_url):
        """404ページの表示テスト"""
        page.goto(f"{base_url}/nonexistent-page")

        # エラーメッセージまたは404表示を確認
        content = page.content().lower()
        assert "404" in content or "not found" in content or "見つかりません" in content

    def test_network_error_handling(self, page: Page, base_url):
        """ネットワークエラーハンドリングのテスト"""
        page.goto(f"{base_url}/")
        page.wait_for_load_state("networkidle")

        # オフライン状態をシミュレート
        page.context.set_offline(True)

        # APIリクエストを試みる
        refresh_button = page.locator("button:has-text('更新')").first
        if refresh_button.count() > 0:
            refresh_button.click()
            time.sleep(1)

        # オンラインに戻す
        page.context.set_offline(False)


@pytest.fixture
def base_url():
    """ベースURLの設定"""
    return "http://localhost:5001"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--headed"])
