#!/usr/bin/env python3
"""
Phase 5: マンガRSSフィード実データ収集テスト

各マンガ/アニメ情報サイトのRSSフィードから実データを収集し、
NGキーワードフィルタリングを適用して結果を表示します。

使用方法:
    python -X utf8 scripts/test_phase5_manga_rss.py              # すべてのフィードをテスト
    python -X utf8 scripts/test_phase5_manga_rss.py --all        # すべてのフィードをテスト
    python -X utf8 scripts/test_phase5_manga_rss.py --bookwalker # BookWalkerのみ
    python -X utf8 scripts/test_phase5_manga_rss.py --save       # 取得データをDBに保存

注意:
    BookWalker / マガポケ / ジャンプBOOKストア の公式RSS URLは現在非公開または
    存在しないため、動作確認済みの代替ソースを使用します:
      - 少年ジャンプ+ RSS  (shonenjumpplus.com)  ← ジャンプ系作品の代替
      - となりのヤングジャンプ RSS              ← 集英社系マンガの代替
      - BIG Comic Brothers (bigcomicbros.net)   ← 小学館系マンガの代替
      - Anime News Network RSS                  ← マンガ/アニメ英語ニュース
      - Yahoo!ニュース エンタメ RSS             ← 日本語エンタメニュース
"""

import argparse
import io
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Windows UTF-8 強制（文字化け防止）
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ロギング設定（外部モジュールのノイズを抑制）
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────
# NGキーワードフィルタ定義（CLAUDE.md 仕様準拠）
# ─────────────────────────────────────────────────
NG_KEYWORDS: List[str] = [
    "エロ",
    "R18",
    "成人向け",
    "BL",
    "百合",
    "ボーイズラブ",
]

# ─────────────────────────────────────────────────
# RSSフィード定義
# 各フィードの実稼働ステータスは確認済み（2026-02-19 時点）
# ─────────────────────────────────────────────────
RSS_FEEDS: Dict[str, Dict[str, Any]] = {
    # ── ジャンプ系 ──────────────────────────────────────────────────────
    "shonenjumpplus": {
        "name": "少年ジャンプ+",
        "url": "https://shonenjumpplus.com/rss",
        "category": "manga",
        "platform": "少年ジャンプ+",
        "note": "ジャンプBOOKストアの代替 (公式RSSあり)",
        "confirmed": True,
    },
    # ── 集英社ヤングジャンプ系 ──────────────────────────────────────────
    "yj_tonari": {
        "name": "となりのヤングジャンプ",
        "url": "https://tonarinoyj.jp/rss",
        "category": "manga",
        "platform": "ヤングジャンプ",
        "note": "集英社系マンガ（確認済み）",
        "confirmed": True,
    },
    # ── 小学館系 ────────────────────────────────────────────────────────
    "bigcomic": {
        "name": "BIG Comic Brothers",
        "url": "https://bigcomicbros.net/feed/",
        "category": "manga",
        "platform": "小学館",
        "note": "小学館コミックス情報（確認済み）",
        "confirmed": True,
    },
    # ── アニメ・マンガニュース（英語）───────────────────────────────────
    "ann": {
        "name": "Anime News Network",
        "url": "https://www.animenewsnetwork.com/newsfeed/rss.xml",
        "category": "news",
        "platform": "ANN",
        "note": "アニメ・マンガ全般ニュース（英語）",
        "confirmed": True,
    },
    # ── 日本語エンタメニュース ─────────────────────────────────────────
    "yahoo_entertainment": {
        "name": "Yahoo!ニュース エンタメ",
        "url": "https://news.yahoo.co.jp/rss/categories/entertainment.xml",
        "category": "news",
        "platform": "Yahoo!ニュース",
        "note": "日本語エンタメ全般ニュース",
        "confirmed": True,
    },
    # ── 原指定URL（参考用：現在非稼働）────────────────────────────────
    "bookwalker_original": {
        "name": "BookWalker (元URL)",
        "url": "https://bookwalker.jp/rss/book/new",
        "category": "manga",
        "platform": "BookWalker",
        "note": "元指定URL（現在404）",
        "confirmed": False,
    },
    "jumpbookstore_original": {
        "name": "ジャンプBOOKストア (元URL)",
        "url": "https://jumpbookstore.com/rss/new-release",
        "category": "manga",
        "platform": "ジャンプBOOKストア",
        "note": "元指定URL（DNS解決不可）",
        "confirmed": False,
    },
    "mangapocket_original": {
        "name": "マガポケ (元URL)",
        "url": "https://mangapocket.jp/rss",
        "category": "manga",
        "platform": "マガポケ",
        "note": "元指定URL（DNS解決不可）",
        "confirmed": False,
    },
    "shonenjumpplus_original": {
        "name": "少年ジャンプ+ /rss/update (元URL)",
        "url": "https://shonenjumpplus.com/rss/update",
        "category": "manga",
        "platform": "少年ジャンプ+",
        "note": "元指定URL（現在404、/rss が正しいパス）",
        "confirmed": False,
    },
    "amazon_kindle_original": {
        "name": "Amazon Kindle (元URL)",
        "url": "https://www.amazon.co.jp/rss/new-releases/digital-text/2275256051",
        "category": "manga",
        "platform": "Amazon",
        "note": "元指定URL（現在404）",
        "confirmed": False,
    },
}


