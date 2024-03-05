# VisionVerse

## Application Window
- response from ChatGPT 4 Turbo API
- generating image DALL-E 3 API
- taking snapshot from a webcam and interprets it using GPT 4 Vision API

![Application Window](app.png)

Image recognition.
![Image Recognition](app-vision.png)

Fullscreen preview.
![Fullscreen Preview](app-fullscreen.png)

## Setup

Create ```.env``` file and put your OpenAI API Key there.

```
OPENAI_API_KEY=ab-YOURKEYEXAMPLEYOURKEYEXAMPLE
```

```
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

## Usage

```
$ python3 main.py
```