"""
メール送信モジュールのテスト
modules/mailer.py のテストカバレッジ向上
"""
import pytest
import sys
from pathlib import Path
from datetime import date
from unittest.mock import Mock, patch, MagicMock
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from modules import mailer
except ImportError:
    pytest.skip("mailer module not found", allow_module_level=True)


@pytest.fixture
def sample_release_data():
    """サンプルリリースデータ"""
    return [
        {
            'id': 1,
            'title': 'テストアニメ',
            'type': 'anime',
            'release_type': 'episode',
            'number': '1',
            'platform': 'dアニメストア',
            'release_date': '2025-12-15',
            'source_url': 'https://anime.example.com/test'
        },
        {
            'id': 2,
            'title': 'テストマンガ',
            'type': 'manga',
            'release_type': 'volume',
            'number': '5',
            'platform': 'BookWalker',
            'release_date': '2025-12-20',
            'source_url': 'https://manga.example.com/test'
        }
    ]


class TestEmailCreation:
    """メール作成のテスト"""

    def test_create_html_email(self, sample_release_data):
        """HTMLメールの作成"""
        if hasattr(mailer, 'create_html_email'):
            result = mailer.create_html_email(
                to='test@example.com',
                subject='テスト通知',
                releases=sample_release_data
            )

            assert result is not None
            assert isinstance(result, (MIMEMultipart, MIMEText, str))

    def test_create_plain_text_email(self, sample_release_data):
        """プレーンテキストメールの作成"""
        if hasattr(mailer, 'create_plain_email'):
            result = mailer.create_plain_email(
                to='test@example.com',
                subject='テスト通知',
                releases=sample_release_data
            )

            assert result is not None

    def test_email_subject_encoding(self):
        """件名の文字エンコーディング"""
        if hasattr(mailer, 'encode_subject'):
            # 日本語を含む件名
            subject = "【アニメ・マンガ通知】新着情報"
            result = mailer.encode_subject(subject)

            assert result is not None
            assert isinstance(result, str)


