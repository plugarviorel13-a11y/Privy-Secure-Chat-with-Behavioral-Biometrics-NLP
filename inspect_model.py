import pickle
import os

# Paths to the saved model and vectorizer
model_path = "app/ai_security/saved_models/spam_model.pkl"
vectorizer_path = "app/ai_security/saved_models/vectorizer.pkl"

print("--- INSPECTING SPAM AI BRAIN ---\n")

# 1.Open the Vectorizer (Text Processing)
if os.path.exists(vectorizer_path):
    with open(vectorizer_path, 'rb') as f:
        vocab = pickle.load(f)
    
    print(f" Vectorizer Loaded!")
    # See how many words it has learned
    print(f"Total number of words learned: {len(vocab.vocabulary_)}")
    # See the first 10 words learned
    print(f"Example words: {list(vocab.vocabulary_.keys())[:10]}")
else:
    print(" Did not find vectorizer.pkl")

print("\n" + "-"*30 + "\n")

# 2.Open the Model (Spam Detector, mathematics/probabilities)
if os.path.exists(model_path):
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    print(f" Model Loaded: {type(model).__name__}")
    # Seeing what classes he knows (0 = Ham/Good, 1 = Spam/Bad)
    print(f"Classes learned: {model.classes_}")
    # Seeing number of messages learned per class
    print(f"Number of messages analyzed during training: {model.class_count_}")
else:
    print(" Did not find spam_model.pkl")