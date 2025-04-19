import os
import cv2
import numpy as np
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
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

    # Range for yellowish-green to dark-green
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

def get_suggestions(tree_count):
    if tree_count < 5000:
        return "Low tree density. Consider afforestation programs."
    elif tree_count < 20000:
        return "Moderate tree density. Focus on enhancing urban green spaces."
    else:
        return "High tree density. Prioritize conservation efforts."

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        area = request.form.get("area")

        if file and allowed_file(file.filename) and area:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            green_percentage, mask = calculate_green_area(file_path)
            tree_count = estimate_trees(green_percentage, float(area))
            suggestion = get_suggestions(tree_count)

            mask_path = os.path.join(app.config["UPLOAD_FOLDER"], f"mask_{filename}")
            cv2.imwrite(mask_path, mask)

            return render_template("index.html", 
                                   image_url=url_for('static', filename=f"uploads/{filename}"),
                                   mask_url=url_for('static', filename=f"uploads/mask_{filename}"),
                                   green_percentage=green_percentage,
                                   tree_count=int(tree_count),
                                   suggestion=suggestion)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

#############################################################################################

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
        suggestion = get_suggestions(tree_count)

        mask_path = os.path.join(app.config["UPLOAD_FOLDER"], f"mask_{filename}")
        cv2.imwrite(mask_path, mask)

        return {
            "image_url": url_for('static', filename=f"uploads/{filename}"),
            "mask_url": url_for('static', filename=f"uploads/mask_{filename}"),
            "green_percentage": green_percentage,
            "tree_count": int(tree_count),
            "suggestion": suggestion
        }

    return {"error": "Invalid input"}, 