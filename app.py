# main.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from PIL import Image
import numpy as np

app = Flask(__name__)
CORS(app)  # 🔥 Enable CORS

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===========================
# Calculate % Green in Image
# ===========================
def calculate_green_percentage(image_path):
    image = Image.open(image_path).convert("RGB")
    np_image = np.array(image)

    lower = np.array([30, 80, 30])
    upper = np.array([120, 255, 120])

    green_mask = ((np_image >= lower) & (np_image <= upper)).all(axis=2)

    green_pixels = np.count_nonzero(green_mask)
    total_pixels = np_image.shape[0] * np_image.shape[1]

    green_percentage = (green_pixels / total_pixels) * 100
    return round(green_percentage, 2)

# ===========================
# Estimate Tree Count
# ===========================
def estimate_tree_count(area_km2: float, green_percentage: float) -> int:
    if area_km2 <= 0 or green_percentage <= 0:
        return 0

    green_coverage = green_percentage / 100

    TREE_DENSITY_LOW = 500
    TREE_DENSITY_MEDIUM = 2000
    TREE_DENSITY_HIGH = 5000

    if green_coverage > 0.35:
        density = TREE_DENSITY_HIGH
    elif green_coverage > 0.15:
        density = TREE_DENSITY_MEDIUM
    else:
        density = TREE_DENSITY_LOW

    estimated_trees = area_km2 * green_coverage * density
    return round(estimated_trees)

# ===========================
# API Endpoint
# ===========================
@app.route("/api/calculate", methods=["POST"])
def calculate():
    if "file" not in request.files or "area" not in request.form:
        return jsonify({"error": "Missing image or area"}), 400

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

# ===========================
# Run Server
# ===========================
if __name__ == "__main__":
    app.run(debug=True)
