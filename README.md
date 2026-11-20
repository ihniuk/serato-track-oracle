# ⚡ SERATO TRACK ORACLE — DJ HARMONIC MIXING & TEMPO COMPANION
> **Intelligent Next-Track Recommender for Serato DJ Pro / Lite on macOS (OSX) & Windows**

Serato Track Oracle runs alongside Serato DJ on your Mac (or external monitor/iPad) to solve the DJ's most critical real-time decision: **"What track should I load on the next deck right now?"**

It continuously analyzes the currently playing track and surfaces instant, club-ready recommendations based on **Camelot Key harmony**, **Tempo (BPM up or down with exact pitch fader %)**, and **Genre/Energy vibe flow**.

---

## 🎧 KEY FEATURES

### 1. 🔄 Live Serato History Sync (Zero-Latency Background Watcher)
- Automatically monitors macOS Serato directories:
  - `~/Music/_Serato_/History/Sessions/*.session`
  - `/Volumes/<ExternalDJDrive>/_Serato_/`
- As soon as you drop and play a track on Deck 1 or Deck 2, Serato Track Oracle auto-detects the title, artist, key, and tempo without you touching anything!
- Also supports **Manual Override** and quick genre presets for preparation before a gig.

### 2. 🎼 Camelot Wheel & Energy Progression Engine
- **Harmonic Flow (0 / ±1)**: Seamless key matching (e.g. `8A` into `8A`, `9A`, or `7A`) with zero harmonic clash.
- **⚡ Energy Boost (+2 / +7 Semitones)**:
  - **Whole-Step Lift (+2 Steps)**: The classic peak-time room elevator (e.g. `8A` → `10A`).
  - **Jaw-Drop Half-Step Pump (+7 Steps)**: Half-step semitone jump for maximum crowd hype (e.g. `8A` → `3A`).
- **🎭 Mood Shift**: Transitions between Relative Major & Minor (e.g. `8A` (Am) ↔ `8B` (C Major)).
- **🧊 Energy Cooldown (-2 Steps)**: Graceful tension release for breakdown or transition sets.
- **Interactive SVG Camelot Wheel**: Visual radar displaying all 24 keys with instant click-to-filter.

### 3. ⏱️ Tempo & Pitch Fader Calculation
- Computes the exact CDJ / Serato pitch slider percentage needed: e.g. `+1.6%` or `-2.3%`.
- **Pitch Range Filters**: Quick toggle for `±4%`, `±8%`, or `±16%` pitch limits.
- **Tempo Direction Filter**: Filter recommendations by:
  - ⬆️ **Tempo Up** (Accelerate the dancefloor)
  - ⬇️ **Tempo Down** (Bring tempo down)
  - ⏸️ **Exact Tempo Lock**
- **Half-Time & Double-Time Engine**: Detects when tracks mix at half/double tempos (e.g. 70 BPM Hip-Hop ↔ 140 BPM Dubstep/Techno, 87 BPM ↔ 174 BPM Drum & Bass).

### 4. 📂 Local Library + 🌐 Online Discovery
- **Local Serato Library**: Automatically loads your Serato `database V2` and crate metadata.
- **Local Folder Scanner**: Built-in ID3 tag reader scans any folder on your Mac (e.g. `~/Music/DJ Tracks`) for Key, BPM, Title, Artist, and Genre.
- **Online DJ Catalog**: Rich pre-loaded collection of club and festival anthems across Tech House, Melodic Techno, Drum & Bass, Hip-Hop, Afrobeats, Amapiano, EDM, and Pop.
- **30-Second Audio Previews**: Click ▶ directly on any card to preview the track in your headphones.
- **Direct Streaming / Store Links**: One-click shortcuts to Beatport, Spotify, Apple Music, and YouTube.

### 5. 📋 Setlist Queue & Set Planner
- Click **"Mix In 🎧"** to simulate transitions and plan a 10-track set progression in advance.
- Click **"+ Queue"** to build a live setlist.

---

## 🚀 QUICK START ON macOS (OSX)

### Option A: Double-Click Launcher (Easiest)
In Finder, navigate to the `serato-track-oracle` folder and **double-click**:
```
SeratoTrackOracle.command
```
*(If macOS asks for permission the first time: right-click `SeratoTrackOracle.command` → Open).*

### Option B: Terminal Command
Open **Terminal** on macOS and run:
```bash
cd "path/to/serato-track-oracle"
chmod +x start.sh
./start.sh
```

The script will automatically install lightweight dependencies (`fastapi`, `uvicorn`, `httpx`), start the local server, and open `http://127.0.0.1:5000` in Safari or Chrome.

---

## 🎛️ SERATO SETUP TIPS

1. **Enable Serato Live Session History**:
   - In Serato DJ Pro, open **History** panel.
   - Serato automatically writes live `.session` files to `~/Music/_Serato_/History/Sessions/`.
   - As long as Serato DJ Pro is running and you play tracks, Serato Track Oracle will auto-update its deck in real time!
2. **Key Analysis in Serato**:
   - In Serato DJ Pro settings, under **Library + Display**, ensure **Show Key as Camelot** is enabled (or standard musical keys). Serato Track Oracle automatically parses both formats seamlessly!

---

## 📁 PROJECT ARCHITECTURE

```
serato-track-oracle/
├── app.py                     # FastAPI backend & Serato live history poller
├── serato_reader.py           # Native macOS & Windows Serato database/session parser
├── harmonic_engine.py         # Camelot wheel, pitch fader calculation & scoring
├── id3_scanner.py             # Pure-Python ID3 tag & local folder scanner
├── online_provider.py         # Online track suggestions, previews & links
├── curated_tracks.json        # Curated library across electronic, bass, urban genres
├── static/
│   ├── index.html             # Responsive Dark Mode DJ HUD Console
│   ├── app.js                 # Frontend state, Camelot SVG radar, live audio previews
│   └── styles.css             # Pioneer DJ / Serato inspired glassmorphism design
├── requirements.txt           # Python dependencies
├── start.sh                   # macOS bash startup script
├── SeratoTrackOracle.command  # 1-click macOS Finder launcher
├── start.bat                  # Windows launcher
└── README.md                  # Complete documentation
```
