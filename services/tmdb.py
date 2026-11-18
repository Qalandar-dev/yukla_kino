import httpx
import logging
from typing import Optional, Dict
from config import Config

logger = logging.getLogger(__name__)


class TMDBService:
    BASE_URL = "https://api.themoviedb.org/3"
    TIMEOUT = 10

    def __init__(self):
        self.api_key = Config.TMDB_API_KEY

    async def _get(self, path: str, **params) -> Optional[Dict]:
        if not self.api_key:
            return None
        params["api_key"] = self.api_key
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(f"{self.BASE_URL}{path}", params=params)
                if response.status_code == 200:
                    return response.json()
                logger.warning(f"TMDB {path}: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"TMDB request error ({path}): {e}")
        return None

    async def search_movie(self, query: str) -> Optional[Dict]:
        """Kino nomi bo'yicha qidirish (birinchi natija)"""
        if not self.api_key:
            logger.warning("TMDB API key not configured")
            return None
        data = await self._get("/search/movie", query=query, language="en-US")
        if data and data.get("results"):
            return data["results"][0]
        return None

    async def get_movie_details(self, tmdb_id: int, language: str = "en-US") -> Optional[Dict]:
        return await self._get(f"/movie/{tmdb_id}", language=language)

    @staticmethod
    def format_movie_data(details: Dict, overview_uz: Optional[str] = None) -> Dict:
        """TMDB ma'lumotlarini bot formatiga o'tkazish.

        Janr va davlat nomlari inglizcha olinadi (janr filtrlari shunga mos),
        mazmun esa mavjud bo'lsa o'zbekcha.
        """
        if not details:
            return {}

        genres = ", ".join(g["name"] for g in details.get("genres", []))
        countries = ", ".join(c["name"] for c in details.get("production_countries", []))
        release = details.get("release_date") or ""
        year = int(release[:4]) if release[:4].isdigit() else None
        poster = details.get("poster_path")

        return {
            "poster_url": f"https://image.tmdb.org/t/p/w500{poster}" if poster else None,
            "year": year,
            "genre": genres or None,
            "duration": details.get("runtime") or None,
            "description": overview_uz or details.get("overview") or None,
            "country": countries or None,
            "language": details.get("original_language"),
        }

    async def get_movie_info_by_name(self, title: str) -> Dict:
        """Kino nomi bo'yicha to'liq ma'lumot olish"""
        search_result = await self.search_movie(title)
        if not search_result or not search_result.get("id"):
            return {}

        tmdb_id = search_result["id"]
        details = await self.get_movie_details(tmdb_id, "en-US")
        if not details:
            return {}

        details_uz = await self.get_movie_details(tmdb_id, "uz-UZ")
        overview_uz = details_uz.get("overview") if details_uz else None
        return self.format_movie_data(details, overview_uz)


tmdb_service = TMDBService()
