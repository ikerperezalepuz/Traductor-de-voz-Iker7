import requests   # Para hacer peticiones HTTP
import uuid       # Genera IDs únicos
from streamlit import secrets  # Accede a las claves guardadas en Streamlit


def transcribe_audio(audio_bytes, language="en-US"):
    """Transcribe un audio WAV con Azure Speech-to-Text."""

    # Endpoint de Azure Speech (usa tu región configurada)
    endpoint = f"https://{secrets.SPEECH_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"

    # Cabeceras HTTP necesarias para la API
    headers = {
        "Ocp-Apim-Subscription-Key": secrets.SPEECH_KEY,  # Clave de Azure Speech
        "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",  # Tipo de audio
        "X-ClientTraceId": str(uuid.uuid4())  # ID único por petición
    }

    # Parámetro de idioma (ej: en-US, es-ES, fr-FR...)
    params = {"language": language}

    try:
        # Enviar audio a Azure Speech
        response = requests.post(endpoint, headers=headers, params=params, data=audio_bytes)

        # Si la respuesta es correcta (HTTP 200)
        if response.ok:
            result = response.json()
            return result.get("DisplayText", ""), result  # Texto y respuesta completa

        # Si Azure devuelve error
        else:
            return None, {"error": response.status_code, "message": response.text}

    # Error de conexión (por ejemplo, sin internet)
    except requests.exceptions.RequestException as e:
        return None, {"error": "connection", "message": str(e)}
