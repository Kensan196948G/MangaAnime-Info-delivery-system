#!/usr/bin/env python3
"""
Phase 2: AniList GraphQL API & しょぼいカレンダー API 実データ収集テスト

このスクリプトは実際のAPIに接続してアニメ情報を取得します。

使用方法:
    python -X utf8 scripts/test_phase2_api.py --anilist       # AniList APIテスト
    python -X utf8 scripts/test_phase2_api.py --syoboi        # しょぼいカレンダーテスト
    python -X utf8 scripts/test_phase2_api.py --all           # すべて実行
    python -X utf8 scripts/test_phase2_api.py --save          # DB保存も実行
"""

import argparse
import asyncio
import io
import json
import logging
import sys
from datetime import datetime, date
from pathlib import Path

# Windows UTF-8強制
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.WARNING,  # 外部モジュールのログを抑制
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def print_section(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_ok(msg: str, detail: str = ""):
    print(f"  ✅ {msg}")
    if detail:
        for line in detail.split("\n"):
            if line:
                print(f"       {line}")


def print_ng(msg: str, detail: str = ""):
    print(f"  ❌ {msg}")
    if detail:
        for line in detail.split("\n"):
            if line:
                print(f"       {line}")


def print_info(msg: str, detail: str = ""):
    print(f"  ℹ️  {msg}")
    if detail:
        for line in detail.split("\n"):
            if line:
                print(f"       {line}")


# ─────────────────────────────────────────────────
# 1. AniList GraphQL API テスト
# ─────────────────────────────────────────────────

async def test_anilist_direct() -> dict:
    """AniList GraphQL API に直接クエリして今期アニメを取得"""
    print_section("AniList GraphQL API テスト")

    result = {
        "success": False,
        "anime_count": 0,
        "sample_titles": [],
        "streaming_platforms": set(),
        "error": None,
    }

    # 現在のシーズンを判定
    now = datetime.now()
    month = now.month
    year = now.year
    if month in [12, 1, 2]:
        season = "WINTER"
    elif month in [3, 4, 5]:
        season = "SPRING"
    elif month in [6, 7, 8]:
        season = "SUMMER"
    else:
        season = "FALL"

    print_info(f"対象シーズン: {year}年 {season}")

    # GraphQLクエリ（今期放送中アニメ）
    query = """
    query ($season: MediaSeason, $year: Int, $perPage: Int) {
      Page(perPage: $perPage) {
        pageInfo {
          total
          hasNextPage
        }
        media(
          season: $season
          seasonYear: $year
          type: ANIME
          status: RELEASING
          sort: POPULARITY_DESC
        ) {
          id
          title {
            romaji
            english
            native
          }
          status
          episodes
          nextAiringEpisode {
            airingAt
            episode
          }
          streamingEpisodes {
            title
            site
            url
          }
          genres
          averageScore
          popularity
          coverImage {
            medium
          }
        }
      }
    }
    """

    variables = {
        "season": season,
        "year": year,
        "perPage": 20,
    }

    try:
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            print_info("API接続中...", "https://graphql.anilist.co")

            async with session.post(
                "https://graphql.anilist.co",
                json={"query": query, "variables": variables},
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            ) as response:
                if response.status != 200:
                    result["error"] = f"HTTP {response.status}"
                    print_ng("APIレスポンスエラー", f"HTTP {response.status}")
                    return result

                data = await response.json()

    except ImportError:
        print_ng("aiohttp未インストール", "pip install aiohttp")
        result["error"] = "aiohttp not installed"
        return result
    except Exception as e:
        print_ng("接続エラー", str(e))
        result["error"] = str(e)
        return result

    # レスポンス解析
    if "errors" in data:
        errors = data["errors"]
        print_ng("GraphQLエラー", str(errors))
        result["error"] = str(errors)
        return result

    page_data = data.get("data", {}).get("Page", {})
    page_info = page_data.get("pageInfo", {})
    media_list = page_data.get("media", [])

    total = page_info.get("total", 0)
    result["anime_count"] = len(media_list)
    result["success"] = True

    print_ok(
        f"API接続成功",
        f"総件数: {total}作品 / 取得: {len(media_list)}作品",
    )

    # 配信プラットフォーム集計
    all_platforms = set()
    for anime in media_list:
        for ep in anime.get("streamingEpisodes", []):
            site = ep.get("site", "").strip()
            if site:
                all_platforms.add(site)

    result["streaming_platforms"] = all_platforms

    # 今期アニメ一覧表示
    print("\n  📺 今期放送中アニメ（人気順）:\n")
    ng_keywords = ["エロ", "R18", "成人向け", "BL", "百合", "ボーイズラブ", "Hentai"]

    filtered_count = 0
    shown_count = 0

    for i, anime in enumerate(media_list, 1):
        title_native = anime.get("title", {}).get("native") or ""
        title_romaji = anime.get("title", {}).get("romaji") or "Unknown"
        title_en = anime.get("title", {}).get("english") or ""
        score = anime.get("averageScore") or 0
        popularity = anime.get("popularity") or 0
        episodes = anime.get("episodes") or "?"
        genres = anime.get("genres", [])

        # NGフィルタ
        is_ng = any(
            kw.lower() in (title_native + title_romaji + title_en).lower()
            for kw in ng_keywords
        )
        if is_ng:
            filtered_count += 1
            continue

        # 配信プラットフォーム
        streaming = anime.get("streamingEpisodes", [])
        platforms = list({ep.get("site", "") for ep in streaming if ep.get("site")})
        platform_str = ", ".join(sorted(platforms)[:3]) if platforms else "不明"

        # 次回放送
        next_ep = anime.get("nextAiringEpisode")
        if next_ep:
            airing_ts = next_ep.get("airingAt", 0)
            ep_num = next_ep.get("episode", "?")
            if airing_ts:
                airing_dt = datetime.fromtimestamp(airing_ts)
                next_info = f"第{ep_num}話: {airing_dt.strftime('%m/%d %H:%M')}"
            else:
                next_info = f"第{ep_num}話"
        else:
            next_info = "放送終了"

        print(f"  {i:2d}. 【{title_native or title_romaji}】")
        if title_en and title_en != title_romaji:
            print(f"       EN: {title_en}")
        print(f"       スコア: {score}/100  人気: {popularity:,}  話数: {episodes}")
        print(f"       ジャンル: {', '.join(genres[:3])}")
        print(f"       配信: {platform_str}")
        print(f"       次回: {next_info}")
        print()

        result["sample_titles"].append({
            "native": title_native,
            "romaji": title_romaji,
            "score": score,
            "platforms": platforms,
        })
        shown_count += 1

    if filtered_count > 0:
        print_info(f"NGフィルタで除外: {filtered_count}作品")

    if all_platforms:
        print_ok(
            "配信プラットフォーム検出",
            "  ".join(sorted(all_platforms)),
        )

    return result


# ─────────────────────────────────────────────────
# 2. しょぼいカレンダー API テスト
# ─────────────────────────────────────────────────

async def test_syoboi_api() -> dict:
    """しょぼいカレンダー API テスト（2段階: ProgLookup → TitleLookup）"""
    print_section("しょぼいカレンダー API テスト")

    result = {
        "success": False,
        "program_count": 0,
        "sample_titles": [],
        "error": None,
    }

    # 本日の番組を取得
    today = date.today()
    # しょぼいカレンダーAPI形式: YYYYMMDD_HHMMSS
    start_str = today.strftime("%Y%m%d") + "_000000"
    end_str = today.strftime("%Y%m%d") + "_235959"

    syoboi_url = "https://cal.syoboi.jp/db.php"

    try:
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=15)
        import xml.etree.ElementTree as ET

        async with aiohttp.ClientSession(timeout=timeout) as session:
            print_info("しょぼいカレンダーAPI接続中...", "https://cal.syoboi.jp/")

            # ── Step 1: ProgLookup で本日の放送スケジュール取得 ──
            params = {
                "Command": "ProgLookup",
                "Range": f"{start_str}-{end_str}",
                "JOIN": "SubTitles",
            }
            async with session.get(syoboi_url, params=params) as response:
                if response.status != 200:
                    print_ng("APIレスポンスエラー", f"HTTP {response.status}")
                    result["error"] = f"HTTP {response.status}"
                    return result
                raw_text = await response.text(encoding="utf-8", errors="replace")

            root = ET.fromstring(raw_text)
            prog_items = root.findall(".//ProgItem")
            result["program_count"] = len(prog_items)

            if not prog_items:
                print_ok("API接続成功", "本日の放送予定はありません")
                result["success"] = True
                return result

            print_ok("API接続成功", f"本日の番組: {len(prog_items)}件")

            # ── Step 2: TIDを収集してバッチでTitleLookup ──
            tids = list({p.findtext("TID") for p in prog_items if p.findtext("TID")})
            tid_to_title = {}

            if tids:
                # 最大50件ずつバッチ処理
                for batch_start in range(0, min(len(tids), 50), 50):
                    batch = tids[batch_start:batch_start + 50]
                    title_params = {
                        "Command": "TitleLookup",
                        "TID": ",".join(batch),
                    }
                    async with session.get(syoboi_url, params=title_params) as r:
                        if r.status == 200:
                            t_text = await r.text(encoding="utf-8", errors="replace")
                            t_root = ET.fromstring(t_text)
                            for title_item in t_root.findall(".//TitleItem"):
                                tid = title_item.findtext("TID")
                                title = title_item.findtext("Title") or "不明"
                                if tid:
                                    tid_to_title[tid] = title

            # ── Step 3: 結果表示 ──
            print(f"\n  📡 本日の放送番組（最初の10件）:\n")

            for i, prog in enumerate(prog_items[:10], 1):
                tid = prog.findtext("TID") or ""
                title = tid_to_title.get(tid, f"TID:{tid}")
                ch_id = prog.findtext("ChID") or "?"
                start_time = prog.findtext("StTime") or ""
                sub_title = prog.findtext("SubTitle") or ""
                count = prog.findtext("Count") or ""

                # 時刻フォーマット変換 ("YYYY-MM-DD HH:MM:SS" → "HH:MM")
                time_str = ""
                if start_time and len(start_time) >= 16:
                    time_str = start_time[11:16]

                ep_str = f" 第{count}話" if count else ""
                sub_str = f" 「{sub_title}」" if sub_title else ""

                print(f"  {i:2d}. {time_str} 【{title}】{ep_str}{sub_str}")
                result["sample_titles"].append({
                    "tid": tid,
                    "title": title,
                    "ch_id": ch_id,
                })
                print()

            result["success"] = True

    except ET.ParseError as e:
        print_ng("XMLパースエラー", f"{e}")
        result["error"] = str(e)
    except Exception as e:
        print_ng("エラー", str(e))
        result["error"] = str(e)

    return result


