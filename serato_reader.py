"""
Serato DJ Library & Live History Reader
Parses Serato binary chunk structures (database V2, .crate files, and .session history files).
Provides live detection of currently playing tracks on Serato decks.
"""

import os
import sys
import glob
import struct
import time
from typing import List, Dict, Optional, Tuple

CONTAINER_TAGS = {"otrk", "oent", "adat"}
TEXT_TAGS = {
    "tsng", "tart", "tkey", "tbpm", "tgen", "ptrk", "pfil",
    "vrsn", "tlen", "tcom", "tbit", "ttyr", "tadd", "uadd"
}

def decode_serato_payload(tag: str, payload: bytes) -> str:
    """Decodes Serato binary string payload, usually UTF-16BE or UTF-8."""
    if tag in ("uadd", "tlen", "tbit", "ttyp"):
        # Could be integer or string depending on version
        if len(payload) == 4:
            val = struct.unpack(">I", payload)[0]
            return str(val)
    try:
        # Most Serato metadata strings are UTF-16BE
        return payload.decode("utf-16-be").strip("\x00").strip()
    except Exception:
        try:
            return payload.decode("utf-8").strip("\x00").strip()
        except Exception:
            return payload.decode("latin1", errors="replace").strip()


def parse_serato_chunks(data: bytes) -> List[Tuple[str, any]]:
    """Recursively parses Serato 8-byte chunk headers: [4-byte Tag][4-byte Length][Payload]."""
    pos = 0
    total_len = len(data)
    chunks = []
    
    while pos + 8 <= total_len:
        tag_bytes = data[pos:pos+4]
        try:
            tag = tag_bytes.decode("ascii")
        except Exception:
            tag = tag_bytes.decode("latin1", errors="replace")
            
        length = struct.unpack(">I", data[pos+4:pos+8])[0]
        pos += 8
        
        if pos + length > total_len:
            # Truncated or malformed chunk
            break
            
        payload = data[pos:pos+length]
        pos += length
        
        if tag in CONTAINER_TAGS:
            sub = parse_serato_chunks(payload)
            chunks.append((tag, sub))
        elif tag in TEXT_TAGS:
            chunks.append((tag, decode_serato_payload(tag, payload)))
        else:
            chunks.append((tag, payload))
            
    return chunks


def extract_track_from_chunk_tree(chunks: List[Tuple[str, any]]) -> Dict:
    """Flattens a Serato chunk tree into a clean dictionary."""
    track = {
        "title": "Unknown Title",
        "artist": "Unknown Artist",
        "key": "",
        "bpm": 0.0,
        "genre": "",
        "path": "",
        "length": "",
        "played_at": 0
    }
    
    for tag, val in chunks:
        if isinstance(val, list):
            sub_res = extract_track_from_chunk_tree(val)
            for k, v in sub_res.items():
                if v and not track[k]:
                    track[k] = v
        elif tag == "tsng" and val:
            track["title"] = val
        elif tag == "tart" and val:
            track["artist"] = val
        elif tag == "tkey" and val:
            track["key"] = val
        elif tag == "tbpm" and val:
            try:
                track["bpm"] = round(float(val), 1)
            except ValueError:
                pass
        elif tag == "tgen" and val:
            track["genre"] = val
        elif tag in ("ptrk", "pfil") and val:
            track["path"] = val
        elif tag == "tlen" and val:
            track["length"] = val
        elif tag == "uadd" and val:
            try:
                track["played_at"] = int(val)
            except ValueError:
                pass
                
    return track


def find_serato_folders() -> List[str]:
    """
    Finds all _Serato_ folders across macOS (OSX), Windows, and external drives.
    On macOS:
      - ~/Music/_Serato_/
      - /Volumes/<ExternalDrive>/_Serato_/
    On Windows:
      - %USERPROFILE%\\Music\\_Serato_\\
      - <Drive>:\\_Serato_\\
    """
    candidates = []
    
    # 1. macOS default: ~/Music/_Serato_
    home_dir = os.path.expanduser("~")
    mac_user_serato = os.path.join(home_dir, "Music", "_Serato_")
    if os.path.exists(mac_user_serato):
        candidates.append(mac_user_serato)
        
    # 2. macOS External Drives in /Volumes/
    if os.path.exists("/Volumes"):
        try:
            for volume in os.listdir("/Volumes"):
                vol_serato = os.path.join("/Volumes", volume, "_Serato_")
                if os.path.exists(vol_serato) and vol_serato not in candidates:
                    candidates.append(vol_serato)
        except Exception:
            pass

    # 3. Windows user profile
    user_profile = os.environ.get("USERPROFILE", "")
    if user_profile:
        win_user_serato = os.path.join(user_profile, "Music", "_Serato_")
        if os.path.exists(win_user_serato) and win_user_serato not in candidates:
            candidates.append(win_user_serato)
            
    # 4. Windows drive letters (C:, D:, E:, etc.)
    for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        root = f"{letter}:\\_Serato_"
        if os.path.exists(root) and root not in candidates:
            candidates.append(root)
            
    return candidates


def parse_serato_session_file(session_path: str) -> List[Dict]:
    """Reads a Serato .session file and returns played tracks in order."""
    if not os.path.exists(session_path):
        return []
    try:
        with open(session_path, "rb") as f:
            data = f.read()
        chunks = parse_serato_chunks(data)
        
        tracks = []
        for tag, val in chunks:
            if tag == "oent" and isinstance(val, list):
                t = extract_track_from_chunk_tree(val)
                if t["title"] != "Unknown Title" or t["artist"] != "Unknown Artist":
                    tracks.append(t)
        return tracks
    except Exception as e:
        print(f"[SeratoReader] Error parsing session {session_path}: {e}")
        return []


def parse_serato_database(database_path: str) -> List[Dict]:
    """Reads a Serato database V2 file and returns all library tracks."""
    if not os.path.exists(database_path):
        return []
    try:
        with open(database_path, "rb") as f:
            data = f.read()
        chunks = parse_serato_chunks(data)
        tracks = []
        for tag, val in chunks:
            if tag in ("otrk", "oent") and isinstance(val, list):
                t = extract_track_from_chunk_tree(val)
                if t["title"] != "Unknown Title" or t["artist"] != "Unknown Artist":
                    tracks.append(t)
        return tracks
    except Exception as e:
        print(f"[SeratoReader] Error parsing database {database_path}: {e}")
        return []


def get_latest_serato_session_track() -> Optional[Dict]:
    """Looks up the most recently modified Serato session file and returns the latest track."""
    serato_dirs = find_serato_folders()
    if not serato_dirs:
        return None
        
    latest_file = None
    latest_mtime = 0
    
    for sdir in serato_dirs:
        sessions_dir = os.path.join(sdir, "History", "Sessions")
        if os.path.exists(sessions_dir):
            for entry in glob.glob(os.path.join(sessions_dir, "*.session")):
                try:
                    mtime = os.path.getmtime(entry)
                    if mtime > latest_mtime:
                        latest_mtime = mtime
                        latest_file = entry
                except OSError:
                    continue
                    
    if latest_file:
        tracks = parse_serato_session_file(latest_file)
        if tracks:
            # Latest played is typically at the end of the session
            last_track = tracks[-1]
            last_track["session_file"] = os.path.basename(latest_file)
            last_track["last_detected"] = latest_mtime
            return last_track
            
    return None
