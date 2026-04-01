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