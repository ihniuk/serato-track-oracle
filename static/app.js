/**
 * Serato Track Oracle - Frontend Application Logic
 * Supports real-time Serato session watching, Camelot wheel rendering,
 * harmonic filtering, tempo pitch calculation, and audio previews.
 */

// Application State
const appState = {
  currentTrack: {
    title: "Losing It",
    artist: "FISHER",
    key: "8A",
    musical_key: "Am",
    bpm: 125.0,
    genre: "Tech House",
    source: "Manual"
  },
  filters: {
    pitch_limit: 8.0,
    tempo_direction: "all",
    harmonic_filter: "all",
    source: "all",
    genre_filter: ""
  },
  queuedSetlist: [],
  currentlyPlayingPreviewId: null
};

// Camelot color palette
const CAMELOT_COLORS = {
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
  "12A": "#3a0ca3", "12B": "#4361ee"
};

// DOM Elements
const el = {
  currentTitle: document.getElementById("current-title"),
  currentArtist: document.getElementById("current-artist"),
  currentGenreChip: document.getElementById("current-genre-chip"),
  currentMusicalKey: document.getElementById("current-musical-key"),
  currentKeyBadge: document.getElementById("current-key-badge"),
  currentBpmVal: document.getElementById("current-bpm-val"),
  trackSourceTag: document.getElementById("track-source-tag"),
  seratoStatusBadge: document.getElementById("serato-status-badge"),
  seratoStatusText: document.getElementById("serato-status-text"),
  resultsCountBadge: document.getElementById("results-count-badge"),
  recommendationsContainer: document.getElementById("recommendations-container"),
  emptyState: document.getElementById("empty-state"),
  genreSearchInput: document.getElementById("genre-search-input"),
  clearSearchBtn: document.getElementById("clear-search-btn"),
  camelotSvg: document.getElementById("camelot-svg"),
  setlistItems: document.getElementById("setlist-items"),
  queueBadgeCount: document.getElementById("queue-badge-count"),
  globalAudioPlayer: document.getElementById("global-preview-player"),
  
  // Modals
  trackEditModal: document.getElementById("track-edit-modal"),
  scannerModal: document.getElementById("scanner-modal"),
  modalTitle: document.getElementById("modal-title"),
  modalArtist: document.getElementById("modal-artist"),
  modalKey: document.getElementById("modal-key"),
  modalBpm: document.getElementById("modal-bpm"),
  modalGenre: document.getElementById("modal-genre"),
  inputScanFolder: document.getElementById("input-scan-folder"),
  scanFeedback: document.getElementById("scan-feedback")
};

// --- INITIALIZATION ---
document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  drawCamelotWheel();
  fetchCurrentTrack();
  fetchRecommendations();
  fetchSetlist();

  // Periodically poll Serato status and live deck track (every 3 seconds)
  setInterval(() => {
    fetchCurrentTrack(true);
  }, 3000);
});

