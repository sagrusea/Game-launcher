from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import sys
import os
from pathlib import Path
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the services directory to the system path
service_dir = Path(__file__).parent.parent / 'services'
sys.path.append(str(service_dir))

try:
    import game_manager
except ImportError as e:
    logger.error(f"Error importing game_manager: {e}")
    logger.error(f"Python path: {sys.path}")
    logger.error(f"Looking for module in: {service_dir}")
    raise

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Initialize the database
game_manager.init_db()

# Directory to store cover art images
COVER_ART_DIR = Path(__file__).parent / 'cover_art'
CACHE_COVER_ART_DIR = Path(os.getenv("CACHE_COVER_ART_DIR", "cache/cover_art"))
SETTINGS_FILE = Path(__file__).parent / 'settings.json'
MUSIC_DIR = Path(os.getenv("MUSIC_DIR", "music"))

@app.route("/", methods=["GET"])
def root():
    logger.info("Root endpoint called")
    return jsonify({
        "name": "Game Launcher API",
        "version": "1.0",
        "endpoints": {
            "GET /api/games": "List all games",
            "POST /api/games": "Add a new game",
            "POST /api/games/<id>/run": "Run a game",
            "PATCH /api/games/<id>": "Update a game",
            "DELETE /api/games/<id>": "Delete a game",
            "POST /api/games/scan": "Scan directory for games",
            "GET /cover_art/<filename>": "Get cover art image",
            "GET /api/settings": "Get settings",
            "POST /api/settings": "Update settings",
            "GET /api/music": "List available music files",
            "GET /music/<filename>": "Get background music file"
        }
    })

@app.route("/api/games", methods=["GET"])
def list_games():
    logger.info("List games endpoint called")
    games = game_manager.get_games()
    return jsonify([{
        "id": g[0], 
        "title": g[1], 
        "cover_art_path": g[2],
        "background": g[3] if g[3] is not None else g[2]  # Use background if available, otherwise use cover_art_path
    } for g in games])

@app.route("/api/games", methods=["POST"])
def add_game():
    data = request.json
    title = data.get("title")
    executable_path = data.get("executable_path")
    cover_art_path = data.get("cover_art_path", None)
    
    if not title or not executable_path:
        logger.error("Title and executable_path are required")
        return jsonify({"error": "Title and executable_path are required"}), 400
    
    game_manager.add_game_to_db(title, executable_path, cover_art_path)
    logger.info(f"Game '{title}' added successfully")
    return jsonify({"message": f"Game '{title}' added successfully."}), 201

@app.route("/api/games/<int:game_id>/run", methods=["POST"])
def run_game(game_id):
    try:
        game_manager.run_game(game_id)
        logger.info(f"Game with ID {game_id} launched successfully")
        return jsonify({"message": f"Game with ID {game_id} launched successfully."}), 200
    except Exception as e:
        logger.error(f"Error launching game with ID {game_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/games/<int:game_id>", methods=["PATCH"])
def update_game(game_id):
    data = request.json
    title = data.get("title")
    executable_path = data.get("executable_path")
    cover_art_path = data.get("cover_art_path")
    
    game_manager.update_game_info(game_id, title, executable_path, cover_art_path)
    logger.info(f"Game with ID {game_id} updated successfully")
    return jsonify({"message": f"Game with ID {game_id} updated successfully."}), 200

@app.route("/api/games/<int:game_id>", methods=["DELETE"])
def delete_game(game_id):
    try:
        game_manager.delete_game(game_id)
        logger.info(f"Game with ID {game_id} deleted successfully")
        return jsonify({"message": f"Game with ID {game_id} deleted successfully."}), 200
    except Exception as e:
        logger.error(f"Error deleting game with ID {game_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/games/scan", methods=["POST"])
def scan_games():
    directory = request.json.get("directory", ".")
    try:
        game_manager.scan_for_games(directory)
        logger.info(f"Scanned for games in directory '{directory}'")
        return jsonify({"message": f"Scanned for games in directory '{directory}'."}), 200
    except Exception as e:
        logger.error(f"Error scanning for games in directory '{directory}': {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/games/scan_epic", methods=["POST"])
def scan_epic_games():
    try:
        game_manager.scan_for_epic_games()
        logger.info("Scanned for Epic Games")
        return jsonify({"message": "Scanned for Epic Games."}), 200
    except Exception as e:
        logger.error(f"Error scanning for Epic Games: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/games/bulk_delete", methods=["POST"])
def bulk_delete_games():
    data = request.json
    game_ids = data.get("game_ids", [])
    
    if not game_ids:
        logger.error("No game IDs provided for bulk delete")
        return jsonify({"error": "No game IDs provided"}), 400
    
    try:
        game_manager.delete_games(game_ids)
        logger.info(f"Games with IDs {game_ids} deleted successfully")
        return jsonify({"message": f"Games with IDs {game_ids} deleted successfully."}), 200
    except Exception as e:
        logger.error(f"Error deleting games with IDs {game_ids}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/cover_art/<filename>")
def get_cover_art(filename):
    logger.info(f"Request for cover art: {filename}")
    response = make_response(send_from_directory(CACHE_COVER_ART_DIR, filename))
    response.headers['Cache-Control'] = 'public, max-age=31536000'  # Cache for 1 year
    return response

@app.route("/api/settings", methods=["GET"])
def get_settings():
    logger.info("Get settings endpoint called")
    with open(SETTINGS_FILE, "r") as file:
        settings = json.load(file)
    return jsonify(settings)

@app.route("/api/settings", methods=["POST"])
def update_settings():
    data = request.json
    with open(SETTINGS_FILE, "w") as file:
        json.dump(data, file, indent=4)
    logger.info("Settings updated successfully")
    return jsonify({"message": "Settings updated successfully."})

@app.route("/api/music", methods=["GET"])
def list_music():
    logger.info("List music endpoint called")
    music_files = [f for f in os.listdir(MUSIC_DIR) if os.path.isfile(os.path.join(MUSIC_DIR, f))]
    return jsonify(music_files)

@app.route("/music/<filename>")
def get_music(filename):
    logger.info(f"Request for music: {filename}")
    return send_from_directory(MUSIC_DIR, filename)

@app.route("/api/config", methods=["POST"])
def update_config():
    new_config = request.json
    try:
        game_manager.edit_config(new_config)
        logger.info("Configuration updated successfully")
        return jsonify({"message": "Configuration updated successfully."}), 200
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logger.info("Starting backend server")
    # Disable reloader to prevent the Flask app from restarting
    app.run(debug=True, port=5000, use_reloader=False)