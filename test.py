import tkinter as tk

# 1. Create the main window
window = tk.Tk()
window.title("Dear Mara")
window.geometry("900x650")
window.configure(bg="#FDF6EC")  # Warm cream background

# 2. Add a label
title = tk.Label(
    window,
    text="Dear Mara",
    font=("Georgia", 36, "bold"),
    bg="#FDF6EC",
    fg="#C16B47"  # Terracotta
)
title.pack(pady=100)  # pady = vertical spacing

# 3. Add a subtitle
subtitle = tk.Label(
    window,
    text="A letter is waiting for you.",
    font=("Georgia", 14, "italic"),
    bg="#FDF6EC",
    fg="#8B6F4E"
)
subtitle.pack()

# 4. Add a button
def on_begin():
    subtitle.config(text="Welcome to Wren.")  # Button changes the text

begin_btn = tk.Button(
    window,
    text="Begin",
    font=("Georgia", 13),
    bg="#C9A84C",
    fg="white",
    padx=30,
    pady=10,
    relief="flat",
    cursor="hand2",
    command=on_begin  # What happens on click
)
begin_btn.pack(pady=40)

# 5. Start the event loop — this keeps the window open
window.mainloop()