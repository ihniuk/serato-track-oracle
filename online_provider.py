"""
Online Track Provider & Recommendation Service
Loads curated DJ anthems and queries external music APIs (iTunes / Deezer / MusicBrainz)
with automatic offline fallback.
"""

import os
import json
import urllib.parse
from typing import List, Dict, Optional
import httpx

CURATED_PATH = os.path.join(os.path.dirname(__file__), "curated_tracks.json")

class OnlineTrackProvider:
    def __init__(self):
        self.curated_catalog: List[Dict] = []
        self.load_curated_catalog()
        
    def load_curated_catalog(self):
        if os.path.exists(CURATED_PATH):
            try:
                with open(CURATED_PATH, "r", encoding="utf-8") as f:
                    self.curated_catalog = json.load(f)
            except Exception as e:
                print(f"[OnlineProvider] Error loading curated catalog: {e}")
                self.curated_catalog = []
                
    def get_curated_tracks(self) -> List[Dict]:
        return [dict(t) for t in self.curated_catalog]

    async def search_itunes(self, query: str, limit: int = 15) -> List[Dict]:
        """Queries iTunes Search API for metadata and 30-second audio previews."""
        if not query.strip():
            return []
        url = f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}&media=music&entity=song&limit={limit}"
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    results = []
                    for item in data.get("results", []):
                        track = {
                            "id": f"itunes_{item.get('trackId')}",
                            "title": item.get("trackName", "Unknown"),
                            "artist": item.get("artistName", "Unknown"),
                            "genre": item.get("primaryGenreName", "Electronic"),
                            "artwork": item.get("artworkUrl100", "").replace("100x100bb", "300x300bb"),
                            "preview_url": item.get("previewUrl", ""),
                            "external_url": item.get("trackViewUrl", ""),
                            "bpm": 0.0,
                            "key": "",
                            "source": "iTunes"
                        }
                        results.append(track)
                    return results
        except Exception:
            pass
        return []

    def get_music_links(self, artist: str, title: str) -> Dict[str, str]:
        """Generates quick launch links for DJ tools and streaming services."""
        q = urllib.parse.quote(f"{artist} {title}")
        return {
            "beatport": f"https://www.beatport.com/search?q={q}",
            "spotify": f"https://open.spotify.com/search/{q}",
            "youtube": f"https://www.youtube.com/results?search_query={q}",
            "apple_music": f"https://music.apple.com/search?term={q}"
        }
