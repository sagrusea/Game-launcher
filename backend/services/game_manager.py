import sqlite3
import os
import subprocess
import json
import shutil

try:
    import curses
    CURSES_AVAILABLE = True
except ImportError:
    CURSES_AVAILABLE = False

# Load configuration from JSON file
config_path = os.path.join(os.path.dirname(__file__), "config.json")
with open(config_path, "r") as config_file:
    config = json.load(config_file)

DB_PATH = config["db_path"]
COVER_ART_DIR = os.path.join(os.path.dirname(__file__), "../api/cover_art")
CACHE_COVER_ART_DIR = "C:/Users/matej/AppData/Roaming/sagrusea/game-launcher/cache/cover_art"

def init_db():
    print(config_path)
    print(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            executable_path TEXT NOT NULL,
            cover_art_path TEXT,
            background TEXT,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.commit()
    con.close()

def get_lowest_available_id():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id FROM games ORDER BY id")
    ids = [row[0] for row in cur.fetchall()]
    con.close()
    for i in range(1, len(ids) + 2):
        if i not in ids:
            return i

def add_game_to_db(title, executable_path, cover_art_path=None):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    new_id = get_lowest_available_id()
    if cover_art_path:
        cover_art_filename = os.path.basename(cover_art_path)
        cover_art_dest = os.path.join(COVER_ART_DIR, cover_art_filename)
        cache_cover_art_dest = os.path.join(CACHE_COVER_ART_DIR, cover_art_filename)
        os.makedirs(COVER_ART_DIR, exist_ok=True)
        os.makedirs(CACHE_COVER_ART_DIR, exist_ok=True)
        shutil.copy(cover_art_path, cover_art_dest)
        shutil.copy(cover_art_path, cache_cover_art_dest)
        cover_art_path = cover_art_filename
    cur.execute("INSERT INTO games (id, title, executable_path, cover_art_path) VALUES (?, ?, ?, ?)", 
                (new_id, title, executable_path, cover_art_path))
    con.commit()
    con.close()
    print(f"Game '{title}' added successfully with ID {new_id}.")

def run_game(game_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT executable_path FROM games WHERE id = ?", (game_id,))
    game = cur.fetchone()
    con.close()
    if game:
        executable_path = game[0]
        if executable_path.startswith("steam://"):
            try:
                subprocess.run(["start", executable_path], shell=True, check=True)
                print(f"Running Steam game with ID {game_id}.")
            except subprocess.CalledProcessError as e:
                print(f"Failed to run the Steam game: {e}")
        elif os.path.exists(executable_path):
            try:
                subprocess.run(executable_path, check=True)
                print(f"Running game with ID {game_id}.")
            except subprocess.CalledProcessError as e:
                print(f"Failed to run the game: {e}")
        else:
            print(f"Executable path '{executable_path}' does not exist.")
    else:
        print(f"No game found with ID {game_id}.")

def update_game_info(game_id, title=None, executable_path=None, cover_art_path=None):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    if title:
        cur.execute("UPDATE games SET title = ? WHERE id = ?", (title, game_id))
    if executable_path:
        cur.execute("UPDATE games SET executable_path = ? WHERE id = ?", (executable_path, game_id))
    if cover_art_path:
        cover_art_filename = os.path.basename(cover_art_path)
        cover_art_dest = os.path.join(COVER_ART_DIR, cover_art_filename)
        cache_cover_art_dest = os.path.join(CACHE_COVER_ART_DIR, cover_art_filename)
        os.makedirs(COVER_ART_DIR, exist_ok=True)
        os.makedirs(CACHE_COVER_ART_DIR, exist_ok=True)
        shutil.copy(cover_art_path, cover_art_dest)
        shutil.copy(cover_art_path, cache_cover_art_dest)
        cover_art_path = cover_art_filename
        cur.execute("UPDATE games SET cover_art_path = ? WHERE id = ?", (cover_art_path, game_id))
    con.commit()
    con.close()
    print(f"Game with ID {game_id} updated successfully.")

def get_games():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id, title, cover_art_path, background FROM games")
    games = cur.fetchall()
    con.close()
    return games

def list_games():
    games = get_games()
    for game in games:
        print(f"ID: {game[0]}, Title: {game[1]}")

def delete_game(game_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM games WHERE id = ?", (game_id,))
    con.commit()
    cur.execute("UPDATE games SET id = id - 1 WHERE id > ?", (game_id,))
    con.commit()
    con.close()
    print(f"Game with ID {game_id} deleted and IDs adjusted successfully.")

def scan_for_games(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".exe"):
                title = os.path.splitext(file)[0]
                executable_path = os.path.join(root, file)
                add_game_to_db(title, executable_path)
                print(f"Found and added game: {title}")

def scan_for_steam_games():
    steam_games = [
        {"title": "Steam Game 1", "url": "steam://rungameid/123456"},
        {"title": "Steam Game 2", "url": "steam://rungameid/654321"}
    ]
    for game in steam_games:
        add_game_to_db(game["title"], game["url"])
        print(f"Found and added Steam game: {game['title']}")

def display_menu(stdscr):
    curses.curs_set(0)
    stdscr.clear()
    stdscr.refresh()

    games = get_games()
    current_row = 0

    while True:
        stdscr.clear()
        for idx, game in enumerate(games):
            x = 0
            y = idx
            if idx == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, f"{game[1]}")
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, x, f"{game[1]}")
        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(games) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            run_game(games[current_row][0])
            break

def simple_menu():
    while True:
        print("1. List games")
        print("2. Add game")
        print("3. Run game")
        print("4. Update game")
        print("5. Delete game")
        print("6. Scan for games")
        print("7. Scan for Steam games")
        print("8. Exit")
        choice = input("Select an option: ")

        if choice == '1':
            list_games()
        elif choice == '2':
            title = input("Enter game title: ")
            executable_path = input("Enter executable path or Steam URL: ")
            cover_art_path = input("Enter cover art path (optional): ")
            add_game_to_db(title, executable_path, cover_art_path)
        elif choice == '3':
            list_games()
            game_id = int(input("Enter game ID to run: "))
            run_game(game_id)
        elif choice == '4':
            list_games()
            game_id = int(input("Enter game ID to update: "))
            title = input("Enter new title (leave blank to keep current): ")
            executable_path = input("Enter new executable path or Steam URL (leave blank to keep current): ")
            cover_art_path = input("Enter new cover art path (leave blank to keep current): ")
            update_game_info(game_id, title or None, executable_path or None, cover_art_path or None)
        elif choice == '5':
            list_games()
            game_id = int(input("Enter game ID to delete: "))
            delete_game(game_id)
        elif choice == '6':
            directory = input("Enter directory to scan for games: ")
            scan_for_games(directory)
        elif choice == '7':
            scan_for_steam_games()
        elif choice == '8':
            break
        else:
            print("Invalid choice. Please try again.")

def main():
    init_db()
    scan_for_games(config.get("scan_directory", "."))
    scan_for_steam_games()
    if CURSES_AVAILABLE:
        curses.wrapper(display_menu)
    else:
        simple_menu()

# Example usage
if __name__ == "__main__":
    main()