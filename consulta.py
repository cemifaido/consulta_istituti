import streamlit as st
import pandas as pd
import datetime
import io
import hashlib

# -----------------------------
# 1) SETUP COSTANTI / COLONNE
# -----------------------------
COLONNE = [
    "Tipo Ente",
    "Istituto",
    "POPOLAZIONE CENSITA TOTALE",
    "POPOLAZIONE CENSITA MASCHILE",
    "POPOLAZIONE CENSITA FEMMINILE",
    "POPOLAZIONE RESIDENTE TOTALE",
    "Sito Ufficiale",
    "Email Ufficio Personale/Concorsi",
    "Telefono Ufficio Personale/Concorsi",
    "Link Concorsi/Personale",
    "Responsabile/Segretario"
]

# Per questa demo manteniamo un dizionario utenti {email: hashed_password}
# Ovviamente in un sistema reale potresti volerlo in un DB esterno o in un file CSV.
REGISTERED_USERS = {
    # "test@example.com": hash_password("password123")
}

def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode('utf-8')).hexdigest()

def verify_password(pwd: str, pwd_hash: str) -> bool:
    return hashlib.sha256(pwd.encode('utf-8')).hexdigest() == pwd_hash

# -----------------------------
# 2) GESTIONE DATI
# -----------------------------
def carica_dati_da_excel(uploaded_file):
    """Carica i dati Excel in un DataFrame, aggiunge colonne mancanti e riempie i NaN."""
    df = pd.read_excel(uploaded_file)
    for col in COLONNE:
        if col not in df.columns:
            df[col] = ""
    df.fillna("", inplace=True)
    return df

def salva_dati_in_memory():
    """
    Esempio di salvataggio su un buffer Excel in memoria.
    Poi potrai usare st.download_button per far scaricare il file all'utente.
    """
    buffer = io.BytesIO()
    st.session_state.df.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer

# -----------------------------
# 3) GESTIONE AUTENTICAZIONE
# -----------------------------
def mostra_login():
    """Mostra il form di login e gestisce l'autenticazione utente."""
    st.subheader("Login")
    email = st.text_input("Inserisci la tua email")
    password = st.text_input("Password", type="password")
    
    if st.button("Entra"):
        # Verifica se la mail è in REGISTERED_USERS e se la pwd combacia
        if email in REGISTERED_USERS and verify_password(password, REGISTERED_USERS[email]):
            st.session_state["user"] = email
            st.success("Login effettuato con successo!")
            st.experimental_rerun()
        else:
            st.error("Credenziali non valide, riprova.")

def mostra_registrazione():
    """Mostra il form di registrazione (per scelta password)."""
    st.subheader("Registrazione nuovo utente")
    email = st.text_input("Email")
    password = st.text_input("Scegli una password", type="password")
    confirm_password = st.text_input("Conferma la password", type="password")
    
    if st.button("Registrati"):
        if not email:
            st.warning("Per registrarti devi inserire una email valida.")
            return
        
        if password != confirm_password:
            st.warning("Le password non coincidono.")
            return
        
        if email in REGISTERED_USERS:
            st.warning("Questa email è già registrata.")
            return
        
        # Aggiungiamo l'utente al dizionario
        REGISTERED_USERS[email] = hash_password(password)
        st.success("Registrazione completata! Ora puoi effettuare il login.")

