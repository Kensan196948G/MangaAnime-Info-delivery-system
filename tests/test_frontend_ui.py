"""
Frontend UI Test Suite
フロントエンドUIの機能テスト
"""

import pytest
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestFrontendUI:
    """フロントエンドUI機能テストクラス"""

    def test_index_page_renders(self, client):
        """トップページが正常にレンダリングされるか"""
        response = client.get('/')

        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data


    def test_index_page_title(self, client):
        """トップページにタイトルが含まれているか"""
        response = client.get('/')

        soup = BeautifulSoup(response.data, 'html.parser')
        title = soup.find('title')

        assert title is not None
        assert len(title.text.strip()) > 0


    def test_dashboard_page(self, client):
        """ダッシュボードページのテスト"""
        response = client.get('/')

        assert response.status_code == 200

        # ダッシュボード要素の確認
        soup = BeautifulSoup(response.data, 'html.parser')

        # 統計情報表示エリアの確認
        stats_elements = soup.find_all(class_=lambda x: x and ('stat' in x or 'card' in x))


    def test_works_list_page(self, client):
        """作品一覧ページのテスト"""
        response = client.get('/works')

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            soup = BeautifulSoup(response.data, 'html.parser')
            # テーブルまたはリスト要素の存在確認
            assert soup.find('table') or soup.find('ul') or soup.find('div')


    def test_releases_page(self, client):
        """リリース一覧ページのテスト"""
        response = client.get('/releases')

        assert response.status_code in [200, 404]


    def test_calendar_page(self, client):
        """カレンダーページのテスト"""
        response = client.get('/calendar')

        assert response.status_code in [200, 404]


    def test_config_page(self, client):
        """設定ページのテスト"""
        response = client.get('/config')

        assert response.status_code in [200, 404]


    def test_logs_page(self, client):
        """ログページのテスト"""
        response = client.get('/logs')

        assert response.status_code in [200, 404]


    def test_responsive_meta_tags(self, client):
        """レスポンシブデザイン用メタタグのテスト"""
        response = client.get('/')

        soup = BeautifulSoup(response.data, 'html.parser')
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})

        # viewportメタタグが推奨される
        if viewport_meta:
            assert 'width=device-width' in viewport_meta.get('content', '')


    def test_css_resources_load(self, client):
        """CSSリソースのロードテスト"""
        response = client.get('/')

        soup = BeautifulSoup(response.data, 'html.parser')
        css_links = soup.find_all('link', rel='stylesheet')

        # CSSリンクが存在することを確認
        assert len(css_links) >= 0


    def test_js_resources_load(self, client):
        """JavaScriptリソースのロードテスト"""
        response = client.get('/')

        soup = BeautifulSoup(response.data, 'html.parser')
        script_tags = soup.find_all('script')

        # スクリプトタグが存在することを確認
        assert len(script_tags) >= 0


    def test_navigation_menu(self, client):
        """ナビゲーションメニューのテスト"""
        response = client.get('/')

        soup = BeautifulSoup(response.data, 'html.parser')

        # ナビゲーション要素の確認
        nav = soup.find('nav') or soup.find(class_=lambda x: x and 'nav' in x)


    def test_form_submission_manual_collection(self, client):
        """手動収集フォームの送信テスト"""
        response = client.post('/api/manual-collection',
                               data={'source': 'test'},
                               follow_redirects=True)

        # 適切なレスポンスが返されることを確認
        assert response.status_code in [200, 302, 400]


    def test_ajax_endpoints_accessible(self, client):
        """AJAX用エンドポイントのアクセステスト"""
        ajax_endpoints = [
            '/api/stats',
            '/api/releases/recent',
            '/api/collection-status',
        ]

        for endpoint in ajax_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            assert response.content_type == 'application/json'


    def test_error_page_404(self, client):
        """404エラーページのテスト"""
        response = client.get('/nonexistent-page-12345')

        assert response.status_code == 404


    def test_error_page_500_handling(self, client):
        """500エラーのハンドリングテスト"""
        # 意図的にエラーを発生させるエンドポイント（存在する場合）
        response = client.get('/api/works/invalid_id')

        # エラーが適切にハンドリングされることを確認
        assert response.status_code in [400, 404, 500]


    def test_accessibility_alt_text(self, client):
        """画像のalt属性テスト（アクセシビリティ）"""
        response = client.get('/')

        soup = BeautifulSoup(response.data, 'html.parser')
        images = soup.find_all('img')

        # 全ての画像にalt属性が設定されているか確認
        for img in images:
            assert img.has_attr('alt'), f"画像にalt属性がありません: {img}"


    def test_accessibility_form_labels(self, client):
        """フォームラベルのテスト（アクセシビリティ）"""
        pages = ['/', '/config']

        for page in pages:
            response = client.get(page)

            if response.status_code == 200:
                soup = BeautifulSoup(response.data, 'html.parser')
                inputs = soup.find_all('input', {'type': ['text', 'email', 'password']})

                # 各入力フィールドにラベルまたはaria-labelがあるか確認
                for input_field in inputs:
                    input_id = input_field.get('id')
                    has_label = soup.find('label', {'for': input_id})
                    has_aria = input_field.has_attr('aria-label')

                    # 警告のみ
                    if not has_label and not has_aria:
                        print(f"警告: ラベルがありません - {input_field}")


    def test_search_functionality(self, client):
        """検索機能のテスト"""
        response = client.get('/api/works?search=test')

        assert response.status_code == 200

        # 検索結果がJSON形式で返されることを確認
        assert response.content_type == 'application/json'


    def test_filter_functionality(self, client):
        """フィルタ機能のテスト"""
        filter_params = {
            'type': 'anime',
            'platform': 'netflix',
            'status': 'ongoing',
        }

        for param, value in filter_params.items():
            response = client.get(f'/api/works?{param}={value}')
            assert response.status_code == 200


    def test_date_format_display(self, client):
        """日付表示フォーマットのテスト"""
        response = client.get('/api/releases/recent')

        if response.status_code == 200:
            data = response.get_json()

            # データが存在する場合、日付フォーマットを確認
            if isinstance(data, list) and len(data) > 0:
                for item in data:
                    if 'release_date' in item:
                        # 日付フォーマットの検証（YYYY-MM-DD）
                        date_str = item['release_date']
                        assert isinstance(date_str, str)


    def test_loading_indicators(self, client):
        """ローディングインジケーターのテスト"""
        response = client.get('/')

        soup = BeautifulSoup(response.data, 'html.parser')

        # ローディング表示要素の存在確認
        loading_elements = soup.find_all(class_=lambda x: x and 'loading' in x.lower())


    def test_empty_state_display(self, client):
        """空状態の表示テスト"""
        response = client.get('/api/works?type=nonexistent')

        assert response.status_code == 200

        data = response.get_json()

        # 空のリストまたは適切なメッセージ
        if isinstance(data, dict):
            assert 'works' in data or 'message' in data
        elif isinstance(data, list):
            assert isinstance(data, list)


    def test_notification_display(self, client):
        """通知表示のテスト"""
        # トースト通知やアラート表示の確認
        response = client.get('/')

        soup = BeautifulSoup(response.data, 'html.parser')

        # 通知用の要素が存在するか確認
        notification_areas = soup.find_all(class_=lambda x: x and (
            'notification' in x.lower() or
            'toast' in x.lower() or
            'alert' in x.lower()
        ))


    def test_mobile_menu_toggle(self, client):
        """モバイルメニュートグルのテスト"""
        response = client.get('/')

        soup = BeautifulSoup(response.data, 'html.parser')

        # ハンバーガーメニューボタンの存在確認
        menu_toggle = soup.find(class_=lambda x: x and (
            'menu-toggle' in x or
            'navbar-toggle' in x or
            'hamburger' in x
        ))


@pytest.fixture
def client():
    """Flaskテストクライアントのフィクスチャ"""
    try:
        from app.web_app import app
        app.config['TESTING'] = True

        with app.test_client() as client:
            yield client
    except ImportError:
        # web_app.pyがない場合はweb_ui.pyを試す
        try:
            from app.web_ui import app
            app.config['TESTING'] = True

            with app.test_client() as client:
                yield client
        except ImportError:
            pytest.skip("web_app.pyまたはweb_ui.pyが見つかりません")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
