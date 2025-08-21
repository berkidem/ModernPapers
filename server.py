# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# server.py
#
# This script provides a simple backend for the ModernPapers application.
# It uses the Flask web framework to serve the main application (index.html)
# and provide API endpoints for managing a library of processed papers.
#
# To run this server:
# 1. Make sure you have Python and pip installed.
# 2. Install the required dependencies:
#    pip install -r requirements.txt
# 3. Run the server from your terminal:
#    python server.py
# 4. Open your web browser and navigate to http://127.0.0.1:8000.
#
# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

import os
import json
import xml.etree.ElementTree as ET
import base64
import re
import requests
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# Configuration
# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

# The port the server will run on. 8000 is used to match the original
# instructions in the README for running a simple Python server.
PORT = 8000

# The directory where processed papers will be stored.
# This will be created if it doesn't exist.
PAPERS_DIR = "papers"

# Initialize the Flask application.
app = Flask(__name__, static_folder=None)

# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# API Endpoints
#
# These endpoints provide the backend functionality for the paper library.
# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

@app.route("/api/papers", methods=["GET"])
def list_papers():
    """
    API endpoint to list all processed papers.

    Scans the PAPERS_DIR directory and returns a list of papers with their
    metadata (title, authors, directory name). This data is used by the
    frontend to display the library of previously processed papers.

    Returns:
        A JSON response containing a list of paper objects.
    """
    papers = []
    if not os.path.exists(PAPERS_DIR):
        return jsonify([])

    # Get a sorted list of paper directories, which will likely be the
    # order of creation.
    paper_dirs = sorted(os.listdir(PAPERS_DIR), reverse=True)

    for paper_dir in paper_dirs:
        dir_path = os.path.join(PAPERS_DIR, paper_dir)
        if os.path.isdir(dir_path):
            xml_path = os.path.join(dir_path, "paper.xml")
            if os.path.exists(xml_path):
                try:
                    # Parse the XML file to extract title and authors
                    tree = ET.parse(xml_path)
                    root = tree.getroot()
                    # Find the text of the first TITLE and AUTHORS tag.
                    # .text is used to get the inner text of the element.
                    # The 'or' provides a default value if the tag is not found.
                    title = root.findtext("TITLE", "Untitled")
                    authors = root.findtext("AUTHORS", "Unknown Authors")

                    papers.append({
                        "directory": paper_dir,
                        "title": title,
                        "authors": authors
                    })
                except ET.ParseError:
                    # If the XML is malformed, we can skip it or log an error.
                    # For now, we'll just print a message to the console.
                    print(f"Warning: Could not parse XML file at {xml_path}")

    return jsonify(papers)

@app.route("/api/save", methods=["POST"])
def save_paper():
    """
    API endpoint to save a newly processed paper.

    Receives the paper's XML content, images, and a desired directory name
    from the frontend. It then saves these files to a new subdirectory
    within the PAPERS_DIR. It also handles overwriting if requested.
    """
    data = request.get_json()

    if not data or 'directory_name' not in data or 'xml_content' not in data:
        return jsonify({"status": "error", "message": "Missing required data."}), 400

    # Sanitize the directory name to prevent directory traversal issues
    # and to create a clean, URL-friendly name.
    dir_name = data['directory_name']
    sane_dir_name = re.sub(r'[^a-zA-Z0-9_-]', '_', dir_name).lower()

    paper_path = os.path.join(PAPERS_DIR, sane_dir_name)
    overwrite = data.get("overwrite", False)

    # Check for duplicates if not in overwrite mode
    if not overwrite and os.path.exists(paper_path):
        return jsonify({
            "status": "error",
            "message": "A paper with this directory name already exists. Please choose another name or agree to overwrite."
        }), 409

    # Create the directory; exist_ok=True prevents errors if it already exists (in overwrite mode)
    os.makedirs(paper_path, exist_ok=True)

    # Save the paper.xml file
    xml_path = os.path.join(paper_path, 'paper.xml')
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(data['xml_content'])

    # Save the images
    if 'images' in data and data['images']:
        for image in data['images']:
            if 'filename' in image and 'data' in image:
                # The data is a base64 string, it might have a prefix like
                # "data:image/png;base64," which we need to remove.
                header, encoded = image['data'].split(",", 1)
                img_data = base64.b64decode(encoded)

                img_path = os.path.join(paper_path, image['filename'])
                with open(img_path, 'wb') as f:
                    f.write(img_data)

    return jsonify({"status": "success", "message": f"Paper saved in '{sane_dir_name}'."})


@app.route("/api/gemini", methods=["POST"])
def gemini_proxy():
    """
    API endpoint to act as a secure proxy to the Google Gemini API.

    This is necessary to avoid exposing the API key in the frontend client-side code.
    The frontend sends the request payload here, and this server adds the
    API key (loaded from the .env file) before forwarding it to Google.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "API key not configured on the server."}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload."}), 400

    # The model is now sent from the frontend in the payload
    model = data.get('model', 'gemini-1.5-flash-latest')

    # We remove the model from the payload before sending it to Google,
    # as it's part of the URL.
    if 'model' in data:
        del data['model']

    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    try:
        response = requests.post(gemini_url, json=data, timeout=120)
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        # Return Google's response directly to the client
        return jsonify(response.json())

    except requests.exceptions.RequestException as e:
        # Handle network errors or bad responses from Google
        error_message = f"Failed to communicate with Gemini API: {e}"
        # Try to include Google's error message if available
        try:
            error_details = e.response.json()
            error_message = error_details.get("error", {}).get("message", error_message)
        except:
            pass # Stick with the original error if we can't parse the response

        return jsonify({"error": error_message}), 502 # 502 Bad Gateway

# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# Static File Serving
#
# These routes are responsible for serving the main application (index.html)
# and any other static assets, including the saved papers themselves.
# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

@app.route("/")
def serve_index():
    """
    Serves the main index.html file of the application.
    """
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def serve_static_files(path):
    """
    Serves other static files from the root directory (e.g., gemini-proxy.php)
    or from the papers directory.

    This is a catch-all route. It will first try to find the file in the
    PAPERS_DIR and then fall back to the root directory. This allows access
    to URLs like /papers/my_paper/paper.xml.
    """
    if path.startswith(PAPERS_DIR + "/") and os.path.exists(path):
        return send_from_directory(".", path)

    # For files like 'gemini-proxy.php' or other assets in the root.
    if os.path.exists(path):
        return send_from_directory(".", path)

    # If the file is not found, return a 404 error.
    return "File not found", 404

# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# Main Entry Point
# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

if __name__ == "__main__":
    # Create the 'papers' directory if it doesn't already exist.
    if not os.path.exists(PAPERS_DIR):
        os.makedirs(PAPERS_DIR)

    # Run the Flask app.
    # The host '0.0.0.0' makes the server accessible from other devices on the
    # same network. 'debug=True' provides helpful error messages during
    # development but should be turned off in a production environment.
    app.run(host="0.0.0.0", port=PORT, debug=True)
