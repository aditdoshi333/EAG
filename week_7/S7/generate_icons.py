from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size):
    # Create a new image with a white background
    image = Image.new('RGB', (size, size), 'white')
    draw = ImageDraw.Draw(image)
    
    # Draw a blue circle
    circle_color = '#4285f4'  # Google Blue
    draw.ellipse([2, 2, size-2, size-2], fill=circle_color)
    
    # Add text
    try:
        font_size = size // 2
        font = ImageFont.truetype("Arial", font_size)
    except:
        font = ImageFont.load_default()
    
    text = "W"
    text_color = 'white'
    
    # Calculate text position to center it
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    # Draw the text
    draw.text((x, y), text, fill=text_color, font=font)
    
    return image

def main():
    # Create chrome_extension directory if it doesn't exist
    if not os.path.exists('chrome_extension'):
        os.makedirs('chrome_extension')
    
    # Generate icons of different sizes
    sizes = [16, 48, 128]
    for size in sizes:
        icon = create_icon(size)
        icon.save(f'chrome_extension/icon{size}.png')

if __name__ == '__main__':
    main() 