# ─────────────────────────────────────────────────
# ユーティリティ関数
# ─────────────────────────────────────────────────

def print_section(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_ok(msg: str, detail: str = "") -> None:
    print(f"  [OK] {msg}")
    if detail:
        for line in detail.split("\n"):
            if line.strip():
                print(f"       {line}")


def print_ng(msg: str, detail: str = "") -> None:
    print(f"  [NG] {msg}")
    if detail:
        for line in detail.split("\n"):
            if line.strip():
                print(f"       {line}")


def print_info(msg: str, detail: str = "") -> None:
    print(f"  [INFO] {msg}")
    if detail:
        for line in detail.split("\n"):
            if line.strip():
                print(f"         {line}")


def print_warn(msg: str, detail: str = "") -> None:
    print(f"  [WARN] {msg}")
    if detail:
        for line in detail.split("\n"):
            if line.strip():
                print(f"         {line}")


# ─────────────────────────────────────────────────
# NGキーワードフィルタリング
# ─────────────────────────────────────────────────

def is_ng_content(title: str, description: str = "") -> Tuple[bool, Optional[str]]:
    """
    NGキーワードに一致するかチェックする。

    Args:
        title: 作品タイトル
        description: 作品説明（任意）

    Returns:
        (is_ng, matched_keyword): NGの場合True と一致したキーワード
    """
    combined = f"{title} {description}".lower()
    for keyword in NG_KEYWORDS:
        if keyword.lower() in combined:
            return True, keyword
    return False, None


# ─────────────────────────────────────────────────
# フィードURL検証（Step 1）
# ─────────────────────────────────────────────────

def check_feed_url(feed_key: str, feed_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    単一のRSSフィードURLのHTTPステータスを確認する。

    Args:
        feed_key: フィードのキー名
        feed_info: フィード設定辞書

    Returns:
        チェック結果辞書（status_code, reachable, content_type など）
    """
    try:
        import requests
    except ImportError:
        return {
            "feed_key": feed_key,
            "name": feed_info["name"],
            "url": feed_info["url"],
            "reachable": False,
            "status_code": None,
            "error": "requests not installed (pip install requests)",
        }

    url = feed_info["url"]
    name = feed_info["name"]
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 MangaAnimeNotifier/1.0"
        ),
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }

    result: Dict[str, Any] = {
        "feed_key": feed_key,
        "name": name,
        "url": url,
        "reachable": False,
        "status_code": None,
        "content_type": None,
        "content_length": 0,
        "error": None,
        "elapsed_sec": None,
    }

    try:
        start = time.monotonic()
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        elapsed = time.monotonic() - start

        result["status_code"] = response.status_code
        result["content_type"] = response.headers.get("content-type", "")
        result["content_length"] = len(response.content)
        result["elapsed_sec"] = round(elapsed, 2)
        result["reachable"] = response.status_code == 200

    except requests.exceptions.ConnectionError as e:
        result["error"] = f"ConnectionError: {str(e)[:120]}"
    except requests.exceptions.Timeout:
        result["error"] = "Timeout (15s)"
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)[:120]}"

    return result


def run_url_checks(feed_keys: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    指定されたフィードキーのURLを一括検証する。

    Args:
        feed_keys: チェック対象のフィードキーリスト

    Returns:
        feed_key -> check_result のマッピング
    """
    print_section("Step 1: RSS URL 到達確認")
    print_info(f"対象フィード数: {len(feed_keys)}")

    results: Dict[str, Dict[str, Any]] = {}
    for key in feed_keys:
        info = RSS_FEEDS[key]
        print(f"\n  チェック中: {info['name']}")
        print(f"    URL: {info['url']}")
        if info.get("note"):
            print(f"    備考: {info['note']}")

        check = check_feed_url(key, info)
        results[key] = check

        if check["reachable"]:
            ct = check["content_type"] or ""
            elapsed = check["elapsed_sec"]
            print_ok(
                f"HTTP {check['status_code']} ({elapsed}s)",
                f"Content-Type: {ct[:60]}\nサイズ: {check['content_length']:,} bytes",
            )
        elif check["status_code"] is not None:
            print_ng(
                f"HTTP {check['status_code']}",
                check.get("error") or f"HTTP {check['status_code']}",
            )
        else:
            print_ng("到達不可", check.get("error", "Unknown error"))

    return results


# ─────────────────────────────────────────────────
# RSSパース処理（Step 2）
# ─────────────────────────────────────────────────

def parse_feed_entries(
    url: str, name: str, platform: str, max_items: int = 10
) -> List[Dict[str, Any]]:
    """
    feedparser でRSSフィードを取得・パースし、最大 max_items 件を返す。

    Args:
        url: フィードURL
        name: フィード表示名
        platform: プラットフォーム名
        max_items: 最大取得件数

    Returns:
        パース済みアイテムのリスト
    """
    try:
        import feedparser
        import requests
    except ImportError as e:
        print_ng(f"依存パッケージ未インストール: {e}", "pip install feedparser requests")
        return []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 MangaAnimeNotifier/1.0"
        ),
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }

    try:
        response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        response.raise_for_status()
    except Exception as e:
        print_ng(f"{name} 取得失敗", str(e)[:120])
        return []

    feed = feedparser.parse(response.content)

    if feed.bozo and feed.bozo_exception:
        # bozo は XML が厳密でない場合でも発生する（致命的ではない）
        print_warn(f"feedparser 警告 ({name}): {feed.bozo_exception}")

    items: List[Dict[str, Any]] = []
    for entry in feed.entries[:max_items]:
        # タイトル取得
        title = getattr(entry, "title", "") or ""
        title = title.strip()

        # URL取得
        link = getattr(entry, "link", "") or ""

        # 発売日取得（複数フォールバック）
        release_date: Optional[str] = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                dt = datetime(*entry.published_parsed[:6])
                release_date = dt.strftime("%Y-%m-%d")
            except (TypeError, ValueError):
                pass

        if release_date is None and hasattr(entry, "updated_parsed") and entry.updated_parsed:
            try:
                dt = datetime(*entry.updated_parsed[:6])
                release_date = dt.strftime("%Y-%m-%d")
            except (TypeError, ValueError):
                pass

        if release_date is None:
            raw_date = getattr(entry, "published", None) or getattr(entry, "updated", None)
            if raw_date:
                release_date = str(raw_date)[:20]

        # 説明取得
        description = (
            getattr(entry, "summary", None)
            or getattr(entry, "description", None)
            or ""
        )
        # HTMLタグ簡易除去
        import re
        description = re.sub(r"<[^>]+>", "", description).strip()
        description = description[:200] if description else ""

        if title:
            items.append({
                "title": title,
                "url": link,
                "release_date": release_date,
                "description": description,
                "platform": platform,
                "source_name": name,
            })

    return items