// --- EVENT LISTENERS ---
function initEventListeners() {
  // Pitch Limit Buttons
  document.querySelectorAll("#pitch-limits .btn-tab").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#pitch-limits .btn-tab").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      appState.filters.pitch_limit = parseFloat(btn.dataset.pitch);
      fetchRecommendations();
    });
  });

  // Tempo Direction Buttons
  document.querySelectorAll("#tempo-direction .btn-tab").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#tempo-direction .btn-tab").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      appState.filters.tempo_direction = btn.dataset.dir;
      fetchRecommendations();
    });
  });

  // Harmonic Goal Buttons
  document.querySelectorAll("#harmonic-goals .btn-tab").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#harmonic-goals .btn-tab").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      appState.filters.harmonic_filter = btn.dataset.goal;
      fetchRecommendations();
    });
  });

  // Source Buttons
  document.querySelectorAll("#track-source .btn-tab").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#track-source .btn-tab").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      appState.filters.source = btn.dataset.source;
      fetchRecommendations();
    });
  });

  // Genre Search Input with Debounce
  let debounceTimer;
  el.genreSearchInput.addEventListener("input", (e) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      appState.filters.genre_filter = e.target.value.trim();
      fetchRecommendations();
    }, 250);
  });

  el.clearSearchBtn.addEventListener("click", () => {
    el.genreSearchInput.value = "";
    appState.filters.genre_filter = "";
    fetchRecommendations();
  });

  document.getElementById("btn-reset-filters").addEventListener("click", () => {
    appState.filters = {
      pitch_limit: 8.0,
      tempo_direction: "all",
      harmonic_filter: "all",
      source: "all",
      genre_filter: ""
    };
    resetFilterButtonsUI();
    fetchRecommendations();
  });

  // Serato Sync Button
  document.getElementById("btn-sync-serato").addEventListener("click", () => {
    fetchCurrentTrack(false);
  });

  // Edit Current Track Modal
  document.getElementById("btn-edit-current").addEventListener("click", () => {
    el.modalTitle.value = appState.currentTrack.title;
    el.modalArtist.value = appState.currentTrack.artist;
    el.modalKey.value = appState.currentTrack.key;
    el.modalBpm.value = appState.currentTrack.bpm;
    el.modalGenre.value = appState.currentTrack.genre || "House";
    el.trackEditModal.style.display = "flex";
  });

  document.getElementById("close-modal-btn").addEventListener("click", () => {
    el.trackEditModal.style.display = "none";
  });

  document.getElementById("btn-save-current-track").addEventListener("click", () => {
    saveCurrentTrackFromModal();
  });

  // Quick Presets in Modal
  document.querySelectorAll(".chip-preset").forEach(chip => {
    chip.addEventListener("click", () => {
      el.modalTitle.value = chip.dataset.title;
      el.modalArtist.value = chip.dataset.artist;
      el.modalKey.value = chip.dataset.key;
      el.modalBpm.value = chip.dataset.bpm;
      el.modalGenre.value = chip.dataset.genre;
      saveCurrentTrackFromModal();
    });
  });

  // Local Scanner Modal
  document.getElementById("btn-open-scanner").addEventListener("click", () => {
    // Show macOS or universal folder example
    if (!el.inputScanFolder.value) {
      el.inputScanFolder.value = "~/Music";
    }
    el.scannerModal.style.display = "flex";
  });

  document.getElementById("close-scanner-btn").addEventListener("click", () => {
    el.scannerModal.style.display = "none";
  });

  document.getElementById("btn-execute-scan").addEventListener("click", executeFolderScan);

  // Setlist Queue Actions
  document.getElementById("btn-clear-queue").addEventListener("click", clearSetlist);

  // Global Audio Player Ended Event
  el.globalAudioPlayer.addEventListener("ended", () => {
    appState.currentlyPlayingPreviewId = null;
    updatePreviewButtonsUI();
  });
}

function resetFilterButtonsUI() {
  document.querySelectorAll("#pitch-limits .btn-tab").forEach(b => {
    b.classList.toggle("active", b.dataset.pitch === "8.0");
  });
  document.querySelectorAll("#tempo-direction .btn-tab").forEach(b => {
    b.classList.toggle("active", b.dataset.dir === "all");
  });
  document.querySelectorAll("#harmonic-goals .btn-tab").forEach(b => {
    b.classList.toggle("active", b.dataset.goal === "all");
  });
  document.querySelectorAll("#track-source .btn-tab").forEach(b => {
    b.classList.toggle("active", b.dataset.source === "all");
  });
  el.genreSearchInput.value = "";
}

// --- API INTERACTIONS ---

async function fetchCurrentTrack(isBackground = false) {
  try {
    const res = await fetch("/api/current_track");
    if (!res.ok) return;
    const data = await res.json();
    
    // Update Serato Status Badge
    const serato = data.serato_status || {};
    if (serato.connected) {
      el.seratoStatusBadge.className = "status-pill status-connected";
      el.seratoStatusText.textContent = `Serato Connected: ${serato.last_session_file || "Live Session"}`;
    } else {
      el.seratoStatusBadge.className = "status-pill status-standby";
      el.seratoStatusText.textContent = "Serato Standby (Manual Mode)";
    }

    // Check if track changed
    const trackChanged = (
      data.title !== appState.currentTrack.title ||
      data.artist !== appState.currentTrack.artist ||
      data.key !== appState.currentTrack.key ||
      data.bpm !== appState.currentTrack.bpm
    );

    appState.currentTrack = data;
    renderCurrentTrackHUD();

    if (trackChanged || !isBackground) {
      drawCamelotWheel();
      fetchRecommendations();
    }
  } catch (err) {
    console.error("Error fetching current track:", err);
  }
}

