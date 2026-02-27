"""UniHelp - Clean version without CSS conflicts."""
import streamlit as st
from pathlib import Path
import sys
import os
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="UniHelp",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state
defaults = {
    'messages': [],
    'vector_store': None,
    'openai_client': None,
    'student_logged_in': False,
    'student': {
        "name": "", "id": "", "year": "1ère année", "specialty": "Informatique",
        "gpa": 0.0, "absences": 0, "max_absences": 15,
        "email": "", "phone": "",
        "eligible_bourse": False, "stage_deadline": "2025-06-30"
    }
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


@st.cache_resource
def get_qdrant_store():
    try:
        from src.qdrant_rest import QdrantRESTClient
        store = QdrantRESTClient()
        if store.get_collection_info()["points_count"] == 0:
            from src.ingest import IngestionPipeline
            with st.spinner("Importation des documents..."):
                IngestionPipeline().ingest_directory("docs/Data")
        return store
    except Exception as e:
        st.error(f"Erreur: {e}")
        return None


@st.cache_resource
def get_openai_client():
    from openai import OpenAI
    key = os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=key) if key else None


def show_login():
    """Login screen."""
    st.markdown("# 👋 Bienvenue sur UniHelp!")
    st.markdown("### Votre assistant IA pour les services universitaires")

    with st.form("login_form"):
        name = st.text_input("Nom complet", placeholder="Ex: Ahmed Ben Ali")
        student_id = st.text_input("Numéro étudiant", placeholder="Ex: 2024001")

        col1, col2 = st.columns(2)
        with col1:
            year = st.selectbox("Année", ["1ère année", "2ème année", "3ème année"])
        with col2:
            specialty = st.selectbox("Spécialité", ["Informatique", "Génie Logiciel", "IA & Data Science"])

        col1, col2 = st.columns(2)
        with col1:
            gpa = st.slider("Moyenne", 0.0, 20.0, 12.0, 0.5)
        with col2:
            absences = st.number_input("Absences", 0, 15, 2)

        if st.form_submit_button("🚀 Commencer", type="primary"):
            if name and student_id:
                st.session_state.student = {
                    "name": name, "id": student_id,
                    "email": f"{name.lower().replace(' ', '.')}@iit.tn",
                    "phone": "+216 XX XXX XXX",
                    "year": year, "specialty": specialty,
                    "gpa": gpa, "absences": absences, "max_absences": 15,
                    "eligible_bourse": gpa >= 14.0,
                    "bourse_amount": "500 TND" if gpa >= 14 else "Non éligible",
                    "stage_deadline": "2025-06-30"
                }
                st.session_state.student_logged_in = True
                st.session_state.messages = []
                st.rerun()


def show_header():
    """Show header with student info."""
    student = st.session_state.student
    cols = st.columns([3, 1])
    with cols[0]:
        st.markdown(f"# 🎓 UniHelp")
        st.caption(f"**{student['name']}** • {student['year']} • {student['specialty']}")
    with cols[1]:
        if st.button("⚙️ Paramètres"):
            for key in ['student_logged_in', 'student', 'messages']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()


def show_chips():
    """Show suggestion chips."""
    st.markdown("### 💡 Comment puis-je vous aider ?")

    chips = [
        "📝 Comment s'inscrire ?", "📜 Demander une attestation",
        "📅 Calendrier des examens", "💰 Montant des bourses",
        "⚠️ Mes absences", "💼 Stage deadline"
    ]

    cols = st.columns(3)
    for i, chip in enumerate(chips):
        with cols[i % 3]:
            if st.button(chip, key=f"chip_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": chip})
                process_action(chip)
                st.rerun()


def process_action(query):
    """Process query and add response."""
    student = st.session_state.student
    q = query.lower()

    if "absence" in q:
        handle_absences(student)
    elif "attestation" in q:
        handle_attestation(student)
    elif "stage" in q:
        handle_stage(student)
    elif "bourse" in q:
        handle_bourses(student)
    else:
        handle_rag(query, student)