# ─────────────────────────────────────────────────
# 3. dアニメストア RSS テスト
# ─────────────────────────────────────────────────

async def test_danime_via_anilist() -> dict:
    """dアニメストア配信作品をAniList streamingEpisodesから取得

    Note: dアニメストアの公式RSSは2024年にサービス終了。
    仕様書の代替手段として、AniList の streamingEpisodes フィールドを使用。
    """
    print_section("dアニメストア配信作品テスト (AniList経由)")
    print_info(
        "dアニメストアRSSは廃止済み",
        "代替: AniList streamingEpisodes から dAnime Store の情報を取得"
    )

    result = {
        "success": False,
        "item_count": 0,
        "sample_titles": [],
        "error": None,
    }

    # AniList で配信プラットフォーム情報を含む今期アニメを取得
    query = """
    query ($season: MediaSeason, $year: Int) {
      Page(perPage: 50) {
        media(
          season: $season
          seasonYear: $year
          type: ANIME
          status_in: [RELEASING, FINISHED]
          sort: POPULARITY_DESC
        ) {
          id
          title { native romaji }
          streamingEpisodes {
            title
            site
            url
          }
          externalLinks {
            site
            url
            type
          }
        }
      }
    }
    """

    now = datetime.now()
    month = now.month
    year = now.year
    season = "WINTER" if month in [12, 1, 2] else \
             "SPRING" if month in [3, 4, 5] else \
             "SUMMER" if month in [6, 7, 8] else "FALL"

    try:
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "https://graphql.anilist.co",
                json={"query": query, "variables": {"season": season, "year": year}},
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status != 200:
                    result["error"] = f"HTTP {response.status}"
                    print_ng("API接続エラー", f"HTTP {response.status}")
                    return result
                data = await response.json()

    except Exception as e:
        print_ng("接続エラー", str(e))
        result["error"] = str(e)
        return result

    media_list = data.get("data", {}).get("Page", {}).get("media", [])

    # dAnime Store 配信作品を抽出
    danime_keywords = ["d Anime Store", "dAnime", "dアニメ", "D-Anime"]
    danime_works = []

    for anime in media_list:
        title = anime.get("title", {}).get("native") or anime.get("title", {}).get("romaji", "")

        # streamingEpisodes でdAnimeを検索
        for ep in anime.get("streamingEpisodes", []):
            site = ep.get("site", "")
            if any(kw.lower() in site.lower() for kw in danime_keywords):
                danime_works.append({
                    "title": title,
                    "site": site,
                    "url": ep.get("url", ""),
                })
                break

        # externalLinks でも検索
        for link in anime.get("externalLinks", []):
            site = link.get("site", "")
            url = link.get("url", "")
            if any(kw.lower() in site.lower() for kw in danime_keywords):
                if not any(w["title"] == title for w in danime_works):
                    danime_works.append({
                        "title": title,
                        "site": site,
                        "url": url,
                    })
                break

    result["item_count"] = len(danime_works)
    result["success"] = True

    if danime_works:
        print_ok(f"dAnime配信作品検出", f"{len(danime_works)}件")
        print("\n  📺 dアニメストア配信作品（AniList経由）:\n")
        for i, work in enumerate(danime_works[:10], 1):
            print(f"  {i:2d}. {work['title']}")
            print(f"       プラットフォーム: {work['site']}")
            print()
        result["sample_titles"] = danime_works
    else:
        print_info(
            "dAnime配信作品は検出されませんでした",
            "AniListのstreamingEpisodesにdAnime情報が含まれていない可能性があります\n"
            "Crunchyroll等の主要プラットフォームは検出できています"
        )
        # 検出されたプラットフォームを表示
        all_sites = set()
        for anime in media_list:
            for ep in anime.get("streamingEpisodes", []):
                site = ep.get("site", "")
                if site:
                    all_sites.add(site)
        if all_sites:
            print_info("検出されたプラットフォーム", ", ".join(sorted(all_sites)))

    return result


