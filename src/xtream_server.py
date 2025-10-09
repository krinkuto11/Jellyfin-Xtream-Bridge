"""
Xtream Codes Server Implementation.
This server implements the Xtream Codes API and translates requests
to Jellyfin API calls for Movies and TV Series.
"""
import json
import logging
import os
import sys
from typing import Dict, List, Optional, Any
from flask import Flask, request, Response, jsonify, send_file

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jellyfin_client import JellyfinClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


class XtreamServer:
    """Xtream Codes API Server backed by Jellyfin"""

    def __init__(self, config_path: str = 'config/config.json'):
        """
        Initialize Xtream Server.
        
        Parameters:
        config_path (str): Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.jellyfin = JellyfinClient(
            self.config['jellyfin']['server_url'],
            self.config['jellyfin']['api_key']
        )
        self.users = self.config['xtream_server']['users']
        self.jellyfin_user_id = None
        self._init_jellyfin_user()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Parameters:
        config_path (str): Path to config file
        
        Returns:
        Dict: Configuration dictionary
        """
        # Try multiple possible config paths
        possible_paths = [
            config_path,
            os.path.join(os.path.dirname(__file__), '..', config_path),
            '/config/config.json'  # Docker volume mount
        ]
        
        config_found = None
        for path in possible_paths:
            if os.path.exists(path):
                config_found = path
                break
        
        if not config_found:
            raise FileNotFoundError(
                f"Config file not found. Tried: {possible_paths}. "
                f"Copy config/config.json.example to config/config.json and configure it."
            )
        
        config_path = config_found
        
        with open(config_path, 'r') as f:
            return json.load(f)

    def _init_jellyfin_user(self):
        """Initialize Jellyfin user ID (uses first user)"""
        try:
            users = self.jellyfin.get_users()
            if users:
                self.jellyfin_user_id = users[0]['Id']
                logger.info(
                    f"Using Jellyfin user: {users[0].get('Name')} "
                    f"({self.jellyfin_user_id})"
                )
            else:
                logger.error("No users found in Jellyfin")
        except Exception as e:
            logger.error(f"Failed to get Jellyfin users: {str(e)}")

    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate user against configured users.
        
        Parameters:
        username (str): Username
        password (str): Password
        
        Returns:
        bool: True if authenticated
        """
        return (
            username in self.users and
            self.users[username] == password
        )

    def get_server_info(self, username: str) -> Dict[str, Any]:
        """
        Get Xtream Codes server info response.
        
        Parameters:
        username (str): Authenticated username
        
        Returns:
        Dict: Server info in Xtream Codes format
        """
        from datetime import datetime
        import time

        return {
            'user_info': {
                'username': username,
                'password': self.users[username],
                'message': 'Welcome to Jellyfin Xtream Server',
                'auth': 1,
                'status': 'Active',
                'exp_date': '9999999999',
                'is_trial': '0',
                'active_cons': '0',
                'created_at': str(int(time.time())),
                'max_connections': '1',
                'allowed_output_formats': ['m3u8', 'ts', 'mp4']
            },
            'server_info': {
                'url': self.config['xtream_server'].get(
                    'server_url',
                    'http://localhost:8080'
                ),
                'port': str(self.config['xtream_server']['port']),
                'https_port': '',
                'server_protocol': 'http',
                'rtmp_port': '',
                'timezone': 'UTC',
                'timestamp_now': int(time.time()),
                'time_now': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }
        }

    def get_vod_categories(self) -> List[Dict[str, Any]]:
        """
        Get VOD (movie) categories from Jellyfin.
        
        Returns:
        List[Dict]: List of categories in Xtream Codes format
        """
        if not self.jellyfin_user_id:
            return []

        try:
            libraries = self.jellyfin.get_movie_libraries(
                self.jellyfin_user_id
            )
            categories = []
            for lib in libraries:
                categories.append({
                    'category_id': lib['Id'],
                    'category_name': lib.get('Name', 'Movies'),
                    'parent_id': 0
                })
            
            # Add a default "All Movies" category
            if not categories:
                categories.append({
                    'category_id': '0',
                    'category_name': 'All Movies',
                    'parent_id': 0
                })
            
            return categories
        except Exception as e:
            logger.error(f"Failed to get VOD categories: {str(e)}")
            return []

    def get_vod_streams(
        self,
        category_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get VOD (movie) streams from Jellyfin.
        
        Parameters:
        category_id (str): Category ID to filter by
        
        Returns:
        List[Dict]: List of VOD streams in Xtream Codes format
        """
        if not self.jellyfin_user_id:
            return []

        try:
            parent_id = None if category_id == '0' else category_id
            movies = self.jellyfin.get_movies(
                self.jellyfin_user_id,
                parent_id
            )
            
            streams = []
            for movie in movies:
                stream_id = movie['Id']
                container = self._get_container_extension(movie)
                
                streams.append({
                    'num': int(stream_id.replace('-', '')[:8], 16),
                    'name': movie.get('Name', 'Unknown'),
                    'stream_type': 'movie',
                    'stream_id': stream_id,
                    'stream_icon': self._get_image_url(movie),
                    'rating': movie.get('CommunityRating', 0),
                    'rating_5based': self._convert_rating_to_5(
                        movie.get('CommunityRating', 0)
                    ),
                    'added': self._parse_date(
                        movie.get('PremiereDate', '')
                    ),
                    'category_id': category_id or '0',
                    'container_extension': container,
                    'custom_sid': '',
                    'direct_source': ''
                })
            
            return streams
        except Exception as e:
            logger.error(f"Failed to get VOD streams: {str(e)}")
            return []

    def get_vod_info(self, vod_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific VOD.
        
        Parameters:
        vod_id (str): VOD ID
        
        Returns:
        Dict: VOD info in Xtream Codes format
        """
        if not self.jellyfin_user_id:
            return {}

        try:
            movie = self.jellyfin.get_item_details(
                self.jellyfin_user_id,
                vod_id
            )
            container = self._get_container_extension(movie)
            
            movie_data = {
                'info': {
                    'kinopoisk_url': '',
                    'tmdb_id': movie.get('ProviderIds', {}).get('Tmdb', ''),
                    'name': movie.get('Name', ''),
                    'o_name': movie.get('OriginalTitle', ''),
                    'cover_big': self._get_image_url(movie, 'Primary'),
                    'movie_image': self._get_image_url(movie, 'Backdrop'),
                    'releasedate': movie.get('PremiereDate', ''),
                    'episode_run_time': str(
                        movie.get('RunTimeTicks', 0) // 10000000 // 60
                    ),
                    'youtube_trailer': '',
                    'director': ', '.join(
                        movie.get('People', [])
                    ) if movie.get('People') else '',
                    'actors': ', '.join(
                        movie.get('People', [])
                    ) if movie.get('People') else '',
                    'cast': ', '.join(
                        movie.get('People', [])
                    ) if movie.get('People') else '',
                    'description': movie.get('Overview', ''),
                    'plot': movie.get('Overview', ''),
                    'age': movie.get('OfficialRating', ''),
                    'mpaa_rating': movie.get('OfficialRating', ''),
                    'rating_5based': self._convert_rating_to_5(
                        movie.get('CommunityRating', 0)
                    ),
                    'rating': movie.get('CommunityRating', 0),
                    'country': '',
                    'genre': ', '.join(movie.get('Genres', [])),
                    'duration_secs': str(
                        movie.get('RunTimeTicks', 0) // 10000000
                    ),
                    'duration': self._format_duration(
                        movie.get('RunTimeTicks', 0)
                    ),
                    'video': self._get_video_info(movie),
                    'audio': self._get_audio_info(movie),
                    'bitrate': self._get_bitrate(movie)
                },
                'movie_data': {
                    'stream_id': vod_id,
                    'name': movie.get('Name', ''),
                    'added': self._parse_date(
                        movie.get('PremiereDate', '')
                    ),
                    'category_id': '',
                    'container_extension': container,
                    'custom_sid': '',
                    'direct_source': ''
                }
            }
            
            return movie_data
        except Exception as e:
            logger.error(f"Failed to get VOD info: {str(e)}")
            return {}

    def get_series_categories(self) -> List[Dict[str, Any]]:
        """
        Get series categories from Jellyfin.
        
        Returns:
        List[Dict]: List of categories in Xtream Codes format
        """
        if not self.jellyfin_user_id:
            return []

        try:
            libraries = self.jellyfin.get_series_libraries(
                self.jellyfin_user_id
            )
            categories = []
            for lib in libraries:
                categories.append({
                    'category_id': lib['Id'],
                    'category_name': lib.get('Name', 'TV Shows'),
                    'parent_id': 0
                })
            
            # Add a default "All Series" category
            if not categories:
                categories.append({
                    'category_id': '0',
                    'category_name': 'All Series',
                    'parent_id': 0
                })
            
            return categories
        except Exception as e:
            logger.error(f"Failed to get series categories: {str(e)}")
            return []

    def get_series(
        self,
        category_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get series list from Jellyfin.
        
        Parameters:
        category_id (str): Category ID to filter by
        
        Returns:
        List[Dict]: List of series in Xtream Codes format
        """
        if not self.jellyfin_user_id:
            return []

        try:
            parent_id = None if category_id == '0' else category_id
            series_list = self.jellyfin.get_series(
                self.jellyfin_user_id,
                parent_id
            )
            
            series = []
            for show in series_list:
                series_id = show['Id']
                
                series.append({
                    'num': int(series_id.replace('-', '')[:8], 16),
                    'name': show.get('Name', 'Unknown'),
                    'series_id': series_id,
                    'cover': self._get_image_url(show),
                    'plot': show.get('Overview', ''),
                    'cast': '',
                    'director': '',
                    'genre': ', '.join(show.get('Genres', [])),
                    'releaseDate': show.get('PremiereDate', ''),
                    'last_modified': self._parse_date(
                        show.get('PremiereDate', '')
                    ),
                    'rating': show.get('CommunityRating', 0),
                    'rating_5based': self._convert_rating_to_5(
                        show.get('CommunityRating', 0)
                    ),
                    'backdrop_path': [self._get_image_url(show, 'Backdrop')],
                    'youtube_trailer': '',
                    'episode_run_time': '',
                    'category_id': category_id or '0'
                })
            
            return series
        except Exception as e:
            logger.error(f"Failed to get series: {str(e)}")
            return []

    def get_series_info(self, series_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific series.
        
        Parameters:
        series_id (str): Series ID
        
        Returns:
        Dict: Series info in Xtream Codes format
        """
        if not self.jellyfin_user_id:
            return {}

        try:
            series_data = self.jellyfin.get_series_info(
                self.jellyfin_user_id,
                series_id
            )
            
            series_info = series_data['info']
            episodes = series_data['episodes']
            
            # Format seasons and episodes for Xtream Codes
            seasons = []
            episodes_dict = {}
            
            for season_num, season_episodes in episodes.items():
                if not season_episodes:
                    continue
                
                season_list = []
                for episode in season_episodes:
                    episode_num = episode.get('IndexNumber', 0)
                    container = self._get_container_extension(episode)
                    
                    episode_data = {
                        'id': episode['Id'],
                        'episode_num': episode_num,
                        'title': episode.get('Name', ''),
                        'container_extension': container,
                        'info': {
                            'name': episode.get('Name', ''),
                            'releasedate': episode.get('PremiereDate', ''),
                            'plot': episode.get('Overview', ''),
                            'duration_secs': str(
                                episode.get('RunTimeTicks', 0) // 10000000
                            ),
                            'duration': self._format_duration(
                                episode.get('RunTimeTicks', 0)
                            ),
                            'video': self._get_video_info(episode),
                            'audio': self._get_audio_info(episode),
                            'bitrate': self._get_bitrate(episode),
                            'rating': episode.get('CommunityRating', 0)
                        },
                        'custom_sid': '',
                        'added': self._parse_date(
                            episode.get('PremiereDate', '')
                        ),
                        'season': int(season_num),
                        'direct_source': ''
                    }
                    season_list.append(episode_data)
                
                if season_list:
                    episodes_dict[season_num] = season_list
                    seasons.append({
                        'season_number': int(season_num),
                        'name': f'Season {season_num}',
                        'episode_count': len(season_list),
                        'overview': '',
                        'cover': self._get_image_url(series_info),
                        'cover_big': self._get_image_url(
                            series_info,
                            'Primary'
                        ),
                    })
            
            result = {
                'seasons': seasons,
                'info': {
                    'name': series_info.get('Name', ''),
                    'cover': self._get_image_url(series_info),
                    'plot': series_info.get('Overview', ''),
                    'cast': '',
                    'director': '',
                    'genre': ', '.join(series_info.get('Genres', [])),
                    'releaseDate': series_info.get('PremiereDate', ''),
                    'last_modified': self._parse_date(
                        series_info.get('PremiereDate', '')
                    ),
                    'rating': series_info.get('CommunityRating', 0),
                    'rating_5based': self._convert_rating_to_5(
                        series_info.get('CommunityRating', 0)
                    ),
                    'backdrop_path': [
                        self._get_image_url(series_info, 'Backdrop')
                    ],
                    'youtube_trailer': '',
                    'episode_run_time': '',
                    'category_id': ''
                },
                'episodes': episodes_dict
            }
            
            return result
        except Exception as e:
            logger.error(f"Failed to get series info: {str(e)}")
            return {}

    def _get_container_extension(self, item: Dict[str, Any]) -> str:
        """
        Get container extension from media item.
        
        Parameters:
        item (dict): Media item
        
        Returns:
        str: Container extension (e.g., 'mp4', 'mkv')
        """
        media_sources = item.get('MediaSources', [])
        if media_sources:
            container = media_sources[0].get('Container', 'mp4')
            return container.lower()
        return 'mp4'

    def _get_image_url(
        self,
        item: Dict[str, Any],
        image_type: str = 'Primary'
    ) -> str:
        """
        Get image URL for an item.
        
        Parameters:
        item (dict): Media item
        image_type (str): Type of image
        
        Returns:
        str: Image URL
        """
        item_id = item.get('Id', '')
        if not item_id:
            return ''
        
        return (
            f"{self.jellyfin.server_url}/Items/{item_id}/Images/{image_type}"
            f"?api_key={self.jellyfin.api_key}"
        )

    def _convert_rating_to_5(self, rating: float) -> float:
        """
        Convert rating to 5-based scale.
        
        Parameters:
        rating (float): Rating (0-10 scale)
        
        Returns:
        float: Rating on 5-based scale
        """
        return round(rating / 2, 1) if rating else 0

    def _parse_date(self, date_str: str) -> str:
        """
        Parse and format date for Xtream Codes.
        
        Parameters:
        date_str (str): Date string
        
        Returns:
        str: Unix timestamp as string
        """
        if not date_str:
            return ''
        
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return str(int(dt.timestamp()))
        except Exception:
            return ''

    def _format_duration(self, ticks: int) -> str:
        """
        Format duration from ticks to HH:MM:SS.
        
        Parameters:
        ticks (int): Duration in ticks
        
        Returns:
        str: Formatted duration
        """
        seconds = ticks // 10000000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _get_video_info(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract video information from item.
        
        Parameters:
        item (dict): Media item
        
        Returns:
        dict: Video information
        """
        media_sources = item.get('MediaSources', [])
        if not media_sources:
            return {}
        
        video_streams = [
            s for s in media_sources[0].get('MediaStreams', [])
            if s.get('Type') == 'Video'
        ]
        
        if not video_streams:
            return {}
        
        video = video_streams[0]
        return {
            'codec': video.get('Codec', ''),
            'width': video.get('Width', 0),
            'height': video.get('Height', 0),
            'bitrate': video.get('BitRate', 0)
        }

    def _get_audio_info(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract audio information from item.
        
        Parameters:
        item (dict): Media item
        
        Returns:
        dict: Audio information
        """
        media_sources = item.get('MediaSources', [])
        if not media_sources:
            return {}
        
        audio_streams = [
            s for s in media_sources[0].get('MediaStreams', [])
            if s.get('Type') == 'Audio'
        ]
        
        if not audio_streams:
            return {}
        
        audio = audio_streams[0]
        return {
            'codec': audio.get('Codec', ''),
            'channels': audio.get('Channels', 0),
            'bitrate': audio.get('BitRate', 0)
        }

    def _get_bitrate(self, item: Dict[str, Any]) -> int:
        """
        Get total bitrate for item.
        
        Parameters:
        item (dict): Media item
        
        Returns:
        int: Bitrate
        """
        media_sources = item.get('MediaSources', [])
        if media_sources:
            return media_sources[0].get('Bitrate', 0)
        return 0


# Initialize server
server = XtreamServer()


@app.route('/player_api.php', methods=['GET'])
def player_api():
    """
    Main Xtream Codes API endpoint.
    Handles authentication and various actions.
    """
    username = request.args.get('username')
    password = request.args.get('password')
    action = request.args.get('action')

    # Authentication
    if not username or not password:
        return jsonify({'error': 'Missing credentials'}), 401

    if not server.authenticate(username, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Handle different actions
    if not action:
        # No action = server info / authentication response
        return jsonify(server.get_server_info(username))

    if action == 'get_vod_categories':
        return jsonify(server.get_vod_categories())

    if action == 'get_vod_streams':
        category_id = request.args.get('category_id')
        return jsonify(server.get_vod_streams(category_id))

    if action == 'get_vod_info':
        vod_id = request.args.get('vod_id')
        if not vod_id:
            return jsonify({'error': 'Missing vod_id'}), 400
        return jsonify(server.get_vod_info(vod_id))

    if action == 'get_series_categories':
        return jsonify(server.get_series_categories())

    if action == 'get_series':
        category_id = request.args.get('category_id')
        return jsonify(server.get_series(category_id))

    if action == 'get_series_info':
        series_id = request.args.get('series_id')
        if not series_id:
            return jsonify({'error': 'Missing series_id'}), 400
        return jsonify(server.get_series_info(series_id))

    if action == 'get_live_categories':
        # Return empty list - live TV not supported but clients expect valid response
        return jsonify([])

    if action == 'get_live_streams':
        # Return empty list - live TV not supported but clients expect valid response
        return jsonify([])

    return jsonify({'error': f'Unknown action: {action}'}), 400


@app.route('/movie/<username>/<password>/<stream_id>.<container>')
def stream_movie(username, password, stream_id, container):
    """
    Stream a movie/VOD.
    Redirects to Jellyfin stream URL.
    Uses HLS for m3u8 requests, direct streaming for other containers.
    """
    if not server.authenticate(username, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Use HLS streaming for m3u8 requests for better XC client compatibility
    if container == 'm3u8':
        stream_url = server.jellyfin.get_hls_stream_url(stream_id)
    else:
        stream_url = server.jellyfin.get_stream_url(stream_id, container)
    return Response(status=302, headers={'Location': stream_url})


@app.route('/series/<username>/<password>/<stream_id>.<container>')
def stream_episode(username, password, stream_id, container):
    """
    Stream an episode.
    Redirects to Jellyfin stream URL.
    Uses HLS for m3u8 requests, direct streaming for other containers.
    """
    if not server.authenticate(username, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Use HLS streaming for m3u8 requests for better XC client compatibility
    if container == 'm3u8':
        stream_url = server.jellyfin.get_hls_stream_url(stream_id)
    else:
        stream_url = server.jellyfin.get_stream_url(stream_id, container)
    return Response(status=302, headers={'Location': stream_url})


def main():
    """Start the Xtream Codes server"""
    host = server.config['xtream_server']['host']
    port = server.config['xtream_server']['port']
    
    logger.info(f"Starting Xtream Codes Server on {host}:{port}")
    logger.info("Jellyfin-Xtream Server is ready")
    
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    main()
