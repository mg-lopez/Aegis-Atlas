const THREAT_PRIORITY = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
  none: 0,
};

const LENS_UI = {
  general: {
    workspaceTitle: "Interactive operating picture",
    workspaceNote: "A balanced operating view for broad hazard triage across the selected AOI.",
    contextTitle: "Terminal Context",
    contextCopy: "What this screen is optimized to do",
    contextMetrics: [
      ["Fusion", "Satellite + geo risk"],
      ["Workflow", "Analyze, rank, act"],
      ["Output", "Customer-grade brief"],
    ],
    profileSummary: "Balanced interpretation for broad hazard triage.",
    profilePriority: "Balanced triage",
    profileMap: "Multi-layer threat field",
    profileAction: "Assess, rank, and act",
    bulletinsTitle: "Live Bulletins + News",
    bulletinsCopy: "Compact feed combining incidents, hotspots, and live headline corroboration around the active operating picture.",
    instabilityTitle: "Instability Index",
    instabilityCopy: "Aegis-derived regional instability ranking for ambient context.",
    analysisChip: "Customer-grade readout",
    analysisCopy: "The right rail stays dedicated to interpretation, trend, evidence trust, and immediate action.",
    overviewTitle: "Risk Overview",
    metricLabels: ["Threat", "Confidence", "Score", "Updated"],
    insightTitle: "AI Lens Insight",
    insightKicker: "How this matters for the current customer lens",
    panelOrderLeft: ["controls", "lens", "bulletins", "instability", "context", "presets"],
    panelOrderRight: ["analysis-banner", "insight", "mission"],
    mapDefaults: { heatmap: true, hotspots: true, incidents: true, watchlists: true, instability: true },
  },
  logistics: {
    workspaceTitle: "Route and corridor operating picture",
    workspaceNote: "Use the map to spot chokepoints, corridor pressure, and supplier continuity risk before operations shift.",
    contextTitle: "Logistics Context",
    contextCopy: "What the terminal prioritizes for route and throughput decisions",
    contextMetrics: [
      ["Priority", "Corridors + chokepoints"],
      ["Workflow", "Detect, reroute, protect"],
      ["Output", "Route continuity brief"],
    ],
    profileSummary: "Emphasizes supply chain continuity, route access, and corridor disruption.",
    profilePriority: "Throughput risk",
    profileMap: "Corridors, ports, hotspots",
    profileAction: "Protect routes and timing",
    bulletinsTitle: "Route Bulletins + News",
    bulletinsCopy: "Priority feed for corridor disruption, watchlist movement, and live headline corroboration.",
    instabilityTitle: "Corridor Instability",
    instabilityCopy: "Aegis-derived instability ranking with corridor and route emphasis.",
    analysisChip: "Route continuity brief",
    analysisCopy: "The right rail explains route exposure, corridor disruption, and what to do before delivery schedules break.",
    overviewTitle: "Route Risk Overview",
    metricLabels: ["Route Risk", "Confidence", "Impact Score", "Updated"],
    insightTitle: "AI Route Insight",
    insightKicker: "How this affects corridor continuity and delivery posture",
    panelOrderLeft: ["controls", "lens", "bulletins", "instability", "context", "presets"],
    panelOrderRight: ["analysis-banner", "insight", "mission"],
    mapDefaults: { heatmap: true, hotspots: true, incidents: true, watchlists: true, instability: true },
  },
  energy: {
    workspaceTitle: "Facility continuity operating picture",
    workspaceNote: "Use the map to inspect site exposure, access corridors, and continuity pressure around energy assets.",
    contextTitle: "Energy Context",
    contextCopy: "What the terminal prioritizes for facilities and operational resilience",
    contextMetrics: [
      ["Priority", "Facilities + access"],
      ["Workflow", "Detect, validate, secure"],
      ["Output", "Continuity brief"],
    ],
    profileSummary: "Emphasizes facility continuity, corridor exposure, and operational resilience.",
    profilePriority: "Continuity risk",
    profileMap: "Sites, access, exposure",
    profileAction: "Protect operations and uptime",
    bulletinsTitle: "Continuity Bulletins + News",
    bulletinsCopy: "Priority feed for facility pressure, access corridors, and live continuity-relevant headlines.",
    instabilityTitle: "Continuity Instability",
    instabilityCopy: "Aegis-derived instability ranking with continuity and site-access emphasis.",
    analysisChip: "Continuity brief",
    analysisCopy: "The right rail is tuned for continuity posture, corridor access, and whether a site should move toward mitigation.",
    overviewTitle: "Continuity Overview",
    metricLabels: ["Continuity", "Confidence", "Risk Score", "Updated"],
    insightTitle: "AI Continuity Insight",
    insightKicker: "How this affects facilities, access, and operating resilience",
    panelOrderLeft: ["controls", "lens", "instability", "bulletins", "presets", "context"],
    panelOrderRight: ["analysis-banner", "mission", "insight"],
    mapDefaults: { heatmap: true, hotspots: true, incidents: true, watchlists: true, instability: false },
  },
  insurance: {
    workspaceTitle: "Exposure and severity operating picture",
    workspaceNote: "Use the map to understand severity breadth, recurrence, and whether exposure is clustering into a claims-relevant zone.",
    contextTitle: "Insurance Context",
    contextCopy: "What the terminal prioritizes for severity and accumulation review",
    contextMetrics: [
      ["Priority", "Severity + breadth"],
      ["Workflow", "Detect, rate, reserve"],
      ["Output", "Exposure brief"],
    ],
    profileSummary: "Emphasizes severity, accumulation risk, and insured asset exposure.",
    profilePriority: "Accumulation watch",
    profileMap: "Affected area + recurrence",
    profileAction: "Frame severity and exposure",
    bulletinsTitle: "Exposure Bulletins + News",
    bulletinsCopy: "Priority feed for severity spread, hotspot persistence, and live exposure-relevant headlines.",
    instabilityTitle: "Exposure Instability",
    instabilityCopy: "Aegis-derived instability ranking with severity breadth emphasis.",
    analysisChip: "Exposure brief",
    analysisCopy: "The right rail frames whether severity is broadening, persisting, or clustering in a commercially relevant way.",
    overviewTitle: "Exposure Overview",
    metricLabels: ["Severity", "Confidence", "Exposure Score", "Updated"],
    insightTitle: "AI Exposure Insight",
    insightKicker: "How this affects severity trajectory and accumulation posture",
    panelOrderLeft: ["controls", "lens", "instability", "bulletins", "context", "presets"],
    panelOrderRight: ["analysis-banner", "insight", "mission"],
    mapDefaults: { heatmap: true, hotspots: true, incidents: true, watchlists: false, instability: true },
  },
  humanitarian: {
    workspaceTitle: "Access and response operating picture",
    workspaceNote: "Use the map to inspect escalation zones, access constraints, and where urgency may outrun current coverage.",
    contextTitle: "Humanitarian Context",
    contextCopy: "What the terminal prioritizes for access, urgency, and responder posture",
    contextMetrics: [
      ["Priority", "Access + urgency"],
      ["Workflow", "Detect, assess, support"],
      ["Output", "Response brief"],
    ],
    profileSummary: "Emphasizes access constraints, responder safety, and affected-population urgency.",
    profilePriority: "Access urgency",
    profileMap: "Hazard clusters + corridors",
    profileAction: "Protect responders and access",
    bulletinsTitle: "Access Bulletins + News",
    bulletinsCopy: "Priority feed for access constraints, responder posture, and live urgency-related headlines.",
    instabilityTitle: "Access Instability",
    instabilityCopy: "Aegis-derived instability ranking with access and urgency emphasis.",
    analysisChip: "Response brief",
    analysisCopy: "The right rail frames whether access is tightening, urgency is rising, and what should happen before deployment decisions.",
    overviewTitle: "Access Overview",
    metricLabels: ["Urgency", "Confidence", "Access Score", "Updated"],
    insightTitle: "AI Access Insight",
    insightKicker: "How this affects access constraints, urgency, and responder posture",
    panelOrderLeft: ["controls", "bulletins", "instability", "context", "lens", "presets"],
    panelOrderRight: ["analysis-banner", "insight", "mission"],
    mapDefaults: { heatmap: true, hotspots: true, incidents: true, watchlists: true, instability: true },
  },
  security: {
    workspaceTitle: "Escalation and posture operating picture",
    workspaceNote: "Use the map to watch instability corridors, incident clustering, and the posture implications for people and sites.",
    contextTitle: "Security Context",
    contextCopy: "What the terminal prioritizes for escalation, personnel safety, and protective posture",
    contextMetrics: [
      ["Priority", "Escalation + posture"],
      ["Workflow", "Detect, escalate, protect"],
      ["Output", "Security brief"],
    ],
    profileSummary: "Emphasizes escalation, personnel safety, and operational posture.",
    profilePriority: "Protective posture",
    profileMap: "Instability corridors + incidents",
    profileAction: "Escalate and harden posture",
    bulletinsTitle: "Escalation Bulletins + News",
    bulletinsCopy: "Priority feed for incidents, instability corridors, and live escalation headlines.",
    instabilityTitle: "Escalation Index",
    instabilityCopy: "Aegis-derived instability ranking with strike and escalation emphasis.",
    analysisChip: "Security posture brief",
    analysisCopy: "The right rail shifts toward escalation posture, protective action, and whether continuity risk is becoming personnel risk.",
    overviewTitle: "Security Posture Overview",
    metricLabels: ["Posture", "Confidence", "Threat Score", "Updated"],
    insightTitle: "AI Security Insight",
    insightKicker: "How this affects escalation, personnel safety, and protective posture",
    panelOrderLeft: ["controls", "instability", "bulletins", "context", "lens", "presets"],
    panelOrderRight: ["analysis-banner", "mission", "insight"],
    mapDefaults: { heatmap: true, hotspots: true, incidents: true, watchlists: false, instability: true },
  },
};

const LENS_LAYOUT = {
  general: {
    layoutProfile: "balanced",
    hiddenPanels: ["lens", "presets", "instability", "context", "analysis-banner", "insight"],
    hiddenDecks: ["evidence", "history"],
    hiddenAnalytics: ["health"],
    defaultDeck: "scan-brief",
    defaultAnalytics: "trend",
  },
  logistics: {
    layoutProfile: "route",
    hiddenPanels: ["lens", "presets", "instability", "context", "analysis-banner", "insight"],
    hiddenDecks: ["history", "evidence"],
    hiddenAnalytics: ["health"],
    defaultDeck: "scan-brief",
    defaultAnalytics: "watchlist",
  },
  energy: {
    layoutProfile: "continuity",
    hiddenPanels: ["lens", "presets", "instability", "context", "analysis-banner", "insight"],
    hiddenDecks: ["history", "evidence"],
    hiddenAnalytics: ["feed"],
    defaultDeck: "scan-brief",
    defaultAnalytics: "health",
  },
  insurance: {
    layoutProfile: "exposure",
    hiddenPanels: ["lens", "presets", "instability", "context", "analysis-banner", "insight"],
    hiddenDecks: ["history", "evidence"],
    hiddenAnalytics: ["watchlist"],
    defaultDeck: "scan-brief",
    defaultAnalytics: "trend",
  },
  humanitarian: {
    layoutProfile: "response",
    hiddenPanels: ["lens", "presets", "instability", "context", "analysis-banner", "insight"],
    hiddenDecks: ["history", "evidence"],
    hiddenAnalytics: ["signals"],
    defaultDeck: "scan-brief",
    defaultAnalytics: "feed",
  },
  security: {
    layoutProfile: "security",
    hiddenPanels: ["lens", "presets", "instability", "context", "analysis-banner", "insight"],
    hiddenDecks: ["history", "evidence"],
    hiddenAnalytics: ["watchlist"],
    defaultDeck: "scan-brief",
    defaultAnalytics: "instability",
  },
};

const statusEl = document.getElementById("status");
const latInput = document.getElementById("lat-input");
const lonInput = document.getElementById("lon-input");
const radiusInput = document.getElementById("radius-input");
const startDateInput = document.getElementById("start-date-input");
const endDateInput = document.getElementById("end-date-input");
const modeSelect = document.getElementById("mode-select");
const riskProfileSelect = document.getElementById("risk-profile-select");
const lensSelect = document.getElementById("lens-select");
const deepLiveCheckbox = document.getElementById("deep-live-checkbox");
const analyzeBtn = document.getElementById("analyze-btn");
const geoBtn = document.getElementById("geo-btn");
const presetChipsEl = document.getElementById("preset-chips");
const commandStatusEl = document.getElementById("command-status");
const commandSubstatusEl = document.getElementById("command-substatus");
const commandTickerEl = document.getElementById("command-ticker");
const commandLensEl = document.getElementById("command-lens");
const commandModeEl = document.getElementById("command-mode");
const commandThreatEl = document.getElementById("command-threat");
const commandIncidentsEl = document.getElementById("command-incidents");
const commandWatchlistsEl = document.getElementById("command-watchlists");
const commandRefreshEl = document.getElementById("command-refresh");
const commandAnalyzeBtn = document.getElementById("command-analyze-btn");
const commandIncidentBtn = document.getElementById("command-incident-btn");
const leftLensPanels = Array.from(document.querySelectorAll(".rail-left [data-lens-panel]"));
const rightLensPanels = Array.from(document.querySelectorAll(".rail-right [data-lens-panel]"));
const deckTabEls = Array.from(document.querySelectorAll(".deck-tab"));
const deckPanelEls = Array.from(document.querySelectorAll("[data-deck-panel]"));
const watchlistTabEls = Array.from(document.querySelectorAll(".watchlist-tab"));
const watchlistPanelEls = Array.from(document.querySelectorAll("[data-watchlist-panel]"));
const analyticsTabEls = Array.from(document.querySelectorAll(".analytics-tab"));
const analyticsChartTitleEl = document.getElementById("analytics-chart-title");
const analyticsChartSubtitleEl = document.getElementById("analytics-chart-subtitle");
const analyticsChartEl = document.getElementById("analytics-chart");
const analyticsSideTitleEl = document.getElementById("analytics-side-title");
const analyticsSideSubtitleEl = document.getElementById("analytics-side-subtitle");
const analyticsMetricsEl = document.getElementById("analytics-metrics");
const analyticsNotesEl = document.getElementById("analytics-notes");
const workspaceTitleEl = document.getElementById("workspace-title");
const workspaceNoteEl = document.getElementById("workspace-note");
const contextTitleEl = document.getElementById("context-title");
const contextCopyEl = document.getElementById("context-copy");
const contextMetric1LabelEl = document.getElementById("context-metric-1-label");
const contextMetric1ValueEl = document.getElementById("context-metric-1-value");
const contextMetric2LabelEl = document.getElementById("context-metric-2-label");
const contextMetric2ValueEl = document.getElementById("context-metric-2-value");
const contextMetric3LabelEl = document.getElementById("context-metric-3-label");
const contextMetric3ValueEl = document.getElementById("context-metric-3-value");
const lensProfileTitleEl = document.getElementById("lens-profile-title");
const lensProfileSummaryEl = document.getElementById("lens-profile-summary");
const lensProfileChipEl = document.getElementById("lens-profile-chip");
const lensProfilePriorityEl = document.getElementById("lens-profile-priority");
const lensProfileMapEl = document.getElementById("lens-profile-map");
const lensProfileActionEl = document.getElementById("lens-profile-action");
const bulletinsTitleEl = document.getElementById("bulletins-title");
const bulletinsCopyEl = document.getElementById("bulletins-copy");
const refreshBulletinsBtn = document.getElementById("refresh-bulletins-btn");
const bulletinsListEl = document.getElementById("bulletins-list");
const instabilityTitleEl = document.getElementById("instability-title");
const instabilityCopyEl = document.getElementById("instability-copy");
const refreshInstabilityBtn = document.getElementById("refresh-instability-btn");
const instabilityTopNameEl = document.getElementById("instability-top-name");
const instabilityTopBandEl = document.getElementById("instability-top-band");
const instabilityListEl = document.getElementById("instability-list");
const analysisBannerEyebrowEl = document.getElementById("analysis-banner-eyebrow");
const analysisBannerChipEl = document.getElementById("analysis-banner-chip");
const analysisBannerCopyEl = document.getElementById("analysis-banner-copy");
const overviewTitleEl = document.getElementById("overview-title");
const metricThreatLabelEl = document.getElementById("metric-threat-label");
const metricConfidenceLabelEl = document.getElementById("metric-confidence-label");
const metricScoreLabelEl = document.getElementById("metric-score-label");
const metricUpdatedLabelEl = document.getElementById("metric-updated-label");
const lensInsightTitleEl = document.getElementById("lens-insight-title");
const lensInsightKickerEl = document.getElementById("lens-insight-kicker");
const lensInsightChipEl = document.getElementById("lens-insight-chip");
const lensInsightHeadlineEl = document.getElementById("lens-insight-headline");
const lensInsightPointsEl = document.getElementById("lens-insight-points");
const lensInsightCaveatEl = document.getElementById("lens-insight-caveat");
const lensInsightActionsEl = document.getElementById("lens-insight-actions");