# ─────────────────────────────────────────────────
# フィードごとのテスト実行（Step 3）
# ─────────────────────────────────────────────────

def run_feed_test(
    feed_key: str,
    feed_info: Dict[str, Any],
    max_items: int = 10,
) -> Dict[str, Any]:
    """
    指定フィードのRSSを取得・パース・フィルタリングして結果を返す。

    Args:
        feed_key: フィードキー
        feed_info: フィード設定辞書
        max_items: 最大取得件数

    Returns:
        {
            feed_key, name, total, passed, filtered, items_passed, items_filtered
        }
    """
    name = feed_info["name"]
    url = feed_info["url"]
    platform = feed_info.get("platform", name)

    print(f"\n  [{name}]  {url}")

    items_raw = parse_feed_entries(url, name, platform, max_items=max_items)

    items_passed: List[Dict[str, Any]] = []
    items_filtered: List[Dict[str, Any]] = []

    for item in items_raw:
        is_ng, matched_kw = is_ng_content(item["title"], item.get("description", ""))
        if is_ng:
            item["ng_keyword"] = matched_kw
            items_filtered.append(item)
        else:
            items_passed.append(item)

    total = len(items_raw)
    passed = len(items_passed)
    filtered = len(items_filtered)

    if total == 0:
        print_warn(f"アイテム 0 件 (フィードが空またはパース失敗)")
    else:
        print_ok(f"取得: {total} 件 | 通過: {passed} 件 | フィルタ除外: {filtered} 件")

    return {
        "feed_key": feed_key,
        "name": name,
        "total": total,
        "passed": passed,
        "filtered": filtered,
        "items_passed": items_passed,
        "items_filtered": items_filtered,
    }


