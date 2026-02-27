"""UniHelp Streamlit App - Dynamic & Interactive."""
import streamlit as st
from pathlib import Path
import sys
import os
from datetime import datetime, timedelta
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="UniHelp - Assistant Universitaire",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #000000;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        text-align: center;
        margin-bottom: 1.5rem;
    }

    /* Dynamic suggestion chips */
    .suggestion-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 0.75rem;
        margin: 1rem 0;
    }
    .suggestion-chip {
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 1rem;
        color: white;
        text-align: center;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        font-size: 0.95rem;
    }
    .suggestion-chip:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }

    /* Animated typing indicator */
    .typing-indicator {
        display: inline-flex;
        gap: 4px;
        padding: 8px 16px;
    }
    .typing-indicator span {
        width: 8px;
        height: 8px;
        background: #667eea;
        border-radius: 50%;
        animation: bounce 1.4s infinite;
    }
    .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
    .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes bounce {
        0%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-8px); }
    }

    /* Action cards with animations - BLACK TEXT */
    .action-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        animation: slideIn 0.3s ease-out;
        color: #000000;
    }
    .action-card * {
        color: #000000 !important;
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }

    /* Countdown styles - BLACK TEXT */
    .countdown-success {
        background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 0.5rem 0;
        color: #000000;
    }
    .countdown-success * {
        color: #000000 !important;
    }
    .countdown-warning {
        background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 0.5rem 0;
        color: #000000;
    }
    .countdown-warning * {
        color: #000000 !important;
    }
    .countdown-danger {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 0.5rem 0;
        color: #000000;
    }
    .countdown-danger * {
        color: #000000 !important;
    }

    /* Ensure all markdown content is black */
    .stMarkdown, .stMarkdown * {
        color: #000000;
    }

    /* Welcome input section */
    .welcome-section {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 1.5rem;
        margin-bottom: 2rem;
        color: white;
    }

    /* Ensure ALL text is readable */
    h1, h2, h3, h4, h5, h6, p, span, div, li, td, th {
        color: inherit !important;
    }

    /* Black text on light backgrounds */
    .stMarkdown, .stChatMessageContent {
        color: #000000 !important;
    }
    .stMarkdown strong, .stMarkdown b {
        color: #000000 !important;
    }

    /* White text on dark/colored backgrounds */
    .countdown-success, .countdown-warning, .countdown-danger,
    .action-card, .welcome-section {
        color: #000000 !important;
    }
    .countdown-success *, .countdown-warning *, .countdown-danger *,
    .action-card *, .welcome-section * {
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)


# Default student data (overridden by user input)
DEFAULT_STUDENT = {
    "name": "",
    "id": "",
    "year": "1ère année",
    "specialty": "Informatique",
    "gpa": 0.0,
    "absences": 0,
    "max_absences": 15,
}

