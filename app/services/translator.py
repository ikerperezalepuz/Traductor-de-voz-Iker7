import requests
from streamlit import secrets

# Mapeo de idiomas a voces compatibles en Azure Neural TTS
VOICE_MAP = {
    "en": "en-US-AriaNeural",
    "es": "es-ES-ElviraNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "it": "it-IT-ElsaNeural",
    "pt": "pt-BR-FranciscaNeural",
}

# Mapeo para el atributo xml:lang en SSML (debe coincidir con la voz)
LANG_SSML_MAP = {
    "en": "en-US",
    "es": "es-ES",
    "fr": "fr-FR",
    "de": "de-DE",
    "it": "it-IT",
    "pt": "pt-BR",
}


def detect_language(text):
    """
    Detecta automáticamente el idioma de un texto usando Azure Translator.
    """
    endpoint = "https://api.cognitive.microsofttranslator.com/detect"
    headers = {
        "Ocp-Apim-Subscription-Key": secrets.TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": secrets.TRANSLATOR_REGION,
        "Content-Type": "application/json"
    }
    body = [{"text": text}]

    try:
        resp = requests.post(endpoint, headers=headers, params={"api-version": "3.0"}, json=body)
        resp.raise_for_status()
        result = resp.json()
        lang = result[0]["language"]
        return lang, result
    except requests.exceptions.RequestException as e:
        return None, {"error": "detect_connection", "message": str(e)}


def translate_and_tts_azure(text, to_lang="en", output_file="translation.mp3"):
    """
    Traduce un texto usando Azure Translator y genera TTS en MP3 usando Azure Speech Service.
    Detecta automáticamente el idioma de origen.
    """
    if not text.strip():
        return None, None, {"error": "empty_text", "message": "El texto está vacío."}

    # --- 1️⃣ Detectar idioma de origen ---
    detect_endpoint = "https://api.cognitive.microsofttranslator.com/detect"
    detect_headers = {
        "Ocp-Apim-Subscription-Key": secrets.TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": secrets.TRANSLATOR_REGION,
        "Content-Type": "application/json"
    }
    detect_body = [{"text": text}]
    try:
        detect_resp = requests.post(detect_endpoint, headers=detect_headers, params={"api-version": "3.0"},
        json=detect_body)
        detect_resp.raise_for_status()
        from_lang = detect_resp.json()[0]["language"]
    except requests.exceptions.RequestException as e:
        return None, None, {"error": "detect_connection", "message": str(e)}

    # --- 2️⃣ Traducir texto ---
    translate_endpoint = "https://api.cognitive.microsofttranslator.com/translate"
    translate_headers = {
        "Ocp-Apim-Subscription-Key": secrets.TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": secrets.TRANSLATOR_REGION,
        "Content-Type": "application/json"
    }
    # Claves de autenticación y tipo de contenido
    translate_params = {"api-version": "3.0", "from": from_lang, "to": [to_lang]}
    # Idiomas de origen y destino para la traducción
    translate_body = [{"text": text}] # Texto que se va a traducir
    # Envía el texto a la API de Azure Translator
    try:
        resp = requests.post(translate_endpoint, headers=translate_headers, params=translate_params, 
        json=translate_body)
        resp.raise_for_status()     # Si hay error HTTP (como 401 o 400) lanza excepción
        # Convierte la respuesta en JSON y extrae la traducción    
        result = resp.json()
        translation = result[0]["translations"][0]["text"]
    except requests.exceptions.RequestException as e:
        return None, None, {"error": "translation_connection", "message": str(e)}

    # --- 3️⃣ Generar audio con TTS ---
    voice = VOICE_MAP.get(to_lang, "en-US-AriaNeural") # Obtiene el nombre de la voz según el idioma destino
    ssml_lang = LANG_SSML_MAP.get(to_lang, "en-US") # Obtiene el código del idioma en formato SSML

# Endpoint del servicio Azure Text-to-Speech (TTS)
    tts_endpoint = f"https://{secrets.SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1" 
    tts_headers = {
        "Ocp-Apim-Subscription-Key": secrets.SPEECH_KEY,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3"
    }
# Crea el contenido SSML (Speech Synthesis Markup Language)
# Es un formato XML que indica qué texto se debe hablar, en qué idioma y con qué voz.
    ssml = f"""
    <speak version='1.0' xml:lang='{ssml_lang}'>
        <voice name='{voice}'>{translation}</voice>
    </speak>
    """.strip()

    # Envía la petición POST al servicio Text-to-Speech de Azure con el texto SSML
    try:
        tts_resp = requests.post(tts_endpoint, headers=tts_headers, data=ssml.encode("utf-8"))
        tts_resp.raise_for_status()
        with open(output_file, "wb") as f:  # Guarda el audio generado por Azure en un archivo local (formato MP3)
            f.write(tts_resp.content)
    except requests.exceptions.RequestException as e:
        return translation, None, {"error": "tts_connection", "message": str(e)}
    
# Si todo salió bien: devuelve el texto traducido, el archivo de audio y None (sin error)
    return translation, output_file, None  # último valor es error_info (None = éxito)
