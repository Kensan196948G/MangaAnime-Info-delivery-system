"""
AniList GraphQL API連携モジュール（型ヒント付き）
"""
import requests
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

ANILIST_API_URL = "https://graphql.anilist.co"
RATE_LIMIT_PER_MINUTE = 90


class AniListAPI:
    """AniList API クライアント"""

    def __init__(self, rate_limit: int = RATE_LIMIT_PER_MINUTE) -> None:
        """
        初期化

        Args:
            rate_limit: 1分あたりのリクエスト制限数
        """
        self.api_url = ANILIST_API_URL
        self.rate_limit = rate_limit
        self.request_count = 0
        self.last_reset_time = time.time()

    def _check_rate_limit(self) -> None:
        """レート制限をチェック"""
        current_time = time.time()
        elapsed = current_time - self.last_reset_time

        # 1分経過したらリセット
        if elapsed >= 60:
            self.request_count = 0
            self.last_reset_time = current_time

        # レート制限に達している場合は待機
        if self.request_count >= self.rate_limit:
            wait_time = 60 - elapsed
            if wait_time > 0:
                logger.warning(f"レート制限に達しました。{wait_time:.1f}秒待機します")
                time.sleep(wait_time)
                self.request_count = 0
                self.last_reset_time = time.time()

    def _execute_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        GraphQLクエリを実行

        Args:
            query: GraphQLクエリ文字列
            variables: クエリ変数

        Returns:
            Optional[Dict[str, Any]]: レスポンスデータ（エラー時はNone）
        """
        self._check_rate_limit()

        try:
            response = requests.post(
                self.api_url,
                json={'query': query, 'variables': variables or {}},
                timeout=30
            )
            response.raise_for_status()

            self.request_count += 1

            data: Dict[str, Any] = response.json()

            if 'errors' in data:
                logger.error(f"GraphQLエラー: {data['errors']}")
                return None

            return data.get('data')

        except requests.exceptions.RequestException as e:
            logger.error(f"APIリクエストエラー: {e}")
            return None

    def get_upcoming_anime(
        self,
        page: int = 1,
        per_page: int = 50,
        season: Optional[str] = None,
        year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        放送予定のアニメを取得

        Args:
            page: ページ番号
            per_page: 1ページあたりの件数
            season: シーズン（WINTER, SPRING, SUMMER, FALL）
            year: 年

        Returns:
            List[Dict[str, Any]]: アニメ情報のリスト
        """
        query = """
        query ($page: Int, $perPage: Int, $season: MediaSeason, $seasonYear: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    total
                    currentPage
                    lastPage
                    hasNextPage
                }
                media(
                    type: ANIME,
                    season: $season,
                    seasonYear: $seasonYear,
                    status_in: [RELEASING, NOT_YET_RELEASED],
                    sort: START_DATE
                ) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    startDate {
                        year
                        month
                        day
                    }
                    episodes
                    status
                    genres
                    tags {
                        name
                        rank
                    }
                    description
                    siteUrl
                    streamingEpisodes {
                        title
                        thumbnail
                        url
                        site
                    }
                }
            }
        }
        """

        variables: Dict[str, Any] = {
            'page': page,
            'perPage': per_page
        }

        if season:
            variables['season'] = season

        if year:
            variables['seasonYear'] = year

        data = self._execute_query(query, variables)

        if not data or 'Page' not in data:
            return []

        media_list: List[Dict[str, Any]] = data['Page'].get('media', [])
        logger.info(f"取得件数: {len(media_list)}件")

        return media_list

    def get_anime_by_id(self, anime_id: int) -> Optional[Dict[str, Any]]:
        """
        IDでアニメ情報を取得

        Args:
            anime_id: アニメID

        Returns:
            Optional[Dict[str, Any]]: アニメ情報（存在しない場合はNone）
        """
        query = """
        query ($id: Int) {
            Media(id: $id, type: ANIME) {
                id
                title {
                    romaji
                    english
                    native
                }
                startDate {
                    year
                    month
                    day
                }
                episodes
                status
                genres
                tags {
                    name
                    rank
                }
                description
                siteUrl
                streamingEpisodes {
                    title
                    thumbnail
                    url
                    site
                }
            }
        }
        """

        variables = {'id': anime_id}
        data = self._execute_query(query, variables)

        if not data:
            return None

        return data.get('Media')

    def search_anime(
        self,
        search_term: str,
        page: int = 1,
        per_page: int = 10
    ) -> List[Dict[str, Any]]:
        """
        アニメを検索

        Args:
            search_term: 検索キーワード
            page: ページ番号
            per_page: 1ページあたりの件数

        Returns:
            List[Dict[str, Any]]: アニメ情報のリスト
        """
        query = """
        query ($search: String, $page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                media(search: $search, type: ANIME) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    startDate {
                        year
                        month
                        day
                    }
                    episodes
                    status
                    genres
                    description
                    siteUrl
                }
            }
        }
        """

        variables = {
            'search': search_term,
            'page': page,
            'perPage': per_page
        }

        data = self._execute_query(query, variables)

        if not data or 'Page' not in data:
            return []

        media_list: List[Dict[str, Any]] = data['Page'].get('media', [])
        logger.info(f"検索結果: {len(media_list)}件")

        return media_list


