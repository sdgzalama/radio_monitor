// frontend/js/main.js (FINAL VERSION)
// =========================================================
// V8 - MODERN UI/UX REDESIGN (FINAL ROBUST VERSION)
// =========================================================

// --- DATA STRUCTURE FOR STATION VISUALS ---
const stationLogos = {
    // English stations - Updated with better logos
    "KEXP (Seattle, 64 kbps)": "https://kexp.org/assets/images/logos/kexp-logo-mark.png",
    "KEXP (Seattle, 160 kbps)": "https://kexp.org/assets/images/logos/kexp-logo-mark.png",
    "NPR": "https://media.npr.org/chrome_svg/npr-logo.svg",
    "WYPR 88.1 FM (Baltimore)": "https://wypr.org/wp-content/uploads/2023/04/wypr-logo-white.png",
    "WAMU 88.5 FM (Washington DC)": "https://wamu.org/wp-content/uploads/2019/12/wamu-logo-150x150.png",
    "BBC World Service": "https://ichef.bbci.co.uk/images/ic/256x256/p081pjz6.png",
    "BBC Radio 4 (UK)": "https://ichef.bbci.co.uk/images/ic/256x256/p081pj77.png",
    "BBC Radio 5 Live (UK)": "https://ichef.bbci.co.uk/images/ic/256x256/p081pj8l.png",
    "BBC Radio 2 (UK)": "https://ichef.bbci.co.uk/images/ic/256x256/p081pj6v.png",
    "KQED NPR (San Francisco)": "https://ww2.kqed.org/wp-content/uploads/sites/2/2018/08/KQED-logo-sq.jpg",
    "WNYC 93.9 FM (New York)": "https://media.wnyc.org/static/img/wnyc_logo_1400x1400.png",
    "WBUR 90.9 FM (Boston)": "https://d279m997dpfwgl.cloudfront.net/wp/2020/09/wbur-logo-2020.png",
    "KPCC 89.3 FM (Los Angeles)": "https://a.scpr.org/i/b3ff8e86db65abc3df96ebb905e77bda/207058-full.jpg",
    "WHYY 90.9 FM (Philadelphia)": "https://whyy.org/wp-content/uploads/2018/03/whyy-logo-icon-512x512.png",
    "ABC News Radio (Australia)": "https://www.abc.net.au/cm/rimage/13119106-3x2-xlarge.png",
    "CBC Radio One (Toronto)": "https://cbc.radio-canada.ca/bin/toutube/cbc-gem-icon-256x256.png",
    "Voice of America (VOA News Now)": "https://www.voanews.com/Content/responsive/VOA/en-US/img/voa-logo-print.png",
    "Al Jazeera English (Audio)": "https://www.aljazeera.com/wp-content/uploads/2023/02/AJE-Logo.png",
    "PRI The World": "https://media.pri.org/s3fs-public/styles/story_main/public/story/images/world_logo_facebook_1200x630_final.png",
    "Radio Paradise (USA, Mix)": "https://img.radioparadise.com/assets/rp-new-site-logo-sq-300.png",
    "KCRW 89.9 FM (Santa Monica)": "https://www.kcrw.com/culture/shows/greater-la/RL230106-Greater-LA-end-of-year/@@images/teaser/teaser",
    
    // French stations - Better Radio France logos
    "France Inter": "https://www.franceinter.fr/s3/cruiser-production/2023/11/7b4f8b0c-9b22-4a7c-9af0-1ee477b6da4d/400x400_maxnewsworld-5858993.jpg",
    "France Info": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/France_Info_-_Logo_2018.svg/512px-France_Info_-_Logo_2018.svg.png",
    "France Culture": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/France_Culture_-_logo_2018.svg/512px-France_Culture_-_logo_2018.svg.png",
    "FIP": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Fip-logo-2018.svg/512px-Fip-logo-2018.svg.png",
    "Radio Classique": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Radio_Classique_logo_2015.svg/512px-Radio_Classique_logo_2015.svg.png",
    
    // Chinese stations - Better quality logos
    "中廣新聞網": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/BCC_News_logo.svg/512px-BCC_News_logo.svg.png",
    "News98新聞網": "https://www.news98.com.tw/wp-content/uploads/2019/04/news98-logo-square.png",
    "飛碟聯播網": "https://www.uforadio.com.tw/assets/images/ufo-logo-square.png"
};

const PLACEHOLDER_LOGO_URL = 'data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22100%22%20height%3D%22100%22%20viewBox%3D%220%200%20100%20100%22%3E%3Crect%20width%3D%22100%22%20height%3D%22100%22%20fill%3D%22%23111%22%2F%3E%3Ctext%20x%3D%2250%22%20y%3D%2260%22%20font-family%3D%22sans-serif%22%20font-size%3D%2240%22%20fill%3D%22%23FFF%22%20text-anchor%3D%22middle%22%3E%3F%3C%2Ftext%3E%3C%2Fsvg%3E';

// --- GLOBAL STATE VARIABLES ---
let status = 'STOPPED';
let ws = null;
let mediaSource = null;
let sourceBuffer = null;
let bufferQueue = [];
let mime = null;
let utteranceHistory = [];
let animationFrameHandle = null;
const MAX_HISTORY_LENGTH = 20;
let isAudioUnlocked = false;
let currentStation = null;
let stationList = {};
let currentLanguage = 'en';
let reconnectTimeoutHandle = null;
let userSyncOffset = -2.0;
const SMOOTHING_FACTOR = 0.05;
let debugMode = false;
let lastVolume = 1.0;
let currentHighlightedSpan = null;
let hasReceivedFirstSummary = false;
let s2tConverter = null;
let lastSummaryTimestamp = null;
let summaryUpdateInterval = null;
let performanceInfo = null;  // NEW: Store performance mode info

// NEW: Station discovery state
let discoveredStations = [];
let activeTab = 'favorites';
let stationCategories = [];
let countries = [];
let languages = [];
// Map of favorite station -> detected language from server
let favoriteStationLanguages = {};

// Debounce and request dedupe state
let _discoverDebounceHandle = null;
let _lastDiscoverSignature = null; // last request signature to avoid duplicates

