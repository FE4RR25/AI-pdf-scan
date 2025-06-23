
import streamlit as st
import pdfplumber
import openai
import json
import pandas as pd
import io

st.title("📄 Intelligente PDF-Rechnungsanalyse mit KI")

# OpenAI API-Key Eingabe
api_key = st.text_input("Gib deinen OpenAI API-Key ein:", type="password")

uploaded_files = st.file_uploader("Lade eine oder mehrere PDF-Dateien hoch", accept_multiple_files=True)

if uploaded_files and api_key:
    extracted_data = []

    for uploaded_file in uploaded_files:
        with pdfplumber.open(uploaded_file) as pdf:
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"

        # GPT-4 Abfrage
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

        with st.spinner("Frage GPT-4... Bitte warten..."):
            try:
                client = openai.OpenAI(api_key=api_key)

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0
                )

                gpt_reply = response.choices[0].message.content

                try:
                    data = json.loads(gpt_reply)
                    st.success("Daten erfolgreich extrahiert!")

                    # Zeige die extrahierten Daten als JSON
                    st.write("### Extrahierte Daten:")
                    st.json(data)

                    # Falls Positionen vorhanden sind, zeige diese als Tabelle
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
                    st.error("Antwort von GPT konnte nicht als JSON gelesen werden. Überprüfe den Prompt oder die API-Antwort.")

            except Exception as e:
                st.error(f"Fehler bei der API-Anfrage: {e}")
