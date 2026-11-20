"""
Serato Track Oracle - DJ Companion & Next-Track Harmonic Recommender
FastAPI Backend with Real-time Serato History Watching,
Camelot Wheel Mixing Engine, and Online/Local Library Search.
"""

import os
import sys
import time
import asyncio
from typing import Optional, List, Dict
from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from harmonic_engine import (
    normalize_key,
    get_harmonic_relationship,
    calculate_tempo_pitch,
    compute_mix_compatibility,
    CAMELOT_COLORS,
    CAMELOT_TO_MUSICAL
)
from serato_reader import (
    find_serato_folders,
    get_latest_serato_session_track,
    parse_serato_database
)
from id3_scanner import scan_music_folder
from online_provider import OnlineTrackProvider

app = FastAPI(title="Serato Track Oracle", version="1.0.0")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# Application In-Memory State
online_provider = OnlineTrackProvider()

state = {
    "current_track": {
        "title": "Losing It",
        "artist": "FISHER",
        "key": "8A",
        "musical_key": "Am",
        "bpm": 125.0,
        "genre": "Tech House",
        "source": "Default Initial Track",
        "detected_at": 0
    },
    "local_library": [],
    "serato_status": {
        "connected": False,
        "serato_dirs": [],
        "last_session_file": None,
        "last_check": 0
    },
    "queued_setlist": [],
    "history": []
}


class CurrentTrackPayload(BaseModel):
    title: str
    artist: str
    key: str
    bpm: float
    genre: Optional[str] = "House"
    source: Optional[str] = "Manual"


class ScanFolderPayload(BaseModel):
    folder_path: str


# Background Serato Poller
async def serato_live_watcher():
    """Periodically polls Serato session folder to detect new tracks automatically."""
    while True:
        try:
            serato_dirs = find_serato_folders()
            state["serato_status"]["serato_dirs"] = serato_dirs
            state["serato_status"]["connected"] = len(serato_dirs) > 0
            
            if serato_dirs:
                latest = get_latest_serato_session_track()
                if latest:
                    state["serato_status"]["last_session_file"] = latest.get("session_file")
                    # Check if changed
                    curr = state["current_track"]
                    norm_k = normalize_key(latest.get("key"))
                    
                    if (latest.get("title") != curr.get("title") or 
                        latest.get("artist") != curr.get("artist")) and latest.get("title"):
                        
                        track_obj = {
                            "title": latest.get("title"),
                            "artist": latest.get("artist"),
                            "key": norm_k or "8A",
                            "musical_key": CAMELOT_TO_MUSICAL.get(norm_k or "8A", ""),
                            "bpm": float(latest.get("bpm") or 124.0),
                            "genre": latest.get("genre") or "Electronic",
                            "source": "Serato Live Deck",
                            "detected_at": latest.get("last_detected", 0)
                        }
                        # Add previous to history
                        if curr.get("title"):
                            state["history"].insert(0, dict(curr))
                            if len(state["history"]) > 20:
                                state["history"].pop()
                                
                        state["current_track"] = track_obj
                        print(f"[Serato Watcher] Live track detected: {track_obj['artist']} - {track_obj['title']} ({track_obj['key']} @ {track_obj['bpm']} BPM)")
        except Exception as e:
            pass
        await asyncio.sleep(2.5)


@app.on_event("startup")
async def startup_event():
    # Attempt initial Serato library load if available
    serato_dirs = find_serato_folders()
    state["serato_status"]["serato_dirs"] = serato_dirs
    state["serato_status"]["connected"] = len(serato_dirs) > 0
    for sdir in serato_dirs:
        db_path = os.path.join(sdir, "database V2")
        if os.path.exists(db_path):
            tracks = parse_serato_database(db_path)
            for t in tracks:
                norm_k = normalize_key(t.get("key"))
                if norm_k:
                    t["key"] = norm_k
                    t["musical_key"] = CAMELOT_TO_MUSICAL.get(norm_k, "")
                    t["source"] = "Serato Library"
                    state["local_library"].append(t)
            print(f"[Startup] Loaded {len(tracks)} tracks from Serato database.")
            break
            
    # Launch background watcher task
    asyncio.create_task(serato_live_watcher())


# --- API Routes ---

