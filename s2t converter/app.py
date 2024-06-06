from flask import Flask, render_template, request, flash
import os
import speech_recognition as sr
from textblob import TextBlob
from better_profanity import profanity
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Set a secret key for flashing messages

# Function to convert audio to text, filter profanity, and rate
def process_audio(file_path):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)

            # Perform sentiment analysis
            sentiment = analyze_sentiment(text)

            # Filter profanity
            filtered_text = profanity.censor(text)

            # Check if profanity is present
            profanity_present = profanity.contains_profanity(text)

            # Calculate rating
            rating = max(5 - profanity_present * 0.5, 0)

            return text, filtered_text, sentiment, rating
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None, None, None, None

def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment_score = blob.sentiment.polarity

    if sentiment_score > 0.2:
        return "happy"
    elif sentiment_score < -0.2:
        return "angry"
    else:
        return "normal"

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None

    if request.method == 'POST':
        folder_path = request.form['folder_path']
        if os.path.exists(folder_path):
            audio_files = [f for f in os.listdir(folder_path) if f.endswith('.wav')]
            if audio_files:
                results = []
                for file in audio_files:
                    file_path = os.path.join(folder_path, file)
                    text, filtered_text, sentiment, rating = process_audio(file_path)
                    results.append({'file': file, 'text': text, 'filtered_text': filtered_text, 'sentiment': sentiment, 'rating': rating})

                # Create a DataFrame from the results
                df = pd.DataFrame(results)

                # Export the DataFrame to an Excel file
                excel_file_path = os.path.join(folder_path, 'results.xlsx')
                df.to_excel(excel_file_path, index=False)

                result = results
            else:
                flash("No valid audio files found in the provided folder.")
        else:
            flash("Folder path does not exist.")

    return render_template('index.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
