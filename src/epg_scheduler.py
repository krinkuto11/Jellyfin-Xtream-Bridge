"""
EPG Scheduler - downloads an EPG source on a cron schedule and syncs
posters/metadata to Jellyfin via epg_poster_sync.

Configured via config.json under "epg_sync":
  {
    "url":     "https://example.com/guiatv_light.xml.gz",
    "library": "Deportes",
    "cron":    "0 6 * * *"
  }
"""
import gzip
import logging
import os
import tempfile
from typing import Optional

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from epg_poster_sync import parse_epg, JellyfinSync, normalize

logger = logging.getLogger(__name__)


def download_epg(url: str) -> str:
    """Download EPG XML (or .gz) and return path to the local XML file."""
    logger.info(f"Downloading EPG from {url}")
    r = requests.get(url, timeout=60, stream=True)
    r.raise_for_status()

    content = r.content
    is_gz = (
        url.lower().endswith('.gz')
        or 'gzip' in r.headers.get('Content-Encoding', '')
        or 'gzip' in r.headers.get('Content-Type', '')
    )
    if is_gz:
        logger.info("Decompressing gzip EPG")
        content = gzip.decompress(content)

    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix='.xml', prefix='epg_', dir='/tmp'
    )
    tmp.write(content)
    tmp.close()
    logger.info(f"EPG saved to {tmp.name} ({len(content) // 1024} KB)")
    return tmp.name


def run_epg_job(server_url: str, api_key: str, epg_url: str, library: str):
    """Download EPG and sync to Jellyfin. Runs on schedule."""
    logger.info("EPG sync job started")
    epg_path = None
    try:
        epg_path = download_epg(epg_url)
        programmes = parse_epg(epg_path)

        sync = JellyfinSync(server_url, api_key)
        user_id = sync.get_user_id()
        library_id = sync.get_library_id(user_id, library)
        if not library_id:
            logger.error(f"EPG sync: library '{library}' not found in Jellyfin")
            return

        movies = sync.get_movies(user_id, library_id)
        logger.info(f"EPG sync: {len(movies)} items in '{library}'")

        matched = 0
        for movie in movies:
            name = movie.get('Name', '')
            prog = programmes.get(normalize(name))
            if not prog:
                logger.debug(f"EPG sync: no match for {name!r}")
                continue

            logger.info(f"EPG sync: {name!r} -> {prog['title']!r}")
            matched += 1
            item_id = movie['Id']

            if prog['icon_url']:
                img_ok = sync.set_image(item_id, prog['icon_url'])
                logger.info(f"  image: {'OK' if img_ok else 'FAIL'}")

            meta_ok = sync.update_metadata(item_id, user_id, prog)
            logger.info(f"  metadata: {'OK' if meta_ok else 'FAIL'}")

        logger.info(f"EPG sync done: {matched}/{len(movies)} matched")

    except Exception as e:
        logger.error(f"EPG sync job failed: {e}", exc_info=True)
    finally:
        if epg_path and os.path.exists(epg_path):
            os.unlink(epg_path)


def start_scheduler(config: dict) -> Optional[BackgroundScheduler]:
    """
    Start the EPG background scheduler if epg_sync is configured.
    Returns the scheduler instance (already started) or None.
    """
    epg_cfg = config.get('xtream_server', {}).get('epg_sync')
    if not epg_cfg:
        return None

    epg_url = epg_cfg.get('url', '').strip()
    library = epg_cfg.get('library', 'Deportes')
    cron_expr = epg_cfg.get('cron', '0 6 * * *')

    if not epg_url:
        logger.warning("epg_sync.url is empty — EPG scheduler not started")
        return None

    jf = config['jellyfin']

    def job():
        run_epg_job(jf['server_url'], jf['api_key'], epg_url, library)

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        job,
        trigger=CronTrigger.from_crontab(cron_expr),
        id='epg_sync',
        name='EPG poster sync',
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()

    logger.info(
        f"EPG scheduler started — library='{library}' cron='{cron_expr}' url='{epg_url}'"
    )

    # Run immediately on startup so the library is populated right away
    import threading
    logger.info("EPG sync: running initial sync in background")
    threading.Thread(target=job, daemon=True, name="epg-initial-sync").start()

    return scheduler
