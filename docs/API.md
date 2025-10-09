# Xtream Codes API Documentation

This document describes the Xtream Codes API endpoints implemented by
Jellyfin-Xtream-Server.

## Base URL

All API requests are made to:
```
http://{server}:{port}/
```

Default: `http://localhost:8080/`

## Authentication

All requests require username and password parameters:
- `username`: Configured in config/config.json
- `password`: Corresponding password

## Streaming Support

The server supports both direct file streaming and HLS (HTTP Live Streaming):

- **Direct Streaming**: Use original container extension (mp4, mkv, etc.)
  - Best for local networks with high bandwidth
  - No transcoding overhead
  
- **HLS Streaming** (Recommended): Use `.m3u8` extension
  - Better compatibility with Xtream Codes clients
  - Adaptive bitrate streaming
  - Works better over internet connections
  - Automatic transcoding when needed

Example:
```
/movie/user/pass/{id}.mp4   # Direct streaming
/movie/user/pass/{id}.m3u8  # HLS streaming (recommended)
```

## Endpoints

### 1. Server Info / Authentication

Authenticate and get server information.

**Endpoint**: `GET /player_api.php`

**Parameters**:
- `username` (required): Username
- `password` (required): Password

**Example**:
```
GET /player_api.php?username=user&password=pass
```

**Response**:
```json
{
  "user_info": {
    "username": "user",
    "password": "pass",
    "message": "Welcome to Jellyfin Xtream Server",
    "auth": 1,
    "status": "Active",
    "exp_date": "9999999999",
    "is_trial": "0",
    "active_cons": "0",
    "created_at": "1609459200",
    "max_connections": "1",
    "allowed_output_formats": ["m3u8", "ts", "mp4"]
  },
  "server_info": {
    "url": "http://localhost:8080",
    "port": "8080",
    "https_port": "",
    "server_protocol": "http",
    "rtmp_port": "",
    "timezone": "UTC",
    "timestamp_now": 1609459200,
    "time_now": "2024-01-01 00:00:00"
  }
}
```

---

### 2. Get VOD Categories

Get list of movie categories.

**Endpoint**: `GET /player_api.php`

**Parameters**:
- `username` (required): Username
- `password` (required): Password
- `action` (required): `get_vod_categories`

**Example**:
```
GET /player_api.php?username=user&password=pass&action=get_vod_categories
```

**Response**:
```json
[
  {
    "category_id": "abc123",
    "category_name": "Movies",
    "parent_id": 0
  },
  {
    "category_id": "def456",
    "category_name": "Kids Movies",
    "parent_id": 0
  }
]
```

---

### 3. Get VOD Streams

Get list of movies, optionally filtered by category.

**Endpoint**: `GET /player_api.php`

**Parameters**:
- `username` (required): Username
- `password` (required): Password
- `action` (required): `get_vod_streams`
- `category_id` (optional): Filter by category

**Example**:
```
GET /player_api.php?username=user&password=pass&action=get_vod_streams
GET /player_api.php?username=user&password=pass&action=get_vod_streams&category_id=abc123
```

**Response**:
```json
[
  {
    "num": 12345,
    "name": "Movie Title",
    "stream_type": "movie",
    "stream_id": "jellyfin-id-123",
    "stream_icon": "http://server/image.jpg",
    "rating": 8.5,
    "rating_5based": 4.25,
    "added": "1609459200",
    "category_id": "abc123",
    "container_extension": "mp4",
    "custom_sid": "",
    "direct_source": ""
  }
]
```

**Field Descriptions**:
- `num`: Numeric identifier (derived from stream_id)
- `name`: Movie title
- `stream_type`: Always "movie"
- `stream_id`: Jellyfin item ID (use for streaming)
- `stream_icon`: Cover image URL
- `rating`: Rating on 10-point scale
- `rating_5based`: Rating on 5-point scale
- `added`: Unix timestamp of premiere date
- `category_id`: Category this movie belongs to
- `container_extension`: File extension (mp4, mkv, etc.)

---

### 4. Get VOD Info

Get detailed information about a specific movie.

**Endpoint**: `GET /player_api.php`

**Parameters**:
- `username` (required): Username
- `password` (required): Password
- `action` (required): `get_vod_info`
- `vod_id` (required): Movie ID (from stream_id)

**Example**:
```
GET /player_api.php?username=user&password=pass&action=get_vod_info&vod_id=jellyfin-id-123
```

