import atexit
from collections import Counter
import cv2
from flask import Flask, render_template, Response, send_from_directory
from deepface import DeepFace
import matplotlib.pyplot as plt
import numpy as np
import io

app = Flask(__name__)

# List to store detected emotions
emotions_list = []

# Emojis corresponding to each emotion
emotion_emojis = {
    'happy': '',
    'sad': '',
    'angry': '',
    'surprise': '',
    'fear': '',
    'neutral': '',
    'disgust': '',
}

# Initialize webcam
cap = cv2.VideoCapture(0)

# Function to release the webcam when the application exits
def release_webcam():
    cap.release()
    cv2.destroyAllWindows()

# Register the release_webcam function to be called at exit
atexit.register(release_webcam)

# Function to analyze frame and update emotions_list
def analyze_frame(frame):
    result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
    emotion = result[0]['dominant_emotion']
    emotions_list.append(emotion)
    return emotion

# Function to generate video frames
def generate_frames():
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        emotion = analyze_frame(frame)

        # Display emotion information on the frame
        cv2.putText(frame, f'Emotion: {emotion}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        # Convert the frame to bytes
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        # Yield the frame bytes
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# Function to generate and save the emotion distribution chart
# Function to generate and save the emotion distribution bar chart
def generate_emotion_chart(emotion_counter):
    emotions = list(emotion_counter.keys())
    counts = list(emotion_counter.values())

    # Create a bar chart with emojis
    fig, ax = plt.subplots(figsize=(8, 6))  # Adjust the figure size as needed

    # Bar chart with additional spacing between emotion names
    bar_width = 0.8
    bar_positions = np.arange(len(emotions))

    # Plot bars
    bars = ax.bar(bar_positions, counts, width=bar_width, align='center')

    # Set emotion names as x-axis labels with additional spacing
    name_spacing = 0.2
    ax.set_xticks(bar_positions)
    ax.set_xticklabels(emotions, ha='center', rotation=45)
    ax.tick_params(axis='x', pad=name_spacing * 100)  # Adjust spacing between emotion names

    # Display counts on top of the bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f'{count}\n', ha='center', va='bottom')

    # Save the chart in memory with reduced size and resolution
    chart_image = io.BytesIO()
    plt.savefig(chart_image, format='png', bbox_inches='tight', dpi=100)  # Adjust dpi as needed
    plt.close()

    # Return the chart image as bytes
    return chart_image.getvalue()



# Route to serve the webcam feed with emotion information
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Route to serve the emotions distribution as a pie chart with emojis
@app.route('/emotions_chart')
def emotions_chart():
    emotion_counter = Counter(emotions_list)
    chart_image = generate_emotion_chart(emotion_counter)
    
    # Return the chart image as a response
    return Response(chart_image, mimetype='image/png')

# Route to display the webcam feed with emotion information and the emotions chart
@app.route('/')
def index():
    return render_template('index.html')

# Route to serve the static emotions chart image
@app.route('/static/<path:filename>')
def static_file(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True)