def extract_title(media: Dict[str, Any]) -> str:
    """
    メディア情報からタイトルを抽出

    Args:
        media: メディア情報

    Returns:
        str: タイトル（優先順: native -> romaji -> english）
    """
    title_obj = media.get('title', {})

    return (
        title_obj.get('native') or
        title_obj.get('romaji') or
        title_obj.get('english') or
        '不明'
    )


def extract_start_date(media: Dict[str, Any]) -> Optional[str]:
    """
    メディア情報から開始日を抽出

    Args:
        media: メディア情報

    Returns:
        Optional[str]: 開始日（YYYY-MM-DD形式、不明な場合はNone）
    """
    start_date = media.get('startDate', {})

    year = start_date.get('year')
    month = start_date.get('month')
    day = start_date.get('day')

    if not year:
        return None

    # 月・日が不明な場合はデフォルト値を使用
    month = month or 1
    day = day or 1

    try:
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        # 日付の妥当性チェック
        datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except ValueError:
        return None


def extract_streaming_platforms(media: Dict[str, Any]) -> List[str]:
    """
    メディア情報から配信プラットフォームを抽出

    Args:
        media: メディア情報

    Returns:
        List[str]: 配信プラットフォームのリスト
    """
    streaming_episodes = media.get('streamingEpisodes', [])
    platforms: List[str] = []

    for episode in streaming_episodes:
        site = episode.get('site')
        if site and site not in platforms:
            platforms.append(site)

    return platforms


def check_ng_keywords(
    media: Dict[str, Any],
    ng_keywords: List[str]
) -> Tuple[bool, List[str]]:
    """
    NGキーワードをチェック

    Args:
        media: メディア情報
        ng_keywords: NGキーワードのリスト

    Returns:
        Tuple[bool, List[str]]: (NGキーワードが含まれるか, マッチしたキーワードのリスト)
    """
    matched_keywords: List[str] = []

    # タイトルをチェック
    title = extract_title(media)
    for keyword in ng_keywords:
        if keyword.lower() in title.lower():
            matched_keywords.append(keyword)

    # ジャンルをチェック
    genres = media.get('genres', [])
    for genre in genres:
        for keyword in ng_keywords:
            if keyword.lower() in str(genre).lower():
                matched_keywords.append(keyword)

    # タグをチェック
    tags = media.get('tags', [])
    for tag in tags:
        tag_name = tag.get('name', '')
        for keyword in ng_keywords:
            if keyword.lower() in tag_name.lower():
                matched_keywords.append(keyword)

    # 説明をチェック
    description = media.get('description', '')
    if description:
        for keyword in ng_keywords:
            if keyword.lower() in description.lower():
                matched_keywords.append(keyword)

    # 重複を削除
    matched_keywords = list(set(matched_keywords))

    return len(matched_keywords) > 0, matched_keywords


def get_current_season() -> Tuple[str, int]:
    """
    現在のシーズンを取得

    Returns:
        Tuple[str, int]: (シーズン名, 年)
    """
    now = datetime.now()
    month = now.month
    year = now.year

    if month in [1, 2, 3]:
        season = 'WINTER'
    elif month in [4, 5, 6]:
        season = 'SPRING'
    elif month in [7, 8, 9]:
        season = 'SUMMER'
    else:  # month in [10, 11, 12]
        season = 'FALL'

    return season, year


def get_next_season() -> Tuple[str, int]:
    """
    次のシーズンを取得

    Returns:
        Tuple[str, int]: (シーズン名, 年)
    """
    now = datetime.now()
    month = now.month
    year = now.year

    if month in [1, 2, 3]:
        season = 'SPRING'
    elif month in [4, 5, 6]:
        season = 'SUMMER'
    elif month in [7, 8, 9]:
        season = 'FALL'
    else:  # month in [10, 11, 12]
        season = 'WINTER'
        year += 1

    return season, year
