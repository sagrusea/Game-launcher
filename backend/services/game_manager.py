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
CACHE_COVER_ART_DIR = os.path.join(os.getenv("APPDATA"), "sagrusea", "game-launcher", "cache", "cover_art")

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

def delete_games(game_ids):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    for game_id in game_ids:
        cur.execute("DELETE FROM games WHERE id = ?", (game_id,))
    con.commit()
    cur.execute("UPDATE games SET id = id - 1 WHERE id > ?", (min(game_ids),))
    con.commit()
    con.close()
    print(f"Games with IDs {game_ids} deleted and IDs adjusted successfully.")

def scan_for_games(directory):
    found_games = False
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".exe"):
                title = os.path.splitext(file)[0]
                executable_path = os.path.join(root, file)
                add_game_to_db(title, executable_path)
                print(f"Found and added game: {title}")
                found_games = True
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            for sub_root, sub_dirs, sub_files in os.walk(dir_path):
                for sub_file in sub_files:
                    if sub_file.endswith(".exe"):
                        title = os.path.splitext(sub_file)[0]
                        executable_path = os.path.join(sub_root, sub_file)
                        add_game_to_db(title, executable_path)
                        print(f"Found and added game: {title}")
                        found_games = True
    if not found_games:
        print(f"No games found in directory: {directory}")

def fetch_steam_games():
    steam_directory = config.get("steam_integration", {}).get("steam_path", "")
    # Implement logic to fetch Steam games from the specified directory
    return []

def fetch_epic_games():
    epic_directory = config.get("epic_integration", {}).get("epic_path", "")
    epic_games = []
    existing_games = {game[1] for game in get_games()}  # Use index 1 to get the title
    non_game_exes = ["UnityCrashHandler", "Uninstall"]

    for dir in os.listdir(epic_directory):
        dir_path = os.path.join(epic_directory, dir)
        if os.path.isdir(dir_path):
            for sub_file in os.listdir(dir_path):
                sub_file_path = os.path.join(dir_path, sub_file)
                if os.path.isfile(sub_file_path) and sub_file.endswith(".exe"):
                    title = os.path.splitext(sub_file)[0]
                    if title not in existing_games and not any(exe in title for exe in non_game_exes):
                        epic_games.append({"title": title, "url": sub_file_path})
    return epic_games

def scan_for_steam_games():
    steam_games = fetch_steam_games()
    steam_directory = config.get("steam_integration", {}).get("steam_path", "")
    if steam_games:
        for game in steam_games:
            add_game_to_db(game["title"], game["url"])
            print(f"Found and added Steam game: {game['title']}")
    else:
        print(f"No Steam games found in directory: {steam_directory}")

def scan_for_epic_games():
    epic_games = fetch_epic_games()
    epic_directory = config.get("epic_integration", {}).get("epic_path", "")
    if epic_games:
        for game in epic_games:
            add_game_to_db(game["title"], game["url"])
            print(f"Found and added Epic game: {game['title']}")
    else:
        print(f"No Epic games found in directory: {epic_directory}")

def edit_config(new_config):
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "w") as config_file:
        json.dump(new_config, config_file, indent=4)
    print("Configuration updated successfully.")

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
        print("\nGame Launcher Menu")
        print("1. Game Management")
        print("2. Run Game")
        print("3. Options")
        print("0. Exit")
        
        choice = input("Select an option: ").strip()

        if choice == '1':
            print("\nGame Management")
            print("1. List games")
            print("2. Add game")
            print("3. Update game")
            print("4. Delete game")
            print("5. Scan for games")
            print("0. Back")
            
            sub_choice = input("Select an option: ").strip()
            
            if sub_choice == '1':
                list_games()
            elif sub_choice == '2':
                title = input("Enter game title: ").strip()
                executable_path = input("Enter executable path or Steam URL: ").strip()
                cover_art_path = input("Enter cover art path (optional): ").strip()
                add_game_to_db(title, executable_path, cover_art_path)
            elif sub_choice == '3':
                list_games()
                game_id = int(input("Enter game ID to update: ").strip())
                title = input("Enter new title (leave blank to keep current): ").strip()
                executable_path = input("Enter new executable path or Steam URL (leave blank to keep current): ").strip()
                cover_art_path = input("Enter new cover art path (leave blank to keep current): ").strip()
                update_game_info(game_id, title or None, executable_path or None, cover_art_path or None)
            elif sub_choice == '4':
                list_games()
                game_ids = input("Enter game IDs to delete (comma-separated): ").strip()
                game_ids = [int(id.strip()) for id in game_ids.split(",")]
                delete_games(game_ids)
            elif sub_choice == '5':
                print("\nScan for Games")
                print("1. Scan for games")
                print("2. Scan for Steam games")
                print("3. Scan for Epic Games")
                print("0. Back")
                
                scan_choice = input("Select an option: ").strip()
                
                if scan_choice == '1':
                    directory = input("Enter directory to scan for games: ").strip()
                    scan_for_games(directory)
                elif scan_choice == '2':
                    scan_for_steam_games()
                elif scan_choice == '3':
                    scan_for_epic_games()
                elif scan_choice == '0':
                    continue
                else:
                    print("Invalid choice. Please try again.")
            elif sub_choice == '0':
                continue
            else:
                print("Invalid choice. Please try again.")
        
        elif choice == '2':
            list_games()
            game_id = int(input("Enter game ID to run: ").strip())
            run_game(game_id)
        
        elif choice == '3':
            print("\nOptions")
            print("1. Edit DB path")
            print("2. Edit Steam games path")
            print("3. Edit Epic Games path")
            print("4. Edit scan directory")
            print("0. Back")
            
            config_choice = input("Select an option: ").strip()
            
            if config_choice == '1':
                new_db_path = input("Enter new DB path: ").strip()
                config["db_path"] = new_db_path
                edit_config(config)
            elif config_choice == '2':
                new_steam_path = input("Enter new Steam games path: ").strip()
                config["steam_integration"]["steam_path"] = new_steam_path
                edit_config(config)
            elif config_choice == '3':
                new_epic_path = input("Enter new Epic Games path: ").strip()
                config["epic_integration"]["epic_path"] = new_epic_path
                edit_config(config)
            elif config_choice == '4':
                new_scan_directory = input("Enter new scan directory: ").strip()
                config["scan_directory"] = new_scan_directory
                edit_config(config)
            elif config_choice == '0':
                continue
            else:
                print("Invalid choice. Please try again.")
        
        elif choice == '0':
            break
        
        else:
            print("Invalid choice. Please try again.")

def main():
    # Ensure the required directory exists
    user_home = os.path.expanduser("~")
    required_directory = os.path.join(user_home, "AppData", "Roaming", "sagrusea", "game-launcher")
    if not os.path.exists(required_directory):
        os.makedirs(required_directory)
        print(f"Created directory: {required_directory}")

    init_db()
    if CURSES_AVAILABLE:
        curses.wrapper(display_menu)
    else:
        simple_menu()

    # Wait for user input before closing
    input("Press Enter to exit...")

# Example usage
if __name__ == "__main__":
    main()