**Response**:
```json
{
  "info": {
    "tmdb_id": "12345",
    "name": "Movie Title",
    "o_name": "Original Title",
    "cover_big": "http://server/image.jpg",
    "movie_image": "http://server/backdrop.jpg",
    "releasedate": "2023-01-01",
    "episode_run_time": "120",
    "director": "Director Name",
    "actors": "Actor1, Actor2",
    "cast": "Actor1, Actor2",
    "description": "Movie description...",
    "plot": "Movie plot...",
    "age": "PG-13",
    "mpaa_rating": "PG-13",
    "rating_5based": 4.25,
    "rating": 8.5,
    "genre": "Action, Drama",
    "duration_secs": "7200",
    "duration": "02:00:00",
    "video": {
      "codec": "h264",
      "width": 1920,
      "height": 1080,
      "bitrate": 5000000
    },
    "audio": {
      "codec": "aac",
      "channels": 6,
      "bitrate": 192000
    },
    "bitrate": 5192000
  },
  "movie_data": {
    "stream_id": "jellyfin-id-123",
    "name": "Movie Title",
    "added": "1609459200",
    "category_id": "",
    "container_extension": "mp4",
    "custom_sid": "",
    "direct_source": ""
  }
}
```

---

### 5. Get Series Categories

Get list of TV series categories.

**Endpoint**: `GET /player_api.php`

**Parameters**:
- `username` (required): Username
- `password` (required): Password
- `action` (required): `get_series_categories`

**Example**:
```
GET /player_api.php?username=user&password=pass&action=get_series_categories
```

**Response**:
```json
[
  {
    "category_id": "xyz789",
    "category_name": "TV Shows",
    "parent_id": 0
  }
]
```

---

### 6. Get Series

Get list of TV series, optionally filtered by category.

**Endpoint**: `GET /player_api.php`

**Parameters**:
- `username` (required): Username
- `password` (required): Password
- `action` (required): `get_series`
- `category_id` (optional): Filter by category

**Example**:
```
GET /player_api.php?username=user&password=pass&action=get_series
GET /player_api.php?username=user&password=pass&action=get_series&category_id=xyz789
```

**Response**:
```json
[
  {
    "num": 67890,
    "name": "Series Title",
    "series_id": "jellyfin-series-id",
    "cover": "http://server/image.jpg",
    "plot": "Series description...",
    "cast": "",
    "director": "",
    "genre": "Drama, Thriller",
    "releaseDate": "2023-01-01",
    "last_modified": "1609459200",
    "rating": 9.0,
    "rating_5based": 4.5,
    "backdrop_path": ["http://server/backdrop.jpg"],
    "youtube_trailer": "",
    "episode_run_time": "",
    "category_id": "xyz789"
  }
]
```

---

### 7. Get Series Info

Get detailed information about a series including all episodes.

**Endpoint**: `GET /player_api.php`

**Parameters**:
- `username` (required): Username
- `password` (required): Password
- `action` (required): `get_series_info`
- `series_id` (required): Series ID

**Example**:
```
GET /player_api.php?username=user&password=pass&action=get_series_info&series_id=jellyfin-series-id
```

**Response**:
```json
{
  "seasons": [
    {
      "season_number": 1,
      "name": "Season 1",
      "episode_count": 10,
      "overview": "",
      "cover": "http://server/image.jpg",
      "cover_big": "http://server/image.jpg"
    }
  ],
  "info": {
    "name": "Series Title",
    "cover": "http://server/image.jpg",
    "plot": "Series description...",
    "cast": "",
    "director": "",
    "genre": "Drama, Thriller",
    "releaseDate": "2023-01-01",
    "last_modified": "1609459200",
    "rating": 9.0,
    "rating_5based": 4.5,
    "backdrop_path": ["http://server/backdrop.jpg"],
    "youtube_trailer": "",
    "episode_run_time": "",
    "category_id": ""
  },
  "episodes": {
    "1": [
      {
        "id": "episode-id-1",
        "episode_num": 1,
        "title": "Episode Title",
        "container_extension": "mp4",
        "info": {
          "name": "Episode Title",
          "releasedate": "2023-01-01",
          "plot": "Episode description...",
          "duration_secs": "2700",
          "duration": "00:45:00",
          "video": {
            "codec": "h264",
            "width": 1920,
            "height": 1080,
            "bitrate": 5000000
          },
          "audio": {
            "codec": "aac",
            "channels": 2,
            "bitrate": 192000
          },
          "bitrate": 5192000,
          "rating": 8.5
        },
        "custom_sid": "",
        "added": "1609459200",
        "season": 1,
        "direct_source": ""
      }
    ]
  }
}
```

