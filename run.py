from app import create_app
from app.db import init_db
# Importing biometric security guard
from app.ai_security.biometrics import KeystrokeBiometrics

# 1.Creating the Flask app
app = create_app()

# 2.Starting the biometric monitoring in the background
# This will analyze typing patterns continuously
security_guard = KeystrokeBiometrics()
security_guard.start_monitoring()

if __name__ == "__main__":
    # Initialize the database (creates tables if not exist)
    init_db()
    
    print("Server running on port 5000...")
    # Starting the Flask app with threading enabled
    app.run(debug=True, port=5000, threaded=True)