const threatLevelEl = document.getElementById("threat-level");
const confidenceEl = document.getElementById("confidence");
const scoreEl = document.getElementById("score");
const lastUpdatedEl = document.getElementById("last-updated");
const briefQualityEl = document.getElementById("brief-quality");
const briefHeadlineEl = document.getElementById("brief-headline");
const briefSummaryEl = document.getElementById("brief-summary");
const briefTagsEl = document.getElementById("brief-tags");
const saveIncidentBtn = document.getElementById("save-incident-btn");
const rescanAnalysisBtn = document.getElementById("rescan-analysis-btn");
const decisionPriorityEl = document.getElementById("decision-priority");
const decisionCaveatEl = document.getElementById("decision-caveat");
const incidentContextNoteEl = document.getElementById("incident-context-note");
const aiInsightHeadlineEl = document.getElementById("ai-insight-headline");
const aiInsightSummaryEl = document.getElementById("ai-insight-summary");
const aiInsightListEl = document.getElementById("ai-insight-list");
const briefModeEl = document.getElementById("brief-mode");
const briefAoiEl = document.getElementById("brief-aoi");
const briefDominantEl = document.getElementById("brief-dominant");
const briefQualityBandEl = document.getElementById("brief-quality-band");
const briefLensEl = document.getElementById("brief-lens");
const trendLabelEl = document.getElementById("trend-label");
const trendSummaryEl = document.getElementById("trend-summary");
const trendDeltaEl = document.getElementById("trend-delta");
const trendPointsEl = document.getElementById("trend-points");
const trendSparklineEl = document.getElementById("trend-sparkline");
const healthOverallEl = document.getElementById("health-overall");
const healthSummaryEl = document.getElementById("health-summary");
const healthSatelliteEl = document.getElementById("health-satellite");
const healthSatelliteDetailEl = document.getElementById("health-satellite-detail");
const healthFeedsEl = document.getElementById("health-feeds");
const healthFeedsDetailEl = document.getElementById("health-feeds-detail");
const healthCorroborationEl = document.getElementById("health-corroboration");
const healthCorroborationDetailEl = document.getElementById("health-corroboration-detail");
const healthNotesEl = document.getElementById("health-notes");
const impactsListEl = document.getElementById("impacts-list");
const nextStepsListEl = document.getElementById("next-steps-list");
const sourcesListEl = document.getElementById("sources-list");
const rationaleListEl = document.getElementById("rationale-list");
const signalsListEl = document.getElementById("signals-list");

const watchlistNameEl = document.getElementById("watchlist-name");
const watchlistMembersEl = document.getElementById("watchlist-members");
const createWatchlistBtn = document.getElementById("create-watchlist-btn");
const scanWatchlistBtn = document.getElementById("scan-watchlist-btn");
const deleteWatchlistBtn = document.getElementById("delete-watchlist-btn");
const watchlistSelectEl = document.getElementById("watchlist-select");
const watchlistAlertEmailEl = document.getElementById("watchlist-alert-email");
const watchlistAlertSmsEl = document.getElementById("watchlist-alert-sms");
const watchlistEmailEnabledEl = document.getElementById("watchlist-email-enabled");
const watchlistSmsEnabledEl = document.getElementById("watchlist-sms-enabled");
const saveWatchlistAlertsBtn = document.getElementById("save-watchlist-alerts-btn");
const watchlistSummaryEl = document.getElementById("watchlist-summary");
const watchlistHealthNoteEl = document.getElementById("watchlist-health-note");
const watchlistTopHotspotEl = document.getElementById("watchlist-top-hotspot");
const watchlistAverageScoreEl = document.getElementById("watchlist-average-score");
const watchlistBiggestRiserEl = document.getElementById("watchlist-biggest-riser");
const watchlistBiggestRiserDetailEl = document.getElementById("watchlist-biggest-riser-detail");
const watchlistPersistentHotspotEl = document.getElementById("watchlist-persistent-hotspot");
const watchlistPersistentHotspotDetailEl = document.getElementById("watchlist-persistent-hotspot-detail");
const watchlistNewlyElevatedEl = document.getElementById("watchlist-newly-elevated");
const watchlistNewlyElevatedDetailEl = document.getElementById("watchlist-newly-elevated-detail");
const watchlistResultsEl = document.getElementById("watchlist-results");

const refreshHistoryBtn = document.getElementById("refresh-history-btn");
const historyListEl = document.getElementById("history-list");
const refreshIncidentsBtn = document.getElementById("refresh-incidents-btn");
const incidentListEl = document.getElementById("incident-list");
const mapGeneratedAtEl = document.getElementById("map-generated-at");
const layerHeatmapToggleEl = document.getElementById("layer-heatmap-toggle");
const layerHotspotsToggleEl = document.getElementById("layer-hotspots-toggle");
const layerIncidentsToggleEl = document.getElementById("layer-incidents-toggle");
const layerWatchlistsToggleEl = document.getElementById("layer-watchlists-toggle");
const layerInstabilityToggleEl = document.getElementById("layer-instability-toggle");
const layerHeatmapCountEl = document.getElementById("layer-heatmap-count");
const layerHotspotsCountEl = document.getElementById("layer-hotspots-count");
const layerIncidentsCountEl = document.getElementById("layer-incidents-count");
const layerWatchlistsCountEl = document.getElementById("layer-watchlists-count");
const layerInstabilityCountEl = document.getElementById("layer-instability-count");
const mapFocusCardEl = document.getElementById("map-focus-card");
const mapFocusTitleEl = document.getElementById("map-focus-title");
const mapFocusMetaEl = document.getElementById("map-focus-meta");
const mapFocusSummaryEl = document.getElementById("map-focus-summary");

const overlayThreatEl = document.getElementById("overlay-threat");
const overlayModeEl = document.getElementById("overlay-mode");
const overlayAoiEl = document.getElementById("overlay-aoi");
const overlaySignalEl = document.getElementById("overlay-signal");

const map = L.map("map", { zoomControl: false }).setView([20, 0], 2);
L.control.zoom({ position: "bottomright" }).addTo(map);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

let marker = L.marker([20, 0]).addTo(map);
let bboxLayer = null;
let activePresetId = null;
let lastAnalysisHistoryId = null;
let currentIncidents = [];
let mapLayerSnapshot = null;
let latestAnalysisPayload = null;
let latestWatchlistPayload = null;
let latestBulletins = [];
let latestInstabilityPayload = null;
let latestOverviewPayload = null;
let activeAnalyticsTab = "trend";
let activeRequestCount = 0;
let lastStatusMessage = "Ready.";
let lastStatusTone = "neutral";
let lastStatusDetail = "Map workspace synced and awaiting analysis.";
let lastSyncAt = null;
let availablePresets = [];
let hasBootstrappedPreset = false;
let availableWatchlists = [];

const mapIntelLayers = {
  heatmap: L.layerGroup().addTo(map),
  hotspots: L.layerGroup().addTo(map),
  incidents: L.layerGroup().addTo(map),
  watchlists: L.layerGroup().addTo(map),
  instability: L.layerGroup().addTo(map),
};

const describeMode = () => {
  if (modeSelect.value !== "live") {
    return "Sample";
  }
  return deepLiveCheckbox.checked ? "Live Deep" : "Live Fast";
};

const toRelativeTime = (value) => {
  if (!value) {
    return "Awaiting sync";
  }
  const date = value instanceof Date ? value : new Date(value);
  const deltaSeconds = Math.max(0, Math.round((Date.now() - date.getTime()) / 1000));
  if (deltaSeconds < 5) {
    return "Just now";
  }
  if (deltaSeconds < 60) {
    return `${deltaSeconds}s ago`;
  }
  const deltaMinutes = Math.round(deltaSeconds / 60);
  if (deltaMinutes < 60) {
    return `${deltaMinutes}m ago`;
  }
  const deltaHours = Math.round(deltaMinutes / 60);
  if (deltaHours < 24) {
    return `${deltaHours}h ago`;
  }
  return date.toLocaleString();
};

const updateSyncStamp = () => {
  commandRefreshEl.textContent = lastSyncAt ? toRelativeTime(lastSyncAt) : "Awaiting sync";
  commandRefreshEl.title = lastSyncAt ? new Date(lastSyncAt).toLocaleString() : "No successful sync yet";
};

const markSynced = () => {
  lastSyncAt = new Date().toISOString();
  updateSyncStamp();
};

const flashElement = (element) => {
  if (!element) {
    return;
  }
  element.classList.remove("is-updating");
  void element.offsetWidth;
  element.classList.add("is-updating");
};

const setButtonBusy = (button, busy, busyLabel = "Working...") => {
  if (!button) {
    return;
  }
  if (busy && !button.dataset.idleLabel) {
    button.dataset.idleLabel = button.textContent;
  }
  if (busy) {
    button.dataset.busy = "true";
    button.textContent = busyLabel;
    return;
  }
  button.dataset.busy = "false";
  button.textContent = button.dataset.idleLabel || button.textContent;
};

const syncCommandContext = () => {
  commandLensEl.textContent = toTitle(lensSelect.value || "general");
  commandModeEl.textContent = describeMode();
  const posture = `${commandLensEl.textContent} lens • ${commandModeEl.textContent} posture`;
  commandSubstatusEl.textContent = activeRequestCount > 0
    ? `${posture} • syncing ${activeRequestCount} task${activeRequestCount === 1 ? "" : "s"}`
    : lastStatusDetail || posture;
  commandStatusEl.dataset.tone = activeRequestCount > 0 ? "loading" : lastStatusTone;
  document.body.dataset.state = activeRequestCount > 0 ? "loading" : lastStatusTone;
  updateSyncStamp();
};

const resolveVisibleTarget = (buttons, datasetKey, targetName) => {
  const visibleButtons = buttons.filter((button) => !button.hidden);
  if (!visibleButtons.length) {
    return targetName;
  }
  if (visibleButtons.some((button) => button.dataset[datasetKey] === targetName)) {
    return targetName;
  }
  return visibleButtons[0].dataset[datasetKey];
};

const setDeckTab = (targetName) => {
  const resolved = resolveVisibleTarget(deckTabEls, "deckTarget", targetName);
  deckTabEls.forEach((button) => {
    button.classList.toggle("active", !button.hidden && button.dataset.deckTarget === resolved);
  });
  deckPanelEls.forEach((panel) => {
    panel.classList.toggle("active", !panel.hidden && panel.dataset.deckPanel === resolved);
  });
};

const setWatchlistTab = (targetName) => {
  const resolved = resolveVisibleTarget(watchlistTabEls, "watchlistTarget", targetName);
  watchlistTabEls.forEach((button) => {
    button.classList.toggle("active", !button.hidden && button.dataset.watchlistTarget === resolved);
  });
  watchlistPanelEls.forEach((panel) => {
    panel.classList.toggle("active", !panel.hidden && panel.dataset.watchlistPanel === resolved);
  });
};

const setStatus = (message, tone = "neutral", detail = null) => {
  lastStatusMessage = message;
  lastStatusTone = tone;
  lastStatusDetail = detail || `${toTitle(lensSelect.value || "general")} lens • ${describeMode()} posture`;
  statusEl.textContent = message;
  statusEl.dataset.tone = tone;
  commandStatusEl.textContent = message;
  syncCommandContext();
};

const setList = (targetEl, items, emptyText) => {
  targetEl.innerHTML = "";
  if (!items.length) {
    const li = document.createElement("li");
    li.textContent = emptyText;
    targetEl.appendChild(li);
    return;
  }
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    targetEl.appendChild(li);
  });
};

const renderTags = (targetEl, items) => {
  targetEl.innerHTML = "";
  if (!items || !items.length) {
    const span = document.createElement("span");
    span.className = "tag muted-tag";
    span.textContent = "No tags";
    targetEl.appendChild(span);
    return;
  }
  items.forEach((item) => {
    const span = document.createElement("span");
    span.className = "tag";
    span.textContent = item;
    targetEl.appendChild(span);
  });
};

const toTitle = (value) => {
  const normalized = String(value || "").replace(/[_-]+/g, " ").trim();
  if (!normalized) {
    return "N/A";
  }
  return normalized.replace(/\b\w/g, (char) => char.toUpperCase());
};

