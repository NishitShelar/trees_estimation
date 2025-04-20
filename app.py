from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from PIL import Image
import numpy as np
import cv2

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ============================================
# ✅ HSV-Based Green Detection for Map Images
# ============================================
def calculate_green_percentage(image_path):
    image = Image.open(image_path).convert("RGB")
    image_np = np.array(image)

    # Convert RGB to HSV
    hsv_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)

    # Define green range in HSV
    lower_green = np.array([35, 40, 40])    # Hue: 35–85 = green zone
    upper_green = np.array([85, 255, 255])

    # Create mask of green areas
    mask = cv2.inRange(hsv_image, lower_green, upper_green)

    green_pixels = np.count_nonzero(mask)
    total_pixels = mask.size

    green_percentage = (green_pixels / total_pixels) * 100
    return round(green_percentage, 2)

# ============================================
# 🌳 Tree Estimation Based on Area & Green %
# ============================================
def estimate_tree_count(area_km2: float, green_percentage: float) -> int:
    if area_km2 <= 0 or green_percentage <= 0:
        return 0

    green_coverage = green_percentage / 100

    TREE_DENSITY_LOW = 500     # roads
    TREE_DENSITY_MEDIUM = 2000 # semi-green
    TREE_DENSITY_HIGH = 5000   # dense green

    if green_coverage > 0.35:
        density = TREE_DENSITY_HIGH
    elif green_coverage > 0.15:
        density = TREE_DENSITY_MEDIUM
    else:
        density = TREE_DENSITY_LOW

    estimated_trees = area_km2 * green_coverage * density
    return round(estimated_trees)

# ============================================
# 🌐 API Endpoint
# ============================================
@app.route("/api/calculate", methods=["POST"])
def calculate():
    if "file" not in request.files or "area" not in request.form:
        return jsonify({"error": "Missing image or area"}), 400

    file = request.files["file"]
    area_km2 = float(request.form["area"])
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Analyze image
    green_percentage = calculate_green_percentage(filepath)
    estimated_trees = estimate_tree_count(area_km2, green_percentage)

    return jsonify({
        "green_percentage": green_percentage,
        "tree_count": estimated_trees,
        "suggestion": "Consider planting more trees along non-green areas.",
        "areaSize": area_km2
    })

# ============================================
# 🔁 Start Server (for Render compatibility)
# ============================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
