from flask import Flask, request, jsonify, send_from_directory, render_template
from PIL import Image, ImageEnhance
import numpy as np
import random
import os
import time
from flask_cors import CORS, cross_origin

BACKED_EP_WITH_SCHEMA=os.environ['BACKEND_HOST']
VIDEO_GENRATION_URL=os.environ['API_GW_URL']
app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/learn-about-tensors')
def learn_tensors():
    return render_template('learn-about-tensors.html')

@app.route('/try-some-examples')
def visualize_tensors():
    return render_template(
        'try-some-examples.html',
        backend_endpoint_with_schema=BACKED_EP_WITH_SCHEMA,
        video_generation_endpoint=VIDEO_GENRATION_URL
    )

@app.route('/cleanup')
def cleanup():
    now = time.time()
    threshold_seconds = 5 * 60  # 5 minutes

    deleted_files = []

    for file in os.listdir():
        if 'img' in file and os.path.isfile(file):
            file_age = now - os.path.getmtime(file)
            if file_age > threshold_seconds:
                os.remove(file)
                deleted_files.append(file)

    return jsonify({'cleaned': deleted_files}), 200


# backend images endpoint
@app.route('/images/<filename>')
def images_backend(filename):
    return send_from_directory('.', filename)

# Fronted images endpoint
@app.route('/images-front/<filename>')
def images_frontend(filename):
    return send_from_directory('templates/images', filename)

# Brightness endpoint
@app.route('/api/tensors/brightness', methods=['POST'])
def brightness():
    file = request.files.get('image')

    if not file:
        return jsonify({'error': 'No file provided'}), 400

    try:
        # Open the image using PIL
        img = Image.open(file.stream).convert('RGB')

        width, height = img.size
        img = img.resize((width // 3, height // 3),  Image.Resampling.LANCZOS)

        # Convert to numpy array
        img_np = np.array(img)
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ['.jpg', '.jpeg', '.png']:
            return jsonify({
                'error-message': 'Only jpg/jpeg/png extensions allowed.'
            })

        # Save the original image
        img_name=f"img-{random.getrandbits(32)}{file_extension}"
        Image.fromarray(img_np).save(img_name)

        # Multiply pixel values by the factor
        bright_image = img_np * 1.5
        # Clip values to stay within 0-255 range
        bright_image = np.clip(bright_image, 0, 255)
        bright_image_matrix = bright_image.astype(np.uint8)
        Image.fromarray(bright_image_matrix).save(f"new-{img_name}")
        return jsonify({
            'original_image_url': f"{BACKED_EP_WITH_SCHEMA}/images/{img_name}",
            'transformed_image_url': f"{BACKED_EP_WITH_SCHEMA}/images/new-{img_name}"
        })
    except Exception as e:
        raise Exception(e)
        return jsonify({'error-message': str(e)}), 500

# Brightness endpoint
@app.route('/api/tensors/grayscale', methods=['POST'])
def grayscale():
    file = request.files.get('image')
    if not file:
        return jsonify({'error': 'No file provided'}), 400

    try:
        # Open the image using PIL
        img = Image.open(file.stream).convert('RGB')
        width, height = img.size
        img = img.resize((width // 3, height // 3),  Image.Resampling.LANCZOS)
        # Convert to numpy array
        img_np = np.array(img)
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ['.jpg', '.jpeg', '.png']:
            return jsonify({
                'error-message': 'Only jpg/jpeg/png extensions allowed.'
            })

        # Save the original image
        img_name=f"img-{random.getrandbits(32)}{file_extension}"
        Image.fromarray(img_np).save(img_name)

        #### Implementation
        # Convert RGB to grayscale using the weighted formula
        # Keep the first two dimensions (height, width), and compute the weighted sum for the third dimension (R, G, B)
        grayscale_matrix = 0.3 * img_np[:, :, 0] + 0.59 * img_np[:, :, 1] + 0.11 * img_np[:, :, 2]

        # Convert back to an image for visualization
        grayscale_image = Image.fromarray(grayscale_matrix.astype('uint8'))
        grayscale_image.save(f"new-{img_name}")

        return jsonify({
            'original_image_url': f"{BACKED_EP_WITH_SCHEMA}/images/{img_name}",
            'transformed_image_url': f"{BACKED_EP_WITH_SCHEMA}/images/new-{img_name}"
        })
    except Exception as e:
        raise Exception(e)
        return jsonify({'error-message': str(e)}), 500
       

if __name__ == '__main__':
    app.run(host="0.0.0.0")