function renderCurrentTrackHUD() {
  const t = appState.currentTrack;
  el.currentTitle.textContent = t.title || "Unknown Title";
  el.currentArtist.textContent = t.artist || "Unknown Artist";
  el.currentGenreChip.textContent = t.genre || "Electronic";
  el.currentMusicalKey.textContent = `${t.musical_key || ""} (${t.key || "8A"})`;
  el.currentKeyBadge.textContent = t.key || "8A";
  el.currentKeyBadge.style.backgroundColor = t.key_color || CAMELOT_COLORS[t.key] || "#8ac926";
  el.currentBpmVal.textContent = parseFloat(t.bpm).toFixed(1);
  el.trackSourceTag.textContent = t.source || "Deck";
}

async function fetchRecommendations() {
  const p = new URLSearchParams({
    key: appState.currentTrack.key || "8A",
    bpm: appState.currentTrack.bpm || 125.0,
    genre: appState.currentTrack.genre || "House",
    pitch_limit: appState.filters.pitch_limit,
    tempo_direction: appState.filters.tempo_direction,
    harmonic_filter: appState.filters.harmonic_filter,
    source: appState.filters.source
  });
  if (appState.filters.genre_filter) {
    p.append("genre_filter", appState.filters.genre_filter);
  }

  try {
    const res = await fetch(`/api/recommendations?${p.toString()}`);
    if (!res.ok) return;
    const data = await res.json();
    renderRecommendations(data.results || []);
    el.resultsCountBadge.textContent = `${data.total_matches || 0} Matches`;
  } catch (err) {
    console.error("Error fetching recommendations:", err);
  }
}

function renderRecommendations(tracks) {
  el.recommendationsContainer.innerHTML = "";
  
  if (!tracks || tracks.length === 0) {
    el.emptyState.style.display = "flex";
    return;
  }
  el.emptyState.style.display = "none";

  tracks.forEach(track => {
    const card = document.createElement("div");
    card.className = "track-card";

    // Match score circle styling
    const score = Math.round(track.score);
    let scoreColor = "#10b981"; // green
    if (score < 80) scoreColor = "#00f0ff"; // cyan
    if (score < 70) scoreColor = "#f59e0b"; // amber

    // Pitch fader styling
    const pitch = track.compatibility.tempo;
    const pitchStr = pitch.pitch_str;
    const pitchColor = pitch.difficulty_color || "#10b981";

    const harmonic = track.compatibility.harmonic;
    const harmonicBadge = harmonic.energy_badge || harmonic.type;
    const harmonicColor = harmonic.badge_color || "#10b981";

    const isPreviewPlaying = (appState.currentlyPlayingPreviewId === track.id);

    card.innerHTML = `
      <!-- COMPATIBILITY SCORE -->
      <div class="track-score-badge" style="border-color: ${scoreColor}; background: ${scoreColor}22; color: ${scoreColor}">
        <span>${score}</span>
        <span class="score-pct">MIX</span>
      </div>

      <!-- TRACK DETAILS -->
      <div class="track-core-details">
        <div class="track-title-row">
          <span class="rec-title" title="${escapeHtml(track.title)}">${escapeHtml(track.title)}</span>
          <span class="source-badge">${escapeHtml(track.source)}</span>
        </div>
        <div class="rec-artist">${escapeHtml(track.artist)}</div>
        <div class="rec-badges-row">
          <span class="rel-badge" style="background: ${harmonicColor}22; color: ${harmonicColor}; border: 1px solid ${harmonicColor}66;">
            ${escapeHtml(harmonicBadge)}
          </span>
          <span class="genre-tag">${escapeHtml(track.genre || "Electronic")}</span>
          ${pitch.is_half_time ? `<span class="rel-badge" style="background: #f9731622; color: #f97316; border: 1px solid #f9731666;">Half-Time Mix</span>` : ''}
          ${pitch.is_double_time ? `<span class="rel-badge" style="background: #8b5cf622; color: #8b5cf6; border: 1px solid #8b5cf666;">Double-Time Mix</span>` : ''}
        </div>
      </div>

      <!-- KEY & BPM METRICS -->
      <div class="track-metrics-summary">
        <div class="metric-item">
          <span class="key-pill" style="background: ${track.key_color || '#8ac926'};">
            ${track.key}
          </span>
        </div>
        <div class="bpm-info-group">
          <div class="bpm-target">${parseFloat(track.bpm).toFixed(1)} <span style="font-size: 10px; color: var(--text-dim)">BPM</span></div>
          <div class="pitch-slider-diff" style="color: ${pitchColor};">
            ${pitchStr} Fader
          </div>
        </div>
      </div>

      <!-- ACTIONS -->
      <div class="card-actions-group">
        ${track.preview_url ? `
          <button class="btn-play-preview ${isPreviewPlaying ? 'playing' : ''}" data-preview="${escapeHtml(track.preview_url)}" data-id="${track.id}" title="Play 30s Audio Preview">
            ${isPreviewPlaying ? '⏸' : '▶'}
          </button>
        ` : ''}
        <button class="btn-mix-into" data-title="${escapeHtml(track.title)}" data-artist="${escapeHtml(track.artist)}" data-key="${track.key}" data-bpm="${track.bpm}" data-genre="${escapeHtml(track.genre)}" title="Set as Current Deck Track to plan next blend">
          Mix In 🎧
        </button>
        <button class="btn-queue" data-track='${JSON.stringify(track).replace(/'/g, "&apos;")}' title="Add to Setlist Queue">
          + Queue
        </button>
      </div>
    `;

    // Bind event handlers
    const mixBtn = card.querySelector(".btn-mix-into");
    mixBtn.addEventListener("click", () => {
      setTrackAsCurrent({
        title: mixBtn.dataset.title,
        artist: mixBtn.dataset.artist,
        key: mixBtn.dataset.key,
        bpm: parseFloat(mixBtn.dataset.bpm),
        genre: mixBtn.dataset.genre,
        source: "Set Sequence"
      });
    });

    const queueBtn = card.querySelector(".btn-queue");
    queueBtn.addEventListener("click", () => {
      addToSetlist(JSON.parse(queueBtn.dataset.track.replace(/&apos;/g, "'")));
    });

    const playBtn = card.querySelector(".btn-play-preview");
    if (playBtn) {
      playBtn.addEventListener("click", () => {
        toggleAudioPreview(playBtn.dataset.id, playBtn.dataset.preview);
      });
    }

    el.recommendationsContainer.appendChild(card);
  });
}