const currentLensUi = () => ({
  ...(LENS_UI.general),
  ...(LENS_UI[lensSelect.value] || {}),
  ...(LENS_LAYOUT.general),
  ...(LENS_LAYOUT[lensSelect.value] || {}),
});

const setTone = (element, tone = "neutral") => {
  if (element) {
    element.dataset.tone = tone || "neutral";
  }
};

const setButtonVariant = (button, variant = "secondary") => {
  if (!button) {
    return;
  }
  button.classList.remove("primary", "secondary");
  button.classList.add(variant === "primary" ? "primary" : "secondary");
};

const applyPanelOrder = (elements, order) => {
  elements.forEach((element) => {
    const key = element.dataset.lensPanel;
    const index = order.indexOf(key);
    element.style.order = String(index === -1 ? order.length + 1 : index + 1);
  });
};

const toggleHiddenByDataset = (elements, datasetKey, hiddenKeys = []) => {
  const hiddenSet = new Set(hiddenKeys || []);
  elements.forEach((element) => {
    const key = element.dataset[datasetKey];
    element.hidden = hiddenSet.has(key);
  });
};

const renderLensInsight = (insight = null) => {
  const ui = currentLensUi();
  lensInsightTitleEl.textContent = ui.insightTitle;
  lensInsightKickerEl.textContent = ui.insightKicker;
  lensInsightChipEl.textContent = toTitle(lensSelect.value);
  lensInsightPointsEl.innerHTML = "";
  lensInsightActionsEl.innerHTML = "";

  if (!insight) {
    lensInsightHeadlineEl.textContent = "Awaiting first scan.";
    ["The AI insight block will summarize why the result matters for the active lens.", "It stays shorter and more tactical than the formal in-platform brief."]
      .forEach((item) => {
        const li = document.createElement("li");
        li.textContent = item;
        lensInsightPointsEl.appendChild(li);
      });
    lensInsightCaveatEl.textContent = "Caveat handling will appear here when evidence health is partial or degraded.";
    setTone(lensInsightCaveatEl, "neutral");
    renderTags(lensInsightActionsEl, ["Awaiting scan"]);
    return;
  }

  lensInsightHeadlineEl.textContent = insight.headline || "Lens-aware insight ready.";
  (insight.bullets || []).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    lensInsightPointsEl.appendChild(li);
  });
  lensInsightCaveatEl.textContent = insight.caveat || "No caveat emitted.";
  setTone(lensInsightCaveatEl, insight.caveat_tone || "neutral");
  renderTags(lensInsightActionsEl, insight.actions || []);
  lensInsightChipEl.textContent = `${toTitle(insight.lens_label || lensSelect.value)} • ${formatThreat(insight.threat_label || "n/a")}`;
};

const renderAiInsight = (payload = null) => {
  if (!payload) {
    aiInsightHeadlineEl.textContent = "Awaiting first scan";
    aiInsightSummaryEl.textContent = "Aegis Atlas will translate the incoming risk, signal, and evidence data into a short protective guidance block here.";
    setList(
      aiInsightListEl,
      ["Run an analysis to generate lens-aware advice and concrete protective steps."],
      "Run an analysis to generate lens-aware advice and concrete protective steps."
    );
    return;
  }

  const brief = payload.brief || {};
  const insight = payload.lens_insight || {};
  const actions = [
    ...(Array.isArray(insight.actions) ? insight.actions : []),
    ...(Array.isArray(brief.next_steps) ? brief.next_steps : []),
  ];
  const uniqueActions = [...new Set(actions.filter(Boolean))].slice(0, 4);
  aiInsightHeadlineEl.textContent = insight.headline || brief.headline || "Protective guidance ready";
  aiInsightSummaryEl.textContent = insight.caveat || brief.summary || payload.recommended_action || "Review the supporting evidence and act according to the current threat posture.";
  setList(aiInsightListEl, uniqueActions, "No protective actions returned for the current scan.");
};

const currentSelectedWatchlist = () => availableWatchlists.find((item) => item.id === watchlistSelectEl.value) || null;

const syncWatchlistActionState = () => {
  const hasSelection = Boolean(currentSelectedWatchlist());
  deleteWatchlistBtn.disabled = !hasSelection;
  saveWatchlistAlertsBtn.disabled = !hasSelection;
};

const hydrateWatchlistEditor = (watchlist = null) => {
  if (!watchlist) {
    watchlistAlertEmailEl.value = "";
    watchlistAlertSmsEl.value = "";
    watchlistEmailEnabledEl.checked = true;
    watchlistSmsEnabledEl.checked = false;
    syncWatchlistActionState();
    return;
  }

  watchlistNameEl.value = watchlist.name || "";
  watchlistMembersEl.value = (watchlist.members || [])
    .map((member) => `${member.label},${member.lat},${member.lon}`)
    .join("\n");

  const alerts = watchlist.alerts || {};
  watchlistAlertEmailEl.value = alerts.email_to || "";
  watchlistAlertSmsEl.value = alerts.sms_to || "";
  watchlistEmailEnabledEl.checked = Boolean(alerts.email_enabled ?? alerts.email_to);
  watchlistSmsEnabledEl.checked = Boolean(alerts.sms_enabled && alerts.sms_to);
  syncWatchlistActionState();
};

const renderDecisionSurface = (payload = null) => {
  if (!payload) {
    decisionPriorityEl.textContent = "Awaiting scan";
    decisionCaveatEl.textContent = "Evidence caveat pending";
    incidentContextNoteEl.textContent = "No linked incident for the current analysis context.";
    setTone(decisionPriorityEl, "neutral");
    setTone(decisionCaveatEl, "neutral");
    setTone(incidentContextNoteEl, "neutral");
    rescanAnalysisBtn.textContent = "Run Analysis";
    saveIncidentBtn.textContent = "Save as Incident";
    commandIncidentBtn.textContent = "Queue Incident";
    rescanAnalysisBtn.dataset.idleLabel = rescanAnalysisBtn.textContent;
    saveIncidentBtn.dataset.idleLabel = saveIncidentBtn.textContent;
    commandIncidentBtn.dataset.idleLabel = commandIncidentBtn.textContent;
    setButtonVariant(rescanAnalysisBtn, "primary");
    setButtonVariant(saveIncidentBtn, "secondary");
    syncIncidentButtonState();
    return;
  }

  const insight = payload.lens_insight || {};
  const incident = payload.incident_context || null;
  const health = payload.evidence_health || {};
  const threatLevel = String(payload.threat_level || "none");
  const priority = String(insight.action_priority || "review");
  const priorityLabel = {
    escalate: "Escalate immediately",
    act: "Act in current cycle",
    review: "Review and validate",
    monitor: "Monitor posture",
    watch: "Watch only",
  }[priority] || "Review and validate";
  const priorityTone = {
    escalate: "critical",
    act: "high",
    review: "watch",
    monitor: "healthy",
    watch: "neutral",
  }[priority] || threatLevel;

  decisionPriorityEl.textContent = priorityLabel;
  setTone(decisionPriorityEl, priorityTone);

  const caveatText = insight.confidence_note || insight.caveat || "Review evidence quality before acting.";
  decisionCaveatEl.textContent = caveatText;
  setTone(decisionCaveatEl, insight.caveat_tone || health.overall_label || "neutral");

  if (incident) {
    const updated = incident.updated_at ? toDateLabel(incident.updated_at) : "recently";
    incidentContextNoteEl.textContent = `Linked to open incident ${incident.title || incident.location_label || incident.id}. Last updated ${updated}.`;
    setTone(incidentContextNoteEl, "watch");
  } else {
    incidentContextNoteEl.textContent = "No linked incident for the current analysis context.";
    setTone(incidentContextNoteEl, "neutral");
  }

  if (payload.mode === "live") {
    rescanAnalysisBtn.textContent = payload.query?.deep_live ? "Rescan Deep Live" : "Rescan Live";
  } else {
    rescanAnalysisBtn.textContent = "Rescan AOI";
  }
  saveIncidentBtn.textContent = incident ? "Update Incident" : "Save as Incident";
  commandIncidentBtn.textContent = incident ? "Update Incident" : "Queue Incident";
  rescanAnalysisBtn.dataset.idleLabel = rescanAnalysisBtn.textContent;
  saveIncidentBtn.dataset.idleLabel = saveIncidentBtn.textContent;
  commandIncidentBtn.dataset.idleLabel = commandIncidentBtn.textContent;

  const shouldFavorIncident = incident || THREAT_PRIORITY[threatLevel] >= THREAT_PRIORITY.high;
  const shouldFavorRescan = !shouldFavorIncident && ["demo", "degraded", "watch"].includes(String(health.overall_label || ""));

  setButtonVariant(saveIncidentBtn, shouldFavorIncident ? "primary" : "secondary");
  setButtonVariant(rescanAnalysisBtn, shouldFavorRescan ? "primary" : "secondary");

  syncIncidentButtonState();
};

const renderBulletins = (items = []) => {
  latestBulletins = items;
  bulletinsListEl.innerHTML = "";
  if (!items.length) {
    const empty = document.createElement("article");
    empty.className = "bulletin-empty";
    empty.textContent = "No bulletins yet.";
    bulletinsListEl.appendChild(empty);
    commandTickerEl.textContent = "No elevated bulletins in the current operating picture.";
    return;
  }

  commandTickerEl.textContent = items
    .slice(0, 3)
    .map((item) => `${formatThreat(item.severity)} ${item.title}`)
    .join("  |  ");

  items.forEach((item) => {
    const kind = item.kind || "operational";
    const sourceLabel = kind === "news"
      ? "Live news"
      : toTitle(item.source || "feed");
    const action = item.url
      ? `<a class="bulletin-link" href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">Open</a>`
      : `<button class="bulletin-focus-btn" type="button">Focus</button>`;
    const article = document.createElement("article");
    article.className = "bulletin-card";
    article.dataset.severity = item.severity || "medium";
    article.dataset.kind = kind;
    article.dataset.lat = item.lat ?? "";
    article.dataset.lon = item.lon ?? "";
    article.dataset.radiusKm = item.radius_km ?? "";
    if (item.lens) {
      article.dataset.lens = item.lens;
    }
    article.innerHTML = `
      <div class="bulletin-head">
        <span class="incident-chip">${escapeHtml(formatThreat(item.severity || "info"))}</span>
        <span class="bulletin-time">${escapeHtml(toDateLabel(item.created_at))}</span>
      </div>
      <h3>${escapeHtml(item.title || "Bulletin")}</h3>
      <p>${escapeHtml(item.summary || "No bulletin detail available.")}</p>
      <div class="bulletin-foot">
        <span>${escapeHtml(sourceLabel)}</span>
        ${action}
      </div>
    `;
    bulletinsListEl.appendChild(article);
  });
  refreshAnalytics();
};

const renderInstability = (payload) => {
  latestInstabilityPayload = payload;
  const items = (payload && payload.items) || [];
  instabilityListEl.innerHTML = "";
  const topItem = payload && payload.top_item ? payload.top_item : items[0];
  instabilityTopNameEl.textContent = topItem ? topItem.name : "N/A";
  instabilityTopBandEl.textContent = topItem ? toTitle(topItem.band || "n/a") : "N/A";

  if (!items.length) {
    const empty = document.createElement("article");
    empty.className = "incident-empty";
    empty.textContent = "No instability ranking loaded.";
    instabilityListEl.appendChild(empty);
    return;
  }

  items.forEach((item) => {
    const article = document.createElement("article");
    article.className = "instability-card";
    article.dataset.band = item.band || "watch";
    article.dataset.lat = item.lat ?? "";
    article.dataset.lon = item.lon ?? "";
    article.dataset.radiusKm = item.radius_km ?? "";
    article.innerHTML = `
      <div class="bulletin-head">
        <span class="incident-chip">${escapeHtml(toTitle(item.band || "n/a"))}</span>
        <span class="bulletin-time">Score ${escapeHtml(formatScore(item.score, 2))}</span>
      </div>
      <h3>${escapeHtml(item.name || "Instability zone")}</h3>
      <p>${escapeHtml(item.reason || "No regional context available.")}</p>
    `;
    instabilityListEl.appendChild(article);
  });
  refreshAnalytics();
};

const applyOverview = (payload) => {
  latestOverviewPayload = payload;
  if (!payload) {
    return;
  }
  const counts = payload.counts || {};
  commandIncidentsEl.textContent = String(counts.open_incidents || 0);
  commandWatchlistsEl.textContent = String(counts.watchlists || 0);
  flashElement(commandIncidentsEl.closest(".command-metric"));
  flashElement(commandWatchlistsEl.closest(".command-metric"));
  refreshAnalytics();
};

const applyLensExperience = ({ resetMapDefaults = false } = {}) => {
  const ui = currentLensUi();
  document.body.dataset.lens = lensSelect.value || "general";
  document.body.dataset.layout = "stable";

  workspaceTitleEl.textContent = ui.workspaceTitle;
  workspaceNoteEl.textContent = ui.workspaceNote;
  contextTitleEl.textContent = ui.contextTitle;
  contextCopyEl.textContent = ui.contextCopy;
  [[contextMetric1LabelEl, contextMetric1ValueEl], [contextMetric2LabelEl, contextMetric2ValueEl], [contextMetric3LabelEl, contextMetric3ValueEl]]
    .forEach(([labelEl, valueEl], index) => {
      const pair = ui.contextMetrics[index] || ["Metric", "N/A"];
      labelEl.textContent = pair[0];
      valueEl.textContent = pair[1];
    });

  lensProfileTitleEl.textContent = `${toTitle(lensSelect.value)} Lens`;
  lensProfileSummaryEl.textContent = ui.profileSummary;
  lensProfileChipEl.textContent = toTitle(lensSelect.value);
  lensProfilePriorityEl.textContent = ui.profilePriority;
  lensProfileMapEl.textContent = ui.profileMap;
  lensProfileActionEl.textContent = ui.profileAction;
  bulletinsTitleEl.textContent = ui.bulletinsTitle;
  bulletinsCopyEl.textContent = ui.bulletinsCopy;
  instabilityTitleEl.textContent = ui.instabilityTitle;
  instabilityCopyEl.textContent = ui.instabilityCopy;

  analysisBannerEyebrowEl.textContent = ui.insightTitle;
  analysisBannerChipEl.textContent = ui.analysisChip;
  analysisBannerCopyEl.textContent = ui.analysisCopy;
  overviewTitleEl.textContent = ui.overviewTitle;
  [metricThreatLabelEl, metricConfidenceLabelEl, metricScoreLabelEl, metricUpdatedLabelEl]
    .forEach((element, index) => {
      element.textContent = ui.metricLabels[index];
    });

  applyPanelOrder(leftLensPanels, ui.panelOrderLeft);
  applyPanelOrder(rightLensPanels, ui.panelOrderRight);
  toggleHiddenByDataset([...leftLensPanels, ...rightLensPanels], "lensPanel", ui.hiddenPanels || []);
  toggleHiddenByDataset(deckTabEls, "deckTarget", ui.hiddenDecks || []);
  toggleHiddenByDataset(deckPanelEls, "deckPanel", ui.hiddenDecks || []);
  toggleHiddenByDataset(analyticsTabEls, "analyticsTarget", ui.hiddenAnalytics || []);
  renderLensInsight();
  setDeckTab(ui.defaultDeck || "analytics");
  setAnalyticsTab(ui.defaultAnalytics || "trend");
  refreshAnalytics();

  if (resetMapDefaults) {
    layerHeatmapToggleEl.checked = ui.mapDefaults.heatmap;
    layerHotspotsToggleEl.checked = ui.mapDefaults.hotspots;
    layerIncidentsToggleEl.checked = ui.mapDefaults.incidents;
    layerWatchlistsToggleEl.checked = ui.mapDefaults.watchlists;
    layerInstabilityToggleEl.checked = ui.mapDefaults.instability;
    syncMapLayerVisibility();
  }
};

