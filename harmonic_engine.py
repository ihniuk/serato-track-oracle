"""
Harmonic Mixing Engine for Serato DJ
Supports Camelot Wheel, Open Key, Standard Musical Key conversions,
Harmonic Compatibility Scoring, Pitch percentage calculation, and Half/Double-time matching.
"""

import re
from typing import Optional, Dict, Tuple, List

# Standard Musical Key to Camelot Wheel mapping
MUSICAL_TO_CAMELOT = {
    # Minor Keys (A)
    "Abm": "1A", "G#m": "1A", "Ab Minor": "1A", "G# Minor": "1A",
    "Ebm": "2A", "D#m": "2A", "Eb Minor": "2A", "D# Minor": "2A",
    "Bbm": "3A", "A#m": "3A", "Bb Minor": "3A", "A# Minor": "3A",
    "Fm": "4A", "F Minor": "4A",
    "Cm": "5A", "C Minor": "5A",
    "Gm": "6A", "G Minor": "6A",
    "Dm": "7A", "D Minor": "7A",
    "Am": "8A", "A Minor": "8A",
    "Em": "9A", "E Minor": "9A",
    "Bm": "10A", "B Minor": "10A",
    "F#m": "11A", "Gbm": "11A", "F# Minor": "11A", "Gb Minor": "11A",
    "C#m": "12A", "Dbm": "12A", "C# Minor": "12A", "Db Minor": "12A",

    # Major Keys (B)
    "B": "1B", "Bmaj": "1B", "B Major": "1B", "Cb": "1B", "Cb Major": "1B",
    "F#": "2B", "Gb": "2B", "F#maj": "2B", "Gbmaj": "2B", "F# Major": "2B", "Gb Major": "2B",
    "Db": "3B", "C#": "3B", "Dbmaj": "3B", "C#maj": "3B", "Db Major": "3B", "C# Major": "3B",
    "Ab": "4B", "G#": "4B", "Abmaj": "4B", "G#maj": "4B", "Ab Major": "4B", "G# Major": "4B",
    "Eb": "5B", "D#": "5B", "Ebmaj": "5B", "D#maj": "5B", "Eb Major": "5B", "D# Major": "5B",
    "Bb": "6B", "A#": "6B", "Bbmaj": "6B", "A#maj": "6B", "Bb Major": "6B", "A# Major": "6B",
    "F": "7B", "Fmaj": "7B", "F Major": "7B",
    "C": "8B", "Cmaj": "8B", "C Major": "8B",
    "G": "9B", "Gmaj": "9B", "G Major": "9B",
    "D": "10B", "Dmaj": "10B", "D Major": "10B",
    "A": "11B", "Amaj": "11B", "A Major": "11B",
    "E": "12B", "Emaj": "12B", "E Major": "12B",
}

# Reverse Camelot to representative musical key
CAMELOT_TO_MUSICAL = {
    "1A": "Abm", "1B": "B",
    "2A": "Ebm", "2B": "F#",
    "3A": "Bbm", "3B": "Db",
    "4A": "Fm",  "4B": "Ab",
    "5A": "Cm",  "5B": "Eb",
    "6A": "Gm",  "6B": "Bb",
    "7A": "Dm",  "7B": "F",
    "8A": "Am",  "8B": "C",
    "9A": "Em",  "9B": "G",
    "10A": "Bm", "10B": "D",
    "11A": "F#m","11B": "A",
    "12A": "C#m","12B": "E",
}

# Key colors for UI visualization (Standard Camelot / Mixed In Key palette)
CAMELOT_COLORS = {
    "1A": "#00b4d8", "1B": "#48cae4",
    "2A": "#0077b6", "2B": "#023e8a",
    "3A": "#7209b7", "3B": "#560bad",
    "4A": "#b5179e", "4B": "#f72585",
    "5A": "#e63946", "5B": "#d62828",
    "6A": "#f77f00", "6B": "#fcbf49",
    "7A": "#ffb703", "7B": "#ffd166",
    "8A": "#8ac926", "8B": "#a7c957",
    "9A": "#2ec4b6", "9B": "#208b81",
    "10A": "#06d6a0", "10B": "#1b9aaa",
    "11A": "#118ab2", "11B": "#073b4c",
    "12A": "#3a0ca3", "12B": "#4361ee",
}


