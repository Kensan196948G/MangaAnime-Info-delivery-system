# Test Notification API - Fix Documentation

## Date: 2025-11-14

## Issue
The `/api/test-notification` endpoint was returning HTTP 400 Bad Request errors.

## Root Cause Analysis

1. **Missing .env file**: The application expected a `.env` file with Gmail credentials, but it didn't exist.
2. **Inconsistent environment variable names**: The code looked for `GMAIL_ADDRESS` but the template used `GMAIL_SENDER_EMAIL`.
3. **Poor error handling**: Error messages didn't provide enough detail for debugging.
4. **JSON parsing issues**: The endpoint didn't handle missing or malformed request bodies properly.

## Changes Implemented

### 1. Created .env File
Created `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/.env` with the following configuration:

```env
GMAIL_APP_PASSWORD=sxsgmzbvubsajtok
GMAIL_SENDER_EMAIL=kensan1969@gmail.com
GMAIL_RECIPIENT_EMAIL=kensan1969@gmail.com
GMAIL_ADDRESS=kensan1969@gmail.com
```

### 2. Enhanced api_test_notification Function

**Location**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/web_app.py` (lines 1303-1475)

**Key Improvements**:

#### A. Robust JSON Parsing
```python
try:
    data = request.get_json(force=True, silent=True) or {}
except Exception as json_error:
    logger.warning(f"Failed to parse JSON body: {json_error}")
    data = {}
```

#### B. Multiple Environment Variable Support
```python
gmail_address = (
    os.getenv('GMAIL_ADDRESS') or
    os.getenv('GMAIL_SENDER_EMAIL') or
    os.getenv('GMAIL_RECIPIENT_EMAIL')
)
```

#### C. Enhanced Configuration Fallback
```python
config = load_config()
gmail_config = config.get('google', {}).get('gmail', {})

from_email = gmail_address or gmail_config.get('from_email', '') or config.get('notification_email', '')
to_email = gmail_address or gmail_config.get('to_email', '') or config.get('notification_email', '')
```

#### D. Detailed Error Messages
Added comprehensive error responses with debugging information:

```python
return jsonify({
    "success": False,
    "error": "メールアドレスが設定されていません",
    "details": "環境変数 GMAIL_ADDRESS または GMAIL_SENDER_EMAIL を .env ファイルに設定してください",
    "debug": error_details
}), 400
```

#### E. Password Validation
```python
gmail_password = gmail_password.replace(' ', '')  # Remove spaces
if len(gmail_password) != 16:
    logger.warning(f"Gmail app password has unexpected length: {len(gmail_password)}")
```

#### F. Granular SMTP Error Handling
```python
try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context, timeout=30) as server:
        logger.info("SMTP connection established, attempting login...")
        server.login(from_email, gmail_password)
        logger.info("Login successful, sending message...")
        server.send_message(msg)
        logger.info("Message sent successfully")
except smtplib.SMTPAuthenticationError as auth_error:
    # Specific handling for authentication errors
except smtplib.SMTPException as smtp_error:
    # Specific handling for other SMTP errors
```

#### G. Enhanced Logging
Added detailed logging at each step:
- Environment variable loading
- Configuration retrieval
- SMTP connection status
- Login status
- Message sending status

### 3. Error Response Structure

All error responses now follow this structure:

```json
{
  "success": false,
  "error": "User-friendly error message",
  "details": "Technical details about the error",
  "help": "Guidance on how to fix the issue (optional)",
  "debug": {
    "additional": "debugging information"
  }
}
```

## Testing

### Manual Test
```bash
curl -X POST http://localhost:3030/api/test-notification \
  -H "Content-Type: application/json" \
  -d '{"message": "Test notification"}'
```

### Expected Success Response
```json
{
  "success": true,
  "message": "✅ テスト通知を送信しました！\n\n送信先: kensan1969@gmail.com\nメールボックスをご確認ください。",
  "details": {
    "from": "kensan1969@gmail.com",
    "to": "kensan1969@gmail.com",
    "sent_at": "2025-11-14T23:30:00.123456"
  }
}
```

### Test Script
A comprehensive test script has been created at `/tmp/test_notification_endpoint.py`:

```bash
python3 /tmp/test_notification_endpoint.py
```

## Security Considerations

1. **App Password**: Using Gmail app password (16 characters) instead of regular password
2. **2-Factor Authentication**: Requires 2FA to be enabled on the Gmail account
3. **Environment Variables**: Sensitive credentials stored in `.env` file (not committed to git)
4. **SSL/TLS**: Using SMTP_SSL for encrypted communication

## Dependencies

All required packages are already installed:
- Flask 3.1.1
- python-dotenv 1.1.1
- smtplib (built-in)
- ssl (built-in)
- email (built-in)

## Related Files

- `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/web_app.py` - Main application file
- `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/.env` - Environment variables (created)
- `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/.env.example` - Template file
- `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config.json` - Application configuration

## Next Steps

1. Start the Flask application: `python3 app/web_app.py`
2. Test the endpoint using the test script
3. Monitor logs for any errors: `tail -f logs/app.log`
4. Verify email delivery in the Gmail inbox

## Rollback Plan

If issues occur, the git history contains the previous version. To rollback:

```bash
git log -1 --oneline app/web_app.py  # Check last commit
git checkout HEAD~1 -- app/web_app.py  # Restore previous version
```

## Notes

- The Gmail app password provided: `sxsg mzbv ubsa jtok` (spaces removed automatically)
- Email address: `kensan1969@gmail.com`
- SMTP server: `smtp.gmail.com:465` (SSL)
- Timeout set to 30 seconds for reliability
