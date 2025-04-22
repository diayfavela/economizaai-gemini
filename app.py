from flask import Flask, request, jsonify
import google.generativeai as genai
import base64
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-1.5-flash")


app = Flask(__name__)

@app.route("/api/interpretar-cupom", methods=["POST"])
def interpretar_cupom():
    if "imagem" not in request.files:
        return jsonify({"erro": "Envie uma imagem com o campo 'imagem'"}), 400

    imagem = request.files["imagem"]
    image_bytes = imagem.read()
    image = Image.open(BytesIO(image_bytes))

    prompt = (
        "Esta é uma imagem de um cupom fiscal de supermercado. "
        "Extraia e retorne no seguinte formato JSON: mercado, endereco, data_compra, "
        "total_compra e uma lista de produtos com: produto, quantidade, preco_unitario e preco_total."
    )

    try:
        response = model.generate_content([prompt, image], stream=False)
        return jsonify({"resultado": response.text})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
