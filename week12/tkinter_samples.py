# selected examples taken from https://www.geeksforgeeks.org/python/python-gui-tkinter/

# mainloop
import tkinter as tk

root = tk.Tk()
# Widgets are added here

root.mainloop()

# label
import tkinter as tk

root = tk.Tk()
label = tk.Label(root, text="GeeksForGeeks.org!")
label.pack()

root.mainloop()

# button
import tkinter as tk

root = tk.Tk()
root.title("Counting Seconds")

button = tk.Button(root, text="Stop", width=25, command=root.destroy)
button.pack()

root.mainloop()

# entry
import tkinter as tk

root = tk.Tk()

tk.Label(root, text="First Name").grid(row=0, column=0)
tk.Label(root, text="Last Name").grid(row=1, column=0)

entry1 = tk.Entry(root)
entry2 = tk.Entry(root)

entry1.grid(row=0, column=1)
entry2.grid(row=1, column=1)

root.mainloop()

# checkbutton
import tkinter as tk

root = tk.Tk()

var1 = tk.IntVar()
var2 = tk.IntVar()

tk.Checkbutton(root, text="Male", variable=var1).grid(row=0, sticky=tk.W)
tk.Checkbutton(root, text="Female", variable=var2).grid(row=1, sticky=tk.W)

root.mainloop()

# radiobutton
import tkinter as tk

root = tk.Tk()
v = tk.IntVar()

tk.Radiobutton(root, text="A", variable=v, value=1).pack(anchor=tk.W)
tk.Radiobutton(root, text="B", variable=v, value=2).pack(anchor=tk.W)
root.mainloop()

# listbox
import tkinter as tk

root = tk.Tk()

lb = tk.Listbox(root)
lb.insert(1, "Python")
lb.insert(2, "Java")
lb.insert(3, "C++")
lb.insert(4, "Any other")

lb.pack()
root.mainloop()

# scrollbar
import tkinter as tk

root = tk.Tk()

scrollbar = tk.Scrollbar(root)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

mylist = tk.Listbox(root, yscrollcommand=scrollbar.set)

for line in range(100):
    mylist.insert(tk.END, "This is line number " + str(line))

mylist.pack(side=tk.LEFT, fill=tk.BOTH)
scrollbar.config(command=mylist.yview)

root.mainloop()

# menu
import tkinter as tk

root = tk.Tk()

menu = tk.Menu(root)
root.config(menu=menu)

filemenu = tk.Menu(menu)
menu.add_cascade(label="File", menu=filemenu)
filemenu.add_command(label="New")
filemenu.add_command(label="Open...")
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)

helpmenu = tk.Menu(menu)
menu.add_cascade(label="Help", menu=helpmenu)
helpmenu.add_command(label="About")

root.mainloop()

# combobox
import tkinter as tk
from tkinter import ttk

def select(event):
    selected_item = combo_box.get()
    label.config(text="Selected Item: " + selected_item)

root = tk.Tk()
root.title("Combobox Example")

label = tk.Label(root, text="Selected Item:")
label.pack(pady=10)

# Create a Combobox widget
combo_box = ttk.Combobox(
    root,
    values=["Option 1", "Option 2", "Option 3"],
    state="readonly"
)
combo_box.pack(pady=5)

combo_box.set("Option 1")

combo_box.bind("<<ComboboxSelected>>", select)
root.mainloop()

# scale
from tkinter import *

master = Tk()

# Vertical scale
vertical_scale = Scale(master, from_=0, to=42)
vertical_scale.pack()

# Horizontal scale
horizontal_scale = Scale(master, from_=0, to=200, orient=HORIZONTAL)
horizontal_scale.pack()

master.mainloop()

# message
from tkinter import *

main = Tk()

ourMessage = "This is our Message"
messageVar = Message(main, text=ourMessage)
messageVar.config(bg="lightgreen")
messageVar.pack()

main.mainloop()

# spinbox
from tkinter import *

root = Tk()
root.title("Spinbox Example")

spinbox = Spinbox(root, from_=0, to=10)
spinbox.pack()

root.mainloop()

# text
from tkinter import *

root = Tk()
root.title("Text Widget Example")

text_widget = Text(root, height=2, width=30)
text_widget.pack()

text_widget.insert(END, "GeeksforGeeks\nBEST WEBSITE\n")
root.mainloop()

# canvas
from tkinter import *

root = Tk()
root.title("Canvas Example")

canvas = Canvas(root, width=200, height=60)
canvas.pack()

y = 30
canvas.create_line(0, y, 200, y)

root.mainloop()

# colors
import tkinter as tk

root = tk.Tk()
root.title("Color Options in Tkinter")

# Create a button with active background and foreground colors
button = tk.Button(root, text="Click Me", activebackground="blue", activeforeground="white")
button.pack()

# Create a label with background and foreground colors
label = tk.Label(root, text="Hello, Tkinter!", bg="lightgray", fg="black")
label.pack()

# Create an Entry widget with selection colors
entry = tk.Entry(root, selectbackground="lightblue", selectforeground="black")
entry.pack()

root.mainloop()

# event handling
import tkinter as tk

def on_key_press(event):
    print(f"Key pressed: {event.keysym}")

def on_left_click(event):
    print(f"Left click at ({event.x}, {event.y})")

def on_right_click(event):
    print(f"Right click at ({event.x}, {event.y})")

def on_mouse_motion(event):
    print(f"Mouse moved to ({event.x}, {event.y})")

root = tk.Tk()
root.title("Advanced Event Handling Example")

root.bind("<KeyPress>", on_key_press)
root.bind("<Button-1>", on_left_click)
root.bind("<Button-3>", on_right_click)
root.bind("<Motion>", on_mouse_motion)

root.mainloop()