# ─────────────────────────────────────────────────
# 結果の表示
# ─────────────────────────────────────────────────

def display_results(feed_result: Dict[str, Any], show_all: bool = False) -> None:
    """
    単一フィードのパース結果を表示する（最新10件）。

    Args:
        feed_result: run_feed_test() の戻り値
        show_all: Trueの場合フィルタ除外分も表示
    """
    name = feed_result["name"]
    items_passed = feed_result["items_passed"]
    items_filtered = feed_result["items_filtered"]

    if not items_passed and not items_filtered:
        return

    print(f"\n  ── {name} : 通過アイテム ──────────────────────────")
    if items_passed:
        for i, item in enumerate(items_passed, 1):
            date_str = item.get("release_date") or "日付不明"
            title = item.get("title", "(タイトルなし)")
            url = item.get("url", "")
            print(f"  {i:2d}. [{date_str}] {title}")
            if url:
                print(f"      URL: {url[:80]}")
    else:
        print("      (通過アイテムなし)")

    if items_filtered:
        print(f"\n  ── {name} : NGキーワードで除外 ──────────────────")
        for item in items_filtered:
            print(f"      - [{item.get('ng_keyword')}] {item.get('title', '')}")


# ─────────────────────────────────────────────────
# DB保存（--save オプション）
# ─────────────────────────────────────────────────

