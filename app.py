import os
import cv2
import numpy as np
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(image, width, height):
    return cv2.resize(image, (width, height))

def calculate_green_area(image_path):
    image = cv2.imread(image_path)
    image = resize_image(image, 1920, 1080)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower_bound = np.array([25, 40, 40])
    upper_bound = np.array([100, 255, 255])

    mask = cv2.inRange(hsv, lower_bound, upper_bound)
    green_area = cv2.countNonZero(mask)
    total_area = image.shape[0] * image.shape[1]
    green_percentage = (green_area / total_area) * 100

    return green_percentage, mask

def estimate_trees(green_percentage, region_area_km2):
    trees_per_sq_km = 288673
    ratio = 21.7 / 100
    return green_percentage * ratio * trees_per_sq_km * region_area_km2

def get_suggestions_by_green_coverage(percentage):
    if percentage < 10:
        return "Critical: Very low green cover. Urgent afforestation needed."
    elif percentage < 20:
        return "Low: Area can benefit from increased greenery and urban forestry."
    elif percentage < 40:
        return "Healthy: Maintain and enhance current green cover."
    else:
        return "Excellent: Forest-like coverage. Prioritize conservation."

@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "Tree Estimation API is running"}), 200

@app.route("/api/calculate", methods=["POST"])
def calculate():
    file = request.files.get("file")
    area = request.form.get("area")

    if file and allowed_file(file.filename) and area:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        green_percentage, mask = calculate_green_area(file_path)
        tree_count = estimate_trees(green_percentage, float(area))
        suggestion = get_suggestions_by_green_coverage(green_percentage)

        # Optional: Save mask
        mask_path = os.path.join(app.config["UPLOAD_FOLDER"], f"mask_{filename}")
        cv2.imwrite(mask_path, mask)

        return jsonify({
            "green_percentage": round(green_percentage, 2),
            "tree_count": int(tree_count),
            "suggestion": suggestion
        })

    return jsonify({"error": "Invalid input. Please upload an image and provide area."}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
