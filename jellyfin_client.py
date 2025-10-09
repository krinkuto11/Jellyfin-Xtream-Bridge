"""
Jellyfin API Client for accessing Movies and TV Series.
This client focuses on Movies and Series, ignoring Live TV functionality.
"""
import requests
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class JellyfinClient:
    """Client for interacting with Jellyfin API"""

    def __init__(self, server_url: str, api_key: str):
        """
        Initialize Jellyfin client.
        
        Parameters:
        server_url (str): The Jellyfin server URL
        api_key (str): The Jellyfin API key for authentication
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'X-Emby-Token': api_key,
            'Accept': 'application/json'
        })

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Make a request to the Jellyfin API.
        
        Parameters:
        endpoint (str): API endpoint path
        params (dict): Query parameters
        
        Returns:
        Any: JSON response data
        """
        url = f"{self.server_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Jellyfin API request failed: {str(e)}")
            raise

    def get_users(self) -> List[Dict[str, Any]]:
        """
        Get all users from Jellyfin.
        
        Returns:
        List[Dict]: List of user objects
        """
        return self._make_request('Users')

    def get_items(
        self,
        user_id: str,
        include_item_types: Optional[str] = None,
        parent_id: Optional[str] = None,
        recursive: bool = True,
        fields: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get items from Jellyfin library.
        
        Parameters:
        user_id (str): User ID
        include_item_types (str): Comma-separated list of item types
        parent_id (str): Parent folder ID
        recursive (bool): Include child items
        fields (str): Additional fields to include
        
        Returns:
        Dict: Response containing items
        """
        params = {
            'UserId': user_id,
            'Recursive': str(recursive).lower(),
        }
        if include_item_types:
            params['IncludeItemTypes'] = include_item_types
        if parent_id:
            params['ParentId'] = parent_id
        if fields:
            params['Fields'] = fields

        return self._make_request('Items', params)

    def get_movie_libraries(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all movie libraries/collections.
        
        Parameters:
        user_id (str): User ID
        
        Returns:
        List[Dict]: List of movie library folders
        """
        params = {
            'UserId': user_id,
            'IncludeItemTypes': 'CollectionFolder'
        }
        response = self._make_request('Items', params)
        movies = [
            item for item in response.get('Items', [])
            if item.get('CollectionType') == 'movies'
        ]
        return movies

    def get_series_libraries(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all series/TV show libraries.
        
        Parameters:
        user_id (str): User ID
        
        Returns:
        List[Dict]: List of series library folders
        """
        params = {
            'UserId': user_id,
            'IncludeItemTypes': 'CollectionFolder'
        }
        response = self._make_request('Items', params)
        series = [
            item for item in response.get('Items', [])
            if item.get('CollectionType') == 'tvshows'
        ]
        return series

    def get_movies(
        self,
        user_id: str,
        parent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all movies.
        
        Parameters:
        user_id (str): User ID
        parent_id (str): Parent folder ID to filter by
        
        Returns:
        List[Dict]: List of movie items
        """
        params = {
            'UserId': user_id,
            'IncludeItemTypes': 'Movie',
            'Recursive': 'true',
            'Fields': (
                'Path,MediaSources,ProviderIds,Overview,Genres,'
                'ProductionYear,PremiereDate,CommunityRating,OfficialRating'
            )
        }
        if parent_id:
            params['ParentId'] = parent_id

        response = self._make_request('Items', params)
        return response.get('Items', [])

    def get_series(
        self,
        user_id: str,
        parent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all TV series.
        
        Parameters:
        user_id (str): User ID
        parent_id (str): Parent folder ID to filter by
        
        Returns:
        List[Dict]: List of series items
        """
        params = {
            'UserId': user_id,
            'IncludeItemTypes': 'Series',
            'Recursive': 'true',
            'Fields': (
                'Path,ProviderIds,Overview,Genres,ProductionYear,'
                'PremiereDate,CommunityRating,OfficialRating'
            )
        }
        if parent_id:
            params['ParentId'] = parent_id

        response = self._make_request('Items', params)
        return response.get('Items', [])

    def get_series_info(
        self,
        user_id: str,
        series_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed information about a series including seasons/episodes.
        
        Parameters:
        user_id (str): User ID
        series_id (str): Series ID
        
        Returns:
        Dict: Series information with episodes
        """
        # Get series details
        series = self._make_request(f'Users/{user_id}/Items/{series_id}')
        
        # Get seasons
        seasons_response = self._make_request(
            f'Shows/{series_id}/Seasons',
            {'UserId': user_id, 'Fields': 'Overview'}
        )
        seasons = seasons_response.get('Items', [])
        
        # Get episodes for each season
        episodes_by_season = {}
        for season in seasons:
            season_id = season.get('Id')
            episodes_response = self._make_request(
                f'Shows/{series_id}/Episodes',
                {
                    'UserId': user_id,
                    'SeasonId': season_id,
                    'Fields': (
                        'Path,MediaSources,Overview,ProductionYear,'
                        'PremiereDate'
                    )
                }
            )
            season_number = season.get('IndexNumber', 0)
            episodes_by_season[str(season_number)] = (
                episodes_response.get('Items', [])
            )
        
        return {
            'info': series,
            'seasons': seasons,
            'episodes': episodes_by_season
        }

    def get_item_details(
        self,
        user_id: str,
        item_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific item.
        
        Parameters:
        user_id (str): User ID
        item_id (str): Item ID
        
        Returns:
        Dict: Item details
        """
        return self._make_request(f'Users/{user_id}/Items/{item_id}')

    def get_stream_url(
        self,
        item_id: str,
        container: str = 'mp4'
    ) -> str:
        """
        Get the stream URL for a media item.
        
        Parameters:
        item_id (str): Item ID
        container (str): Container format
        
        Returns:
        str: Stream URL
        """
        return (
            f"{self.server_url}/Videos/{item_id}/stream.{container}"
            f"?api_key={self.api_key}&Static=true"
        )

    def close(self):
        """Close the session and cleanup resources"""
        if hasattr(self, 'session') and self.session:
            try:
                self.session.close()
            except Exception as e:
                logger.debug(f"Error closing Jellyfin session: {e}")

    def __enter__(self):
        """Enter the context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and cleanup resources"""
        self.close()
        return False

    def __del__(self):
        """Ensure session is closed when object is destroyed"""
        self.close()
