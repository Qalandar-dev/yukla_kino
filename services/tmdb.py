import httpx
import logging
from typing import Optional, Dict
from config import Config

logger = logging.getLogger(__name__)


class TMDBService:
    BASE_URL = "https://api.themoviedb.org/3"
    
    def __init__(self):
        self.api_key = Config.TMDB_API_KEY
    
    async def search_movie(self, query: str) -> Optional[Dict]:
        """Kino nomi bo'yicha qidirish"""
        if not self.api_key:
            logger.warning("TMDB API key not configured")
            return None
        
        url = f"{self.BASE_URL}/search/movie"
        params = {
            "api_key": self.api_key,
            "query": query,
            "language": "uz-UZ"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("results"):
                        return data["results"][0]  # Birinchi natijani qaytarish
        except Exception as e:
            logger.error(f"TMDB search error: {e}")
        
        return None
    
    async def get_movie_details(self, tmdb_id: int) -> Optional[Dict]:
        """Kino tafsilotlarini olish"""
        if not self.api_key:
            return None
        
        url = f"{self.BASE_URL}/movie/{tmdb_id}"
        params = {
            "api_key": self.api_key,
            "language": "uz-UZ"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"TMDB details error: {e}")
        
        return None
    
    def format_movie_data(self, tmdb_data: Dict) -> Dict:
        """TMDB ma'lumotlarini biz formatiga o'tkazish"""
        if not tmdb_data:
            return {}
        
        genres = ", ".join([g["name"] for g in tmdb_data.get("genres", [])])
        countries = ", ".join([c["name"] for c in tmdb_data.get("production_countries", [])])
        
        return {
            "poster_url": f"https://image.tmdb.org/t/p/w500{tmdb_data.get('poster_path')}" if tmdb_data.get("poster_path") else None,
            "year": tmdb_data.get("release_date", "")[:4] if tmdb_data.get("release_date") else None,
            "genre": genres,
            "duration": tmdb_data.get("runtime"),
            "description": tmdb_data.get("overview"),
            "country": countries,
            "language": tmdb_data.get("original_language")
        }
    
    async def get_movie_info_by_name(self, title: str) -> Dict:
        """Kino nomi bo'yicha to'liq ma'lumot olish"""
        search_result = await self.search_movie(title)
        if not search_result:
            return {}
        
        tmdb_id = search_result.get("id")
        if not tmdb_id:
            return {}
        
        details = await self.get_movie_details(tmdb_id)
        if not details:
            return {}
        
        return self.format_movie_data(details)


# Global instance
tmdb_service = TMDBService()
