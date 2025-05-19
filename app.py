from langchain.prompts import ChatPromptTemplate
from groq import Groq
from flask_socketio import emit
from utiles.globalllm import GroqLLM
from flask import Flask, request, jsonify
from sqlalchemy import or_
import os
import secrets
from flask import Flask, redirect, url_for, session, jsonify, request
from authlib.integrations.flask_client import OAuth
from flask_jwt_extended import create_access_token
from models import User, db  # adjust as needed
import tempfile
import requests
from utiles.utils import build_system_prompt, ImageProcessing,get_image
from flask_cors import CORS
from flask_cors import cross_origin
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify,send_from_directory, abort
from flask_migrate import Migrate
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash 
from models import *
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
app = Flask(__name__)

#secret token key
secret_token_key = secrets.token_hex(16)
# print("generated secret key is:",secret_token_key)
 
app.secret_key = secret_token_key
oauth = OAuth(app)

# Configure Google OAuth
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url=os.getenv("GOOGLE_DISCOVERY_URL"),
    client_kwargs={'scope': 'openid email profile'}
)


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

@app.route('/login/google')
def login_with_google():
    session.clear()
    nonce = secrets.token_hex(16)
    session['nonce'] = nonce

    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri, nonce=nonce)

@app.route('/google/callback')
def google_callback():
    try:
        # Step 1: Authorize token
        token = google.authorize_access_token()

        nonce = session.get('nonce')
        if not nonce:
            return jsonify({'error': 'Nonce missing from session'}), 400

        # Step 2: Get user info
        user_info = google.parse_id_token(token, nonce=nonce)
        if not user_info:
            return jsonify({'error': 'Failed to retrieve user info'}), 400

        email = user_info.get('email')
        name = user_info.get('name')

        if not email:
            return jsonify({'error': 'Email not provided by Google'}), 400

        # Step 3: Check if user exists
        user = User.query.filter_by(email=email).first()

        if user:
            # Existing user - do not change tokens
            access_token = create_access_token(identity=str(user.id))
            session['access_token'] = access_token

            return jsonify({
                'message': 'Login successful',
                'user_id': user.id,
                'user_name': user.name,
                'user_email': user.email,
                'tokens': user.tokens,
                'access_token': access_token
            }), 200

        else:
            # New user - give 200 tokens
            user = User(
                email=email,
                name=name,
                password="",  # Placeholder since it's Google login
                tokens=200
            )
            db.session.add(user)
            db.session.commit()

            access_token = create_access_token(identity=str(user.id))
            session['access_token'] = access_token

            Base_url="https://illustrious-horse-fbf3f5.netlify.app"
            frontend_url = f"{Base_url}/google-auth-callback"  # or your production domain
            redirect_url = f"{frontend_url}?token={access_token}&user_id={user.id}&user_name={user.name}"
            return redirect(redirect_url)

    except Exception as e:
        return jsonify({'error': 'Google login failed', 'message': str(e)}), 400
    
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
 
    return jsonify({'message':'User Registered Succesfully', 'email':Email,'name':Name, 'Tokens':initial_tokens}), 200
 
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

        if not any([body_shape, breast_size, butt_size, skin_color, eye_color, hair_color, hair_style, gender, age]):
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

    if not name or not age:
        return jsonify({"error": "Name and age are required"}), 400

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
            image_data.image_name = name
            db.session.commit()

        return jsonify({
            "message": "Prompt updated successfully" if image_data else "Image URL not found in database",
            "image_analysis": physical_description,
            "system_prompt": system_prompt,
            "image_name" : name
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
            "image_name": img.image_name,
            "prompt": img.prompt,   
            "timestamp": img.timestamp
        })

    return jsonify(result), 200

