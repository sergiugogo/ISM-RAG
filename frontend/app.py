import streamlit as st
import requests
import os

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="ISM RAG demo", page_icon="📘", layout="centered")

st.title("📘 ISM Portfolio")
st.caption("RAG Demo – ISM (Innovative Software & Models SRL)")

# 1️⃣ Upload PDF
st.subheader("📄 Încarcă un document PDF")
uploaded_file = st.file_uploader("Alege fișierul PDF", type=["pdf"])

if uploaded_file:
    st.info(f"Se încarcă fișierul **{uploaded_file.name}** în backend...")
    files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
    response = requests.post(f"{BACKEND_URL}/upload", files=files)

    if response.status_code == 200:
        data = response.json()
        st.success(f"✅ PDF procesat cu succes! {data.get('chunks', 0)} bucăți de text au fost indexate.")
    else:
        st.error(f"Eroare la upload: {response.text}")

# 2️⃣ Întrebare către sistem
st.subheader("💬 Adresează o întrebare despre document")
question = st.text_input("Scrie întrebarea ta:")

if st.button("🔍 Obține răspuns"):
    if not question:
        st.warning("Te rog să introduci o întrebare.")
    else:
        with st.spinner("Se caută răspuns..."):
            response = requests.post(f"{BACKEND_URL}/ask", data={"question": question})
            if response.status_code == 200:
                data = response.json()
                st.markdown(f"### ✅ Răspuns: \n> {data['answer']}")
                with st.expander("📚 Context folosit"):
                    st.text(data["context"])
            else:
                st.error(f"Eroare: {response.text}")
