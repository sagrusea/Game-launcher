from flask import Blueprint, request, jsonify
from services.game_manager import GameManager

games_blueprint = Blueprint("games", __name__)
game_manager = GameManager("db/launcher.db")  # Path to your SQLite database

# List all games
@games_blueprint.route("/", methods=["GET"])
def list_games():
    games = game_manager.get_all_games()
    return jsonify(games)

# Add a new game
@games_blueprint.route("/", methods=["POST"])
def add_game():
    data = request.json
    title = data.get("title")
    executable_path = data.get("executable_path")
    cover_art_path = data.get("cover_art_path", None)

    if not title or not executable_path:
        return jsonify({"error": "Title and executable_path are required"}), 400

    game_manager.add_game(title, executable_path, cover_art_path)
    return jsonify({"message": "Game added successfully"}), 201

# Delete a game by ID
@games_blueprint.route("/<int:game_id>", methods=["DELETE"])
def delete_game(game_id):
    game_manager.delete_game(game_id)
    return jsonify({"message": "Game deleted successfully"}), 200

# Launch a game by ID
@games_blueprint.route("/<int:game_id>/launch", methods=["POST"])
def launch_game(game_id):
    success = game_manager.launch_game(game_id)
    if success:
        return jsonify({"message": "Game launched successfully"}), 200
    else:
        return jsonify({"error": "Failed to launch game"}), 500
