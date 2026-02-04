import google.generativeai as genai
import tkinter as tk
from tkinter import filedialog
import time
import os
from dotenv import load_dotenv

# Load API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found. Please set it in your .env file.")
    exit(1)
genai.configure(api_key=api_key)

# Initialize Gemini model
model = genai.GenerativeModel("gemini-3-flash-preview")

# File selection window
root = tk.Tk()
root.withdraw()

audio_path = filedialog.askopenfilename(
    title="Select file",
    filetypes=[("Formats", "*.m4a *.mp3 *.wav *.aac")]
)

if not audio_path:
    print("No file selected")
    exit()

print(f'Selected file: {audio_path}')

# Language selection
languages = {
    "1": ("en", "English"),
    "2": ("ru", "Russian"),
    "3": ("pl", "Polish")
}

print("\nSelect language:")
for key, (code, name) in languages.items():
    print(f"{key} - {name}")

lang_choice = input("Enter number: ")

if lang_choice in languages:
    language_code = languages[lang_choice][0]
    language_name = languages[lang_choice][1]
    print(f"Selected language: {language_name}")
else:
    print("Invalid language choice, using English by default")
    language_code = "en"
    language_name = "English"

# Conversation type selection
conv_types = {
    "1": "interview",
    "2": "business"
}

print("\nSelect conversation type:")
print("1 - Interview")
print("2 - Business meeting")

conv_choice = input("Enter number: ")

if conv_choice in conv_types:
    conv_type = conv_types[conv_choice]
    print(f"Selected type: {conv_type}")
else:
    print("Invalid choice, using interview by default")
    conv_type = "interview"

# Upload audio file
print("\nUploading audio file...")
audio_file = genai.upload_file(audio_path)

# Create prompt based on conversation type
if conv_type == "interview":
    prompt = f"""Transcribe this audio in {language_name} and provide interview analysis.

Format:
1. TRANSCRIPTION: [full transcription]
2. OVERALL ASSESSMENT: [rating and summary]
3. STRENGTHS: [bullet points]
4. WEAKNESSES: [bullet points]
5. RECOMMENDATIONS: [specific advice]"""
else:  # business
    prompt = f"""Transcribe this audio in {language_name} and provide business meeting summary.

Format:
1. TRANSCRIPTION: [full transcription]
2. SUMMARY: [key points discussed]
3. ACTION ITEMS: [list of tasks/decisions with responsible parties if mentioned]
4. NEXT STEPS: [follow-up actions]"""

# Generate response
print("Processing... Please wait")
start_time = time.time()

response = model.generate_content([prompt, audio_file])

end_time = time.time()
elapsed_time = end_time - start_time

# Output
print(f"\n{'='*50}")
print(response.text)
print(f"{'='*50}")
print(f"\nProcessing time: {elapsed_time:.2f} seconds")

# Token usage
# Token usage and cost
if hasattr(response, 'usage_metadata'):
    usage = response.usage_metadata
    
    # Pricing for gemini-3-flash-preview
    input_cost_per_1m = 0.50
    output_cost_per_1m = 3.00
    
    input_cost = (usage.prompt_token_count / 1_000_000) * input_cost_per_1m
    output_cost = (usage.candidates_token_count / 1_000_000) * output_cost_per_1m
    total_cost = input_cost + output_cost
    
    print(f"\nToken usage:")
    print(f"  Prompt tokens: {usage.prompt_token_count:,}")
    print(f"  Response tokens: {usage.candidates_token_count:,}")
    print(f"  Total tokens: {usage.total_token_count:,}")
    print(f"\nCost breakdown:")
    print(f"  Input cost: ${input_cost:.4f}")
    print(f"  Output cost: ${output_cost:.4f}")
    print(f"  Total cost: ${total_cost:.4f}")