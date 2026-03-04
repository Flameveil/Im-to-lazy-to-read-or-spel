import sqlite3


def manage_tasks():
    # 1. Connect to Database (creates the file if it doesn't exist)
    # Use ':memory:' instead of a filename to run it entirely in RAM
    connection = sqlite3.connect('workflow.db')
    cursor = connection.cursor()

    # 2. Create a Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            priority INTEGER DEFAULT 1,
            status TEXT CHECK(status IN ('Pending', 'Completed')) DEFAULT 'Pending'
        )
    ''')

    # 3. Create (Insert Data)
    # We use '?' placeholders to prevent SQL Injection attacks
    new_tasks = [
        ('Fix login bug', 3),
        ('Update documentation', 1),
        ('Submit expense report', 2)
    ]
    cursor.executemany('INSERT INTO tasks (title, priority) VALUES (?, ?)', new_tasks)

    # 4. Update (Change a status)
    cursor.execute('UPDATE tasks SET status = ? WHERE title = ?', ('Completed', 'Fix login bug'))

    # 5. Read (Query Data)
    print("--- Current Task List ---")
    cursor.execute('SELECT * FROM tasks ORDER BY priority DESC')
    for row in cursor.fetchall():
        print(f"[{row[3]}] ID: {row[0]} | Task: {row[1]} | Priority: {row[2]}")

    # 6. Delete (Remove a specific record)
    cursor.execute('DELETE FROM tasks WHERE priority < ?', (2,))

    # Commit changes and close the connection
    connection.commit()
    connection.close()
    print("\nChanges saved and connection closed.")


if __name__ == "__main__":
    manage_tasks()