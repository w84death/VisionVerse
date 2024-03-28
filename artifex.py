import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageTk
import time
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI
from io import BytesIO
import requests

class DalleApp:
    def __init__(self, root, client):
        self.root = root
        self.client = client
        self.root.title("ArtiFex, a DALL-E Editor")
        self.root.configure(bg='black')
        self.root.bind("<Escape>", lambda e: root.destroy())
        # Input for prompts
        self.prompt_input = tk.Entry(root, width=50)
        self.prompt_input.pack()

        # Button to open file browser and select image
        self.open_file_btn = tk.Button(root, text="Open Image", command=self.open_image)
        self.open_file_btn.pack()


        # Canvas for drawing mask
        self.canvas = tk.Canvas(root, width=512, height=512, bg="white")
        self.canvas.pack()
        self.canvas.bind("<B1-Motion>", self.draw_mask)


        # Image for drawing
        self.initialize_mask()

        self.clear_mask_btn = tk.Button(root, text="Clear Mask", command=self.clear_mask)
        self.clear_mask_btn.pack()

        # Button to send data to the API
        self.send_btn = tk.Button(root, text="Send to DALL-E", command=self.send_to_dalle)
        self.send_btn.pack()

        # Placeholder for user-selected image path
        self.user_image_path = None
        self.result_image = None
        self.canvas_image_id = None

    def initialize_mask(self):

        self.mask_image = Image.new("RGBA", (512, 512), (255, 255, 255, 255))
        self.draw = ImageDraw.Draw(self.mask_image)

    def save_image(self, image):
        # Format the current date and time as a string
        datestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"image_{datestamp}.jpg"

        # Save the PIL.Image object to a file
        image.save(filename)
        print(f"Image saved as {filename}")

    def open_image(self):
        # User selects an image file
        self.user_image_path = filedialog.askopenfilename()
        if not self.user_image_path:  # Check if a file was selected
            return

        # Load the image with PIL
        user_image = Image.open(self.user_image_path)
        # Resize the image to fit the canvas (1024x768 in this case)
        user_image = user_image.resize((512, 512), Image.Resampling.LANCZOS)

        # Convert PIL image to PhotoImage, which is compatible with Tkinter
        self.user_photo_image = ImageTk.PhotoImage(user_image)

        # If there's already an image on the canvas, remove it
        if self.canvas_image_id is not None:
            self.canvas.delete(self.canvas_image_id)

        # Display the image on the canvas
        self.canvas_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.user_photo_image)

        # Ensure the drawing (mask) will be on top of the background image
        self.canvas.tag_lower(self.canvas_image_id)

    def draw_mask(self, event):
        # Draw on the canvas and the mask image simultaneously
        brush_size = 50
        self.draw.ellipse((event.x - brush_size, event.y - brush_size,
                           event.x + brush_size, event.y + brush_size), fill=(0, 0, 0, 0))

        self.canvas.create_oval(event.x - brush_size, event.y - brush_size,
                                event.x + brush_size, event.y + brush_size, fill="black")
    def clear_mask(self):
        # Re-initialize the mask to clear it
        self.initialize_mask()

        # Clear any drawings from the canvas as well, maintaining the background image if any
        self.canvas.delete("all")
        if hasattr(self, 'user_photo_image'):
            # If a background image exists, redraw it on the canvas
            self.canvas.create_image(0, 0, anchor="nw", image=self.user_photo_image)

    def call_dalle_api(self):
        try:
            mask_bytes_io = BytesIO()
            self.mask_image.save(mask_bytes_io, format='PNG')
            mask_bytes_io.seek(0)  # Rewind to the beginning of the BytesIO object

            response = self.client.images.edit(
                    image=open(self.user_image_path, "rb"),
                    mask=mask_bytes_io,
                    prompt=self.prompt_input.get(),
                    n=1,
                    size="512x512"
                )
            image_url = response.data[0].url
            image_response = requests.get(image_url)
            image_data = Image.open(BytesIO(image_response.content))
            self.save_image(image_data)
            self.result_image = ImageTk.PhotoImage(image_data)
        except Exception as e:
            print("Error generating or displaying the image:", e)

    def send_to_dalle(self):
        # Here, implement the API call to DALL-E with the image and prompt
        print("Sending to DALL-E with prompt:", self.prompt_input.get())
        self.call_dalle_api()

        # Show the returned image in a separate window (placeholder logic)
        result_window = tk.Toplevel(self.root)
        result_window.title("DALL-E Result")
        image_label = tk.Label(result_window,bg='black')
        image_label.configure(image=self.result_image )
        image_label.pack()



# Create the main application window
root = tk.Tk()
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI()
app = DalleApp(root, client)
root.mainloop()
