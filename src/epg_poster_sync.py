"""
EPG Poster Sync - matches Jellyfin library items to guiatv_light.xml programmes
and applies poster images + metadata via the Jellyfin API.

Handles the colon-stripping that filesystems apply to folder names:
  EPG:      "DIRECTO Grupo B: Catar - Suiza T2026 · Mundial 2026"
  Filename: "DIRECTO Grupo B Catar - Suiza T2026 · Mundial 2026"
"""
import argparse
import json
import logging
import os
import re
import sys
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

COLON_RE = re.compile(r':\s*')


def normalize(title: str) -> str:
    title = COLON_RE.sub(' ', title)
    return re.sub(r'\s+', ' ', title).strip().lower()


def parse_epg(xml_path: str) -> Dict[str, dict]:
    """Parse guiatv_light.xml and return a dict keyed by normalized title."""
    logger.info(f"Parsing EPG: {xml_path}")
    tree = ET.parse(xml_path)
    root = tree.getroot()

    programmes: Dict[str, dict] = {}
    for prog in root.findall('programme'):
        icon = prog.find('icon')
        if icon is None:
            continue

        title = prog.findtext('title', '').strip()
        norm = normalize(title)

        desc_raw = prog.findtext('desc', '').strip()
        desc = re.sub(r'^\([^)]+\)\s*', '', desc_raw)

        categories = [c.text.strip() for c in prog.findall('category') if c.text]

        date_el = prog.findtext('date', '')
        year = int(date_el) if date_el and date_el.isdigit() else None

        star_el = prog.find('star-rating/value')
        rating = float(star_el.text.split('/')[0]) if star_el is not None else None

        # Keep earliest occurrence when the same programme repeats
        if norm not in programmes:
            programmes[norm] = {
                'title': title,
                'desc': desc,
                'icon_url': icon.get('src', ''),
                'categories': categories,
                'year': year,
                'rating': rating,
                'channel': prog.get('channel', ''),
            }

    logger.info(f"Indexed {len(programmes)} EPG programmes with icons")
    return programmes


class JellyfinSync:
    def __init__(self, server_url: str, api_key: str):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'X-Emby-Token': api_key,
            'Accept': 'application/json',
        })

    def _get(self, endpoint: str, params: dict = None) -> dict:
        r = self.session.get(
            f"{self.server_url}/{endpoint.lstrip('/')}",
            params=params, timeout=30
        )
        r.raise_for_status()
        return r.json()

    def get_user_id(self) -> str:
        return self._get('Users')[0]['Id']

    def get_library_id(self, user_id: str, library_name: str) -> Optional[str]:
        items = self._get('Items', {
            'userId': user_id,
            'IncludeItemTypes': 'CollectionFolder',
        })
        for item in items.get('Items', []):
            if item.get('Name', '').lower() == library_name.lower():
                return item['Id']
        return None

    def get_movies(self, user_id: str, library_id: str) -> List[dict]:
        items = self._get('Items', {
            'userId': user_id,
            'ParentId': library_id,
            'IncludeItemTypes': 'Movie',
            'Recursive': 'true',
            'Fields': 'Overview,Genres,Path',
        })
        return items.get('Items', [])

    def set_image(self, item_id: str, image_url: str) -> bool:
        # Ask Jellyfin to fetch the image directly from the URL
        try:
            r = self.session.post(
                f"{self.server_url}/Items/{item_id}/RemoteImages/Download",
                params={'type': 'Primary', 'imageUrl': image_url},
                timeout=30,
            )
            r.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"  RemoteImages/Download failed ({e}), falling back to direct upload")

        # Fallback: download locally and POST the binary
        try:
            img_r = requests.get(image_url, timeout=15)
            img_r.raise_for_status()
            content_type = img_r.headers.get('Content-Type', 'image/jpeg').split(';')[0].strip()
            r = self.session.post(
                f"{self.server_url}/Items/{item_id}/Images/Primary",
                data=img_r.content,
                headers={'Content-Type': content_type},
                timeout=30,
            )
            r.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"  Image upload failed: {e}")
            return False

    def update_metadata(self, item_id: str, user_id: str, prog: dict) -> bool:
        try:
            current = self._get(f'Items/{item_id}', {'userId': user_id})
            if prog['desc']:
                current['Overview'] = prog['desc']
            if prog['year']:
                current['ProductionYear'] = prog['year']
            if prog['rating'] is not None:
                current['CommunityRating'] = prog['rating']
            if prog['categories']:
                current['Genres'] = prog['categories']
            r = self.session.post(
                f"{self.server_url}/Items/{item_id}",
                json=current,
                timeout=30,
            )
            r.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"  Metadata update failed: {e}")
            return False


def load_config(config_path: str) -> dict:
    candidates = [
        config_path,
        os.path.join(os.path.dirname(__file__), '..', config_path),
        '/config/config.json',
    ]
    for p in candidates:
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    raise FileNotFoundError(f"Config not found. Tried: {candidates}")


def run_sync(
    epg_path: str,
    config_path: str = 'config/config.json',
    library_name: str = 'Deportes',
    dry_run: bool = False,
):
    config = load_config(config_path)
    jf = config['jellyfin']

    programmes = parse_epg(epg_path)
    sync = JellyfinSync(jf['server_url'], jf['api_key'])

    user_id = sync.get_user_id()
    library_id = sync.get_library_id(user_id, library_name)
    if not library_id:
        logger.error(f"Library '{library_name}' not found in Jellyfin")
        sys.exit(1)

    movies = sync.get_movies(user_id, library_id)
    logger.info(f"Found {len(movies)} items in '{library_name}'")

    matched, unmatched = 0, []

    for movie in movies:
        name = movie.get('Name', '')
        prog = programmes.get(normalize(name))

        if not prog:
            unmatched.append(name)
            continue

        logger.info(f"MATCH  {name!r}")
        logger.info(f"    -> {prog['title']!r}  [{prog['channel']}]")
        logger.info(f"       icon: {prog['icon_url']}")
        matched += 1

        if dry_run:
            continue

        item_id = movie['Id']
        img_ok = sync.set_image(item_id, prog['icon_url'])
        meta_ok = sync.update_metadata(item_id, user_id, prog)
        logger.info(f"       image={'OK' if img_ok else 'FAIL'}  metadata={'OK' if meta_ok else 'FAIL'}")

    logger.info(f"\nResult: {matched}/{len(movies)} matched")
    if unmatched:
        logger.info(f"Unmatched ({len(unmatched)}):")
        for name in unmatched:
            logger.info(f"  - {name!r}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sync EPG posters/metadata to Jellyfin')
    parser.add_argument('epg', help='Path to guiatv_light.xml')
    parser.add_argument('--config', default='config/config.json')
    parser.add_argument('--library', default='Deportes', help='Jellyfin library name')
    parser.add_argument('--dry-run', action='store_true', help='Match only, no writes')
    args = parser.parse_args()

    run_sync(args.epg, args.config, args.library, args.dry_run)
