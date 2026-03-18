import os
import pickle
from flask import Blueprint, request, jsonify, render_template, session
from app.db import get_db
import mysql.connector

# --- AUTHENTICATION HELPER (TOKEN BYPASS) ---
def get_current_user_id():
    """
    Attempts to retrieve the User ID from the Session (Cookie).
    If that fails (due to browser restrictions), it checks the custom Header (Token).
    """
    # 1. Try the standard session method (Cookie)
    if 'user_id' in session:
        return session['user_id']
    
    # 2. Try the backup method (Token from LocalStorage)
    token_id = request.headers.get('X-User-ID')
    if token_id and token_id.isdigit():
        return int(token_id)
        
    return None

# IMPORT THE PHISHING AI MODULE
from app.ai_security.phishing import PhishingDetector

api = Blueprint('api', __name__)

# --- INITIALIZE AI ENGINE ---
# We initialize it here so it stays loaded in memory for performance
phishing_ai = PhishingDetector()

# Check if the model is already trained. If not, train it now.
if not os.path.exists(phishing_ai.model_path):
    print("Training AI model for the first time...")
    phishing_ai.train_model()

# --- ROUTE 0: HOME ---
@api.route('/')
def home():
   # Renders the main frontend interface
    return render_template('index.html')

# Global in-memory storage for live AI analysis (if needed)
LIVE_AI_MEMORY = []