def mostra_area_riservata():
    """La sezione di gestione dei dati, visibile solo a chi è loggato."""
    st.sidebar.write(f"Utente loggato: **{st.session_state['user']}**")
    
    if st.sidebar.button("Logout"):
        st.session_state["user"] = None
        st.experimental_rerun()
    
    st.title("Gestione Enti / Istituti")

    # Se l'utente non ha ancora caricato un file, o se vogliamo consentire il caricamento di un nuovo file:
    if "df" not in st.session_state:
        st.info("Carica un file Excel per iniziare.")
        uploaded_file = st.file_uploader("Carica il file Excel", type=["xlsx", "xls"])
        if uploaded_file is not None:
            st.session_state.df = carica_dati_da_excel(uploaded_file)
            st.success("File caricato con successo.")
            st.experimental_rerun()
        return

    # Mostriamo la parte di consultazione e modifica
    mostra_consulta()
    st.write("---")
    mostra_modifica()

    # Bottone per scaricare l'Excel aggiornato
    buffer = salva_dati_in_memory()
    st.download_button(
        label="Scarica Excel aggiornato",
        data=buffer,
        file_name="enti_aggiornato.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# -----------------------------
# 4) FUNZIONI UI SPECIFICHE (Consulta / Modifica)
# -----------------------------
def mostra_consulta():
    st.subheader("Filtro e Visualizzazione")
    df = st.session_state.df

    query = st.text_input("Cerca per Nome, Email o Telefono (Consulta):")
    if query:
        mask = (
            df["Tipo Ente"].str.contains(query, case=False, na=False) |
            df["Istituto"].str.contains(query, case=False, na=False) |
            df["Email Ufficio Personale/Concorsi"].str.contains(query, case=False, na=False) |
            df["Telefono Ufficio Personale/Concorsi"].astype(str).str.contains(query, case=False, na=False)
        )
        df_filtrato = df[mask]
    else:
        df_filtrato = df

    st.write(f"Numero di record trovati: {len(df_filtrato)}")
    st.dataframe(df_filtrato)

    if not df_filtrato.empty:
        record_sel = st.selectbox("Seleziona un record per il dettaglio", options=[""] + df_filtrato["Istituto"].tolist())
        if record_sel:
            record = df_filtrato[df_filtrato["Istituto"] == record_sel].iloc[0]
            st.markdown("### Dettagli del record")
            for col in COLONNE:
                value = record[col]
                if "link" in col.lower() and isinstance(value, str) and (value.startswith("http://") or value.startswith("https://")):
                    st.markdown(f"**{col}:** [Link]({value})", unsafe_allow_html=True)
                else:
                    st.write(f"**{col}:** {value}")

def mostra_modifica():
    st.subheader("Aggiungi un nuovo Ente")
    with st.form("aggiungi_form"):
        nuovo_istituto = st.text_input("Istituto")
        nuovo_sito = st.text_input("Sito Ufficiale")
        nuovo_email = st.text_input("Email Ufficio Personale/Concorsi")
        nuovo_telefono = st.text_input("Telefono Ufficio Personale/Concorsi")
        nuovo_link = st.text_input("Link Concorsi/Personale")
        nuovo_resp = st.text_input("Responsabile/Segretario")
        submitted_add = st.form_submit_button("Aggiungi Record")
        if submitted_add:
            nuovo_record = {
                "Istituto": nuovo_istituto.strip(),
                "Sito Ufficiale": nuovo_sito.strip(),
                "Email Ufficio Personale/Concorsi": nuovo_email.strip(),
                "Telefono Ufficio Personale/Concorsi": nuovo_telefono.strip(),
                "Link Concorsi/Personale": nuovo_link.strip(),
                "Responsabile/Segretario": nuovo_resp.strip()
            }
            # Aggiungiamo colonne obbligatorie vuote se mancanti
            for c in COLONNE:
                if c not in nuovo_record:
                    nuovo_record[c] = ""
            st.session_state.df = pd.concat(
                [st.session_state.df, pd.DataFrame([nuovo_record])],
                ignore_index=True
            )
            st.success("Nuovo record aggiunto.")

    st.write("---")
    st.subheader("Modifica o Cancella un Ente")
    df = st.session_state.df
    search_ente = st.text_input("Filtra elenco enti (Modifica):")
    enti_unici = df["Istituto"].unique().tolist()
    filtered_enti = [e for e in enti_unici if search_ente.lower() in e.lower()] if search_ente else enti_unici

    selezionato = st.selectbox("Seleziona un Ente da modificare/cancellare:", options=[""] + filtered_enti)
    if selezionato:
        idx = df[df["Istituto"] == selezionato].index
        if len(idx) == 0:
            st.warning("Nessuna riga trovata per questo Ente.")
        else:
            idx = idx[0]
            with st.form("modifica_form"):
                ed_istituto = st.text_input("Istituto", value=df.at[idx, "Istituto"])
                ed_sito = st.text_input("Sito Ufficiale", value=df.at[idx, "Sito Ufficiale"])
                ed_email = st.text_input("Email Ufficio Personale/Concorsi", value=df.at[idx, "Email Ufficio Personale/Concorsi"])
                ed_telefono = st.text_input("Telefono Ufficio Personale/Concorsi", value=str(df.at[idx, "Telefono Ufficio Personale/Concorsi"]))
                ed_link = st.text_input("Link Concorsi/Personale", value=df.at[idx, "Link Concorsi/Personale"])
                ed_resp = st.text_input("Responsabile/Segretario", value=df.at[idx, "Responsabile/Segretario"])
                submitted_edit = st.form_submit_button("Salva Modifiche")
                if submitted_edit:
                    st.session_state.df.at[idx, "Istituto"] = ed_istituto.strip()
                    st.session_state.df.at[idx, "Sito Ufficiale"] = ed_sito.strip()
                    st.session_state.df.at[idx, "Email Ufficio Personale/Concorsi"] = ed_email.strip()
                    st.session_state.df.at[idx, "Telefono Ufficio Personale/Concorsi"] = ed_telefono.strip()
                    st.session_state.df.at[idx, "Link Concorsi/Personale"] = ed_link.strip()
                    st.session_state.df.at[idx, "Responsabile/Segretario"] = ed_resp.strip()
                    st.success("Record modificato.")

            if st.button("Cancella questo record"):
                st.session_state.df.drop(idx, inplace=True)
                st.session_state.df.reset_index(drop=True, inplace=True)
                st.success("Record cancellato.")

# -----------------------------
# 5) MAIN
# -----------------------------
def main():
    st.set_page_config(page_title="Gestione Enti ed istituti", layout="wide")

    # Verifica se l'utente è loggato
    if "user" not in st.session_state or not st.session_state["user"]:
        # Se non è loggato, mostriamo la possibilità di login o registrazione
        scelta = st.sidebar.selectbox("Autenticazione", ["Login", "Registrazione"])
        if scelta == "Login":
            mostra_login()
        elif scelta == "Registrazione":
            mostra_registrazione()
    else:
        # Se è loggato, mostriamo l'area riservata con CRUD
        mostra_area_riservata()

if __name__ == "__main__":
    main()