@app.route('/image_data_delete',methods=['DELETE'])
@cross_origin(
    origins="*",
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)
@jwt_required()
def delete_image():
    data = request.get_json()
    image_id = data.get("image_id")

    if not image_id:
        return jsonify({"error": "Image ID is required"}), 400

    try:
        image_data = ImageData.query.filter_by(id=image_id).first()
        if not image_data:
            return jsonify({"error": "Image not found"}), 404

        db.session.delete(image_data)
        db.session.commit()

        return jsonify({"message": "Image deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# @app.route('/add_token', methods =['PUT'])
# @cross_origin(
#     origins="*",
#     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
#     supports_credentials=True,
#     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
# )
# @jwt_required()
# def add_tokens():
#     try :
#         data  = request.get_json()
#         user_id = data.get("user_id")

#         if not user_id:
#             return jsonify({"error":" User ID required"}),404
        
#         #detect user from the database
#         user =  User.query.filter_by(id=user_id).first()
#         if not user:
#             return jsonify({"error":"User not found"})
         
#         #adding 100 tokens to the user's account
#         user.tokens += 100
#         db.session.commit()
#         return jsonify({"message":"Tokens added successfully", "user_id": user_id, "New_added_tokens": user.tokens}), 200
    
#     except Exception as e:
#         return jsonify({"error": str(e)}),500
@app.route('/add_token', methods=['PUT'])
@cross_origin(
    origins="*",
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)
@jwt_required()
def add_tokens():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        plan_id = data.get("plan_id")

        if not user_id or not plan_id:
            return jsonify({"error": "User ID and Plan ID are required"}), 400

        # Find user
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Find plan
        plan = Plans.query.filter_by(id=plan_id).first()
        if not plan:
            return jsonify({"error": "Plan not found"}), 404

        # Update user's tokens and assign the purchased plan
        user.tokens += plan.plan_tokens
        user.plan_id = plan.id  # Store which plan was purchased
        db.session.commit()

        return jsonify({
            "message": "Plan purchased and tokens added successfully",
            "user_id": user_id,
            "purchased_plan": {
                "plan_id": plan.id,
                "plan_name": plan.plan_name,
                "plan_price": plan.plan_price,
                "plan_tokens": plan.plan_tokens,
                "plan_duration": plan.plan_duration
            },
            "added_tokens": plan.plan_tokens,
            "total_tokens": user.tokens
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

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


    # check human message should not be empty
    if not human_msg:
        return jsonify({"error": "Empty message! Please write something!"}), 400

    # Fetch prompt from DB using image_id
    image_data = ImageData.query.filter_by(id=receiver_id).first()

    # Check if image data exists
    if not image_data :
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

 
@socketio.on("chat_history")
# @jwt_required()  # Protect the event with JWT authentication
def handle_chat_history(data):
    try:
        # If data is a string, parse it into a dictionary
        if isinstance(data, str):
            data = json.loads(data)
        
        print("Received data:", data)  # Log the incoming data to verify the event
        
        # Get user_id and image_id from the incoming data
        user_id = data.get("user_id")
        image_id = data.get("image_id")

        # Check for missing data and emit error
        if not user_id or not image_id:
            emit("chat_history", {"error": "User_id and image_id required"})
            return

        # Fetch the conversation from the database (adjust your query based on your model)
        conversation = Chat_messages.query.filter(
            ((Chat_messages.sender_id == user_id) & (Chat_messages.receiver_id == image_id)) |
            ((Chat_messages.sender_id == image_id) & (Chat_messages.receiver_id == user_id))
        ).order_by(Chat_messages.timestamp).all()

        # Format messages
        messages = [{
            "sender": msg.sender_id,
            "message": msg.message,
            "timestamp": msg.timestamp.isoformat()
        } for msg in conversation]

        # Emit the chat history back to the client
        emit("chat_history", {"messages": messages})

    except Exception as e:
        print("Error handling chat history:", e)
        emit("chat_history", {"error": "An error occurred while fetching the chat history"})

 
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
   

@app.route('/message_count', methods=['GET'])
@cross_origin(
    origins="*",
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)
@jwt_required()
def get_message_count():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    try:
        # Count messages sent by the user
        sent_count = db.session.query(Chat_messages).filter(Chat_messages.sender_id == user_id).count()

        # Count messages received by the user
        received_count = db.session.query(Chat_messages).filter(Chat_messages.receiver_id == user_id).count()

        # Total count (sent or received)
        total_count = db.session.query(Chat_messages).filter(
            or_(Chat_messages.sender_id == user_id, Chat_messages.receiver_id == user_id)
        ).count()

        return jsonify({
            "user_id": user_id,
            "sent_messages": sent_count,
            "received_messages": received_count,
            "total_messages": total_count
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

   # Create a plan
@app.route('/plans', methods=['POST'])
# @cross_origin(
#     origins="*",
#     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
#     supports_credentials=True,
#     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
# )
# @jwt_required()
def add_plan():
    data = request.get_json()

    try:
        new_plan = Plans(
            plan_name=data['plan_name'],
            plan_price=data['plan_price'],
            plan_duration=data['plan_duration'],
            plan_tokens=data['plan_tokens']
        )
        db.session.add(new_plan)
        db.session.commit()
        return jsonify({'message': 'Plan added successfully', 'plan_id': new_plan.id}), 201

    except KeyError as e:
        return jsonify({'error': f'Missing field: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Delete a plan
@app.route('/plans', methods=['DELETE'])
# @cross_origin(
#     origins="*",
#     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
#     supports_credentials=True,
#     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
# )
# @jwt_required()
def delete_plan():
    data = request.get_json()
    plan_id = data.get('plan_id')

    if not plan_id:
        return jsonify({'error': 'Plan ID is required'}), 400
    plan = Plans.query.get(plan_id)
    if not plan:
        return jsonify({'error': 'Plan not found'}), 404

    try:
        db.session.delete(plan)
        db.session.commit()
        return jsonify({'message': 'Plan deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Get all plans
@app.route('/plans', methods=['GET'])
def get_plans():
    plans = Plans.query.all()
    return jsonify([{
        'id': plan.id,
        'plan_name': plan.plan_name,
        'plan_price': plan.plan_price,
        'plan_duration': plan.plan_duration,
        'plan_tokens': plan.plan_tokens
    } for plan in plans]), 200


@app.route('/api/user/usage', methods=['GET'])
def get_user_usage():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not user.plan:
        return jsonify({'error': 'User has not purchased a plan'}), 400

    plan = user.plan

    total_tokens = plan.plan_tokens
    tokens_remaining = user.tokens
    tokens_used = max(0, total_tokens - tokens_remaining)
    token_price = plan.plan_price / total_tokens
    value_used_usd = round(tokens_used * token_price, 2)

    return jsonify({
        'user_id': user.id,
        'user_name': user.name,
        'plan': {
            'plan_id': plan.id,
            'plan_name': plan.plan_name,
            'plan_price': plan.plan_price,
            'plan_duration': plan.plan_duration,
            'plan_tokens': total_tokens
        },
        'tokens_remaining': tokens_remaining,
        'tokens_used': tokens_used,
        'value_used_usd': value_used_usd
    }), 200

if __name__ == "__main__":
    print("Starting server now...")
    socketio.run(app, host='0.0.0.0', port=8001, debug=True)
