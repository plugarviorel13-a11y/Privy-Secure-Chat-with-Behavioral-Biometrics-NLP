const API_URL = "http://127.0.0.1:5000";
let currentUser = null;

// --- NAVIGATION BETWEEN LOGIN AND REGISTER ---
function showRegister() {
    document.getElementById('loginForm').classList.add('hidden');
    document.getElementById('registerForm').classList.remove('hidden');
}

function showLogin() {
    document.getElementById('registerForm').classList.add('hidden');
    document.getElementById('loginForm').classList.remove('hidden');
}

// --- FUNCTION 1: REGISTER ---
async function doRegister() {
    const user = document.getElementById('regUser').value.trim();
    const pass = document.getElementById('regPass').value.trim();
    const status = document.getElementById('regStatus');

    if(!user || !pass) { alert("Please complete all fields!"); return; }

    status.innerText = "Creating account...";

    try {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: user,
                password: pass, 
                public_key: "demo_pk_generated_by_js", 
                kdf_salt: "demo_salt"
            }),
            credentials: 'include' // <--- IMPORTANT: Allows cookie handling
        });

        if (response.status === 201) {
            status.innerText = "Account created! Redirecting...";
            status.style.color = "#a6e3a1";
            setTimeout(showLogin, 1500); 
        } else if (response.status === 409) {
            status.innerText = "Username already exists.";
            status.style.color = "#f9e2af";
        } else {
            status.innerText = "Server error.";
        }
    } catch (e) { console.error(e); }
}

// --- FUNCTION 2: LOGIN ---
async function doLogin() {
    const user = document.getElementById('loginUser').value.trim();
    const pass = document.getElementById('loginPass').value.trim();
    const status = document.getElementById('loginStatus');

    if(!user || !pass) { alert("Please enter username and password!"); return; }

    status.innerText = "Verifying credentials...";

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass }),
            credentials: 'include' // <--- CRITICAL: Saves the session cookie
        });

        if (response.status === 200) {
            // LOGIN SUCCESSFUL
            currentUser = user;
            document.getElementById('authContainer').classList.add('hidden');
            document.getElementById('dashboardScreen').classList.remove('hidden');
            document.getElementById('currentUserDisplay').innerText = currentUser;
            
            // LOAD DATA
            loadInbox(); 
            loadContacts(); 
        } else {
            status.innerText = "Invalid username or password.";
            status.style.color = "#f38ba8";
        }
    } catch (e) { 
        status.innerText = "Network error";
    }
}

// --- FUNCTION 3: LOGOUT ---
function logout() {
    // Ideally call a logout endpoint, but reload works for demo
    location.reload();
}

// ==========================================
// NEW FEATURES: CONTACTS / FRIEND LIST
// ==========================================

