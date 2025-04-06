# basic import 
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
import sys
import subprocess
import time
import json
import os
import tempfile
import base64
from PIL import Image
import io
import numpy as np
import pyautogui

# Helper function to make numpy types JSON serializable
def make_json_serializable(obj):
    if isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64,
                         np.uint8, np.uint16, np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, (np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    return obj

# instantiate an MCP server client
mcp = FastMCP("ScreenshotAutomator")

# Global variables to track state
paint_process = None
paint_window_title = "Simple Paint"
last_screenshot_path = None
detected_elements = {}
default_window_width = 800
default_window_height = 600
last_rectangle_coords = None  # Store the last drawn rectangle coordinates

@mcp.tool()
async def open_paint() -> dict:
    """Open the paint application with colored buttons"""
    global paint_process
    try:
        # Close existing paint process if running
        if paint_process:
            try:
                paint_process.terminate()
                time.sleep(0.5)
            except:
                pass
        
        # Start the custom paint application with colored buttons
        paint_process = subprocess.Popen(
            ["python", "mac_paint_colored.py"], 
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Give it more time to start and render fully
        time.sleep(3)
        
        # Force the paint window to the front using multiple methods
        await force_window_to_front()
        
        # Try to maximize the window using multiple methods
        maximize_result = await force_window_maximize()
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Paint application opened and maximized: {maximize_result}"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error opening paint: {str(e)}"
                )
            ]
        }

async def force_window_to_front():
    """Force the paint window to the front using multiple methods"""
    try:
        # Method 1: Use AppleScript to bring window to front
        front_script = '''
        tell application "System Events"
            set processList to every process whose name contains "Python"
            repeat with proc in processList
                set frontmost of proc to true
                set windowList to every window of proc
                repeat with win in windowList
                    set winName to name of win
                    if winName contains "Python" or winName contains "paint" or winName contains "Paint" then
                        set position of win to {0, 0}
                    end if
                end repeat
            end repeat
        end tell
        '''
        subprocess.run(['osascript', '-e', front_script], capture_output=True)
        time.sleep(0.5)
        
        # Method 2: Try to activate the Python process more directly
        activate_script = '''
        tell application "System Events"
            set myApp to first process whose name contains "Python"
            set frontmost of myApp to true
        end tell
        '''
        subprocess.run(['osascript', '-e', activate_script], capture_output=True)
        time.sleep(0.5)
        
    except Exception as e:
        print(f"Error bringing window to front: {str(e)}")

async def force_window_maximize():
    """Force the paint window to maximize using multiple methods"""
    try:
        # Method 1: Get screen dimensions and use them
        try:
            screen_info_script = '''
            tell application "Finder"
                set screenResolution to bounds of window of desktop
                return screenResolution
            end tell
            '''
            result = subprocess.run(['osascript', '-e', screen_info_script], capture_output=True, text=True)
            screen_info = result.stdout.strip()
            print(f"Screen info: {screen_info}")
            
            # Try to get screen dimensions from the result
            screen_width = 1200
            screen_height = 800
            try:
                if screen_info:
                    parts = screen_info.strip('{}').split(',')
                    if len(parts) == 4:
                        screen_width = int(parts[2].strip())
                        screen_height = int(parts[3].strip())
                        print(f"Detected screen dimensions: {screen_width}x{screen_height}")
            except Exception as e:
                print(f"Error parsing screen dimensions: {e}")
        except:
            print("Could not get screen dimensions, using defaults")
            screen_width = 1200
            screen_height = 800
        
        # Method 2: Try to maximize with AppleScript
        # Use a more aggressive approach for window size
        maximize_script = f'''
        tell application "System Events"
            set processList to every process whose name contains "Python"
            repeat with proc in processList
                set windowList to every window of proc
                repeat with win in windowList
                    set winName to name of win
                    if winName contains "Python" or winName contains "paint" or winName contains "Paint" then
                        set position of win to {{0, 0}}
                        set size of win to {{{screen_width}, {screen_height}}}
                        return "Window maximized to {screen_width}x{screen_height}"
                    end if
                end repeat
            end repeat
        end tell
        '''
        maximize_result = subprocess.run(['osascript', '-e', maximize_script], capture_output=True, text=True)
        maximize_output = maximize_result.stdout.strip()
        print(f"Maximize result: {maximize_output}")
        
        # Method 3: Try direct communication with paint app
        try:
            # First try maximize command
            maximize_command = {
                "action": "maximize_window"
            }
            paint_process.stdin.write(json.dumps(maximize_command) + "\n")
            paint_process.stdin.flush()
            time.sleep(0.5)
            
            # Then try specific size command with screen dimensions
            resize_command = {
                "action": "resize_window",
                "width": screen_width,
                "height": screen_height
            }
            paint_process.stdin.write(json.dumps(resize_command) + "\n")
            paint_process.stdin.flush()
            time.sleep(0.5)
            
            # Try direct AppleScript click on zoom button
            try:
                zoom_script = '''
                tell application "System Events"
                    set processList to every process whose name contains "Python"
                    repeat with proc in processList
                        set windowList to every window of proc
                        repeat with win in windowList
                            set winName to name of win
                            if winName contains "Python" or winName contains "paint" or winName contains "Paint" then
                                tell win
                                    click button 2
                                end tell
                                return "Clicked window zoom button"
                            end if
                        end repeat
                    end repeat
                end tell
                '''
                zoom_result = subprocess.run(['osascript', '-e', zoom_script], capture_output=True, text=True)
                zoom_output = zoom_result.stdout.strip()
                print(f"Zoom button click result: {zoom_output}")
            except Exception as e:
                print(f"Error clicking zoom button: {e}")
            
        except Exception as e:
            print(f"Error sending maximize command to paint: {str(e)}")
        
        return maximize_output or "Window maximization attempted"
    except Exception as e:
        print(f"Error maximizing window: {str(e)}")
        return f"Window maximization failed: {str(e)}"

