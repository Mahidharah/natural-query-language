import sqlite3
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from PIL import Image, ImageTk
from openai import OpenAI
import apikey

# Globals
db_name = "/mnt/c/Users/admin/Downloads/sakila_master.db"
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

def execute_query(er_diagram):
    """Execute the SQL query entered by the user and display the results in tabular format."""
    NLP_query = query_entry.get("1.0", tk.END).strip()
    selected_tables = er_diagram.get_selected_tables()
    print(f"Selected tables: {selected_tables}")
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
    schema = extract_schema_for_prompt('src/sqlite-sakila-schema.txt')

    # Format the schema for better readability
    #formatted_schema = format_schema(schema)
    
    system_message = (f"Generate only the SQL query based on the database schema: {schema} " +
                      "Do not provide any explanation, just the SQL code. " +
                      "Do not add any markdown syntax. " +
                      "Only provide the SQL code. If the user requests something that you determine to be outside the defined schema, " +
                      "try to find the closest match if not, provide an empty output.")
    
    print("\n--- Debug: Input to Language Model ---")
    print(f"System Message:\n{system_message}")
    print(f"\nUser Query:\n{user_query}")
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_query}
        ],
        max_tokens=200
    )
    
    sql_query = response.choices[0].message.content.strip()
    
    print("\n--- Debug: Output from Language Model ---")
    print(f"Generated SQL query:\n{sql_query}")
    
    return sql_query

'''
def format_schema(schema):
    """Format the schema for better readability by the LLM."""
    formatted_lines = []
    for line in schema.split('\n'):
        if line.strip().startswith('CREATE TABLE'):
            formatted_lines.append('\n' + line)
        elif line.strip().startswith(');'):
            formatted_lines.append(line + '\n')
        else:
            formatted_lines.append('  ' + line)
    return '\n'.join(formatted_lines)
'''

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

class ImageERDiagramWidget(tk.Frame):
    def __init__(self, master, image_path, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.image_path = image_path
        self.selected_tables = set()
        self.create_widget()

    def create_widget(self):
        # Load and display the image
        self.image = Image.open(self.image_path)
        self.photo = ImageTk.PhotoImage(self.image)
        self.canvas = tk.Canvas(self, width=self.image.width, height=self.image.height)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        # Define clickable areas for each table
        first_row_x_coords = (43, 209)
        second_row_x_coords = (312, 478)
        third_row_x_coords = (592, 758)
        self.table_areas = {
            'category': (first_row_x_coords[0], 110, first_row_x_coords[1], 220),
            'film_category': (first_row_x_coords[0], 270, first_row_x_coords[1], 376),
            'film': (first_row_x_coords[0], 414, first_row_x_coords[1], 701),
            'language': (first_row_x_coords[0], 773, first_row_x_coords[1], 880),
            'film_actor': (first_row_x_coords[0], 920, first_row_x_coords[1], 1026),
            'inventory': (second_row_x_coords[0], 110, second_row_x_coords[1], 231),
            'rental': (second_row_x_coords[0], 269, second_row_x_coords[1], 432),
            'payment': (second_row_x_coords[0], 491, second_row_x_coords[1], 635),
            'staff': (second_row_x_coords[0], 670, second_row_x_coords[1], 902),
            'actor': (second_row_x_coords[0], 928, second_row_x_coords[1], 1038),
            'customer': (third_row_x_coords[0], 110, third_row_x_coords[1], 332),
            'address': (third_row_x_coords[0], 391, third_row_x_coords[1], 579),
            'city': (third_row_x_coords[0], 638, third_row_x_coords[1], 758),
            'country': (third_row_x_coords[0], 807, third_row_x_coords[1], 902),
            'store': (third_row_x_coords[0], 928, third_row_x_coords[1], 1038)
        }

        # Create clickable rectangles for each table
        self.table_rectangles = {}
        for table, coords in self.table_areas.items():
            rect = self.canvas.create_rectangle(coords, outline='', fill='', tags=table)
            self.table_rectangles[table] = rect
            self.canvas.tag_bind(rect, '<Button-1>', lambda event, t=table: self.toggle_table_selection(t))

    def toggle_table_selection(self, table):
        if table in self.selected_tables:
            self.selected_tables.remove(table)
            self.canvas.itemconfig(self.table_rectangles[table], fill='')
        else:
            self.selected_tables.add(table)
            self.canvas.itemconfig(self.table_rectangles[table], fill='yellow', stipple='gray50')
        #print(f"Selected tables: {self.selected_tables}")  # For debugging

    def get_selected_tables(self):
        return list(self.selected_tables)

# Connect to the database
conn = connect_to_db(db_name)  # Replace with your actual database file

root = tk.Tk()
root.title("SQLite Query Executor with ER Diagram")

# Create a frame for the ER diagram
er_frame = tk.Frame(root)
er_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create the Image-based ER diagram widget
# Replace 'path_to_your_image.png' with the actual path to your ER diagram image
er_diagram = ImageERDiagramWidget(er_frame, image_path='/mnt/c/Users/admin/Pictures/SQL_ER_Diagram.png')
er_diagram.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create scrollbars for the ER diagram
h_scrollbar = tk.Scrollbar(er_frame, orient=tk.HORIZONTAL, command=er_diagram.canvas.xview)
h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
v_scrollbar = tk.Scrollbar(er_frame, orient=tk.VERTICAL, command=er_diagram.canvas.yview)
v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

er_diagram.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
er_diagram.canvas.configure(scrollregion=er_diagram.canvas.bbox(tk.ALL))

# Create a frame for the query input and results
query_frame = tk.Frame(root)
query_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Add your existing widgets to the query frame
query_label = tk.Label(query_frame, text="Enter your SQL query:")
query_label.pack()

query_entry = tk.Text(query_frame, height=5, width=60)
query_entry.pack()

execute_button = tk.Button(query_frame, text="Execute", command=lambda: execute_query(er_diagram))
execute_button.pack()

result_tree = ttk.Treeview(query_frame)
result_tree.pack(fill="both", expand=True)

result_display = scrolledtext.ScrolledText(query_frame, height=5, width=80)
result_display.pack()

exit_button = tk.Button(query_frame, text="Exit", command=root.quit)
exit_button.pack()

# Start the Tkinter event loop
root.mainloop()

