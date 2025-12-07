#!/bin/bash
set -e
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

echo "Executing authentication integration..."
chmod +x integrate_auth_complete.sh
./integrate_auth_complete.sh

echo ""
echo "Verification..."
echo "Checking if changes were applied..."

echo ""
echo "1. Checking web_app.py for flask_login import..."
grep -n "from flask_login import" app/web_app.py || echo "  [NOT FOUND]"

echo ""
echo "2. Checking web_app.py for auth_bp registration..."
grep -n "register_blueprint.*auth_bp" app/web_app.py || echo "  [NOT FOUND]"

echo ""
echo "3. Checking web_app.py for @login_required decorator..."
grep -n "@login_required" app/web_app.py || echo "  [NOT FOUND]"

echo ""
echo "4. Checking routes/__init__.py..."
cat app/routes/__init__.py 2>/dev/null || echo "  [FILE NOT FOUND]"

echo ""
echo "5. Checking base.html for login status..."
grep -n "current_user.is_authenticated" templates/base.html || echo "  [NOT FOUND]"

echo ""
echo "Done!"
