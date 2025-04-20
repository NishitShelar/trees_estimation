from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import numpy as np
from PIL import Image
import cv2

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===============================
# GREEN DETECTION USING HSV
# ===============================
def calculate_green_percentage(image_path):
    image = Image.open(image_path).convert("RGB")
    image_np = np.array(image)

    # Convert to HSV
    hsv_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)

    # Define broad green hue range for Indian context
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([85, 255, 255])

    # Create green mask
    green_mask = cv2.inRange(hsv_image, lower_green, upper_green)

    green_pixels = np.count_nonzero(green_mask)
    total_pixels = green_mask.size

    green_percentage = (green_pixels / total_pixels) * 100
    return round(green_percentage, 2)

# ===============================
# TREE ESTIMATION LOGIC (INDIA)
# ===============================
def estimate_tree_count(area_km2: float, green_percentage: float) -> int:
    if area_km2 <= 0 or green_percentage <= 0:
        return 0

    green_coverage = green_percentage / 100

    # India-specific calibrated tree densities
    if green_coverage > 0.35:
        density = 12000  # Dense park/forests
    elif green_coverage > 0.15:
        density = 7500   # Mixed-use green
    else:
        density = 3000   # Sparse roadside green

    estimated_trees = area_km2 * green_coverage * density
    return round(estimated_trees)

# ===============================
# API ENDPOINT
# ===============================
@app.route("/api/calculate", methods=["POST"])
def calculate():
    if "file" not in request.files or "area" not in request.form:
        return jsonify({"error": "Missing file or area"}), 400

    file = request.files["file"]
    area_km2 = float(request.form["area"])
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    green_percentage = calculate_green_percentage(filepath)
    estimated_trees = estimate_tree_count(area_km2, green_percentage)

    return jsonify({
        "green_percentage": green_percentage,
        "tree_count": estimated_trees,
        "suggestion": "Consider planting more trees along non-green areas.",
        "areaSize": area_km2
    })

# ===============================
# FOR RENDER DEPLOYMENT
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
