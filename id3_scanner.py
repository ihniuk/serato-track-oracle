"""
Pure Python ID3 Tag Scanner
Reads TIT2 (Title), TPE1 (Artist), TBPM (BPM), TKEY (Key), TCON (Genre)
from MP3, WAV, AIFF, and FLAC files without external dependencies.
"""

import os
import struct
from typing import Dict, Optional, List

def read_id3v2_tags(filepath: str) -> Dict[str, str]:
    tags = {
        "title": os.path.splitext(os.path.basename(filepath))[0],
        "artist": "Unknown Artist",
        "bpm": 0.0,
        "key": "",
        "genre": "General",
        "path": filepath
    }
    
    try:
        with open(filepath, "rb") as f:
            header = f.read(10)
            if len(header) < 10 or header[:3] != b"ID3":
                return tags
                
            version_major = header[3]
            # syncsafe size of tag
            tag_size = (
                ((header[6] & 0x7F) << 21) |
                ((header[7] & 0x7F) << 14) |
                ((header[8] & 0x7F) << 7) |
                (header[9] & 0x7F)
            )
            
            tag_data = f.read(tag_size)
            pos = 0
            
            while pos + 10 <= len(tag_data):
                frame_id = tag_data[pos:pos+4].decode("latin1", errors="ignore")
                
                if frame_id[0] == "\x00":
                    break  # padding reached
                    
                if version_major == 4:
                    # ID3v2.4 uses syncsafe integer for frame size
                    frame_size = (
                        ((tag_data[pos+4] & 0x7F) << 21) |
                        ((tag_data[pos+5] & 0x7F) << 14) |
                        ((tag_data[pos+6] & 0x7F) << 7) |
                        (tag_data[pos+7] & 0x7F)
                    )
                else:
                    # ID3v2.3 uses regular 32-bit int
                    frame_size = struct.unpack(">I", tag_data[pos+4:pos+8])[0]
                    
                pos += 10
                if pos + frame_size > len(tag_data):
                    break
                    
                frame_payload = tag_data[pos:pos+frame_size]
                pos += frame_size
                
                # Parse text frame (TIT2, TPE1, TBPM, TKEY, TCON)
                if frame_id in ("TIT2", "TPE1", "TBPM", "TKEY", "TCON", "TALB") and len(frame_payload) > 1:
                    encoding = frame_payload[0]
                    content_bytes = frame_payload[1:]
                    text = ""
                    try:
                        if encoding == 0:
                            text = content_bytes.decode("iso-8859-1", errors="replace")
                        elif encoding == 1:
                            text = content_bytes.decode("utf-16", errors="replace")
                        elif encoding == 2:
                            text = content_bytes.decode("utf-16-be", errors="replace")
                        elif encoding == 3:
                            text = content_bytes.decode("utf-8", errors="replace")
                    except Exception:
                        text = content_bytes.decode("latin1", errors="replace")
                        
                    clean_text = text.replace("\x00", "").strip()
                    
                    if frame_id == "TIT2" and clean_text:
                        tags["title"] = clean_text
                    elif frame_id == "TPE1" and clean_text:
                        tags["artist"] = clean_text
                    elif frame_id == "TBPM" and clean_text:
                        try:
                            # Sometimes BPM has decimals or strings like '128.00'
                            tags["bpm"] = round(float(clean_text), 1)
                        except ValueError:
                            pass
                    elif frame_id == "TKEY" and clean_text:
                        tags["key"] = clean_text
                    elif frame_id == "TCON" and clean_text:
                        tags["genre"] = clean_text
                        
    except Exception as e:
        pass
        
    return tags


def scan_music_folder(folder_path: str, max_tracks: int = 500) -> List[Dict]:
    """Recursively scans a local folder for audio tracks and extracts tags."""
    if not os.path.exists(folder_path):
        return []
        
    valid_exts = {".mp3", ".wav", ".aif", ".aiff", ".flac", ".m4a"}
    tracks = []
    
    for root, _, files in os.walk(folder_path):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in valid_exts:
                full_path = os.path.join(root, f)
                tags = read_id3v2_tags(full_path)
                tracks.append(tags)
                if len(tracks) >= max_tracks:
                    return tracks
                    
    return tracks
