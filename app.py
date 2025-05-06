from langchain.prompts import ChatPromptTemplate
from groq import Groq
from utiles.globalllm import GroqLLM
from flask import Flask, request, jsonify
import os
import tempfile
import requests
from werkzeug.utils import secure_filename
from utiles.utils import build_system_prompt, ImageProcessing,get_image
from flask_cors import CORS
from flask_cors import cross_origin
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MY_API_KEY")
client = Groq(api_key=API_KEY)

groq_llm = GroqLLM(model="llama-3.3-70b-versatile", api_key=API_KEY,temperature=0.8)#llama-3.1-8b-instan

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/text-to-image', methods=['POST'])
@cross_origin()
def generate_image_endpoint():
    try:
        # Get the prompt from the JSON request body
        data = request.get_json()  # Proper way to get JSON body
        # prompt = data.get('prompt')  # Access the prompt from the JSON object
        body_shape=data.get("body_shape")
        breast_size=data.get("breast_size")
        butt_size=data.get("butt_size")
        skin_color=data.get("skin_color")
        eye_color=data.get("eye_color")
        hair_color=data.get("hair_color")
        hair_style=data.get("hair_style")
        gender=data.get("gender")
        age=data.get("age")
        nationality = data.get("nationality")  # Add this line


        if not body_shape and not breast_size and not butt_size and not skin_color and not eye_color and not hair_color and not hair_style and not gender:
            return jsonify({"error": "Prompt is required"}), 400

        # Generate the image URL
        image_url = get_image(f"""
    Generate a hyperrealistic full-body image of a {age}-year-old {gender} from {nationality}. She has a {body_shape} body type with a noticeably large butt. Her skin tone is {skin_color}, and she has {eye_color} eyes that are expressive and lifelike. Her hair is {hair_color}, styled in a {hair_style} manner that flows naturally. 

    The image should capture realistic lighting, natural shadows, detailed skin texture, and lifelike proportions. Her pose should appear relaxed and confident, and the overall composition should feel grounded in reality, with clothing and background subtly enhancing the realism rather than distracting from it.
    """)


  # Call your get_image function

        if not image_url:
            return jsonify({"error": "Image generation failed"}), 500

        return jsonify({"image_url": image_url}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#image analysis route
@app.route("/analyze_image_prompt", methods=["POST"])
@cross_origin()
def analyze_image():
    image_file = request.files.get("image")
    image_url = request.form.get("image_url")
    temp_file_path = None

    # Reject if both image and image_url are provided
    if image_file and image_url:
        return jsonify({"error": "Provide either an image file or an image URL, not both"}), 400

    # Reject if neither provided
    if not image_file and not image_url:
        return jsonify({"error": "No image file or image URL provided"}), 400

    # Handle uploaded file
    if image_file and image_file.filename != "":
        filename = secure_filename(image_file.filename)
        file_path = os.path.join("uploads", filename)
        os.makedirs("uploads", exist_ok=True)
        image_file.save(file_path)

    # Handle image URL
    elif image_url:
        try:
            response = requests.get(image_url, stream=True)
            if response.status_code != 200:
                return jsonify({"error": "Failed to download image from URL"}), 400

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            for chunk in response.iter_content(1024):
                temp_file.write(chunk)
            temp_file.close()
            file_path = temp_file.name
            temp_file_path = file_path  # Mark for deletion
        except Exception as e:
            return jsonify({"error": f"Error downloading image: {str(e)}"}), 400

    else:
        return jsonify({"error": "Invalid image input"}), 400

    # Extract user-provided form data
    name = request.form.get("name", "Unknown")
    age = request.form.get("age", "Unknown")
    relationship_status = request.form.get("relationship_status", "friend")
    tone = request.form.get("tone", "neutral")
    way_of_talking = request.form.get("way_of_talking", "normal")
    nature_type = request.form.get("nature_type", "undisclosed")
    language=request.form.get("prefered_language","english")
    gender=request.form.get("gender","female")
    personality1=request.form.get("personality1","cute")
    personality2=request.form.get("personality2","naughty")
    personality3=request.form.get("personality3","bold")

    try:
        # Analyze the image
        physical_description = ImageProcessing(file_path)
        # Build system prompt
        system_prompt = build_system_prompt(
           name, age, gender ,language,relationship_status, tone, way_of_talking, nature_type, physical_description,personality1,personality2,personality3
        )

        return jsonify({
            "system_prompt": system_prompt,
            "image_analysis": physical_description
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temp files
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        elif image_file and os.path.exists(file_path):
            os.remove(file_path)


@app.route("/chat", methods=["POST"])
@cross_origin()
def chat():
    data = request.get_json()
    
    # Validate input
    if not data or "system_prompt" not in data or "human_msg" not in data:
        return jsonify({"error": "Missing required parameters"}), 400

    system_prompt = data["system_prompt"]
    human_msg = data["human_msg"]

    # Construct prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt.strip()),
        ("human", human_msg.strip())
    ])

    # Create chain and invoke
    chain = prompt | groq_llm
    response = chain.invoke({})

    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0",port=8001)
