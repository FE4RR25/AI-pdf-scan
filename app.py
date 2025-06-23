
import streamlit as st
import pdfplumber
import json
import pandas as pd
import io
import requests

st.title("📄 Intelligente PDF-Rechnungsanalyse mit Hugging Face API (Kostenlos)")

huggingface_api_key = st.text_input("Gib deinen Hugging Face API-Key ein (optional, für mehr Geschwindigkeit):", type="password")

uploaded_files = st.file_uploader("Lade eine oder mehrere PDF-Dateien hoch", accept_multiple_files=True)

# Verlässliches, kostenloses Modell von Hugging Face
model_url = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-alpha"

headers = {"Authorization": f"Bearer {huggingface_api_key}"} if huggingface_api_key else {}

def query_huggingface(prompt):
    payload = {"inputs": prompt}
    response = requests.post(model_url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Status Code {response.status_code}: {response.text}"}

if uploaded_files:
    for uploaded_file in uploaded_files:
        with pdfplumber.open(uploaded_file) as pdf:
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"

        prompt = f"""
Hier ist der vollständige Rechnungs-Text:

{full_text}

Bitte extrahiere folgende Informationen:
- Name des Verkäufers
- Adresse des Verkäufers
- Name des Käufers
- Rechnungsnummer
- Rechnungsdatum
- Alle Positionen (Leistung, Menge, Einzelpreis, Gesamtpreis)
- Zwischensumme
- Mehrwertsteuer
- Gesamtbetrag
- IBAN

Antworte im JSON-Format.
"""

        with st.spinner("Frage kostenloses Hugging Face Modell... Bitte warten..."):
            try:
                result = query_huggingface(prompt)

                if isinstance(result, dict) and "error" in result:
                    st.error(f"Fehler von Hugging Face API: {result['error']}")
                else:
                    try:
                        if isinstance(result, list) and "generated_text" in result[0]:
                            gpt_reply = result[0]["generated_text"]
                        else:
                            gpt_reply = str(result)

                        data = json.loads(gpt_reply)
                        st.success("Daten erfolgreich extrahiert!")

                        # Zeige die extrahierten Daten als JSON
                        st.write("### Extrahierte Daten:")
                        st.json(data)

                        if 'Positionen' in data:
                            df = pd.DataFrame(data['Positionen'])
                            st.write("### Rechnungspositionen")
                            st.write(df)

                            # Excel-Datei zum Download erstellen
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                df.to_excel(writer, index=False)
                            excel_data = output.getvalue()

                            st.download_button(
                                label="📥 Excel-Datei herunterladen",
                                data=excel_data,
                                file_name=f'extrahierte_daten_{uploaded_file.name}.xlsx',
                                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            )

                    except json.JSONDecodeError:
                        st.error("Antwort konnte nicht als JSON gelesen werden. Prüfe das Modell oder den Prompt.")

            except Exception as e:
                st.error(f"Fehler bei der API-Anfrage: {e}")
