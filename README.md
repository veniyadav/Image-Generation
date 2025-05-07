# 🧠 AI Personality Mimic - Backend

This is the backend service for the **AI Personality Mimic** project. It is built with **Flask** and interacts with external AI APIs such as **DeepAI** and **Groq** to generate personality-based responses or media.

---

## 📁 Project Structure

    ai_personality_mimic/
    ├── app.py # Main Flask application
    ├── requirements.txt # Python dependencies
    ├── .env # Environment variables (API keys, secrets)
    ├── utiles/ # Utility scripts and helper functions
    └── README.md

## 🚀 Getting Started

Follow these steps to set up and run the backend server.

### 1. Clone the Repository

    git clone https://github.com/Aditya11-11/personality-mimic.git
    cd ai_personality_mimic

## 2. Set Up a Virtual Environment (Recommended)
    python -m venv venv
    source venv/bin/activate      # On Windows: venv\Scripts\activate
## 3. Install Dependencies
    pip install -r requirements.txt
## 4. Configure Environment Variables
Create a .env file in the backend/ directory and add your API keys:

    DEEPAI_API_KEY=your_deepai_key
    GROQ_API_KEY=your_groq_key
## 5. Run the Flask Server
    app.py

## 6.The server will start at:

    http://localhost:5000


## 📡 API Reference

### 🖼️ POST `/text-to-image`

Generates an image based on the text prompt using the DeepAI API.

#### 🔗 Endpoint


#### 🧾 Request Headers
| Key           | Value               |
|---------------|---------------------|
| `Content-Type` | `application/json`  |

#### 📥 Request Body (JSON)

    {
    "prompt": "a futuristic robot reading a book"
    }

 #### 📤 Response (Success: 200 OK)

    {
    "image_url": "https://api.deepai.org/job-view-file/abcd1234/output.jpg"
    }

#### ❌ Error Responses(400 Bad Request)
    { "error": "Prompt is required" }

#### 500 Internal Server Error
    { "error": "Image generation failed" }

    
### 🖼️ POST `/text-to-image`

Generates an image based on the text prompt using the DeepAI API.

#### 🔗 Endpoint


#### 🧾 Request Headers
| Key           | Value               |
|---------------|---------------------|
| `Content-Type` | `application/json`  |

#### 📥 Request Body (JSON)


    {
    "prompt": "a futuristic robot reading a book"
    }

 #### 📤 Response (Success: 200 OK)

    {
    "image_url": "https://api.deepai.org/job-view-file/abcd1234/output.jpg"
    }

#### ❌ Error Responses(400 Bad Request)
    { "error": "Prompt is required" }

#### 500 Internal Server Error
    { "error": "Image generation failed" }
