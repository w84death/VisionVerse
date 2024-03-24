

# VisionVerse


import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import PhotoImage, Label, simpledialog, filedialog, ttk
from PIL import Image, ImageTk
import requests
from io import BytesIO
from openai import OpenAI
import cv2
import base64
import time
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path
import pygame

load_dotenv()
image_save_path = "webcam_image.jpg"
api_key = os.getenv('OPENAI_API_KEY')
pygame.mixer.init()

def show_wait_popup():
    popup = tk.Toplevel()
    popup.title("Please wait...")
    popup.resizable(False, False)
    popup.geometry("256x32")
    popup.configure(bg='red')
    popup.update_idletasks()
    
    return popup

def close_wait_popup(popup):
    # Destroy the popup window
    popup.destroy()

def call_openai_api():
    popup = show_wait_popup()
    system_prompt = system_prompt_textbox.get("1.0", tk.END).strip()
    user_prompt = user_prompt_textbox.get("1.0", tk.END).strip()

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        api_response_textbox.delete("1.0", tk.END)  # Clear the textbox before inserting new content
        
        if response.choices and len(response.choices) > 0:
            message_content = response.choices[0].message.content
            api_response_textbox.insert(tk.END, message_content)
        else:
            api_response_textbox.insert(tk.END, "No response from API")
    except Exception as e:
        api_response_textbox.insert(tk.END, "Error: " + str(e))

    close_wait_popup(popup)

def save_image(image):
    # Format the current date and time as a string
    datestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"image_{datestamp}.jpg"
    
    # Save the PIL.Image object to a file
    image.save(filename)
    print(f"Image saved as {filename}")

def on_image_click(event=None):
    top = tk.Toplevel()
    top.attributes('-fullscreen', True)
    img_full = image_label.full_image
    label = tk.Label(top, image=img_full)
    
    label.pack(expand=True, fill=tk.BOTH)

    top.bind("<Escape>", lambda e: top.destroy())
    label.image = img_full

def generate_image():
    popup = show_wait_popup()
    user_prompt = user_prompt_textbox.get("1.0", tk.END).strip()

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=user_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url

        # Fetch the image from the URL
        image_response = requests.get(image_url)
        image_data = Image.open(BytesIO(image_response.content))
        resized_image_data = image_data.resize((512,512), Image.Resampling.LANCZOS)
        img = ImageTk.PhotoImage(resized_image_data)
        save_image(image_data)
        image_label.configure(image=img)
        image_label.image = img
        image_label.full_image = ImageTk.PhotoImage(image_data) 

    except Exception as e:
        print("Error generating or displaying the image:", e)

    close_wait_popup(popup)


def capture_image_from_webcam(image_save_path="webcam_image.jpg", width=512, height=512):    # Start the webcam
    cap = cv2.VideoCapture(0)
    
    # Check if the webcam is opened correctly
    if not cap.isOpened():
        raise IOError("Cannot open webcam")


    time.sleep(1)

    ret, frame = cap.read()
    resized_frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
    cv2.imshow('Capture', frame)
    cap.release()
    cv2.destroyAllWindows()
    
    # Save the captured image
    cv2.imwrite(image_save_path, frame)

    image = Image.open(image_save_path)

    # Convert the Pillow image to a format Tkinter can handle
    img = ImageTk.PhotoImage(image)

    # Display the image in the GUI
    image_label.configure(image=img)
    # Keep a reference to the image
    image_label.image = img
    
def call_image_recognition():
    popup = show_wait_popup()

    # Function to encode the image to base64
    def encode_image():
        with open(image_save_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    # Path to your image
    #image_path = "test.jpg"

    # Getting the base64 string
    base64_image = encode_image()

    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
    }

    payload = {
    "model": "gpt-4-vision-preview",
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": "What’s in this image?"
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
            }
        ]
        }
    ],
    "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    
    api_response_textbox.delete("1.0", tk.END)
    message_content = response.json()
    api_response_textbox.insert(tk.END, message_content['choices'][0]['message']['content'])

    close_wait_popup(popup)

def capture_image():
    capture_image_from_webcam(image_save_path);
    call_image_recognition();


def select_and_transcribe_audio():
    # Open a file dialog to select the MP3 file
    file_path = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
    if not file_path:  # User cancelled the dialog
        return


    popup = show_wait_popup()
    # Open the selected audio file
    with open(file_path, "rb") as audio_file:
        try:
            # Send the audio file to the API for transcription
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
            # Insert the transcription text into the api_response_textbox
            api_response_textbox.delete("1.0", tk.END)  # Clear the textbox first
            api_response_textbox.insert(tk.END, transcription.text)
            close_wait_popup(popup)
        except Exception as e:
            api_response_textbox.delete("1.0", tk.END)  # Clear the textbox first
            api_response_textbox.insert(tk.END, "Error during transcription: " + str(e))
            close_wait_popup(popup)


def play_speech(filename):
    # Define the path to your speech file
    speech_file_path = Path(filename)
    if speech_file_path.exists():
        # Load and play the speech file
        pygame.mixer.music.load(str(speech_file_path))
        pygame.mixer.music.play()
    else:
        print("Speech file not found. Please generate the speech first.")

