#!/bin/bash
#
# 認証統合の実行と検証
#

set -e
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

echo "========================================================================"
echo "認証機構統合 - 実行と検証"
echo "========================================================================"
echo ""

# 統合スクリプトを実行
echo "[1] Executing integration script..."
echo "------------------------------------------------------------------------"
python3 final_integration.py

# 検証
echo ""
echo "[2] Verification"
echo "------------------------------------------------------------------------"

echo ""
echo "2.1. Checking flask_login import in web_app.py..."
if grep -q "from flask_login import" app/web_app.py; then
    echo "  ✓ FOUND: $(grep "from flask_login import" app/web_app.py)"
else
    echo "  ✗ NOT FOUND"
fi

echo ""
echo "2.2. Checking auth_bp registration in web_app.py..."
if grep -q "register_blueprint.*auth_bp" app/web_app.py; then
    echo "  ✓ FOUND: $(grep "register_blueprint.*auth_bp" app/web_app.py)"
else
    echo "  ✗ NOT FOUND"
fi

echo ""
echo "2.3. Checking @login_required decorators in web_app.py..."
count=$(grep -c "@login_required" app/web_app.py || true)
echo "  Found $count instances of @login_required"
if [ "$count" -gt 0 ]; then
    grep -n "@login_required" app/web_app.py | head -5
fi

echo ""
echo "2.4. Checking routes/__init__.py..."
if [ -f "app/routes/__init__.py" ]; then
    echo "  ✓ File exists"
    if grep -q "from app.routes.auth import" app/routes/__init__.py; then
        echo "  ✓ auth module exported"
    else
        echo "  ✗ auth module not exported"
    fi
else
    echo "  ✗ File does not exist"
fi

echo ""
echo "2.5. Checking login status in base.html..."
if grep -q "current_user.is_authenticated" templates/base.html; then
    echo "  ✓ FOUND: Login status display added"
else
    echo "  ✗ NOT FOUND"
fi

echo ""
echo "========================================================================"
echo "✓ Verification Complete"
echo "========================================================================"
echo ""
echo "Please restart the application and test:"
echo "  python3 app/web_app.py"
echo ""
echo "Then visit:"
echo "  http://localhost:5000/auth/register"
echo "  http://localhost:5000/auth/login"
echo "  http://localhost:5000/settings"
echo ""
echo "========================================================================"
