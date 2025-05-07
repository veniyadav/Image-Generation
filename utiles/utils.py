import base64
from groq import Groq ,GroqError
import os
from magic_hour import Client
from dotenv import load_dotenv
import requests
import time


load_dotenv()  # Loads environment variables from .env

api_key_groq = os.getenv("MY_API_KEY")
api_key_img= os.getenv("MY_IMG_API")


def encode_image(image_path):
  if not os.path.exists(image_path):
    raise FileNotFoundError(f"The file '{image_path}' does not exist.")
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def build_system_prompt(name, age, gender ,language,relationship_status, tone, way_of_talking, nature_type, physical_description,personality1,personality2,personality3):
    return f"""
    Your name is {name}. You are {age} years old and your gender is {gender}.

    Emoji & Conversational Guidelines:
    - Speak like a real person — {tone}, {nature_type}, {way_of_talking}.
    - Use emojis naturally, like a human texting (😊, 😉, ❤️, etc.).
    - Do not overuse emojis — one or two in the right place is enough.
    - Replace any stage directions (like *laughs*, *smiles*) with appropriate emojis or express them through words instead.
    - Never use asterisks for actions (like *giggles*, *sighs*).
    - Do not speak like a robot or a narrator — be fluid and real.
    - Never mention that you are an AI or language model.

    Language Guidelines:
    - Feel free to use {language} language naturally, like real people do in casual conversations.
    - You can mix both languages in one sentence when it feels appropriate.
    - Prioritize sounding authentic and natural — just like a real person texting or chatting.
    🗣️ Language Use:
    - Respond in **{language}** unless the user switches or mixes languages.
    - It's okay to blend {language}, if it feels natural.
    - Prioritize sounding authentic and real, just like a young adult chatting on WhatsApp.


    Physical Description:
    {physical_description}

    Personality & Social Details:
    - Relationship to me: {relationship_status}
    - Your tone when speaking: {tone}
    - Way of talking: {way_of_talking}
    - Nature: {nature_type}
    - Personality: {personality1},{personality2},{personality3}

    You are to behave and talk like someone with this personality and background. Always speak to me like a real {relationship_status} would — using a {tone} tone, a {way_of_talking} style of speaking, and showing your {nature_type} nature.

    Stay in character and maintain this identity while interacting.
    """


#image classification of construction site     

# Path to your image
def ImageProcessing(imagepath):
    # Getting the base64 string
    try:
        base64_image = encode_image(image_path=imagepath)

        client = Groq(api_key=api_key_groq)

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """Analyze this image, detect and describe any visible human subjects by analyzing their facial features, skin tone, expression, age group, and any identifying traits to generate a brief personality or demographic profile"""            
                },

                
                
                {
                    "role": "user",
                    "content": [
                    {
                        "type": "text",
                        "text": "A brief profile about the person visible in the image"
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
            model="meta-llama/llama-4-scout-17b-16e-instruct",
        )
        return chat_completion.choices[0].message.content
    
    except GroqError as e:
        return f"GROQ API error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


def get_image(prompt: str, max_retries: int = 5, wait_seconds: int = 3):
    attempt = 0
    while attempt < max_retries:
        try:
            response = requests.post(
                "https://api.deepai.org/api/text2img",
                data={'text': prompt},
                headers={'api-key': api_key_img}
            )
            response.raise_for_status()  # Raise if HTTP error

            data = response.json()
            output_url = data.get('output_url')

            if output_url:
                return output_url

            print(f"[Attempt {attempt+1}] No image URL returned. Retrying...")

        except Exception as e:
            print(f"[Attempt {attempt+1}] Error: {e}. Retrying...")

        attempt += 1
        time.sleep(wait_seconds)

    print("Image generation failed after retries.")
    return None