def handle_absences(s):
    absences = s['absences']
    pct = (absences / 15) * 100

    emoji = "✅" if pct < 50 else "⚠️" if pct < 75 else "🚨"
    bg = "#dcfce7" if pct < 50 else "#fef3c7" if pct < 75 else "#fee2e2"

    st.markdown(f"""
    <div style='background: {bg}; padding: 1.5rem; border-radius: 1rem; color: #000;'>
        <h3>{emoji} Vos Absences</h3>
        <p><strong>{'Tout va bien!' if pct < 50 else 'Attention!' if pct < 75 else 'Alerte!'}</strong> {pct:.0f}% utilisé</p>
        <div style='display: flex; gap: 2rem;'>
            <span>Utilisées: <strong>{absences}/15</strong></span>
            <span>Restantes: <strong>{15-absences}</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": f"Vos absences: {absences}/15 ({pct:.0f}%)"})

    st.caption("📚 05_absences.txt")


def handle_attestation(s):
    email = f"""Objet: Demande d'Attestation

Madame, Monsieur,

Je soussigné(e), {s['name']}, étudiant en {s['year']} - {s['specialty']},
numéro {s['id']}, vous prie de m'établir une attestation de scolarité.

Cordialement,
{s['name']}"""

    st.success(f"✅ Attestation générée pour {s['name']}")
    with st.expander("📧 Voir l'email"):
        st.code(email)
        if st.button("📋 Copier"):
            st.success("Copié!")

    st.session_state.messages.append({"role": "assistant", "content": f"Attestation prête pour {s['name']}"})
    st.caption("📚 02_certificats.txt")


def handle_stage(s):
    deadline = datetime.strptime(s['stage_deadline'], "%Y-%m-%d")
    days = (deadline - datetime.now()).days

    emoji = "📅" if days > 60 else "⚠️" if days > 30 else "🚨"
    bg = "#dcfce7" if days > 60 else "#fef3c7" if days > 30 else "#fee2e2"

    st.markdown(f"""
    <div style='background: {bg}; padding: 1.5rem; border-radius: 1rem; color: #000;'>
        <h3>{emoji} Deadline Stage</h3>
        <p><strong>{days} jours</strong> restants jusqu'au {s['stage_deadline']}</p>
    </div>
    """, unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": f"Stage: {days} jours restants"})
    st.caption("📚 04_stages.txt")


def handle_bourses(s):
    if s['gpa'] >= 14:
        st.success(f"🎉 Félicitations! Avec {s['gpa']}/20, vous êtes éligible à **500 TND/trimestre**")
        st.session_state.messages.append({"role": "assistant", "content": f"Éligible bourse: 500 TND/trimestre"})
    else:
        need = 14 - s['gpa']
        st.info(f"💰 Votre moyenne: {s['gpa']}/20. Il vous manque {need:.1f} points pour la bourse.")
        st.session_state.messages.append({"role": "assistant", "content": f"Non éligible - Manque {need:.1f} points"})
    st.caption("📚 03_bourses.txt")


def handle_rag(query, student):
    """Handle regular RAG query."""
    store = get_qdrant_store()
    if not store:
        st.error("Vector store non disponible")
        return

    results = store.search(query, limit=3)
    context = "\n".join([r["text"][:400] for r in results])
    sources = list(set([r["metadata"].get("source", "") for r in results]))

    client = get_openai_client()
    if client:
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Réponds simplement et clairement à {student['name']}. Pas de markdown."},
                    {"role": "user", "content": f"Contexte: {context}\nQuestion: {query}"}
                ],
                max_tokens=500
            )
            answer = resp.choices[0].message.content
        except:
            answer = context[:500]
    else:
        answer = context[:500]

    st.info(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
    if sources:
        st.caption(f"📚 {', '.join(sources)}")


def show_chat():
    """Show chat history."""
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div style='text-align: right;'><span style='background: #e0e7ff; padding: 0.5rem 1rem; border-radius: 1rem; color: #000;'>{msg['content']}</span></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background: #f9fafb; padding: 1rem; border-radius: 1rem; margin: 0.5rem 0; color: #000;'>{msg['content']}</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("💬 Posez votre question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        process_action(prompt)
        st.rerun()


def main():
    """Main app."""
    if not st.session_state.student_logged_in:
        show_login()
    else:
        # Initialize
        if not st.session_state.vector_store:
            st.session_state.vector_store = get_qdrant_store()
        if not st.session_state.openai_client:
            st.session_state.openai_client = get_openai_client()

        show_header()
        show_chips()
        st.markdown("---")
        show_chat()

    # Sidebar
    with st.sidebar:
        if st.session_state.student_logged_in:
            s = st.session_state.student
            st.markdown("### 👤 Profil")
            st.metric("Nom", s['name'])
            st.metric("Moyenne", f"{s['gpa']}/20")
            st.metric("Absences", f"{s['absences']}/15")


if __name__ == "__main__":
    main()
