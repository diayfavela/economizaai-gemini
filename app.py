import os
import base64
import mimetypes
from flask import Flask, request, jsonify
from google.generativeai import GenerativeModel, configure
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# Configuração da API do Gemini
configure(api_key=os.getenv("GEMINI_API_KEY"))
model = GenerativeModel("gemini-1.5-flash")

# Lista de mimeTypes suportados pelo Gemini
SUPPORTED_MIME_TYPES = [
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/heic',
    'image/heif'
]

@app.route("/api/interpretar-cupom", methods=["POST"])
def interpretar_cupom():
    try:
        # Verificar se há uma imagem na requisição
        if 'image' not in request.files:
            return jsonify({"erro": "Nenhuma imagem fornecida."}), 400

        # Ler a imagem da requisição
        image_file = request.files['image']
        if not image_file:
            return jsonify({"erro": "Arquivo de imagem vazio."}), 400

        # Obter o nome do arquivo e inferir o mimeType
        filename = image_file.filename
        mime_type, _ = mimetypes.guess_type(filename)

        # Se o mimeType não puder ser inferido, tentar usar o mimetype fornecido pelo Flask
        if mime_type is None:
            mime_type = image_file.mimetype or 'image/jpeg'  # Fallback para JPEG

        # Validar se o mimeType é suportado pelo Gemini
        if mime_type not in SUPPORTED_MIME_TYPES:
            return jsonify({
                "erro": f"Formato de imagem não suportado: {mime_type}. Tipos suportados: {', '.join(SUPPORTED_MIME_TYPES)}"
            }), 400

        # Ler os bytes da imagem e converter para base64
        image_bytes = image_file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        # Prompt para o Gemini interpretar a imagem
        prompt = """
Você é um assistente especializado em interpretar cupons fiscais brasileiros a partir de imagens. Sua tarefa é extrair informações estruturadas do cupom fiscal presente na imagem fornecida. O cupom contém uma lista de itens com colunas como código, descrição, quantidade, unidade, preço unitário e preço total, além de informações do supermercado (razão social, CNPJ, endereço, data da compra, etc.) e o valor total da compra.

### Instruções:
1. Extraia as informações do supermercado (razão social, CNPJ, endereço, data da compra, etc.).
2. Identifique a categoria como "supermercado".
3. Extraia a lista de produtos, onde cada produto deve ter:
   - "codigo": Código do produto.
   - "produto": Descrição do produto.
   - "quantidade": Quantidade (converta para número).
   - "preco_unitario": Preço unitário (converta para número).
   - "preco_total": Preço total do item (converta para número).
4. Extraia o valor total da compra.
5. Retorne os dados em formato JSON.

### Formato de Saída:
Retorne um JSON com os seguintes campos:
- "categoria": "supermercado"
- "razao_social": Razão social do supermercado
- "nome_fantasia": Nome fantasia (pode ser null se não encontrado)
- "CNPJ": CNPJ do supermercado
- "endereco": Endereço do supermercado
- "data_compra": Data da compra
- "total_compra": Valor total da compra (número)
- "produtos": Lista de produtos, onde cada produto tem:
  - "codigo": string
  - "produto": string
  - "quantidade": número
  - "preco_unitario": número
  - "preco_total": número
"""

        # Enviar a imagem e o prompt ao Gemini
        response = model.generate_content(
            [
                prompt,
                {
                    "mime_type": mime_type,
                    "data": image_base64
                }
            ]
        )

        # Extrair o texto retornado pelo Gemini
        response_text = response.text

        # Remover marcações de markdown, se houver
        cleaned_response = response_text.replace("```json\n", "").replace("```", "").strip()

        # Parsear o JSON retornado pelo Gemini
        import json
        dados_cupom = json.loads(cleaned_response)

        return jsonify(dados_cupom), 200

    except Exception as e:
        print(f"Erro ao interpretar a imagem do cupom: {str(e)}")
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)