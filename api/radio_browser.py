# api/radio_browser.py
"""
Radio Browser API integration for discovering thousands of radio stations.
Based on the Community Radio Browser project: https://www.radio-browser.info/
"""
import aiohttp
import asyncio
import logging
from typing import List, Dict, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

class RadioBrowserAPI:
    """Interface with the Radio Browser API to discover radio stations worldwide."""
    
    def __init__(self):
        self.base_url = "https://de1.api.radio-browser.info/json"  # German server
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_stations(self, 
                            name: Optional[str] = None,
                            country: Optional[str] = None,
                            language: Optional[str] = None,
                            tag: Optional[str] = None,
                            limit: int = 50) -> List[Dict]:
        """
        Search for radio stations with various filters.
        
        Args:
            name: Station name (partial match)
            country: Country code (e.g., 'US', 'FR', 'TW')
            language: Language code (e.g., 'english', 'french', 'chinese')
            tag: Tag filter (e.g., 'news', 'music', 'talk')
            limit: Maximum number of results
            
        Returns:
            List of station dictionaries with metadata
        """
        if not self.session:
            raise RuntimeError("RadioBrowserAPI must be used as async context manager")
            
        params = {
            'limit': limit,
            'hidebroken': 'true',
            'order': 'clickcount',  # Order by popularity
            'reverse': 'true'
        }
        
        # Build search parameters
        if name:
            params['name'] = name
        if country:
            params['country'] = country
        if language:
            params['language'] = language
        if tag:
            params['tag'] = tag
            
        try:
            url = f"{self.base_url}/stations/search"
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with self.session.get(url, params=params, timeout=timeout) as response:
                if response.status == 200:
                    stations = await response.json()
                    return self._process_stations(stations)
                else:
                    logger.warning(f"Radio Browser API returned status {response.status}")
                    return []
                    
        except asyncio.TimeoutError:
            logger.warning("Radio Browser API request timed out")
            return []
        except Exception as e:
            logger.error(f"Error searching stations: {e}")
            return []
    
    async def get_popular_stations(self, limit: int = 100) -> List[Dict]:
        """Get the most popular stations globally."""
        try:
            url = f"{self.base_url}/stations/topclick/{limit}"
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with self.session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    stations = await response.json()
                    return self._process_stations(stations)
                else:
                    logger.warning(f"Radio Browser API returned status {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting popular stations: {e}")
            return []
    
    async def get_stations_by_country(self, country_code: str, limit: int = 50) -> List[Dict]:
        """Get stations for a specific country."""
        return await self.search_stations(country=country_code, limit=limit)
    
    async def get_news_stations(self, country: Optional[str] = None, limit: int = 30) -> List[Dict]:
        """Get news/talk radio stations."""
        return await self.search_stations(tag="news", country=country, limit=limit)
    
    def _process_stations(self, stations: List[Dict]) -> List[Dict]:
        """Process and clean station data from Radio Browser API."""
        processed = []
        
        for station in stations:
            # Skip stations without streaming URL
            if not station.get('url_resolved') or not station.get('name'):
                continue
                
            # Determine language for ASR
            detected_language = self._detect_language(station)
            
            # Import here to avoid circular dependency
            from config import get_asr_language
            asr_language, is_fallback = get_asr_language(detected_language)
            
            processed_station = {
                'name': station.get('name') or 'Unknown Station',
                'url': station.get('url_resolved') or station.get('url') or '',
                'homepage': station.get('homepage') or '',
                'favicon': station.get('favicon') or '',
                'country': station.get('country') or '',
                'detected_language': detected_language,
                'asr_language': asr_language,
                'is_fallback': is_fallback,
                'tags': station.get('tags') or '',
                'bitrate': station.get('bitrate') or 0,
                'votes': station.get('votes') or 0
            }
            
            processed.append(processed_station)
            
        return processed
    
    def _detect_language(self, station: Dict) -> str:
        """
        Detect the language based on station metadata.
        
        Returns:
            Language code (e.g., 'en', 'fr', 'zh', 'es', 'de', etc.)
        """
        # Safe extraction with None protection
        country = (station.get('country') or '').upper()
        language = (station.get('language') or '').lower()
        tags = (station.get('tags') or '').lower()
        name = (station.get('name') or '').lower()
        
        # Language detection by country code
        country_language_map = {
            # Chinese variants
            'CN': 'zh', 'TW': 'zh', 'HK': 'zh', 'SG': 'zh',
            
            # French
            'FR': 'fr', 'BE': 'fr', 'CH': 'fr', 'CA': 'fr', 'LU': 'fr', 'MC': 'fr',
            
            # Spanish
            'ES': 'es', 'MX': 'es', 'AR': 'es', 'CO': 'es', 'PE': 'es', 'VE': 'es',
            'CL': 'es', 'EC': 'es', 'GT': 'es', 'CU': 'es', 'BO': 'es', 'DO': 'es',
            'HN': 'es', 'PY': 'es', 'SV': 'es', 'NI': 'es', 'CR': 'es', 'PA': 'es',
            'UY': 'es', 'PR': 'es',
            
            # German
            'DE': 'de', 'AT': 'de',
            
            # Italian
            'IT': 'it',
            
            # Portuguese
            'BR': 'pt', 'PT': 'pt',
            
            # Japanese
            'JP': 'ja',
            
            # Korean
            'KR': 'ko',
            
            # Other languages
            'RU': 'ru', 'PL': 'pl', 'NL': 'nl', 'SE': 'sv', 'NO': 'no',
            'DK': 'da', 'FI': 'fi', 'HU': 'hu', 'CZ': 'cs', 'SK': 'sk',
            'TR': 'tr', 'AR': 'ar', 'TH': 'th', 'VN': 'vi',
        }
        
        # Check country-based detection first
        if country in country_language_map:
            detected = country_language_map[country]
            # Verify with language field if available
            if language and detected[:2] in language:
                return detected
            # If no language confirmation, still use country-based detection
            return detected
        
        # Language keyword detection
        language_keywords = {
            'zh': ['chinese', 'mandarin', 'cantonese', '中文', '普通话', '粤语', 'taiwan', 'hong kong'],
            'fr': ['french', 'français', 'francais', 'france'],
            'es': ['spanish', 'español', 'espanol', 'castilian', 'latino', 'hispanic'],
            'de': ['german', 'deutsch', 'deutschland'],
            'it': ['italian', 'italiano', 'italia'],
            'pt': ['portuguese', 'português', 'portugues', 'brasil', 'portugal'],
            'ja': ['japanese', '日本語', 'nihongo', 'japan'],
            'ko': ['korean', '한국어', 'hangul', 'korea'],
            'ru': ['russian', 'русский', 'russia'],
            'ar': ['arabic', 'العربية', 'عربي'],
            'nl': ['dutch', 'nederlands', 'holland'],
            'sv': ['swedish', 'svenska', 'sweden'],
            'no': ['norwegian', 'norsk', 'norway'],
            'da': ['danish', 'dansk', 'denmark'],
            'pl': ['polish', 'polski', 'poland'],
            'tr': ['turkish', 'türkçe', 'turkey'],
            'th': ['thai', 'ไทย', 'thailand'],
            'vi': ['vietnamese', 'tiếng việt', 'vietnam'],
        }
        
        # Check language keywords in all metadata fields
        for lang_code, keywords in language_keywords.items():
            if any(keyword in language for keyword in keywords) or \
               any(keyword in tags for keyword in keywords) or \
               any(keyword in name for keyword in keywords):
                return lang_code
        
        # Default to English if no specific language detected
        return 'en'

# Utility functions for integration
async def discover_stations(search_query: str = "", 
                          country: str = "", 
                          language: str = "", 
                          category: str = "popular") -> List[Dict]:
    """
    Main function to discover radio stations.
    
    Args:
        search_query: Station name search
        country: Country filter (US, FR, TW, etc.)
        language: Language filter  
        category: 'popular', 'news', 'music', etc.
    
    Returns:
        List of station dictionaries
    """
    async with RadioBrowserAPI() as api:
        # If a search query is provided, use it regardless of category
        if search_query:
            return await api.search_stations(
                name=search_query,
                country=country,
                language=language,
                limit=50
            )

        # Otherwise, respect category and country filters
        if category == "popular":
            return await api.get_popular_stations(limit=100)
        if category == "news":
            return await api.get_news_stations(country=country, limit=50)
        if country:
            return await api.get_stations_by_country(country, limit=50)

        # Fallback to popular stations
        return await api.get_popular_stations(limit=50)