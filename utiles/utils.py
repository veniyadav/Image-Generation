import base64
from groq import Groq ,GroqError
import os


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

        client = Groq(api_key="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")

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




import requests
import time
def generate_image(prompt: str):
    url = "https://api.freepik.com/v1/ai/mystic"

    payload = {
        "structure_strength": 48,
        "adherence": 50,
        "hdr": 50,
        "resolution": "2k",
        "aspect_ratio": "square_1_1",
        "model": "realism",
        "creative_detailing": 33,
        "engine": "automatic",
        "fixed_generation": False,
        "filter_nsfw": True,
        "prompt": prompt
    }

    headers = {
        "x-freepik-api-key": "FPSXa78a40fab6404ffb9c4359a9066eb74f",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    # Check for HTTP error
    if response.status_code != 200:
        print("Error from Freepik API:")
        print(response.status_code, response.text)
        return None, None

    data = response.json()
    # print("Initial generation response:", data)  # Debug output

    statuscode = data.get("data", {}).get("status")
    task_id = data.get("data", {}).get("task_id")

    return statuscode, task_id

def get_image(prompt: str):
    statuscode, task_id = generate_image(prompt)
    if not task_id:
        print("Invalid task_id. Exiting.")
        return None

    headers = {"x-freepik-api-key": "FPSXa78a40fab6404ffb9c4359a9066eb74f"}

    while statuscode == "CREATED" or statuscode == "IN_PROGRESS":
        # print("Waiting for image generation...")
        time.sleep(5)
        response = requests.get(f"https://api.freepik.com/v1/ai/mystic/{task_id}", headers=headers)
        statuscode = response.json().get("data", {}).get("status")

    response = requests.get(f"https://api.freepik.com/v1/ai/mystic/{task_id}", headers=headers)
    # print("Image generation completed.")
    data=response.json()

    generated_images = data.get("data", {}).get("generated", [])
    if generated_images:
        image_url = generated_images[0]
        # print("Here is the generated image:", image_url)
        return image_url
    else:
        print("No image URL found.")
        return None