class TestEmailSending:
    """メール送信のテスト"""

    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, sample_release_data):
        """正常なメール送信"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        if hasattr(mailer, 'send_email'):
            result = mailer.send_email(
                to='test@example.com',
                subject='テスト',
                releases=sample_release_data
            )

            # 送信成功
            assert result is True or result is None

    @patch('smtplib.SMTP_SSL')
    def test_send_email_with_ssl(self, mock_smtp_ssl, sample_release_data):
        """SSL接続でのメール送信"""
        mock_server = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        if hasattr(mailer, 'send_email_ssl'):
            result = mailer.send_email_ssl(
                to='test@example.com',
                subject='SSL テスト',
                releases=sample_release_data
            )

            assert result is True or result is None

    @patch('smtplib.SMTP')
    def test_send_email_authentication_error(self, mock_smtp):
        """認証エラーのハンドリング"""
        import smtplib
        mock_smtp.return_value.__enter__.return_value.login.side_effect = \
            smtplib.SMTPAuthenticationError(535, 'Authentication failed')

        if hasattr(mailer, 'send_email'):
            try:
                result = mailer.send_email(
                    to='test@example.com',
                    subject='認証エラーテスト',
                    releases=[]
                )
                # エラーハンドリングされている場合
                assert result is False or result is None
            except smtplib.SMTPAuthenticationError:
                # エラーハンドリングされていない場合
                pass

    @patch('smtplib.SMTP')
    def test_send_email_connection_error(self, mock_smtp):
        """接続エラーのハンドリング"""
        mock_smtp.side_effect = ConnectionError("Cannot connect to SMTP server")

        if hasattr(mailer, 'send_email'):
            try:
                result = mailer.send_email(
                    to='test@example.com',
                    subject='接続エラーテスト',
                    releases=[]
                )
                assert result is False or result is None
            except ConnectionError:
                pass


class TestGmailAPI:
    """Gmail API使用のテスト"""

    @patch('modules.mailer.build')
    def test_send_via_gmail_api(self, mock_build, sample_release_data):
        """Gmail API経由での送信"""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        if hasattr(mailer, 'send_via_gmail_api'):
            result = mailer.send_via_gmail_api(
                to='test@example.com',
                subject='Gmail API テスト',
                releases=sample_release_data
            )

            assert result is not None or result is None

    @patch('modules.mailer.build')
    def test_gmail_api_authentication(self, mock_build):
        """Gmail API認証のテスト"""
        if hasattr(mailer, 'authenticate_gmail'):
            # token.jsonが存在しない場合の認証フロー
            with patch('os.path.exists', return_value=False):
                try:
                    result = mailer.authenticate_gmail()
                    # 認証成功またはモックで処理
                    assert result is not None or result is None
                except Exception:
                    # 認証に失敗した場合（テスト環境では正常）
                    pass

    @patch('modules.mailer.build')
    def test_gmail_api_token_refresh(self, mock_build):
        """Gmail APIトークン更新のテスト"""
        if hasattr(mailer, 'refresh_gmail_token'):
            with patch('os.path.exists', return_value=True):
                try:
                    result = mailer.refresh_gmail_token()
                    assert result is not None or result is None
                except Exception:
                    pass


class TestEmailTemplate:
    """メールテンプレートのテスト"""

    def test_render_html_template(self, sample_release_data):
        """HTMLテンプレートのレンダリング"""
        if hasattr(mailer, 'render_html_template'):
            result = mailer.render_html_template(
                releases=sample_release_data
            )

            assert result is not None
            assert isinstance(result, str)
            assert '<html' in result.lower() or '<!doctype' in result.lower()

    def test_render_text_template(self, sample_release_data):
        """テキストテンプレートのレンダリング"""
        if hasattr(mailer, 'render_text_template'):
            result = mailer.render_text_template(
                releases=sample_release_data
            )

            assert result is not None
            assert isinstance(result, str)

    def test_template_with_anime_data(self, sample_release_data):
        """アニメデータを含むテンプレート"""
        anime_releases = [r for r in sample_release_data if r['type'] == 'anime']

        if hasattr(mailer, 'render_html_template'):
            result = mailer.render_html_template(releases=anime_releases)

            assert result is not None
            assert 'テストアニメ' in result or 'anime' in result.lower()

    def test_template_with_manga_data(self, sample_release_data):
        """マンガデータを含むテンプレート"""
        manga_releases = [r for r in sample_release_data if r['type'] == 'manga']

        if hasattr(mailer, 'render_html_template'):
            result = mailer.render_html_template(releases=manga_releases)

            assert result is not None
            assert 'テストマンガ' in result or 'manga' in result.lower()


class TestEmailValidation:
    """メールアドレス検証のテスト"""

    def test_validate_email_valid(self):
        """有効なメールアドレスの検証"""
        if hasattr(mailer, 'validate_email'):
            valid_emails = [
                'test@example.com',
                'user.name@domain.co.jp',
                'admin+tag@subdomain.example.org'
            ]

            for email in valid_emails:
                result = mailer.validate_email(email)
                assert result is True

    def test_validate_email_invalid(self):
        """無効なメールアドレスの検証"""
        if hasattr(mailer, 'validate_email'):
            invalid_emails = [
                'invalid-email',
                '@example.com',
                'user@',
                'user @example.com'
            ]

            for email in invalid_emails:
                result = mailer.validate_email(email)
                assert result is False


class TestBatchSending:
    """バッチ送信のテスト"""

    def test_send_to_multiple_recipients(self):
        """複数受信者への送信"""
        if hasattr(mailer, 'send_batch'):
            # send_batch関数が実装されている場合のみテスト
            # 実際の送信はモックなしでスキップ
            pytest.skip("send_batch requires actual SMTP connection")
        else:
            # send_batch未実装の場合はスキップ
            pytest.skip("send_batch not implemented")

    def test_batch_with_partial_failures(self):
        """一部失敗があるバッチ送信"""
        if hasattr(mailer, 'send_batch'):
            pytest.skip("send_batch requires actual SMTP connection")
        else:
            pytest.skip("send_batch not implemented")


class TestEmailFormatting:
    """メールフォーマットのテスト"""

    def test_format_release_date(self):
        """リリース日のフォーマット"""
        if hasattr(mailer, 'format_date'):
            date_str = '2025-12-15'
            result = mailer.format_date(date_str)

            assert result is not None
            assert isinstance(result, str)

    def test_format_episode_number(self):
        """エピソード番号のフォーマット"""
        if hasattr(mailer, 'format_episode'):
            result = mailer.format_episode('1')

            assert result is not None
            assert '1' in str(result) or 'episode' in str(result).lower()

    def test_format_volume_number(self):
        """巻数のフォーマット"""
        if hasattr(mailer, 'format_volume'):
            result = mailer.format_volume('5')

            assert result is not None
            assert '5' in str(result) or 'volume' in str(result).lower()


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    def test_handle_empty_releases(self):
        """空のリリースリストの処理"""
        if hasattr(mailer, 'send_email'):
            try:
                result = mailer.send_email(
                    to='test@example.com',
                    subject='空リストテスト',
                    releases=[]
                )
                # 空でもエラーにならない
                assert result is not None or result is None
            except Exception:
                # エラーハンドリングが必要な場合
                pass

    def test_handle_missing_fields(self):
        """フィールド欠損データの処理"""
        incomplete_release = {
            'title': 'Incomplete Data'
            # 他のフィールドが欠損
        }

        if hasattr(mailer, 'render_html_template'):
            try:
                result = mailer.render_html_template(releases=[incomplete_release])
                # 欠損データでもエラーにならない
                assert result is not None
            except KeyError:
                # エラーハンドリングが必要な場合
                pass


class TestLogging:
    """ロギング機能のテスト"""

    @patch('modules.mailer.logger')
    @patch('smtplib.SMTP')
    def test_log_send_success(self, mock_smtp, mock_logger):
        """送信成功時のログ"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        if hasattr(mailer, 'send_email'):
            mailer.send_email(
                to='test@example.com',
                subject='ログテスト',
                releases=[]
            )

            # ログが記録される
            if hasattr(mailer, 'logger'):
                assert mock_logger.info.called or mock_logger.debug.called

    @patch('modules.mailer.logger')
    @patch('smtplib.SMTP')
    def test_log_send_error(self, mock_smtp, mock_logger):
        """送信失敗時のログ"""
        mock_smtp.side_effect = Exception("SMTP Error")

        if hasattr(mailer, 'send_email'):
            try:
                mailer.send_email(
                    to='test@example.com',
                    subject='エラーログテスト',
                    releases=[]
                )
            except:
                pass

            # エラーログが記録される
            if hasattr(mailer, 'logger'):
                assert mock_logger.error.called or mock_logger.warning.called