def normalize_key(raw_key: str) -> Optional[str]:
    """
    Normalizes any key representation (e.g. '8A', 'Am', 'A minor', '8d', '1m')
    into standard Camelot format (e.g. '8A', '12B').
    """
    if not raw_key:
        return None
    k = raw_key.strip()
    
    # Check if already Camelot format (1A to 12B)
    m = re.match(r"^([1-9]|1[0-2])([ABab])$", k)
    if m:
        return f"{m.group(1)}{m.group(2).upper()}"
        
    # Check Open Key format (e.g. 1d = 1B, 1m = 1A)
    m_ok = re.match(r"^([1-9]|1[0-2])([dDmM])$", k)
    if m_ok:
        num = m_ok.group(1)
        letter = "B" if m_ok.group(2).lower() == "d" else "A"
        return f"{num}{letter}"
        
    # Normalize clean musical key string
    k_clean = k.replace("maj", "").replace("min", "m").replace("Minor", "m").replace("Major", "")
    k_clean = re.sub(r"\s+", "", k_clean)
    
    if k in MUSICAL_TO_CAMELOT:
        return MUSICAL_TO_CAMELOT[k]
    if k_clean in MUSICAL_TO_CAMELOT:
        return MUSICAL_TO_CAMELOT[k_clean]
        
    # Case-insensitive lookup
    for mk, cam in MUSICAL_TO_CAMELOT.items():
        if mk.lower() == k.lower() or mk.lower() == k_clean.lower():
            return cam
            
    return None


def parse_camelot(camelot_key: str) -> Tuple[int, str]:
    """Extracts (number: 1..12, letter: 'A' or 'B') from a Camelot string."""
    m = re.match(r"^([1-9]|1[0-2])([AB])$", camelot_key)
    if not m:
        raise ValueError(f"Invalid camelot key: {camelot_key}")
    return int(m.group(1)), m.group(2)


