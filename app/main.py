import streamlit as st
import pandas as pd
import io
from services import speech, translator

# === Idiomas destino disponibles ===
IDIOMAS_DESTINO = {
    "Inglés": "en",
    "Español": "es",
    "Francés": "fr",
    "Alemán": "de",
    "Italiano": "it",
    "Portugués": "pt",
    "Japonés": "ja",
    "Chino": "zh-Hans",
    "Árabe": "ar"
}

# === Configuración ===
st.set_page_config(page_title="🎙️ Transcriptor Pro", layout="centered")
st.title("🎙️ WAV → Texto → Traducción + Voz 🌐")
st.write("Sube un archivo `.wav` para transcribir, traducir, generar voz y guardar todo en tu historial 🪄")

# === Estado global (historial en memoria) ===
if "historial" not in st.session_state:
    st.session_state.historial = []

# === Subida de archivo ===
uploaded_file = st.file_uploader("📂 Sube un archivo WAV", type=["wav"])

# === Selección de idioma destino ===
idioma_destino_label = st.selectbox(
    "🌍 Idioma al que traducir:",
    options=list(IDIOMAS_DESTINO.keys()),
    index=0
)
idioma_destino = IDIOMAS_DESTINO[idioma_destino_label]

IDIOMA_BASE_TRANSCRIPCION = "es-ES"  # por defecto español

if uploaded_file is not None:
    st.audio(uploaded_file, format="audio/wav")

    if st.button("🪄 Transcribir, traducir y guardar"):
        with st.spinner("🎧 Procesando audio... ⏳"):
            audio_data = uploaded_file.read()

            # --- 1️⃣ Transcripción con timestamps ---
            texto_transcrito, result_speech = speech.transcribe_audio(audio_data,
            language=IDIOMA_BASE_TRANSCRIPCION)

            if texto_transcrito:
                st.success("✅ Transcripción completada")
                st.text_area("Texto reconocido:", texto_transcrito, height=200)

                # --- 2️⃣ Detección de idioma ---
                idioma_detectado, result_detect = translator.detect_language(texto_transcrito)
                if idioma_detectado:
                    st.info(f"🌍 Idioma detectado: **{idioma_detectado}**")

                # --- 3️⃣ Subtítulos con timestamps ---
                # Si el servicio devuelve timestamps, los mostramos
                if "segments" in result_speech:
                    st.markdown("### ⏱️ Subtítulos con timestamps")
                    subs = []
                    for seg in result_speech["segments"]:
                        start = seg.get("offset", 0) / 10_000_000  # ticks → segundos
                        end = start + (seg.get("duration", 0) / 10_000_000)
                        text = seg.get("text", "")
                        subs.append({
                            "Inicio (s)": round(start, 2),
                            "Fin (s)": round(end, 2),
                            "Texto": text
                        })
                    df_subs = pd.DataFrame(subs)
                    st.dataframe(df_subs, hide_index=True, use_container_width=True)
                else:
                    st.warning("⚠️ No se devolvieron timestamps en la transcripción.")

                # --- 4️⃣ Traducción + síntesis ---
                traduccion, archivo_tts, result_translation = translator.translate_and_tts_azure(
                    texto_transcrito,
                    to_lang=idioma_destino
                )

                if traduccion:
                    st.success(f"🌐 Traducción al {idioma_destino_label}:")
                    st.text_area("Texto traducido:", traduccion, height=200)
                    if archivo_tts:
                        st.audio(archivo_tts, format="audio/mp3")

                    # --- 5️⃣ Guardar en historial ---
                    st.session_state.historial.append({
                        "Archivo": uploaded_file.name,
                        "Texto original": texto_transcrito,
                        "Idioma detectado": idioma_detectado,
                        "Idioma destino": idioma_destino_label,
                        "Traducción": traduccion
                    })
                else:
                    st.error("❌ Error en traducción.")
                    st.json(result_translation)
            else:
                st.error("❌ Error en transcripción.")
                st.json(result_speech)

# === 6️⃣ Mostrar historial y permitir descarga ===
if st.session_state.historial:
    st.markdown("## 📜 Historial de transcripciones")
    #Convierte el historial en una tabla (DataFrame) y lo muestra
    #en pantalla para que el usuario vea todas las transcripciones hechas.
    df_hist = pd.DataFrame(st.session_state.historial)
    st.dataframe(df_hist, use_container_width=True)

    # Botón de descarga CSV: Permite descargar el historial completo en formato CSV,
    # con todas las transcripciones y traducciones realizadas.
    buffer = io.StringIO()
    df_hist.to_csv(buffer, index=False, encoding="utf-8")
    st.download_button(
        label="⬇️ Descargar historial en CSV",
        data=buffer.getvalue(),
        file_name="historial_transcripciones.csv",
        mime="text/csv"
    )
