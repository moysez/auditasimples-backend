# services/ia.py
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROMPT = """
Você é um especialista tributário brasileiro. 
Diga apenas "SIM" ou "NÃO" se a descrição do produto for de um item monofásico no regime de substituição tributária (bebidas, refrigerantes, cervejas etc.).
"""

def classify_product(description: str) -> bool:
    if not description or len(description) < 3:
        return False

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": f"Descrição: {description}"}
            ],
            max_tokens=3
        )
        result = response.choices[0].message.content.strip().upper()
        return result == "SIM"
    except Exception as e:
        print(f"⚠️ Erro na classificação IA: {e}")
        return False
