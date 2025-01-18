import sqlite3
import os
import subprocess

try:
    import curses
    CURSES_AVAILABLE = True
except ImportError:
    CURSES_AVAILABLE = False

DB_PATH = "backend/db/launcher.db"

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            executable_path TEXT NOT NULL,
            cover_art_path TEXT,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.commit()
    con.close()

def add_game_to_db(title, executable_path, cover_art_path=None):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("INSERT INTO games (title, executable_path, cover_art_path) VALUES (?, ?, ?)", 
                (title, executable_path, cover_art_path))
    con.commit()
    con.close()
    print(f"Game '{title}' added successfully.")

def run_game(game_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT executable_path FROM games WHERE id = ?", (game_id,))
    game = cur.fetchone()
    con.close()
    if game:
        executable_path = game[0]
        if os.path.exists(executable_path):
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
        cur.execute("UPDATE games SET cover_art_path = ? WHERE id = ?", (cover_art_path, game_id))
    con.commit()
    con.close()
    print(f"Game with ID {game_id} updated successfully.")

def get_games():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id, title FROM games")
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
    con.close()
    print(f"Game with ID {game_id} deleted successfully.")

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
        print("6. Exit")
        choice = input("Select an option: ")

        if choice == '1':
            list_games()
        elif choice == '2':
            title = input("Enter game title: ")
            executable_path = input("Enter executable path: ")
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
            executable_path = input("Enter new executable path (leave blank to keep current): ")
            cover_art_path = input("Enter new cover art path (leave blank to keep current): ")
            update_game_info(game_id, title or None, executable_path or None, cover_art_path or None)
        elif choice == '5':
            list_games()
            game_id = int(input("Enter game ID to delete: "))
            delete_game(game_id)
        elif choice == '6':
            break
        else:
            print("Invalid choice. Please try again.")

def main():
    if CURSES_AVAILABLE:
        curses.wrapper(display_menu)
    else:
        simple_menu()

# Example usage
if __name__ == "__main__":
    init_db()
    main()