// --- DOM ELEMENT VARIABLES ---
let dynamicBackground, stationModal, openStationModalBtn, closeStationModalBtn,
    stationListContainer, playerStationLogo, playerStationName, playBtn, stopBtn,
    languageIndicator, userCountIndicator, syncSlider, syncValueSpan,
    debugPanel, debugContent, audio, muteBtn, volumeSlider, summaryText,
    summaryTimestamp, performanceModeIndicator;  // NEW: Performance mode display

// NEW: Station discovery elements
let stationSearchInput, searchBtn, countryFilter, languageFilter, categoryFilter,
    discoverStationsContainer, newsStationsContainer, popularStationsContainer,
    loadingIndicator;

// --- UI CONTROL FUNCTIONS ---
function openStationModal() { 
    if (stationModal) {
        stationModal.classList.add('visible');
        // Load initial content based on active tab
        loadTabContent(activeTab);
    }
}

function closeStationModal() { 
    if (stationModal) stationModal.classList.remove('visible'); 
}

// NEW: Station discovery functions
async function loadStationCategories() {
    // Load available categories and countries for station discovery
    try {
        const response = await fetch('/api/stations/categories');
        const data = await response.json();
        
        stationCategories = data.categories || [];
        countries = data.countries || [];
        languages = data.languages || [];
        
        populateFilters();
    } catch (error) {
        console.error('Failed to load station categories:', error);
    }
}

function populateFilters() {
    // Populate filter dropdowns with available options
    if (countryFilter) {
        countryFilter.innerHTML = '<option value="">All Countries</option>';
        countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country.code;
            option.textContent = `${country.flag} ${country.name}`;
            countryFilter.appendChild(option);
        });
    }
    
    if (languageFilter) {
        languageFilter.innerHTML = '<option value="">All Languages</option>';
        languages.forEach(lang => {
            const option = document.createElement('option');
            option.value = lang.code;
            option.textContent = `${lang.name} ${lang.asr_support ? '✅' : '❌'}`;
            languageFilter.appendChild(option);
        });
    }
}

async function discoverStations(searchQuery = '', country = '', language = '', category = 'popular') {
    // Discover stations using the Radio Browser API
    if (!loadingIndicator || !discoverStationsContainer) return;
    
    loadingIndicator.style.display = 'block';
    discoverStationsContainer.innerHTML = '';
    
    try {
        // Trim and normalize search query
        const trimmedQuery = (searchQuery || '').trim();

        const params = new URLSearchParams({
            search: trimmedQuery,
            country: country,
            language: language,
            category: category,
            limit: '50'
        });

        // Debug: log the final request URL and params
        const requestUrl = `/api/stations/discover?${params.toString()}`;
        console.debug('discoverStations() - Request URL:', requestUrl, { search: trimmedQuery, country, language, category });

        // Show request URL visibly in the loading indicator to help debugging
        if (loadingIndicator) {
            loadingIndicator.style.display = 'block';
            loadingIndicator.innerHTML = `<div style="font-size:12px;color:#ccc;padding:8px;">🔎 Request: ${requestUrl}</div>`;
        }

        const response = await fetch(requestUrl);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        discoveredStations = data.stations || [];
        console.log('Discovered stations:', discoveredStations); // DEBUG
        displayDiscoveredStations(discoveredStations);
        
    } catch (error) {
        console.error('Failed to discover stations:', error);
        console.error('Error stack:', error.stack); // DEBUG
        discoverStationsContainer.innerHTML = `
            <div style="text-align: center; color: #ff6b6b; padding: 2rem;">
                ❌ Failed to discover stations: ${error.message || 'Unknown error'}
                <br><small>Check console for details</small>
            </div>
        `;
    } finally {
        loadingIndicator.style.display = 'none';
    }
}

function displayDiscoveredStations(stations) {
    // Display discovered stations in the grid
    if (!discoverStationsContainer) return;
    
    if (stations.length === 0) {
        discoverStationsContainer.innerHTML = `
            <div style="text-align: center; color: #ccc; padding: 2rem; grid-column: 1 / -1;">
                🔍 No stations found. Try adjusting your search filters.
            </div>
        `;
        return;
    }
    
    discoverStationsContainer.innerHTML = '';
    
    stations.forEach(station => {
        const stationItem = createStationElement(station, true);
        discoverStationsContainer.appendChild(stationItem);
    });
}

function createStationElement(station, isDiscovered = false) {
    // Create a station element for display
    const stationItem = document.createElement('div');
    stationItem.className = 'station-item';
    
    // Get logo URL
    const logoUrl = isDiscovered 
        ? (station.favicon || PLACEHOLDER_LOGO_URL)
        : (stationLogos[station.name] || PLACEHOLDER_LOGO_URL);
    
    // Determine if language is supported
    const stationLanguage = station.detected_language || station.asr_language || station.language || 'en';
    const supportedLanguages = ['en', 'fr', 'zh'];
    const isSupported = supportedLanguages.includes(stationLanguage);
    
    stationItem.innerHTML = `
        <img class="station-logo" src="${logoUrl}" alt="${station.name || 'Unknown'}" 
             onerror="this.src='${PLACEHOLDER_LOGO_URL}'" />
        <div class="station-info">
            <div class="station-name">${station.name || 'Unknown Station'}</div>
            <div class="station-details">
                ${station.country ? `<span>📍 ${station.country}</span>` : ''}
                ${station.bitrate ? `<span>🎵 ${station.bitrate}k</span>` : ''}
                ${station.codec ? `<span>📻 ${station.codec}</span>` : ''}
                ${station.genre ? `<span class="station-tag">${station.genre.split(',')[0]}</span>` : ''}
            </div>
        </div>
        <div class="language-badge ${isSupported ? '' : 'unsupported-language'}">
            ${stationLanguage.toUpperCase()}
        </div>
    `;
    
    stationItem.addEventListener('click', () => {
        if (isDiscovered) {
            selectDiscoveredStation(station);
        } else {
            selectStation(station.name, station.url || stationList[station.name]);
        }
    });
    
    return stationItem;
}

function selectDiscoveredStation(station) {
    // Select a discovered station and add it to the temporary list
    if (!station.url) {
        console.error('Station has no stream URL');
        return;
    }
    
    // Add to temporary station list
    stationList[station.name] = station.url;
    
    // Update current station info
    selectStation(station.name, station.url);
    
    console.log(`Selected discovered station: ${station.name} (${station.language})`);
}

