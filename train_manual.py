import pickle
import os
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

# Definirea cailor
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'app', 'ai_security', 'saved_models')
model_path = os.path.join(MODEL_DIR, 'spam_model.pkl')
vectorizer_path = os.path.join(MODEL_DIR, 'vectorizer.pkl')

# Making sure the model directory exists
os.makedirs(MODEL_DIR, exist_ok=True)

print("--- MANUAL AI TRAINING STARTED ---")

# 1. Training Data (Simplified for demonstration)
emails = [
    "Click here to win a prize", 
    "Urgent account update required", 
    "Free money limited time offer", 
    "Verify your password immediately",
    "Hello, how are you today?", 
    "Meeting confirmed for tomorrow", 
    "Project updates attached", 
    "Lets grab lunch later"
]
labels = [1, 1, 1, 1, 0, 0, 0, 0]  # 1 = Spam, 0 = Ham

# 2. Vectorization
print("Vectorizing data...")
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(emails)

# 3. Training the Model(Naive Bayes)
print("Training Naive Bayes model...")
model = MultinomialNB()
model.fit(X, labels)

# 4. Saving the Model and Vectorizer
print(f"Saving models to: {MODEL_DIR}")
with open(model_path, 'wb') as f:
    pickle.dump(model, f)

with open(vectorizer_path, 'wb') as f:
    pickle.dump(vectorizer, f)

print(" SUCCESS: Models regenerated cleanly without corruption.")