# ─────────────────────────────────────────────────
# 4. DB保存テスト
# ─────────────────────────────────────────────────

async def test_db_save(anilist_result: dict) -> bool:
    """AniListデータをDBに保存テスト"""
    print_section("データベース保存テスト")

    if not anilist_result.get("success") or not anilist_result.get("sample_titles"):
        print_info("保存データなし（AniListテストをスキップ）")
        return False

    try:
        from modules.db import get_db
        db = get_db()

        saved_count = 0
        for anime in anilist_result["sample_titles"][:3]:
            title = anime.get("native") or anime.get("romaji") or "Unknown"
            # works テーブルに保存
            work_id = db.save_work({
                "title": title,
                "type": "anime",
                "source": "anilist",
            })
            if work_id:
                saved_count += 1

        print_ok(f"DB保存成功", f"{saved_count}件保存しました")
        return True

    except Exception as e:
        print_ng("DB保存エラー", str(e))
        return False


# ─────────────────────────────────────────────────
# メイン
# ─────────────────────────────────────────────────

async def main_async(args):
    results = {}

    print("\n" + "=" * 60)
    print("  Phase 2: アニメ情報収集 API テスト")
    print(f"  実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if args.anilist or args.all:
        results["anilist"] = await test_anilist_direct()

    if args.syoboi or args.all:
        results["syoboi"] = await test_syoboi_api()

    if args.danime or args.all:
        results["danime"] = await test_danime_via_anilist()

    if args.save and "anilist" in results:
        results["db"] = await test_db_save(results["anilist"])

    # サマリー表示
    print_section("結果サマリー")
    icons = {True: "✅", False: "❌"}

    if "anilist" in results:
        r = results["anilist"]
        status = icons[r["success"]]
        count = r.get("anime_count", 0)
        print(f"  AniList API:          {status} ({count}作品取得)")
        if r.get("streaming_platforms"):
            platforms = sorted(r["streaming_platforms"])
            print(f"    検出プラットフォーム: {', '.join(platforms)}")
        if r.get("error"):
            print(f"    エラー: {r['error']}")

    if "syoboi" in results:
        r = results["syoboi"]
        status = icons[r["success"]]
        count = r.get("program_count", 0)
        print(f"  しょぼいカレンダー:    {status} ({count}番組取得)")
        if r.get("error"):
            print(f"    エラー: {r['error']}")

    if "danime" in results:
        r = results["danime"]
        status = icons[r["success"]]
        count = r.get("item_count", 0)
        print(f"  dアニメ(AniList経由): {status} ({count}件検出)")
        if r.get("error"):
            print(f"    エラー: {r['error']}")

    if "db" in results:
        print(f"  DB保存テスト:         {icons[results['db']]}")

    # 次のステップ
    all_ok = all(r.get("success", False) for r in results.values() if isinstance(r, dict))
    print()
    if all_ok:
        print("  🎉 Phase 2 完了！次は Phase 3: Gmail API HTMLメール送信")
    else:
        failed = [k for k, v in results.items() if isinstance(v, dict) and not v.get("success")]
        print(f"  ⚠️  失敗したAPI: {', '.join(failed)}")
        print("  ネットワーク接続を確認してください")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Phase 2: アニメ情報収集 API テスト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--anilist", action="store_true", help="AniList GraphQL API テスト")
    parser.add_argument("--syoboi", action="store_true", help="しょぼいカレンダー API テスト")
    parser.add_argument("--danime", action="store_true", help="dアニメストア RSS テスト")
    parser.add_argument("--save", action="store_true", help="取得データをDBに保存")
    parser.add_argument("--all", action="store_true", help="すべてのAPIをテスト")

    args = parser.parse_args()

    # デフォルト: --all
    if not any(vars(args).values()):
        args.all = True

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