const escapeHtml = (value) => String(value || "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll("\"", "&quot;")
  .replaceAll("'", "&#39;");

const toDateLabel = (iso) => {
  try {
    return new Date(iso).toLocaleString();
  } catch (_err) {
    return "N/A";
  }
};

const threatColor = (value) => ({
  critical: "#ff755d",
  high: "#ffac6a",
  medium: "#e8c15f",
  low: "#7bd8ae",
  none: "#7bd8ae",
}[String(value || "none").toLowerCase()] || "#7bd8ae");

const formatScore = (value, digits = 3) => (value === null || value === undefined || Number.isNaN(Number(value))
  ? "n/a"
  : Number(value).toFixed(digits));

const formatThreat = (value) => String(value || "none").toUpperCase();

const setMapFocus = ({ title, meta, summary, tone = "neutral" }) => {
  mapFocusCardEl.dataset.tone = String(tone || "neutral").toLowerCase();
  mapFocusTitleEl.textContent = title || "Global operating picture";
  mapFocusMetaEl.textContent = meta || "No hotspot selected";
  mapFocusSummaryEl.textContent = summary || "Hover or click map intelligence items to inspect them.";
};

const stageMapLocation = (item, { loadLens = false, fit = true } = {}) => {
  if (!item || !Number.isFinite(Number(item.lat)) || !Number.isFinite(Number(item.lon))) {
    return;
  }
  latInput.value = Number(item.lat).toFixed(5);
  lonInput.value = Number(item.lon).toFixed(5);
  if (Number.isFinite(Number(item.radius_km))) {
    radiusInput.value = clamp(Number(item.radius_km), 5, 250).toFixed(0);
  }
  if (loadLens && item.lens) {
    lensSelect.value = item.lens;
  }
  previewSelection({ fit });
  syncCommandContext();
};

const buildIntelTooltip = (item, chipLabel) => `
  <div class="intel-tooltip-body">
    <div class="intel-tooltip-head">
      <span>${escapeHtml(chipLabel)}</span>
      <span class="intel-tooltip-chip">${escapeHtml(formatThreat(item.threat_level || item.category || "info"))}</span>
    </div>
    <p class="intel-tooltip-title">${escapeHtml(item.label || item.name || "Untitled")}</p>
    <p class="intel-tooltip-copy">${escapeHtml(item.summary || item.reason || "No supporting detail available.")}</p>
  </div>
`;

const createIntelIcon = (variant, threatLevel) => L.divIcon({
  className: "intel-marker-shell",
  html: `<span class="intel-marker intel-marker-${variant} intel-marker-${String(threatLevel || "low").toLowerCase()}"></span>`,
  iconSize: variant === "incident" ? [22, 22] : [18, 18],
  iconAnchor: variant === "incident" ? [11, 11] : [9, 9],
});

const setAnalyticsTab = (name) => {
  activeAnalyticsTab = resolveVisibleTarget(analyticsTabEls, "analyticsTarget", name);
  analyticsTabEls.forEach((button) => {
    button.classList.toggle("active", !button.hidden && button.dataset.analyticsTarget === activeAnalyticsTab);
  });
};

const renderAnalyticsMetrics = (items = []) => {
  analyticsMetricsEl.innerHTML = "";
  if (!items.length) {
    analyticsMetricsEl.innerHTML = `
      <article class="mini-card">
        <span>Status</span>
        <strong>Awaiting data</strong>
      </article>
    `;
    return;
  }
  items.forEach((item) => {
    const article = document.createElement("article");
    article.className = "mini-card";
    article.innerHTML = `<span>${escapeHtml(item.label || "Metric")}</span><strong>${escapeHtml(item.value || "N/A")}</strong>`;
    analyticsMetricsEl.appendChild(article);
  });
};

const renderAnalyticsNotes = (items = []) => {
  analyticsNotesEl.innerHTML = "";
  if (!items.length) {
    const li = document.createElement("li");
    li.textContent = "Run analysis, scan a watchlist, or wait for live context to populate the strip.";
    analyticsNotesEl.appendChild(li);
    return;
  }
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    analyticsNotesEl.appendChild(li);
  });
};

const renderEmptyAnalytics = (title, subtitle, note) => {
  analyticsChartTitleEl.textContent = title;
  analyticsChartSubtitleEl.textContent = subtitle;
  analyticsSideTitleEl.textContent = "Key Metrics";
  analyticsSideSubtitleEl.textContent = "Selected analytics context will appear here.";
  analyticsChartEl.className = "analytics-chart-shell analytics-chart-empty";
  analyticsChartEl.textContent = note;
  renderAnalyticsMetrics([]);
  renderAnalyticsNotes([note]);
};

const createSvg = (width, height, className = "analytics-svg") => {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("class", className);
  return svg;
};