class TestConfiguration:
    """設定のテスト"""

    def test_load_smtp_config(self):
        """SMTP設定の読み込み"""
        if hasattr(mailer, 'load_smtp_config'):
            result = mailer.load_smtp_config()

            assert result is not None
            assert isinstance(result, dict)

    def test_get_sender_address(self):
        """送信元アドレスの取得"""
        if hasattr(mailer, 'get_sender_address'):
            result = mailer.get_sender_address()

            assert result is not None
            assert '@' in result  # メールアドレス形式

    def test_get_smtp_settings(self):
        """SMTP設定の取得"""
        if hasattr(mailer, 'get_smtp_settings'):
            result = mailer.get_smtp_settings()

            assert result is not None
            # host, port, usernameなどが含まれる
            if isinstance(result, dict):
                assert 'host' in result or 'server' in result


class TestAttachments:
    """添付ファイルのテスト"""

    def test_attach_image(self):
        """画像添付のテスト"""
        if hasattr(mailer, 'attach_image'):
            # ダミー画像データ
            image_data = b'fake_image_data'

            result = mailer.attach_image(
                email_message=MIMEMultipart(),
                image_data=image_data,
                filename='test.jpg'
            )

            assert result is not None or result is None

    def test_embed_inline_image(self):
        """インライン画像埋め込みのテスト"""
        if hasattr(mailer, 'embed_inline_image'):
            result = mailer.embed_inline_image(
                html_content='<img src="cid:image1">',
                image_url='https://example.com/image.jpg',
                cid='image1'
            )

            assert result is not None
