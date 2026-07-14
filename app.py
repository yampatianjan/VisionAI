import os
import time
import json
import boto3
from PIL import Image
from werkzeug.utils import secure_filename
from utils.pdf_generator import generate_report
from flask import (
    Flask,
    render_template,
    request,
    send_file,
    session
)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "development_secret_key")
# -----------------------------
# Allowed image types
# -----------------------------
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# -----------------------------
# Statistics Functions
# -----------------------------
def load_stats():
    with open("app_stats.json", "r") as file:
        return json.load(file)


def save_stats(stats):
    with open("app_stats.json", "w") as file:
        json.dump(stats, file, indent=4)


# -----------------------------
# AWS Rekognition Client
# -----------------------------
client = boto3.client(
    "rekognition",
    region_name="ap-south-1"
)


# -----------------------------
# Home Page
# -----------------------------

@app.route("/")
def home():

    stats = load_stats()
    stats["visitors"] += 1
    save_stats(stats)

    return render_template(
        "index.html",
        stats=stats
    )


# -----------------------------
# Analyze Image
# -----------------------------

@app.route("/analyze", methods=["POST"])
def analyze():

    image = request.files["image"]

    if not image or image.filename == "":
        return "No image selected."

    if not allowed_file(image.filename):
        return "Only PNG, JPG, JPEG and WEBP images are allowed."

    filename = secure_filename(image.filename)

    filepath = os.path.join("static", "uploads", filename)

    image.save(filepath)
    img = Image.open(filepath)

    width, height = img.size

    image_format = img.format

    file_size = round(os.path.getsize(filepath) / 1024, 2)

    # Load statistics
    stats = load_stats()
   

    with open(filepath, "rb") as img:
        image_bytes = img.read()

    # -----------------------------
    # Start Timer
    # -----------------------------
    start = time.time()

    # -----------------------------
    # Detect Labels
    # -----------------------------
    response = client.detect_labels(
        Image={"Bytes": image_bytes},
        MaxLabels=10,
        MinConfidence=70
    )

    # -----------------------------
    # Detect Faces
    # -----------------------------
    face_response = client.detect_faces(
        Image={"Bytes": image_bytes},
        Attributes=["ALL"]
    )

    
    end = time.time()
    processing_time = round(end - start, 2)

    # -----------------------------
    # Labels
    # -----------------------------
    labels = []

    for label in response["Labels"]:
        labels.append({
            "name": label["Name"],
            "confidence": round(label["Confidence"], 2)
        })

    highest = max(labels, key=lambda x: x["confidence"])

    # -----------------------------
    # Icons
    # -----------------------------
    icons = {
        "Person": "👤",
        "Face": "😊",
        "Dog": "🐶",
        "Cat": "🐱",
        "Laptop": "💻",
        "Computer": "💻",
        "Electronics": "💻",
        "PC": "🖥️",
        "Phone": "📱",
        "Car": "🚗",
        "Tree": "🌳",
        "Book": "📖",
        "Bottle": "🧴",
        "Food": "🍔",
        "Fruit": "🍎",
        "Smile": "😊"
    }

    for label in labels:
        label["icon"] = icons.get(label["name"], "🔹")

    highest["icon"] = icons.get(highest["name"], "🔹")

    # -----------------------------
    # Face Details
    # -----------------------------
    faces = []

    for face in face_response["FaceDetails"]:

        emotion = max(
            face["Emotions"],
            key=lambda x: x["Confidence"]
        )

        faces.append({
            "gender": face["Gender"]["Value"],
            "gender_confidence": round(face["Gender"]["Confidence"], 2),
            "emotion": emotion["Type"],
            "emotion_confidence": round(emotion["Confidence"], 2),
            "age_low": face["AgeRange"]["Low"],
            "age_high": face["AgeRange"]["High"]
        })

    # Update statistics
    stats["images"] += 1
    stats["faces"] += len(faces)
    save_stats(stats)

    # Store latest analysis so PDF can be generated
    session["analysis"] = {
    "filename": filename,
    "image_format": image_format,
    "width": width,
    "height": height,
    "file_size": file_size,
    "processing_time": processing_time,
    "labels": labels,
    "faces": faces
}
    

    # -----------------------------
    # Render Page
    # -----------------------------
    return render_template(
        "index.html",
        labels=labels,
        faces=faces,
        image_path=filepath,
        filename=filename,
        total=len(labels),
        highest=highest,
        processing_time=processing_time,
        file_size=file_size,
        image_width=width,
        image_height=height,
        image_format=image_format,
        stats=stats
    )

@app.route("/download-report")
def download_report():

    analysis = session.get("analysis")

    if not analysis:

        return "No analysis available."

    pdf = generate_report(analysis)

    return send_file(

        pdf,

        as_attachment=True,

        download_name="VisionAI_Report.pdf",

        mimetype="application/pdf"

    )
# -----------------------------
# Run Application
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)