const renderLineAreaChart = (values, { stroke = "#d8b55b", fill = "rgba(216, 181, 91, 0.16)" } = {}) => {
  const width = 640;
  const height = 220;
  const padding = 18;
  const svg = createSvg(width, height);
  if (!values.length) {
    return svg;
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = Math.max(0.001, max - min);
  const points = values.map((value, index) => {
    const x = padding + ((width - padding * 2) * index) / Math.max(1, values.length - 1);
    const y = height - padding - (((value - min) / span) * (height - padding * 2));
    return [x, y];
  });
  const pointString = points.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const area = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
  const firstX = points[0][0];
  const lastX = points[points.length - 1][0];
  area.setAttribute(
    "points",
    `${firstX.toFixed(1)},${(height - padding).toFixed(1)} ${pointString} ${lastX.toFixed(1)},${(height - padding).toFixed(1)}`
  );
  area.setAttribute("fill", fill);
  svg.appendChild(area);
  const line = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  line.setAttribute("points", pointString);
  line.setAttribute("fill", "none");
  line.setAttribute("stroke", stroke);
  line.setAttribute("stroke-width", "3");
  line.setAttribute("stroke-linecap", "round");
  line.setAttribute("stroke-linejoin", "round");
  svg.appendChild(line);
  return svg;
};

const renderBarChart = (items, { color = "#79d3c0", background = "rgba(255,255,255,0.05)", formatter = (item) => formatScore(item.value, 2) } = {}) => {
  const width = 640;
  const rowHeight = 30;
  const gap = 12;
  const height = Math.max(140, 26 + (items.length * (rowHeight + gap)));
  const svg = createSvg(width, height);
  const max = Math.max(0.001, ...items.map((item) => Number(item.value || 0)));
  items.forEach((item, index) => {
    const y = 18 + (index * (rowHeight + gap));
    const track = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    track.setAttribute("x", "170");
    track.setAttribute("y", String(y));
    track.setAttribute("width", "420");
    track.setAttribute("height", String(rowHeight));
    track.setAttribute("rx", "8");
    track.setAttribute("fill", background);
    svg.appendChild(track);

    const bar = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    bar.setAttribute("x", "170");
    bar.setAttribute("y", String(y));
    bar.setAttribute("width", String((420 * Number(item.value || 0)) / max));
    bar.setAttribute("height", String(rowHeight));
    bar.setAttribute("rx", "8");
    bar.setAttribute("fill", color);
    svg.appendChild(bar);

    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", "10");
    label.setAttribute("y", String(y + 20));
    label.setAttribute("fill", "#eef6f2");
    label.setAttribute("font-size", "13");
    label.setAttribute("font-family", "IBM Plex Mono, monospace");
    label.textContent = item.label;
    svg.appendChild(label);

    const value = document.createElementNS("http://www.w3.org/2000/svg", "text");
    value.setAttribute("x", "602");
    value.setAttribute("y", String(y + 20));
    value.setAttribute("text-anchor", "end");
    value.setAttribute("fill", "#8aa4a1");
    value.setAttribute("font-size", "12");
    value.setAttribute("font-family", "IBM Plex Mono, monospace");
    value.textContent = formatter(item);
    svg.appendChild(value);
  });
  return svg;
};

const renderMatrixChart = (items) => {
  const width = 640;
  const height = 220;
  const svg = createSvg(width, height);
  const size = 70;
  const gap = 18;
  const startX = 30;
  const startY = 28;
  items.slice(0, 6).forEach((item, index) => {
    const x = startX + ((size + gap) * (index % 3));
    const y = startY + ((size + gap) * Math.floor(index / 3));
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", String(x));
    rect.setAttribute("y", String(y));
    rect.setAttribute("width", String(size));
    rect.setAttribute("height", String(size));
    rect.setAttribute("rx", "12");
    rect.setAttribute("fill", threatColor(item.threat_level || "none"));
    rect.setAttribute("fill-opacity", String(clamp(0.3 + (Number(item.score || 0) * 0.7), 0.3, 1)));
    svg.appendChild(rect);

    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", String(x + 10));
    label.setAttribute("y", String(y + 22));
    label.setAttribute("fill", "#081118");
    label.setAttribute("font-size", "12");
    label.setAttribute("font-family", "IBM Plex Mono, monospace");
    label.textContent = item.label.slice(0, 10);
    svg.appendChild(label);

    const value = document.createElementNS("http://www.w3.org/2000/svg", "text");
    value.setAttribute("x", String(x + 10));
    value.setAttribute("y", String(y + 48));
    value.setAttribute("fill", "#081118");
    value.setAttribute("font-size", "15");
    value.setAttribute("font-family", "IBM Plex Mono, monospace");
    value.textContent = formatThreat(item.threat_level || "none");
    svg.appendChild(value);
  });
  return svg;
};

const hoursAgo = (iso) => {
  try {
    return Math.max(0, (Date.now() - new Date(iso).getTime()) / 3600000);
  } catch (_err) {
    return null;
  }
};

const refreshAnalytics = () => {
  analyticsChartEl.innerHTML = "";
  analyticsChartEl.className = "analytics-chart-shell";

  if (activeAnalyticsTab === "trend") {
    const trend = latestAnalysisPayload && latestAnalysisPayload.trend ? latestAnalysisPayload.trend : null;
    if (!trend || !(trend.sparkline || []).length) {
      renderEmptyAnalytics("Trend trajectory", "Need repeated scans to show movement.", "Run at least two scans on the same AOI to populate trend analytics.");
      return;
    }
    analyticsChartTitleEl.textContent = "Trend trajectory";
    analyticsChartSubtitleEl.textContent = trend.summary || "Recent movement across repeated scans.";
    analyticsSideTitleEl.textContent = "Trend Metrics";
    analyticsSideSubtitleEl.textContent = "Direction, delta, and scan density.";
    analyticsChartEl.appendChild(renderLineAreaChart(trend.sparkline, { stroke: "#d8b55b", fill: "rgba(216, 181, 91, 0.16)" }));
    renderAnalyticsMetrics([
      { label: "Trend", value: toTitle(trend.trend_label || "n/a") },
      { label: "Delta", value: typeof trend.delta_score === "number" ? trend.delta_score.toFixed(3) : "N/A" },
      { label: "Scans", value: String(trend.point_count || 0) },
    ]);
    renderAnalyticsNotes([trend.summary || "Trend summary unavailable.", "Trend becomes more reliable as repeated scans accumulate under the same analysis key."]);
    return;
  }

  if (activeAnalyticsTab === "signals") {
    const signals = (((latestAnalysisPayload || {}).explainability || {}).signals || [])
      .filter((item) => item && typeof item === "object")
      .map((item) => ({
        label: toTitle(item.key || "signal"),
        value: Number(item.contribution || item.score || 0),
        note: `${item.status || "n/a"} via ${item.source || "unknown"}`,
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 6);
    if (!signals.length) {
      renderEmptyAnalytics("Signal contribution", "No explainability signals are available yet.", "Run a scan with explainability data to populate signal contribution analytics.");
      return;
    }
    analyticsChartTitleEl.textContent = "Signal contribution";
    analyticsChartSubtitleEl.textContent = "Relative contribution of the strongest explainability signals.";
    analyticsSideTitleEl.textContent = "Signal Metrics";
    analyticsSideSubtitleEl.textContent = "Top weighted drivers in the current result.";
    analyticsChartEl.appendChild(renderBarChart(signals, { color: "#79d3c0" }));
    renderAnalyticsMetrics([
      { label: "Top Driver", value: signals[0].label },
      { label: "Signals", value: String(signals.length) },
      { label: "Lens", value: toTitle(lensSelect.value) },
    ]);
    renderAnalyticsNotes(signals.slice(0, 3).map((item) => `${item.label}: ${item.note}`));
    return;
  }

  if (activeAnalyticsTab === "health") {
    const health = latestAnalysisPayload && latestAnalysisPayload.evidence_health ? latestAnalysisPayload.evidence_health : null;
    if (!health) {
      renderEmptyAnalytics("Evidence health", "Health analytics appear after a scan completes.", "Run a scan to populate coverage, consensus, and feed-health analytics.");
      return;
    }
    const items = [
      { label: "Coverage", value: Number((health.coverage || {}).value || 0) },
      { label: "Consensus", value: Number((health.consensus || {}).value || 0) },
      { label: "Confidence", value: Number(latestAnalysisPayload.confidence_score || 0) },
    ];
    analyticsChartTitleEl.textContent = "Evidence health";
    analyticsChartSubtitleEl.textContent = health.summary || "Coverage, consensus, and confidence posture.";
    analyticsSideTitleEl.textContent = "Health Metrics";
    analyticsSideSubtitleEl.textContent = "Evidence quality and source posture.";
    analyticsChartEl.appendChild(renderBarChart(items, { color: "#8cc4ff", formatter: (item) => formatScore(item.value, 2) }));
    renderAnalyticsMetrics([
      { label: "Overall", value: toTitle(health.overall_label || "n/a") },
      { label: "Satellite", value: toTitle((health.satellite || {}).label || "n/a") },
      { label: "Feeds", value: toTitle((health.external_feeds || {}).label || "n/a") },
    ]);
    renderAnalyticsNotes((health.notes || []).slice(0, 3));
    return;
  }

  if (activeAnalyticsTab === "instability") {
    const items = (latestInstabilityPayload && latestInstabilityPayload.items) || [];
    if (!items.length) {
      renderEmptyAnalytics("Instability ranking", "Instability analytics are waiting on live context.", "Refresh the instability index or wait for the ambient context poll.");
      return;
    }
    const bars = items.slice(0, 6).map((item) => ({ label: item.name, value: Number(item.score || 0), note: item.reason }));
    analyticsChartTitleEl.textContent = "Instability ranking";
    analyticsChartSubtitleEl.textContent = "Aegis-derived regional instability ranking for the active lens.";
    analyticsSideTitleEl.textContent = "Instability Metrics";
    analyticsSideSubtitleEl.textContent = "Highest-ranked regions in the current ambient model.";
    analyticsChartEl.appendChild(renderBarChart(bars, { color: "#56b7cf" }));
    renderAnalyticsMetrics([
      { label: "Top Region", value: items[0].name },
      { label: "Band", value: toTitle(items[0].band || "n/a") },
      { label: "Lens", value: toTitle(latestInstabilityPayload.lens || lensSelect.value) },
    ]);
    renderAnalyticsNotes(items.slice(0, 3).map((item) => item.reason || `${item.name} remains elevated.`));
    return;
  }

  if (activeAnalyticsTab === "feed") {
    const bulletins = latestBulletins || [];
    if (!bulletins.length) {
      renderEmptyAnalytics("Feed velocity", "The feed timeline populates from ambient bulletins.", "Wait for bulletins to load or refresh the live context modules.");
      return;
    }
    const buckets = [
      { label: "0-1h", value: 0 },
      { label: "1-6h", value: 0 },
      { label: "6-24h", value: 0 },
      { label: "24h+", value: 0 },
    ];
    bulletins.forEach((item) => {
      const hours = hoursAgo(item.created_at);
      if (hours === null) {
        buckets[3].value += 1;
      } else if (hours <= 1) {
        buckets[0].value += 1;
      } else if (hours <= 6) {
        buckets[1].value += 1;
      } else if (hours <= 24) {
        buckets[2].value += 1;
      } else {
        buckets[3].value += 1;
      }
    });
    analyticsChartTitleEl.textContent = "Feed velocity";
    analyticsChartSubtitleEl.textContent = "Recency distribution across the current bulletin stream.";
    analyticsSideTitleEl.textContent = "Feed Metrics";
    analyticsSideSubtitleEl.textContent = "Severity and freshness across live bulletins.";
    analyticsChartEl.appendChild(renderBarChart(buckets, { color: "#f0a63a", formatter: (item) => String(item.value) }));
    renderAnalyticsMetrics([
      { label: "Bulletins", value: String(bulletins.length) },
      { label: "Top Severity", value: formatThreat(bulletins[0].severity || "n/a") },
      { label: "Lead Item", value: (bulletins[0].title || "N/A").slice(0, 18) },
    ]);
    renderAnalyticsNotes(bulletins.slice(0, 3).map((item) => `${formatThreat(item.severity)} ${item.title}`));
    return;
  }

  if (activeAnalyticsTab === "watchlist") {
    const results = (((latestWatchlistPayload || {}).results) || [])
      .filter((item) => item.ok !== false)
      .map((item) => ({ label: item.member_label || "member", threat_level: item.threat_level, score: Number(item.score || 0) }))
      .sort((a, b) => THREAT_PRIORITY[b.threat_level || "none"] - THREAT_PRIORITY[a.threat_level || "none"] || b.score - a.score);
    if (!results.length) {
      renderEmptyAnalytics("Watchlist matrix", "Scan a watchlist to compare member posture visually.", "Watchlist analytics activate after a scan returns location-level results.");
      return;
    }
    const summary = (latestWatchlistPayload && latestWatchlistPayload.summary) || {};
    analyticsChartTitleEl.textContent = "Watchlist matrix";
    analyticsChartSubtitleEl.textContent = summary.summary || "Comparative posture across the latest watchlist scan.";
    analyticsSideTitleEl.textContent = "Watchlist Metrics";
    analyticsSideSubtitleEl.textContent = "Hotspot concentration and scan spread.";
    analyticsChartEl.appendChild(renderMatrixChart(results));
    renderAnalyticsMetrics([
      { label: "Top Hotspot", value: summary.top_hotspot ? summary.top_hotspot.member_label : "None" },
      { label: "Average", value: formatScore(summary.average_score || 0, 3) },
      { label: "Members", value: String(results.length) },
    ]);
    renderAnalyticsNotes(results.slice(0, 3).map((item) => `${item.label}: ${formatThreat(item.threat_level)} at ${formatScore(item.score, 3)}`));
  }
};

const syncMapLayerVisibility = () => {
  const visibility = [
    ["heatmap", layerHeatmapToggleEl.checked],
    ["hotspots", layerHotspotsToggleEl.checked],
    ["incidents", layerIncidentsToggleEl.checked],
    ["watchlists", layerWatchlistsToggleEl.checked],
    ["instability", layerInstabilityToggleEl.checked],
  ];
  visibility.forEach(([name, enabled]) => {
    const layer = mapIntelLayers[name];
    if (enabled && !map.hasLayer(layer)) {
      layer.addTo(map);
    }
    if (!enabled && map.hasLayer(layer)) {
      map.removeLayer(layer);
    }
  });
};

const updateThreatPill = (value) => {
  const normalized = (value || "none").toLowerCase();
  threatLevelEl.textContent = normalized.toUpperCase();
  threatLevelEl.className = `pill ${normalized}`;
  overlayThreatEl.textContent = normalized.toUpperCase();
  commandThreatEl.textContent = normalized.toUpperCase();
};

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

const bboxFromPoint = (lat, lon, radiusKm) => {
  const latDelta = radiusKm / 111;
  const cosLat = Math.max(0.1, Math.cos((lat * Math.PI) / 180));
  const lonDelta = radiusKm / (111 * cosLat);
  return [
    clamp(lon - lonDelta, -180, 180),
    clamp(lat - latDelta, -90, 90),
    clamp(lon + lonDelta, -180, 180),
    clamp(lat + latDelta, -90, 90),
  ];
};

const drawBbox = (bbox) => {
  if (!bbox || bbox.length !== 4) {
    return;
  }
  const [minLon, minLat, maxLon, maxLat] = bbox;
  const bounds = [
    [minLat, minLon],
    [maxLat, maxLon],
  ];
  if (bboxLayer) {
    map.removeLayer(bboxLayer);
  }
  bboxLayer = L.rectangle(bounds, {
    color: "#d8b55b",
    weight: 2,
    fillOpacity: 0.07,
  }).addTo(map);
};

const previewSelection = ({ fit = false } = {}) => {
  const lat = Number(latInput.value);
  const lon = Number(lonInput.value);
  const radiusKm = Number(radiusInput.value || 25);
  if (!Number.isFinite(lat) || !Number.isFinite(lon) || !Number.isFinite(radiusKm)) {
    return;
  }
  const bbox = bboxFromPoint(lat, lon, clamp(radiusKm, 5, 250));
  marker.setLatLng([lat, lon]);
  drawBbox(bbox);
  overlayAoiEl.textContent = `${clamp(radiusKm, 5, 250).toFixed(0)} km radius`;
  if (fit && bboxLayer) {
    map.fitBounds(bboxLayer.getBounds(), { padding: [24, 24] });
  }
};

const clearMapIntelLayers = () => {
  Object.values(mapIntelLayers).forEach((layer) => layer.clearLayers());
};

const renderMapLayers = (payload) => {
  mapLayerSnapshot = payload || null;
  clearMapIntelLayers();

  const counts = (payload && payload.counts) || {};
  layerHeatmapCountEl.textContent = String(counts.heatmap_points || 0);
  layerHotspotsCountEl.textContent = String(counts.hotspot_markers || 0);
  layerIncidentsCountEl.textContent = String(counts.incident_markers || 0);
  layerWatchlistsCountEl.textContent = String(counts.watchlist_markers || 0);
  layerInstabilityCountEl.textContent = String(counts.instability_points || 0);
  mapGeneratedAtEl.textContent = payload && payload.generated_at
    ? `Updated ${toDateLabel(payload.generated_at)}`
    : "Awaiting refresh";

  const instabilityPoints = (payload && payload.instability_points) || [];
  instabilityPoints.forEach((point) => {
    const color = point.category === "strike-risk" ? "#ff755d" : "#56b7cf";
    const circle = L.circle([point.lat, point.lon], {
      radius: Number(point.radius_km || 200) * 1000,
      color,
      weight: 1.2,
      opacity: 0.4,
      dashArray: "8 8",
      fillColor: color,
      fillOpacity: 0.04 + (Number(point.score || 0) * 0.08),
      interactive: true,
    });
    circle.bindTooltip(buildIntelTooltip(point, point.category === "strike-risk" ? "Strike risk" : "Instability"), {
      className: "intel-tooltip",
      sticky: true,
      direction: "top",
      opacity: 0.98,
    });
    circle.on("mouseover", () => {
      setMapFocus({
        title: point.name,
        meta: `${toTitle(point.category || "instability")} corridor`,
        summary: point.reason || "Regional instability context layer.",
        tone: point.score >= 0.85 ? "high" : "medium",
      });
    });
    mapIntelLayers.instability.addLayer(circle);
  });

  const heatmapPoints = (payload && payload.heatmap_points) || [];
  heatmapPoints.forEach((point) => {
    const color = threatColor(point.threat_level);
    const circle = L.circle([point.lat, point.lon], {
      radius: clamp(Number(point.radius_km || 25) * 1000, 8000, 160000),
      color,
      weight: 1,
      opacity: 0.18,
      fillColor: color,
      fillOpacity: clamp(0.08 + (Number(point.intensity || 0.2) * 0.22), 0.08, 0.34),
      interactive: true,
    });
    circle.bindTooltip(buildIntelTooltip(point, `${toTitle(point.source_type || "analysis")} field`), {
      className: "intel-tooltip",
      sticky: true,
      direction: "top",
      opacity: 0.98,
    });
    circle.on("mouseover", () => {
      setMapFocus({
        title: point.label || "Threat field",
        meta: `${formatThreat(point.threat_level)} • Score ${formatScore(point.score)} • ${toTitle(point.source_type)}`,
        summary: point.summary || "Threat field hotspot.",
        tone: point.threat_level || "neutral",
      });
    });
    circle.on("click", () => {
      stageMapLocation(point, { loadLens: true, fit: true });
      setStatus(`Map focus moved to ${point.label || "selected hotspot"}.`, "neutral");
    });
    mapIntelLayers.heatmap.addLayer(circle);
  });

  const hotspotMarkers = (payload && payload.hotspot_markers) || [];
  hotspotMarkers.forEach((point) => {
    const markerLayer = L.marker([point.lat, point.lon], {
      icon: createIntelIcon("hotspot", point.threat_level),
      riseOnHover: true,
      keyboard: false,
    });
    markerLayer.bindTooltip(buildIntelTooltip(point, "Hotspot"), {
      className: "intel-tooltip",
      sticky: true,
      direction: "top",
      opacity: 0.98,
    });
    markerLayer.on("mouseover", () => {
      setMapFocus({
        title: point.label || point.member_label || "Hotspot",
        meta: `${formatThreat(point.threat_level)} • Score ${formatScore(point.score)} • ${toTitle(point.lens || payload.lens || "general")}`,
        summary: point.summary || "Elevated hotspot from recent scans.",
        tone: point.threat_level || "neutral",
      });
    });
    markerLayer.on("click", () => {
      stageMapLocation(point, { loadLens: true, fit: true });
      setDeckTab(point.source_type === "watchlist" ? "watchlists" : point.source_type === "incident" ? "incidents" : "scan-brief");
      setStatus(`Hotspot loaded: ${point.label || point.member_label || "location"}.`, "neutral");
    });
    mapIntelLayers.hotspots.addLayer(markerLayer);
  });

  const watchlistMarkers = (payload && payload.watchlist_markers) || [];
  watchlistMarkers.forEach((point) => {
    const markerLayer = L.marker([point.lat, point.lon], {
      icon: createIntelIcon("watchlist", point.threat_level),
      riseOnHover: true,
      keyboard: false,
    });
    markerLayer.bindTooltip(buildIntelTooltip(point, point.watchlist_name || "Watchlist"), {
      className: "intel-tooltip",
      sticky: true,
      direction: "top",
      opacity: 0.98,
    });
    markerLayer.on("mouseover", () => {
      setMapFocus({
        title: point.member_label || point.label || "Watchlist member",
        meta: `${point.watchlist_name || "Watchlist"} • ${formatThreat(point.threat_level)} • ${toTitle(point.lens || "general")}`,
        summary: point.summary || "Watchlist member risk summary.",
        tone: point.threat_level || "neutral",
      });
    });
    markerLayer.on("click", () => {
      stageMapLocation(point, { loadLens: true, fit: true });
      setDeckTab("watchlists");
      setStatus(`Watchlist location loaded: ${point.member_label || point.label}.`, "neutral");
    });
    mapIntelLayers.watchlists.addLayer(markerLayer);
  });

  const incidentMarkers = (payload && payload.incident_markers) || [];
  incidentMarkers.forEach((point) => {
    const markerLayer = L.marker([point.lat, point.lon], {
      icon: createIntelIcon("incident", point.threat_level),
      riseOnHover: true,
      keyboard: false,
    });
    markerLayer.bindTooltip(buildIntelTooltip(point, "Incident"), {
      className: "intel-tooltip",
      sticky: true,
      direction: "top",
      opacity: 0.98,
    });
    markerLayer.on("mouseover", () => {
      setMapFocus({
        title: point.label || "Incident",
        meta: `${formatThreat(point.threat_level)} • Trend ${toTitle(point.trend_label || "n/a")} • Health ${toTitle(point.health_label || "n/a")}`,
        summary: point.summary || "Open incident summary.",
        tone: point.threat_level || "neutral",
      });
    });
    markerLayer.on("click", () => {
      const incident = currentIncidents.find((item) => item.id === point.incident_id);
      if (incident) {
        openIncidentOnMap(incident);
        setDeckTab("incidents");
      } else {
        stageMapLocation(point, { loadLens: true, fit: true });
      }
    });
    mapIntelLayers.incidents.addLayer(markerLayer);
  });

  syncMapLayerVisibility();

  const summaryCount = Number(counts.hotspot_markers || 0);
  setMapFocus({
    title: "Global operating picture",
    meta: `${summaryCount} hotspot${summaryCount === 1 ? "" : "s"} • ${counts.incident_markers || 0} open incidents`,
    summary: `Lens context: ${toTitle((payload && payload.lens) || lensSelect.value || "general")}. Threat field blends recent analyses, watchlist scans, incident queue state, and regional instability corridors.`,
    tone: summaryCount > 0 ? "medium" : "neutral",
  });
};

const renderSparkline = (targetEl, values) => {
  targetEl.innerHTML = "";
  if (!values || values.length < 2) {
    targetEl.textContent = "No history yet.";
    targetEl.className = "sparkline-placeholder";
    return;
  }

  const width = 180;
  const height = 46;
  const padding = 4;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = Math.max(0.001, max - min);
  const points = values.map((value, index) => {
    const x = padding + ((width - padding * 2) * index) / Math.max(1, values.length - 1);
    const y = height - padding - (((value - min) / span) * (height - padding * 2));
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("class", "sparkline");

  const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  polyline.setAttribute("points", points.join(" "));
  polyline.setAttribute("fill", "none");
  polyline.setAttribute("stroke", "#d8b55b");
  polyline.setAttribute("stroke-width", "3");
  polyline.setAttribute("stroke-linecap", "round");
  polyline.setAttribute("stroke-linejoin", "round");
  svg.appendChild(polyline);

  const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  const lastPoint = points[points.length - 1].split(",");
  circle.setAttribute("cx", lastPoint[0]);
  circle.setAttribute("cy", lastPoint[1]);
  circle.setAttribute("r", "3.5");
  circle.setAttribute("fill", "#78d1c2");
  svg.appendChild(circle);

  targetEl.className = "sparkline-shell";
  targetEl.appendChild(svg);
};

const renderTrend = (trend) => {
  trendLabelEl.textContent = toTitle(trend && trend.trend_label ? trend.trend_label : "n/a");
  trendSummaryEl.textContent = trend && trend.summary ? trend.summary : "Need at least two scans to establish movement.";
  trendDeltaEl.textContent = trend && typeof trend.delta_score === "number"
    ? `${trend.delta_score >= 0 ? "+" : ""}${trend.delta_score.toFixed(3)}`
    : "N/A";
  trendPointsEl.textContent = `${trend && trend.point_count ? trend.point_count : 0} scans tracked`;
  renderSparkline(trendSparklineEl, trend && trend.sparkline ? trend.sparkline : []);
};

const setHealthTone = (targetEl, label) => {
  const normalized = String(label || "neutral").toLowerCase();
  targetEl.dataset.tone = normalized;
};

const renderEvidenceHealth = (health) => {
  const satellite = (health && health.satellite) || {};
  const feeds = (health && health.external_feeds) || {};
  const coverage = (health && health.coverage) || {};
  const consensus = (health && health.consensus) || {};
  const overallLabel = health && health.overall_label ? health.overall_label : "n/a";

  healthOverallEl.textContent = toTitle(overallLabel);
  healthSummaryEl.textContent = health && health.summary ? health.summary : "No evidence-health summary yet.";
  setHealthTone(healthOverallEl, overallLabel);

  healthSatelliteEl.textContent = satellite.label ? toTitle(satellite.label) : "N/A";
  healthSatelliteDetailEl.textContent = satellite.summary || "No satellite detail yet.";
  setHealthTone(healthSatelliteEl, satellite.label || "neutral");

  healthFeedsEl.textContent = feeds.label ? toTitle(feeds.label) : "N/A";
  healthFeedsDetailEl.textContent = feeds.summary || "No feed-health detail yet.";
  setHealthTone(healthFeedsEl, feeds.label || "neutral");

  healthCorroborationEl.textContent = `${toTitle(coverage.label || "n/a")} / ${toTitle(consensus.label || "n/a")}`;
  healthCorroborationDetailEl.textContent = `Coverage ${typeof coverage.value === "number" ? coverage.value.toFixed(2) : "n/a"} • Consensus ${typeof consensus.value === "number" ? consensus.value.toFixed(2) : "n/a"}`;
  setHealthTone(healthCorroborationEl, health && health.quality_band ? health.quality_band : "neutral");

  renderTags(healthNotesEl, (health && health.notes) || []);
};

const renderResult = (payload) => {
  latestAnalysisPayload = payload;
  lastAnalysisHistoryId = payload.history_id || null;
  syncIncidentButtonState();
  updateThreatPill(payload.threat_level);
  confidenceEl.textContent = String(payload.confidence || "n/a").toUpperCase();
  scoreEl.textContent = payload.score === null || payload.score === undefined
    ? "N/A"
    : Number(payload.score).toFixed(4);
  lastUpdatedEl.textContent = toDateLabel(payload.last_updated);

  const brief = payload.brief || {};
  briefQualityEl.textContent = `Evidence quality: ${String(brief.quality_band || "n/a").toUpperCase()}`;
  briefHeadlineEl.textContent = brief.headline || "Analysis complete";
  briefSummaryEl.textContent = brief.summary || "No summary available.";
  briefModeEl.textContent = brief.analysis_mode_label || "N/A";
  briefAoiEl.textContent = payload.query?.radius_km ? `${Number(payload.query.radius_km).toFixed(0)} km radius` : "N/A";
  briefDominantEl.textContent = brief.dominant_signal?.label || "N/A";
  briefQualityBandEl.textContent = String(brief.quality_band || "n/a").toUpperCase();
  briefLensEl.textContent = brief.lens_label || payload.lens_label || "N/A";
  renderTags(briefTagsEl, brief.customer_tags || []);
  renderLensInsight(payload.lens_insight || null);
  renderAiInsight(payload);
  renderDecisionSurface(payload);
  renderTrend(payload.trend || brief.trend || null);
  renderEvidenceHealth(payload.evidence_health || brief.evidence_health || null);
  setList(impactsListEl, brief.operational_impacts || [], "No impact summary available.");
  setList(nextStepsListEl, brief.next_steps || [], "No next steps available.");

  const sources = payload.sources || [];
  setList(sourcesListEl, sources, "No source scenes returned.");
  setList(rationaleListEl, payload.rationale || [], "No rationale emitted.");

  const signals = (payload.explainability && payload.explainability.signals) || [];
  const signalLines = signals.map((signal) => {
    const scoreText = signal.score === null || signal.score === undefined ? "n/a" : Number(signal.score).toFixed(2);
    const reliabilityText = signal.reliability === null || signal.reliability === undefined ? "n/a" : Number(signal.reliability).toFixed(2);
    return `${signal.key} [${signal.status}] score=${scoreText} reliability=${reliabilityText} ${signal.details || ""}`;
  });
  setList(signalsListEl, signalLines, "No signal explainability available.");

  overlayModeEl.textContent = payload.mode === "live"
    ? (payload.query?.deep_live ? "LIVE DEEP" : "LIVE FAST")
    : "SAMPLE";
  overlaySignalEl.textContent = brief.dominant_signal?.label || "No dominant signal";

  if (payload.query) {
    const { lat, lon, bbox, radius_km: radiusKm } = payload.query;
    latInput.value = Number(lat).toFixed(5);
    lonInput.value = Number(lon).toFixed(5);
    radiusInput.value = Number(radiusKm || 25).toFixed(0);
    marker.setLatLng([lat, lon]);
    drawBbox(bbox);
    overlayAoiEl.textContent = `${Number(radiusKm || 25).toFixed(0)} km radius`;
    if (bboxLayer) {
      map.fitBounds(bboxLayer.getBounds(), { padding: [24, 24] });
    }
  }
  refreshAnalytics();
  flashElement(document.querySelector(".analysis-banner"));
  flashElement(document.querySelector(".lens-insight-panel"));
  flashElement(document.querySelector(".mission-panel"));
};

const syncModeControls = () => {
  const liveMode = modeSelect.value === "live";
  deepLiveCheckbox.disabled = !liveMode;
  if (!liveMode) {
    deepLiveCheckbox.checked = false;
  }
};

const parseInputs = () => {
  const lat = Number(latInput.value);
  const lon = Number(lonInput.value);
  const radiusKm = Number(radiusInput.value);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    throw new Error("Enter valid latitude and longitude first.");
  }
  if (!Number.isFinite(radiusKm)) {
    throw new Error("Enter a valid AOI radius.");
  }
  return {
    lat,
    lon,
    radius_km: clamp(radiusKm, 5, 250),
    mode: modeSelect.value,
    risk_profile: riskProfileSelect.value,
    lens: lensSelect.value,
    deep_live: modeSelect.value === "live" && deepLiveCheckbox.checked,
    start_date: startDateInput.value,
    end_date: endDateInput.value,
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
  activeRequestCount += 1;
  syncCommandContext();
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    const payload = await response.json();
    if (!response.ok || payload.ok === false) {
      throw new Error(payload.error || `Request failed (${response.status})`);
    }
    markSynced();
    return payload;
  } catch (err) {
    if (err && err.name === "AbortError") {
      throw new Error(`Request timed out after ${Math.round(timeoutMs / 1000)}s`);
    }
    throw err;
  } finally {
    activeRequestCount = Math.max(0, activeRequestCount - 1);
    syncCommandContext();
    clearTimeout(timer);
  }
};

const loadMapLayers = async ({ silent = true } = {}) => {
  try {
    const payload = await fetchJson(`/api/map/layers?lens=${encodeURIComponent(lensSelect.value || "general")}`);
    renderMapLayers(payload);
    flashElement(mapFocusCardEl);
  } catch (err) {
    if (!silent) {
      setStatus(`Error: ${err.message}`, "error");
    }
  }
};

const loadBulletins = async ({ silent = true } = {}) => {
  try {
    const payload = await fetchJson(`/api/feed/bulletins?lens=${encodeURIComponent(lensSelect.value || "general")}&limit=5`);
    renderBulletins(payload.items || []);
    flashElement(bulletinsListEl.closest(".bulletins-panel, .rail-panel, .deck-panel"));
  } catch (err) {
    if (!silent) {
      setStatus(`Error: ${err.message}`, "error");
    }
  }
};

const loadInstability = async ({ silent = true } = {}) => {
  try {
    const payload = await fetchJson(`/api/instability?lens=${encodeURIComponent(lensSelect.value || "general")}&limit=6`);
    renderInstability(payload);
    flashElement(instabilityListEl.closest(".rail-panel"));
  } catch (err) {
    if (!silent) {
      setStatus(`Error: ${err.message}`, "error");
    }
  }
};

const loadOverview = async ({ silent = true } = {}) => {
  try {
    const payload = await fetchJson(`/api/dashboard/overview?lens=${encodeURIComponent(lensSelect.value || "general")}`);
    applyOverview(payload);
  } catch (err) {
    if (!silent) {
      setStatus(`Error: ${err.message}`, "error");
    }
  }
};

const loadLiveContext = async ({ silent = true } = {}) => {
  await Promise.all([
    loadOverview({ silent }),
    loadBulletins({ silent }),
    loadInstability({ silent }),
  ]);
};

const renderPresetChips = (items) => {
  presetChipsEl.innerHTML = "";
  if (!items.length) {
    const fallback = document.createElement("span");
    fallback.className = "tag muted-tag";
    fallback.textContent = "No presets available";
    presetChipsEl.appendChild(fallback);
    return;
  }
  items.forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "preset-chip";
    if (item.id === activePresetId) {
      button.classList.add("active");
    }
    if (item.featured) {
      button.classList.add("featured");
    }
    button.dataset.presetId = item.id;
    button.title = item.operator_note || item.description || item.name;
    button.innerHTML = `
      <strong>${item.name}</strong>
      <span>${item.region}</span>
      <small>${item.demo_headline || item.description}</small>
      <small>${toTitle(item.lens)} • ${formatThreat(item.threat_level || "medium")}</small>
    `;
    presetChipsEl.appendChild(button);
  });
};

const applyPreset = (preset, { initialLoad = false, autorun = false } = {}) => {
  activePresetId = preset.id;
  latInput.value = Number(preset.lat).toFixed(5);
  lonInput.value = Number(preset.lon).toFixed(5);
  radiusInput.value = Number(preset.radius_km || 25).toFixed(0);
  modeSelect.value = preset.mode || "sample";
  riskProfileSelect.value = preset.risk_profile || "balanced";
  lensSelect.value = preset.lens || "general";
  applyLensExperience({ resetMapDefaults: true });
  syncModeControls();
  if (Array.isArray(preset.watchlist_seed) && preset.watchlist_seed.length) {
    watchlistNameEl.value = preset.watchlist_name || `${preset.name} Assets`;
    watchlistMembersEl.value = preset.watchlist_seed
      .map((member) => `${member.label},${Number(member.lat).toFixed(4)},${Number(member.lon).toFixed(4)}`)
      .join("\n");
  }
  previewSelection({ fit: true });
  overlayModeEl.textContent = modeSelect.value === "live" ? "LIVE FAST" : "SAMPLE";
  syncCommandContext();
  setMapFocus({
    title: preset.name || "Featured scenario",
    meta: `${preset.region || "Scenario"} • ${toTitle(preset.lens || "general")} • ${formatThreat(preset.threat_level || "medium")}`,
    summary: preset.demo_headline || preset.description || "Featured demo scenario staged on the map.",
    tone: String(preset.threat_level || "medium").toLowerCase(),
  });
  const onboarding = initialLoad
    ? "Featured scenario staged. Press A to analyze or W to scan the seeded watchlist."
    : `Preset loaded: ${preset.name}. Press A to analyze or W to scan the seeded watchlist.`;
  const statusMessage = initialLoad ? `Featured scenario ready: ${preset.name}.` : `Preset loaded: ${preset.name}.`;
  setStatus(statusMessage, "neutral", onboarding);
  if (autorun) {
    runAnalysis();
  }
};

const loadPresets = async () => {
  const payload = await fetchJson("/api/presets");
  availablePresets = payload.items || [];
  renderPresetChips(availablePresets);
  if (!currentIncidents.length) {
    renderIncidents(currentIncidents);
  }
  if (!hasBootstrappedPreset && !activePresetId && availablePresets.length) {
    const featured = availablePresets.find((item) => item.id === payload.featured_id)
      || availablePresets.find((item) => item.featured)
      || availablePresets[0];
    if (featured) {
      hasBootstrappedPreset = true;
      applyPreset(featured, { initialLoad: true });
      renderPresetChips(availablePresets);
    }
  }
  presetChipsEl.onclick = (event) => {
    const target = event.target.closest(".preset-chip");
    if (!target) {
      return;
    }
    const preset = availablePresets.find((item) => item.id === target.dataset.presetId);
    if (!preset) {
      return;
    }
    applyPreset(preset);
    renderPresetChips(availablePresets);
  };
};

const loadWatchlists = async (selectedId = null) => {
  const payload = await fetchJson("/api/watchlists");
  const items = payload.items || [];
  availableWatchlists = items;
  commandWatchlistsEl.textContent = String(items.length);
  watchlistSelectEl.innerHTML = "";
  if (!items.length) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "No watchlists";
    watchlistSelectEl.appendChild(opt);
    hydrateWatchlistEditor(null);
    return;
  }
  const preferredId = selectedId || watchlistSelectEl.value || (items[0] && items[0].id) || "";
  items.forEach((item) => {
    const opt = document.createElement("option");
    opt.value = item.id;
    opt.textContent = `${item.name} (${(item.members || []).length} locations)`;
    if (preferredId && item.id === preferredId) {
      opt.selected = true;
    }
    watchlistSelectEl.appendChild(opt);
  });
  hydrateWatchlistEditor(currentSelectedWatchlist());
};

const renderWatchlistSummary = (summary) => {
  if (!summary) {
    latestWatchlistPayload = null;
    watchlistSummaryEl.textContent = "No watchlist scan yet.";
    watchlistHealthNoteEl.textContent = "Watchlist evidence-health note will appear here.";
    watchlistTopHotspotEl.textContent = "N/A";
    watchlistAverageScoreEl.textContent = "N/A";
    watchlistBiggestRiserEl.textContent = "N/A";
    watchlistBiggestRiserDetailEl.textContent = "No trend history yet.";
    watchlistPersistentHotspotEl.textContent = "N/A";
    watchlistPersistentHotspotDetailEl.textContent = "No persistent hotspot yet.";
    watchlistNewlyElevatedEl.textContent = "N/A";
    watchlistNewlyElevatedDetailEl.textContent = "No newly elevated member yet.";
    refreshAnalytics();
    return;
  }
  watchlistSummaryEl.textContent = summary.summary || "Watchlist scan complete.";
  watchlistHealthNoteEl.textContent = summary.health_note || "No watchlist evidence-health note available.";
  watchlistTopHotspotEl.textContent = summary.top_hotspot
    ? `${summary.top_hotspot.member_label} (${String(summary.top_hotspot.threat_level || "none").toUpperCase()})`
    : "None";
  watchlistAverageScoreEl.textContent = Number(summary.average_score || 0).toFixed(4);

  const trends = summary.trends || {};
  const biggestRiser = trends.biggest_riser;
  watchlistBiggestRiserEl.textContent = biggestRiser
    ? biggestRiser.member_label
    : "None";
  watchlistBiggestRiserDetailEl.textContent = biggestRiser
    ? `Delta ${Number(biggestRiser.delta_score || 0).toFixed(3)} to ${String(biggestRiser.latest_threat_level || "none").toUpperCase()}`
    : "No upward movement recorded yet.";

  const persistentHotspot = trends.most_persistent_hotspot;
  watchlistPersistentHotspotEl.textContent = persistentHotspot
    ? persistentHotspot.member_label
    : "None";
  watchlistPersistentHotspotDetailEl.textContent = persistentHotspot
    ? `${String(persistentHotspot.latest_threat_level || "none").toUpperCase()} with ${toTitle(persistentHotspot.trend_label || "stable")} pattern`
    : "No persistent hotspot yet.";

  const newlyElevated = trends.newly_elevated;
  watchlistNewlyElevatedEl.textContent = newlyElevated
    ? newlyElevated.member_label
    : "None";
  watchlistNewlyElevatedDetailEl.textContent = newlyElevated
    ? `${String(newlyElevated.latest_threat_level || "none").toUpperCase()} on latest scan`
    : "No newly elevated member yet.";
};

const loadWatchlistTrends = async () => {
  const watchlistId = watchlistSelectEl.value;
  if (!watchlistId) {
    renderWatchlistSummary(null);
    return;
  }
  try {
    const payload = await fetchJson(`/api/watchlists/${watchlistId}/trends?lens=${encodeURIComponent(lensSelect.value)}`);
    renderWatchlistSummary({
      summary: payload.trends && payload.trends.summary ? payload.trends.summary : "Trend history loaded.",
      top_hotspot: null,
      average_score: 0,
      trends: payload.trends,
      lens_label: payload.lens,
    });
  } catch (_err) {
    // Leave the last successful watchlist summary in place.
  }
};

const renderIncidents = (items) => {
  currentIncidents = items || [];
  commandIncidentsEl.textContent = String(currentIncidents.filter((item) => item.status === "open").length);
  flashElement(commandIncidentsEl.closest(".command-metric"));
  incidentListEl.innerHTML = "";
  if (!currentIncidents.length) {
    const demoQueue = [...availablePresets]
      .sort((a, b) => Number(b.priority || 0) - Number(a.priority || 0))
      .slice(0, 3);
    if (!demoQueue.length) {
      const empty = document.createElement("article");
      empty.className = "incident-empty";
      empty.textContent = "No incidents pinned.";
      incidentListEl.appendChild(empty);
      return;
    }
    demoQueue.forEach((preset) => {
      const article = document.createElement("article");
      article.className = "incident-card demo-incident-card";
      article.innerHTML = `
        <div class="incident-head">
          <div>
            <h3>${escapeHtml(preset.name || "Featured scenario")}</h3>
            <p class="incident-subtitle">${escapeHtml(preset.demo_headline || preset.description || "Curated hackathon scenario.")}</p>
          </div>
          <span class="incident-status" data-status="demo">demo</span>
        </div>
        <div class="incident-meta">
          <span class="incident-chip">${escapeHtml(formatThreat(preset.threat_level || "medium"))}</span>
          <span class="incident-chip">${escapeHtml(toTitle(preset.lens || "general"))}</span>
          <span class="incident-chip">${escapeHtml(preset.region || "Global")}</span>
        </div>
        <div class="incident-foot">
          <span>${escapeHtml(preset.operator_note || "Curated featured scenario.")}</span>
          <span>Radius ${escapeHtml(String(Number(preset.radius_km || 25).toFixed(0)))} km</span>
        </div>
        <div class="incident-actions">
          <button class="btn secondary" type="button" data-action="preset" data-preset-id="${escapeHtml(preset.id)}">Stage Demo</button>
          <button class="btn primary" type="button" data-action="preset" data-preset-id="${escapeHtml(preset.id)}" data-autorun="true">Analyze Demo</button>
        </div>
      `;
      incidentListEl.appendChild(article);
    });
    return;
  }

  currentIncidents.forEach((incident) => {
    const article = document.createElement("article");
    article.className = "incident-card";
    article.dataset.status = incident.status || "open";

    const scoreText = incident.latest_score === null || incident.latest_score === undefined
      ? "n/a"
      : Number(incident.latest_score).toFixed(4);
    article.innerHTML = `
      <div class="incident-head">
        <div>
          <h3>${escapeHtml(incident.location_label || incident.title || "Incident")}</h3>
          <p class="incident-subtitle">${escapeHtml(incident.brief_headline || incident.summary || "Pinned analysis incident.")}</p>
        </div>
        <span class="incident-status" data-status="${escapeHtml(incident.status || "open")}">${escapeHtml(incident.status || "open")}</span>
      </div>
      <div class="incident-meta">
        <span class="incident-chip">${escapeHtml(String(incident.latest_threat_level || "none").toUpperCase())}</span>
        <span class="incident-chip">Score ${escapeHtml(scoreText)}</span>
        <span class="incident-chip">Trend ${escapeHtml(toTitle(incident.latest_trend_label || "n/a"))}</span>
        <span class="incident-chip">${escapeHtml(incident.lens_label || toTitle(incident.lens || "general"))}</span>
        <span class="incident-chip">Health ${escapeHtml(toTitle(incident.evidence_health_label || "n/a"))}</span>
      </div>
      <div class="incident-foot">
        <span>${escapeHtml(incident.summary || "Active incident in the queue.")}</span>
        <span>Updated ${escapeHtml(toDateLabel(incident.updated_at))}</span>
      </div>
      <div class="incident-actions">
        <button class="btn secondary" type="button" data-action="map" data-incident-id="${escapeHtml(incident.id)}">Open on Map</button>
        <button class="btn secondary" type="button" data-action="rescan" data-incident-id="${escapeHtml(incident.id)}" ${incident.status !== "open" ? "disabled" : ""}>Rescan</button>
        <button class="btn secondary" type="button" data-action="close" data-incident-id="${escapeHtml(incident.id)}" ${incident.status !== "open" ? "disabled" : ""}>Close</button>
      </div>
    `;
    incidentListEl.appendChild(article);
  });
};

const loadIncidents = async () => {
  const payload = await fetchJson("/api/incidents");
  renderIncidents(payload.items || []);
  await loadMapLayers();
  await loadOverview();
};

const syncIncidentButtonState = () => {
  saveIncidentBtn.disabled = !lastAnalysisHistoryId;
  commandIncidentBtn.disabled = !lastAnalysisHistoryId;
};

const openIncidentOnMap = (incident) => {
  const query = incident && incident.query ? incident.query : null;
  if (!query) {
    setStatus("Incident query is missing.", "error");
    return;
  }
  latInput.value = Number(query.lat).toFixed(5);
  lonInput.value = Number(query.lon).toFixed(5);
  radiusInput.value = Number(query.radius_km || 25).toFixed(0);
  modeSelect.value = query.mode || "sample";
  riskProfileSelect.value = query.risk_profile || "balanced";
  lensSelect.value = query.lens || "general";
  applyLensExperience({ resetMapDefaults: true });
  deepLiveCheckbox.checked = Boolean(query.deep_live);
  syncModeControls();
  previewSelection({ fit: true });
  overlayModeEl.textContent = modeSelect.value === "live"
    ? (deepLiveCheckbox.checked ? "LIVE DEEP" : "LIVE FAST")
    : "SAMPLE";
  setStatus(`Incident loaded: ${incident.location_label || incident.title}.`, "success");
};

const refreshHistory = async () => {
  const payload = await fetchJson("/api/history?limit=8");
  const items = payload.items || [];
  const lines = items.map((item) => {
    const ts = toDateLabel(item.created_at);
    if (item.type === "watchlist_scan") {
      const lensLabel = item.summary?.lens_label || item.lens || "general";
      return `${ts}: ${item.summary?.summary || `watchlist scan (${item.result_count} results)`} [${String(lensLabel).toUpperCase()}]`;
    }
    const threat = item.alert?.threat_level || "unknown";
    const score = item.alert?.score;
    const scoreText = score === null || score === undefined ? "n/a" : Number(score).toFixed(3);
    const lensLabel = item.query?.lens || item.lens || "general";
    return `${ts}: ${String(threat).toUpperCase()} risk at ${scoreText} [${String(lensLabel).toUpperCase()}]`;
  });
  setList(historyListEl, lines, "No history loaded.");
};

const saveIncident = async () => {
  if (!lastAnalysisHistoryId) {
    setStatus("Run an analysis before saving an incident.", "error");
    return;
  }
  saveIncidentBtn.disabled = true;
  commandIncidentBtn.disabled = true;
  setButtonBusy(saveIncidentBtn, true, "Saving...");
  try {
    const payload = await fetchJson("/api/incidents", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ history_id: lastAnalysisHistoryId }),
    });
    if (latestAnalysisPayload) {
      latestAnalysisPayload.incident_context = payload.incident || null;
      renderDecisionSurface(latestAnalysisPayload);
    }
    await loadIncidents();
    setDeckTab("incidents");
    setStatus(payload.created ? "Incident saved to queue." : "Incident queue entry refreshed.", "success");
  } catch (err) {
    setStatus(`Error: ${err.message}`, "error");
  } finally {
    setButtonBusy(saveIncidentBtn, false);
    syncIncidentButtonState();
  }
};

