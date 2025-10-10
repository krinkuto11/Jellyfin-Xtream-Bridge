"""
Test script for Jellyfin-Xtream Server.
This script demonstrates how to test the server using the Xtream client.
"""
import sys
import os
import logging

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from xtream_codes import Client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_authentication(client: Client):
    """Test authentication"""
    print("\n" + "="*60)
    print("Testing Authentication")
    print("="*60)
    try:
        info = client.authenticate()
        print("✓ Authentication successful")
        print(f"  User: {info['user_info']['username']}")
        print(f"  Status: {info['user_info']['status']}")
        print(f"  Message: {info['user_info']['message']}")
        return True
    except Exception as e:
        print(f"✗ Authentication failed: {str(e)}")
        return False


def test_vod_categories(client: Client):
    """Test VOD categories"""
    print("\n" + "="*60)
    print("Testing VOD Categories")
    print("="*60)
    try:
        categories = client.get_vod_categories()
        print(f"✓ Retrieved {len(categories)} VOD categories")
        for cat in categories[:5]:
            print(f"  - {cat['category_name']} (ID: {cat['category_id']})")
        return categories
    except Exception as e:
        print(f"✗ Failed to get VOD categories: {str(e)}")
        return []


def test_vod_streams(client: Client, category_id: str = None):
    """Test VOD streams"""
    print("\n" + "="*60)
    print("Testing VOD Streams")
    print("="*60)
    try:
        streams = client.get_vod_streams(category_id)
        print(f"✓ Retrieved {len(streams)} VOD streams")
        for stream in streams[:5]:
            print(f"  - {stream['name']}")
            print(f"    ID: {stream['stream_id']}")
            print(f"    Rating: {stream.get('rating', 0)}")
            print(f"    Plot: {stream.get('plot', 'N/A')[:50]}...")
            print(f"    Genre: {stream.get('genre', 'N/A')}")
        return streams
    except Exception as e:
        print(f"✗ Failed to get VOD streams: {str(e)}")
        return []


def test_vod_info(client: Client, vod_id: str):
    """Test VOD info"""
    print("\n" + "="*60)
    print("Testing VOD Info")
    print("="*60)
    try:
        info = client.get_vod_info(vod_id)
        print(f"✓ Retrieved VOD info")
        print(f"  Title: {info['info']['name']}")
        print(f"  Release: {info['info'].get('releasedate', 'N/A')}")
        print(f"  Rating: {info['info'].get('rating', 0)}")
        print(f"  Duration: {info['info'].get('duration', 'N/A')}")
        print(f"  Genre: {info['info'].get('genre', 'N/A')}")
        
        # Show stream URL
        url = client.get_vod_stream_url(
            vod_id,
            info['movie_data']['container_extension']
        )
        print(f"  Stream URL: {url}")
        return True
    except Exception as e:
        print(f"✗ Failed to get VOD info: {str(e)}")
        return False


def test_series_categories(client: Client):
    """Test series categories"""
    print("\n" + "="*60)
    print("Testing Series Categories")
    print("="*60)
    try:
        categories = client.get_series_categories()
        print(f"✓ Retrieved {len(categories)} series categories")
        for cat in categories[:5]:
            print(f"  - {cat['category_name']} (ID: {cat['category_id']})")
        return categories
    except Exception as e:
        print(f"✗ Failed to get series categories: {str(e)}")
        return []


def test_series(client: Client, category_id: str = None):
    """Test series list"""
    print("\n" + "="*60)
    print("Testing Series List")
    print("="*60)
    try:
        series = client.get_series(category_id)
        print(f"✓ Retrieved {len(series)} series")
        for show in series[:5]:
            print(f"  - {show['name']}")
            print(f"    ID: {show['series_id']}")
            print(f"    Rating: {show.get('rating', 0)}")
        return series
    except Exception as e:
        print(f"✗ Failed to get series: {str(e)}")
        return []


def test_series_info(client: Client, series_id: str):
    """Test series info"""
    print("\n" + "="*60)
    print("Testing Series Info")
    print("="*60)
    try:
        info = client.get_series_info(series_id)
        print(f"✓ Retrieved series info")
        print(f"  Title: {info['info']['name']}")
        print(f"  Rating: {info['info'].get('rating', 0)}")
        print(f"  Genre: {info['info'].get('genre', 'N/A')}")
        
        # Show seasons and episodes
        episodes = info.get('episodes', {})
        print(f"  Seasons: {len(episodes)}")
        for season_num, eps in episodes.items():
            print(f"    Season {season_num}: {len(eps)} episodes")
            if eps:
                first_ep = eps[0]
                print(f"      First episode: {first_ep['title']}")
                # Show stream URL for first episode
                url = client.get_episode_stream_url(
                    first_ep['id'],
                    first_ep['container_extension']
                )
                print(f"      Stream URL: {url}")
        return True
    except Exception as e:
        print(f"✗ Failed to get series info: {str(e)}")
        return False


def test_live_categories(client: Client):
    """Test live categories (should return empty list)"""
    print("\n" + "="*60)
    print("Testing Live Categories")
    print("="*60)
    try:
        categories = client.get_live_categories()
        if not isinstance(categories, list):
            print(f"✗ Expected list, got {type(categories)}")
            return False
        print(f"✓ Retrieved {len(categories)} live categories (expected: 0)")
        if len(categories) == 0:
            print("  ✓ Correctly returns empty list for unsupported feature")
        return True
    except Exception as e:
        print(f"✗ Failed to get live categories: {str(e)}")
        return False


def main():
    """Run all tests"""
    if len(sys.argv) < 4:
        print(
            "Usage: python test_server.py "
            "<server_url> <username> <password>"
        )
        print(
            "Example: python test_server.py "
            "http://localhost:8080 admin password"
        )
        sys.exit(1)
    
    server_url = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    
    print("="*60)
    print("Jellyfin-Xtream Server Test Suite")
    print("="*60)
    print(f"Server: {server_url}")
    print(f"Username: {username}")
    
    try:
        with Client(server_url, username, password) as client:
            # Test authentication
            if not test_authentication(client):
                print("\n✗ Authentication failed. Stopping tests.")
                sys.exit(1)
            
            # Test VOD
            vod_cats = test_vod_categories(client)
            vod_streams = test_vod_streams(client)
            
            if vod_streams:
                # Test first VOD's detailed info
                test_vod_info(client, vod_streams[0]['stream_id'])
            
            # Test Series
            series_cats = test_series_categories(client)
            series = test_series(client)
            
            if series:
                # Test first series' detailed info
                test_series_info(client, series[0]['series_id'])
            
            # Test Live TV (should return empty lists)
            test_live_categories(client)
            
            print("\n" + "="*60)
            print("Test Suite Completed")
            print("="*60)
    except Exception as e:
        print(f"\n✗ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
