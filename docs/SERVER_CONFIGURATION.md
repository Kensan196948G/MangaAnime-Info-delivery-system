# サーバー設定ガイド

## 概要

アニメ・マンガ情報配信システムのWebUIは、柔軟なサーバー設定をサポートしています。このドキュメントでは、IPアドレス対応、ポート設定、環境変数の使用方法について説明します。

## 目次

1. [基本的な起動方法](#基本的な起動方法)
2. [IPアドレス対応](#ipアドレス対応)
3. [設定ファイル](#設定ファイル)
4. [環境変数](#環境変数)
5. [起動オプション](#起動オプション)
6. [トラブルシューティング](#トラブルシューティング)

---

## 基本的な起動方法

### デフォルト起動

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app
python3 start_web_ui.py
```

デフォルトでは以下の設定で起動します：
- **ホスト**: 0.0.0.0 (全インターフェース)
- **ポート**: 5000
- **デバッグモード**: 無効

### アクセスURL

起動すると、以下のようなURLが表示されます：

```
======================================================================
     アニメ・マンガ情報配信システム Web UI
======================================================================
  サーバー起動情報:
    - バインドアドレス: 0.0.0.0
    - ポート番号: 5000
    - デバッグモード: 無効

  アクセスURL:
    - ローカル: http://localhost:5000
    - ネットワーク: http://192.168.3.135:5000
    - 外部アクセス: http://<your-public-ip>:5000

  環境変数オプション:
    - SERVER_HOST: サーバーホストを指定
    - SERVER_PORT: サーバーポートを指定
    - DEBUG_MODE: デバッグモードを有効化
======================================================================
```

---

## IPアドレス対応

### 自動IPアドレス検出

システムは起動時に自動的にローカルIPアドレスを検出します。

**検出方法**:
1. Google DNS (8.8.8.8) への接続を確立
2. 使用されているネットワークインターフェースのIPアドレスを取得
3. 接続に失敗した場合は `127.0.0.1` にフォールバック

### ネットワークアクセス

同じネットワーク上の他のデバイスからアクセスする場合：

```bash
# 他のデバイスのブラウザで開く
http://192.168.3.135:5000
```

**注意**: ファイアウォール設定でポート5000を許可する必要がある場合があります。

### ローカルアクセスのみ

外部からのアクセスを制限したい場合：

```bash
python3 start_web_ui.py --localhost-only
```

これにより、`127.0.0.1` にバインドされ、同じマシンからのみアクセス可能になります。

---

## 設定ファイル

### config.json

サーバー設定は `config.json` に保存されます：

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 5000,
    "last_ip": "192.168.3.135",
    "auto_detect_ip": true,
    "cors_enabled": false,
    "allowed_origins": [
      "http://localhost:5000",
      "http://192.168.3.135:5000"
    ]
  }
}
```

### 設定項目の説明

| 項目 | 説明 | デフォルト値 |
|------|------|-------------|
| `host` | バインドするホストアドレス | `0.0.0.0` |
| `port` | リスニングポート番号 | `5000` |
| `last_ip` | 最後に検出されたIPアドレス | 自動検出 |
| `auto_detect_ip` | IP自動検出の有効化 | `true` |
| `cors_enabled` | CORS設定の有効化 | `false` |
| `allowed_origins` | 許可するオリジン | ローカルのみ |

### 設定の優先順位

1. **コマンドライン引数** (最優先)
2. **環境変数**
3. **config.json**
4. **デフォルト値** (最低優先)

---

## 環境変数

### 利用可能な環境変数

#### SERVER_HOST

サーバーがバインドするホストアドレスを指定します。

```bash
export SERVER_HOST=192.168.3.135
python3 start_web_ui.py
```

**値の例**:
- `0.0.0.0` - 全インターフェース (デフォルト)
- `127.0.0.1` - ローカルホストのみ
- `192.168.3.135` - 特定のIPアドレス

#### SERVER_PORT

リスニングポート番号を指定します。

```bash
export SERVER_PORT=8080
python3 start_web_ui.py
```

**注意**: 1024以下のポートを使用する場合は、管理者権限が必要です。

#### DEBUG_MODE

デバッグモードを有効にします。

```bash
export DEBUG_MODE=true
python3 start_web_ui.py
```

**値**:
- `true`, `1`, `yes` - デバッグモード有効
- その他 - デバッグモード無効

#### SECRET_KEY

Flaskのセッション管理に使用されるシークレットキーを指定します。

```bash
export SECRET_KEY=your-secret-key-here
python3 start_web_ui.py
```

**重要**: 本番環境では必ず安全なランダム文字列を使用してください。

### 環境変数の設定方法

#### 一時的な設定 (現在のセッションのみ)

```bash
export SERVER_HOST=0.0.0.0
export SERVER_PORT=8080
export DEBUG_MODE=false
python3 start_web_ui.py
```

#### 永続的な設定 (.bashrc / .zshrc)

```bash
# ~/.bashrc に追加
export SERVER_HOST=0.0.0.0
export SERVER_PORT=5000
export SECRET_KEY=your-production-secret-key
```

#### .envファイルを使用 (推奨)

`.env` ファイルを作成：

```bash
# .env
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
DEBUG_MODE=false
SECRET_KEY=your-secret-key-here
```

起動スクリプトで読み込み：

```bash
set -a
source .env
set +a
python3 start_web_ui.py
```

---

## 起動オプション

### 利用可能なコマンドライン引数

```bash
python3 start_web_ui.py [OPTIONS]
```

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--host HOST` | バインドするホスト | config.jsonまたは0.0.0.0 |
| `--port PORT` | リスニングポート | config.jsonまたは5000 |
| `--debug` | デバッグモードを有効化 | 無効 |
| `--no-auto-reload` | 自動リロードを無効化 | 有効 (debugモード時) |
| `--localhost-only` | ローカルホストのみバインド | 無効 |

### 使用例

#### カスタムポートで起動

```bash
python3 start_web_ui.py --port 8080
```

#### デバッグモードで起動

```bash
python3 start_web_ui.py --debug
```

#### デバッグモード + 自動リロード無効

```bash
python3 start_web_ui.py --debug --no-auto-reload
```

#### ローカルホストのみでカスタムポート

```bash
python3 start_web_ui.py --localhost-only --port 3000
```

#### 複数オプションの組み合わせ

```bash
python3 start_web_ui.py --host 192.168.3.135 --port 8080 --debug
```

---

## トラブルシューティング

### ポートが既に使用されている

**エラーメッセージ**:
```
エラー: ポート 5000 は既に使用されています。
別のポートを指定してください: --port <ポート番号>
```

**解決方法**:

1. **別のポートを使用**:
   ```bash
   python3 start_web_ui.py --port 8080
   ```

2. **使用中のプロセスを確認**:
   ```bash
   sudo lsof -i :5000
   ```

3. **プロセスを終了**:
   ```bash
   kill -9 <PID>
   ```

### ネットワークから接続できない

**原因**:
- ファイアウォールがポートをブロックしている
- `127.0.0.1` にバインドされている

**解決方法**:

1. **ファイアウォール設定を確認**:
   ```bash
   sudo ufw status
   sudo ufw allow 5000/tcp
   ```

2. **0.0.0.0にバインドされているか確認**:
   ```bash
   python3 start_web_ui.py --host 0.0.0.0
   ```

3. **ネットワーク設定を確認**:
   ```bash
   ip addr show
   ```

### IPアドレスが自動検出されない

**症状**: IPアドレスが `127.0.0.1` と表示される

**解決方法**:

1. **ネットワーク接続を確認**:
   ```bash
   ping 8.8.8.8
   ```

2. **手動でIPアドレスを指定**:
   ```bash
   python3 start_web_ui.py --host 192.168.3.135
   ```

3. **config.jsonを編集**:
   ```json
   {
     "server": {
       "host": "192.168.3.135",
       "auto_detect_ip": false
     }
   }
   ```

### 設定ファイルが見つからない

**警告メッセージ**:
```
⚠️  警告: 以下のファイルが見つかりません:
    - config.json
```

**解決方法**:

1. **設定ファイルを作成**:
   ```bash
   cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
   # メインシステムを実行して設定ファイルを生成
   python3 main.py
   ```

2. **手動で作成**:
   ```bash
   cp config.json.example config.json
   ```

### データベースが見つからない

**警告メッセージ**:
```
⚠️  警告: 以下のファイルが見つかりません:
    - db.sqlite3
```

**解決方法**:

1. **データベースを初期化**:
   ```bash
   cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
   python3 main.py
   ```

2. **modules/db.pyを実行**:
   ```bash
   python3 modules/db.py
   ```

---

## セキュリティのベストプラクティス

### 本番環境での推奨設定

1. **SECRET_KEYを必ず変更**:
   ```bash
   export SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
   ```

2. **デバッグモードを無効化**:
   ```bash
   export DEBUG_MODE=false
   ```

3. **HTTPS/リバースプロキシを使用**:
   - Nginx、Apacheなどでリバースプロキシを設定
   - SSL/TLS証明書を適用

4. **ファイアウォールを設定**:
   ```bash
   sudo ufw enable
   sudo ufw allow 5000/tcp
   ```

5. **適切なアクセス制限**:
   - 必要に応じて `allowed_origins` を設定
   - VPN経由でのアクセスを推奨

---

## クロスプラットフォーム対応

### Linux

```bash
python3 start_web_ui.py
```

### macOS

```bash
python3 start_web_ui.py
```

### Windows

```bash
python start_web_ui.py
```

または

```cmd
py start_web_ui.py
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=5000

EXPOSE 5000

CMD ["python", "app/start_web_ui.py"]
```

---

## 参考情報

### 関連ドキュメント

- [システム仕様書](../CLAUDE.md)
- [データベース設計](./DATABASE_DESIGN.md)
- [API仕様書](./API_REFERENCE.md)

### 外部リソース

- [Flask公式ドキュメント](https://flask.palletsprojects.com/)
- [Pythonソケットプログラミング](https://docs.python.org/3/library/socket.html)
- [環境変数のベストプラクティス](https://12factor.net/config)

---

## まとめ

このガイドでは、アニメ・マンガ情報配信システムのWebUIサーバー設定について説明しました。

**重要なポイント**:
1. IPアドレスは自動検出される
2. 設定は config.json、環境変数、コマンドライン引数で管理
3. 優先順位: CLI > 環境変数 > config.json > デフォルト
4. 本番環境では必ずSECRET_KEYを変更
5. ネットワークアクセスにはファイアウォール設定が必要

ご質問やサポートが必要な場合は、プロジェクトのissueトラッカーをご利用ください。
