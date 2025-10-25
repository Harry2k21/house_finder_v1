let count = 0;
const maxRequirements = 20;

// ============================================
// GLOBAL VARIABLES
// ============================================

let authToken = null;
let currentUsername = null;
const API_URL = 'http://127.0.0.1:5000';

// ============================================
// CHECK AUTHENTICATION ON PAGE LOAD
// ============================================

function checkAuth() {
  // Try to get stored token from localStorage
  const storedToken = localStorage.getItem('authToken');
  const storedUsername = localStorage.getItem('currentUsername');

  if (storedToken && storedUsername) {
    // Verify token is still valid by calling a protected route
    verifyTokenWithBackend(storedToken);
  } else {
    // Show login form, hide app
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
      // Token is valid, show app
      authToken = token;
      currentUsername = localStorage.getItem('currentUsername');
      showAppScreen();
    } else {
      // Token expired or invalid
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
  
  // Hide the message box
  const msg = document.getElementById('message');
  msg.textContent = '';
  msg.style.display = 'none';
  msg.className = 'message';
  
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
  setTimeout(() => {
    msg.textContent = '';
    msg.className = 'message';
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
    
    // Store token securely
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

function handleLogout() {
  authToken = null;
  currentUsername = null;
  localStorage.removeItem('authToken');
  localStorage.removeItem('currentUsername');
  clearAuthInputs();
  document.getElementById('loginForm').classList.remove('hidden');
  document.getElementById('registerForm').classList.add('hidden');
  showLoginScreen();
}

// ============================================
// PAGE INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  // Check if user is already logged in
  checkAuth();

  // Add Enter key support for login
  const loginPassword = document.getElementById('loginPassword');
  if (loginPassword) {
    loginPassword.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') handleLogin();
    });
  }

  // Add Enter key support for register
  const confirmPassword = document.getElementById('confirmPassword');
  if (confirmPassword) {
    confirmPassword.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') handleRegister();
    });
  }
});

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, c =>
    ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]
  );
}

async function getResults() {
  const url = document.getElementById("urlInput").value;
  const output = document.getElementById("output");
  if (!url) {
    output.textContent = "Please enter a Rightmove URL.";
    return;
  }

  try {
    const response = await fetch(`http://127.0.0.1:5000/scrape?url=${encodeURIComponent(url)}`);
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

// Light and Dark Mode Function////

 function toggleTheme() {
      document.body.classList.toggle("light-mode");
      const isLight = document.body.classList.contains("light-mode");
      document.getElementById("themeToggle").textContent = isLight ? "Dark Mode" : "Light Mode";
    }

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { toggleTheme };
}

async function loadHistory() {
  try {
    const response = await fetch("http://127.0.0.1:5000/history");
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

/* ---------------------------
   REQUIREMENTS SAVE / LOAD
---------------------------- */
function saveRequirements() {
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
  localStorage.setItem("requirements", JSON.stringify(reqs));
}

function loadRequirements() {
  const saved = JSON.parse(localStorage.getItem("requirements") || "[]");
  const list = document.getElementById("list");
  list.innerHTML = "";
  count = 0;
  saved.forEach(req => {
    addRequirement(req.text, req.checked);
  });
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

  saveRequirements(); // save on add
}

/* ---------------------------
   SHORTLIST SAVE / LOAD
---------------------------- */
let shortlistCount = 0;
const maxShortlist = 20;

function saveShortlist() {
  const list = document.getElementById("shortlist");
  const items = [];
  list.querySelectorAll(".short-item").forEach(itemDiv => {
    const textInput = itemDiv.querySelector("input[type=text]");
    items.push({
      text: textInput.value
    });
  });
  localStorage.setItem("shortlist", JSON.stringify(items));
}

function loadShortlist() {
  const saved = JSON.parse(localStorage.getItem("shortlist") || "[]");
  const list = document.getElementById("shortlist");
  list.innerHTML = "";
  shortlistCount = 0;
  saved.forEach(item => {
    addShortlistItem(item.text);
  });
}

function addShortlistItem(text = "") {
  if (shortlistCount >= maxShortlist) return;
  shortlistCount++;

  const list = document.getElementById("shortlist");

  const itemDiv = document.createElement("div");
  itemDiv.className = "short-item";

  const textInput = document.createElement("input");
  textInput.type = "text";
  textInput.placeholder = "Enter shortlisted item...";
  textInput.value = text;
  textInput.addEventListener("input", saveShortlist);

  const delBtn = document.createElement("button");
  delBtn.textContent = "❌";
  delBtn.onclick = () => {
    list.removeChild(itemDiv);
    shortlistCount--;
    document.getElementById("addShortBtn").disabled = false;
    saveShortlist();
  };

  itemDiv.appendChild(textInput);
  itemDiv.appendChild(delBtn);
  list.appendChild(itemDiv);

  if (shortlistCount >= maxShortlist) {
    document.getElementById("addShortBtn").disabled = true;
  }

  saveShortlist(); // save on add
}

async function askExpert() {
  const question = document.getElementById("question").value;
  const res = await fetch("http://127.0.0.1:5000/ask_expert", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question })
  });
  const data = await res.json();
  document.getElementById("answer").textContent = data.answer || data.error;
}



/* ---------------------------
   PAGE LOAD
---------------------------- */
document.addEventListener("DOMContentLoaded", () => {
  loadHistory();
  loadRequirements();
  loadShortlist();
   // load saved requirements

  const scrapeBtn = document.getElementById("scrapeBtn");
  if (scrapeBtn) scrapeBtn.addEventListener("click", getResults);

  const addBtn = document.getElementById("addBtn");
  if (addBtn) addBtn.addEventListener("click", () => addRequirement());

  const addShortBtn = document.getElementById("addShortBtn");
  if (addShortBtn) addShortBtn.addEventListener("click", () => addShortlistItem());
  
});

async function getResults() {
const url = document.getElementById("urlInput").value;
const output = document.getElementById("output");

if (!url) {
        output.textContent = "Please enter a Rightmove URL.";
        return;
      }

try {
        const response = await fetch(`http://127.0.0.1:5000/scrape?url=${encodeURIComponent(url)}`);
        const data = await response.json();

    if (data.results) {
          output.textContent = `Number of results: ${data.results}`;
        } else {
          output.textContent = `Error: ${data.error}`;
        }
      } catch (err) {
        output.textContent = "Failed to connect to backend.";
      }
    }


if (typeof module !== 'undefined' && module.exports) {
  module.exports = { toggleTheme, addRequirement, addShortlistItem };
}