function switchTab(tabName) {
    // Switch between different tabs in the station modal
    // Update active tab
    activeTab = tabName;
    
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-tab`);
    });
    
    // Load content for the active tab
    loadTabContent(tabName);
}

async function loadTabContent(tabName) {
    // Load content for a specific tab
    switch (tabName) {
        case 'discover':
            if (discoveredStations.length === 0) {
                await discoverStations(); // Load popular stations by default
            }
            break;
            
        case 'news':
            await loadNewsStations();
            break;
            
        case 'popular':
            await loadPopularStations();
            break;
            
        case 'favorites':
            // Favorites are loaded on page load
            break;
    }
}

async function loadNewsStations() {
    // Load news stations into the news tab
    if (!newsStationsContainer) return;
    
    try {
        const response = await fetch('/api/stations/discover?category=news&limit=30');
        const data = await response.json();
        
        newsStationsContainer.innerHTML = '';
        (data.stations || []).forEach(station => {
            const stationItem = createStationElement(station, true);
            newsStationsContainer.appendChild(stationItem);
        });
        
    } catch (error) {
        console.error('Failed to load news stations:', error);
        newsStationsContainer.innerHTML = '<div style="color: #ff6b6b;">Failed to load news stations</div>';
    }
}

async function loadPopularStations() {
    // Load popular stations into the popular tab
    if (!popularStationsContainer) return;
    
    try {
        const response = await fetch('/api/stations/discover?category=popular&limit=50');
        const data = await response.json();
        
        popularStationsContainer.innerHTML = '';
        (data.stations || []).forEach(station => {
            const stationItem = createStationElement(station, true);
            popularStationsContainer.appendChild(stationItem);
        });
        
    } catch (error) {
        console.error('Failed to load popular stations:', error);
        popularStationsContainer.innerHTML = '<div style="color: #ff6b6b;">Failed to load popular stations</div>';
    }
}

// --- TOKEN PROCESSING PIPELINE ---
function processAsrTokens(tokens) {
    const spacedTokens = processTokens(tokens);
    const decodedTokens = decodeUtf8Bytes(spacedTokens);
    if (currentLanguage === 'zh' && s2tConverter) {
        return decodedTokens.map(token => s2tConverter(token));
    }
    return decodedTokens;
}

function decodeUtf8Bytes(tokens) {
    if (!Array.isArray(tokens) || tokens.length === 0) return tokens;
    const cleanTokens = [];
    const decoder = new TextDecoder('utf-8', { fatal: false });
    const byteRegex = /<0x([0-9A-Fa-f]{2})>/;
    for (let i = 0; i < tokens.length; i++) {
        const token = tokens[i];
        const match = token.match(byteRegex);
        if (!match) {
            cleanTokens.push(token);
            continue;
        }
        const firstByte = parseInt(match[1], 16);
        let sequenceLen = 0;
        if (firstByte >= 0xC2 && firstByte <= 0xDF) sequenceLen = 2;
        else if (firstByte >= 0xE0 && firstByte <= 0xEF) sequenceLen = 3;
        else if (firstByte >= 0xF0 && firstByte <= 0xF4) sequenceLen = 4;
        if (sequenceLen === 0 || (i + sequenceLen > tokens.length)) {
            cleanTokens.push(token);
            continue;
        }
        const byteSequence = [firstByte];
        let isValidSequence = true;
        for (let j = 1; j < sequenceLen; j++) {
            const nextTokenMatch = tokens[i + j].match(byteRegex);
            if (nextTokenMatch) {
                byteSequence.push(parseInt(nextTokenMatch[1], 16));
            } else {
                isValidSequence = false;
                break;
            }
        }
        if (isValidSequence) {
            const byteArray = new Uint8Array(byteSequence);
            const decodedChar = decoder.decode(byteArray);
            cleanTokens.push(decodedChar);
            i += sequenceLen - 1;
        } else {
            cleanTokens.push(token);
        }
    }
    return cleanTokens;
}

function populateStationModal() {
    if (!stationListContainer) return;
    stationListContainer.innerHTML = '';
    for (const stationName in stationList) {
        const stationItem = document.createElement('div');
        stationItem.className = 'station-item';
        stationItem.onclick = () => selectStation(stationName);
        const logo = document.createElement('img');
        logo.src = stationLogos[stationName] || PLACEHOLDER_LOGO_URL;
        logo.alt = `${stationName} Logo`;
        logo.className = 'station-logo';
        logo.onerror = (e) => { e.target.src = PLACEHOLDER_LOGO_URL; };
        const nameSpan = document.createElement('span');
        nameSpan.textContent = stationName;
        stationItem.appendChild(logo);
        stationItem.appendChild(nameSpan);
        stationListContainer.appendChild(stationItem);
    }
}

function selectStation(stationName) {
    const wasPlaying = (status === 'PLAYING' || status === 'CONNECTING');
    if (wasPlaying) stop();
    currentStation = stationName;
    currentLanguage = getStationLanguage(stationName);
    playerStationName.textContent = stationName;
    const logoUrl = stationLogos[stationName] || PLACEHOLDER_LOGO_URL;
    playerStationLogo.src = logoUrl;
    playerStationLogo.onerror = () => { playerStationLogo.src = PLACEHOLDER_LOGO_URL; };
    dynamicBackground.style.backgroundImage = `url(${logoUrl})`;
    updateLanguageIndicator();
    closeStationModal();
    if (wasPlaying) setTimeout(play, 500);
}

function updateUI() {
    if (playBtn) playBtn.disabled = status !== 'STOPPED';
    if (stopBtn) stopBtn.disabled = status === 'STOPPED' || status === 'WAITING';
}

// --- CORE APPLICATION LOGIC ---
async function unlockAudio() {
    if (isAudioUnlocked) return;
    logDebug("Attempting to unlock audio context...");
    if (!audio) return;
    const silentAudio = "data:audio/mp3;base64,SUQzBAAAAAABEVRYWFgAAAAtAAADY29tbWVudABCaXRyYXRlIHN1cHBseSBieSBiaXRyYXRlLmNvbQBLTEFNQwAAAAMIAAAAAFVJRTMAAAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";
    audio.src = silentAudio;
    audio.volume = 0;
    try {
        await audio.play();
        logDebug("Audio context unlocked successfully.");
        isAudioUnlocked = true;
        audio.pause();
        audio.src = '';
    } catch (error) {
        logDebug(`Audio unlock failed: ${error.message}. App may not function correctly.`);
    }
}

async function loadStations() {
    logDebug("Loading radio stations from backend");
    try {
        const response = await fetch('/api/stations');
        const payload = await response.json();
        // Backwards compatibility: payload may be either an object {stations, languages}
        // or a plain map of stations. Handle both.
        if (payload && payload.stations) {
            stationList = payload.stations;
            favoriteStationLanguages = payload.languages || {};
        } else {
            stationList = payload || {};
            favoriteStationLanguages = {};
        }
        logDebug(`Loaded ${Object.keys(stationList).length} stations`);
        populateStationModal();
        const defaultStation = "NPR";
        selectStation(stationList[defaultStation] ? defaultStation : Object.keys(stationList)[0]);
    } catch (error) {
        logDebug(`Failed to load stations: ${error.message}`);
    }
}

function populateStationModal() {
    // Populate favorites tab with curated stations
    if (!stationListContainer) return;
    
    stationListContainer.innerHTML = '';
    
    Object.keys(stationList).forEach(stationName => {
        const detectedLang = favoriteStationLanguages[stationName] || 'en';
        const stationItem = createStationElement({
            name: stationName,
            url: stationList[stationName],
            language: detectedLang
        }, false);
        
        stationListContainer.appendChild(stationItem);
    });
}

async function getInitialStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        if (userCountIndicator) userCountIndicator.textContent = data.user_count !== undefined ? data.user_count : 'N/A';
    } catch (error) {
        console.error('Failed to get initial server status:', error);
        if (userCountIndicator) userCountIndicator.textContent = 'N/A';
    }
}

async function play() {
    if (status === 'CONNECTING' || status === 'PLAYING') return;
    clearTimeout(reconnectTimeoutHandle);
    logDebug("Play button clicked");
    await unlockAudio();
    initializePlayer();
    status = 'CONNECTING';
    updateUI();
    logDebug(`Connecting to WebSocket for station: ${currentStation}`);
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws?station=${encodeURIComponent(currentStation)}`;
    ws = new WebSocket(wsUrl);
    ws.binaryType = 'arraybuffer';
    ws.onopen = () => {
        status = 'PLAYING';
        logDebug("WebSocket connection established");
        startKaraokeLoop();
        updateUI();
    };
    ws.onmessage = (event) => {
        if (event.data instanceof ArrayBuffer) {
            handleAudio(new Uint8Array(event.data));
        } else {
            const msg = JSON.parse(event.data);
            
            // DEBUG: Log all received messages
            console.log('📨 DEBUG: WebSocket message received:', msg.type, msg);
            
            if (msg.type === 'config') { handleConfig(msg.payload); }
            else if (msg.type === 'asr') { handleAsr(msg.payload); }
            else if (msg.type === 'language') {
                // Handle enhanced language info with fallback detection
                currentLanguage = msg.payload.asr_language || msg.payload.language; // Backward compatibility
                updateLanguageIndicator(msg.payload);
                
                // Show fallback warning if applicable
                if (msg.payload.is_fallback) {
                    showLanguageFallbackNotification(msg.payload);
                }
            } else if (msg.type === 'performance_info') {
                console.log('🎯 DEBUG: Performance info message received:', msg.payload);
                handlePerformanceInfo(msg.payload);
            } else if (msg.type === 'user_count') {
                if (userCountIndicator) userCountIndicator.textContent = msg.payload.count;
            } else if (msg.type === 'wait') {
                logDebug(`Received wait message: ${msg.payload.message}`);
            } else if (msg.type === 'summary') {
                if (currentStation && msg.payload.station.trim() === currentStation.trim()) {
                    updateSummary(msg.payload); // Pass the whole payload
                }
            } else if (msg.type === 'summary_state') {
                handleSummaryState(msg.payload);
            }
        }
    };
    ws.onclose = handleDisconnect;
    ws.onerror = (err) => { logDebug(`WebSocket error: ${err.message || 'Unknown error'}`); };
}

