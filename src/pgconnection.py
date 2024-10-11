import sqlite3
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from openai import OpenAI
import apikey

# Globals
db_name = "/mnt/c/Users/admin/Downloads/chinook/chinook.db"
client = OpenAI(api_key=apikey.api_key)


def connect_to_db(db_name):
    """Connect to the SQLite database."""
    try:
        conn = sqlite3.connect(db_name)
        print(f"Connected to {db_name} successfully.")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def execute_query():
    """Execute the SQL query entered by the user and display the results in tabular format."""
    NLP_query = query_entry.get("1.0", tk.END).strip()
    SQL_query = get_sql_query(NLP_query)
    try:
        cursor = conn.cursor()
        cursor.execute(SQL_query)
        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]  # Get column names
        
        # Clear the treeview before showing new results
        for item in result_tree.get_children():
            result_tree.delete(item)

        # Set the columns and headers in the treeview
        result_tree["columns"] = columns
        result_tree["show"] = "headings"  # Only show the headings, no default column
        for col in columns:
            result_tree.heading(col, text=col)
            result_tree.column(col, width=150)  # Adjust the width of each column

        # Insert the results row by row
        for row in results:
            result_tree.insert("", "end", values=row)

    except sqlite3.Error as e:
        result_display.delete("1.0", tk.END)
        result_display.insert(tk.END, f"Error executing query: {e}\n")

def get_sql_query(user_query):
    """Get the SQL query from the OpenAI API based on the user's natural language query."""
    schema = extract_schema_for_prompt('src/schema.txt')
    response = client.chat.completions.create(model="gpt-4o",
        messages=[
            {"role": "system", "content": "Generate only the SQL query based on the database schema: {schema} " +
                "Do not provide any explanation, just the SQL code. " +
                "Ensure all names used in SQL query exists and is stated in the schma and the schema only" +
                "Do not add any markdown syntax. " +
                "Only provide the SQL code. If the user requests something that you determine to be outside the defined schema, " +
                "try to find the closest match if not, provide an empty output."},
            {"role": "user", "content": user_query}
        ],
        max_tokens=200)
    sql_query = response.choices[0].message.content.strip()
    print(f"Generated SQL query: {sql_query}")
    return sql_query

def extract_schema_for_prompt(file_path):
    """Extract schema from a txt file and process it into a plain text format for API calls."""
    schema_lines = []
    
    try:
        with open(file_path, 'r') as file:
            print(f"Schema found found: {file_path}")
            for line in file:
                clean_line = line.strip()  # Remove unnecessary whitespace
                if clean_line:  # Skip empty lines
                    schema_lines.append(clean_line)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return ""
    
    # Join the lines into a single string, separated by spaces
    schema_as_string = " ".join(schema_lines)
    
    return schema_as_string

def on_exit():
    """Close the database connection and exit the program."""
    if conn:
        conn.close()
    root.destroy()

# Create the main application window
root = tk.Tk()
root.title("SQLite Query Executor")

# Connect to the database
conn = connect_to_db(db_name)  # Replace with your actual database file

# Create a label and text box for entering SQL queries
query_label = tk.Label(root, text="Enter your SQL query:")
query_label.pack()

query_entry = tk.Text(root, height=5, width=60)
query_entry.pack()

# Create a button to execute the query
execute_button = tk.Button(root, text="Execute", command=execute_query)
execute_button.pack()

# Create a Treeview widget to display the results in a tabular format
result_tree = ttk.Treeview(root)
result_tree.pack(fill="both", expand=True)

# Create a scrollable text area to display any errors
result_display = scrolledtext.ScrolledText(root, height=5, width=80)
result_display.pack()

# Create an exit button
exit_button = tk.Button(root, text="Exit", command=on_exit)
exit_button.pack()

# Start the Tkinter event loop
root.mainloop()