def get_harmonic_relationship(curr_key: str, target_key: str) -> Dict:
    """
    Computes harmonic relationship, compatibility score, transition name,
    and energy impact between two Camelot keys.
    """
    curr = normalize_key(curr_key)
    target = normalize_key(target_key)
    
    if not curr or not target:
        return {
            "compatible": False,
            "score": 0,
            "type": "Unknown Key",
            "energy": "neutral",
            "description": "Missing or unparseable musical key",
            "badge_color": "#6c757d"
        }
        
    c_num, c_mode = parse_camelot(curr)
    t_num, t_mode = parse_camelot(target)
    
    # Identical Key (Seamless mix)
    if c_num == t_num and c_mode == t_mode:
        return {
            "compatible": True,
            "score": 100,
            "type": "Harmonic Match",
            "energy": "steady",
            "energy_badge": "Steady Vibe 🎧",
            "description": f"Identical key ({curr}). Seamless blend with zero pitch clash.",
            "badge_color": "#10b981"
        }
        
    # Relative Major / Minor (Same number, opposite mode)
    if c_num == t_num and c_mode != t_mode:
        mood = "Darker / Melodic" if t_mode == "A" else "Brighter / Uplifting"
        return {
            "compatible": True,
            "score": 92,
            "type": "Relative Mode Shift",
            "energy": "mood_shift",
            "energy_badge": f"Mood Shift ({mood}) 🎭",
            "description": f"Relative mode switch ({curr} -> {target}). Strong emotional pivot.",
            "badge_color": "#8b5cf6"
        }
        
    # Camelot Clock Distance (1 to 12)
    step_diff = (t_num - c_num) % 12
    if step_diff > 6:
        step_diff -= 12  # e.g. -1 instead of +11
        
    # Adjacent Keys (+1 or -1 on Camelot Wheel)
    if c_mode == t_mode:
        if step_diff == 1:
            return {
                "compatible": True,
                "score": 95,
                "type": "Harmonic Step Up (+1)",
                "energy": "energy_up",
                "energy_badge": "Energy Lift ⬆️",
                "description": f"Clockwise step (+1). Natural melodic progression and gentle energy lift.",
                "badge_color": "#06b6d4"
            }
        elif step_diff == -1:
            return {
                "compatible": True,
                "score": 95,
                "type": "Harmonic Step Down (-1)",
                "energy": "energy_down",
                "energy_badge": "Energy Settle ⬇️",
                "description": f"Counter-clockwise step (-1). Smooth harmonic descent for cooling down.",
                "badge_color": "#3b82f6"
            }
            
        # Energy Boost Techniques (Famous DJ tricks)
        # +2 Semitones (+2 on Camelot wheel):
        if step_diff == 2:
            return {
                "compatible": True,
                "score": 88,
                "type": "Energy Boost (+2 Steps)",
                "energy": "boost",
                "energy_badge": "Big Energy Boost ⚡",
                "description": f"Whole-step boost (+2 Camelot). Classic peak-time room elevator.",
                "badge_color": "#f59e0b"
            }
        # -2 Semitones (-2 on Camelot wheel):
        elif step_diff == -2:
            return {
                "compatible": True,
                "score": 82,
                "type": "Energy Drop (-2 Steps)",
                "energy": "drop",
                "energy_badge": "Energy Drop 🧊",
                "description": f"Drop 2 steps. Deliberate tension release for transition sections.",
                "badge_color": "#64748b"
            }
        # +1 Semitone = +7 on Camelot wheel
        if (t_num - c_num) % 12 == 7:
            return {
                "compatible": True,
                "score": 85,
                "type": "Half-Step Semitone Pump",
                "energy": "boost",
                "energy_badge": "Jaw-Drop Energy 🚀",
                "description": f"Half-step modulation (+1 Semitone / +7 Camelot). Massive surge of hype.",
                "badge_color": "#ef4444"
            }
        # -1 Semitone = -7 on Camelot wheel (+5)
        if (t_num - c_num) % 12 == 5:
            return {
                "compatible": True,
                "score": 80,
                "type": "Half-Step Semitone Drop",
                "energy": "drop",
                "energy_badge": "Deep Vibe Reset 🌊",
                "description": f"-1 Semitone drop. Deep contrast transition.",
                "badge_color": "#6366f1"
            }

    # Diagonal Mix (+1 or -1 with mode change)
    if c_mode != t_mode and abs(step_diff) == 1:
        return {
            "compatible": True,
            "score": 78,
            "type": "Diagonal Modulation",
            "energy": "mood_shift",
            "energy_badge": "Diagonal Twist 🌀",
            "description": f"Diagonal shift ({curr} -> {target}). Rich, sophisticated chord change.",
            "badge_color": "#ec4899"
        }
        
    # Non-harmonic / clash
    return {
        "compatible": False,
        "score": max(30, 70 - abs(step_diff) * 10),
        "type": "Key Clash / Non-Harmonic",
        "energy": "neutral",
        "energy_badge": "Rough Transition ⚠️",
        "description": f"Distant key relation ({curr} vs {target}). Recommended to use drum breakdown, filter fade, or echo freeze.",
        "badge_color": "#475569"
    }


def calculate_tempo_pitch(curr_bpm: float, target_bpm: float) -> Dict:
    """
    Calculates exact pitch slider percentage and detects half-time / double-time compatibility.
    """
    if curr_bpm <= 0 or target_bpm <= 0:
        return {
            "pitch_diff_pct": 0.0,
            "pitch_str": "0.0%",
            "bpm_diff": 0.0,
            "is_half_time": False,
            "is_double_time": False,
            "effective_target_bpm": target_bpm,
            "difficulty": "Unknown",
            "direction": "same"
        }
        
    # Check direct pitch difference
    direct_diff = target_bpm - curr_bpm
    direct_pitch_pct = (direct_diff / curr_bpm) * 100
    
    # Check half-time (e.g. 140 -> 70 bpm)
    half_bpm = target_bpm * 2
    half_pitch_pct = ((half_bpm - curr_bpm) / curr_bpm) * 100
    
    # Check double-time (e.g. 85 -> 170 bpm)
    double_bpm = target_bpm / 2
    double_pitch_pct = ((double_bpm - curr_bpm) / curr_bpm) * 100
    
    # Determine best mode
    chosen_diff = direct_diff
    chosen_pitch_pct = direct_pitch_pct
    is_half = False
    is_double = False
    effective_bpm = target_bpm
    
    if abs(half_pitch_pct) < abs(direct_pitch_pct) and abs(half_pitch_pct) <= 12.0:
        chosen_diff = half_bpm - curr_bpm
        chosen_pitch_pct = half_pitch_pct
        is_half = True
        effective_bpm = half_bpm
    elif abs(double_pitch_pct) < abs(direct_pitch_pct) and abs(double_pitch_pct) <= 12.0:
        chosen_diff = double_bpm - curr_bpm
        chosen_pitch_pct = double_pitch_pct
        is_double = True
        effective_bpm = double_bpm
        
    # Difficulty categorization
    abs_pitch = abs(chosen_pitch_pct)
    if abs_pitch <= 2.0:
        diff_label = "Perfect (±2%)"
        color = "#10b981"
    elif abs_pitch <= 4.0:
        diff_label = "Easy (±4%)"
        color = "#06b6d4"
    elif abs_pitch <= 8.0:
        diff_label = "Standard (±8%)"
        color = "#f59e0b"
    elif abs_pitch <= 16.0:
        diff_label = "Wide (±16%)"
        color = "#f97316"
    else:
        diff_label = "Extreme (>16%)"
        color = "#ef4444"
        
    sign = "+" if chosen_pitch_pct > 0 else ""
    direction = "up" if chosen_pitch_pct > 0.3 else ("down" if chosen_pitch_pct < -0.3 else "same")
    
    return {
        "pitch_diff_pct": round(chosen_pitch_pct, 2),
        "pitch_str": f"{sign}{chosen_pitch_pct:.2f}%",
        "bpm_diff": round(chosen_diff, 1),
        "is_half_time": is_half,
        "is_double_time": is_double,
        "effective_target_bpm": round(effective_bpm, 1),
        "difficulty": diff_label,
        "difficulty_color": color,
        "direction": direction
    }