**Notes**:
- Episodes are grouped by season number
- Each season is a key in the `episodes` object
- Each episode contains full metadata and stream info

---

### 8. Stream Movie

Stream a movie file.

**Endpoint**: `GET /movie/{username}/{password}/{stream_id}.{container}`

**Parameters**:
- `username` (path): Username
- `password` (path): Password
- `stream_id` (path): Movie ID (from VOD streams)
- `container` (path): Container extension (mp4, mkv, m3u8, etc.)

**Example**:
```
GET /movie/user/pass/jellyfin-id-123.mp4
GET /movie/user/pass/jellyfin-id-123.m3u8  # HLS streaming (recommended)
```

**Response**:
- HTTP 302 Redirect to Jellyfin stream URL
- Client follows redirect to actual video stream
- For m3u8 requests, redirects to HLS master playlist for adaptive streaming

---

### 9. Stream Episode

Stream an episode file.

**Endpoint**: `GET /series/{username}/{password}/{stream_id}.{container}`

**Parameters**:
- `username` (path): Username
- `password` (path): Password
- `stream_id` (path): Episode ID (from series info)
- `container` (path): Container extension (mp4, mkv, m3u8, etc.)

**Example**:
```
GET /series/user/pass/episode-id-1.mp4
GET /series/user/pass/episode-id-1.m3u8  # HLS streaming (recommended)
```

**Response**:
- HTTP 302 Redirect to Jellyfin stream URL
- Client follows redirect to actual video stream
- For m3u8 requests, redirects to HLS master playlist for adaptive streaming

---

### 10. Get Live Categories (Not Supported)

Get list of live TV categories. Returns empty list as live TV is not supported.

**Endpoint**: `GET /player_api.php`

**Parameters**:
- `username` (required): Username
- `password` (required): Password
- `action` (required): `get_live_categories`

**Example**:
```
GET /player_api.php?username=user&password=pass&action=get_live_categories
```

**Response**:
```json
[]
```

**Note**: This endpoint returns an empty list because live TV functionality is not supported. It exists for compatibility with Xtream Codes clients that expect this endpoint to be available.

---

### 11. Get Live Streams (Not Supported)

Get list of live TV streams. Returns empty list as live TV is not supported.

**Endpoint**: `GET /player_api.php`

**Parameters**:
- `username` (required): Username
- `password` (required): Password
- `action` (required): `get_live_streams`
- `category_id` (optional): Category ID (ignored)

**Example**:
```
GET /player_api.php?username=user&password=pass&action=get_live_streams
GET /player_api.php?username=user&password=pass&action=get_live_streams&category_id=123
```

**Response**:
```json
[]
```

**Note**: This endpoint returns an empty list because live TV functionality is not supported. It exists for compatibility with Xtream Codes clients that expect this endpoint to be available.

---

## Error Responses

### 401 Unauthorized
```json
{
  "error": "Invalid credentials"
}
```

### 400 Bad Request
```json
{
  "error": "Missing required parameter"
}
```

### 404 Not Found
Standard HTTP 404 for invalid endpoints.

---

## Client Implementation Example

### Python (using requests)

```python
import requests

base_url = "http://localhost:8080"
username = "user"
password = "pass"

# Authenticate
params = {
    "username": username,
    "password": password
}
response = requests.get(f"{base_url}/player_api.php", params=params)
server_info = response.json()

# Get VOD streams
params["action"] = "get_vod_streams"
response = requests.get(f"{base_url}/player_api.php", params=params)
movies = response.json()

# Stream a movie
movie_id = movies[0]["stream_id"]
container = movies[0]["container_extension"]
stream_url = f"{base_url}/movie/{username}/{password}/{movie_id}.{container}"
# Use stream_url in video player
```

### JavaScript (using fetch)

```javascript
const baseUrl = "http://localhost:8080";
const username = "user";
const password = "pass";

// Authenticate
const authUrl = `${baseUrl}/player_api.php?username=${username}&password=${password}`;
const authResponse = await fetch(authUrl);
const serverInfo = await authResponse.json();

// Get VOD streams
const vodUrl = `${authUrl}&action=get_vod_streams`;
const vodResponse = await fetch(vodUrl);
const movies = await vodResponse.json();

// Get stream URL
const movie = movies[0];
const streamUrl = `${baseUrl}/movie/${username}/${password}/${movie.stream_id}.${movie.container_extension}`;
// Use streamUrl in video player
```

---

## Rate Limiting

Currently no rate limiting is implemented. This is suitable for personal
use but should be added for production deployments.

## CORS

CORS is not configured by default. Add Flask-CORS if needed for
browser-based clients.
