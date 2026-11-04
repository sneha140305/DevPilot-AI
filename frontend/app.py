import requests
import streamlit as st

# ---------------- PAGE CONFIGURATION ----------------

st.set_page_config(
    page_title="DevPilot AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = "http://127.0.0.1:8000"

# ---------------- CUSTOM CSS ----------------

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0e1117;
    }

    .main-title {
        font-size: 38px;
        font-weight: 800;
        color: #ffffff;
    }

    .subtitle {
        color: #a0a0a0;
        font-size: 16px;
    }

    .metric-card {
        background-color: #1c2333;
        padding: 22px;
        border-radius: 12px;
        border: 1px solid #30394b;
    }

    .metric-label {
        color: #a0a0a0;
        font-size: 14px;
    }

    .metric-value {
        color: #ffffff;
        font-size: 30px;
        font-weight: bold;
    }

    .status-online {
        color: #2ecc71;
        font-weight: bold;
    }

    .status-offline {
        color: #ff6b6b;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------- BACKEND CONNECTION ----------------

def check_backend():
    try:
        response = requests.get(
            f"{API_URL}/api/v1/health",
            timeout=3,
        )

        if response.status_code == 200:
            return True, response.json()

        return False, {}

    except requests.RequestException:
        return False, {}


backend_online, health_data = check_backend()


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.title("🚀 DevPilot AI")

    st.caption("AI-Powered Developer Assistant")

    st.divider()

    page = st.radio(
        "NAVIGATION",
        [
            "Dashboard",
            "Upload Project",
            "Code Analysis",
            "AI Code Review",
            "Test Generator",
            "Reports",
        ],
    )

    st.divider()

    st.caption("Version 1.0.0")
    st.caption("Built for developers ❤️")


# ---------------- DASHBOARD ----------------

if page == "Dashboard":

    st.markdown(
        '<div class="main-title">Developer Dashboard</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        "Analyze code, identify bugs, review quality, "
        "and generate automated tests."
        "</div>",
        unsafe_allow_html=True,
    )

    st.write("")

    # Backend status

    if backend_online:
        st.success("Backend connected successfully")
    else:
        st.error(
            "Backend is offline. Start FastAPI to enable "
            "backend features."
        )

    st.write("")

    # Metrics

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Projects Analyzed</div>
                <div class="metric-value">0</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Issues Detected</div>
                <div class="metric-value">0</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Tests Generated</div>
                <div class="metric-value">0</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Code Reviews</div>
                <div class="metric-value">0</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    st.divider()

    # Quick actions

    st.subheader("Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📁 Upload Project", use_container_width=True):
            st.session_state["selected_page"] = "Upload Project"
            st.rerun()

    with col2:
        if st.button("🔍 Analyze Code", use_container_width=True):
            st.session_state["selected_page"] = "Code Analysis"
            st.rerun()

    with col3:
        if st.button("🧪 Generate Tests", use_container_width=True):
            st.session_state["selected_page"] = "Test Generator"
            st.rerun()

    st.divider()

    st.subheader("System Information")

    if backend_online:
        st.write("**Backend:** Online")
        st.write("**API Status:** Healthy")
        st.write(
            "**Health Response:**",
            health_data,
        )
    else:
        st.write("**Backend:** Offline")

# ---------------- OTHER PAGES ----------------

elif page == "Upload Project":

    st.title("📁 Upload Your Project")

    st.write(
        "Upload a Python file or a ZIP archive containing "
        "your Python project."
    )

    uploaded_file = st.file_uploader(
        "Choose your project",
        type=["py", "zip"],
        help="Maximum upload size is controlled by the backend.",
    )

    if uploaded_file is not None:

        st.success(f"Selected: {uploaded_file.name}")

        st.write(f"File size: {uploaded_file.size / 1024:.2f} KB")

        if st.button("🚀 Upload Project", use_container_width=True):

            with st.spinner("Uploading project..."):

                try:
                    response = requests.post(
                        f"{API_URL}/api/v1/uploads",
                        files={
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                uploaded_file.type,
                            )
                        },
                        timeout=60,
                    )

                    if response.status_code == 201:

                        result = response.json()

                        st.session_state["upload_id"] = result["upload_id"]

                        st.session_state["uploaded_file_name"] = (
                            uploaded_file.name
                        )

                        st.success("Project uploaded successfully!")

                        st.code(
                            result["upload_id"],
                            language="text",
                        )

                        st.json(result)

                    else:
                        try:
                            error = response.json()
                        except ValueError:
                            error = response.text

                        st.error(f"Upload failed: {error}")

                except requests.RequestException as exc:
                    st.error(f"Backend connection error: {exc}")

    if "upload_id" in st.session_state:

        st.divider()

        st.subheader("Current Uploaded Project")

        st.write(
            f"**Filename:** "
            f"{st.session_state['uploaded_file_name']}"
        )

        st.write(
            f"**Upload ID:** "
            f"`{st.session_state['upload_id']}`"
        )

elif page == "Code Analysis":
    st.title("🔍 Code Analysis")
    st.info("Static code analysis interface is coming soon.")

elif page == "AI Code Review":
    st.title("🤖 AI Code Review")
    st.info("Code review interface is coming soon.")

elif page == "Test Generator":
    st.title("🧪 Automated Test Generator")
    st.info("Test generation interface is coming soon.")

elif page == "Reports":
    st.title("📊 Reports")
    st.info("Analysis reports will be available here.")