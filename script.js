let count = 0;
const maxRequirements = 20;
let shortlistCount = 0;
const maxShortlist = 20;

// ============================================
// GLOBAL VARIABLES
// ============================================

let authToken = null;
let currentUsername = null;
const API_URL = 'http://127.0.0.1:5000';

// Map variables
let map = null;
let markers = [];
let mapInitialized = false;

// ============================================
// CHECK AUTHENTICATION ON PAGE LOAD
// ============================================

function checkAuth() {
  const storedToken = localStorage.getItem('authToken');
  const storedUsername = localStorage.getItem('currentUsername');

  if (storedToken && storedUsername) {
    verifyTokenWithBackend(storedToken);
  } else {
    showLoginScreen();
  }
}

async function verifyTokenWithBackend(token) {
  try {
    const response = await fetch(`${API_URL}/verify_token`, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.ok) {
      authToken = token;
      currentUsername = localStorage.getItem('currentUsername');
      showAppScreen();
    } else {
      localStorage.removeItem('authToken');
      localStorage.removeItem('currentUsername');
      showLoginScreen();
    }
  } catch (err) {
    console.error('Token verification failed:', err);
    showLoginScreen();
  }
}

function showLoginScreen() {
  document.getElementById('authContainer').style.display = 'flex';
  document.getElementById('app').style.display = 'none';
}

function showAppScreen() {
  document.getElementById('authContainer').style.display = 'none';
  document.getElementById('app').style.display = 'block';
  document.getElementById('userDisplay').textContent = `Welcome, ${currentUsername}!`;
  
  // Load user-specific data after login
  loadRequirements();
  loadShortlist();
  loadHistory();
}

// ============================================
// AUTHENTICATION FUNCTIONS
// ============================================

function handleLogout() {
  authToken = null;
  currentUsername = null;
  localStorage.removeItem('authToken');
  localStorage.removeItem('currentUsername');
  clearAuthInputs();
  
  const msg = document.getElementById('message');
  if (msg) {
    msg.textContent = '';
    msg.style.display = 'none';
    msg.className = 'message';
  }
  
  document.getElementById('loginForm').classList.remove('hidden');
  document.getElementById('registerForm').classList.add('hidden');
  showLoginScreen();
}

function toggleForms() {
  document.getElementById('loginForm').classList.toggle('hidden');
  document.getElementById('registerForm').classList.toggle('hidden');
  document.getElementById('message').textContent = '';
  clearAuthInputs();
}

function clearAuthInputs() {
  document.getElementById('loginUsername').value = '';
  document.getElementById('loginPassword').value = '';
  document.getElementById('registerUsername').value = '';
  document.getElementById('registerEmail').value = '';
  document.getElementById('registerPassword').value = '';
  document.getElementById('confirmPassword').value = '';
}

function showMessage(text, isError = false) {
  const msg = document.getElementById('message');
  msg.textContent = text;
  msg.className = `message ${isError ? 'error' : 'success'}`;
  msg.style.display = 'block';
  setTimeout(() => {
    msg.textContent = '';
    msg.className = 'message';
    msg.style.display = 'none';
  }, 4000);
}

async function handleLogin() {
  const username = document.getElementById('loginUsername').value.trim();
  const password = document.getElementById('loginPassword').value;

  if (!username || !password) {
    showMessage('Please enter username and password', true);
    return;
  }

  try {
    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    const data = await response.json();

    if (!response.ok) {
      showMessage(data.error || 'Login failed', true);
      return;
    }

    authToken = data.token;
    currentUsername = data.username;
    showMessage('Login successful!');
    
    localStorage.setItem('authToken', authToken);
    localStorage.setItem('currentUsername', currentUsername);
    
    setTimeout(() => {
      showAppScreen();
      clearAuthInputs();
    }, 1000);
  } catch (err) {
    showMessage('Login failed: ' + err.message, true);
    console.error('Login error:', err);
  }
}