function stop() {
    logDebug("Stop button clicked");
    if (status === 'STOPPED') return;
    clearTimeout(reconnectTimeoutHandle);
    if (ws) {
        logDebug("Closing WebSocket connection");
        ws.onclose = null;
        ws.close();
        ws = null;
    }
    if (summaryUpdateInterval) clearInterval(summaryUpdateInterval);
    lastSummaryTimestamp = null;
    cleanupPlayer();
    cancelAnimationFrame(animationFrameHandle);
    status = 'STOPPED';
    mime = null;
    utteranceHistory = [];
    if (document.getElementById('transcript-content')) {
        document.getElementById('transcript-content').innerHTML = '';
    }
    updateUI();
    logDebug("Player stopped and reset");
}

function handleDisconnect() {
    if (status === 'STOPPED') return;
    if (status === 'WAITING') {
        logDebug("Disconnected from waiting room. Reverting to STOPPED state.");
        cleanupPlayer();
        setTimeout(() => {
            status = 'STOPPED';
            updateUI();
        }, 3000);
        return;
    }
    cleanupPlayer();
    status = 'RECONNECTING';
    updateUI();
    console.log("Connection lost. Attempting to reconnect in 3 seconds...");
    reconnectTimeoutHandle = setTimeout(play, 3000);
}

// --- PLAYER & MEDIA SOURCE LOGIC ---
function initializePlayer() {
    mediaSource = new MediaSource();
    audio.src = URL.createObjectURL(mediaSource);
    audio.muted = false;
    audio.volume = volumeSlider.value / 100;
    const onSourceOpen = () => {
        logDebug("MediaSource opened. Ready for buffer.");
        if (mime) setupBuffer();
    };
    mediaSource.addEventListener('sourceopen', onSourceOpen, { once: true });
    audio.play().catch(e => logDebug(`MediaSource play failed: ${e.message}`));
}

function cleanupPlayer() {
    if (audio) {
        audio.pause();
        if (mediaSource && mediaSource.readyState === 'open') {
            try { mediaSource.endOfStream(); }
            catch (e) { console.warn("Error during endOfStream:", e.message); }
        }
        audio.src = '';
        audio.removeAttribute('src');
        audio.load();
    }
    mediaSource = null;
    sourceBuffer = null;
    bufferQueue = [];
}

