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
        print("Enviando imagem para a Gemini...")
        response = model.generate_content([prompt, image], stream=False)
        print("Resposta da Gemini (texto):", response.text)

        # Remover o bloco de markdown (```json ... ```) e extrair apenas o JSON
        texto_resposta = response.text.strip()
        if texto_resposta.startswith("```json"):
            texto_resposta = texto_resposta[7:]  # Remove "```json\n"
        if texto_resposta.endswith("```"):
            texto_resposta = texto_resposta[:-3]  # Remove "```"
        texto_resposta = texto_resposta.strip()

        print("Texto JSON extraído:", texto_resposta)

        # Tente parsear a resposta como JSON
        try:
            dados_cupom = json.loads(texto_resposta)
            # Renomear "lista_de_produtos" para "produtos" para corresponder ao esperado pelo app
            if "lista_de_produtos" in dados_cupom:
                dados_cupom["produtos"] = dados_cupom.pop("lista_de_produtos")
            print("Dados decodificados:", dados_cupom)
            return jsonify(dados_cupom)
        except json.JSONDecodeError as json_error:
            print(f"Erro ao decodificar a resposta JSON: {json_error}")
            return jsonify({"erro": "Erro ao processar a resposta da Gemini: resposta inválida"}), 500

    except Exception as e:
        print(f"Erro ao processar imagem: {e}")
        return jsonify({"erro": str(e)}), 500