# --- ROUTE 1: REGISTER ---
@api.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    required = ['username', 'password', 'public_key', 'kdf_salt']
    
    if not data or not all(k in data for k in required):
        return jsonify({"error": "Incomplete data"}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Saving the user credentials
        # Note: In a production environment, password_hash should be a real hash (e.g., bcrypt)
        query = """
            INSERT INTO users (username, password_hash, public_key, kdf_salt)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (
            data['username'], 
            data['password'], 
            data['public_key'], 
            data['kdf_salt']
        ))
        conn.commit()
        return jsonify({"message": "User created successfully"}), 201

    except mysql.connector.IntegrityError:
        return jsonify({"error": "Username already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# --- ROUTE 2: LOGIN ---
@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Missing credentials"}), 400

    conn = get_db()
    cursor = conn.cursor()
    
    # Verify username and password
    query = "SELECT id, username FROM users WHERE username = %s AND password_hash = %s"
    cursor.execute(query, (data['username'], data['password']))
    user = cursor.fetchone() # user will be a tuple: (id, username)
    cursor.close()
    conn.close()

    if user:
        # Set session for standard browsers
        session['user_id'] = user[0]
        session['username'] = user[1]
        
        # Return the user_id so the frontend can store it as a Token (localStorage)
        return jsonify({
            "message": "Login successful",
            "user_id": user[0] 
        }), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

# --- ROUTE 3: GET PUBLIC KEY ---
@api.route('/get_public_key/<username>', methods=['GET'])
def get_public_key(username):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT public_key FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        return jsonify({"public_key": result[0]}), 200
    else:
        return jsonify({"error": "User not found"}), 404

# --- ROUTE 4: SEND MESSAGE ---
@api.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    global LIVE_AI_MEMORY
    # --- 1. BIOMETRIC ANALYSIS START ---
    keystrokes = data.get('keystrokes', [])
    biometric_warning = False # Default e False (totul e ok)
    
    if keystrokes:

        LIVE_AI_MEMORY.extend(keystrokes)
        # Calculating average typing speed
        avg_speed = sum(keystrokes) / len(keystrokes)
        print(f"[AI BIOMETRICS] Average speed: {avg_speed:.2f} ms")
        
        # DETECTION LOGIC
        # If under 80ms (too fast/robot) OR over 400ms (too slow)
        # Set 80ms to catch even your speed of 74.79ms from the logs!
        if avg_speed < 90 or avg_speed > 1200:  
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(" ALERT: SUSPICIOUS TYPING STYLE DETECTED! ")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            
            
            biometric_warning = True 
            
    # --- 1. BIOMETRIC ANALYSIS END ---

    conn = get_db()
    cursor = conn.cursor()
    try:
        # Get IDs for sender and receiver
        get_id = "SELECT id FROM users WHERE username = %s"
        cursor.execute(get_id, (data['sender_username'],))
        sender = cursor.fetchone()
        cursor.execute(get_id, (data['receiver_username'],))
        receiver = cursor.fetchone()

        if not sender or not receiver:
            return jsonify({"error": "Users not found"}), 404

        # Insert encrypted message
        query = """INSERT INTO messages (sender_id, receiver_id, encrypted_content, encrypted_aes_key, iv)
                   VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(query, (sender[0], receiver[0], data['encrypted_content'], data['encrypted_aes_key'], data['iv']))
        conn.commit()
        
        # --- AICI TRIMITEM REZULTATUL LA BROWSER ---
        return jsonify({
            "message": "Message sent",
            "biometric_warning": biometric_warning # <--- Asta spune site-ului sa arate alerta
        }), 201
        
    except Exception as e:
        print(f"Error sending message: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# --- ROUTE 5: GET MESSAGES ---
@api.route('/get_messages/<username>', methods=['GET'])
def get_messages(username):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Validate user
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user_res = cursor.fetchone()
        if not user_res: return jsonify({"error": "User not found"}), 404
        
        # Fetch messages where this user is the receiver
        query = """
            SELECT m.id, m.encrypted_content, m.iv, u.username, u.public_key
            FROM messages m JOIN users u ON m.sender_id = u.id
            WHERE m.receiver_id = %s ORDER BY m.created_at DESC
        """
        cursor.execute(query, (user_res[0],))
        messages = cursor.fetchall()
        
        # Format response
        results = [{"id": m[0], "content": m[1], "iv": m[2], "sender": m[3], "sender_public_key": m[4]} for m in messages]
        return jsonify(results), 200
    finally:
        cursor.close()
        conn.close()

# --- ROUTE 6: AI PHISHING CHECK ---
@api.route('/analyze_phishing', methods=['POST'])
def analyze_phishing():
    data = request.get_json()
    
    # We expect JSON like: {"message_text": "Click here to win"}
    text_to_analyze = data.get('message_text', '')
    
    if not text_to_analyze:
        return jsonify({"result": "No text provided"}), 400

    # Get prediction from our local AI model
    prediction_result = phishing_ai.predict(text_to_analyze)
    
    return jsonify({"analysis": prediction_result}), 200


# ==========================================
# FRIEND LIST FEATURES (Private Agenda Style)
# ==========================================

@api.route('/add_friend', methods=['POST'])
def add_friend():
    """
    Adds a user to the current user's friend list.
    Strict privacy mode: You must know the exact username.
    """
    # 1. Security Check: Use our helper to support both Cookie and Token
    current_user_id = get_current_user_id()
    
    if not current_user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    friend_username = data.get('username')

    # 2. Validation: Cannot add empty username
    if not friend_username:
        return jsonify({"error": "Username is required."}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        # 3. Check if the target user exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (friend_username,))
        friend = cursor.fetchone()

        if not friend:
            return jsonify({"error": "User not found. Please check the username."}), 404

        friend_id = friend[0]

        # 4. Prevention: Cannot add yourself
        if friend_id == current_user_id:
            return jsonify({"error": "You cannot add yourself as a contact."}), 400

        # 5. Insert into Database
        # We use INSERT IGNORE to avoid crashing if the friend is already added (Unique Constraint)
        cursor.execute("INSERT IGNORE INTO friends (user_id, friend_id) VALUES (%s, %s)", (current_user_id, friend_id))
        conn.commit()

        return jsonify({"message": f"User '{friend_username}' added to contacts."}), 201

    except Exception as e:
        print(f"Error adding friend: {e}") # Log error for debugging
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        cursor.close()
        conn.close()


@api.route('/get_friends', methods=['GET'])
def get_friends():
    """
    Retrieves the list of friends for the logged-in user.
    Used to populate the sidebar.
    """
    # 1. Security Check: Use our helper
    current_user_id = get_current_user_id()
    
    if not current_user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cursor = conn.cursor()

    try:
        # 2. Fetch friends' usernames using a JOIN
        query = """
            SELECT u.username 
            FROM friends f
            JOIN users u ON f.friend_id = u.id
            WHERE f.user_id = %s
            ORDER BY u.username ASC
        """
        cursor.execute(query, (current_user_id,))
        
        # Convert list of tuples [('Bob',), ('Alice',)] into a simple list ['Bob', 'Alice']
        friends = [row[0] for row in cursor.fetchall()]

        return jsonify({"friends": friends}), 200

    except Exception as e:
        print(f"Error fetching friends: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        cursor.close()
        conn.close()

@api.route('/save_brain', methods=['GET'])
def save_brain():
    global LIVE_AI_MEMORY
    
    if not LIVE_AI_MEMORY:
        return jsonify({"status": "Empty brain (No keystrokes recorded yet)"})

    # Calculate the overall average learned in this session
    session_avg = sum(LIVE_AI_MEMORY) / len(LIVE_AI_MEMORY)

    # Create a simple AI model representation
    ai_model = {
        "session_id": "LIVE",
        "total_keystrokes_analyzed": len(LIVE_AI_MEMORY),
        "learned_average_speed": session_avg,
        "raw_data_sample": LIVE_AI_MEMORY[-10:], # Ultimele 10 apasari
        "status": "TRAINED_ON_REAL_DATA"
    }

    # Save the model to disk
    with open('live_model.pkl', 'wb') as f:
        pickle.dump(ai_model, f)

    return jsonify({
        "message": "Succes! Model saved to disk.",
        "file": "live_model.pkl",
        "stats": ai_model
    })