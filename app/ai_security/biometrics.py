import time
import threading
import numpy as np
from pynput import keyboard
from sklearn.ensemble import IsolationForest

class KeystrokeBiometrics:
    def __init__(self):
        self.key_press_times = {}
        self.dwell_times = [] # How long a key is pressed
        self.model = IsolationForest(contamination=0.3)
        self.is_trained = False
        self.lock = threading.Lock() # For thread safety

    def on_press(self, key):

        try:
            
            #print(f"DEBUG: Tasta detectata!", flush=True) 
            # Record the time when key is pressed
            self.key_press_times[key] = time.time()
        except Exception as e:
            print(f"Error reading key: {e}")

    def on_release(self, key):
        current_time = time.time()
        
        if key in self.key_press_times:
            press_time = self.key_press_times.pop(key)
            dwell_time = current_time - press_time
            
            with self.lock:
                self.dwell_times.append(dwell_time)
                
                # Logic: Every 20 keystrokes, we check the user
                if len(self.dwell_times) % 10 == 0:
                    self.analyze_behavior()

    def analyze_behavior(self):
        # reduce the limit to 10 keystokes for faster testing
        if len(self.dwell_times) < 10: 
            return

        data = np.array(self.dwell_times).reshape(-1, 1)

        # Model training or prediction
        if not self.is_trained:
            self.model.fit(data)
            self.is_trained = True
            
            # Calculating average dwell time in milliseconds
            avg_dwell = np.mean(self.dwell_times) * 1000 
            
            # Showing training confirmation with styled text
            print("\n" + "="*50)
            print("\033[96m[AI BIOMETRICS] Your rhythm has been learned!\033[0m")
            print(f"  BIOMETRIC PROFILE GENERATED:")
            print(f" -> Average key press speed (Dwell Time): {avg_dwell:.2f} ms")
            print(f" -> The AI has calibrated its sensitivity to this rhythm.")
            print("="*50 + "\n")
        else:
            recent_data = data[-10:] # Analizing last 10 keystrokes
            prediction = self.model.predict(recent_data)
            anomalies = np.sum(prediction == -1)
            
            # If more than 5 anomalies, raise alert
            if anomalies > 5:
                # Red text for alert
                print("\n" + "!"*50)
                print("\033[91m ALERT: SUSPICIOUS TYPING STYLE DETECTED! \033[0m")
                print(f"\033[91m-> Anomalies: {anomalies}/10 keystrokes\033[0m")
                print("!"*50 + "\n")
            else:
                # Green text for normal
                print(f"\033[92m[✓] User Verified. Anomalies: {anomalies}/10\033[0m")

    def start_monitoring(self):
        # Runs the listener in a non-blocking way
        listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        listener.start()
        print("Keystroke Dynamics Monitoring Started...")

# Simple test if run directly
if __name__ == "__main__":
    bio = KeystrokeBiometrics()
    bio.start_monitoring()
    
    # Keep the script running to test typing
    while True:
        time.sleep(1)