function handleConfig(payload) {
    mime = payload.mime;
    if (mediaSource && mediaSource.readyState === 'open') setupBuffer();
}

function setupBuffer() {
    if (!mime || !mediaSource || mediaSource.readyState !== 'open' || sourceBuffer) return;
    try {
        logDebug(`Adding source buffer with MIME type: ${mime}`);
        sourceBuffer = mediaSource.addSourceBuffer(mime);
        sourceBuffer.mode = 'sequence';
        sourceBuffer.addEventListener('updateend', appendNext);
        appendNext();
    } catch (e) { console.error("Error setting up source buffer:", e); }
}

function handleAudio(bytes) {
    bufferQueue.push(bytes);
    if (sourceBuffer && !sourceBuffer.updating) appendNext();
}

function appendNext() {
    if (sourceBuffer && !sourceBuffer.updating && bufferQueue.length > 0) {
        try { sourceBuffer.appendBuffer(bufferQueue.shift()); }
        catch (e) { console.error("Error appending buffer:", e); }
    }
}

// --- PERFORMANCE INFO HANDLING ---
function handlePerformanceInfo(payload) {
    console.log('🔧 DEBUG: handlePerformanceInfo called with:', payload);
    
    performanceInfo = payload;
    
    // Immediate test of the indicator
    console.log('🔍 DEBUG: performanceModeIndicator element:', performanceModeIndicator);
    
    if (!performanceModeIndicator) {
        console.error('❌ DEBUG: Performance indicator not available, attempting to find it again...');
        performanceModeIndicator = document.getElementById('performance-mode-indicator');
        
        if (!performanceModeIndicator) {
            console.error('❌ DEBUG: Still cannot find performance-mode-indicator element!');
            console.log('🔍 DEBUG: Searching for similar elements...');
            
            // Search for any element that might be the performance indicator
            const candidateElements = [
                document.querySelector('.performance-mode'),
                document.querySelector('[class*="performance"]'),
                document.querySelector('[id*="performance"]'),
                document.querySelector('.sub-info span:last-child')
            ];
            
            candidateElements.forEach((el, index) => {
                console.log(`🔍 DEBUG: Candidate ${index}:`, el);
            });
            
            // Try to create the element if it doesn't exist
            const subInfo = document.querySelector('.sub-info');
            if (subInfo) {
                console.log('🔧 DEBUG: Creating missing performance indicator element');
                const indicator = document.createElement('span');
                indicator.id = 'performance-mode-indicator';
                indicator.className = 'performance-mode';
                indicator.style.cssText = 'margin-left: 10px; padding: 2px 6px; background: #333; border-radius: 3px; font-size: 12px; font-weight: bold;';
                subInfo.appendChild(indicator);
                performanceModeIndicator = indicator;
                console.log('✅ DEBUG: Performance indicator created:', indicator);
            }
        } else {
            console.log('✅ DEBUG: Found performance indicator on second attempt');
        }
    }
    
    updatePerformanceModeIndicator();
    
    // Log performance info for debugging
    console.log('🎯 Performance Mode:', payload.mode);
    console.log('⚙️ Configuration:', payload);
    
    // Add to debug panel if available
    if (debugContent) {
        const perfInfo = `Performance Mode: ${payload.mode}\n` +
                        `ASR Threads: ${payload.asr_threads}\n` +
                        `Chunk Size: ${payload.chunk_size}\n` +
                        `Max Connections: ${payload.max_connections}\n` +
                        `Summarizer: ${payload.enable_summarizer ? 'Enabled' : 'Disabled'}`;
        
        const existingPerfDiv = debugContent.querySelector('.performance-info');
        if (existingPerfDiv) {
            existingPerfDiv.textContent = perfInfo;
        } else {
            const perfDiv = document.createElement('div');
            perfDiv.className = 'performance-info';
            perfDiv.style.cssText = 'margin: 10px 0; padding: 8px; background: rgba(0,255,0,0.1); border-radius: 4px; font-family: monospace; font-size: 12px; white-space: pre-line;';
            perfDiv.textContent = perfInfo;
            debugContent.insertBefore(perfDiv, debugContent.firstChild);
        }
    }
}

function updatePerformanceModeIndicator() {
    console.log('🎨 DEBUG: updatePerformanceModeIndicator called');
    console.log('🔍 DEBUG: performanceModeIndicator:', performanceModeIndicator);
    console.log('🔍 DEBUG: performanceInfo:', performanceInfo);
    
    if (!performanceModeIndicator) {
        console.error('❌ DEBUG: No performance indicator element available');
        return;
    }
    
    if (!performanceInfo) {
        console.error('❌ DEBUG: No performance info available');
        return;
    }
    
    const mode = performanceInfo.mode;
    console.log('🎯 DEBUG: Processing mode:', mode);
    
    const modeConfig = {
        'ultra_low': { 
            text: '🔧 ULTRA LOW', 
            color: '#ff6b6b', 
            title: 'Ultra Low Resource Mode - Summarizer Disabled' 
        },
        'low_resource': { 
            text: '⚡ LOW RESOURCE', 
            color: '#ffd93d', 
            title: 'Low Resource Mode - Optimized for HF Spaces' 
        },
        'normal': { 
            text: '🚀 NORMAL', 
            color: '#6bcf7f', 
            title: 'Normal Mode - Full Features' 
        }
    };
    
    const config = modeConfig[mode] || { 
        text: `🔧 ${mode.toUpperCase()}`, 
        color: '#888', 
        title: `Performance Mode: ${mode}` 
    };
    
    console.log('🎨 DEBUG: Applying config:', config);
    
    performanceModeIndicator.textContent = config.text;
    performanceModeIndicator.style.color = config.color;
    performanceModeIndicator.title = config.title;
    
    // Force visibility
    performanceModeIndicator.style.display = 'inline';
    performanceModeIndicator.style.visibility = 'visible';
    
    console.log('✅ DEBUG: Performance indicator updated successfully');
    console.log('🔍 DEBUG: Final element state:', {
        textContent: performanceModeIndicator.textContent,
        style: performanceModeIndicator.style.cssText,
        outerHTML: performanceModeIndicator.outerHTML
    });
}

