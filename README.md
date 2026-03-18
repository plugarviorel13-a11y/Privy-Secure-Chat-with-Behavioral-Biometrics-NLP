# Privy - AI-Enhanced Secure Messenger

**Privy** is a Proof of Concept (PoC) secure messaging application that goes beyond traditional password authentication. It introduces a Layered Security Architecture integrating **Behavioral Biometrics** and **Machine Learning** to actively protect user sessions and prevent social engineering attacks.

## Key Security Features

1. **Continuous Authentication (Keystroke Dynamics)**
   * Implements a Statistical Anomaly Detection algorithm that analyzes user typing patterns (Dwell Time) in real-time.
   * Defends against session hijacking, bot/script automated messaging, and unauthorized physical access.

2. **Active Anti-Phishing Engine (NLP)**
   * Integrates a Supervised Machine Learning model (`Multinomial Naive Bayes` via Scikit-Learn) to scan incoming messages.
   * Trained on a custom dataset to identify and flag social engineering and phishing attempts (malicious links, CEO fraud, etc.) with high accuracy.

3. **Data Obfuscation & Simulated E2E Architecture**
   * Messages are processed via Base64 encoding at the database level to simulate payload encryption, ensuring that plain text is never stored directly in the relational database.
   * Built on a secure REST API architecture preventing common web vulnerabilities (like CSRF via custom `X-User-ID` headers).

## Tech Stack

* **Backend:** Python 3, Flask (RESTful API)
* **Frontend:** Vanilla JavaScript, HTML5, CSS3 (DOM API, Fetch API)
* **Machine Learning / AI:** Scikit-Learn, Pandas, NumPy
* **Database:** MySQL

## How it works (Under the hood)
* The **Biometric Engine** acts as an unsupervised online classifier, instantly flagging unrealistic typing speeds (<70ms for bots) or suspicious delays.
* The **Phishing Engine** utilizes a `CountVectorizer` (Bag of Words) to evaluate the probability of a message being malicious based on a pre-trained dataset, completely decoupled from the application logic.
