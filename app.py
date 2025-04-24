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
    "Extraia e retorne no seguinte formato JSON:\n"
    "- categoria (ex: supermercado, farmácia, etc — este campo é obrigatório e deve vir primeiro)\n"
    "- razao_social\n"
    "- nome_fantasia (se houver)\n"
    "- CNPJ\n"
    "- endereco\n"
    "- data_compra\n"
    "- total_compra\n"
    "- lista de produtos com os campos: codigo (EAN/GTIN, se visível), produto, quantidade, preco_unitario, preco_total.\n\n"
    "Para determinar a categoria, siga esta lógica:\n"
    "- Priorize o nome do estabelecimento (ex: Assaí, Drogasil, Boticário, etc.)\n"
    "- Use os tipos de produtos apenas como apoio secundário.\n"
    "- Mesmo que o cupom contenha itens variados, se for de um supermercado, classifique como 'supermercado'.\n"
    "- Nunca retorne múltiplas categorias. Sempre escolha uma única categoria principal com base no local da compra.\n\n"
    "⚠️ Importante: se não souber o nome fantasia, deixe o campo como null. Mas nunca deixe de preencher a categoria."
)

    try:
        response = model.generate_content([prompt, image], stream=False)
        return jsonify({"resultado": response.text})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