def compute_mix_compatibility(
    curr_key: str, curr_bpm: float, curr_genre: str,
    cand_key: str, cand_bpm: float, cand_genre: str,
    pitch_limit_pct: float = 8.0,
    allow_half_double: bool = True
) -> Dict:
    """
    Computes holistic mixing compatibility score (0 to 100) combining
    Key harmony, BPM pitch adjustment feasibility, and Genre proximity.
    """
    harmonic_info = get_harmonic_relationship(curr_key, cand_key)
    tempo_info = calculate_tempo_pitch(curr_bpm, cand_bpm)
    
    # Pitch Penalty Calculation
    pitch_pct = abs(tempo_info["pitch_diff_pct"])
    if pitch_pct <= 1.0:
        tempo_score = 100
    elif pitch_pct <= 4.0:
        tempo_score = 95 - (pitch_pct - 1.0) * 5
    elif pitch_pct <= pitch_limit_pct:
        tempo_score = 80 - (pitch_pct - 4.0) * 6
    else:
        overshoot = pitch_pct - pitch_limit_pct
        tempo_score = max(10, 50 - overshoot * 10)
        
    # Half-time / Double-time bonus if applicable
    if (tempo_info["is_half_time"] or tempo_info["is_double_time"]) and not allow_half_double:
        tempo_score = max(10, tempo_score - 40)
        
    # Genre Similarity Score
    genre_score = 85
    cg = (curr_genre or "").lower().strip()
    tg = (cand_genre or "").lower().strip()
    
    if cg and tg:
        if cg == tg:
            genre_score = 100
        elif cg in tg or tg in cg:
            genre_score = 95
        else:
            # Check genre family overlap
            house_terms = {"house", "tech house", "deep house", "afro house", "melodic", "disco"}
            bass_terms = {"dubstep", "trap", "bass", "drum and bass", "dnb", "jungle"}
            urban_terms = {"hip hop", "hip-hop", "rap", "r&b", "afrobeat", "dancehall", "reggaeton"}
            techno_terms = {"techno", "minimal", "hard techno", "acid"}
            
            families = [house_terms, bass_terms, urban_terms, techno_terms]
            matched_family = False
            for fam in families:
                c_in = any(term in cg for term in fam)
                t_in = any(term in tg for term in fam)
                if c_in and t_in:
                    genre_score = 90
                    matched_family = True
                    break
            if not matched_family:
                genre_score = 70
                
    # Composite Score
    composite_score = (
        harmonic_info["score"] * 0.50 +
        tempo_score * 0.35 +
        genre_score * 0.15
    )
    composite_score = round(min(100.0, max(0.0, composite_score)), 1)
    
    return {
        "overall_score": composite_score,
        "harmonic": harmonic_info,
        "tempo": tempo_info,
        "genre_score": genre_score,
        "mixable": composite_score >= 65 and pitch_pct <= (pitch_limit_pct if not (tempo_info["is_half_time"] or tempo_info["is_double_time"]) else 12.0)
    }
