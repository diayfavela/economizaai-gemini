from flask import Flask, request, jsonify
import google.generativeai as genai
import base64
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Configura a API do Gemini com a chave gerada
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# Cria a aplicação Flask
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
        # Tentando gerar a resposta do modelo Gemini
        print(f"Enviando imagem e prompt ao modelo Gemini...")
        response = model.generate_content([prompt, image], stream=False)
        print(f"Resposta do Gemini: {response.text}")

        # Converte a string JSON retornada pelo Gemini em um objeto Python
        dados_cupom = json.loads(response.text)
        
        # Log para ver os dados recebidos
        print(f"Dados do cupom decodificados: {dados_cupom}")
        
        return jsonify(dados_cupom)

    except Exception as e:
        # Captura qualquer erro e retorna um erro 500 com a descrição
        print(f"Erro ao processar a imagem: {e}")
        return jsonify({"erro": f"Erro ao processar a imagem: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