def text_to_speech():
    # Read text from the api_response_textbox
    text = api_response_textbox.get("1.0", tk.END).strip()
    if not text:  # Check if the textbox is empty
        print("The text box is empty. Please provide some text for speech synthesis.")
        return
 
    voice = selected_voice.get()

    try:
        popup = show_wait_popup()
        # Call the OpenAI API to generate speech from the text
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )

        # Define the path for the output MP3 file
        #speech_file_path = Path("speech.mp3")

        datestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"speech_{datestamp}.mp3"

        # Save the audio stream to the file
        response.stream_to_file(str(filename))
        close_wait_popup(popup)
        play_speech(filename)
        print(f"Speech file saved to: {filename}")
    except Exception as e:
        print(f"Error during text-to-speech conversion: {str(e)}")
        close_wait_popup(popup)



# Create the main window
root = tk.Tk()
root.title("VisionVerse")
root.geometry("1280x900")
root.configure(bg='black')
root.bind("<Escape>", lambda e: root.destroy())

# Main frame to contain left and right frames
main_frame = tk.Frame(root, bg='lightgray', padx=10, pady=10)
main_frame.pack(expand=True, fill='both', padx=20, pady=20)
main_frame.configure(bg='black')


# Left frame for inputs and buttons
left_frame = tk.Frame(main_frame, bg='lightgray')
left_frame.grid(row=0, column=0, sticky="nsew")

# Right frame for the image preview
right_frame = tk.Frame(main_frame, bg='black')
right_frame.grid(row=0, column=1, sticky="nsew", padx=(20, 0))  # Add some padding between the frames

# Configure the main frame grid to allocate space properly

main_frame.rowconfigure(0, weight=1)

# Configure the layout of the left_frame for inputs and buttons
left_frame.columnconfigure(0, weight=1)
left_frame.rowconfigure([0, 1, 2, 3, 4], weight=1)  # Configure rows to distribute space as needed

# Add your existing widgets to the left_frame instead of frame
system_prompt_label = tk.Label(left_frame, text="System Prompt:", bg='lightgray')
system_prompt_label.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

system_prompt_textbox = ScrolledText(left_frame, height=5)
system_prompt_textbox.insert(tk.END, "You are impersonating Hunter S. Thompson. Writing in Gonzo Style.")
system_prompt_textbox.grid(row=1, column=0, sticky="nsew", padx=5)

user_prompt_label = tk.Label(left_frame, text="User Prompt:", bg='lightgray')
user_prompt_label.grid(row=2, column=0, sticky="nw", padx=5, pady=5)

user_prompt_textbox = ScrolledText(left_frame, height=5)
user_prompt_textbox.grid(row=3, column=0, sticky="nsew", padx=5)

# Buttons
buttons_frame = tk.Frame(left_frame, bg='lightgray')
buttons_frame.grid(row=4, column=0, sticky="ew", pady=5)
chatgpt_button = tk.Button(buttons_frame, text="ChatGPT",  bg="blue", fg="white", command=call_openai_api)
chatgpt_button.pack(side=tk.LEFT, expand=True)
generate_image_button = tk.Button(buttons_frame, text="Generate Image", bg="green", fg="white", command=generate_image)
generate_image_button.pack(side=tk.LEFT, expand=True)
camera_button = tk.Button(buttons_frame, text="Camera", bg="red", fg="white", command=capture_image)
camera_button.pack(side=tk.LEFT, expand=True)

api_response_label = tk.Label(left_frame, text="API Response:", bg='lightgray')
api_response_label.grid(row=5, column=0, sticky="nw", padx=5, pady=5)

api_response_textbox = ScrolledText(left_frame, height=22)
api_response_textbox.grid(row=6, column=0, sticky="nsew", padx=5, pady=5)


audio_frame = tk.Frame(left_frame, bg='lightgray')
audio_frame.grid(row=7, column=0, sticky="ew", pady=5)

transcript_button = tk.Button(audio_frame, text="STT (MP3)", bg="violet", fg="white", command=select_and_transcribe_audio)
transcript_button.pack(side=tk.LEFT, expand=True)

voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
selected_voice = tk.StringVar()
selected_voice.set(voices[0])  # Default voice
voice_dropdown = ttk.Combobox(audio_frame, textvariable=selected_voice, values=voices)
voice_dropdown.pack(side=tk.LEFT, expand=True)

tts_button = tk.Button(audio_frame, text="TTS", bg="violet", fg="white", command=text_to_speech)
tts_button.pack(side=tk.LEFT, expand=True)

api_response_label = tk.Label(left_frame, text="(c)2024 Krzysztof Krystian Jankowski; Using OpenAI API", bg='white')
api_response_label.grid(row=8, column=0, sticky="nw", padx=5, pady=1)


# Configure the right_frame for the image
right_frame.columnconfigure(0, weight=1)
right_frame.rowconfigure(0, weight=1)

# Assuming image_label is your image preview widget, add it to right_frame
image_label = tk.Label(right_frame, bg='black')
image_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
image_label.bind("<Button-1>", on_image_click)

# Run the application

client = OpenAI()

root.mainloop()