// DEBUG: Manual test function
function testPerformanceIndicator() {
    console.log('🧪 MANUAL TEST: testPerformanceIndicator called');
    
    const indicator = document.getElementById('performance-mode-indicator');
    console.log('🔍 TEST: Found indicator:', indicator);
    
    if (indicator) {
        indicator.textContent = '🧪 MANUAL TEST';
        indicator.style.color = '#ff0000';
        indicator.style.backgroundColor = '#ffff00';
        indicator.style.padding = '4px 8px';
        indicator.style.borderRadius = '4px';
        console.log('✅ TEST: Manual styling applied');
        
        // Test with performance info
        setTimeout(() => {
            console.log('🔄 TEST: Testing with fake performance info...');
            handlePerformanceInfo({
                mode: 'low_resource',
                asr_threads: 1,
                chunk_size: 3200,
                enable_summarizer: true,
                max_connections: 1
            });
        }, 2000);
    } else {
        console.error('❌ TEST: Indicator not found!');
        alert('Performance indicator not found! Check console for details.');
    }
}

// Make function available globally for the HTML button
window.testPerformanceIndicator = testPerformanceIndicator;

// --- TRANSCRIPTION & HIGHLIGHTING LOGIC ---
function handleAsr(asrPayload) {
    if (!audio || audio.paused || audio.readyState < 2) return;
    const lastUtterance = utteranceHistory.length > 0 ? utteranceHistory[utteranceHistory.length - 1] : null;
    if (!lastUtterance || lastUtterance.is_final) {
        const clientAnchorTime = audio.currentTime;
        asrPayload.startTimeInCtx = clientAnchorTime;
        if (typeof asrPayload.absolute_start_time === 'number') {
            const serverAnchorTime = asrPayload.absolute_start_time;
            const measuredLag = clientAnchorTime - serverAnchorTime;
            userSyncOffset = (1 - SMOOTHING_FACTOR) * userSyncOffset + SMOOTHING_FACTOR * measuredLag;
            syncSlider.value = userSyncOffset;
            syncValueSpan.textContent = `${userSyncOffset.toFixed(2)}s`;
        }
        handleUtteranceHistory(asrPayload);
    } else {
        asrPayload.absolute_start_time = lastUtterance.absolute_start_time;
        asrPayload.startTimeInCtx = lastUtterance.startTimeInCtx;
        utteranceHistory[utteranceHistory.length - 1] = asrPayload;
        updateLastUtterance(asrPayload);
    }
}

function handleUtteranceHistory(newUtterance) {
    const contentContainer = document.getElementById('transcript-content');
    utteranceHistory.push(newUtterance);
    if (utteranceHistory.length > MAX_HISTORY_LENGTH) {
        utteranceHistory.shift();
        if (contentContainer && contentContainer.firstChild) {
            contentContainer.removeChild(contentContainer.firstChild);
        }
    }
    renderNewUtterance(newUtterance);
}

function renderNewUtterance(utterance) {
    const contentContainer = document.getElementById('transcript-content');
    if (!contentContainer) return;
    const utteranceDiv = document.createElement('div');
    utteranceDiv.className = 'utterance';
    if (utterance.is_final) utteranceDiv.classList.add('final');
    if (utterance.utterance_id) {
        utteranceDiv.id = `utterance-${utterance.utterance_id}`;
    }
    const processedTokens = processAsrTokens(utterance.tokens);
    let content = '';
    processedTokens.forEach((token) => { content += `<span>${escapeHtml(token)}</span>`; });
    utteranceDiv.innerHTML = content;
    contentContainer.appendChild(utteranceDiv);
    scrollToLastUtterance(true);
}

function updateLastUtterance(utterance) {
    const contentContainer = document.getElementById('transcript-content');
    if (!contentContainer || !contentContainer.lastElementChild) return;
    const lastUtteranceDiv = contentContainer.lastElementChild;
    if (utterance.is_final) lastUtteranceDiv.classList.add('final');
    if (utterance.utterance_id) {
        lastUtteranceDiv.id = `utterance-${utterance.utterance_id}`;
    }
    const processedTokens = processAsrTokens(utterance.tokens);
    let content = '';
    processedTokens.forEach((token) => { content += `<span>${escapeHtml(token)}</span>`; });
    lastUtteranceDiv.innerHTML = content;
    scrollToLastUtterance();
}

function startKaraokeLoop() {
    if (animationFrameHandle) cancelAnimationFrame(animationFrameHandle);
    function loop() {
        updateHighlights();
        animationFrameHandle = requestAnimationFrame(loop);
    }
    loop();
}

function updateHighlights() {
    if (status !== 'PLAYING' || !audio || utteranceHistory.length === 0) return;
    const effectiveSyncTime = audio.currentTime - userSyncOffset;
    const contentContainer = document.getElementById('transcript-content');
    if (!contentContainer) return;

    let utteranceIndex = -1;
    for (let i = utteranceHistory.length - 1; i >= 0; i--) {
        if (utteranceHistory[i].absolute_start_time + utteranceHistory[i].start_time <= effectiveSyncTime) {
            utteranceIndex = i;
            break;
        }
    }
    if (utteranceIndex === -1) return;

    const utterance = utteranceHistory[utteranceIndex];
    if (!utterance) return;
    let tokenIndex = -1;
    for (let j = 0; j < utterance.timestamps.length; j++) {
        if (utterance.absolute_start_time + utterance.timestamps[j] <= effectiveSyncTime) {
            tokenIndex = j;
        } else { break; }
    }
    
    let newHighlightSpan = null;
    if (tokenIndex > -1) {
        const utteranceDivs = contentContainer.querySelectorAll('.utterance');
        if (utteranceIndex < utteranceDivs.length) {
            const tokenSpans = utteranceDivs[utteranceIndex].querySelectorAll('span');
            if (tokenIndex < tokenSpans.length) {
                newHighlightSpan = tokenSpans[tokenIndex];
            }
        }
    }

    if (newHighlightSpan !== currentHighlightedSpan) {
        if (currentHighlightedSpan) {
            currentHighlightedSpan.classList.remove('highlight');
        }
        if (newHighlightSpan) {
            newHighlightSpan.classList.add('highlight');
        }
        currentHighlightedSpan = newHighlightSpan;
    }
}

