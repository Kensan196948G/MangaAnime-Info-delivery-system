#!/usr/bin/env python3
"""
Phase 3: Gmail SMTP HTMLメール通知テスト

AniList APIで取得した実データをHTMLメールとして送信するエンドツーエンドテスト。

使用方法:
    python -X utf8 scripts/test_phase3_email.py --preview    # HTML内容を確認（送信しない）
    python -X utf8 scripts/test_phase3_email.py --send       # 実際にメール送信
    python -X utf8 scripts/test_phase3_email.py --test-data  # サンプルデータで確認
"""

import argparse
import asyncio
import io
import sys
from datetime import datetime
from pathlib import Path

# Windows UTF-8強制
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def print_section(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


# ─────────────────────────────────────────────────
# 1. AniListからリリースデータを収集
# ─────────────────────────────────────────────────

async def collect_anime_for_notification() -> list:
    """AniList APIから本日配信予定のアニメを取得して通知用データに変換"""
    import aiohttp

    query = """
    query ($season: MediaSeason, $year: Int) {
      Page(perPage: 10) {
        media(
          season: $season
          seasonYear: $year
          type: ANIME
          status: RELEASING
          sort: POPULARITY_DESC
        ) {
          id
          title { native romaji english }
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
          coverImage { medium }
          siteUrl
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

    releases = []

    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "https://graphql.anilist.co",
                json={"query": query, "variables": {"season": season, "year": year}},
                headers={"Content-Type": "application/json"},
            ) as response:
                data = await response.json()

        media_list = data.get("data", {}).get("Page", {}).get("media", [])

        ng_keywords = ["エロ", "R18", "成人向け", "BL", "百合", "ボーイズラブ", "Hentai"]

        for anime in media_list:
            title_native = anime.get("title", {}).get("native") or \
                          anime.get("title", {}).get("romaji", "Unknown")
            title_romaji = anime.get("title", {}).get("romaji", "")
            title_en = anime.get("title", {}).get("english", "")

            # NGフィルタ
            combined = (title_native + title_romaji + title_en).lower()
            if any(kw.lower() in combined for kw in ng_keywords):
                continue

            # 次回放送エピソード情報
            next_ep = anime.get("nextAiringEpisode")
            if next_ep:
                airing_ts = next_ep.get("airingAt", 0)
                ep_num = next_ep.get("episode", "?")
                if airing_ts:
                    air_date = datetime.fromtimestamp(airing_ts).strftime("%Y-%m-%d %H:%M")
                else:
                    air_date = ""
            else:
                ep_num = "?"
                air_date = ""

            # 配信プラットフォーム
            platforms = list({
                ep.get("site", "")
                for ep in anime.get("streamingEpisodes", [])
                if ep.get("site")
            })
            platform = ", ".join(sorted(platforms)) if platforms else "Netflix/Amazon等"

            releases.append({
                "type": "anime",
                "title": title_native,
                "title_en": title_en,
                "number": str(ep_num),
                "platform": platform,
                "release_date": air_date,
                "source_url": anime.get("siteUrl", ""),
                "score": anime.get("averageScore") or 0,
                "genres": anime.get("genres", []),
            })

    except Exception as e:
        logger.warning(f"AniList API エラー: {e}")
        # フォールバック: サンプルデータ
        releases = get_sample_releases()

    return releases


def get_sample_releases() -> list:
    """テスト用サンプルリリースデータ"""
    return [
        {
            "type": "anime",
            "title": "呪術廻戦 死滅回游 前編",
            "title_en": "JUJUTSU KAISEN Season 3",
            "number": "8",
            "platform": "Crunchyroll",
            "release_date": "2026-02-27 00:26",
            "source_url": "https://anilist.co/anime/145064",
            "score": 84,
            "genres": ["Action", "Drama", "Supernatural"],
        },
        {
            "type": "anime",
            "title": "葬送のフリーレン 第2期",
            "title_en": "Frieren: Beyond Journey's End Season 2",
            "number": "6",
            "platform": "不明",
            "release_date": "2026-02-27 23:00",
            "source_url": "https://anilist.co/anime/154587",
            "score": 89,
            "genres": ["Adventure", "Drama", "Fantasy"],
        },
        {
            "type": "manga",
            "title": "進撃の巨人 コミックス",
            "number": "34",
            "platform": "BookWalker",
            "release_date": "2026-02-20",
            "source_url": "https://bookwalker.jp/",
            "score": 95,
            "genres": [],
        },
    ]


# ─────────────────────────────────────────────────
# 2. HTMLメール生成
# ─────────────────────────────────────────────────

def generate_html_notification(releases: list, date_str: str = None) -> str:
    """リリース情報からHTMLメールを生成"""
    if not date_str:
        date_str = datetime.now().strftime("%Y年%m月%d日")

    anime_releases = [r for r in releases if r.get("type") == "anime"]
    manga_releases = [r for r in releases if r.get("type") == "manga"]

    def gen_release_card(release: dict, card_class: str, badge_class: str) -> str:
        title = release.get("title", "不明")
        title_en = release.get("title_en", "")
        number = release.get("number", "")
        platform = release.get("platform", "")
        release_date = release.get("release_date", "")
        source_url = release.get("source_url", "")
        score = release.get("score", 0)
        genres = release.get("genres", [])
        is_anime = release.get("type") == "anime"

        ep_label = "話" if is_anime else "巻"
        ep_str = f"第{number}{ep_label}" if number and number != "?" else ""
        genres_str = ", ".join(genres[:3]) if genres else ""

        link_text = "詳細・視聴" if is_anime else "購入・詳細"

        card = f"""
        <div class="release-item {card_class}">
          <div class="release-title">{title}</div>
          {"<div class='release-sub'>" + title_en + "</div>" if title_en else ""}
          <div class="release-details">
            {f'<span class="badge {badge_class}">{ep_str}</span>' if ep_str else ""}
            {f'<span class="badge platform-badge">{platform}</span>' if platform else ""}
            {f'<div class="meta">📅 {release_date}</div>' if release_date else ""}
            {f'<div class="meta">🎭 {genres_str}</div>' if genres_str else ""}
            {f'<div class="meta">⭐ スコア: {score}/100</div>' if score else ""}
            {f'<div class="meta"><a href="{source_url}" class="release-link">{link_text} →</a></div>' if source_url else ""}
          </div>
        </div>"""
        return card

    anime_section = ""
    if anime_releases:
        cards = "".join(
            gen_release_card(r, "anime-card", "anime-badge")
            for r in anime_releases
        )
        anime_section = f"""
        <div class="section">
          <h2 class="section-title anime-title">📺 アニメ情報</h2>
          {cards}
        </div>"""

    manga_section = ""
    if manga_releases:
        cards = "".join(
            gen_release_card(r, "manga-card", "manga-badge")
            for r in manga_releases
        )
        manga_section = f"""
        <div class="section">
          <h2 class="section-title manga-title">📚 マンガ情報</h2>
          {cards}
        </div>"""

    total = len(releases)
    anime_count = len(anime_releases)
    manga_count = len(manga_releases)
    summary = f"アニメ{anime_count}件" if anime_count > 0 else ""
    if manga_count > 0:
        summary += ("・" if summary else "") + f"マンガ{manga_count}件"

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>アニメ・マンガ最新情報 - {date_str}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Hiragino Kaku Gothic ProN', Meiryo, sans-serif;
      background: #f0f2f5;
      color: #333;
      padding: 20px;
    }}
    .container {{
      max-width: 680px;
      margin: 0 auto;
      background: #fff;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }}
    .header {{
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      color: white;
      text-align: center;
      padding: 32px 24px;
    }}
    .header h1 {{ font-size: 24px; font-weight: bold; margin-bottom: 8px; }}
    .header .date {{ font-size: 14px; opacity: 0.8; }}
    .header .summary {{
      margin-top: 16px;
      background: rgba(255,255,255,0.15);
      border-radius: 20px;
      padding: 8px 20px;
      display: inline-block;
      font-size: 14px;
    }}
    .section {{ padding: 24px 24px 8px; }}
    .section-title {{
      font-size: 18px;
      font-weight: bold;
      margin-bottom: 16px;
      padding-bottom: 8px;
      border-bottom: 2px solid;
    }}
    .anime-title {{ color: #2ecc71; border-color: #2ecc71; }}
    .manga-title {{ color: #f39c12; border-color: #f39c12; }}
    .release-item {{
      border-radius: 10px;
      padding: 16px;
      margin-bottom: 14px;
      border-left: 4px solid;
    }}
    .anime-card {{ background: #f0fff4; border-color: #2ecc71; }}
    .manga-card {{ background: #fffbf0; border-color: #f39c12; }}
    .release-title {{ font-size: 16px; font-weight: bold; margin-bottom: 4px; }}
    .release-sub {{ font-size: 12px; color: #666; margin-bottom: 8px; }}
    .release-details {{ font-size: 13px; }}
    .badge {{
      display: inline-block;
      padding: 3px 10px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: bold;
      color: white;
      margin-right: 6px;
      margin-bottom: 6px;
    }}
    .anime-badge {{ background: #2ecc71; }}
    .manga-badge {{ background: #f39c12; }}
    .platform-badge {{ background: #3498db; }}
    .meta {{ margin-top: 4px; color: #666; font-size: 12px; }}
    .release-link {{
      color: #3498db;
      text-decoration: none;
      font-weight: bold;
    }}
    .footer {{
      text-align: center;
      padding: 20px;
      background: #f8f9fa;
      color: #999;
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🎬 アニメ・マンガ最新情報</h1>
      <div class="date">{date_str}</div>
      <div class="summary">本日の配信: {summary} ({total}件)</div>
    </div>
    {anime_section}
    {manga_section}
    <div class="footer">
      <p>📧 このメールは MangaAnime Info System が自動配信しています</p>
      <p style="margin-top: 4px;">© 2026 MangaAnime-Info-delivery-system</p>
    </div>
  </div>
</body>
</html>"""

    return html


def generate_text_notification(releases: list, date_str: str = None) -> str:
    """プレーンテキスト版メール本文生成"""
    if not date_str:
        date_str = datetime.now().strftime("%Y年%m月%d日")

    text = f"アニメ・マンガ最新情報 - {date_str}\n"
    text += "=" * 40 + "\n\n"

    anime_releases = [r for r in releases if r.get("type") == "anime"]
    manga_releases = [r for r in releases if r.get("type") == "manga"]

    if anime_releases:
        text += "📺 アニメ情報\n"
        text += "-" * 20 + "\n"
        for r in anime_releases:
            ep = r.get("number", "")
            ep_str = f" 第{ep}話" if ep and ep != "?" else ""
            text += f"• {r.get('title', '')}{ep_str}"
            platform = r.get("platform", "")
            if platform:
                text += f" ({platform})"
            release_date = r.get("release_date", "")
            if release_date:
                text += f"\n  配信: {release_date}"
            text += "\n"
        text += "\n"

    if manga_releases:
        text += "📚 マンガ情報\n"
        text += "-" * 20 + "\n"
        for r in manga_releases:
            vol = r.get("number", "")
            vol_str = f" 第{vol}巻" if vol else ""
            text += f"• {r.get('title', '')}{vol_str}"
            release_date = r.get("release_date", "")
            if release_date:
                text += f"\n  発売: {release_date}"
            text += "\n"
        text += "\n"

    text += "=" * 40 + "\n"
    text += "このメールは自動配信されています\n"
    return text


# ─────────────────────────────────────────────────
# 3. SMTP送信
# ─────────────────────────────────────────────────

def send_notification_email(releases: list) -> bool:
    """SMTPでHTMLメール通知を送信"""
    from modules.smtp_mailer import SMTPGmailSender

    sender = SMTPGmailSender()
    if not sender.validate_config():
        print("  ❌ SMTP設定が不完全です")
        return False

    date_str = datetime.now().strftime("%Y年%m月%d日")
    html_content = generate_html_notification(releases, date_str)
    text_content = generate_text_notification(releases, date_str)

    anime_count = len([r for r in releases if r.get("type") == "anime"])
    manga_count = len([r for r in releases if r.get("type") == "manga"])

    subject_parts = []
    if anime_count > 0:
        subject_parts.append(f"アニメ{anime_count}件")
    if manga_count > 0:
        subject_parts.append(f"マンガ{manga_count}件")
    subject_str = "・".join(subject_parts) or f"{len(releases)}件"
    subject = f"[アニメ・マンガ情報] {date_str} - {subject_str}の新着情報"

    success = sender.send_email(
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )

    return success


# ─────────────────────────────────────────────────
# メイン
# ─────────────────────────────────────────────────

async def main_async(args):
    print("\n" + "=" * 60)
    print("  Phase 3: Gmail SMTP HTMLメール通知テスト")
    print(f"  実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # データ取得
    if args.test_data:
        print_section("サンプルデータを使用")
        releases = get_sample_releases()
        print(f"  ℹ️  サンプルデータ: {len(releases)}件")
    else:
        print_section("AniList APIからデータ取得中")
        releases = await collect_anime_for_notification()
        print(f"  ✅ 取得完了: {len(releases)}件のリリース情報")

    for r in releases[:5]:
        type_label = "📺" if r["type"] == "anime" else "📚"
        num = r.get("number", "")
        ep_str = f" 第{num}{'話' if r['type'] == 'anime' else '巻'}" if num and num != "?" else ""
        print(f"  {type_label} {r['title']}{ep_str} - {r.get('release_date', '')}")

    # HTMLプレビュー
    if args.preview:
        print_section("HTML プレビュー生成")
        html = generate_html_notification(releases)
        preview_path = project_root / "logs" / "email_preview.html"
        preview_path.parent.mkdir(exist_ok=True)
        with open(str(preview_path), "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  ✅ HTMLを保存しました: {preview_path}")
        print(f"     ブラウザで開いて確認してください")
        print(f"     file://{preview_path}")

    # メール送信
    if args.send:
        print_section("HTMLメール送信")
        print(f"  🔄 送信中...")
        success = send_notification_email(releases)
        if success:
            print(f"  ✅ HTMLメール送信成功！")
            print(f"     受信ボックスを確認してください")
        else:
            print(f"  ❌ 送信失敗")
        return success

    if not args.preview and not args.send:
        print_section("次のステップ")
        print("  --preview  : HTML内容をブラウザで確認")
        print("  --send     : 実際にHTMLメールを送信")
        print("  --test-data: サンプルデータで確認")

    return True


def main():
    parser = argparse.ArgumentParser(description="Phase 3: HTMLメール通知テスト")
    parser.add_argument("--preview", action="store_true", help="HTML内容を logs/email_preview.html に保存")
    parser.add_argument("--send", action="store_true", help="HTMLメールを実際に送信")
    parser.add_argument("--test-data", action="store_true", help="サンプルデータを使用（API不要）")
    args = parser.parse_args()

    asyncio.run(main_async(args))


def print_section(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


if __name__ == "__main__":
    main()
