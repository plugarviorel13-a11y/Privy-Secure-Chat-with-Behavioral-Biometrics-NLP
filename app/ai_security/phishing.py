import os
import joblib
import pandas as pd  # Used for efficient data manipulation (DataFrames)
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

class PhishingDetector:
    """
    A class responsible for training, saving, and utilizing a Naive Bayes classifier
    to detect phishing attempts in text messages.
    """

    def __init__(self):
        # --- PATH CONFIGURATION ---
        # We use absolute paths to prevent "File Not Found" errors when running from different directories.
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Paths for the serialized model components (The "Brain")
        self.model_path = os.path.join(base_dir, 'saved_models', 'spam_model.pkl')
        self.vector_path = os.path.join(base_dir, 'saved_models', 'vectorizer.pkl')
        
        # Path for the training dataset (CSV file)
        self.dataset_path = os.path.join(base_dir, 'phishing_dataset.csv')
        
        self.clf = None       # The Classifier (Algorithm)
        self.vectorizer = None # The Feature Extractor
        
        # --- INITIALIZATION LOGIC ---
        # If a trained model already exists on disk, load it to save time.
        # Otherwise, the system will wait for a manual training trigger.
        if os.path.exists(self.model_path):
            self.load_model()
        else:
            print("[INFO] Model not found. Initializing training sequence...")
            self.train_model()

    def train_model(self):
        """
        Reads the dataset, processes the text, and trains the Naive Bayes algorithm.
        """
        # 1. DATA LOADING
        if not os.path.exists(self.dataset_path):
            print(f"[ERROR] Dataset not found at {self.dataset_path}. Using fallback data.")
            # Fallback data to prevent crash during presentation
            data = {'text': ["Click to win", "Hello friend"], 'label': [1, 0]}
            df = pd.DataFrame(data)
        else:
            print(f"[INFO] Loading dataset from: {self.dataset_path}")
            df = pd.read_csv(self.dataset_path)
            print(f"[INFO] Dataset loaded successfully. Samples: {len(df)}")

        # Ensure all text data is string format
        messages = df['text'].astype(str)
        labels = df['label'] # 1 = Phishing, 0 = Safe

        # 2. FEATURE EXTRACTION (Bag of Words)
        # Convert human-readable text into numerical vectors that the machine can understand.
        self.vectorizer = CountVectorizer()
        X = self.vectorizer.fit_transform(messages)
        
        # 3. MODEL TRAINING (Fitting)
        # We use Multinomial Naive Bayes, which is standard for text classification tasks.
        self.clf = MultinomialNB()
        self.clf.fit(X, labels)
        
        # 4. SERIALIZATION (Saving to Disk)
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # Save both the classifier and the vectorizer (vocabulary)
        joblib.dump(self.clf, self.model_path)
        joblib.dump(self.vectorizer, self.vector_path)
        
        print("[SUCCESS] Model trained and saved to disk.")

    def load_model(self):
        """
        Loads the pre-trained model and vectorizer from the disk.
        """
        try:
            self.clf = joblib.load(self.model_path)
            self.vectorizer = joblib.load(self.vector_path)
            print("[INFO] AI Model successfully loaded from storage.")
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")

    def predict(self, text):
        """
        Analyzes a single text string and returns a verdict (Safe vs Phishing).
        """
        # Safety check: Ensure model is trained
        if self.clf is None:
            self.train_model()
            
        # 1. PRE-PROCESSING
        # Transform the new text using the SAME vocabulary learned during training
        vectorized_text = self.vectorizer.transform([text])
        
        # 2. INFERENCE (Prediction)
        prediction = self.clf.predict(vectorized_text)          # Returns 0 or 1
        probability = self.clf.predict_proba(vectorized_text)   # Returns confidence score
        
        # Extract confidence for the 'Phishing' class (index 1)
        confidence_percent = probability[0][1] * 100
        
        # 3. RESULT INTERPRETATION
        if prediction[0] == 1:
            return f"WARNING: Phishing Detected! (Confidence: {confidence_percent:.2f}%)"
        return "SAFE: Message looks clean."