// --- UTILITY & HELPER FUNCTIONS ---
function scrollToLastUtterance(forceScroll = false) {
    const container = document.getElementById('transcript-container');
    if (container && (forceScroll || container.scrollTop >= container.scrollHeight - container.clientHeight - 100)) {
        container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    }
}

function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function getStationLanguage(stationName) {
    const frenchStations = ["France Inter", "France Info", "France Culture", "FIP", "Radio Classique"];
    const mandarinStations = ["中廣新聞網", "News98新聞網", "飛碟聯播網"];
    if (frenchStations.includes(stationName)) return 'fr';
    if (mandarinStations.includes(stationName)) return 'zh';
    return 'en';
}

function updateLanguageIndicator(languagePayload = null) {
    if (languageIndicator) {
        const languageNames = { 
            'en': 'English', 
            'fr': 'French', 
            'zh': 'Mandarin',
            'es': 'Spanish',
            'de': 'German', 
            'it': 'Italian',
            'pt': 'Portuguese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ru': 'Russian',
            'ar': 'Arabic',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'no': 'Norwegian',
            'da': 'Danish',
            'pl': 'Polish',
            'tr': 'Turkish',
            'th': 'Thai',
            'vi': 'Vietnamese'
        };
        
        if (languagePayload && languagePayload.is_fallback) {
            const detectedName = languageNames[languagePayload.detected_language] || languagePayload.detected_language;
            const asrName = languageNames[languagePayload.asr_language] || languagePayload.asr_language;
            languageIndicator.innerHTML = `${detectedName} → ${asrName} <span style="color: #ffa500;">⚠</span>`;
            languageIndicator.title = `Station language: ${detectedName}. Using ${asrName} ASR model (closest match).`;
        } else {
            const langName = languageNames[currentLanguage] || 'Unknown';
            languageIndicator.textContent = langName;
            languageIndicator.title = `ASR Language: ${langName}`;
        }
    }
}

function showLanguageFallbackNotification(languagePayload) {
    const notification = document.createElement('div');
    notification.className = 'language-fallback-notification';
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">⚠️</span>
            <div class="notification-text">
                <strong>Language Notice:</strong> 
                ${languagePayload.fallback_message || 
                  `Station language not fully supported. Using closest available ASR model.`}
            </div>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    // Add to page (create notification container if it doesn't exist)
    let container = document.querySelector('.notifications-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'notifications-container';
        document.body.appendChild(container);
    }
    
    container.appendChild(notification);
    
    // Auto-hide after 8 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 8000);
}

function processTokens(tokens) {
    if (!Array.isArray(tokens)) return tokens;
    return tokens.map(t => t === ' ' ? ' ' : t);
}

// --- DEBUG FUNCTIONS ---
function logDebug(message) {
    if (!debugContent) return;
    if (!debugMode && (!debugPanel || !debugPanel.classList.contains('visible'))) return;
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    const logEntry = document.createElement('li');
    logEntry.textContent = `[${timeString}] ${message}`;
    if (debugContent.firstChild) {
        debugContent.insertBefore(logEntry, debugContent.firstChild);
    } else {
        debugContent.appendChild(logEntry);
    }
    while (debugContent.children.length > 50) {
        debugContent.removeChild(debugContent.lastChild);
    }
}

window.toggleDebug = function() {
    debugMode = !debugMode;
    if (debugPanel) debugPanel.classList.toggle('visible', debugMode);
    logDebug(`Debug mode ${debugMode ? 'enabled' : 'disabled'}`);
};

function updateSummary(payload) {
    if (summaryText && typeof marked !== 'undefined' && typeof DOMPurify !== 'undefined') {
        lastSummaryTimestamp = new Date(payload.timestamp);
        highlightSummarizedUtterances(payload.source_utterance_ids);
        const dirtyHtml = marked.parse(payload.summary);
        const cleanHtml = DOMPurify.sanitize(dirtyHtml);
        summaryText.innerHTML = cleanHtml;
        summaryText.closest('.summary-content').style.opacity = 1;
        updateTimeAgo();
        if (summaryUpdateInterval) clearInterval(summaryUpdateInterval);
        summaryUpdateInterval = setInterval(updateTimeAgo, 5000);
        hasReceivedFirstSummary = true;
    }
}

function highlightSummarizedUtterances(ids) {
    if (!Array.isArray(ids)) return;
    document.querySelectorAll('.utterance.summarized').forEach(el => {
        el.classList.remove('summarized');
    });
    ids.forEach(id => {
        const el = document.getElementById(`utterance-${id}`);
        if (el) {
            el.classList.add('summarized');
        }
    });
}

function updateTimeAgo() {
    const timestampEl = document.getElementById('summary-timestamp');
    if (!timestampEl || !lastSummaryTimestamp) return;
    const now = new Date();
    const seconds = Math.round((now - lastSummaryTimestamp) / 1000);
    if (seconds < 10) {
        timestampEl.textContent = "just now";
    } else if (seconds < 60) {
        timestampEl.textContent = `${seconds} seconds ago`;
    } else {
        const minutes = Math.round(seconds / 60);
        timestampEl.textContent = minutes === 1 ? "a minute ago" : `${minutes} minutes ago`;
    }
}

function handleSummaryState(payload) {
    if (!summaryText) return;
    switch (payload.status) {
        case 'loading':
            summaryText.textContent = "Initializing summarizer model...";
            break;
        case 'ready':
            if (!hasReceivedFirstSummary) {
                summaryText.textContent = "Waiting for enough content to generate a summary...";
            }
            break;
        case 'summarizing':
            summaryText.textContent = "Generating new summary...";
            break;
    }
}

// --- VOLUME CONTROL FUNCTIONS ---
function handleVolumeChange() {
    const volume = volumeSlider.value / 100;
    audio.volume = volume;
    audio.muted = volume === 0;
    if (volume > 0) {
        lastVolume = volume;
    }
    updateMuteButtonIcon();
}

function toggleMute() {
    audio.muted = !audio.muted;
    if (audio.muted) {
        lastVolume = audio.volume > 0 ? audio.volume : lastVolume;
        volumeSlider.value = 0;
        audio.volume = 0;
    } else {
        audio.volume = lastVolume;
        volumeSlider.value = lastVolume * 100;
    }
    updateMuteButtonIcon();
}

