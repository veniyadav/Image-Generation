from langchain.prompts import ChatPromptTemplate
from groq import Groq
from utiles.globalllm import GroqLLM
from flask import Flask, request, jsonify
import os
import tempfile
import requests
from utiles.utils import build_system_prompt, ImageProcessing,get_image
from flask_cors import CORS
from flask_cors import cross_origin
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify,send_from_directory, abort
from flask_migrate import Migrate
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash 
from models import *
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required
)

app = Flask(__name__)

#DBCONFIGER
# Local MySQL Database Configuration (fallback to SQLite for development)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/image_generation'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:dtyxtGrcajPlvDLILFCfgVdWFwwCvTdD@metro.proxy.rlwy.net:41157/railway'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# Set a secret key for JWT (change this in production)
app.config['JWT_SECRET_KEY'] = 'super-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)


db.init_app(app)  # Initialize SQLAlchemy with app
migrate = Migrate(app, db)

# Define and set the upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize SQLAlchemy, JWTManager, and SocketIO
# db = SQLAlchemy(app)
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # For development only

CORS(app, resources={r"/*": {"origins": "*"}},
     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

load_dotenv()

API_KEY = os.getenv("MY_API_KEY")
client = Groq(api_key=API_KEY)

groq_llm = GroqLLM(model="llama-3.3-70b-versatile", api_key=API_KEY,temperature=0.8)#llama-3.1-8b-instan




#register login and password change routes****************
 
@app.route('/register', methods=['POST'])
@cross_origin(
    origins="*",
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)
def UserRegistration():
    data = request.get_json()
    if not data:
         return jsonify({'message': 'Data is required'}), 400
    Name = data.get('name')
    Email = data.get('email')
    Password = data.get('password')
    confirm_password = data.get('confirm_password')
 
    if not Name or not Email or not Password or not confirm_password:
        return jsonify({'message': 'ALl fields are required'}),400
 
    if Password != confirm_password:
        return jsonify({'message': 'Password and confirm password must be same'}), 400
     
    if User.query.filter_by(email=Email).first():
        return jsonify({'message': 'Email already exists'}), 400
 
    #hashing the password
    hashed_password = generate_password_hash(Password, method='pbkdf2:sha256')
    initial_tokens=200

    #creating a new user
    new_user = User(name=Name,
                        email=Email,
                        password=hashed_password,
                        tokens=initial_tokens) #initialize the token to new user account
    db.session.add(new_user)
    db.session.commit()
 
    return jsonify({'message':'User Registered Succesfully', 'email':Email,'name':Name, 'Tokens':initial_tokens}), 201
 
@app.route('/Login', methods=['POST'])
@cross_origin(
    origins="*",
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)
def User_login():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Fields are required'}), 400

    Email = data.get('email')
    Password = data.get('password')

    if not Email or not Password:
        return jsonify({'message': 'Email & Password are required'}), 400

    user = User.query.filter_by(email=Email).first()
    if not user or not check_password_hash(user.password, Password):
        return jsonify({'message': 'Invalid Credentials'}), 404

    # Create access token
    access_token = create_access_token(identity=str(user.id))
    return jsonify({'message': 'Login successful', 'access_token': access_token, "user_id":user.id, "user_name":user.name, "user_email":user.email, "Remaining tokens": user.tokens}), 200
 
@app.route('/password_change', methods=['PUT'])
@cross_origin(
    origins="*",
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)
@jwt_required()
def User_Password_Change():
    data = request.get_json()
   
    email = data.get('email')
    new_password = data.get('new_password')
    new_name=data.get("name")
    # if not email or not new_password:
    #     return jsonify({'message':'Email & Password are required'}),400
   
    employee = User.query.filter_by(email=email).first()
    if not employee:
        return jsonify({'message':'Invalid Credentials'}), 404
    if new_password:
        employee.password = generate_password_hash(new_password, method='pbkdf2:sha256')

    if new_name:
        employee.name = new_name

    db.session.commit()
    return jsonify({'message':'Profile changed successfully'}),200

 
@app.route('/getusers', methods=['GET'])
@cross_origin(
    origins="*",
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)
def get_users():
    user_id = request.args.get('user_id')
    user_email = request.args.get('user_email')
   
    query = User.query
    if user_id:
        query = query.filter(User.id == user_id)
    if user_email:
        query = query.filter(User.email == user_email)
   
    data = query.all()
    users = []
    for user in data:
        users.append({
            'user_id': user.id,
            'name': user.name,
            'email': user.email,
            'tokens':user.tokens
        })
    return jsonify(users), 200

@app.route('/get_tokens',methods=['GET'])
@cross_origin(
    origins="*",
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)
def get_tokens():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error":"User ID required"})
    
    #check user in database
    filter_id = User.query.filter_by(id=user_id).first()

    return jsonify({"token_count": filter_id.tokens})

@app.route('/text-to-image', methods=['POST'])
@cross_origin(
    origins="*",
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)
@jwt_required()
def generate_image_endpoint():
    try:
        data = request.get_json()
        user_id = data.get("user_id")

        #Fetch user from the database
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({"error":"User not found"}),404
        
        #check if the user has enough tokens

        body_shape = data.get("body_shape")
        breast_size = data.get("breast_size")
        butt_size = data.get("butt_size")
        skin_color = data.get("skin_color")
        eye_color = data.get("eye_color")
        hair_color = data.get("hair_color")
        hair_style = data.get("hair_style")
        gender = data.get("gender")
        age = data.get("age")
        nationality = data.get("nationality")

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        if not any([body_shape, breast_size, butt_size, skin_color, eye_color, hair_color, hair_style, gender]):
            return jsonify({"error": "At least one descriptive field is required"}), 400

        # Construct the prompt
        if gender.lower() == "boy":
            prompt = f"""
        Generate a hyperrealistic full-body image of a {age}-year-old {gender} from {nationality}. 
        He has a {body_shape} body type with well-defined features. His skin tone is {skin_color}, and he has {eye_color} eyes that are expressive and lifelike. 
        His hair is {hair_color}, styled in a {hair_style} manner that suits his personality.

        The image should capture realistic lighting, natural shadows, detailed skin texture, and lifelike proportions. 
        His pose should appear relaxed and confident, and the overall composition should feel grounded in reality, 
        with clothing and background subtly enhancing the realism rather than distracting from it.
        """
            
        else:
           prompt = f"""
            Generate a hyperrealistic full-body image of a {age}-year-old {gender} from {nationality}. She has a {body_shape} body type with a noticeably {butt_size} butt and {breast_size} curves . Her skin tone is {skin_color}, and she has {eye_color} eyes that are expressive and lifelike. Her hair is {hair_color}, styled in a {hair_style} manner that flows naturally.
            The image should capture realistic lighting, natural shadows, detailed skin texture, and lifelike proportions. Her pose should appear relaxed and confident, and the overall composition should feel grounded in reality, with clothing and background subtly enhancing the realism rather than distracting from it.
            """

        # Generate the image (replace this with your actual image generation call)
        image_url = get_image(prompt)

        if not image_url:
            return jsonify({"error": "Image generation failed"}), 500
    
        if user.tokens < 10:
            return jsonify({"error":"Insufficient tokens, Please add more tokends to your account"})
        
        #deduction per image
        if image_url:
            new_tokens=user.tokens - 10
            user.tokens = new_tokens
        

        # Save to database
        image_entry = ImageData(
            user_id=user_id,
            image_url=image_url,
            timestamp=str(datetime.utcnow())
        )
        db.session.add(image_entry)
        db.session.commit()

        return jsonify({"image_url": image_url, "Remaining tokens": user.tokens}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#image analysis route
@app.route("/analyze_image_prompt", methods=["POST"])
@cross_origin(
    origins="*",
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)
@jwt_required()
def analyze_image():
    # image_file = request.files.get("image")
    image_url = request.form.get("image_url")
    temp_file_path = None


    # Reject if neither provided
    if  not image_url:
        return jsonify({"error": "No image URL provided"}), 400

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

        image_data = ImageData.query.filter_by(image_url=image_url).first()
        if image_data:
            image_data.prompt = system_prompt
            db.session.commit()

        return jsonify({
            "message": "Prompt updated successfully" if image_data else "Image URL not found in database",
            "image_analysis": physical_description,
            "system_prompt": system_prompt
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temp files
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        # elif image_file and os.path.exists(file_path):
        #     os.remove(file_path)

@app.route("/image_data", methods=["GET"])
@cross_origin(
    origins="*",
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)
@jwt_required()
def get_images():
    # Get optional query parameters
    user_id = request.args.get("user_id")
    image_id = request.args.get("image_id")
    image_url = request.args.get("image_url")

    # Start with base query
    query = ImageData.query

    # Apply filters if provided
    if user_id:
        query = query.filter_by(user_id=user_id)
    if image_id:
        query = query.filter_by(id=image_id)
    if image_url:
        query = query.filter_by(image_url=image_url)

    # Execute query
    images = query.all()

    # Format response
    result = []
    for img in images:
        result.append({
            "id": img.id,
            "user_id": img.user_id,
            "image_url": img.image_url,
            "prompt": img.prompt,   
            "timestamp": img.timestamp
        })

    return jsonify(result), 200


@app.route('/add_token', methods =['PUT'])
@cross_origin(
    origins="*",
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)
@jwt_required()
def add_tokens():
    try :
        data  = request.get_json()
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error":" User ID required"}),404
        
        #detect user from the database
        user =  User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({"error":"User not found"})
         
        #adding 100 tokens to the user's account
        user.tokens += 100
        db.session.commit()
        return jsonify({"message":"Tokens added successfully", "user_id": user_id, "New_added_tokens": user.tokens}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}) ,500

@app.route("/chat", methods=["POST"])
@cross_origin(
    origins="*",
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)
@jwt_required()
def chat():
    data = request.get_json()

    # Validate input
    if not data or "image_id" not in data or "human_msg" not in data or "user_id" not in data:
        return jsonify({"error": "Missing required parameters: image_id, human_msg, or user_id"}), 400

    # Extract parameters
    receiver_id = data.get("image_id")
    sender_id = data.get("user_id")
    human_msg = data.get("human_msg")

    # Fetch prompt from DB using image_id
    image_data = ImageData.query.filter_by(id=receiver_id).first()
    chat_data = Chat_messages.query.filter_by(id=sender_id).first()

    # Check if image data exists
    if not image_data and not chat_data :
        return jsonify({"error": "Data not found"}), 404

    s_prompt = image_data.prompt
    system_prompt = s_prompt.strip() if s_prompt else s_prompt

    # Construct chat prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_msg.strip())
    ])

    # Create chain and invoke
    chain = prompt | groq_llm
    response = chain.invoke({})

    # Determine sender and receiver
    sender_is_user = True  # Assuming the user is the sender
    receiver_is_user = False  # Assuming the AI is the receiver

    # Store the conversation
    new_chat = Chat_messages(
        sender_id=sender_id,
        receiver_id=receiver_id,
        message=human_msg,
        is_sender=sender_is_user
    )
    db.session.add(new_chat)
    db.session.commit()

    # Store the AI's response
    new_chat = Chat_messages(
        sender_id=receiver_id,
        receiver_id=sender_id,
        message=response,
        is_sender=receiver_is_user
    )
    db.session.add(new_chat)
    db.session.commit()

    return jsonify({"response": response})

@app.route("/chat_history", methods=["GET"])
@cross_origin(
    origins="*",
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)
@jwt_required()
def get_conversation():
    user_id=request.args.get('user_id')
    image_id=request.args.get("image_id")
    if not user_id and not image_id:
        return jsonify({"error" : "User_id and image_id required"})
    
    conversation = Chat_messages.query.filter(
        ((Chat_messages.sender_id == user_id) & (Chat_messages.receiver_id == image_id)) |
        ((Chat_messages.sender_id == image_id) & (Chat_messages.receiver_id == user_id))
    ).order_by(Chat_messages.timestamp).all()

    messages = [{"sender": c.sender_id, "message": c.message ,"timestamp": c.timestamp.isoformat()} for c in conversation]
    return jsonify(messages)
 
@app.route("/delete_chat", methods=["DELETE"])
@cross_origin(
    origins="*",
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)
@jwt_required()
def delete_chat():
    data= request.get_json()
    sender_id=data.get("sender_id")
    receiver_id=data.get("reciver_id")
 
    # Validate input
    if not sender_id or not receiver_id:
        return jsonify({"error": " ID is required"}), 400
   
    # Fetch chat messages from the database
    chat_messages = Chat_messages.query.filter(
        ((Chat_messages.sender_id == sender_id) & (Chat_messages.receiver_id == receiver_id)) |
        ((Chat_messages.sender_id == receiver_id) & (Chat_messages.receiver_id == sender_id))
    ).order_by(Chat_messages.timestamp).all()
   
    if not chat_messages:
        return jsonify({"error": "No chat messages found"}), 404
   
    # Delete chat messages
    for message in chat_messages:
        db.session.delete(message)
    db.session.commit()
 
    return jsonify({"message": "Chat messages deleted successfully"}), 200
   

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0",port=8001)