async function handleRegister() {
  const username = document.getElementById('registerUsername').value.trim();
  const email = document.getElementById('registerEmail').value.trim();
  const password = document.getElementById('registerPassword').value;
  const confirm = document.getElementById('confirmPassword').value;

  if (!username || !email || !password || !confirm) {
    showMessage('Please fill all fields', true);
    return;
  }

  if (password.length < 6) {
    showMessage('Password must be at least 6 characters', true);
    return;
  }

  if (password !== confirm) {
    showMessage('Passwords do not match', true);
    return;
  }

  try {
    const response = await fetch(`${API_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        username, 
        email, 
        password, 
        confirm_password: confirm 
      })
    });

    const data = await response.json();

    if (!response.ok) {
      showMessage(data.error || 'Registration failed', true);
      return;
    }

    showMessage('Registration successful! Please log in.');
    setTimeout(toggleForms, 1500);
    clearAuthInputs();
  } catch (err) {
    showMessage('Registration failed: ' + err.message, true);
    console.error('Register error:', err);
  }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, c =>
    ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]
  );
}

function toggleTheme() {
  document.body.classList.toggle("light-mode");
  const isLight = document.body.classList.contains("light-mode");
  document.getElementById("themeToggle").textContent = isLight ? "Dark Mode" : "Light Mode";
}

// ============================================
// SCRAPING & HISTORY
// ============================================

async function getResults() {
  if (!authToken) {
    document.getElementById("output").textContent = "Please log in first.";
    return;
  }

  const url = document.getElementById("urlInput").value;
  const output = document.getElementById("output");
  
  if (!url) {
    output.textContent = "Please enter a Rightmove URL.";
    return;
  }

  try {
    const response = await fetch(`${API_URL}/scrape?url=${encodeURIComponent(url)}`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    
    if (!response.ok) {
      const text = await response.text();
      output.textContent = `Backend error ${response.status}: ${text}`;
      return;
    }

    const data = await response.json();

    if (data.results != null) {
      output.textContent = `Number of results: ${data.results}`;
      if (data.history) {
        displayHistory(data.history);
      } else {
        loadHistory();
      }
    } else {
      output.textContent = `Error: ${data.error || 'Unknown error from backend'}`;
    }
  } catch (err) {
    console.error('getResults error', err);
    output.textContent = "Failed to connect to backend. Check console/network.";
  }
}

async function loadHistory() {
  if (!authToken) return;
  
  try {
    const response = await fetch(`${API_URL}/history`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    
    if (!response.ok) {
      console.error('History fetch failed', response.status);
      return;
    }
    const history = await response.json();
    displayHistory(history);
  } catch (err) {
    console.error('loadHistory error', err);
  }
}

function displayHistory(historyData) {
  const historyEl = document.getElementById("history") || createHistoryEl();
  const items = Array.isArray(historyData) ? historyData : [historyData];

  let html = "<h3>Results History:</h3><ul>";
  items.forEach(entry => {
    const date = entry.date || new Date().toLocaleString();
    const results = (entry.results != null) ? entry.results : '—';
    html += `<li>${escapeHtml(date)}: ${escapeHtml(results)} results</li>`;
  });
  html += "</ul>";

  historyEl.innerHTML = html;
}

function createHistoryEl() {
  const el = document.createElement('div');
  el.id = 'history';
  const output = document.getElementById('output');
  output.parentNode.insertBefore(el, output.nextSibling);
  return el;
}

// ============================================
// REQUIREMENTS
// ============================================

async function saveRequirements() {
  if (!authToken) return;
  
  const list = document.getElementById("list");
  const reqs = [];
  list.querySelectorAll(".requirement").forEach(reqDiv => {
    const checkbox = reqDiv.querySelector("input[type=checkbox]");
    const textInput = reqDiv.querySelector("input[type=text]");
    reqs.push({
      checked: checkbox.checked,
      text: textInput.value
    });
  });
  
  try {
    await fetch(`${API_URL}/requirements`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({ requirements: reqs })
    });
  } catch (err) {
    console.error('Failed to save requirements:', err);
  }
}

async function loadRequirements() {
  if (!authToken) return;
  
  try {
    const response = await fetch(`${API_URL}/requirements`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    
    if (!response.ok) {
      console.error('Failed to load requirements');
      return;
    }
    
    const saved = await response.json();
    const list = document.getElementById("list");
    list.innerHTML = "";
    count = 0;
    
    (saved || []).forEach(req => {
      addRequirement(req.text, req.checked);
    });
  } catch (err) {
    console.error('Failed to load requirements:', err);
  }
}

function addRequirement(text = "", checked = false) {
  if (count >= maxRequirements) return;
  count++;

  const list = document.getElementById("list");

  const reqDiv = document.createElement("div");
  reqDiv.className = "requirement";

  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.checked = checked;
  checkbox.addEventListener("change", saveRequirements);

  const textInput = document.createElement("input");
  textInput.type = "text";
  textInput.placeholder = "Enter requirement...";
  textInput.value = text;
  textInput.addEventListener("input", saveRequirements);

  const delBtn = document.createElement("button");
  delBtn.textContent = "❌";
  delBtn.onclick = () => {
    list.removeChild(reqDiv);
    count--;
    document.getElementById("addBtn").disabled = false;
    saveRequirements();
  };

  reqDiv.appendChild(checkbox);
  reqDiv.appendChild(textInput);
  reqDiv.appendChild(delBtn);

  list.appendChild(reqDiv);

  if (count >= maxRequirements) {
    document.getElementById("addBtn").disabled = true;
  }

  saveRequirements();
}

// ============================================
// SHORTLIST
// ============================================

async function saveShortlist() {
  if (!authToken) return;
  
  const list = document.getElementById("shortlist");
  const items = [];
  list.querySelectorAll(".short-item").forEach(itemDiv => {
    const inputs = itemDiv.querySelectorAll("input[type=text]");
    items.push({
      address: inputs[0].value,
      price: inputs[1].value,
      bedrooms: inputs[2].value,
      type: inputs[3].value,
      link: inputs[4].value
    });
  });
  
  try {
    await fetch(`${API_URL}/shortlist`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({ shortlist: items })
    });
    
    // Refresh map if it's visible
    if (mapInitialized && document.getElementById('mapContainer').style.display !== 'none') {
      await loadMap();
    }
  } catch (err) {
    console.error('Failed to save shortlist:', err);
  }
}

async function loadShortlist() {
  if (!authToken) return;
  
  try {
    const response = await fetch(`${API_URL}/shortlist`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    
    if (!response.ok) {
      console.error('Failed to load shortlist');
      return;
    }
    
    const saved = await response.json();
    const list = document.getElementById("shortlist");
    list.innerHTML = "";
    shortlistCount = 0;
    
    (saved || []).forEach(item => {
      addShortlistItem(item.address, item.price, item.bedrooms, item.type, item.link);
    });
  } catch (err) {
    console.error('Failed to load shortlist:', err);
  }
}

function addShortlistItem(address = "", price = "", bedrooms = "", type = "", link = "") {
  if (shortlistCount >= maxShortlist) return;
  shortlistCount++;

  const list = document.getElementById("shortlist");

  const itemDiv = document.createElement("div");
  itemDiv.className = "short-item";
  itemDiv.style.display = "flex";
  itemDiv.style.flexDirection = "column";
  itemDiv.style.gap = "8px";

  const inputContainer = document.createElement("div");
  inputContainer.style.display = "flex";
  inputContainer.style.gap = "8px";
  inputContainer.style.flexWrap = "wrap";

  const createInput = (placeholder, value) => {
    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = placeholder;
    input.value = value;
    input.style.flex = "1";
    input.style.minWidth = "150px";
    input.addEventListener("input", saveShortlist);
    return input;
  };

  const addressInput = createInput("Address", address);
  const priceInput = createInput("Price", price);
  const bedroomsInput = createInput("Bedrooms", bedrooms);
  const typeInput = createInput("Type", type);
  const linkInput = createInput("Rightmove Link", link);

  addressInput.style.flex = "2";
  linkInput.style.flex = "2";

  const delBtn = document.createElement("button");
  delBtn.textContent = "❌";
  delBtn.style.width = "auto";
  delBtn.style.padding = "8px 14px";
  delBtn.onclick = () => {
    list.removeChild(itemDiv);
    shortlistCount--;
    document.getElementById("addShortBtn").disabled = false;
    saveShortlist();
  };

  inputContainer.appendChild(addressInput);
  inputContainer.appendChild(priceInput);
  inputContainer.appendChild(bedroomsInput);
  inputContainer.appendChild(typeInput);
  inputContainer.appendChild(delBtn);

  itemDiv.appendChild(inputContainer);
  itemDiv.appendChild(linkInput);

  list.appendChild(itemDiv);

  if (shortlistCount >= maxShortlist) {
    document.getElementById("addShortBtn").disabled = true;
  }

  saveShortlist();
}

// ============================================
// MAP FUNCTIONALITY
// ============================================

function toggleMapView() {
  const mapContainer = document.getElementById('mapContainer');
  const viewMapBtn = document.getElementById('viewMapBtn');
  const loadingMessage = document.getElementById('mapLoadingMessage');
  
  if (mapContainer.style.display === 'none') {
    mapContainer.style.display = 'block';
    loadingMessage.style.display = 'none';
    viewMapBtn.textContent = 'Hide Map';
    if (!mapInitialized) {
      initializeMap();
    }
    loadMap();
  } else {
    mapContainer.style.display = 'none';
    loadingMessage.style.display = 'block';
    viewMapBtn.textContent = 'View Map';
  }
}

function initializeMap() {
  if (!map) {

      const mapElement = document.getElementById('map');
    mapElement.style.width = '100%';
    mapElement.style.height = '600px'; 
    
    map = L.map('map').setView([51.5074, -0.1278], 10);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19
    }).addTo(map);
    
    mapInitialized = true;
  }
}

async function loadMap() {
  if (!authToken || !map) return;
  
  updateMapStatus('Loading properties...', true);
  
  try {
    const response = await fetch(`${API_URL}/shortlist`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    
    if (!response.ok) {
      updateMapStatus('Failed to load properties', false);
      return;
    }
    
    const shortlist = await response.json();
    
    if (shortlist.length === 0) {
      updateMapStatus('No properties in shortlist', false);
      return;
    }
    
    // Clear existing markers
    markers.forEach(marker => marker.remove());
    markers = [];
    
    const bounds = [];
    let geocodedCount = 0;
    
    updateMapStatus(`Geocoding ${shortlist.length} properties...`, true);
    
    for (let i = 0; i < shortlist.length; i++) {
      const property = shortlist[i];
      
      if (!property.address) continue;
      
      // Check if we already have coordinates
      if (!property.coordinates) {
        const coords = await geocodeAddress(property.address);
        if (coords) {
          property.coordinates = coords;
          geocodedCount++;
        }
      }
      
      if (property.coordinates) {
        const marker = L.marker([property.coordinates.lat, property.coordinates.lon])
          .addTo(map)
          .bindPopup(`
            <div>
              <h3>${property.price || 'Price not set'}</h3>
              <p><strong>${property.address}</strong></p>
              <p>${property.bedrooms || '?'} bed • ${property.type || 'Type not set'}</p>
              ${property.link ? `<a href="${property.link}" target="_blank">View Listing →</a>` : ''}
            </div>
          `);
        
        markers.push(marker);
        bounds.push([property.coordinates.lat, property.coordinates.lon]);
      }
    }
    
    // Fit map to show all markers
    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [50, 50] });
      updateMapStatus(`Showing ${bounds.length} properties on map`, false);
    } else {
      updateMapStatus('No properties could be geocoded', false);
    }
    
    // Save updated shortlist with coordinates
    if (geocodedCount > 0) {
      await fetch(`${API_URL}/shortlist`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ shortlist })
      });
    }
    
  } catch (err) {
    console.error('Map loading error:', err);
    updateMapStatus('Error loading map', false);
  }
}

async function geocodeAddress(address) {
  try {
    const response = await fetch(`${API_URL}/geocode`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({ address })
    });
    
    if (response.ok) {
      const data = await response.json();
      // Add small delay to respect Nominatim rate limits
      await new Promise(resolve => setTimeout(resolve, 1000));
      return { lat: data.lat, lon: data.lon };
    }
    return null;
  } catch (err) {
    console.error('Geocoding error:', err);
    return null;
  }
}

function updateMapStatus(text, isLoading) {
  const statusEl = document.getElementById('mapStatusText');
  const statusContainer = document.getElementById('mapStatus');
  
  if (isLoading) {
    statusEl.innerHTML = `<div class="spinner"></div> ${text}`;
    statusContainer.style.display = 'flex';
  } else {
    statusEl.textContent = text;
    statusContainer.style.display = 'block';
    setTimeout(() => {
      statusContainer.style.display = 'none';
    }, 3000);
  }
}
function toggleMapExpand() {
  const mapSection = document.getElementById('map-1');
  const mapDiv = document.getElementById('map');
  const expandBtn = document.getElementById('expandMapBtn');
  const expandIcon = document.getElementById('expandIcon');
  const mapTitle = document.getElementById('mapTitle');
  const mapStatus = document.getElementById('mapStatus');
  const mapContainer = document.getElementById('mapContainer');
  
  // Get all other sections
  const scrapeSection = document.getElementById('scrape-1');
  const requirementsSection = document.getElementById('requirements-1');
  const shortlistSection = document.getElementById('shortlist-1');
  const expertSection = document.getElementById('expert-1');
  const viewMapBtn = document.getElementById('viewMapBtn');
  const mapLoadingMsg = document.getElementById('mapLoadingMessage');
  
  // Check if currently expanded
  const isExpanded = mapDiv.style.height !== '500px';
  
  if (!isExpanded) {
    // EXPAND: Hide everything else and make map fullscreen
    scrapeSection.style.display = 'none';
    requirementsSection.style.display = 'none';
    shortlistSection.style.display = 'none';
    expertSection.style.display = 'none';
    viewMapBtn.style.display = 'none';
    mapLoadingMsg.style.display = 'none';
    mapTitle.style.display = 'none';
    mapStatus.style.display = 'none';
    
    // Remove all padding and margins from map section and container
    mapSection.style.padding = '0';
    mapSection.style.margin = '0';
    mapSection.style.maxWidth = 'none';
    mapContainer.style.margin = '0';
    mapContainer.style.padding = '0';
    
    // Make map fill edge to edge below navbar
    mapDiv.style.height = 'calc(100vh - 70px)'; // Adjust based on your navbar height
    mapDiv.style.width = '100vw';
    mapDiv.style.marginLeft = 'calc(-50vw + 50%)'; // Center and expand to full width
    mapDiv.style.borderRadius = '0';
    mapDiv.style.border = 'none';
    
    // Change button text and position
    expandBtn.innerHTML = '<span id="expandIcon">✕</span>';
    expandBtn.style.position = 'fixed';
    expandBtn.style.top = '90px';
    expandBtn.style.right = '20px';
    expandBtn.style.zIndex = '1000';
    expandBtn.style.background = '#dc2626';
    expandBtn.style.boxShadow = '0 2px 8px rgba(0,0,0,0.3)';
    expandBtn.style.padding = '8px 12px';
    expandBtn.style.fontSize = '18px';
    expandBtn.style.minWidth = 'auto';
    expandBtn.style.width = 'auto';
    // expandMapBtn.style.position = 'center';
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
    
    // Refresh map - CRITICAL: Multiple invalidations with delays
    if (window.mapInstance) {
      // Force immediate invalidation
      window.mapInstance.invalidateSize();
      
      // Second invalidation after a short delay
      setTimeout(() => {
        window.mapInstance.invalidateSize();
      }, 100);
      
      // Third invalidation to catch any late rendering
      setTimeout(() => {
        window.mapInstance.invalidateSize();
      }, 300);
      
      // Final invalidation
      setTimeout(() => {
        window.mapInstance.invalidateSize();
      }, 500);
    }
    
  } else {
    // COLLAPSE: Show everything again
    scrapeSection.style.display = '';
    requirementsSection.style.display = '';
    shortlistSection.style.display = '';
    expertSection.style.display = '';
    viewMapBtn.style.display = '';
    mapLoadingMsg.style.display = '';
    mapTitle.style.display = '';
    mapStatus.style.display = '';
    
    // Reset map section and container
    mapSection.style.padding = '';
    mapSection.style.margin = '';
    mapSection.style.maxWidth = '';
    mapContainer.style.margin = '';
    mapContainer.style.padding = '';
    
    // Reset map
    mapDiv.style.height = '500px';
    mapDiv.style.width = '';
    mapDiv.style.marginLeft = '';
    mapDiv.style.borderRadius = '8px';
    mapDiv.style.border = '2px solid var(--border-color)';
    
    // Reset button
    expandBtn.innerHTML = '<span id="expandIcon">⛶</span> Expand Map';
    expandBtn.style.position = '';
    expandBtn.style.top = '';
    expandBtn.style.right = '';
    expandBtn.style.zIndex = '';
    expandBtn.style.background = 'var(--primary-color)';
    expandBtn.style.boxShadow = '';
    
    // Restore body scroll
    document.body.style.overflow = '';
    
    // Refresh map on collapse too
    if (window.mapInstance) {
      setTimeout(() => {
        window.mapInstance.invalidateSize();
      }, 100);
    }
  }
}
// ============================================
// ASK EXPERT
// ============================================

async function askExpert() {
  const question = document.getElementById("question").value;
  
  if (!question) {
    document.getElementById("answer").textContent = "Please enter a question.";
    return;
  }
  
  try {
    const res = await fetch(`${API_URL}/ask_expert`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });
    const data = await res.json();
    document.getElementById("answer").textContent = data.answer || data.error;
  } catch (err) {
    document.getElementById("answer").textContent = "Failed to get answer: " + err.message;
  }
}

// ============================================
// PAGE INITIALIZATION
// ============================================

document.addEventListener("DOMContentLoaded", () => {
  checkAuth();

  // Login form Enter key support
  const loginPassword = document.getElementById('loginPassword');
  if (loginPassword) {
    loginPassword.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') handleLogin();
    });
  }

  // Register form Enter key support
  const confirmPassword = document.getElementById('confirmPassword');
  if (confirmPassword) {
    confirmPassword.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') handleRegister();
    });
  }

  // Event listeners for buttons
  const scrapeBtn = document.getElementById("scrapeBtn");
  if (scrapeBtn) scrapeBtn.addEventListener("click", getResults);

  const addBtn = document.getElementById("addBtn");
  if (addBtn) addBtn.addEventListener("click", () => addRequirement());

  const addShortBtn = document.getElementById("addShortBtn");
  if (addShortBtn) addShortBtn.addEventListener("click", () => addShortlistItem());
});

// ============================================
// EXPORTS (for testing)
// ============================================

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { toggleTheme, addRequirement, addShortlistItem };
}