@mcp.tool()
async def maximize_paint_window() -> dict:
    """Maximize the paint application window"""
    global paint_process
    try:
        if not paint_process:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Force the paint window to the front
        await force_window_to_front()
        
        # Force maximize the window
        maximize_result = await force_window_maximize()
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Paint window maximized: {maximize_result}"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error maximizing window: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def take_screenshot() -> dict:
    """Take a screenshot of the current screen"""
    global last_screenshot_path
    try:
        # Force the paint window to the front
        await force_window_to_front()
        
        # Create temp directory if it doesn't exist
        temp_dir = tempfile.gettempdir()
        last_screenshot_path = os.path.join(temp_dir, f"screenshot_{int(time.time())}.png")
        
        # Take screenshot using screencapture
        subprocess.run(["screencapture", "-x", last_screenshot_path], check=True)
        
        # Get the image dimensions
        img = Image.open(last_screenshot_path)
        width, height = img.size
        
        # Return info about the screenshot
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Screenshot taken: {last_screenshot_path}"
                ),
                TextContent(
                    type="text",
                    text=f"Screenshot dimensions: {width}x{height}"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error taking screenshot: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def detect_colored_buttons() -> dict:
    """Analyze the screenshot to detect buttons (colored or not)"""
    global last_screenshot_path, detected_elements
    try:
        if not last_screenshot_path or not os.path.exists(last_screenshot_path):
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="No screenshot available. Please take a screenshot first."
                    )
                ]
            }
        
        # Open the image
        img = Image.open(last_screenshot_path)
        img_array = np.array(img)
        
        # Convert to grayscale for non-colored button detection
        gray = np.dot(img_array[..., :3], [0.2989, 0.5870, 0.1140])
        
        # Look for the paint application UI elements
        
        # First, try to find colored buttons
        # Red has high R, low G and B values
        red_mask = (
            (img_array[:,:,0] > 180) &  # High red
            (img_array[:,:,1] < 120) &  # Low green
            (img_array[:,:,2] < 120)     # Low blue
        )
        red_pixels = np.where(red_mask)
        
        # Green has high G, low R and B values
        green_mask = (
            (img_array[:,:,0] < 120) &  # Low red
            (img_array[:,:,1] > 180) &  # High green
            (img_array[:,:,2] < 120)     # Low blue
        )
        green_pixels = np.where(green_mask)
        
        # If color detection didn't work, try to detect UI elements based on layout
        color_detection_success = len(red_pixels[0]) > 10 and len(green_pixels[0]) > 10
        
        if not color_detection_success:
            # Save a debug copy of the screenshot
            debug_path = os.path.join(tempfile.gettempdir(), "debug_screenshot.png")
            img.save(debug_path)
            
            # Find the canvas area (usually the large white/light area)
            # Simple light area detection
            light_area_mask = (
                (img_array[:,:,0] > 220) & 
                (img_array[:,:,1] > 220) & 
                (img_array[:,:,2] > 220)
            )
            light_pixels = np.where(light_area_mask)
            
            # Use the light area to infer the canvas position
            if len(light_pixels[0]) > 5000:  # Large enough light area
                # Convert coordinates to regular Python integers
                canvas_top = int(min(light_pixels[0]))
                canvas_left = int(min(light_pixels[1]))
                canvas_bottom = int(max(light_pixels[0]))
                canvas_right = int(max(light_pixels[1]))
                
                # Calculate canvas center
                canvas_center_x = int((canvas_left + canvas_right) // 2)
                canvas_center_y = int((canvas_top + canvas_bottom) // 2)
                
                # Look for UI elements at the top
                # Estimate button positions based on typical paint app layout
                top_bar_height = canvas_top - 10 if canvas_top > 10 else 30
                
                # Assuming toolbar is at the top with buttons
                rect_button_x = int(canvas_left + (canvas_right - canvas_left) * 0.2)
                text_button_x = int(canvas_left + (canvas_right - canvas_left) * 0.5)
                button_y = int(top_bar_height // 2)
                
                # Store detected elements with regular Python integers
                detected_elements = {
                    "rectangle_button": {"x": rect_button_x, "y": button_y},
                    "text_button": {"x": text_button_x, "y": button_y},
                    "canvas_center": {"x": canvas_center_x, "y": canvas_center_y}
                }
                
                return {
                    "content": [
                        TextContent(
                            type="text",
                            text=f"Detected elements using light area method: {json.dumps(detected_elements)}"
                        ),
                        TextContent(
                            type="text",
                            text=f"Debug screenshot saved to: {debug_path}"
                        )
                    ]
                }
            else:
                # If no large light area, use fixed positions based on screen size
                screen_width = img.width
                screen_height = img.height
                
                # Store reasonable defaults based on screen size
                detected_elements = {
                    "rectangle_button": {"x": int(screen_width * 0.2), "y": 30},
                    "text_button": {"x": int(screen_width * 0.5), "y": 30},
                    "canvas_center": {"x": int(screen_width // 2), "y": int(screen_height // 2)}
                }
                
                return {
                    "content": [
                        TextContent(
                            type="text",
                            text=f"Could not detect buttons. Using fallback positions based on screen size: {json.dumps(detected_elements)}"
                        )
                    ]
                }
        
        # Process color detection results if successful
        if len(red_pixels[0]) > 10:
            rect_y_center = int(np.mean(red_pixels[0]))
            rect_x_center = int(np.mean(red_pixels[1]))
            detected_elements["rectangle_button"] = {"x": rect_x_center, "y": rect_y_center}
        else:
            detected_elements["rectangle_button"] = {"x": 60, "y": 30}  # Fallback
            
        if len(green_pixels[0]) > 10:
            text_y_center = int(np.mean(green_pixels[0]))
            text_x_center = int(np.mean(green_pixels[1]))
            detected_elements["text_button"] = {"x": text_x_center, "y": text_y_center}
        else:
            detected_elements["text_button"] = {"x": 180, "y": 30}  # Fallback
        
        # Add canvas center (for drawing)
        canvas_center_x = int(img.width // 2)
        canvas_center_y = int((img.height // 2) + 50)  # Adjust for UI controls at top
        detected_elements["canvas_center"] = {"x": canvas_center_x, "y": canvas_center_y}
        
        # Make all detected coordinates JSON serializable
        detected_elements = make_json_serializable(detected_elements)
        
        # Return the detected elements
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Detected elements in screenshot: {json.dumps(detected_elements)}"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error detecting buttons: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def click_button(button_type: str) -> dict:
    """Click on a button (rectangle or text) using the detected coordinates"""
    global paint_process, detected_elements
    try:
        if not paint_process:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Force the paint window to the front
        await force_window_to_front()
        
        if not detected_elements or button_type not in detected_elements:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Button coordinates not detected. Please run detect_colored_buttons first."
                    )
                ]
            }
        
        # Get the button coordinates
        button_coords = detected_elements.get(button_type)
        if not button_coords:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"No {button_type} button detected in the screenshot."
                    )
                ]
            }
        
        # Convert coordinates to regular Python integers if needed
        x = int(button_coords["x"]) if isinstance(button_coords["x"], (np.integer, np.floating)) else button_coords["x"]
        y = int(button_coords["y"]) if isinstance(button_coords["y"], (np.integer, np.floating)) else button_coords["y"]
        
        # Send click command to paint app
        command = {
            "action": "click",
            "x": x,
            "y": y
        }
        
        paint_process.stdin.write(json.dumps(command) + "\n")
        paint_process.stdin.flush()
        
        # Wait for response
        response = None
        for _ in range(10):
            if paint_process.stdout.readable():
                line = paint_process.stdout.readline().strip()
                if line:
                    try:
                        response = json.loads(line)
                        break
                    except:
                        pass
            time.sleep(0.1)
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Clicked on {button_type} button at coordinates: ({x}, {y})"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error clicking button: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def draw_rectangle(width: int, height: int) -> dict:
    """Draw a rectangle with the specified width and height centered in the canvas"""
    global paint_process, detected_elements, last_rectangle_coords
    try:
        if not paint_process:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Force the paint window to the front
        await force_window_to_front()
        
        if not detected_elements or "canvas_center" not in detected_elements:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Canvas center not detected. Please run detect_colored_buttons first."
                    )
                ]
            }
        
        # Get canvas center and convert to regular Python integers if needed
        center = detected_elements["canvas_center"]
        center_x = int(center["x"]) if isinstance(center["x"], (np.integer, np.floating)) else center["x"]
        center_y = int(center["y"]) if isinstance(center["y"], (np.integer, np.floating)) else center["y"]
        
        # Calculate rectangle coordinates
        x1 = int(center_x - width // 2)
        y1 = int(center_y - height // 2)
        x2 = int(center_x + width // 2)
        y2 = int(center_y + height // 2)
        
        # Store the rectangle coordinates for centering text later
        last_rectangle_coords = {
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "center_x": (x1 + x2) // 2,
            "center_y": (y1 + y2) // 2
        }
        
        # Send rectangle command to paint
        command = {
            "action": "rectangle",
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2
        }
        
        paint_process.stdin.write(json.dumps(command) + "\n")
        paint_process.stdin.flush()
        
        # Wait for response
        response = None
        for _ in range(10):
            if paint_process.stdout.readable():
                line = paint_process.stdout.readline().strip()
                if line:
                    try:
                        response = json.loads(line)
                        break
                    except:
                        pass
            time.sleep(0.1)
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error drawing rectangle: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def add_text(text: str) -> dict:
    """Add text in the center of the most recently drawn rectangle"""
    global paint_process, detected_elements, last_rectangle_coords
    try:
        if not paint_process:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Force the paint window to the front
        await force_window_to_front()
        
        # Check if we have the rectangle coordinates for centering
        if last_rectangle_coords:
            center_x = last_rectangle_coords["center_x"]
            center_y = last_rectangle_coords["center_y"]
        elif not detected_elements or "canvas_center" not in detected_elements:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="No rectangle has been drawn and canvas center not detected. Please run detect_colored_buttons first."
                    )
                ]
            }
        else:
            # Fall back to canvas center
            center = detected_elements["canvas_center"]
            center_x = int(center["x"]) if isinstance(center["x"], (np.integer, np.floating)) else center["x"]
            center_y = int(center["y"]) if isinstance(center["y"], (np.integer, np.floating)) else center["y"]
        
        # Send text command to paint
        command = {
            "action": "text",
            "x": center_x,
            "y": center_y,
            "text": text
        }
        
        print(f"Sending text command: {json.dumps(command)}")
        paint_process.stdin.write(json.dumps(command) + "\n")
        paint_process.stdin.flush()
        
        # Wait for response
        response = None
        for _ in range(10):
            if paint_process.stdout.readable():
                line = paint_process.stdout.readline().strip()
                if line:
                    try:
                        response = json.loads(line)
                        break
                    except:
                        pass
            time.sleep(0.1)
        
        position_info = f"at rectangle center ({center_x}, {center_y})" if last_rectangle_coords else "at canvas center"
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Text '{text}' added {position_info}"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error adding text: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def resize_paint_window(width: int = 800, height: int = 600) -> dict:
    """Resize the paint application window to the specified dimensions"""
    global paint_process
    try:
        if not paint_process:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Force the paint window to the front
        await force_window_to_front()
        
        # Try to resize the window using applescript
        try:
            # Resize the window
            resize_script = f'''
            tell application "System Events"
                set processList to every process whose name contains "Python"
                repeat with proc in processList
                    set windowList to every window of proc
                    repeat with win in windowList
                        set winName to name of win
                        if winName contains "Python" or winName contains "paint" or winName contains "Paint" then
                            set size of win to {{{width}, {height}}}
                            return "Resized window to {width}x{height}"
                        end if
                    end repeat
                end repeat
            end tell
            '''
            
            resize_result = subprocess.run(['osascript', '-e', resize_script], capture_output=True, text=True)
            resize_output = resize_result.stdout.strip()
            
            # Also send resize command directly to the paint app
            resize_command = {
                "action": "resize_window",
                "width": width,
                "height": height
            }
            
            paint_process.stdin.write(json.dumps(resize_command) + "\n")
            paint_process.stdin.flush()
            time.sleep(0.5)
            
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"Paint window resized to {width}x{height}"
                    ),
                    TextContent(
                        type="text",
                        text=f"AppleScript result: {resize_output}"
                    )
                ]
            }
            
        except Exception as e:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"Error resizing window: {str(e)}"
                    )
                ]
            }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error resizing window: {str(e)}"
                )
            ]
        }

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution 