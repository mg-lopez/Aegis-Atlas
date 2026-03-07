const statusEl = document.getElementById("status");
const latInput = document.getElementById("lat-input");
const lonInput = document.getElementById("lon-input");
const modeSelect = document.getElementById("mode-select");
const analyzeBtn = document.getElementById("analyze-btn");
const geoBtn = document.getElementById("geo-btn");
const threatLevelEl = document.getElementById("threat-level");
const confidenceEl = document.getElementById("confidence");
const scoreEl = document.getElementById("score");
const lastUpdatedEl = document.getElementById("last-updated");
const actionTextEl = document.getElementById("action-text");
const sourcesListEl = document.getElementById("sources-list");
const rationaleListEl = document.getElementById("rationale-list");
const signalsListEl = document.getElementById("signals-list");
const watchlistNameEl = document.getElementById("watchlist-name");
const watchlistMembersEl = document.getElementById("watchlist-members");
const createWatchlistBtn = document.getElementById("create-watchlist-btn");
const scanWatchlistBtn = document.getElementById("scan-watchlist-btn");
const watchlistSelectEl = document.getElementById("watchlist-select");
const watchlistResultsEl = document.getElementById("watchlist-results");
const refreshHistoryBtn = document.getElementById("refresh-history-btn");
const historyListEl = document.getElementById("history-list");

const map = L.map("map", { zoomControl: false }).setView([20, 0], 2);
L.control.zoom({ position: "bottomright" }).addTo(map);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

let marker = L.marker([20, 0]).addTo(map);
let bboxLayer = null;

const setStatus = (msg) => {
  statusEl.textContent = msg;
};

const setList = (targetEl, items, emptyText) => {
  targetEl.innerHTML = "";
  if (!items.length) {
    const li = document.createElement("li");
    li.textContent = emptyText;
    targetEl.appendChild(li);
    return;
  }
  items.forEach((line) => {
    const li = document.createElement("li");
    li.textContent = line;
    targetEl.appendChild(li);
  });
};

const toDateLabel = (iso) => {
  try {
    return new Date(iso).toLocaleString();
  } catch (_err) {
    return "N/A";
  }
};

const updateThreatPill = (value) => {
  const normalized = (value || "none").toLowerCase();
  threatLevelEl.textContent = normalized.toUpperCase();
  threatLevelEl.className = `pill ${normalized}`;
};

const drawBbox = (bbox) => {
  if (!bbox || bbox.length !== 4) return;

  const [minLon, minLat, maxLon, maxLat] = bbox;
  const bounds = [
    [minLat, minLon],
    [maxLat, maxLon],
  ];

  if (bboxLayer) {
    map.removeLayer(bboxLayer);
  }

  bboxLayer = L.rectangle(bounds, {
    color: "#4bc9a8",
    weight: 2,
    fillOpacity: 0.08,
  }).addTo(map);
};

const renderResult = (payload) => {
  updateThreatPill(payload.threat_level);
  confidenceEl.textContent = (payload.confidence || "n/a").toUpperCase();
  scoreEl.textContent = payload.score === null || payload.score === undefined
    ? "N/A"
    : Number(payload.score).toFixed(4);
  lastUpdatedEl.textContent = toDateLabel(payload.last_updated);
  actionTextEl.textContent = payload.recommended_action || "No recommendation available.";

  const sources = payload.sources || [];
  setList(sourcesListEl, sources, "No source scenes returned.");

  const rationale = payload.rationale || [];
  setList(rationaleListEl, rationale, "No rationale emitted.");

  const signals = payload.explainability?.signals || [];
  const signalLines = signals.map((signal) => {
    const scoreText = signal.score === null || signal.score === undefined
      ? "n/a"
      : Number(signal.score).toFixed(2);
    return `${signal.key} [${signal.status}] score=${scoreText} weight=${signal.weight}`;
  });
  setList(signalsListEl, signalLines, "No signal explainability available.");

  if (payload.query) {
    const { lat, lon, bbox } = payload.query;
    marker.setLatLng([lat, lon]);
    drawBbox(bbox);
    map.fitBounds(bboxLayer.getBounds(), { padding: [20, 20] });
  }
};

const parseInputs = () => {
  const lat = Number(latInput.value);
  const lon = Number(lonInput.value);

  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    throw new Error("Enter valid latitude and longitude first.");
  }

  return {
    lat,
    lon,
    mode: modeSelect.value,
  };
};

const parseWatchlistMembers = () => {
  const lines = watchlistMembersEl.value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const members = lines.map((line) => {
    const parts = line.split(",").map((part) => part.trim());
    if (parts.length !== 3) {
      throw new Error("Each member line must be: label,lat,lon");
    }
    const [label, latRaw, lonRaw] = parts;
    const lat = Number(latRaw);
    const lon = Number(lonRaw);
    if (!label || !Number.isFinite(lat) || !Number.isFinite(lon)) {
      throw new Error(`Invalid member line: ${line}`);
    }
    return { label, lat, lon };
  });

  if (!members.length) {
    throw new Error("Enter at least one watchlist member.");
  }
  return members;
};

