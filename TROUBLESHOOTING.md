# Troubleshooting Guide

This guide helps resolve common issues with Jellyfin-Xtream-Server.

## Server Won't Start

### Error: "Config file not found"

**Problem**: config.json doesn't exist

**Solution**:
```bash
cp config.json.example config.json
nano config.json  # Edit with your settings
```

### Error: "No module named 'flask'"

**Problem**: Dependencies not installed

**Solution**:
```bash
pip install -r requirements.txt
# or
pip3 install -r requirements.txt
```

### Error: "Address already in use"

**Problem**: Port 8080 is already taken

**Solutions**:
1. Change port in config.json
2. Stop the other process using port 8080:
```bash
# Linux/Mac - Find process
lsof -i :8080
# Kill the process
kill -9 <PID>

# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

## Connection Issues

### Can't Connect to Server

**Check 1**: Server is running
```bash
# Should show output like:
# * Running on http://0.0.0.0:8080/
ps aux | grep xtream_server.py
```

**Check 2**: Network access
```bash
# From same machine
curl http://localhost:8080/player_api.php?username=test&password=test

# From another machine
curl http://SERVER_IP:8080/player_api.php?username=test&password=test
```

**Check 3**: Firewall rules
```bash
# Linux - Open port 8080
sudo ufw allow 8080

# Check if firewall is blocking
sudo ufw status
```

### Can't Connect to Jellyfin

**Problem**: Jellyfin server not accessible from Xtream server

**Check 1**: Jellyfin URL is correct
```bash
# Test from Xtream server
curl http://jellyfin-server:8096/System/Info
```

**Check 2**: API key is valid
- Go to Jellyfin Dashboard → API Keys
- Verify the key matches config.json
- Create new key if needed

**Check 3**: Network connectivity
```bash
# Ping Jellyfin server
ping jellyfin-server

# Check if Jellyfin port is open
telnet jellyfin-server 8096
# or
nc -zv jellyfin-server 8096
```

## Authentication Issues

### Error: "Invalid credentials"

**Problem 1**: Wrong username/password in client

**Solution**: Check config.json users section:
```json
{
  "xtream_server": {
    "users": {
      "your_username": "your_password"
    }
  }
}
```

**Problem 2**: Config not reloaded after change

**Solution**: Restart the server after changing config.json

### Error: "Authentication failed: Invalid response from server"

**Problem**: Jellyfin API key is invalid or expired

**Solution**:
1. Log into Jellyfin Dashboard
2. Go to API Keys section
3. Delete old key and create new one
4. Update config.json with new key
5. Restart Xtream server

## No Content Showing

### No Movies/Series in Client

**Check 1**: Jellyfin has content

Log into Jellyfin web interface and verify:
- Movies library exists and has content
- TV Shows library exists and has content
- Content is not hidden or restricted

**Check 2**: Check server logs

Start server and look for errors:
```bash
python3 xtream_server.py
# Look for ERROR messages
```

**Check 3**: Test API directly

```bash
# Get VOD categories
curl "http://localhost:8080/player_api.php?username=USER&password=PASS&action=get_vod_categories"

# Get VOD streams
curl "http://localhost:8080/player_api.php?username=USER&password=PASS&action=get_vod_streams"

# Get series categories
curl "http://localhost:8080/player_api.php?username=USER&password=PASS&action=get_series_categories"

# Get series
curl "http://localhost:8080/player_api.php?username=USER&password=PASS&action=get_series"
```

**Check 4**: Jellyfin user permissions

The Jellyfin user (first user returned by /Users) needs:
- Access to Movie and Series libraries
- Permission to view content

### Categories Empty

**Problem**: No Jellyfin libraries of type "movies" or "tvshows"

**Solution**:
1. Log into Jellyfin Dashboard
2. Go to Libraries
3. Ensure you have at least one library with type:
   - "Movies" for VOD content
   - "TV Shows" for series content

## Streaming Issues

### Video Won't Play

**Check 1**: Direct Jellyfin streaming works
```bash
# Get a stream URL from API
curl "http://localhost:8080/player_api.php?username=USER&password=PASS&action=get_vod_streams" | grep stream_id

# Try streaming directly
curl -I "http://localhost:8080/movie/USER/PASS/STREAM_ID.mp4"
# Should return 302 redirect

