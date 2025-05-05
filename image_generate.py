from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

API_TOKEN= '41803036-2c67-4e62-8c34-a42b47ef7860'
APP_URL="https://api.deepai.org/api/text2img"

@app.route('/text-to-image', methods=['POST'])
def generate_image():
    try:
        #get prompt from the request
        prompt=request.get('prompt')
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        #make api request
        response = requests.post(
            APP_URL,
            headers={"api-key": API_TOKEN,
                     "Content-type": "application/json"},
            data ={"text": prompt})
  
        #parse the api response
        try:
            result = response.json()
        except ValueError:
            return jsonify({"error": "Invalid response from the API"}), 500

        #check if the response contains the expexted fields
        if 'output_url' in result:
            return jsonify({"image_url": result['output_url']}), 200
        else:
            return jsonify({"error": "Image generation failed"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
