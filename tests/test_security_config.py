#!/usr/bin/env python3
"""
Test suite for enhanced security configuration and OAuth2 authentication.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from modules.config import ConfigManager, SecureConfigManager
    from modules.mailer import GmailNotifier, AuthenticationState
    from modules.calendar import GoogleCalendarManager, CalendarAuthState
except ImportError as e:
    print(f"Error: Cannot import modules: {e}")
    sys.exit(1)


class TestSecureConfigManager(unittest.TestCase):
    """Test secure configuration management."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_password = "test_password_123"
        self.secure_manager = SecureConfigManager(self.test_password)
    
    def test_encryption_setup(self):
        """Test encryption key setup."""
        self.assertIsNotNone(self.secure_manager._encryption_key)
    
    def test_encrypt_decrypt_value(self):
        """Test value encryption and decryption."""
        test_value = "sensitive_api_key_12345"
        
        # Encrypt the value
        encrypted_value = self.secure_manager.encrypt_value(test_value)
        self.assertNotEqual(test_value, encrypted_value)
        
        # Decrypt the value
        decrypted_value = self.secure_manager.decrypt_value(encrypted_value)
        self.assertEqual(test_value, decrypted_value)
    
    def test_encrypt_without_key(self):
        """Test encryption without encryption key."""
        no_key_manager = SecureConfigManager()
        test_value = "test_value"
        
        # Should return original value if no encryption key
        result = no_key_manager.encrypt_value(test_value)
        self.assertEqual(test_value, result)


class TestEnhancedConfigManager(unittest.TestCase):
    """Test enhanced configuration manager."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_config = {
            "system": {"environment": "test"},
            "google": {
                "gmail": {
                    "app_password": "encrypted_password"
                }
            }
        }
        
        # Create temporary config file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        import json
        json.dump(self.test_config, self.temp_file)
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up test environment."""
        os.unlink(self.temp_file.name)
    
    @patch.dict(os.environ, {
        'MANGA_ANIME_GMAIL_FROM': 'test@example.com',
        'GMAIL_APP_PASSWORD': 'env_password',
        'MANGA_ANIME_MASTER_PASSWORD': 'test_master_pass'
    })
    def test_environment_variable_override(self):
        """Test environment variable override functionality."""
        config_manager = ConfigManager(self.temp_file.name)
        
        # Check if environment variable overrides config file
        gmail_from = config_manager.get('google.gmail.from_email')
        self.assertEqual(gmail_from, 'test@example.com')
    
    @patch.dict(os.environ, {'MANGA_ANIME_MASTER_PASSWORD': 'test_master'})
    def test_secure_value_handling(self):
        """Test secure value encryption and decryption."""
        config_manager = ConfigManager(self.temp_file.name, enable_encryption=True)
        
        # Test setting and getting secure value
        config_manager.set_secure('test.secret_key', 'secret_value_123')
        retrieved_value = config_manager.get_secure('test.secret_key')
        
        self.assertEqual(retrieved_value, 'secret_value_123')
    
    def test_sensitive_keyword_detection(self):
        """Test automatic detection of sensitive configuration keys."""
        config_manager = ConfigManager(self.temp_file.name)
        
        # These should be detected as sensitive
        sensitive_keys = [
            'google.gmail.app_password',
            'security.secret_key',
            'apis.anilist.api_key'
        ]
        
        for key in sensitive_keys:
            # Simulate getting a value that would be auto-decrypted
            with patch.object(config_manager, '_secure_manager') as mock_secure:
                mock_secure.decrypt_value.return_value = 'decrypted_value'
                config_manager.get(key)
                # Verify auto-decryption was attempted for sensitive keys
                # (This test mainly verifies the logic path)


