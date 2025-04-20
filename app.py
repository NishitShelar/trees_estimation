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

    # Broad HSV range for Indian greenery context
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([85, 255, 255])

    green_mask = cv2.inRange(hsv_image, lower_green, upper_green)

    green_pixels = np.count_nonzero(green_mask)
    total_pixels = green_mask.size
    green_percentage = (green_pixels / total_pixels) * 100

    return round(green_percentage, 2)

# ===============================
# TREE ESTIMATION
# ===============================
def estimate_tree_count(area_km2: float, green_percentage: float) -> int:
    if area_km2 <= 0 or green_percentage <= 0:
        return 0

    green_coverage = green_percentage / 100

    if green_coverage > 0.35:
        density = 12000  # Dense green
    elif green_coverage > 0.15:
        density = 7500   # Moderate green
    else:
        density = 3000   # Sparse green

    estimated_trees = area_km2 * green_coverage * density
    return round(estimated_trees)

# ===============================
# DYNAMIC SUGGESTION
# ===============================
def generate_suggestion(green_percentage: float) -> str:
    if green_percentage > 35:
        return "The area is densely green. Maintain and protect existing greenery. 🌳"
    elif green_percentage > 15:
        return "The area has moderate greenery. Consider adding more trees to enhance green cover. 🌿"
    elif green_percentage > 5:
        return "The area is sparsely green. Urban greening programs or roadside plantations can help. 🌱"
    else:
        return "The area lacks greenery. Strongly consider afforestation or park development. 🚧"

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
    suggestion = generate_suggestion(green_percentage)

    return jsonify({
        "green_percentage": green_percentage,
        "tree_count": estimated_trees,
        "suggestion": suggestion,
        "areaSize": area_km2
    })

# ===============================
# RENDER DEPLOYMENT
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