// 1. Add a new contact
async function addContact() {
    const contactInput = document.getElementById('newContactInput');
    const username = contactInput.value.trim();

    if (!username) return;

    try {
        const response = await fetch(`${API_URL}/add_friend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username }),
            credentials: 'include' // <--- CRITICAL: Sends session cookie to prove who you are
        });

        const data = await response.json();

        if (response.ok) {
            alert("Success: " + data.message);
            contactInput.value = ""; // Clear input
            loadContacts(); // Refresh list
        } else {
            alert("Error: " + data.error);
        }
    } catch (e) {
        console.error("Error adding contact:", e);
    }
}

// 2. Load and Display Contacts
async function loadContacts() {
    const listContainer = document.getElementById('contactsList');
    listContainer.innerHTML = '<p class="placeholder-text">Loading...</p>';

    try {
        // GET requests also need credentials: 'include'
        const response = await fetch(`${API_URL}/get_friends`, {
            credentials: 'include' 
        });
        const data = await response.json();

        listContainer.innerHTML = ""; // Clear loader

        if (data.friends && data.friends.length > 0) {
            data.friends.forEach(friendName => {
                // Create HTML for each friend
                const div = document.createElement('div');
                div.className = 'contact-item';
                div.onclick = function() { selectContact(friendName); }; // Click to select
                
                div.innerHTML = `
                    <span class="contact-name">${friendName}</span>
                    <span class="contact-icon">💬</span>
                `;
                
                listContainer.appendChild(div);
            });
        } else {
            listContainer.innerHTML = '<p class="placeholder-text">No contacts yet.</p>';
        }
    } catch (e) {
        console.error("Error loading contacts:", e);
        listContainer.innerHTML = '<p class="status" style="color:red">Error loading.</p>';
    }
}

// 3. Helper: Fill the "To" input when clicking a friend
function selectContact(username) {
    document.getElementById('receiverInput').value = username;
    document.getElementById('messageInput').focus();
}




// --- MESSAGING FUNCTIONS ---
async function sendMessage() {
    const receiver = document.getElementById('receiverInput').value.trim();
    const message = document.getElementById('messageInput').value;
    const status = document.getElementById('statusMsg');

    if (!receiver || !message) { alert("Please fill in receiver and message!"); return; }
    
    status.innerText = "Sending...";

    try {
        const response = await fetch(`${API_URL}/send_message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sender_username: currentUser,
                receiver_username: receiver,
                encrypted_content: btoa(message), // Demo encryption (Base64)
                encrypted_aes_key: "demo",
                iv: "demo_iv"
            }),
            credentials: 'include' // <--- CRITICAL
        });

        if (response.ok) {
            status.innerText = "Message sent successfully!";
            status.style.color = "#a6e3a1";
            document.getElementById('messageInput').value = "";
            setTimeout(() => status.innerText = "", 3000);
        } else {
            status.innerText = "Error (Does the user exist?)";
            status.style.color = "#f38ba8";
        }
    } catch (e) { status.innerText = "Network error"; }
}

// --- CHECK PHISHING ---
async function checkPhishing(messageText, resultElementId) {
    const resultSpan = document.getElementById(resultElementId);
    resultSpan.innerText = " Analyzing with AI...";
    resultSpan.style.color = "#89dceb";

    try {
        const response = await fetch(`${API_URL}/analyze_phishing`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message_text: messageText }),
            credentials: 'include' // <--- Added for safety
        });

        if (response.ok) {
            const data = await response.json();
            resultSpan.innerText = " " + data.analysis;
            
            if (data.analysis.includes("WARNING")) {
                resultSpan.style.color = "#f38ba8"; 
                resultSpan.style.fontWeight = "bold";
            } else {
                resultSpan.style.color = "#a6e3a1"; 
            }
        } else {
            resultSpan.innerText = " AI Error.";
        }
    } catch (e) {
        console.error(e);
        resultSpan.innerText = " Connection failed.";
    }
}

// --- LOAD INBOX ---
async function loadInbox() {
    const list = document.getElementById('inboxList');
    list.innerHTML = "Loading...";
    try {
        const res = await fetch(`${API_URL}/get_messages/${currentUser}`, {
            credentials: 'include' // <--- CRITICAL for GET requests too
        });
        
        if(res.ok) {
            const msgs = await res.json();
            list.innerHTML = "";
            if(msgs.length === 0) { list.innerHTML = "<p>Inbox is empty.</p>"; return; }
            
            msgs.forEach(m => {
                const decryptedContent = atob(m.content);
                const uniqueId = `ai-res-${m.id}`;
                const safeContent = decryptedContent.replace(/'/g, "\\'"); 

                list.innerHTML += `
                <div class='msg-item' style="border:1px solid #444; padding:10px; margin-bottom:10px; border-radius:8px;">
                    <span class='msg-sender' style="font-weight:bold; color:#89b4fa;">From: ${m.sender}</span>
                    <div class='msg-text' style="margin: 5px 0;">${decryptedContent}</div>
                    
                    <div style="margin-top:5px;">
                        <button onclick="checkPhishing('${safeContent}', '${uniqueId}')" 
                                style="background:#313244; color:#cdd6f4; border:none; padding:5px 10px; cursor:pointer; border-radius:4px; font-size:0.8em;">
                            DETECT PHISHING
                        </button>
                        <span id="${uniqueId}" style="margin-left:10px; font-size:0.9em;"></span>
                    </div>
                </div>`;
            });
        }
    } catch(e) { 
        console.error(e);
        list.innerText = "Error loading messages."; 
    }
}