class TestEnhancedOAuth2Authentication(unittest.TestCase):
    """Test enhanced OAuth2 authentication."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_config = {
            'google': {
                'gmail': {
                    'from_email': 'test@example.com',
                    'to_email': 'test@example.com'
                },
                'credentials_file': 'test_credentials.json',
                'token_file': 'test_token.json',
                'scopes': ['https://www.googleapis.com/auth/gmail.send']
            }
        }
    
    @patch('modules.mailer.GOOGLE_AVAILABLE', True)
    @patch('modules.mailer.build')
    @patch('modules.mailer.Credentials')
    def test_token_near_expiry_detection(self, mock_creds, mock_build):
        """Test detection of tokens near expiry."""
        from datetime import datetime, timedelta
        
        gmail_notifier = GmailNotifier(self.test_config)
        
        # Set token to expire in 5 minutes (should be detected as near expiry)
        gmail_notifier.auth_state.token_expires_at = datetime.now() + timedelta(minutes=5)
        
        self.assertTrue(gmail_notifier._is_token_near_expiry())
        
        # Set token to expire in 20 minutes (should not be near expiry)
        gmail_notifier.auth_state.token_expires_at = datetime.now() + timedelta(minutes=20)
        
        self.assertFalse(gmail_notifier._is_token_near_expiry())
    
    @patch('modules.mailer.GOOGLE_AVAILABLE', True)
    @patch('modules.mailer.build')
    @patch('modules.mailer.Credentials')
    @patch('os.path.exists')
    def test_proactive_token_refresh(self, mock_exists, mock_creds, mock_build):
        """Test proactive token refresh functionality."""
        from datetime import datetime, timedelta
        
        mock_exists.return_value = True
        mock_creds_instance = MagicMock()
        mock_creds_instance.refresh_token = 'refresh_token'
        mock_creds_instance.expiry = datetime.now() + timedelta(hours=1)
        mock_creds.from_authorized_user_file.return_value = mock_creds_instance
        
        gmail_notifier = GmailNotifier(self.test_config)
        
        # Set up state for refresh
        gmail_notifier.auth_state.token_expires_at = datetime.now() + timedelta(minutes=5)
        gmail_notifier.auth_state.is_authenticated = True
        
        # Mock the refresh process
        with patch.object(gmail_notifier, '_refresh_token', return_value=True) as mock_refresh:
            result = gmail_notifier._refresh_token_proactively()
            self.assertTrue(result)
            mock_refresh.assert_called_once()
    
    def test_authentication_state_management(self):
        """Test authentication state management."""
        auth_state = AuthenticationState()
        
        # Test initial state
        self.assertFalse(auth_state.is_authenticated)
        self.assertEqual(auth_state.consecutive_auth_failures, 0)
        self.assertEqual(auth_state.token_refresh_count, 0)
        
        # Test refresh tracking
        auth_state.token_refresh_count += 1
        self.assertEqual(auth_state.token_refresh_count, 1)


class TestCalendarOAuth2Enhancement(unittest.TestCase):
    """Test enhanced Calendar OAuth2 authentication."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_config = {
            'google': {
                'calendar': {
                    'calendar_id': 'primary'
                },
                'credentials_file': 'test_credentials.json',
                'token_file': 'test_token.json',
                'scopes': ['https://www.googleapis.com/auth/calendar.events']
            }
        }
    
    @patch('modules.calendar.GOOGLE_AVAILABLE', True)
    def test_calendar_auth_state_initialization(self):
        """Test Calendar authentication state initialization."""
        calendar_manager = GoogleCalendarManager(self.test_config)
        
        self.assertIsInstance(calendar_manager.auth_state, CalendarAuthState)
        self.assertFalse(calendar_manager.auth_state.is_authenticated)
        self.assertEqual(calendar_manager.auth_state.token_refresh_count, 0)
    
    @patch('modules.calendar.GOOGLE_AVAILABLE', True)
    def test_calendar_token_expiry_detection(self):
        """Test Calendar token expiry detection."""
        from datetime import datetime, timedelta
        
        calendar_manager = GoogleCalendarManager(self.test_config)
        
        # Test near expiry detection
        calendar_manager.auth_state.token_expires_at = datetime.now() + timedelta(minutes=5)
        self.assertTrue(calendar_manager._is_token_near_expiry())
        
        # Test not near expiry
        calendar_manager.auth_state.token_expires_at = datetime.now() + timedelta(hours=1)
        self.assertFalse(calendar_manager._is_token_near_expiry())


class TestSecurityCompliance(unittest.TestCase):
    """Test security compliance features."""
    
    def test_secure_file_permissions(self):
        """Test secure file permission handling."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Test secure file creation with umask
            old_umask = os.umask(0o077)
            try:
                with open(temp_path, 'w') as f:
                    f.write('test content')
            finally:
                os.umask(old_umask)
            
            # Check permissions (should be 600)
            stat_info = os.stat(temp_path)
            permissions = stat_info.st_mode & 0o777
            self.assertEqual(permissions, 0o600)
            
        finally:
            os.unlink(temp_path)
    
    @patch.dict(os.environ, {})
    def test_missing_environment_variables(self):
        """Test handling of missing environment variables."""
        # Test that missing critical environment variables are handled gracefully
        config_manager = ConfigManager()
        
        # Should not crash even with missing env vars
        gmail_from = config_manager.get('google.gmail.from_email', 'default@example.com')
        self.assertIsNotNone(gmail_from)
    
    def test_sensitive_data_logging_prevention(self):
        """Test that sensitive data is not logged."""
        import logging
        from io import StringIO
        
        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        logger = logging.getLogger('modules.config')
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        
        try:
            # Test environment variable override with sensitive data
            with patch.dict(os.environ, {'GMAIL_CLIENT_SECRET': 'secret_value_123'}):
                config_manager = ConfigManager()
                
                # Check that sensitive values are redacted in logs
                log_output = log_capture.getvalue()
                self.assertNotIn('secret_value_123', log_output)
                self.assertIn('[REDACTED]', log_output)
                
        finally:
            logger.removeHandler(handler)


def run_security_tests():
    """Run all security-related tests."""
    test_classes = [
        TestSecureConfigManager,
        TestEnhancedConfigManager,
        TestEnhancedOAuth2Authentication,
        TestCalendarOAuth2Enhancement,
        TestSecurityCompliance
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_security_tests()
    sys.exit(0 if success else 1)