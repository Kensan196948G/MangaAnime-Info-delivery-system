"""
Gunicorn設定ファイル
本番環境用のWSGIサーバー設定
"""
import os
import multiprocessing

# サーバーソケット
bind = "0.0.0.0:8000"
backlog = 2048

# ワーカープロセス
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# プロセス名
proc_name = "mangaanime-info-system"

# ログ設定
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# デーモン化（本番環境のみ）
daemon = False  # systemdで管理する場合はFalse

# プロセスID
pidfile = "/tmp/gunicorn_mangaanime.pid"

# ユーザー・グループ（本番環境で設定）
# user = "www-data"
# group = "www-data"

# 環境変数
raw_env = [
    f"FLASK_ENV=production",
]

# セキュリティ
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
