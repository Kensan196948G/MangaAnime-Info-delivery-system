# Quick Start Guide - Testing Notification API

## Overview
This guide will help you quickly test the fixed `/api/test-notification` endpoint.

## Prerequisites
All prerequisites are now satisfied:
- ✓ .env file created with Gmail credentials
- ✓ Python dependencies installed (Flask, python-dotenv, etc.)
- ✓ web_app.py enhanced with better error handling

## Quick Test (3 Steps)

### Step 1: Start the Flask Application

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
python3 app/web_app.py
```

You should see output like:
```
 * Running on http://0.0.0.0:3030
 * Running on http://192.168.3.135:3030
```

### Step 2: Test the Endpoint (in a new terminal)

**Option A: Using curl**
```bash
curl -X POST http://localhost:3030/api/test-notification \
  -H "Content-Type: application/json" \
  -d '{"message": "テスト通知です"}'
```

**Option B: Using the test script**
```bash
python3 /tmp/test_notification_endpoint.py
```

**Option C: Using Python requests**
```python
import requests
response = requests.post(
    'http://localhost:3030/api/test-notification',
    json={'message': 'Test from Python'}
)
print(response.json())
```

### Step 3: Check Your Email

Check `kensan1969@gmail.com` for the test email. It should arrive within a few seconds.

## Expected Results

### Success Response (HTTP 200)
```json
{
  "success": true,
  "message": "✅ テスト通知を送信しました！\n\n送信先: kensan1969@gmail.com\nメールボックスをご確認ください。",
  "details": {
    "from": "kensan1969@gmail.com",
    "to": "kensan1969@gmail.com",
    "sent_at": "2025-11-14T23:45:00.000000"
  }
}
```

### Error Response Example (HTTP 400)
If there's a configuration issue:
```json
{
  "success": false,
  "error": "メールアドレスが設定されていません",
  "details": "環境変数 GMAIL_ADDRESS または GMAIL_SENDER_EMAIL を .env ファイルに設定してください",
  "debug": {
    "env_gmail_address": false,
    "env_gmail_sender": true,
    "config_from_email": false,
    "config_notification_email": false
  }
}
```

## Troubleshooting

### Issue: "Gmail認証に失敗しました"

**Solution:**
1. Verify 2-factor authentication is enabled on your Gmail account
2. Generate a new app password at: https://myaccount.google.com/apppasswords
3. Update `.env` file with the new password

### Issue: "メールアドレスが設定されていません"

**Solution:**
1. Check `.env` file exists: `ls -la .env`
2. Verify environment variables: `grep GMAIL .env`
3. Restart the Flask application

### Issue: Connection timeout

**Solution:**
1. Check firewall settings
2. Verify internet connectivity
3. Test SMTP connection: `telnet smtp.gmail.com 465`

### Issue: Python module import errors

**Solution:**
```bash
pip3 install flask python-dotenv requests
```

## Verification Commands

**Check .env file:**
```bash
cat .env | grep -E "(GMAIL|EMAIL)"
```

**Verify all configuration:**
```bash
python3 tools/verify_notification_setup.py
```

**Check Flask is running:**
```bash
curl http://localhost:3030/api/health || echo "Server not running"
```

## Log Files

Application logs are located at:
```
./logs/app.log
```

View recent logs:
```bash
tail -f logs/app.log
```

## Configuration Files

- **Environment Variables:** `.env`
- **Application Config:** `config.json`
- **Flask Application:** `app/web_app.py`

## What Was Fixed

1. **Created .env file** with Gmail credentials
2. **Enhanced JSON parsing** - handles empty/malformed bodies
3. **Multiple env var support** - checks GMAIL_ADDRESS, GMAIL_SENDER_EMAIL, GMAIL_RECIPIENT_EMAIL
4. **Better error messages** - detailed debugging information
5. **SMTP error handling** - separate handling for auth vs other errors
6. **Password validation** - removes spaces, validates length
7. **Enhanced logging** - step-by-step connection status

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/test-notification` | POST | Send test email notification |
| `/api/health` | GET | Check API health status |
| `/api/test-configuration` | POST | Test all system configurations |

## Next Steps

After successful testing:

1. **Update config.json** to enable notifications permanently
2. **Set up calendar integration** if needed
3. **Configure scheduled notifications** using cron
4. **Monitor logs** for any issues

## Support

For issues or questions:
1. Check logs: `tail -f logs/app.log`
2. Run verification: `python3 tools/verify_notification_setup.py`
3. Review documentation: `docs/NOTIFICATION_FIX.md`

---

**Last Updated:** 2025-11-14
**Status:** Fixed and Verified