@app.get("/api/current_track")
def get_current_track():
    curr = state["current_track"]
    norm_k = normalize_key(curr.get("key")) or "8A"
    return {
        **curr,
        "key": norm_k,
        "musical_key": CAMELOT_TO_MUSICAL.get(norm_k, "Am"),
        "key_color": CAMELOT_COLORS.get(norm_k, "#00b4d8"),
        "serato_status": state["serato_status"]
    }


@app.post("/api/current_track")
def set_current_track(payload: CurrentTrackPayload):
    norm_k = normalize_key(payload.key) or "8A"
    new_track = {
        "title": payload.title.strip(),
        "artist": payload.artist.strip(),
        "key": norm_k,
        "musical_key": CAMELOT_TO_MUSICAL.get(norm_k, "Am"),
        "bpm": round(float(payload.bpm), 1),
        "genre": payload.genre.strip() if payload.genre else "Electronic",
        "source": payload.source or "Manual Selection",
        "detected_at": time.time()
    }
    # Add previous to history
    if state["current_track"].get("title"):
        state["history"].insert(0, dict(state["current_track"]))
        if len(state["history"]) > 20:
            state["history"].pop()
            
    state["current_track"] = new_track
    return {"status": "ok", "current_track": new_track}


@app.get("/api/recommendations")
def get_recommendations(
    key: Optional[str] = None,
    bpm: Optional[float] = None,
    genre: Optional[str] = None,
    pitch_limit: float = Query(default=8.0, ge=1.0, le=25.0),
    tempo_direction: str = Query(default="all", pattern="^(all|up|down|same)$"),
    harmonic_filter: str = Query(default="all", pattern="^(all|harmonic|energy_boost|mood_shift|energy_drop)$"),
    source: str = Query(default="all", pattern="^(all|local|online)$"),
    genre_filter: Optional[str] = None,
    allow_half_double: bool = True
):
    """
    Computes real-time next-track suggestions based on key harmonic matching,
    tempo pitch calculation, energy shifts, and genre compatibility.
    """
    curr = state["current_track"]
    curr_key = normalize_key(key) or curr["key"]
    curr_bpm = float(bpm) if bpm is not None else float(curr["bpm"])
    curr_genre = genre if genre else curr.get("genre", "House")
    
    # 1. Gather candidate pool
    candidates = []
    
    # Online Curated Pool
    if source in ("all", "online"):
        for t in online_provider.get_curated_tracks():
            cand = dict(t)
            cand["source"] = "Online Curated"
            cand["key"] = normalize_key(cand.get("key"))
            if cand["key"]:
                candidates.append(cand)
                
    # Local Library Pool
    if source in ("all", "local"):
        for t in state["local_library"]:
            cand = dict(t)
            cand["key"] = normalize_key(cand.get("key"))
            if cand["key"]:
                candidates.append(cand)
                
    # 2. Evaluate each candidate against current playing track
    recommendations = []
    
    for cand in candidates:
        cand_key = cand.get("key")
        cand_bpm = float(cand.get("bpm", 0.0))
        cand_genre = cand.get("genre", "")
        
        # Don't recommend the exact same track
        cand_t = cand.get("title", "").lower().strip()
        curr_t = curr.get("title", "").lower().strip()
        if cand_t and curr_t and (cand_t == curr_t or cand_t in curr_t or curr_t in cand_t):
            cand_a = cand.get("artist", "").lower().strip()
            curr_a = curr.get("artist", "").lower().strip()
            if cand_a and curr_a and (cand_a in curr_a or curr_a in cand_a):
                continue
            
        compat = compute_mix_compatibility(
            curr_key=curr_key,
            curr_bpm=curr_bpm,
            curr_genre=curr_genre,
            cand_key=cand_key,
            cand_bpm=cand_bpm,
            cand_genre=cand_genre,
            pitch_limit_pct=pitch_limit,
            allow_half_double=allow_half_double
        )
        
        # Filter by Pitch Limit (unless half/double time within range)
        pitch_diff = abs(compat["tempo"]["pitch_diff_pct"])
        if pitch_diff > pitch_limit and not (compat["tempo"]["is_half_time"] or compat["tempo"]["is_double_time"]):
            continue
            
        # Filter by Tempo Direction
        direction = compat["tempo"]["direction"]
        if tempo_direction == "up" and direction != "up":
            continue
        elif tempo_direction == "down" and direction != "down":
            continue
        elif tempo_direction == "same" and direction != "same":
            continue
            
        # Filter by Harmonic Style / Energy
        energy_type = compat["harmonic"]["energy"]
        if harmonic_filter == "harmonic" and compat["harmonic"]["score"] < 90:
            continue
        elif harmonic_filter == "energy_boost" and energy_type != "boost":
            continue
        elif harmonic_filter == "mood_shift" and energy_type != "mood_shift":
            continue
        elif harmonic_filter == "energy_drop" and energy_type != "drop":
            continue
            
        # Filter by Genre search keyword
        if genre_filter and genre_filter.strip():
            gf = genre_filter.strip().lower()
            if gf not in cand_genre.lower() and gf not in cand.get("title", "").lower():
                continue
                
        # Music streaming & store links
        links = online_provider.get_music_links(cand.get("artist", ""), cand.get("title", ""))
        
        rec_entry = {
            "id": cand.get("id") or f"{cand.get('artist')}_{cand.get('title')}",
            "title": cand.get("title"),
            "artist": cand.get("artist"),
            "key": cand_key,
            "musical_key": CAMELOT_TO_MUSICAL.get(cand_key, ""),
            "key_color": CAMELOT_COLORS.get(cand_key, "#00b4d8"),
            "bpm": cand_bpm,
            "genre": cand_genre,
            "source": cand.get("source", "Local"),
            "path": cand.get("path", ""),
            "year": cand.get("year", ""),
            "preview_url": cand.get("preview_url", ""),
            "links": links,
            "compatibility": compat,
            "score": compat["overall_score"]
        }
        recommendations.append(rec_entry)
        
    # Sort recommendations by Overall Score descending
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "current_track": {
            "title": curr.get("title"),
            "artist": curr.get("artist"),
            "key": curr_key,
            "musical_key": CAMELOT_TO_MUSICAL.get(curr_key, ""),
            "bpm": curr_bpm,
            "genre": curr_genre
        },
        "filters_applied": {
            "pitch_limit": pitch_limit,
            "tempo_direction": tempo_direction,
            "harmonic_filter": harmonic_filter,
            "source": source,
            "genre_filter": genre_filter
        },
        "total_matches": len(recommendations),
        "results": recommendations[:60]
    }