function updateMuteButtonIcon() {
    if (audio.muted || audio.volume === 0) {
        muteBtn.textContent = '🔇';
        muteBtn.title = 'Unmute';
    } else {
        muteBtn.textContent = '🔊';
        muteBtn.title = 'Mute';
    }
}

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', () => {
    // Assign DOM elements
    dynamicBackground = document.getElementById('dynamic-background');
    stationModal = document.getElementById('station-modal');
    openStationModalBtn = document.getElementById('open-station-modal-btn');
    closeStationModalBtn = document.getElementById('close-station-modal-btn');
    stationListContainer = document.getElementById('station-list');
    playerStationLogo = document.getElementById('player-station-logo');
    playerStationName = document.getElementById('player-station-name');
    playBtn = document.getElementById('playBtn');
    stopBtn = document.getElementById('stopBtn');
    languageIndicator = document.getElementById('language-indicator');
    userCountIndicator = document.getElementById('user-count-indicator');
    performanceModeIndicator = document.getElementById('performance-mode-indicator');  // NEW
    
    // DEBUG: Check if performance indicator was found
    console.log('🔍 DEBUG: Performance indicator element:', performanceModeIndicator);
    if (!performanceModeIndicator) {
        console.error('❌ DEBUG: performance-mode-indicator element not found in DOM!');
        console.log('🔍 DEBUG: Available elements with "performance" in ID:');
        document.querySelectorAll('[id*="performance"]').forEach(el => {
            console.log('  -', el.id, el);
        });
    } else {
        console.log('✅ DEBUG: Performance indicator found successfully');
        // Test immediate display
        performanceModeIndicator.textContent = 'INITIALIZING...';
        performanceModeIndicator.style.color = '#orange';
    }
    
    syncSlider = document.getElementById('sync-offset-slider');
    syncValueSpan = document.getElementById('sync-offset-value');
    debugPanel = document.getElementById('debug-panel');
    debugContent = document.getElementById('debug-content');
    audio = document.getElementById('player');
    muteBtn = document.getElementById('muteBtn');
    volumeSlider = document.getElementById('volumeSlider');
    summaryTimestamp = document.getElementById('summary-timestamp');
    summaryText = document.getElementById('summary-text');

    // NEW: Station discovery elements
    stationSearchInput = document.getElementById('station-search');
    searchBtn = document.getElementById('search-btn');
    countryFilter = document.getElementById('country-filter');
    languageFilter = document.getElementById('language-filter');
    categoryFilter = document.getElementById('category-filter');
    discoverStationsContainer = document.getElementById('discover-stations');
    newsStationsContainer = document.getElementById('news-stations');
    popularStationsContainer = document.getElementById('popular-stations');
    loadingIndicator = document.getElementById('loading-indicator');

    // Debounced discover function reference (shared)
    let debouncedDiscover = null;

    // Attach Event Listeners
    if (openStationModalBtn) openStationModalBtn.addEventListener('click', openStationModal);
    if (closeStationModalBtn) closeStationModalBtn.addEventListener('click', closeStationModal);
    if (stationModal) {
        stationModal.addEventListener('click', (event) => {
            if (event.target === stationModal) closeStationModal();
        });
    }
    
    // NEW: Station discovery event listeners
    if (searchBtn) {
        debouncedDiscover = (searchQuery, country, language, category) => {
            // Create a signature for this request
            const sig = `${searchQuery}||${country}||${language}||${category}`;

            // If identical to last request within short window, skip
            if (sig === _lastDiscoverSignature) {
                console.debug('discoverStations: duplicate request skipped', sig);
                if (loadingIndicator) loadingIndicator.innerHTML = `<div style="color:#999;padding:8px;">⏱️ Duplicate request skipped</div>`;
                return;
            }

            // Clear previous debounce
            if (_discoverDebounceHandle) clearTimeout(_discoverDebounceHandle);

            _discoverDebounceHandle = setTimeout(() => {
                _lastDiscoverSignature = sig;
                discoverStations(searchQuery, country, language, category);
                // Reset signature after 3s to allow re-queries
                setTimeout(() => { if (_lastDiscoverSignature === sig) _lastDiscoverSignature = null; }, 3000);
            }, 300); // 300ms debounce
        };

        searchBtn.addEventListener('click', () => {
            const searchQuery = stationSearchInput?.value || '';
            const country = countryFilter?.value || '';
            const language = languageFilter?.value || '';
            const category = categoryFilter?.value || 'popular';
            debouncedDiscover(searchQuery.trim(), country, language, category);
        });
    }
    
    if (stationSearchInput) {
        stationSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchBtn?.click();
            }
        });
    }
    
    // Tab switching for station modal
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            if (tabName) switchTab(tabName);
        });
    });
    
    if (syncSlider) {
        syncSlider.addEventListener('input', () => {
            const newOffset = parseFloat(syncSlider.value);
            syncValueSpan.textContent = `${newOffset.toFixed(2)}s`;
            userSyncOffset = newOffset;
        });
    }
    if (muteBtn) muteBtn.addEventListener('click', toggleMute);
    if (volumeSlider) volumeSlider.addEventListener('input', handleVolumeChange);

    // Run Startup Functions
    logDebug("Page loaded. Initializing application.");
    loadStations();
    getInitialStatus();
    updateUI();
    
    // NEW: Load station categories for discovery
    loadStationCategories();

    // Debug: confirm discovery UI elements and listeners
    console.debug('Discovery init:', {
        searchBtnExists: !!searchBtn,
        searchInputExists: !!stationSearchInput,
        countryFilterExists: !!countryFilter,
        languageFilterExists: !!languageFilter
    });
    if (searchBtn && stationSearchInput) {
        console.debug('Attached search click listener and enter key listener');
    } else {
        console.warn('Discovery UI missing elements. Search may not function correctly.');
    }

    // Initialize OpenCC-JS for S2T conversion
    (async () => {
        if (typeof OpenCC !== 'undefined') {
            try {
                s2tConverter = await OpenCC.Converter({ from: 'cn', to: 'twp' });
                logDebug("Simplified to Traditional Chinese converter loaded successfully.");
            } catch (e) {
                console.error("Failed to load OpenCC converter:", e);
                logDebug("ERROR: Failed to load S2T converter.");
            }
        } else {
            console.error("OpenCC library not found. S2T conversion will not work.");
            logDebug("ERROR: OpenCC.js library not found.");
        }
    })();
});