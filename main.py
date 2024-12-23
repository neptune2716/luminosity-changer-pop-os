import os
import threading
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from pynput import keyboard
import pystray
from PIL import Image

overlay_window = None
overlay_hide_id = None

def show_overlay(value):
    global overlay_window, overlay_hide_id
    if not overlay_window or not overlay_window.winfo_exists():
        overlay_window = tk.Toplevel(root)
        overlay_window.overrideredirect(True)
        overlay_window.attributes("-topmost", True)
        overlay_window.attributes("-alpha", 0.8)
        overlay_window.geometry("200x50+800+400")  # Adjust position as needed

        overlay_window.progress = ttk.Progressbar(overlay_window, orient="horizontal", length=180, maximum=100)
        overlay_window.progress.pack(pady=5)
        overlay_window.lbl = ttk.Label(overlay_window)
        overlay_window.lbl.pack()

    overlay_window.progress["value"] = float(value)
    overlay_window.lbl.config(text=f"{int(float(value))}%")
    overlay_window.deiconify()

    if overlay_hide_id:
        overlay_window.after_cancel(overlay_hide_id)
    overlay_hide_id = overlay_window.after(2000, overlay_window.withdraw)

def set_brightness(value):
    """Apply brightness level via xrandr."""
    try:
        brightness = max(0, min(float(value), 100)) / 100
        if brightness < 0.2:
            # Increase gamma to offset the "whitening" effect
            os.system(f"xrandr --output DP-4 --brightness {brightness} --gamma 1.2:1.2:1.2")
        else:
            # Normal gamma
            os.system(f"xrandr --output DP-4 --brightness {brightness} --gamma 1:1:1")
        entry_var.set(f"{int(float(value))}%")
        show_overlay(value)
    except ValueError:
        pass

def on_entry_change(event=None):
    """Update brightness from entry value."""
    try:
        value = entry_var.get().strip('%')
        value = max(0, min(float(value), 100))
        slider.set(value)
        set_brightness(value)
    except ValueError:
        pass

def increase_brightness():
    """Increase brightness by 5% up to 100%."""
    try:
        value = float(entry_var.get().strip('%'))
        new_value = min(value + 2, 100)
        slider.set(new_value)
        set_brightness(new_value)
        entry_var.set(f"{int(new_value)}%")
    except ValueError:
        pass

def decrease_brightness():
    """Decrease brightness by 5% down to 2%."""
    try:
        value = float(entry_var.get().strip('%'))
        new_value = max(value - 2, 2)
        slider.set(new_value)
        set_brightness(new_value)
        entry_var.set(f"{int(new_value)}%")
    except ValueError:
        pass

current_modifiers = {'super': False}

def on_press(key):
    """Detect global shortcuts."""
    try:
        if key == keyboard.Key.f5 and current_modifiers.get('super', False):
            root.after(0, increase_brightness)
        elif key == keyboard.Key.f6 and current_modifiers.get('super', False):
            root.after(0, decrease_brightness)
    except AttributeError:
        pass

def on_key_press(key):
    if key in (keyboard.Key.cmd, keyboard.Key.alt_l, keyboard.Key.alt_gr):
        current_modifiers['super'] = True
    if key == keyboard.Key.f6 and current_modifiers.get('super', False):
        root.after(0, increase_brightness)
    elif key == keyboard.Key.f5 and current_modifiers.get('super', False):
        root.after(0, decrease_brightness)

def on_key_release(key):
    if key in (keyboard.Key.cmd, keyboard.Key.alt_l, keyboard.Key.alt_gr):
        current_modifiers['super'] = False

def listen_hotkeys():
    with keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as listener:
        listener.join()

def setup_tray_icon():
    """Configure system tray icon."""
    icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
    icon_image = Image.open(icon_path).convert("RGBA")

    def restore_window(_):
        root.deiconify()
        root.lift()

    def quit_app(_):
        icon.stop()
        root.quit()

    menu = (
        pystray.MenuItem("Ouvrir", restore_window),
        pystray.MenuItem("Quitter", quit_app)
    )

    icon = pystray.Icon("LuminosityControl", icon_image, "Contrôle Luminosité", menu)
    icon.run_detached()

root = ttk.Window(themename="darkly")
root.title("Réglage de la Luminosité")
root.geometry("400x200")

label = ttk.Label(root, text="Réglez la luminosité (%) :", font=("Helvetica", 14))
label.pack(pady=10)

entry_var = ttk.StringVar(value="70%")
slider = ttk.Scale(root, from_=2, to=100, orient="horizontal", command=set_brightness, length=300)
slider.set(70)
slider.pack(pady=10)

entry = ttk.Entry(root, textvariable=entry_var, font=("Helvetica", 12), justify="center")
entry.pack(pady=10)
entry.bind("<Return>", on_entry_change)

def hide_window():
    root.withdraw()
    setup_tray_icon()

root.protocol("WM_DELETE_WINDOW", hide_window)

listener_thread = threading.Thread(target=listen_hotkeys, daemon=True)
listener_thread.start()

def main():
    hide_window()
    root.mainloop()

if __name__ == "__main__":
    main()