function toggleAudioPreview(id, url) {
  if (appState.currentlyPlayingPreviewId === id) {
    el.globalAudioPlayer.pause();
    appState.currentlyPlayingPreviewId = null;
  } else {
    el.globalAudioPlayer.src = url;
    el.globalAudioPlayer.play().catch(e => console.warn("Preview playback error:", e));
    appState.currentlyPlayingPreviewId = id;
  }
  updatePreviewButtonsUI();
}

function updatePreviewButtonsUI() {
  document.querySelectorAll(".btn-play-preview").forEach(btn => {
    const isPlaying = (btn.dataset.id === appState.currentlyPlayingPreviewId);
    btn.classList.toggle("playing", isPlaying);
    btn.innerHTML = isPlaying ? "⏸" : "▶";
  });
}

async function setTrackAsCurrent(trackData) {
  try {
    const res = await fetch("/api/current_track", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(trackData)
    });
    if (res.ok) {
      const data = await res.json();
      appState.currentTrack = data.current_track;
      renderCurrentTrackHUD();
      drawCamelotWheel();
      fetchRecommendations();
    }
  } catch (err) {
    console.error("Error setting current track:", err);
  }
}

function saveCurrentTrackFromModal() {
  const payload = {
    title: el.modalTitle.value.trim() || "Untitled",
    artist: el.modalArtist.value.trim() || "Unknown Artist",
    key: el.modalKey.value.trim() || "8A",
    bpm: parseFloat(el.modalBpm.value) || 124.0,
    genre: el.modalGenre.value.trim() || "House",
    source: "Manual Selection"
  };
  setTrackAsCurrent(payload);
  el.trackEditModal.style.display = "none";
}

async function executeFolderScan() {
  const folder = el.inputScanFolder.value.trim();
  if (!folder) return;
  el.scanFeedback.textContent = "Scanning audio files and reading ID3 tags...";
  try {
    const res = await fetch("/api/library/scan_folder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ folder_path: folder })
    });
    const data = await res.json();
    if (res.ok) {
      el.scanFeedback.innerHTML = `✅ Scanned ${data.tracks_scanned} files.<br>Found ${data.tracks_with_key} tracks with Key/BPM metadata.<br>Total Local Library: ${data.total_local_library} tracks.`;
      setTimeout(() => {
        fetchRecommendations();
      }, 500);
    } else {
      el.scanFeedback.textContent = `❌ ${data.error || "Scan failed."}`;
    }
  } catch (err) {
    el.scanFeedback.textContent = "❌ Error connecting to backend.";
  }
}