const createWatchlist = async () => {
  let members;
  const pendingAlerts = readWatchlistAlertForm();
  try {
    members = parseWatchlistMembers();
  } catch (err) {
    setStatus(err.message, "error");
    return;
  }

  createWatchlistBtn.disabled = true;
  setButtonBusy(createWatchlistBtn, true, "Creating...");
  setStatus("Creating watchlist...", "neutral");
  try {
    const payload = await fetchJson("/api/watchlists", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: watchlistNameEl.value.trim() || "Priority Assets",
        members,
      }),
    });
    await loadWatchlists(payload.watchlist?.id || null);
    watchlistAlertEmailEl.value = pendingAlerts.email_to;
    watchlistAlertSmsEl.value = pendingAlerts.sms_to;
    watchlistEmailEnabledEl.checked = pendingAlerts.email_enabled;
    watchlistSmsEnabledEl.checked = pendingAlerts.sms_enabled;
    if (pendingAlerts.email_to || pendingAlerts.sms_to) {
      await saveWatchlistAlerts({ silent: true });
    }
    await loadWatchlistTrends();
    await Promise.all([loadMapLayers(), loadLiveContext()]);
    setStatus("Watchlist created.", "success");
  } catch (err) {
    setStatus(`Error: ${err.message}`, "error");
  } finally {
    setButtonBusy(createWatchlistBtn, false);
    createWatchlistBtn.disabled = false;
  }
};