const fetchJson = async (url, options = {}, timeoutMs = 80000) => {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    const payload = await response.json();
    if (!response.ok || payload.ok === false) {
      throw new Error(payload.error || `Request failed (${response.status})`);
    }
    return payload;
  } catch (err) {
    if (err && err.name === "AbortError") {
      throw new Error(`Request timed out after ${Math.round(timeoutMs / 1000)}s`);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
};

const loadWatchlists = async () => {
  const payload = await fetchJson("/api/watchlists");
  const items = payload.items || [];
  watchlistSelectEl.innerHTML = "";
  if (!items.length) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "No watchlists";
    watchlistSelectEl.appendChild(opt);
    return;
  }
  items.forEach((item) => {
    const opt = document.createElement("option");
    opt.value = item.id;
    opt.textContent = `${item.name} (${(item.members || []).length} locations)`;
    watchlistSelectEl.appendChild(opt);
  });
};

const refreshHistory = async () => {
  const payload = await fetchJson("/api/history?limit=8");
  const items = payload.items || [];
  const lines = items.map((item) => {
    const ts = toDateLabel(item.created_at);
    if (item.type === "watchlist_scan") {
      return `${ts}: watchlist scan (${item.result_count} results)`;
    }
    const threat = item.alert?.threat_level || "unknown";
    return `${ts}: single analysis (${threat.toUpperCase()})`;
  });
  setList(historyListEl, lines, "No history loaded.");
};

const createWatchlist = async () => {
  let members;
  try {
    members = parseWatchlistMembers();
  } catch (err) {
    setStatus(err.message);
    return;
  }

  createWatchlistBtn.disabled = true;
  setStatus("Creating watchlist...");
  try {
    await fetchJson("/api/watchlists", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: watchlistNameEl.value.trim() || "Family Watchlist",
        members,
      }),
    });
    await loadWatchlists();
    setStatus("Watchlist created.");
  } catch (err) {
    setStatus(`Error: ${err.message}`);
  } finally {
    createWatchlistBtn.disabled = false;
  }
};

const scanWatchlist = async () => {
  const watchlistId = watchlistSelectEl.value;
  if (!watchlistId) {
    setStatus("Select a watchlist first.");
    return;
  }

  scanWatchlistBtn.disabled = true;
  setStatus("Scanning watchlist...");
  try {
    const payload = await fetchJson(`/api/watchlists/${watchlistId}/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: modeSelect.value }),
    });
    const results = payload.results || [];
    const lines = results.map((result) => {
      if (result.ok === false) {
        return `${result.member_label}: ERROR (${result.error})`;
      }
      return `${result.member_label}: ${String(result.threat_level || "none").toUpperCase()} score=${result.score}`;
    });
    setList(watchlistResultsEl, lines, "No watchlist results.");
    await refreshHistory();
    setStatus(`Watchlist scan complete (${results.length} locations).`);
  } catch (err) {
    setStatus(`Error: ${err.message}`);
  } finally {
    scanWatchlistBtn.disabled = false;
  }
};

const runAnalysis = async () => {
  let payload;
  try {
    payload = parseInputs();
  } catch (err) {
    setStatus(err.message);
    return;
  }

  analyzeBtn.disabled = true;
  setStatus(`Analyzing ${payload.lat.toFixed(4)}, ${payload.lon.toFixed(4)}...`);

  try {
    const result = await fetchJson("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }, 85000);

    renderResult(result);
    await refreshHistory();
    setStatus(`Analysis complete (${result.mode.toUpperCase()} mode).`);
  } catch (err) {
    setStatus(`Error: ${err.message}`);
  } finally {
    analyzeBtn.disabled = false;
  }
};

const useBrowserLocation = () => {
  if (!navigator.geolocation) {
    setStatus("Geolocation is not supported in this browser.");
    return;
  }

  setStatus("Fetching browser location...");
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      latInput.value = lat.toFixed(5);
      lonInput.value = lon.toFixed(5);
      marker.setLatLng([lat, lon]);
      map.setView([lat, lon], 9);
      setStatus("Location loaded. Click Analyze Risk.");
    },
    () => setStatus("Unable to read current location; enter coordinates manually."),
    { enableHighAccuracy: true, timeout: 9000 }
  );
};

map.on("click", (event) => {
  const { lat, lng } = event.latlng;
  latInput.value = lat.toFixed(5);
  lonInput.value = lng.toFixed(5);
  marker.setLatLng([lat, lng]);
  setStatus("Map point selected. Click Analyze Risk.");
});

analyzeBtn.addEventListener("click", runAnalysis);
geoBtn.addEventListener("click", useBrowserLocation);
createWatchlistBtn.addEventListener("click", createWatchlist);
scanWatchlistBtn.addEventListener("click", scanWatchlist);
refreshHistoryBtn.addEventListener("click", () => {
  refreshHistory().catch((err) => setStatus(`Error: ${err.message}`));
});

latInput.value = "37.77490";
lonInput.value = "-122.41940";
marker.setLatLng([37.7749, -122.4194]);
map.setView([37.7749, -122.4194], 8);
watchlistMembersEl.value = "Home,37.7749,-122.4194\nWork,37.7897,-122.3942";
loadWatchlists().catch(() => setStatus("Unable to load watchlists."));
refreshHistory().catch(() => setStatus("Unable to load history."));
