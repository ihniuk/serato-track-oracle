/**
 * Serato Track Oracle - Micro Player HUD Logic
 */

const miniState = {
  currentTrack: {},
  filterGoal: "all",
  pitchLimit: 8.0
};

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

const el = {
  title: document.getElementById("mini-current-title"),
  artist: document.getElementById("mini-current-artist"),
  key: document.getElementById("mini-current-key"),
  bpm: document.getElementById("mini-current-bpm"),
  seratoTag: document.getElementById("serato-tag"),
  countBadge: document.getElementById("mini-count-badge"),
  cardsContainer: document.getElementById("mini-cards-container"),
  btnBoost: document.getElementById("btn-toggle-boost"),
  btnFlow: document.getElementById("btn-toggle-flow")
};

document.addEventListener("DOMContentLoaded", () => {
  initMiniEvents();
  fetchMiniData();
  setInterval(() => fetchMiniData(true), 2500);
});

function initMiniEvents() {
  el.btnBoost.addEventListener("click", () => {
    if (miniState.filterGoal === "energy_boost") {
      miniState.filterGoal = "all";
      el.btnBoost.classList.remove("active");
    } else {
      miniState.filterGoal = "energy_boost";
      el.btnBoost.classList.add("active");
      el.btnFlow.classList.remove("active");
    }
    fetchMiniRecommendations();
  });

  el.btnFlow.addEventListener("click", () => {
    if (miniState.filterGoal === "harmonic") {
      miniState.filterGoal = "all";
      el.btnFlow.classList.remove("active");
    } else {
      miniState.filterGoal = "harmonic";
      el.btnFlow.classList.add("active");
      el.btnBoost.classList.remove("active");
    }
    fetchMiniRecommendations();
  });
}

async function fetchMiniData(isBackground = false) {
  try {
    const res = await fetch("/api/current_track");
    if (!res.ok) return;
    const data = await res.json();

    const changed = (
      data.title !== miniState.currentTrack.title ||
      data.artist !== miniState.currentTrack.artist ||
      data.key !== miniState.currentTrack.key ||
      data.bpm !== miniState.currentTrack.bpm
    );

    miniState.currentTrack = data;
    renderMiniDeck();

    if (changed || !isBackground) {
      fetchMiniRecommendations();
    }
  } catch (err) {
    console.error("Error fetching mini data:", err);
  }
}

function renderMiniDeck() {
  const t = miniState.currentTrack;
  el.title.textContent = t.title || "Unknown Title";
  el.title.title = t.title || "";
  el.artist.textContent = t.artist || "Unknown Artist";
  el.key.textContent = t.key || "8A";
  el.key.style.backgroundColor = CAMELOT_COLORS[t.key] || "#8ac926";
  el.bpm.textContent = parseFloat(t.bpm || 124.0).toFixed(1);

  const serato = t.serato_status || {};
  if (serato.connected) {
    el.seratoTag.textContent = "SERATO LIVE";
    el.seratoTag.style.color = "#34d399";
  } else {
    el.seratoTag.textContent = "MANUAL";
    el.seratoTag.style.color = "#fbbf24";
  }
}

async function fetchMiniRecommendations() {
  const t = miniState.currentTrack;
  const p = new URLSearchParams({
    key: t.key || "8A",
    bpm: t.bpm || 125.0,
    genre: t.genre || "House",
    pitch_limit: miniState.pitchLimit,
    harmonic_filter: miniState.filterGoal,
    source: "all"
  });

  try {
    const res = await fetch(`/api/recommendations?${p.toString()}`);
    if (!res.ok) return;
    const data = await res.json();
    renderMiniCards(data.results || []);
    el.countBadge.textContent = `${data.total_matches || 0} Matches`;
  } catch (err) {
    console.error("Error loading mini recs:", err);
  }
}

function renderMiniCards(tracks) {
  el.cardsContainer.innerHTML = "";
  // Show top 4 in micro view
  const slice = tracks.slice(0, 4);

  if (slice.length === 0) {
    el.cardsContainer.innerHTML = `<div style="text-align:center; padding:15px; font-size:11px; color:#64748b;">No matching tracks found.</div>`;
    return;
  }

  slice.forEach(tr => {
    const card = document.createElement("div");
    card.className = "mini-card";

    const score = Math.round(tr.score);
    let scoreColor = "#10b981";
    if (score < 80) scoreColor = "#00f0ff";
    if (score < 70) scoreColor = "#f59e0b";

    const pitch = tr.compatibility.tempo;
    const pitchStr = pitch.pitch_str;
    const pitchColor = pitch.difficulty_color || "#10b981";

    card.innerHTML = `
      <div class="mini-score-dot" style="border-color:${scoreColor}; color:${scoreColor}; background:${scoreColor}22;">
        ${score}
      </div>
      <div class="mini-track-info">
        <div class="mini-track-name" title="${tr.title}">${tr.title}</div>
        <div class="mini-artist-name">${tr.artist}</div>
      </div>
      <div class="mini-metric-group">
        <span class="mini-key-tag" style="background:${tr.key_color || '#8ac926'};">
          ${tr.key}
        </span>
        <span class="mini-pitch-val" style="color:${pitchColor};">
          ${pitchStr}
        </span>
      </div>
      <button class="mini-btn-mix" data-title="${tr.title}" data-artist="${tr.artist}" data-key="${tr.key}" data-bpm="${tr.bpm}" data-genre="${tr.genre}">
        Mix In 🎧
      </button>
    `;

    const mixBtn = card.querySelector(".mini-btn-mix");
    mixBtn.addEventListener("click", () => {
      setTrackAsCurrent({
        title: mixBtn.dataset.title,
        artist: mixBtn.dataset.artist,
        key: mixBtn.dataset.key,
        bpm: parseFloat(mixBtn.dataset.bpm),
        genre: mixBtn.dataset.genre,
        source: "Micro HUD Sequence"
      });
    });

    el.cardsContainer.appendChild(card);
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
      miniState.currentTrack = data.current_track;
      renderMiniDeck();
      fetchMiniRecommendations();
    }
  } catch (err) {}
}