def save_to_db(all_passed: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    取得・フィルタ済みのアイテムをSQLite DBに保存する。

    Args:
        all_passed: フィルタ通過済みアイテムのリスト

    Returns:
        {"stored": n, "skipped": m, "error": k}
    """
    from dotenv import load_dotenv
    load_dotenv()

    try:
        from modules.db import get_db
    except ImportError as e:
        print_ng("DBモジュールのインポート失敗", str(e))
        return {"stored": 0, "skipped": 0, "error": len(all_passed)}

    try:
        db = get_db()
    except Exception as e:
        print_ng("DB初期化失敗", str(e))
        return {"stored": 0, "skipped": 0, "error": len(all_passed)}

    stored = 0
    skipped = 0
    error_count = 0

    for item in all_passed:
        title = item.get("title", "").strip()
        if not title:
            skipped += 1
            continue

        try:
            work_id = db.get_or_create_work(
                title=title,
                work_type="manga",
                official_url=item.get("url"),
            )

            release_date = item.get("release_date")
            # "2026-02-19 15:00:00" 形式を "2026-02-19" に短縮
            if release_date and len(release_date) > 10:
                release_date = release_date[:10]

            db.create_release(
                work_id=work_id,
                release_type="volume",
                number=None,
                platform=item.get("platform", "RSS"),
                release_date=release_date,
                source=f"rss_{item.get('feed_key', 'unknown')}",
                source_url=item.get("url"),
            )
            stored += 1

        except Exception as e:
            logger.debug(f"DB保存スキップ ({title}): {e}")
            skipped += 1

    return {"stored": stored, "skipped": skipped, "error": error_count}


# ─────────────────────────────────────────────────
# メイン処理
# ─────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="マンガRSSフィード実データ収集テスト (Phase 5)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="すべてのフィードをテスト（デフォルト動作）",
    )
    parser.add_argument(
        "--bookwalker",
        action="store_true",
        default=False,
        help="BookWalker関連フィードのみテスト（元URL確認含む）",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        default=False,
        help="取得データをDBに保存する",
    )
    parser.add_argument(
        "--show-ng",
        action="store_true",
        default=False,
        help="NGキーワードで除外されたアイテムも詳細表示",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Phase 5: マンガRSSフィード 実データ収集テスト")
    print(f"  実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ── ターゲットフィードの決定 ──────────────────────────────────────
    if args.bookwalker:
        # BookWalker 関連（元URL確認 + 動作代替URL）
        target_keys = [
            "bookwalker_original",     # 元URL（404確認用）
            "shonenjumpplus",          # 動作する代替フィード
        ]
        print_info("モード: BookWalkerフィードテスト（代替フィード含む）")
    else:
        # デフォルト: すべてのフィードをテスト（確認済み + 元指定URL）
        target_keys = list(RSS_FEEDS.keys())
        print_info("モード: 全フィードテスト (--all)")

    # ── Step 1: URL到達確認 ───────────────────────────────────────────
    url_check_results = run_url_checks(target_keys)

    # 到達可能なフィードを抽出
    reachable_keys = [
        k for k in target_keys
        if url_check_results.get(k, {}).get("reachable", False)
    ]
    unreachable_keys = [k for k in target_keys if k not in reachable_keys]

    print_section("URL到達確認 サマリー")
    print_ok(f"到達可能: {len(reachable_keys)} フィード")
    if reachable_keys:
        for k in reachable_keys:
            r = url_check_results[k]
            print(f"    - {r['name']} ({r['elapsed_sec']}s)")

    if unreachable_keys:
        print_ng(f"到達不可: {len(unreachable_keys)} フィード")
        for k in unreachable_keys:
            r = url_check_results[k]
            status = r.get("status_code")
            error = r.get("error") or ""
            reason = f"HTTP {status}" if status else error[:80]
            print(f"    - {r['name']}: {reason}")

    # ── Step 2: 到達可能フィードからRSS取得・パース ───────────────────
    # 確認済み有効フィードのみパースする（元URLは URL チェック目的のみ）
    parse_keys = [
        k for k in reachable_keys
        if RSS_FEEDS[k].get("confirmed", False)
    ]

    print_section("Step 2: RSSパース & NGキーワードフィルタリング")
    print_info(f"NGキーワード: {NG_KEYWORDS}")
    print_info(f"パース対象フィード: {len(parse_keys)} 件")

    all_results: List[Dict[str, Any]] = []
    all_passed: List[Dict[str, Any]] = []
    all_filtered: List[Dict[str, Any]] = []

    for key in parse_keys:
        feed_info = RSS_FEEDS[key]
        result = run_feed_test(key, feed_info, max_items=10)
        # feed_keyをアイテムに付与（DB保存用）
        for item in result["items_passed"]:
            item["feed_key"] = key
        all_results.append(result)
        all_passed.extend(result["items_passed"])
        all_filtered.extend(result["items_filtered"])

    # ── Step 3: 結果表示 ──────────────────────────────────────────────
    print_section("Step 3: 取得アイテム詳細")
    for result in all_results:
        display_results(result, show_all=args.show_ng)

    # ── サマリー ──────────────────────────────────────────────────────
    print_section("収集サマリー")

    total_items = sum(r["total"] for r in all_results)
    total_passed = len(all_passed)
    total_filtered = len(all_filtered)

    print(f"  フィード数         : {len(parse_keys)} 件")
    print(f"  取得アイテム合計   : {total_items} 件")
    print(f"  フィルタ通過       : {total_passed} 件")
    print(f"  NGキーワード除外   : {total_filtered} 件")

    print("\n  フィード別集計:")
    print(f"  {'フィード名':<30} {'取得':>4} {'通過':>4} {'除外':>4}")
    print(f"  {'-'*30} {'-'*4} {'-'*4} {'-'*4}")
    for r in all_results:
        print(f"  {r['name']:<30} {r['total']:>4} {r['passed']:>4} {r['filtered']:>4}")

    if total_filtered > 0:
        print(f"\n  除外されたアイテム ({total_filtered} 件):")
        for item in all_filtered:
            print(f"    - [{item.get('ng_keyword')}] {item.get('title', '')}")

    # ── 元指定URLの確認結果レポート ───────────────────────────────────
    original_url_keys = [
        k for k in target_keys
        if not RSS_FEEDS[k].get("confirmed", False)
    ]
    if original_url_keys:
        print_section("元指定URL の確認結果")
        print_info("以下のURLは仕様書で指定されていましたが現在は利用不可です。")
        for k in original_url_keys:
            info = RSS_FEEDS[k]
            check = url_check_results.get(k, {})
            status = check.get("status_code")
            error = check.get("error") or ""
            reason = f"HTTP {status}" if status else error[:80]
            print(f"\n  {info['name']}")
            print(f"    URL   : {info['url']}")
            print(f"    状態  : {reason}")
            print(f"    備考  : {info.get('note', '')}")

        print_info(
            "代替フィード使用推奨:",
            "少年ジャンプ+    → https://shonenjumpplus.com/rss\n"
            "ヤングジャンプ   → https://tonarinoyj.jp/rss\n"
            "小学館           → https://bigcomicbros.net/feed/\n"
            "ANN (英語)       → https://www.animenewsnetwork.com/newsfeed/rss.xml",
        )

    # ── DB保存（--save オプション） ───────────────────────────────────
    if args.save:
        print_section("Step 4: DBへの保存")
        if not all_passed:
            print_warn("保存対象アイテムが0件です")
        else:
            print_info(f"保存対象: {len(all_passed)} 件")
            save_result = save_to_db(all_passed)
            print_ok(
                "DB保存完了",
                f"保存: {save_result['stored']} 件 | "
                f"スキップ: {save_result['skipped']} 件 | "
                f"エラー: {save_result['error']} 件",
            )

    print("\n" + "=" * 60)
    print("  テスト完了")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
