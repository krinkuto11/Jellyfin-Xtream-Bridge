# Changelog

## [Unreleased] - 2025-10-09

### Added
- **HLS Streaming Support**: Added HTTP Live Streaming (HLS) support for better Xtream Codes client compatibility
  - New `get_hls_stream_url()` method in `JellyfinClient` for generating HLS master playlist URLs
  - Clients can now use `.m3u8` extension for adaptive bitrate streaming
  - Automatic transcoding support when needed
  - Better compatibility over internet connections
  
- **Streaming Options Documentation**
  - Added comprehensive "Streaming Support" section in API.md
  - Added "Streaming Options" section in README.md
  - Documented best practices for choosing between HLS and direct streaming
  - Provided usage examples for both streaming modes

### Changed
- Updated `/movie/` endpoint to support HLS when `.m3u8` extension is requested
- Updated `/series/` endpoint to support HLS when `.m3u8` extension is requested
- Enhanced API documentation with HLS examples and recommendations

### Technical Details
- HLS uses Jellyfin's `/Videos/{itemId}/master.m3u8` endpoint
- Maximum streaming bitrate: 120Mbps (configurable)
- Supported video codecs: h264, hevc
- Supported audio codecs: aac, mp3, ac3, eac3
- Transcoding parameters optimized for Xtream Codes clients

### Backward Compatibility
- All existing direct streaming functionality preserved
- Original container formats (mp4, mkv, avi, etc.) continue to work
- No breaking changes to existing API
- Clients using direct streaming URLs are unaffected

## Streaming Mode Comparison

| Feature | Direct Streaming | HLS Streaming |
|---------|-----------------|---------------|
| Compatibility | Good | Excellent |
| Bandwidth Usage | Fixed | Adaptive |
| Server CPU | Low | Medium |
| Network Efficiency | Good (local) | Excellent (internet) |
| Transcoding | Optional | Automatic |
| Use Case | Local networks | XC clients, internet |

## Recommendations

For best results with Xtream Codes clients:
1. **Use HLS streaming** (`.m3u8`) for maximum compatibility
2. Use direct streaming (`.mp4`, `.mkv`) only on fast local networks
3. HLS is especially recommended when streaming over the internet
4. Let Jellyfin handle transcoding automatically via HLS

## Migration Notes

No migration required. This is an additive change that enhances functionality without breaking existing implementations.

Clients can immediately start using HLS by changing the file extension in stream URLs:
- Before: `/movie/user/pass/{id}.mp4`
- After: `/movie/user/pass/{id}.m3u8`
