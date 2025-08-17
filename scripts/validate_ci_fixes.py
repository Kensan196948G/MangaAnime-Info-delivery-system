#!/usr/bin/env python3
"""
CI Pipeline修正の検証スクリプト
"""

import yaml
import sys
from pathlib import Path


def validate_ci_fixes():
    """CI.ymlの修正内容を検証"""
    errors = []
    warnings = []

    ci_file = Path(".github/workflows/ci.yml")

    if not ci_file.exists():
        print("❌ CI.yml ファイルが見つかりません")
        return False

    with open(ci_file, "r") as f:
        content = f.read()

    # Pythonバージョンのチェック
    if "'3.9'" in content:
        errors.append("Python 3.9がまだ含まれています（setup.pyの要件は>=3.11）")

    if "'3.11'" in content and "'3.12'" in content:
        print("✅ Pythonバージョンマトリックス: 3.11, 3.12")

    # アクションバージョンのチェック
    old_versions = {
        "actions/cache@v3": "actions/cache@v4",
        "actions/download-artifact@v3": "actions/download-artifact@v4",
        "actions/github-script@v6": "actions/github-script@v7",
    }

    for old, new in old_versions.items():
        if old in content:
            errors.append(f"古いバージョン {old} が残っています（推奨: {new}）")
        elif new in content:
            print(f"✅ {new} 使用中")

    # 環境設定のチェック
    if "TESTING=true" in content:
        print("✅ テスト環境変数設定あり")
    else:
        warnings.append("テスト環境変数の設定が見つかりません")

    if "test.db" in content:
        print("✅ テストデータベース設定あり")
    else:
        warnings.append("テストデータベース設定が見つかりません")

    # 依存関係の確認
    if "needs: [test-summary]" in content:
        print("✅ notificationsジョブの依存関係が修正されています")

    # requirements.txtの重複チェック
    req_file = Path("requirements.txt")
    if req_file.exists():
        with open(req_file, "r") as f:
            req_lines = f.readlines()

        packages = {}
        for i, line in enumerate(req_lines, 1):
            if line.strip() and not line.startswith("#"):
                pkg = line.split(">=")[0].split("==")[0].strip()
                if pkg in packages:
                    errors.append(
                        f"requirements.txt: {pkg} が重複 (行 {packages[pkg]} と {i})"
                    )
                else:
                    packages[pkg] = i

    # pytest.iniの確認
    pytest_ini = Path("pytest.ini")
    if pytest_ini.exists():
        with open(pytest_ini, "r") as f:
            pytest_content = f.read()

        if "minversion = 7.4" in pytest_content:
            print("✅ pytest最小バージョン: 7.4")

        if "--cov-fail-under=60" in pytest_content:
            print("✅ カバレッジ要件: 60%")

    # 結果表示
    print("\n" + "=" * 50)

    if errors:
        print("❌ エラー:")
        for error in errors:
            print(f"   - {error}")

    if warnings:
        print("⚠️  警告:")
        for warning in warnings:
            print(f"   - {warning}")

    if not errors:
        print("✅ CI Pipeline修正の検証が成功しました！")
        return True
    else:
        print("❌ 修正が必要な問題があります")
        return False


if __name__ == "__main__":
    success = validate_ci_fixes()
    sys.exit(0 if success else 1)
