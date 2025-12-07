#!/bin/bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
if [ -f "app/routes/__init__.py" ]; then
    echo "EXISTS: app/routes/__init__.py"
    cat app/routes/__init__.py
else
    echo "NOT FOUND: app/routes/__init__.py"
    echo "Creating new file..."
    cat > app/routes/__init__.py << 'EOF'
"""
Routes package
Contains all route blueprints for the application
"""
from app.routes.auth import auth_bp, init_login_manager

__all__ = ['auth_bp', 'init_login_manager']
EOF
    echo "Created successfully"
    cat app/routes/__init__.py
fi