# Suggestion chips with icons and colors
SUGGESTION_CHIPS = [
    {"emoji": "📝", "text": "Comment s'inscrire ?", "gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"},
    {"emoji": "📜", "text": "Demander une attestation", "gradient": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"},
    {"emoji": "📅", "text": "Calendrier des examens", "gradient": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"},
    {"emoji": "💰", "text": "Montant des bourses", "gradient": "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)"},
    {"emoji": "⚠️", "text": "Mes absences", "gradient": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)"},
    {"emoji": "💼", "text": "Stage deadline", "gradient": "linear-gradient(135deg, #30cfd0 0%, #330867 100%)"},
    {"emoji": "💳", "text": "Paiement des frais", "gradient": "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)"},
    {"emoji": "🔄", "text": "Session de rattrapage", "gradient": "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)"},
]


# Initialize Qdrant client
@st.cache_resource
def get_qdrant_store():
    """Initialize Qdrant vector store."""
    try:
        from src.qdrant_rest import QdrantRESTClient
        store = QdrantRESTClient()
        info = store.get_collection_info()
        if info["points_count"] == 0:
            from src.ingest import IngestionPipeline
            with st.spinner("Importation des documents..."):
                pipeline = IngestionPipeline()
                result = pipeline.ingest_directory("docs/Data")
                st.success(f"✅ {result['files_processed']} documents importés!")
        return store
    except Exception as e:
        st.error(f"Erreur: {e}")
        return None


@st.cache_resource
def get_openai_client():
    """Initialize OpenAI client."""
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=api_key) if api_key else None


def init_session_state():
    """Initialize session state."""
    defaults = {
        'messages': [],
        'vector_store': None,
        'openai_client': None,
        'student_logged_in': False,
        'student': DEFAULT_STUDENT.copy(),
        'generated_actions': []
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def display_header():
    """Display header."""
    if st.session_state.student_logged_in:
        student = st.session_state.student
        st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center;'>
        <div>
            <div style='font-size: 2rem; font-weight: bold; color: #000; margin: 0;'>🎓 UniHelp</div>
            <div style='font-size: 1rem; color: #333; margin: 0.25rem 0;'>
                Bonjour, <strong style='color: #000;'>{student['name']}</strong> • {student['year']} • {student['specialty']}
            </div>
        </div>
        <div style='text-align: right;'>
            <span style='padding: 0.5rem 1rem; border: 1px solid #e5e7eb; background: white; border-radius: 0.5rem; color: #000;'>
                ⚙️ Paramètres
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-size: 2.5rem; font-weight: bold; color: #000; text-align: center;'>🎓 UniHelp</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 1.2rem; color: #666; text-align: center;'>Assistant IA pour les services universitaires - IIT / NAU</div>", unsafe_allow_html=True)

    st.markdown("---")


def show_welcome_screen():
    """Show welcome/login screen."""
    st.markdown("""
    <div class='welcome-section'>
        <h1 style='margin: 0;'>👋 Bienvenue sur UniHelp!</h1>
        <p style='font-size: 1.1rem; margin: 1rem 0;'>Votre assistant IA pour tous vos besoins universitaires</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        st.markdown("### 🎓 Identifiez-vous")
        name = st.text_input("Nom complet", placeholder="Ex: Ahmed Ben Ali")
        student_id = st.text_input("Numéro étudiant", placeholder="Ex: 2024001")

        col_year, col_spec = st.columns(2)
        with col_year:
            year = st.selectbox("Année", ["1ère année", "2ème année", "3ème année"])
        with col_spec:
            specialty = st.selectbox("Spécialité", ["Informatique", "Génie Logiciel", "Réseaux", "IA & Data Science", "Génie Industriel"])

        col_gpa, col_abs = st.columns(2)
        with col_gpa:
            gpa = st.slider("Moyenne générale", 0.0, 20.0, 12.0, 0.5)
        with col_abs:
            absences = st.number_input("Absences ce semestre", 0, 15, 2)

        if st.button("🚀 Commencer", type="primary", use_container_width=True):
            if name and student_id:
                # Clear previous messages from other sessions
                st.session_state.messages = []

                st.session_state.student = {
                    "name": name,
                    "id": student_id,
                    "email": f"{name.lower().replace(' ', '.')}@iit.tn",
                    "phone": "+216 XX XXX XXX",
                    "year": year,
                    "specialty": specialty,
                    "gpa": gpa,
                    "absences": absences,
                    "max_absences": 15,
                    "eligible_bourse": gpa >= 14.0,
                    "bourse_amount": "500 TND/trimestre" if gpa >= 14.0 else "Non éligible",
                    "documents_requested": 0,
                    "documents_pending": 0,
                    "stage_status": "Non commencé",
                    "stage_deadline": "2025-06-30",
                }
                st.session_state.student_logged_in = True
                st.rerun()
            else:
                st.warning("Veuillez remplir votre nom et numéro étudiant")


def render_suggestion_chips():
    """Render clickable suggestion chips."""
    if not st.session_state.student_logged_in:
        st.markdown("### 💡 Connectez-vous pour commencer")
        st.info("👆 Remplissez le formulaire en haut pour accéder à l'assistant")
        return

    st.markdown("### 💡 Que puis-je vous aider ?")

    cols = st.columns(4)
    for i, chip in enumerate(SUGGESTION_CHIPS):
        with cols[i % 4]:
            if st.button(
                f"{chip['emoji']} {chip['text']}",
                key=f"chip_{chip['emoji']}",
                use_container_width=True
            ):
                # Add user message
                st.session_state.messages.append({"role": "user", "content": chip['text']})

                # Process the query and get response
                process_query_and_respond(chip['text'])

                st.rerun()


def process_query_and_respond(query: str):
    """Process query and add assistant response to messages."""
    # Check if student is logged in
    if not st.session_state.student_logged_in:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "👋 Veuillez d'abord vous identifier en haut de la page pour que je puisse vous aider personnellement!"
        })
        return

    student = st.session_state.student

    # Detect action
    query_lower = query.lower()
    action = None

    if "absence" in query_lower or "mes absences" in query_lower:
        action = "absences"
    elif "attestation" in query_lower or "certificat" in query_lower:
        action = "attestation"
    elif "stage" in query_lower:
        action = "stage"
    elif "bourse" in query_lower:
        action = "bourses"
    elif "inscription" in query_lower or "s'inscrire" in query_lower:
        action = "inscription"
    elif "calendrier" in query_lower or "examen" in query_lower:
        action = "calendrier"
    elif "paiement" in query_lower or "frais" in query_lower:
        action = "paiement"
    elif "rattrapage" in query_lower:
        action = "rattrapage"

    # Handle actions
    if action == "absences":
        handle_absences_action(student)
        return

    if action == "attestation":
        handle_attestation_action(student)
        return

    if action == "stage":
        handle_stage_action(student)
        return

    if action == "bourses":
        handle_bourses_action(student)
        return

    # Regular RAG search
    store = st.session_state.vector_store or get_qdrant_store()
    if store:
        results = store.search(query, limit=3)
        context = "\n\n".join([r["text"][:500] for r in results])
        sources = list(set([r["metadata"].get("source", "Doc") for r in results]))
    else:
        context = ""
        sources = []

    client = get_openai_client()
    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Tu es UniHelp, assistant de l'IIT. L'étudiant est {student['name']}, en {student['year']}. Réponds de manière simple et claire, sans utiliser de markdown (pas de **, pas de ###)."},
                    {"role": "user", "content": f"CONTEXTE:\n{context}\n\nQUESTION: {query}"}
                ],
                max_tokens=600
            )
            answer = response.choices[0].message.content
        except:
            answer = context[:600] if context else "Service indisponible."
    else:
        answer = context[:600] if context else "Connectez OpenAI."

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })


def process_query(query: str):
    """Process user query from chat input."""
    process_query_and_respond(query)


def handle_absences_action(student):
    """Handle absences with dynamic countdown."""
    absences = student['absences']
    max_abs = student['max_absences']
    percentage = (absences / max_abs) * 100
    remaining = max_abs - absences

    if percentage < 50:
        emoji = "✅"
        msg = f"Tout va bien! Vous n'avez utilisé que {percentage:.0f}% de vos absences."
    elif percentage < 75:
        emoji = "⚠️"
        msg = f"Attention: {percentage:.0f}% utilisé. Il vous reste {remaining} absences."
    else:
        emoji = "🚨"
        msg = f"Alerte! Plus que {remaining} absences avant élimination!"

    # Use streamlit components instead of markdown text
    answer_data = {
        "emoji": emoji,
        "message": msg,
        "absences": f"{absences}/{max_abs}",
        "percentage": f"{percentage:.1f}%",
        "remaining": str(remaining)
    }

    st.session_state.messages.append({
        "role": "assistant",
        "content": msg,
        "sources": ["05_absences.txt"],
        "action": "absences",
        "style": "countdown-success" if percentage < 50 else "countdown-warning" if percentage < 75 else "countdown-danger",
        "data": answer_data
    })


def handle_attestation_action(student):
    """Handle attestation with generated email."""
    email_body = f"""Objet: Demande d'Attestation de Scolarité

Madame, Monsieur,

Je soussigné(e), {student['name']}, étudiant(e) en {student['year']} - {student['specialty']},
numéro {student['id']}, vous prie de bien vouloir m'établir une attestation de scolarité
pour l'année universitaire 2024-2025.

Je vous remercie par avance pour votre attention.

Cordialement,

{student['name']}
Étudiant en {student['year']}
Email: {student['email']}"""

    st.session_state.messages.append({
        "role": "assistant",
        "content": f"Attestation prête pour {student['name']} • {student['id']}",
        "sources": ["02_certificats.txt"],
        "action": "attestation",
        "email": email_body,
        "student_name": student['name']
    })


def handle_stage_action(student):
    """Handle stage deadline with countdown."""
    deadline = datetime.strptime(student['stage_deadline'], "%Y-%m-%d")
    days_left = (deadline - datetime.now()).days

    if days_left > 60:
        emoji = "📅"
        bg = "countdown-success"
        msg = f"Vous avez {days_left} jours devant vous!"
    elif days_left > 30:
        emoji = "⚠️"
        bg = "countdown-warning"
        msg = f"{days_left} jours restants. Commencez à chercher!"
    else:
        emoji = "🚨"
        bg = "countdown-danger"
        msg = f"Urgent! Seulement {days_left} jours!"

    st.session_state.messages.append({
        "role": "assistant",
        "content": f"{emoji} Deadline Stage: {days_left} jours restants",
        "sources": ["04_stages.txt"],
        "action": "stage",
        "style": bg,
        "data": {"deadline": student['stage_deadline'], "days_left": days_left}
    })


def handle_bourses_action(student):
    """Handle bourses with eligibility."""
    gpa = student['gpa']
    eligible = gpa >= 14.0

    if eligible:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Félicitations {student['name'].split()[0]}! Vous êtes éligible à la bourse au mérite (500 TND/trimestre) avec votre moyenne de {gpa}/20",
            "sources": ["03_bourses.txt"],
            "action": "bourses",
            "eligible": True,
            "gpa": gpa
        })
    else:
        needed = 14.0 - gpa
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Votre moyenne: {gpa}/20. Il vous manque {needed:.1f} points pour être éligible à la bourse au mérite. Continuez vos efforts!",
            "sources": ["03_bourses.txt"],
            "action": "bourses",
            "eligible": False,
            "gpa": gpa
        })


def render_message(message, msg_index: int):
    """Render a chat message with clean styling."""
    if message["role"] == "user":
        st.markdown(f"""
        <div style='text-align: right; margin: 1rem 0;'>
            <span style='background: #e0e7ff; padding: 0.75rem 1.5rem; border-radius: 2rem; display: inline-block; color: #000;'>
                {message['content']}
            </span>
        </div>
        """, unsafe_allow_html=True)
        return

    # Assistant messages
    action = message.get("action")

    if action == "absences":
        data = message.get("data", {})
        st.markdown(f"""
        <div class='{message.get('style', 'countdown-success')}'>
            <h3>{data.get('emoji', '📊')} Vos Absences</h3>
            <p><strong>{message['content']}</strong></p>
            <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1rem;'>
                <div style='background: rgba(255,255,255,0.5); padding: 1rem; border-radius: 0.5rem; text-align: center;'>
                    <div style='font-size: 1.5rem; font-weight: bold;'>{data.get('absences', '0/15')}</div>
                    <div style='font-size: 0.85rem;'>Utilisées</div>
                </div>
                <div style='background: rgba(255,255,255,0.5); padding: 1rem; border-radius: 0.5rem; text-align: center;'>
                    <div style='font-size: 1.5rem; font-weight: bold;'>{data.get('percentage', '0%')}</div>
                    <div style='font-size: 0.85rem;'>Pourcentage</div>
                </div>
                <div style='background: rgba(255,255,255,0.5); padding: 1rem; border-radius: 0.5rem; text-align: center;'>
                    <div style='font-size: 1.5rem; font-weight: bold;'>{data.get('remaining', '0')}</div>
                    <div style='font-size: 0.85rem;'>Restantes</div>
                </div>
            </div>
            <p style='margin-top: 1rem; font-size: 0.9rem;'>Règle: Plus de 15% d'absences = élimination</p>
        </div>
        """, unsafe_allow_html=True)

    elif action == "attestation":
        st.markdown(f"""
        <div class='action-card'>
            <h3>✅ Attestation Prête!</h3>
            <p>J'ai généré votre demande pour: <strong>{message.get('student_name', 'Vous')}</strong></p>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("📧 Voir l'email généré"):
            st.code(message.get("email", ""), language="text")
            copy_key = f"copy_{msg_index}_{hash(str(message)) % 10000}"
            if st.button("📋 Copier l'email", key=copy_key):
                st.success("✅ Email copié!")

    elif action == "stage":
        data = message.get("data", {})
        st.markdown(f"""
        <div class='{message.get('style', 'countdown-success')}'>
            <h3>💼 Deadline Stage</h3>
            <p><strong>Temps restant:</strong> {data.get('days_left', 0)} jours</p>
            <p><strong>Date limite:</strong> {data.get('deadline', '2025-06-30')}</p>
        </div>
        """, unsafe_allow_html=True)

    elif action == "bourses":
        eligible = message.get("eligible", False)
        gpa = message.get("gpa", 0)
        bg = "countdown-success" if eligible else "countdown-warning"
        if eligible:
            st.markdown(f"""
            <div class='{bg}'>
                <h3>🎉 Bourse au Mérite!</h3>
                <p>Félicitations! Avec une moyenne de <strong>{gpa}/20</strong>, vous êtes éligible à <strong>500 TND/trimestre</strong></p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='{bg}'>
                <h3>💰 Bourses</h3>
                <p>Votre moyenne: <strong>{gpa}/20</strong>. Continuez vos efforts pour atteindre 14/20!</p>
            </div>
            """, unsafe_allow_html=True)

    else:
        # Regular message - just plain text
        st.markdown(f"""
        <div style='background: #f9fafb; padding: 1rem; border-radius: 1rem; margin: 0.5rem 0; border-left: 4px solid #22c55e; color: #000;'>
            {message['content']}
        </div>
        """, unsafe_allow_html=True)

    # Sources
    if message.get("sources"):
        sources = ", ".join(message['sources'])
        st.caption(f"📚 Source: {sources}")


def sidebar():
    """Render sidebar."""
    with st.sidebar:
        st.markdown("### ⚙️ Paramètres")

        if st.session_state.student_logged_in:
            st.markdown("---")
            st.markdown("### 👤 Mon Profil")

            student = st.session_state.student
            st.metric("Nom", student['name'])
            st.metric("Année", student['year'])
            st.metric("Moyenne", f"{student['gpa']}/20")
            st.metric("Absences", f"{student['absences']}/15")

            if student['gpa'] >= 14:
                st.success("🏆 Éligible bourse")
            else:
                st.info("💰 Non éligible bourse")

            st.markdown("---")
            if st.button("🔄 Changer de compte"):
                for key in ['student_logged_in', 'student', 'messages']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

        st.markdown("---")
        st.markdown("### 📚 Documents")
        data_dir = Path("docs/Data")
        if data_dir.exists():
            for doc in sorted(data_dir.glob("*.txt"))[:8]:
                st.text(f"📄 {doc.stem.replace('_', ' ').title()}")


def chat_interface():
    """Render chat interface."""
    # Render all messages with index
    for idx, message in enumerate(st.session_state.messages):
        render_message(message, idx)

    # Chat input
    if prompt := st.chat_input("💬 Posez votre question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("🤔"):
            process_query(prompt)
        st.rerun()


def main():
    """Main app."""
    init_session_state()
    display_header()

    # Show welcome screen if not logged in
    if not st.session_state.student_logged_in:
        show_welcome_screen()
    else:
        # Initialize services
        if not st.session_state.vector_store:
            st.session_state.vector_store = get_qdrant_store()
        if not st.session_state.openai_client:
            st.session_state.openai_client = get_openai_client()

        # Suggestion chips
        render_suggestion_chips()

        st.markdown("---")

        # Chat
        chat_interface()

    # Sidebar
    sidebar()

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #999; font-size: 0.85rem;'>🎓 UniHelp - Challenge IA Night © 2025 | IIT / NAU</div>",
        unsafe_allow_html=True
    )


def email_interface():
    """Email generator tab."""
    st.markdown("### ✉️ Générateur d'Emails")

    student = st.session_state.get('student', DEFAULT_STUDENT)

    col1, col2 = st.columns([1, 1])
    with col1:
        request_type = st.selectbox("Type de demande", [
            "Attestation de scolarité", "Certificat de réussite",
            "Convention de stage", "Justification d'absence",
            "Demande de rattrapage", "Demande de bourse"
        ])

        st.markdown("#### 👤 Vos infos")
        name = st.text_input("Nom", value=student.get('name', ''))
        student_id = st.text_input("Numéro étudiant", value=student.get('id', ''))
        email = st.text_input("Email", value=student.get('email', ''))
        add_info = st.text_area("Informations supplémentaires", height=100)

    with col2:
        if st.button("✨ Générer", type="primary", use_container_width=True):
            client = get_openai_client()
            if client:
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "Génère un email administratif professionnel."},
                            {"role": "user", "content": f"Type: {request_type}\nDe: {name}\nID: {student_id}\n{add_info}"}
                        ]
                    )
                    st.session_state.generated_email = response.choices[0].message.content
                except:
                    pass

        if 'generated_email' in st.session_state:
            st.text_area("Email généré", st.session_state.generated_email, height=350)


if __name__ == "__main__":
    main()
