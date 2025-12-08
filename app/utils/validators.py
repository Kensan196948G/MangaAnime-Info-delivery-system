"""
入力検証モジュール
Phase 14: セキュリティ強化

機能:
- パスワード強度検証（8文字以上 + 大文字・小文字・数字）
- ユーザー名検証
- メールアドレス検証
"""

import re
from typing import Tuple


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    パスワード強度検証

    要件:
    - 8文字以上
    - 大文字1文字以上
    - 小文字1文字以上
    - 数字1文字以上

    Args:
        password: 検証するパスワード

    Returns:
        tuple: (有効性, エラーメッセージまたは'OK')

    Examples:
        >>> validate_password_strength('Abc12345')
        (True, 'OK')

        >>> validate_password_strength('abc123')
        (False, 'パスワードは8文字以上である必要があります')

        >>> validate_password_strength('abcdefgh')
        (False, '大文字を1文字以上含める必要があります')
    """
    if not password:
        return False, "パスワードは必須です"

    if len(password) < 8:
        return False, "パスワードは8文字以上である必要があります"

    if not re.search(r"[A-Z]", password):
        return False, "大文字を1文字以上含める必要があります"

    if not re.search(r"[a-z]", password):
        return False, "小文字を1文字以上含める必要があります"

    if not re.search(r"[0-9]", password):
        return False, "数字を1文字以上含める必要があります"

    return True, "OK"


def validate_username(username: str) -> Tuple[bool, str]:
    """
    ユーザー名検証

    要件:
    - 3文字以上32文字以下
    - 英数字とアンダースコア、ハイフンのみ
    - 英字で開始

    Args:
        username: 検証するユーザー名

    Returns:
        tuple: (有効性, エラーメッセージまたは'OK')

    Examples:
        >>> validate_username('user123')
        (True, 'OK')

        >>> validate_username('ab')
        (False, 'ユーザー名は3文字以上32文字以下である必要があります')

        >>> validate_username('123user')
        (False, 'ユーザー名は英字で開始する必要があります')
    """
    if not username:
        return False, "ユーザー名は必須です"

    if len(username) < 3 or len(username) > 32:
        return False, "ユーザー名は3文字以上32文字以下である必要があります"

    if not re.match(r"^[a-zA-Z]", username):
        return False, "ユーザー名は英字で開始する必要があります"

    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        return False, "ユーザー名は英数字、アンダースコア、ハイフンのみ使用可能です"

    return True, "OK"


def validate_email(email: str) -> Tuple[bool, str]:
    """
    メールアドレス検証

    基本的なRFC 5322準拠の検証

    Args:
        email: 検証するメールアドレス

    Returns:
        tuple: (有効性, エラーメッセージまたは'OK')

    Examples:
        >>> validate_email('user@example.com')
        (True, 'OK')

        >>> validate_email('invalid-email')
        (False, '有効なメールアドレスを入力してください')

        >>> validate_email('user@')
        (False, '有効なメールアドレスを入力してください')
    """
    if not email:
        return False, "メールアドレスは必須です"

    # RFC 5322準拠の基本的なパターン
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, email):
        return False, "有効なメールアドレスを入力してください"

    # メールアドレス長チェック（RFC 5321: 最大254文字）
    if len(email) > 254:
        return False, "メールアドレスが長すぎます（最大254文字）"

    # ローカルパート長チェック（@の前、最大64文字）
    local_part = email.split("@")[0]
    if len(local_part) > 64:
        return False, "メールアドレスのローカルパートが長すぎます（最大64文字）"

    return True, "OK"


def validate_url(url: str) -> Tuple[bool, str]:
    """
    URL検証

    基本的なURL形式チェック

    Args:
        url: 検証するURL

    Returns:
        tuple: (有効性, エラーメッセージまたは'OK')
    """
    if not url:
        return False, "URLは必須です"

    url_pattern = r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$"

    if not re.match(url_pattern, url):
        return False, "有効なURLを入力してください（http://またはhttps://で開始）"

    return True, "OK"


# テスト実行用
if __name__ == "__main__":
    # パスワード検証テスト
    print("=" * 70)
    print("🧪 Validators テスト")
    print("=" * 70)

    test_passwords = [
        "Abc12345",  # ✅ 有効
        "abc12345",  # ❌ 大文字なし
        "ABC12345",  # ❌ 小文字なし
        "Abcdefgh",  # ❌ 数字なし
        "Abc123",  # ❌ 8文字未満
    ]

    print("\n【パスワード強度テスト】")
    for pwd in test_passwords:
        valid, msg = validate_password_strength(pwd)
        status = "✅" if valid else "❌"
        print(f"  {status} '{pwd}': {msg}")

    # ユーザー名検証テスト
    test_usernames = [
        "user123",  # ✅ 有効
        "ab",  # ❌ 短すぎる
        "123user",  # ❌ 数字開始
        "user@123",  # ❌ 無効文字
    ]

    print("\n【ユーザー名検証テスト】")
    for username in test_usernames:
        valid, msg = validate_username(username)
        status = "✅" if valid else "❌"
        print(f"  {status} '{username}': {msg}")

    # メール検証テスト
    test_emails = [
        "user@example.com",  # ✅ 有効
        "invalid-email",  # ❌ 無効
        "user@",  # ❌ ドメインなし
    ]

    print("\n【メールアドレス検証テスト】")
    for email in test_emails:
        valid, msg = validate_email(email)
        status = "✅" if valid else "❌"
        print(f"  {status} '{email}': {msg}")

    print("\n" + "=" * 70)
    print("✅ テスト完了")
    print("=" * 70)