@app.get("/api/online/search")
async def search_online_tracks(q: str = Query(..., min_length=2)):
    """Live online search through iTunes API for track previews and metadata."""
    results = await online_provider.search_itunes(q)
    return {"query": q, "results": results}


@app.post("/api/library/scan_folder")
def scan_folder(payload: ScanFolderPayload):
    """Scans any specified local folder for audio files and loads them into local library."""
    folder = payload.folder_path.strip()
    if not os.path.exists(folder):
        return JSONResponse(status_code=400, content={"error": f"Folder does not exist: {folder}"})
        
    found_tracks = scan_music_folder(folder, max_tracks=500)
    added_count = 0
    for t in found_tracks:
        norm_k = normalize_key(t.get("key"))
        if norm_k:
            t["key"] = norm_k
            t["musical_key"] = CAMELOT_TO_MUSICAL.get(norm_k, "")
            t["source"] = "Local Folder"
            state["local_library"].append(t)
            added_count += 1
            
    return {
        "status": "ok",
        "scanned_folder": folder,
        "tracks_scanned": len(found_tracks),
        "tracks_with_key": added_count,
        "total_local_library": len(state["local_library"])
    }


@app.get("/api/library")
def get_library():
    return {
        "total": len(state["local_library"]),
        "tracks": state["local_library"][:100]
    }


@app.post("/api/playlist/queue")
def queue_track(track: Dict):
    state["queued_setlist"].append(track)
    return {"status": "ok", "queued_count": len(state["queued_setlist"])}


@app.get("/api/playlist")
def get_setlist():
    return {
        "count": len(state["queued_setlist"]),
        "setlist": state["queued_setlist"]
    }


@app.delete("/api/playlist")
def clear_setlist():
    state["queued_setlist"].clear()
    return {"status": "ok"}


@app.get("/api/history")
def get_history():
    return {"history": state["history"]}


# Serve Frontend
@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=5000, reload=True)
