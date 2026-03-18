import requests
import base64
import os
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SERVER_URL = "http://127.0.0.1:5000"

class User:
    def __init__(self, name):
        self.name = name
        # Generating keys for the user
        self.private_key = x25519.X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.salt = os.urandom(16).hex()

    def get_pub_str(self):
        pub_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return base64.b64encode(pub_bytes).decode('utf-8')

    def register(self):
        payload = {
            "username": self.name,
            "password_hash": "demo_hash",
            "public_key": self.get_pub_str(),
            "kdf_salt": self.salt
        }
        # Ignoring server response for demo purposes if the user already exists
        requests.post(f"{SERVER_URL}/register", json=payload)
        print(f" {self.name} connected to server and registered.")

    def send_message(self, receiver_name, text):
        # 1. Getting the public key of the receiver from the server
        res = requests.get(f"{SERVER_URL}/get_public_key/{receiver_name}")
        if res.status_code != 200:
            print("Error: couldn't get receiver's public key.")
            return

        receiver_pub_b64 = res.json()['public_key']
        receiver_pub_bytes = base64.b64decode(receiver_pub_b64)
        receiver_pub_key = x25519.X25519PublicKey.from_public_bytes(receiver_pub_bytes)

        # 2. Deriving the shared secret key
        shared_key = self.private_key.exchange(receiver_pub_key)
        aes_key = HKDF(hashes.SHA256(), 32, None, b'handshake data').derive(shared_key)

        # 3. Crypting the message with AES-GCM
        iv = os.urandom(12)
        aesgcm = AESGCM(aes_key)
        encrypted = aesgcm.encrypt(iv, text.encode('utf-8'), None)

        # 4. verifying and sending the message to the server
        payload = {
            "sender_username": self.name,
            "receiver_username": receiver_name,
            "encrypted_content": base64.b64encode(encrypted).decode('utf-8'),
            "encrypted_aes_key": "hybrid",
            "iv": base64.b64encode(iv).decode('utf-8')
        }
        requests.post(f"{SERVER_URL}/send_message", json=payload)
        print(f" {self.name} send: '{text}' (Crypted)")

    def check_messages(self):
        print(f"\n {self.name} verifying...")
        res = requests.get(f"{SERVER_URL}/get_messages/{self.name}")
        if res.status_code != 200:
            print("Nothing to verify.")
            return

        messages = res.json()
        for msg in messages:
            # Decrypting each message
            
            # 1. Reconstructing the sender's public key
            sender_pub_bytes = base64.b64decode(msg['sender_public_key'])
            sender_pub_key = x25519.X25519PublicKey.from_public_bytes(sender_pub_bytes)

            # 2. Doing the same thing as the sender to derive the shared key
            shared_key = self.private_key.exchange(sender_pub_key)
            aes_key = HKDF(hashes.SHA256(), 32, None, b'handshake data').derive(shared_key)

            # 3. Decrypting the message
            iv = base64.b64decode(msg['iv'])
            ciphertext = base64.b64decode(msg['content'])
            
            try:
                aesgcm = AESGCM(aes_key)
                plaintext = aesgcm.decrypt(iv, ciphertext, None)
                print(f" Message from {msg['sender']}: {plaintext.decode('utf-8')}")
            except Exception as e:
                print(f" Error decrypting: {e}")

if __name__ == "__main__":
    # Using two users for demo
    alice = User("Alice_Demo_Live")
    bob = User("Bob_Demo_Live")

    alice.register()
    bob.register()

    # Alice sends a message to Bob
    alice.send_message("Bob_Demo_Live", "Hello bob! This is a secret message.")

    # Bob checks and decrypts his messages
    bob.check_messages()