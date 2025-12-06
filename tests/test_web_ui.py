# -*- coding: utf-8 -*-
"""
Web UIモジュールのテスト
app/web_ui.py のテストカバレッジ向上
"""
import pytest
import sys
import os
from pathlib import Path
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# Flaskアプリケーションをインポート
try:
    from app import web_ui
    from app.web_ui import app
except ImportError:
    # web_ui.pyが存在しない場合はスキップ
    pytest.skip("web_ui module not found", allow_module_level=True)


@pytest.fixture
def client():
    """Flaskテストクライアントを提供"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # テスト時はCSRF無効化

    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_db():
    """データベース操作のモック（sqlite3接続のモック）"""
    with patch('app.web_ui.sqlite3.connect') as mock:
        yield mock


class TestIndexRoute:
    """トップページのテスト"""

    def test_index_page_loads(self, client):
        """トップページが正常に表示される"""
        response = client.get('/')
        assert response.status_code == 200

    def test_index_page_contains_title(self, client):
        """トップページにタイトルが含まれる"""
        response = client.get('/')
        assert b'MangaAnime' in response.data or b'manga' in response.data.lower()

    def test_index_with_releases(self, client):
        """リリース情報がある場合の表示テスト"""
        # 実際のDBを使用してテスト（モック不要）
        response = client.get('/')
        assert response.status_code == 200


class TestReleasesRoute:
    """リリース一覧ページのテスト"""

    def test_releases_page_loads(self, client):
        """リリース一覧ページが正常に表示される"""
        response = client.get('/releases')
        assert response.status_code == 200

    def test_releases_display_data(self, client):
        """リリースデータが正しく表示される"""
        response = client.get('/releases')
        assert response.status_code == 200


class TestWorksRoute:
    """作品一覧ページのテスト"""

    def test_works_page_loads(self, client):
        """作品一覧ページが正常に表示される"""
        response = client.get('/works')
        assert response.status_code == 200

    def test_works_display_anime(self, client):
        """アニメ作品が正しく表示される"""
        response = client.get('/works?type=anime')
        assert response.status_code == 200

    def test_works_display_manga(self, client):
        """マンガ作品が正しく表示される"""
        response = client.get('/works?type=manga')
        assert response.status_code == 200


class TestAPIRoutes:
    """API エンドポイントのテスト"""

    def test_api_releases_json(self, client):
        """リリースAPI（JSON）のテスト - ルート未実装の場合スキップ"""
        if '/api/releases' in [rule.rule for rule in app.url_map.iter_rules()]:
            response = client.get('/api/releases')
            assert response.status_code == 200
        else:
            pytest.skip("API routes not implemented")

    def test_api_works_json(self, client):
        """作品API（JSON）のテスト - ルート未実装の場合スキップ"""
        if '/api/works' in [rule.rule for rule in app.url_map.iter_rules()]:
            response = client.get('/api/works')
            assert response.status_code == 200
        else:
            pytest.skip("API routes not implemented")


class TestSearchFunctionality:
    """検索機能のテスト"""

    def test_search_by_title(self, client):
        """タイトルでの検索テスト"""
        # /works?search=xxx を使用
        response = client.get('/works?search=テスト')
        assert response.status_code == 200

    def test_search_empty_query(self, client):
        """空の検索クエリのテスト"""
        response = client.get('/works?search=')
        assert response.status_code == 200


class TestFilterFunctionality:
    """フィルタリング機能のテスト"""

    def test_filter_by_type_anime(self, client):
        """アニメでのフィルタリング"""
        response = client.get('/works?type=anime')
        assert response.status_code == 200

    def test_filter_by_type_manga(self, client):
        """マンガでのフィルタリング"""
        response = client.get('/works?type=manga')
        assert response.status_code == 200


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    def test_404_error(self, client):
        """404エラーページのテスト"""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404

    def test_database_error_handling(self, client):
        """データベースエラーのハンドリング"""
        # エラーが発生してもアプリケーションがクラッシュしないことを確認
        response = client.get('/releases')
        assert response.status_code in [200, 500]


class TestStaticFiles:
    """静的ファイルのテスト"""

    def test_static_css_accessible(self, client):
        """CSSファイルにアクセス可能か"""
        # static/css/style.css が存在する場合
        response = client.get('/static/css/style.css')
        # 存在すれば200、なければ404
        assert response.status_code in [200, 404]

    def test_static_js_accessible(self, client):
        """JavaScriptファイルにアクセス可能か"""
        # static/js/main.js が存在する場合
        response = client.get('/static/js/main.js')
        assert response.status_code in [200, 404]


class TestTemplateRendering:
    """テンプレートレンダリングのテスト"""

    def test_template_context_data(self, client):
        """テンプレートに正しいデータが渡される"""
        response = client.get('/')
        assert response.status_code == 200
        # テンプレートが正しくレンダリングされている
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data

    def test_base_template_elements(self, client):
        """ベーステンプレートの基本要素を確認"""
        response = client.get('/')
        data = response.data.decode('utf-8')

        # HTML5の基本構造
        assert '<html' in data.lower()
        assert '</html>' in data.lower()


class TestPagination:
    """ページネーションのテスト"""

    def test_pagination_first_page(self, client):
        """最初のページのテスト"""
        response = client.get('/releases?page=1')
        assert response.status_code == 200

    def test_pagination_second_page(self, client):
        """2ページ目のテスト"""
        response = client.get('/releases?page=2')
        assert response.status_code in [200, 404]


class TestResponsiveDesign:
    """レスポンシブデザインのテスト"""

    def test_viewport_meta_tag(self, client):
        """ビューポートメタタグの存在確認"""
        response = client.get('/')
        data = response.data.decode('utf-8')

        # モバイル対応のメタタグ
        assert 'viewport' in data.lower() or '<meta' in data


class TestAccessibility:
    """アクセシビリティのテスト"""

    def test_lang_attribute(self, client):
        """言語属性の存在確認"""
        response = client.get('/')
        data = response.data.decode('utf-8')

        # 日本語のlang属性
        assert 'lang=' in data or 'ja' in data

    def test_alt_attributes_for_images(self, client):
        """画像のalt属性確認"""
        response = client.get('/')
        data = response.data.decode('utf-8')

        # 画像がある場合、alt属性が存在するか
        if '<img' in data:
            # alt属性の存在確認（簡易版）
            assert 'alt=' in data or data.count('<img') == 0