# Follow redirect manually
curl -L "http://localhost:8080/movie/USER/PASS/STREAM_ID.mp4" > /dev/null
# Should download/stream video
```

**Check 2**: Jellyfin transcoding enabled

1. Log into Jellyfin Dashboard
2. Go to Playback settings
3. Ensure hardware acceleration is configured (if needed)
4. Check transcoding logs for errors

**Check 3**: Client codec support

- Client may not support the video codec
- Jellyfin should transcode automatically
- Check Jellyfin dashboard for active streams

### Buffering Issues

**Problem**: Video keeps buffering

**Causes and Solutions**:

1. **Network bandwidth**: Check network speed
   ```bash
   # Test download speed
   speedtest-cli
   ```

2. **Jellyfin transcoding**: Reduce quality in client settings

3. **Server resources**: Check CPU/memory usage
   ```bash
   top
   # or
   htop
   ```

### HTTP 404 on Stream

**Problem**: Stream URL not found

**Check 1**: Item ID is correct
- The stream_id from API must match Jellyfin item ID
- Try getting item info directly from Jellyfin

**Check 2**: Item still exists in Jellyfin
- Library may have been rescanned
- Item may have been deleted

## Performance Issues

### Slow Response Times

**Problem 1**: Jellyfin server is slow

**Solutions**:
- Check Jellyfin server resources
- Optimize Jellyfin database
- Add more hardware resources

**Problem 2**: Network latency

**Solutions**:
- Deploy Xtream server closer to Jellyfin
- Use faster network connection
- Consider caching (future feature)

### High Memory Usage

**Problem**: Python process consuming too much memory

**Solutions**:
1. Restart server periodically
2. Use production WSGI server (gunicorn):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8080 xtream_server:app
   ```

## Client-Specific Issues

### TiviMate

**Issue**: Can't add server

**Solutions**:
- Use "Xtream Codes API" playlist type
- Don't include "/player_api.php" in URL
- Just use: `http://server:8080`
- Enter username and password in separate fields

**Issue**: No EPG data

**Note**: EPG (Electronic Program Guide) not supported
- This is for VOD/Series only
- Live TV features not implemented

### Perfect Player

**Issue**: Movies not showing in VOD section

**Solutions**:
- Ensure "VOD" section is enabled in app
- Refresh playlist in app settings
- Check app logs for errors

## Debugging Tips

### Enable Debug Logging

Edit xtream_server.py:
```python
# Change this line:
logging.basicConfig(level=logging.INFO, ...)

# To this:
logging.basicConfig(level=logging.DEBUG, ...)
```

### Check Raw API Responses

Use curl with pretty printing:
```bash
# Authentication
curl "http://localhost:8080/player_api.php?username=USER&password=PASS" | python3 -m json.tool

# VOD streams
curl "http://localhost:8080/player_api.php?username=USER&password=PASS&action=get_vod_streams" | python3 -m json.tool

# Series info
curl "http://localhost:8080/player_api.php?username=USER&password=PASS&action=get_series_info&series_id=ID" | python3 -m json.tool
```

### Test with Reference Client

Use the included test script:
```bash
python3 test_server.py http://localhost:8080 USER PASS
```

Or use the xtream_codes.py client directly:
```python
from xtream_codes import Client

client = Client("http://localhost:8080", "USER", "PASS")
client.authenticate()
print(client.get_vod_categories())
print(client.get_vod_streams())
```

### Monitor Server Logs

Watch logs in real-time:
```bash
python3 xtream_server.py 2>&1 | tee server.log
```

### Check Jellyfin API Directly

Test Jellyfin API independently:
```bash
# Get users
curl "http://jellyfin:8096/Users?api_key=YOUR_KEY" | python3 -m json.tool

# Get movies
curl "http://jellyfin:8096/Items?UserId=USER_ID&IncludeItemTypes=Movie&api_key=YOUR_KEY" | python3 -m json.tool

# Get series
curl "http://jellyfin:8096/Items?UserId=USER_ID&IncludeItemTypes=Series&api_key=YOUR_KEY" | python3 -m json.tool
```

## Getting Help

If you're still having issues:

1. **Check server logs** for error messages
2. **Test API endpoints** directly with curl
3. **Verify Jellyfin** is working independently
4. **Check network** connectivity between components
5. **Enable debug logging** for more details

### Information to Include When Reporting Issues

- Server OS and Python version
- Jellyfin version
- Client app and version
- Config.json (without passwords)
- Server logs showing the error
- Steps to reproduce the issue