const readWatchlistAlertForm = () => ({
  email_to: watchlistAlertEmailEl.value.trim(),
  sms_to: watchlistAlertSmsEl.value.trim(),
  email_enabled: watchlistEmailEnabledEl.checked,
  sms_enabled: watchlistSmsEnabledEl.checked,
  threshold: "high",
});

const saveWatchlistAlerts = async ({ silent = false } = {}) => {
  const watchlistId = watchlistSelectEl.value;
  if (!watchlistId) {
    if (!silent) {
      setStatus("Select a watchlist first.", "error");
    }
    return false;
  }

  saveWatchlistAlertsBtn.disabled = true;
  setButtonBusy(saveWatchlistAlertsBtn, true, "Saving...");
  if (!silent) {
    setStatus("Saving watchlist alerting...", "neutral");
  }
  try {
    const payload = await fetchJson(`/api/watchlists/${watchlistId}/alerts`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(readWatchlistAlertForm()),
    });
    await loadWatchlists(payload.watchlist?.id || watchlistId);
    if (!silent) {
      setStatus("Watchlist alerting saved.", "success");
    }
    return true;
  } catch (err) {
    if (!silent) {
      setStatus(`Error: ${err.message}`, "error");
    }
    return false;
  } finally {
    setButtonBusy(saveWatchlistAlertsBtn, false);
    syncWatchlistActionState();
  }
};

