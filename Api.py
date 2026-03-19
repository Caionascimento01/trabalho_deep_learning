import streamlit as st
from transformers import pipeline
from pypdf import PdfReader

st.set_page_config(page_title="Smart Document Analyzer", layout="centered")

st.title("📄 Smart Document Analyzer")

# ------------------------
# Carregar modelos
# ------------------------
@st.cache_resource
def load_models():
    try:
        summarizer_pipeline = pipeline(
            "summarization",
            model="csebuetnlp/mT5_multilingual_XLSum"
        )

        classifier_pipeline = pipeline(
            "zero-shot-classification",
            model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
        )

        return summarizer_pipeline, classifier_pipeline

    except Exception as e:
        st.error(f"Erro ao carregar modelos: {e}")
        return None, None

summarizer, classifier = load_models()

# 🚨 Validação importante
if summarizer is None or classifier is None:
    st.stop()

# ------------------------
# Função para ler arquivos
# ------------------------
def read_file(uploaded_file):
    try:
        if uploaded_file.type == "text/plain":
            return str(uploaded_file.read(), "utf-8")

        elif uploaded_file.type == "application/pdf":
            pdf = PdfReader(uploaded_file)
            text = "".join(page.extract_text() or "" for page in pdf.pages)
            return text

    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        return ""

    return ""

# ------------------------
# Histórico
# ------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# ------------------------
# Entrada
# ------------------------
uploaded_file = st.file_uploader("Envie um arquivo (.txt ou .pdf)", type=["txt", "pdf"])
manual_text = st.text_area("Ou cole um texto manualmente:")

text = ""
if uploaded_file:
    text = read_file(uploaded_file)
elif manual_text:
    text = manual_text

# ------------------------
# Processamento
# ------------------------
if st.button("Analisar"):
    if text.strip():

        with st.spinner("A IA está analisando o documento..."):

            text_to_process = text[:2000]

            # -------- Resumo --------
            try:
                summary = summarizer(
                    text_to_process,
                    max_length=130,
                    min_length=30,
                    do_sample=False
                )[0]['summary_text']
            except Exception:
                summary = "Não foi possível gerar o resumo."

            # -------- Classificação --------
            try:
                labels = ["tecnologia", "educação", "negócios", "saúde", "ciência"]
                result = classifier(text_to_process, labels)

                top_labels = result['labels'][:3]
                top_scores = result['scores'][:3]

            except Exception as e:
                st.error(f"Erro na classificação: {e}")
                top_labels, top_scores = [], []

        # -------- Exibição --------
        st.subheader("📌 Resumo")
        st.write(summary)

        if top_labels:
            st.subheader("🏷️ Top 3 Tópicos")
            for label, score in zip(top_labels, top_scores):
                st.write(f"**{label.capitalize()} — {score:.2%}**")
                st.progress(float(score))

        # -------- Histórico --------
        st.session_state.history.append({
            "resumo": summary,
            "topicos": list(zip(top_labels, top_scores)),
            "preview": text[:200]
        })

    else:
        st.warning("Por favor, forneça um texto ou envie um arquivo válido.")

# ------------------------
# Histórico
# ------------------------
st.divider()
st.subheader("🕓 Histórico de Análises")

if st.session_state.history:
    for i, item in enumerate(reversed(st.session_state.history), 1):
        with st.expander(f"Análise {i}"):

            st.caption(item["preview"])

            st.markdown("**Resumo:**")
            st.write(item["resumo"])

            st.markdown("**Tópicos:**")
            for label, score in item["topicos"]:
                st.write(f"- {label.capitalize()}: {score:.2%}")
else:
    st.info("Nenhuma análise realizada ainda.")

# ------------------------
# Aviso final
# ------------------------
st.caption("⚠️ Este sistema utiliza modelos de IA pré-treinados e pode apresentar imprecisões.")