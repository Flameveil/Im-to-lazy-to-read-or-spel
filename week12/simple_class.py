import tkinter as tk
from tkinter import messagebox

class MyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Class-Based UI")
        self.root.geometry("400x300")

        # Define variables
        self.user_input = tk.StringVar()

        # Build the UI
        self.create_widgets()

    def create_widgets(self):
        """Initializes and places all UI elements."""
        # Label
        self.label = tk.Label(self.root, text="Enter your name:", font=("Arial", 12))
        self.label.pack(pady=10)

        # Entry (Input field)
        self.entry = tk.Entry(self.root, textvariable=self.user_input)
        self.entry.pack(pady=5)

        # Button
        self.submit_btn = tk.Button(
            self.root, 
            text="Greet Me", 
            command=self.handle_click,
            bg="#4CAF50",
            fg="white"
        )
        self.submit_btn.pack(pady=20)

    def handle_click(self):
        """Logic for the button click."""
        name = self.user_input.get()
        if name.strip():
            messagebox.showinfo("Hello!", f"Welcome to the app, {name}!")
        else:
            messagebox.showwarning("Input Error", "Please enter a name first.")

if __name__ == "__main__":
    root = tk.Tk()
    app = MyApp(root)
    root.mainloop()