import tkinter as tk
from tkinter import Canvas, Button, Frame, SUNKEN, Label, font
import sys
import json
import os
import time
import threading

class SimplePaint:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Paint")
        self.root.geometry("1200x800")
        
        # Set up canvas
        self.canvas_frame = Frame(root, bd=2, relief=SUNKEN)
        self.canvas_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        self.canvas = Canvas(self.canvas_frame, bg="white", width=1100, height=700)
        self.canvas.pack(expand=True, fill=tk.BOTH)
        
        # Set up controls with colored buttons
        self.controls_frame = Frame(root, height=50)
        self.controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create RED rectangle button
        self.rect_button = Button(
            self.controls_frame, 
            text="Rectangle", 
            command=self.set_rectangle_mode,
            bg="red",  # Red color for easier detection
            fg="white",
            width=10,
            height=2
        )
        self.rect_button.pack(side=tk.LEFT, padx=20, pady=5)
        
        # Create GREEN text button
        self.text_button = Button(
            self.controls_frame, 
            text="Text", 
            command=self.set_text_mode,
            bg="green",  # Green color for easier detection
            fg="white",
            width=10,
            height=2
        )
        self.text_button.pack(side=tk.LEFT, padx=20, pady=5)
        
        self.status_label = Label(self.controls_frame, text="Ready")
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # State variables
        self.mode = "none"  # Current drawing mode
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.text_input = None
        
        # Commands queue
        self.command_queue = []
        
        # Bind events
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Set up command processing
        self.root.after(100, self.check_commands)
    
    def set_rectangle_mode(self):
        """Set mode to rectangle drawing"""
        self.mode = "rectangle"
        self.status_label.config(text="Rectangle Mode")
    
    def set_text_mode(self):
        """Set mode to text input"""
        self.mode = "text"
        self.status_label.config(text="Text Mode")
    
    def on_mouse_down(self, event):
        """Handle mouse down event"""
        self.start_x = event.x
        self.start_y = event.y
        
        if self.mode == "rectangle":
            self.rect_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, self.start_x, self.start_y,
                outline="black", width=2
            )
        elif self.mode == "text":
            # Create text entry widget at click position
            self.text_input = tk.Entry(self.root)
            self.canvas.create_window(event.x, event.y, window=self.text_input)
            self.text_input.focus_set()
            self.text_input.bind("<Return>", self.on_text_enter)
    
    def on_mouse_drag(self, event):
        """Handle mouse drag event"""
        if self.mode == "rectangle" and self.rect_id:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)
    
    def on_mouse_up(self, event):
        """Handle mouse up event"""
        if self.mode == "rectangle" and self.rect_id:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)
    
    def on_text_enter(self, event):
        """Handle text entry submission"""
        text = self.text_input.get()
        x = self.start_x
        y = self.start_y
        self.canvas.create_text(x, y, text=text, anchor="nw", font=("Arial", 12))
        self.text_input.destroy()
        self.text_input = None
    
    def draw_rectangle(self, x1, y1, x2, y2):
        """Draw a rectangle with the specified coordinates"""
        self.status_label.config(text=f"Drawing rectangle: ({x1},{y1}) to ({x2},{y2})")
        rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline="black", width=3)
        self.root.update_idletasks()
        return True
    
    def add_text(self, x, y, text):
        """Add text at the specified coordinates"""
        self.status_label.config(text=f"Adding text: {text}")
        text_font = font.Font(family="Arial", size=16, weight="bold")
        text_id = self.canvas.create_text(x, y, text=text, anchor="center", font=text_font, fill="blue")
        self.root.update_idletasks()
        return True
    
    def click_at(self, x, y):
        """Simulate clicking at the specified coordinates"""
        self.status_label.config(text=f"Clicking at: ({x},{y})")
        
        # Check if we're clicking on a button
        if 5 <= x <= 105 and 5 <= y <= 45:  # Rectangle button area
            self.set_rectangle_mode()
            return True
        elif 125 <= x <= 225 and 5 <= y <= 45:  # Text button area
            self.set_text_mode()
            return True
        else:
            # Clicking on canvas
            self.on_mouse_down(tk.Event())
            self.start_x = x
            self.start_y = y
            return True
    
    def check_commands(self):
        """Check for incoming commands on stdin"""
        try:
            if sys.stdin.isatty() == False:
                try:
                    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        line = sys.stdin.readline().strip()
                        if line:
                            try:
                                cmd = json.loads(line)
                                self.command_queue.append(cmd)
                            except json.JSONDecodeError:
                                pass
                except:
                    pass
            
            if self.command_queue:
                cmd = self.command_queue.pop(0)
                action = cmd.get("action")
                
                if action == "rectangle":
                    x1 = cmd.get("x1", 100)
                    y1 = cmd.get("y1", 100)
                    x2 = cmd.get("x2", 300)
                    y2 = cmd.get("y2", 300)
                    result = self.draw_rectangle(x1, y1, x2, y2)
                    print(json.dumps({"status": "ok" if result else "error"}))
                    sys.stdout.flush()
                
                elif action == "text":
                    x = cmd.get("x", 200)
                    y = cmd.get("y", 200)
                    text = cmd.get("text", "")
                    result = self.add_text(x, y, text)
                    print(json.dumps({"status": "ok" if result else "error"}))
                    sys.stdout.flush()
                    
                elif action == "click":
                    x = cmd.get("x", 0)
                    y = cmd.get("y", 0)
                    result = self.click_at(x, y)
                    print(json.dumps({"status": "ok" if result else "error", "message": f"Clicked at ({x}, {y})"}))
                    sys.stdout.flush()
                
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}))
            sys.stdout.flush()
        
        # Schedule the next check
        self.root.after(100, self.check_commands)

def main():
    # Add select module for non-blocking stdin reading
    global select
    import select
    
    root = tk.Tk()
    app = SimplePaint(root)
    root.mainloop()

if __name__ == "__main__":
    main() 