import requests
import base64
import os
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

# Configuration: connecting to local server
SERVER_URL = "http://127.0.0.1:5000"

class SecureClient:
    def __init__(self, username):
        self.username = username
        self.private_key = None
        self.public_key = None
        # Generating a random salt for KDF(Key Derivation Function)
        self.salt = os.urandom(16).hex()

    def generate_keys(self):
        """Generates a new key pair for the user(private and public)"""
        print(f"!Generating ECC keys for {self.username}...")
        # 1. Private key(keeping on the local client)
        self.private_key = x25519.X25519PrivateKey.generate()
        # 2. Public key(to be sent to the server)
        self.public_key = self.private_key.public_key()

    def get_public_key_string(self):
        """Converts the public key to a base64 string for transmission"""
        pub_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return base64.b64encode(pub_bytes).decode('utf-8')

    def register(self):
        """Sends the registration request to the server"""
        payload = {
            "username": self.username,
            "password_hash": "placeholder_hash_v1",
            "public_key": self.get_public_key_string(),
            "kdf_salt": self.salt
        }
        
        try:
            response = requests.post(f"{SERVER_URL}/register", json=payload)
            
            if response.status_code == 201:
                print(f"[SUCCESS] {self.username} registered successfully!")
            elif response.status_code == 409:
                print(f" [INFO] User {self.username} already exists.")
            else:
                print(f" [ERROR] Server responded: {response.text}")
                
        except Exception as e:
            print(f" CRITICAL: can't connect to server: {e}")

if __name__ == "__main__":
    # Change the username as needed
    alice = SecureClient("Bob_The_Receiver") 
    alice.generate_keys()
    alice.register()