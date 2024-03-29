# Import and variables
import os
import numpy as np
import tensorflow as tf
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from PIL import Image
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.preprocessing import image

app = Flask(__name__)

dir_path = os.path.dirname(os.path.realpath(__file__))
app.config['UPLOAD_FOLDER'] = "uploads"
app.config['STATIC_FOLDER'] = "static"
app.config['HOST'] = '0.0.0.0'
app.config['PORT'] = 80
app.config['IS_DEBUG'] = True
sizeofimage = 256

# Load model
cauliflower_model = tf.keras.models.load_model(app.config['STATIC_FOLDER'] + "/model/Cauliflower_best_model.h5")

# Preprocess an image
def preprocess(image):
    image = tf.image.decode_jpeg(image, channels=3)
    image = tf.image.resize(image, [sizeofimage, sizeofimage])
    image /= 255.0  # normalize
    return image

# Read the image from path
def load(path):
    image = tf.io.read_file(path)
    return preprocess(image)

# Add a pre-screenr to catch image that doesn't belong to the class
# Load pre-trained ResNet50 model
pre_trained_model = tf.keras.applications.ResNet50(weights='imagenet')

# Define a function to preprocess the image and predict the class using the pre-trained model
def model_predict_image(image_path):
    img = image.load_img(image_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    preds = pre_trained_model.predict(x)
    return tf.keras.applications.resnet50.decode_predictions(preds, top=1)[0][0][1]

# Predict & classify image
def model_classify(model, image_path):
    # Add a pre-screener to catch images that are not cauliflower or do not belong to the same category
    if model_predict_image(image_path) != "cauliflower":
        return "Not a cauliflower image", 0.0

    finalimage = load(image_path)
    finalimage = tf.reshape(finalimage, (1, sizeofimage, sizeofimage, 3))

    probability = cauliflower_model.predict(finalimage)
    label = "Healthy" if probability[0][0] <= 0.5 \
        else "Diseased"

    classified_probability = probability[0][0] \
        if probability[0][0] >= 0.5 \
        else 1 - probability[0][0]

    return label, classified_probability

# Index landing page
@app.route("/")
def index():
    return render_template("index.html")

# About page
@app.route("/about")
def about():
    return render_template("about.html")

# Contact page
@app.route("/contact")
def contact():
    return render_template("contact.html")

# Feedback page
@app.route("/feedback")
def feedback():
    return redirect("https://forms.office.com/r/FbhU0KprGJ")

# Classify page
@app.route("/classify", methods=["POST", "GET"])
def predict():
    if request.method == "POST":
        file = request.files["image"]
        upload_image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(upload_image_path)
        label = model_predict_image(upload_image_path)
        label, probability = model_classify(cauliflower_model, upload_image_path)
        probability = round((probability * 100), 2)
        return render_template("classified.html", imagefile=file.filename, label=label, prob=probability)
    else:
        return render_template("classify.html")

@app.route("/classify/<filename>")
def send_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['IS_DEBUG'])