// --- SETLIST QUEUE ---

async function fetchSetlist() {
  try {
    const res = await fetch("/api/playlist");
    if (!res.ok) return;
    const data = await res.json();
    appState.queuedSetlist = data.setlist || [];
    renderSetlist();
  } catch (e) {}
}

async function addToSetlist(track) {
  try {
    await fetch("/api/playlist/queue", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(track)
    });
    fetchSetlist();
  } catch (e) {}
}

async function clearSetlist() {
  try {
    await fetch("/api/playlist", { method: "DELETE" });
    fetchSetlist();
  } catch (e) {}
}

function renderSetlist() {
  const list = appState.queuedSetlist;
  el.queueBadgeCount.textContent = list.length;
  el.setlistItems.innerHTML = "";

  if (list.length === 0) {
    el.setlistItems.innerHTML = `<div class="empty-queue-hint">No tracks queued yet. Click "+ Queue" on any suggested track to plan your set!</div>`;
    return;
  }

  list.forEach((t, i) => {
    const item = document.createElement("div");
    item.className = "queue-item";
    item.innerHTML = `
      <div style="display:flex; align-items:center; gap:8px;">
        <span style="font-family: var(--font-mono); color: var(--neon-cyan); font-weight:700;">#${i+1}</span>
        <span class="queue-title">${escapeHtml(t.artist)} - ${escapeHtml(t.title)}</span>
      </div>
      <div style="display:flex; align-items:center; gap:6px;">
        <span class="key-pill" style="background:${t.key_color || '#8ac926'}; font-size:11px; padding:2px 6px;">${t.key}</span>
        <span style="font-family:var(--font-mono); color:#fff; font-size:11px;">${parseFloat(t.bpm).toFixed(1)}</span>
      </div>
    `;
    el.setlistItems.appendChild(item);
  });
}

// --- CAMELOT WHEEL SVG RENDERING ---

