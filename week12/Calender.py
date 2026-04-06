import tkinter as tk
from tkinter import ttk
import calendar
from datetime import datetime

class CalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter Calendar")
        self.root.geometry("420x420")

        # Current date
        now = datetime.now()
        self.year = now.year
        self.month = now.month
        self.today = now.day

        # ===== Top Controls =====
        control_frame = tk.Frame(root)
        control_frame.pack(pady=10)

        tk.Button(control_frame, text="<", width=3, command=self.prev_month).grid(row=0, column=0)

        # Month dropdown
        self.month_var = tk.StringVar()
        self.month_combo = ttk.Combobox(
            control_frame,
            textvariable=self.month_var,
            values=list(calendar.month_name)[1:],
            state="readonly",
            width=10
        )
        self.month_combo.grid(row=0, column=1, padx=5)
        self.month_combo.bind("<<ComboboxSelected>>", self.update_from_dropdown)

        # Year dropdown
        self.year_var = tk.IntVar()
        self.year_combo = ttk.Combobox(
            control_frame,
            textvariable=self.year_var,
            values=list(range(1900, 2101)),
            state="readonly",
            width=6
        )
        self.year_combo.grid(row=0, column=2, padx=5)
        self.year_combo.bind("<<ComboboxSelected>>", self.update_from_dropdown)

        tk.Button(control_frame, text=">", width=3, command=self.next_month).grid(row=0, column=3)

        # ===== Calendar Frame =====
        self.cal_frame = tk.Frame(root)
        self.cal_frame.pack()

        self.update_dropdowns()
        self.draw_calendar()

    def update_dropdowns(self):
        self.month_var.set(calendar.month_name[self.month])
        self.year_var.set(self.year)

    def draw_calendar(self):
        for widget in self.cal_frame.winfo_children():
            widget.destroy()

        # Days header
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            tk.Label(self.cal_frame, text=day, font=("Arial", 10, "bold"),
                     width=5).grid(row=0, column=i)

        month_data = calendar.monthcalendar(self.year, self.month)

        for r, week in enumerate(month_data, start=1):
            for c, day in enumerate(week):
                if day == 0:
                    tk.Label(self.cal_frame, text="", width=5, height=2).grid(row=r, column=c)
                else:
                    bg = "lightblue" if (
                        day == self.today and
                        self.month == datetime.now().month and
                        self.year == datetime.now().year
                    ) else "white"

                    tk.Label(
                        self.cal_frame,
                        text=str(day),
                        width=5,
                        height=2,
                        borderwidth=1,
                        relief="solid",
                        bg=bg
                    ).grid(row=r, column=c, padx=1, pady=1)

    def prev_month(self):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self.update_dropdowns()
        self.draw_calendar()

    def next_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self.update_dropdowns()
        self.draw_calendar()

    def update_from_dropdown(self, event):
        self.month = list(calendar.month_name).index(self.month_var.get())
        self.year = self.year_var.get()
        self.draw_calendar()


if __name__ == "__main__":
    root = tk.Tk()
    app = CalendarApp(root)
    root.mainloop()