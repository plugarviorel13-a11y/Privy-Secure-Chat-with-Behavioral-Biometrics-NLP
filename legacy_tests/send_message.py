import requests
import base64
import os
import json
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Configuration: connecting to local server
SERVER_URL = "http://127.0.0.1:5000"

class EncryptedMessenger:
    def __init__(self, my_username):
        self.username = my_username
        # In a real app, keys would be persistently stored
        # For this demo, we generate them fresh each time   
        self.private_key = x25519.X25519PrivateKey.generate()
        print(f" Logged in as: {self.username}")

    def get_user_public_key(self, target_username):
        """Step 1: Ask the server for the recipient's public key"""
        try:
            response = requests.get(f"{SERVER_URL}/get_public_key/{target_username}")
            if response.status_code == 200:
                pub_key_b64 = response.json()['public_key']
                # Decoding from base64 to bytes
                pub_bytes = base64.b64decode(pub_key_b64)
                return x25519.X25519PublicKey.from_public_bytes(pub_bytes)
            else:
                print(f" Did not find user {target_username}")
                return None
        except Exception as e:
            print(f"Network error: {e}")
            return None

    def derive_shared_secret(self, peer_public_key):
        """Step 2: ECDH to derive shared secret"""
        # My private key + Bob's public key = Shared Secret 
        shared_key = self.private_key.exchange(peer_public_key)
        
        # Deriving a symmetric key from the shared secret
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32, # 32 bytes = 256 bits for AES-256
            salt=None,
            info=b'handshake data',
        ).derive(shared_key)
        
        return derived_key

    def encrypt_message(self, message, aes_key):
        """Step 3: Encrypt the message with AES-GCM"""
        iv = os.urandom(12) # Unique initialization vector
        aesgcm = AESGCM(aes_key)
        ciphertext = aesgcm.encrypt(iv, message.encode('utf-8'), None)
        return ciphertext, iv

    def send(self, receiver_username, message_text):
        print(f"\n Preparing message to {receiver_username}...")
        
        # 1. Get Bob's public key
        bob_pub_key = self.get_user_public_key(receiver_username)
        if not bob_pub_key:
            return

        # 2. Calculate the shared secret
        aes_key = self.derive_shared_secret(bob_pub_key)
        print(" Shared secret derived (ECDH + HKDF): [SECURE]")

        # 3. Encrypt the message
        encrypted_content, iv = self.encrypt_message(message_text, aes_key)
        
        # 4. Send to server
        payload = {
            "sender_username": self.username,
            "receiver_username": receiver_username,
            "encrypted_content": base64.b64encode(encrypted_content).decode('utf-8'),
            "encrypted_aes_key": "Hybrid_Enc_Simulated", 
            "iv": base64.b64encode(iv).decode('utf-8')
        }

        try:
            res = requests.post(f"{SERVER_URL}/send_message", json=payload)
            if res.status_code == 201:
                print(f" Message sent successfully! (AES-256 encrypted)")
                print(f"   -> Original content: '{message_text}'")
                print(f"   -> What the server/hacker sees: {payload['encrypted_content'][:20]}...")
            else:
                print(f"❌ Error sending message: {res.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    # Alice sends a message to Bob
    # Warning: Make sure Bob_The_Receiver is registered before running this
    alice = EncryptedMessenger("Alice_Final_Test")
    alice.send("Bob_The_Receiver", "Hello bob! This is a secret message.")