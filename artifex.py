import tkinter as tk
from tkinter import filedialog, Checkbutton, IntVar
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

        self.buttons_frame = tk.Frame(root)
        self.buttons_frame.pack(fill=tk.X, pady=10)  # Adjust padding as needed


        # Button to open file browser and select image
        self.open_file_btn = tk.Button(self.buttons_frame, text="Open Image", command=self.open_image)
        self.open_file_btn.pack(side=tk.LEFT, padx=5)
        self.painting_enabled = IntVar(value=1)  # 1 means painting is enabled by default
        self.toggle_paint_btn = Checkbutton(self.buttons_frame, text="Enable Mask Painting", variable=self.painting_enabled, command=self.toggle_painting)
        self.toggle_paint_btn.pack(side=tk.LEFT, padx=5)

        self.clear_mask_btn = tk.Button(self.buttons_frame, text="Clear Mask", command=self.clear_mask)
        self.clear_mask_btn.pack(side=tk.LEFT, padx=5)

        # Button to send data to the API
        self.send_btn = tk.Button(self.buttons_frame, text="Send to DALL-E", command=self.send_to_dalle)
        self.send_btn.pack(side=tk.LEFT, padx=5)


        # Canvas for drawing mask
        self.canvas = tk.Canvas(root, width=1024, height=1024, bg="white")
        self.canvas.pack()
        self.canvas.bind("<B1-Motion>", self.draw_mask)


        # Image for drawing
        self.initialize_mask()


        # Placeholder for user-selected image path
        self.user_image_path = None
        self.result_image = None
        self.canvas_image_id = None

    def toggle_painting(self):
        # This method can be expanded to disable/enable drawing functionality dynamically
        if self.painting_enabled.get() == 0:
            self.canvas.unbind("<B1-Motion>")
        else:
            self.canvas.bind("<B1-Motion>", self.draw_mask)

    def initialize_mask(self):

        self.mask_image = Image.new("RGBA", (1024, 1024), (255, 255, 255, 255))
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
        # Convert PIL image to PhotoImage, which is compatible with Tkinter
        self.user_photo_image = ImageTk.PhotoImage(user_image.resize((1024, 1024), Image.Resampling.LANCZOS))

        # If there's already an image on the canvas, remove it
        if self.canvas_image_id is not None:
            self.canvas.delete(self.canvas_image_id)

        # Display the image on the canvas
        self.canvas_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.user_photo_image)

        # Ensure the drawing (mask) will be on top of the background image
        self.canvas.tag_lower(self.canvas_image_id)

    def draw_mask(self, event):
        # Draw on the canvas and the mask image simultaneously
        if self.painting_enabled.get():
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

    def prepare_image_for_dalle(self, image_path):
            """
            Open the user-selected image, convert it to RGBA (if not already),
            and save it to a bytes object for the API call.
            """
            # Open the image
            image = Image.open(image_path)
            image.resize((1024, 1024), Image.Resampling.LANCZOS)

            # Convert the image to RGBA
            image_rgba = image.convert("RGBA")

            # Save the image to a bytes object
            image_bytes_io = BytesIO()
            image_rgba.save(image_bytes_io, format='PNG')
            image_bytes_io.seek(0)  # Rewind to the start

            return image_bytes_io

    def call_dalle_api(self):
        try:
            user_image_bytes = self.prepare_image_for_dalle(self.user_image_path)
            if self.painting_enabled.get():
                mask_bytes_io = BytesIO()
                self.mask_image.save(mask_bytes_io, format='PNG')
                mask_bytes_io.seek(0)  # Rewind to the beginning of the BytesIO object

                response = self.client.images.edit(
                        image=user_image_bytes,
                        mask=mask_bytes_io,
                        prompt=self.prompt_input.get(),
                        n=1,
                        size="1024x1024"
                    )
            else:
                response = self.client.images.edit(
                        image=user_image_bytes,
                        prompt=self.prompt_input.get(),
                        n=1,
                        size="1024x1024"
                    )
            image_url = response.data[0].url
            image_response = requests.get(image_url)
            image_data = Image.open(BytesIO(image_response.content))
            self.save_image(image_data)
            self.result_image = ImageTk.PhotoImage(image_data)
        except Exception as e:
            print("Error generating or displaying the image:", e)

    def use_as_new_base(self):
        self.user_photo_image = self.result_image

        # Update the canvas with the new image
        self.canvas.delete("all")  # Clear existing canvas content
        self.canvas.create_image(0, 0, anchor="nw", image=self.user_photo_image)

        # Reinitialize the mask for new edits
        self.initialize_mask()

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

        #use_new_base_btn = tk.Button(result_window, text="Use as New Base", command=lambda: self.use_as_new_base())
        #use_new_base_btn.pack()


# Create the main application window
root = tk.Tk()
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI()
app = DalleApp(root, client)
root.mainloop()