function drawCamelotWheel() {
  const svg = el.camelotSvg;
  svg.innerHTML = "";

  const currKey = appState.currentTrack.key || "8A";
  const currMatch = currKey.match(/^([1-9]|1[0-2])([AB])$/);
  const currNum = currMatch ? parseInt(currMatch[1]) : 8;
  const currMode = currMatch ? currMatch[2] : "A";

  const numSectors = 12;
  const rInnerMinor = 45;
  const rOuterMinor = 75;
  const rInnerMajor = 78;
  const rOuterMajor = 110;

  // Draw 12 Outer Sectors (B - Major) and 12 Inner Sectors (A - Minor)
  for (let i = 1; i <= 12; i++) {
    // Camelot wheel positions: 1 is at 1 o'clock, 12 at 12 o'clock
    const startAngle = ((i - 1) * 30 - 90 - 15) * (Math.PI / 180);
    const endAngle = (i * 30 - 90 - 15) * (Math.PI / 180);
    const midAngle = ((startAngle + endAngle) / 2);

    // Check relationship with current key
    const isMajorCurrent = (currMode === "B" && currNum === i);
    const isMinorCurrent = (currMode === "A" && currNum === i);

    // Outer Sector (Major / B)
    const keyB = `${i}B`;
    const pathB = createSectorPath(0, 0, rInnerMajor, rOuterMajor, startAngle, endAngle);
    const pathElemB = document.createElementNS("http://www.w3.org/2000/svg", "path");
    pathElemB.setAttribute("d", pathB);
    pathElemB.setAttribute("fill", isMajorCurrent ? "#ffffff" : CAMELOT_COLORS[keyB]);
    pathElemB.setAttribute("stroke", isMajorCurrent ? "#00f0ff" : "rgba(0,0,0,0.6)");
    pathElemB.setAttribute("stroke-width", isMajorCurrent ? "3" : "1");
    pathElemB.style.cursor = "pointer";
    pathElemB.addEventListener("click", () => onWheelSectorClicked(keyB));
    svg.appendChild(pathElemB);

    // Text B
    const textB = document.createElementNS("http://www.w3.org/2000/svg", "text");
    const txB = Math.cos(midAngle) * ((rInnerMajor + rOuterMajor) / 2);
    const tyB = Math.sin(midAngle) * ((rInnerMajor + rOuterMajor) / 2) + 4;
    textB.setAttribute("x", txB);
    textB.setAttribute("y", tyB);
    textB.setAttribute("fill", isMajorCurrent ? "#000000" : "#ffffff");
    textB.setAttribute("font-size", "10");
    textB.setAttribute("font-family", "Chakra Petch");
    textB.setAttribute("font-weight", "700");
    textB.setAttribute("text-anchor", "middle");
    textB.style.pointerEvents = "none";
    textB.textContent = keyB;
    svg.appendChild(textB);

    // Inner Sector (Minor / A)
    const keyA = `${i}A`;
    const pathA = createSectorPath(0, 0, rInnerMinor, rOuterMinor, startAngle, endAngle);
    const pathElemA = document.createElementNS("http://www.w3.org/2000/svg", "path");
    pathElemA.setAttribute("d", pathA);
    pathElemA.setAttribute("fill", isMinorCurrent ? "#ffffff" : CAMELOT_COLORS[keyA]);
    pathElemA.setAttribute("stroke", isMinorCurrent ? "#00f0ff" : "rgba(0,0,0,0.6)");
    pathElemA.setAttribute("stroke-width", isMinorCurrent ? "3" : "1");
    pathElemA.style.cursor = "pointer";
    pathElemA.addEventListener("click", () => onWheelSectorClicked(keyA));
    svg.appendChild(pathElemA);

    // Text A
    const textA = document.createElementNS("http://www.w3.org/2000/svg", "text");
    const txA = Math.cos(midAngle) * ((rInnerMinor + rOuterMinor) / 2);
    const tyA = Math.sin(midAngle) * ((rInnerMinor + rOuterMinor) / 2) + 3.5;
    textA.setAttribute("x", txA);
    textA.setAttribute("y", tyA);
    textA.setAttribute("fill", isMinorCurrent ? "#000000" : "#ffffff");
    textA.setAttribute("font-size", "9");
    textA.setAttribute("font-family", "Chakra Petch");
    textA.setAttribute("font-weight", "700");
    textA.setAttribute("text-anchor", "middle");
    textA.style.pointerEvents = "none";
    textA.textContent = keyA;
    svg.appendChild(textA);
  }

  // Center Circle
  const centerCircle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  centerCircle.setAttribute("cx", "0");
  centerCircle.setAttribute("cy", "0");
  centerCircle.setAttribute("r", "38");
  centerCircle.setAttribute("fill", "#0b0e14");
  centerCircle.setAttribute("stroke", "rgba(0, 240, 255, 0.4)");
  centerCircle.setAttribute("stroke-width", "2");
  svg.appendChild(centerCircle);

  // Center Text (Current Key)
  const centerText = document.createElementNS("http://www.w3.org/2000/svg", "text");
  centerText.setAttribute("x", "0");
  centerText.setAttribute("y", "5");
  centerText.setAttribute("fill", "#00f0ff");
  centerText.setAttribute("font-size", "15");
  centerText.setAttribute("font-family", "Chakra Petch");
  centerText.setAttribute("font-weight", "700");
  centerText.setAttribute("text-anchor", "middle");
  centerText.textContent = currKey;
  svg.appendChild(centerText);
}

function createSectorPath(cx, cy, rIn, rOut, aStart, aEnd) {
  const x1 = cx + rOut * Math.cos(aStart);
  const y1 = cy + rOut * Math.sin(aStart);
  const x2 = cx + rOut * Math.cos(aEnd);
  const y2 = cy + rOut * Math.sin(aEnd);

  const x3 = cx + rIn * Math.cos(aEnd);
  const y3 = cy + rIn * Math.sin(aEnd);
  const x4 = cx + rIn * Math.cos(aStart);
  const y4 = cy + rIn * Math.sin(aStart);

  const largeArc = (aEnd - aStart) > Math.PI ? 1 : 0;

  return `M ${x1} ${y1} A ${rOut} ${rOut} 0 ${largeArc} 1 ${x2} ${y2} L ${x3} ${y3} A ${rIn} ${rIn} 0 ${largeArc} 0 ${x4} ${y4} Z`;
}

function onWheelSectorClicked(selectedKey) {
  setTrackAsCurrent({
    title: `Key ${selectedKey} Groove`,
    artist: "Harmonic Pivot",
    key: selectedKey,
    bpm: appState.currentTrack.bpm,
    genre: appState.currentTrack.genre,
    source: "Camelot Wheel Selection"
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
