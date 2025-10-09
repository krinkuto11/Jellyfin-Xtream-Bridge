# Jellyfin-Xtream-Server

A middleware server that allows Xtream Codes based clients (like TiviMate) to access a Jellyfin library. This enables apps designed for IPTV services to browse and play Movies and TV Series from your Jellyfin server.

## Features

- **Xtream Codes API Compatible**: Implements the Xtream Codes API protocol
- **Movies (VOD) Support**: Browse and stream movies from Jellyfin
- **TV Series Support**: Browse series, seasons, and episodes
- **HLS Streaming**: Adaptive bitrate streaming for better compatibility
- **Direct Streaming**: Support for direct file streaming
- **Automatic Transcoding**: Leverages Jellyfin's streaming capabilities
- **Category Support**: Maps Jellyfin libraries to Xtream categories
- **Metadata**: Provides rich metadata (descriptions, ratings, artwork)

**Note**: This middleware focuses on Movies and TV Series. Live TV functionality from Jellyfin is intentionally not included.

## Requirements

- Python 3.7+
- Jellyfin Server (10.8+)
- Jellyfin API Key

## Installation

1. Clone this repository:
```bash
git clone https://github.com/krinkuto11/Jellyfin-Xtream-Server.git
cd Jellyfin-Xtream-Server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create configuration file:
```bash
cp config.json.example config.json
```

4. Edit `config.json` with your settings:
```json
{
    "jellyfin": {
        "server_url": "http://your-jellyfin-server:8096",
        "api_key": "your-jellyfin-api-key"
    },
    "xtream_server": {
        "host": "0.0.0.0",
        "port": 8080,
        "users": {
            "your_username": "your_password"
        }
    }
}
```

### Getting Jellyfin API Key

1. Log into your Jellyfin server
2. Go to Dashboard → API Keys
3. Click "+" to create a new API key
4. Give it a name (e.g., "Xtream Server")
5. Copy the generated API key to your config.json

## Usage

### Starting the Server

```bash
python xtream_server.py
```

The server will start on the configured host and port (default: `0.0.0.0:8080`).

### Connecting with Xtream Codes Clients

Configure your client app (e.g., TiviMate) with these settings:

- **Server URL**: `http://your-server-ip:8080`
- **Username**: As configured in `config.json`
- **Password**: As configured in `config.json`

The client will now see your Jellyfin movies and series as if they were on an Xtream Codes IPTV service.

## Streaming Options

The server supports two streaming modes:

### HLS Streaming (Recommended)
Use `.m3u8` extension for adaptive bitrate streaming:
- Better compatibility with Xtream Codes clients
- Automatic quality adjustment based on bandwidth
- Works better over internet connections
- Supports transcoding when needed

Example:
```
http://your-server:8080/movie/user/pass/movie-id.m3u8
http://your-server:8080/series/user/pass/episode-id.m3u8
```

### Direct Streaming
Use original container extension (`.mp4`, `.mkv`, etc.):
- Best for local networks with high bandwidth
- No transcoding overhead
- Lower server CPU usage

Example:
```
http://your-server:8080/movie/user/pass/movie-id.mp4
http://your-server:8080/series/user/pass/episode-id.mkv
```

**Recommendation**: Use HLS (`.m3u8`) for the best compatibility with Xtream Codes clients, especially when streaming over the internet.

## API Endpoints

The server implements the following Xtream Codes API endpoints:

### Authentication
- `GET /player_api.php?username=X&password=Y` - Authenticate and get server info

### VOD (Movies)
- `GET /player_api.php?username=X&password=Y&action=get_vod_categories` - Get movie categories
- `GET /player_api.php?username=X&password=Y&action=get_vod_streams&category_id=Z` - Get movies in category
- `GET /player_api.php?username=X&password=Y&action=get_vod_info&vod_id=Z` - Get movie details
- `GET /movie/username/password/stream_id.mp4` - Stream a movie (direct)
- `GET /movie/username/password/stream_id.m3u8` - Stream a movie (HLS, recommended)

### Series
- `GET /player_api.php?username=X&password=Y&action=get_series_categories` - Get series categories
- `GET /player_api.php?username=X&password=Y&action=get_series&category_id=Z` - Get series in category
- `GET /player_api.php?username=X&password=Y&action=get_series_info&series_id=Z` - Get series details with episodes
- `GET /series/username/password/stream_id.mp4` - Stream an episode (direct)
- `GET /series/username/password/stream_id.m3u8` - Stream an episode (HLS, recommended)

## Architecture

```
┌─────────────────┐         ┌──────────────────────┐         ┌─────────────────┐
│                 │         │                      │         │                 │
│  Xtream Client  │ ◄─────► │  Xtream Server       │ ◄─────► │  Jellyfin       │
│  (TiviMate)     │         │  (This Middleware)   │         │  Server         │
│                 │         │                      │         │                 │
└─────────────────┘         └──────────────────────┘         └─────────────────┘
```

### Components

1. **xtream_codes.py**: Reference client implementation showing how Xtream Codes API works
2. **jellyfin_client.py**: Client for interacting with Jellyfin API
3. **xtream_server.py**: Main server that translates between Xtream Codes and Jellyfin APIs

## Configuration Options

### Jellyfin Settings
- `server_url`: Your Jellyfin server URL
- `api_key`: Jellyfin API key for authentication

### Xtream Server Settings
- `host`: Interface to bind to (use `0.0.0.0` for all interfaces)
- `port`: Port to listen on
- `users`: Dictionary of username/password pairs for authentication

## Troubleshooting

### Server won't start
- Check that the port is not already in use
- Verify your config.json is valid JSON
- Ensure Jellyfin server is accessible

### No movies/series showing
- Verify your Jellyfin API key is correct
- Check that you have movie/series libraries in Jellyfin
- Look at server logs for error messages

### Streaming issues
- Ensure your Jellyfin server can transcode media
- Check network connectivity between client and both servers
- Verify the client supports the media formats

## Development

### Running Tests
Currently, there are no automated tests. Manual testing can be done using the reference client:

```python
from xtream_codes import Client

# Connect to your Xtream server
client = Client(
    "http://localhost:8080",
    "your_username",
    "your_password"
)

# Test authentication
client.authenticate()

# Test VOD
categories = client.get_vod_categories()
streams = client.get_vod_streams()

# Test Series
series_cats = client.get_series_categories()
series = client.get_series()
```

### Code Style
This project follows PEP 8 Python coding conventions. See `python.instructions.md` for detailed guidelines.

## License

This project is provided as-is for personal use. Please ensure compliance with Jellyfin's terms of service.

## Contributing

Contributions are welcome! Please ensure your code follows the Python coding conventions outlined in `python.instructions.md`.

## Acknowledgments

- [Jellyfin](https://jellyfin.org/) - The media server
- Xtream Codes API - The IPTV protocol standard

## Disclaimer

This tool is for personal use with your own Jellyfin server. Do not use it to distribute copyrighted content illegally.
