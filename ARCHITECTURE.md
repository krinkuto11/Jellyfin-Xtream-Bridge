# Architecture Overview

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Xtream Codes Client                      │
│                     (TiviMate, Perfect Player, etc.)            │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Xtream Codes API Protocol
                            │ (HTTP/REST)
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                   Jellyfin-Xtream-Server                        │
│                         (This Middleware)                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              xtream_server.py (Flask)                  │    │
│  │  - Authentication                                      │    │
│  │  - API Endpoint Handlers                               │    │
│  │  - Format Translation                                  │    │
│  └──────────────────────┬─────────────────────────────────┘    │
│                         │                                       │
│  ┌──────────────────────▼─────────────────────────────────┐    │
│  │           jellyfin_client.py                           │    │
│  │  - Jellyfin API Client                                 │    │
│  │  - Library Management                                  │    │
│  │  - Item Queries                                        │    │
│  └──────────────────────┬─────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Jellyfin API (HTTP/REST)
                            │ + X-Emby-Token Authentication
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                      Jellyfin Server                            │
│  - Media Library Management                                     │
│  - Transcoding & Streaming                                      │
│  - Metadata Management                                          │
└─────────────────────────────────────────────────────────────────┘
```

## Request Flow

### Authentication Flow

```
Client                  Xtream Server           Jellyfin Server
  │                           │                        │
  │ GET /player_api.php       │                        │
  │ ?username=X&password=Y    │                        │
  ├──────────────────────────►│                        │
  │                           │ Validate credentials   │
  │                           │ (config.json)          │
  │                           │                        │
  │                           │ GET /Users             │
  │                           ├───────────────────────►│
  │                           │                        │
  │                           │◄───────────────────────┤
  │                           │ [User List]            │
  │                           │                        │
  │◄──────────────────────────┤                        │
  │ Server Info JSON          │                        │
  │ (Xtream format)           │                        │
```

### VOD/Movie Browsing Flow

```
Client                  Xtream Server           Jellyfin Server
  │                           │                        │
  │ GET /player_api.php       │                        │
  │ ?action=get_vod_streams   │                        │
  ├──────────────────────────►│                        │
  │                           │                        │
  │                           │ GET /Items             │
  │                           │ ?IncludeItemTypes=Movie│
  │                           ├───────────────────────►│
  │                           │                        │
  │                           │◄───────────────────────┤
  │                           │ [Movie Items]          │
  │                           │                        │
  │                           │ Transform to           │
  │                           │ Xtream format          │
  │                           │                        │
  │◄──────────────────────────┤                        │
  │ VOD Streams JSON          │                        │
```

### Streaming Flow

```
Client                  Xtream Server           Jellyfin Server
  │                           │                        │
  │ GET /movie/user/pass/     │                        │
  │     {stream_id}.mp4       │                        │
  ├──────────────────────────►│                        │
  │                           │ Validate auth          │
  │                           │                        │
  │                           │ Build Jellyfin URL     │
  │                           │                        │
  │◄──────────────────────────┤                        │
  │ HTTP 302 Redirect         │                        │
  │ Location: /Videos/{id}/   │                        │
  │           stream.mp4      │                        │
  │                           │                        │
  │─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─►│
  │ GET /Videos/{id}/stream.mp4?api_key=X              │
  │                                                    │
  │◄───────────────────────────────────────────────────┤
  │ Video Stream (Direct or Transcoded)                │
```

## Data Models

### Xtream Codes Format

The middleware translates between these formats:

#### VOD Stream Object
```json
{
  "num": 1234,
  "name": "Movie Name",
  "stream_type": "movie",
  "stream_id": "jellyfin-item-id",
  "stream_icon": "http://server/image.jpg",
  "rating": 8.5,
  "rating_5based": 4.25,
  "added": "1609459200",
  "category_id": "category-id",
  "container_extension": "mp4"
}
```

#### Series Object
```json
{
  "num": 5678,
  "name": "Series Name",
  "series_id": "jellyfin-series-id",
  "cover": "http://server/image.jpg",
  "plot": "Description...",
  "genre": "Drama, Action",
  "rating": 9.0,
  "rating_5based": 4.5,
  "category_id": "category-id"
}
```

### Jellyfin Format

The middleware consumes Jellyfin's API format:

#### Item Object (Movie/Episode)
```json
{
  "Id": "guid",
  "Name": "Item Name",
  "Type": "Movie",
  "Overview": "Description...",
  "Genres": ["Genre1", "Genre2"],
  "CommunityRating": 8.5,
  "OfficialRating": "PG-13",
  "PremiereDate": "2023-01-01T00:00:00Z",
  "RunTimeTicks": 72000000000,
  "MediaSources": [...]
}
```

## Key Translation Logic

### Category Mapping
- Jellyfin Collection Folders → Xtream Categories
- Movies library → VOD categories
- TV Shows library → Series categories

### Stream ID Mapping
- Direct 1:1 mapping: Jellyfin Item ID = Xtream Stream ID
- Allows efficient lookups without maintaining state

### Stream URL Construction
- Xtream URL: `/movie/{user}/{pass}/{id}.{ext}`
- Jellyfin URL: `/Videos/{id}/stream.{ext}?api_key={key}`
- Uses HTTP redirect (302) for seamless streaming

### Metadata Translation
| Jellyfin Field | Xtream Field |
|----------------|--------------|
| Name | name |
| Overview | plot/description |
| CommunityRating (0-10) | rating_5based (0-5) |
| PremiereDate | releasedate/added |
| Genres | genre (comma-separated) |
| RunTimeTicks | duration_secs |

## Authentication

### Client Authentication
- Username/password defined in `config.json`
- Simple dictionary lookup (not database)
- Suitable for personal use

### Jellyfin Authentication
- API Key-based authentication
- X-Emby-Token header
- Full access to library

## Performance Considerations

### Caching
Currently no caching implemented. Future improvements:
- Cache library structure
- Cache metadata for X minutes
- Invalidate on Jellyfin webhook events

### Connection Pooling
- Jellyfin client uses requests.Session for connection reuse
- Flask development server (single-threaded)
- Production: Use gunicorn/uwsgi for multi-process

### Scalability
- Stateless design (no session storage)
- Each request is independent
- Can run multiple instances behind load balancer

## Security Considerations

### Authentication
- Basic username/password (HTTP)
- Consider HTTPS in production
- API keys stored in config (not in code)

### Access Control
- Single Jellyfin user for all requests
- No per-user library filtering
- Suitable for single-user/family deployments

### Data Exposure
- Full library visible to authenticated users
- No content restrictions
- Parent controls should be on Jellyfin side

## Extension Points

### Adding Live TV Support
1. Implement `get_live_categories()` mapping
2. Add `get_live_streams()` endpoint
3. Handle `/live/{user}/{pass}/{id}.ts` URLs
4. Note: Currently ignored per requirements

### Custom Metadata
- Override `_get_image_url()` for custom artwork
- Extend VOD/Series info with additional fields
- Add custom categories/filtering

### Multiple Jellyfin Users
- Add user mapping in config
- Pass user_id based on Xtream username
- Implement per-user library filtering

## Error Handling

### Client-Side Errors
- Invalid credentials → 401 Unauthorized
- Missing parameters → 400 Bad Request
- Unknown action → 400 Bad Request

### Server-Side Errors
- Jellyfin connection failed → Empty results
- Logged to console/file
- Graceful degradation

### Network Errors
- Requests have 30s timeout
- Connection pooling with retries
- Error propagation to client