const removeWatchlist = async () => {
  const watchlist = currentSelectedWatchlist();
  if (!watchlist) {
    setStatus("Select a watchlist first.", "error");
    return;
  }

  deleteWatchlistBtn.disabled = true;
  setButtonBusy(deleteWatchlistBtn, true, "Removing...");
  setStatus(`Removing ${watchlist.name}...`, "neutral");
  try {
    await fetchJson(`/api/watchlists/${watchlist.id}`, { method: "DELETE" });
    latestWatchlistPayload = null;
    renderWatchlistSummary(null);
    setList(watchlistResultsEl, [], "No watchlist scans yet.");
    await Promise.all([loadWatchlists(), loadMapLayers(), loadLiveContext()]);
    setStatus("Watchlist removed.", "success");
  } catch (err) {
    setStatus(`Error: ${err.message}`, "error");
  } finally {
    setButtonBusy(deleteWatchlistBtn, false);
    syncWatchlistActionState();
  }
};

const scanWatchlist = async () => {
  const watchlistId = watchlistSelectEl.value;
  if (!watchlistId) {
    setStatus("Select a watchlist first.", "error");
    return;
  }

  scanWatchlistBtn.disabled = true;
  setButtonBusy(scanWatchlistBtn, true, "Scanning...");
  setStatus("Scanning watchlist...", "neutral");
  try {
    const notify = readWatchlistAlertForm();
    const payload = await fetchJson(`/api/watchlists/${watchlistId}/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: modeSelect.value,
        risk_profile: riskProfileSelect.value,
        lens: lensSelect.value,
        radius_km: Number(radiusInput.value || 25),
        start_date: startDateInput.value,
        end_date: endDateInput.value,
        deep_live: modeSelect.value === "live" && deepLiveCheckbox.checked,
        notify,
      }),
    }, 85000);

    const results = [...(payload.results || [])].sort((a, b) => {
      const threatDelta = THREAT_PRIORITY[String(b.threat_level || "none")] - THREAT_PRIORITY[String(a.threat_level || "none")];
      if (threatDelta !== 0) {
        return threatDelta;
      }
      return Number(b.score || 0) - Number(a.score || 0);
    });

    const lines = results.map((result) => {
      if (result.ok === false) {
        return `${result.member_label}: ERROR (${result.error})`;
      }
      return `${result.member_label}: ${String(result.threat_level || "none").toUpperCase()} score=${Number(result.score || 0).toFixed(4)} confidence=${String(result.confidence || "n/a").toUpperCase()}`;
    });
    latestWatchlistPayload = payload;
    renderWatchlistSummary(payload.summary);
    setList(watchlistResultsEl, lines, "No watchlist results.");
    refreshAnalytics();
    await refreshHistory();
    await Promise.all([loadMapLayers(), loadLiveContext()]);
    setDeckTab("watchlists");
    setWatchlistTab("results");
    setStatus(`Watchlist scan complete (${results.length} locations).`, "success");
  } catch (err) {
    setStatus(`Error: ${err.message}`, "error");
  } finally {
    setButtonBusy(scanWatchlistBtn, false);
    scanWatchlistBtn.disabled = false;
  }
};

const runAnalysis = async () => {
  let payload;
  try {
    payload = parseInputs();
  } catch (err) {
    setStatus(err.message, "error");
    return;
  }

  analyzeBtn.disabled = true;
  commandAnalyzeBtn.disabled = true;
  rescanAnalysisBtn.disabled = true;
  setButtonBusy(analyzeBtn, true, "Analyzing...");
  setButtonBusy(commandAnalyzeBtn, true, "Analyzing...");
  setButtonBusy(rescanAnalysisBtn, true, "Analyzing...");
  setStatus(`Analyzing ${payload.lat.toFixed(4)}, ${payload.lon.toFixed(4)}...`, "neutral");

  try {
    const result = await fetchJson("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }, 85000);

    renderResult(result);
    await refreshHistory();
    await Promise.all([loadMapLayers(), loadLiveContext()]);
    setDeckTab("scan-brief");
    setStatus(`Analysis complete (${result.mode.toUpperCase()} mode).`, "success");
  } catch (err) {
    setStatus(`Error: ${err.message}`, "error");
  } finally {
    setButtonBusy(analyzeBtn, false);
    setButtonBusy(commandAnalyzeBtn, false);
    setButtonBusy(rescanAnalysisBtn, false);
    analyzeBtn.disabled = false;
    commandAnalyzeBtn.disabled = false;
    rescanAnalysisBtn.disabled = false;
  }
};

const useBrowserLocation = () => {
  if (!navigator.geolocation) {
    setStatus("Geolocation is not supported in this browser.", "error");
    return;
  }

  setStatus("Fetching browser location...", "neutral");
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      latInput.value = lat.toFixed(5);
      lonInput.value = lon.toFixed(5);
      previewSelection({ fit: true });
      setStatus("Location loaded. Click Analyze Risk.", "success");
    },
    () => setStatus("Unable to read current location; enter coordinates manually.", "error"),
    { enableHighAccuracy: true, timeout: 9000 }
  );
};

map.on("click", (event) => {
  const { lat, lng } = event.latlng;
  latInput.value = lat.toFixed(5);
  lonInput.value = lng.toFixed(5);
  previewSelection();
  setStatus("Map point selected. Click Analyze Risk.", "neutral");
});

analyzeBtn.addEventListener("click", runAnalysis);
rescanAnalysisBtn.addEventListener("click", runAnalysis);
geoBtn.addEventListener("click", useBrowserLocation);
createWatchlistBtn.addEventListener("click", createWatchlist);
scanWatchlistBtn.addEventListener("click", scanWatchlist);
deleteWatchlistBtn.addEventListener("click", removeWatchlist);
saveWatchlistAlertsBtn.addEventListener("click", () => {
  saveWatchlistAlerts().catch((err) => setStatus(`Error: ${err.message}`, "error"));
});
saveIncidentBtn.addEventListener("click", saveIncident);
commandAnalyzeBtn.addEventListener("click", () => analyzeBtn.click());
commandIncidentBtn.addEventListener("click", () => saveIncidentBtn.click());
refreshHistoryBtn.addEventListener("click", () => {
  refreshHistory().catch((err) => setStatus(`Error: ${err.message}`, "error"));
});
refreshIncidentsBtn.addEventListener("click", () => {
  loadIncidents().catch((err) => setStatus(`Error: ${err.message}`, "error"));
});
refreshBulletinsBtn.addEventListener("click", () => {
  loadBulletins({ silent: false }).catch((err) => setStatus(`Error: ${err.message}`, "error"));
});
refreshInstabilityBtn.addEventListener("click", () => {
  loadInstability({ silent: false }).catch((err) => setStatus(`Error: ${err.message}`, "error"));
});
deckTabEls.forEach((button) => {
  button.addEventListener("click", () => setDeckTab(button.dataset.deckTarget));
});
watchlistTabEls.forEach((button) => {
  button.addEventListener("click", () => setWatchlistTab(button.dataset.watchlistTarget));
});
[...analyticsTabEls].forEach((button) => {
  button.addEventListener("click", () => {
    setAnalyticsTab(button.dataset.analyticsTarget);
    refreshAnalytics();
  });
});
[layerHeatmapToggleEl, layerHotspotsToggleEl, layerIncidentsToggleEl, layerWatchlistsToggleEl, layerInstabilityToggleEl]
  .forEach((input) => {
    input.addEventListener("change", syncMapLayerVisibility);
  });
watchlistSelectEl.addEventListener("change", () => {
  hydrateWatchlistEditor(currentSelectedWatchlist());
  loadWatchlistTrends().catch(() => undefined);
});
incidentListEl.addEventListener("click", async (event) => {
  const target = event.target.closest("button[data-action]");
  if (!target) {
    return;
  }
  if (target.dataset.action === "preset") {
    const preset = availablePresets.find((item) => item.id === target.dataset.presetId);
    if (!preset) {
      setStatus("Demo scenario not found.", "error");
      return;
    }
    applyPreset(preset, { autorun: target.dataset.autorun === "true" });
    setDeckTab(target.dataset.autorun === "true" ? "scan-brief" : "watchlists");
    return;
  }
  const incidentId = target.dataset.incidentId;
  const action = target.dataset.action;
  const incident = currentIncidents.find((item) => item.id === incidentId);
  if (!incident) {
    setStatus("Incident not found in current queue state.", "error");
    return;
  }

  if (action === "map") {
    openIncidentOnMap(incident);
    return;
  }

  target.disabled = true;
  try {
    if (action === "rescan") {
      const payload = await fetchJson(`/api/incidents/${encodeURIComponent(incidentId)}/rescan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      }, 85000);
      renderResult(payload.analysis);
      await Promise.all([refreshHistory(), loadIncidents()]);
      setStatus("Incident rescanned.", "success");
      return;
    }

    if (action === "close") {
      await fetchJson(`/api/incidents/${encodeURIComponent(incidentId)}/close`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      await loadIncidents();
      if (latestAnalysisPayload && latestAnalysisPayload.incident_context && latestAnalysisPayload.incident_context.id === incidentId) {
        latestAnalysisPayload.incident_context = null;
        renderDecisionSurface(latestAnalysisPayload);
      }
      setStatus("Incident closed.", "success");
    }
  } catch (err) {
    setStatus(`Error: ${err.message}`, "error");
  } finally {
    target.disabled = false;
  }
});
lensSelect.addEventListener("change", () => {
  applyLensExperience({ resetMapDefaults: true });
  syncCommandContext();
  loadWatchlistTrends().catch(() => undefined);
  loadMapLayers().catch(() => undefined);
  loadLiveContext().catch(() => undefined);
});
modeSelect.addEventListener("change", () => {
  syncModeControls();
  overlayModeEl.textContent = modeSelect.value === "live"
    ? (deepLiveCheckbox.checked ? "LIVE DEEP" : "LIVE FAST")
    : "SAMPLE";
  syncCommandContext();
});
deepLiveCheckbox.addEventListener("change", () => {
  overlayModeEl.textContent = modeSelect.value === "live"
    ? (deepLiveCheckbox.checked ? "LIVE DEEP" : "LIVE FAST")
    : "SAMPLE";
  syncCommandContext();
});
[latInput, lonInput, radiusInput].forEach((input) => {
  input.addEventListener("change", () => previewSelection());
});

bulletinsListEl.addEventListener("click", (event) => {
  if (event.target.closest(".bulletin-link")) {
    return;
  }
  const card = event.target.closest(".bulletin-card");
  if (!card) {
    return;
  }
  const lat = Number(card.dataset.lat);
  const lon = Number(card.dataset.lon);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    return;
  }
  stageMapLocation(
    {
      lat,
      lon,
      radius_km: Number(card.dataset.radiusKm || 25),
      lens: card.dataset.lens || lensSelect.value,
    },
    { loadLens: Boolean(card.dataset.lens), fit: true }
  );
  setStatus("Bulletin focused on map.", "neutral");
});

instabilityListEl.addEventListener("click", (event) => {
  const card = event.target.closest(".instability-card");
  if (!card) {
    return;
  }
  const lat = Number(card.dataset.lat);
  const lon = Number(card.dataset.lon);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    return;
  }
  stageMapLocation(
    {
      lat,
      lon,
      radius_km: Number(card.dataset.radiusKm || 120),
    },
    { fit: true }
  );
  setStatus("Instability zone focused on map.", "neutral");
});

document.addEventListener("keydown", (event) => {
  const target = event.target;
  const tag = target && target.tagName ? target.tagName.toLowerCase() : "";
  const isEditable = target && (target.isContentEditable || ["input", "textarea", "select"].includes(tag));
  if (isEditable || event.metaKey || event.ctrlKey || event.altKey) {
    return;
  }
  if (event.key === "a" || event.key === "A") {
    event.preventDefault();
    analyzeBtn.click();
  } else if (event.key === "r" || event.key === "R") {
    event.preventDefault();
    rescanAnalysisBtn.click();
  } else if (event.key === "i" || event.key === "I") {
    event.preventDefault();
    commandIncidentBtn.click();
  } else if (event.key === "e" || event.key === "E") {
    event.preventDefault();
    setDeckTab("evidence");
  } else if (event.key === "w" || event.key === "W") {
    event.preventDefault();
    scanWatchlistBtn.click();
  }
});

const today = new Date();
const start = new Date(today);
start.setDate(today.getDate() - 30);
startDateInput.value = start.toISOString().slice(0, 10);
endDateInput.value = today.toISOString().slice(0, 10);
latInput.value = "37.77490";
lonInput.value = "-122.41940";
radiusInput.value = "25";
watchlistMembersEl.value = "HQ,37.7749,-122.4194\nPort,37.8044,-122.2712";
watchlistNameEl.value = "Priority Assets";
watchlistEmailEnabledEl.checked = true;
watchlistSmsEnabledEl.checked = false;
lensSelect.value = "general";
marker.setLatLng([37.7749, -122.4194]);
map.setView([37.7749, -122.4194], 8);
syncModeControls();
applyLensExperience({ resetMapDefaults: true });
previewSelection();
overlayModeEl.textContent = "SAMPLE";
commandThreatEl.textContent = "N/A";
commandTickerEl.textContent = "Awaiting live context.";
renderDecisionSurface();
renderAiInsight();
syncIncidentButtonState();
syncWatchlistActionState();
setDeckTab("scan-brief");
setWatchlistTab("overview");
setAnalyticsTab("trend");
syncCommandContext();
syncMapLayerVisibility();
setMapFocus({
  title: "Global operating picture",
  meta: "No hotspot selected",
  summary: "The intelligence layer will summarize hotspots, incidents, and instability corridors here as scans and watchlists accumulate.",
  tone: "neutral",
});
refreshAnalytics();
updateSyncStamp();

loadPresets().catch(() => setStatus("Unable to load presets.", "error"));
loadWatchlists().catch(() => setStatus("Unable to load watchlists.", "error"));
loadWatchlistTrends().catch(() => undefined);
refreshHistory().catch(() => setStatus("Unable to load history.", "error"));
loadIncidents().catch(() => setStatus("Unable to load incidents.", "error"));
loadMapLayers().catch(() => undefined);
loadLiveContext().catch(() => undefined);

window.setInterval(() => {
  loadBulletins().catch(() => undefined);
  loadOverview().catch(() => undefined);
}, 20000);

window.setInterval(() => {
  loadInstability().catch(() => undefined);
}, 30000);

window.setInterval(() => {
  updateSyncStamp();
}, 15000);
