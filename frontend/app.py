import requests
import streamlit as st
import json
from datetime import datetime, timezone

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

    st.write(
        "Analyze your uploaded Python project to detect "
        "bugs, security risks, and code-quality issues."
    )

    upload_id = st.session_state.get("upload_id")

    if not upload_id:
        st.warning(
            "No project uploaded yet. Please upload a Python "
            "file or ZIP project first."
        )

    else:

        st.success("Project is ready for analysis.")

        st.write(
            "**Uploaded file:**",
            st.session_state.get("uploaded_file_name", "Unknown"),
        )

        st.code(upload_id)

        st.divider()

        if st.button(
            "🚀 Analyze Code",
            use_container_width=True,
        ):

            with st.spinner("Analyzing your project..."):

                try:
                    # Change post() to get() if your backend
                    # analysis route uses @router.get().
                    response = requests.post(
                        f"{API_URL}/api/v1/analyze/{upload_id}",
                        timeout=60,
                    )

                    if response.status_code == 200:

                        result = response.json()

                        st.session_state["analysis_result"] = result

                        st.success("Code analysis completed!")

                    else:
                        try:
                            error = response.json()
                        except ValueError:
                            error = response.text

                        st.error(f"Analysis failed: {error}")

                except requests.RequestException as exc:
                    st.error(f"Backend connection error: {exc}")

        # Display analysis results

        result = st.session_state.get("analysis_result")

        if result and result.get("upload_id") == upload_id:

            st.divider()

            st.subheader("📊 Analysis Results")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Total Issues",
                    result.get("total_issues", 0),
                )

            with col2:
                st.metric(
                    "Quality Score",
                    result.get("quality_score", "N/A"),
                )

            with col3:
                st.metric(
                    "Files Analyzed",
                    result.get("total_files", "N/A"),
                )

            st.divider()

            # Severity distribution

            severity_counts = result.get("severity_counts", {})

            st.subheader("Issue Severity")

            if severity_counts:

                severity_columns = st.columns(
                    len(severity_counts)
                )

                for column, (severity, count) in zip(
                    severity_columns,
                    severity_counts.items(),
                ):

                    with column:
                        st.metric(
                            severity.replace("_", " ").title(),
                            count,
                        )

            # Detected issues

            issues = result.get("issues", [])

            st.subheader("🐛 Detected Issues")

            if issues:

                for index, issue in enumerate(issues, start=1):

                    title = (
                        issue.get("message")
                        or issue.get("rule_id")
                        or f"Issue {index}"
                    )

                    with st.expander(
                        f"{index}. {title}"
                    ):

                        st.write(
                            "**Rule:**",
                            issue.get("rule_id", "N/A"),
                        )

                        st.write(
                            "**Severity:**",
                            issue.get("severity", "N/A"),
                        )

                        st.write(
                            "**File:**",
                            issue.get("file_path", "N/A"),
                        )

                        st.write(
                            "**Line:**",
                            issue.get("line", "N/A"),
                        )

                        st.write(
                            "**Category:**",
                            issue.get("category", "N/A"),
                        )

                        st.write(
                            "**Description:**",
                            issue.get("message", "No description"),
                        )

            else:
                st.success("No issues detected!")

            with st.expander("View complete API response"):

                st.json(result)

elif page == "AI Code Review":

    st.title("🤖 AI Code Review")

    st.write(
        "Understand detected code issues, their impact, "
        "and recommended fixes."
    )

    upload_id = st.session_state.get("upload_id")

    if not upload_id:

        st.warning(
            "No project uploaded. Please upload a project first."
        )

    else:

        st.success("Project ready for code review.")

        st.write(
            "**Project:**",
            st.session_state.get("uploaded_file_name", "Unknown"),
        )

        if st.button(
            "🚀 Review My Code",
            use_container_width=True,
        ):

            with st.spinner("Reviewing your code..."):

                try:

                    response = requests.post(
                        f"{API_URL}/api/v1/review/{upload_id}",
                        timeout=60,
                    )

                    if response.status_code == 200:

                        result = response.json()

                        st.session_state["review_result"] = result

                        st.success("Code review completed!")

                    else:

                        try:
                            error = response.json()
                        except ValueError:
                            error = response.text

                        st.error(f"Review failed: {error}")

                except requests.RequestException as exc:

                    st.error(
                        f"Backend connection error: {exc}"
                    )

        result = st.session_state.get("review_result")

        if result and result.get("upload_id") == upload_id:

            st.divider()

            st.subheader("📊 Review Summary")

            reviews = result.get("reviews", [])

            total_issues = result.get("total_issues", 0)

            high_issues = sum(
                1 for issue in reviews
                if issue.get("severity", "").lower() == "high"
            )

            medium_issues = sum(
                1 for issue in reviews
                if issue.get("severity", "").lower() == "medium"
            )

            low_issues = sum(
                1 for issue in reviews
                if issue.get("severity", "").lower() == "low"
            )

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Total Issues", total_issues)
            col2.metric("High", high_issues)
            col3.metric("Medium", medium_issues)
            col4.metric("Low", low_issues)

            st.caption(
                f"Review provider: {result.get('review_provider', 'N/A')}"
            )

            st.divider()

            st.subheader("🔎 Detailed Code Review")

            if reviews:

                for index, issue in enumerate(reviews, start=1):

                    severity = issue.get("severity", "Unknown")

                    with st.expander(
                        f"{index}. {issue.get('rule_name', 'Code Issue')} "
                        f"— {severity.upper()}"
                    ):

                        st.markdown(
                            f"**Rule:** {issue.get('rule_id', 'N/A')}"
                        )

                        st.markdown(
                            f"**Category:** {issue.get('category', 'N/A')}"
                        )

                        st.markdown(
                            f"**File:** `{issue.get('file_path', 'N/A')}`"
                        )

                        st.markdown(
                            f"**Line:** {issue.get('line', 'N/A')}"
                        )

                        st.markdown("### 📝 Description")

                        st.write(issue.get("message", "N/A"))

                        st.markdown("### 💡 Explanation")

                        st.write(issue.get("explanation", "N/A"))

                        st.markdown("### ⚠️ Potential Impact")

                        st.write(issue.get("impact", "N/A"))

                        st.markdown("### 🔧 Suggested Fix")

                        st.info(
                            issue.get("fix_suggestion", "No suggestion available.")
                        )

                        st.progress(
                            float(issue.get("confidence", 0))
                        )

                        st.caption(
                            f"Confidence: "
                            f"{issue.get('confidence', 0) * 100:.1f}%"
                        )

            else:

                st.success(
                    "Excellent! No code issues were found."
                )

            with st.expander("View Complete API Response"):

                st.json(result)

elif page == "Test Generator":

    st.title("🧪 Automated Test Generator")

    st.write(
        "Automatically discover Python functions and generate "
        "pytest test cases for your uploaded code."
    )

    st.divider()

    upload_id = st.session_state.get("upload_id")
    uploaded_file_name = st.session_state.get(
        "uploaded_file_name",
        "",
    )

    if not upload_id:

        st.warning(
            "No project uploaded. Please upload a Python file first."
        )

    else:

        st.success("Project is ready for test generation.")

        st.write(f"**Uploaded project:** {uploaded_file_name}")

        st.code(upload_id)

        # Select Python file

        if uploaded_file_name.lower().endswith(".py"):

            file_name = uploaded_file_name

        else:

            st.info(
                "For ZIP projects, enter the relative path of "
                "the Python file you want to process."
            )

            file_name = st.text_input(
                "Python file path",
                placeholder="example.py or src/calculator.py",
            )

        st.divider()

        if st.button(
            "🚀 Generate Pytest Code",
            use_container_width=True,
        ):

            if not file_name:

                st.warning("Please provide a Python filename.")

            elif not file_name.lower().endswith(".py"):

                st.error("Only Python files are supported.")

            else:

                with st.spinner("Discovering functions and generating tests..."):

                    try:

                        response = requests.post(
                            f"{API_URL}/api/v1/generate-tests/"
                            f"{upload_id}/{file_name}",
                            timeout=60,
                        )

                        if response.status_code == 200:

                            result = response.json()

                            st.session_state["test_generation_result"] = (
                                result
                            )

                            st.success(
                                "Test generation completed!"
                            )

                        else:

                            try:
                                error = response.json()
                            except ValueError:
                                error = response.text

                            st.error(
                                f"Test generation failed: {error}"
                            )

                    except requests.RequestException as exc:

                        st.error(
                            f"Backend connection error: {exc}"
                        )

        # Display generated tests

        result = st.session_state.get(
            "test_generation_result"
        )

        if (
            result
            and result.get("upload_id") == upload_id
            and result.get("file_path") == file_name
        ):

            st.divider()

            st.subheader("📊 Generation Summary")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Functions Discovered",
                    result.get("total_functions", 0),
                )

            with col2:
                st.metric(
                    "Tests Generated",
                    result.get("total_tests", 0),
                )

            with col3:
                st.metric(
                    "Generation Status",
                    "Success" if result.get("success") else "Failed",
                )

            st.info(result.get("message", ""))

            test_code = result.get("test_code", "")

            if test_code:

                st.subheader("Generated Pytest Code")

                st.code(
                    test_code,
                    language="python",
                )

                st.download_button(
                    label="⬇️ Download Generated Tests",
                    data=test_code,
                    file_name="test_generated.py",
                    mime="text/x-python",
                    use_container_width=True,
                )

            else:

                st.warning(
                    "No test code was generated. "
                    "Check whether the uploaded file contains "
                    "supported Python functions."
                )

            with st.expander("View Complete API Response"):

                st.json(result)

elif page == "Reports":

    st.title("📊 Project Reports")

    st.write(
        "View your project's code analysis, code review, "
        "and automated test generation results."
    )

    upload_id = st.session_state.get("upload_id")

    if not upload_id:

        st.warning(
            "No project uploaded. Upload a project to view reports."
        )

    else:

        project_name = st.session_state.get(
            "uploaded_file_name",
            "Unknown Project",
        )

        st.subheader("Project Information")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Project:** {project_name}")

        with col2:
            st.write(f"**Upload ID:** `{upload_id}`")

        # Retrieve results belonging to the current upload

        analysis = st.session_state.get("analysis_result", {})
        review = st.session_state.get("review_result", {})
        test_generation = st.session_state.get(
            "test_generation_result", {}
        )

        if analysis.get("upload_id") != upload_id:
            analysis = {}

        if review.get("upload_id") != upload_id:
            review = {}

        if test_generation.get("upload_id") != upload_id:
            test_generation = {}

        st.divider()

        # Summary metrics

        analysis_available = bool(analysis)
        review_available = bool(review)
        tests_available = bool(test_generation)

        review_count = review.get("total_issues", 0)

        generated_tests = test_generation.get("total_tests", 0)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Code Analysis",
                "Completed" if analysis_available else "Pending",
            )

        with col2:
            st.metric(
                "Issues Reviewed",
                review_count if review_available else "Pending",
            )

        with col3:
            st.metric(
                "Tests Generated",
                generated_tests if tests_available else "Pending",
            )

        st.divider()

        # Analysis section

        st.subheader("🔍 Static Code Analysis")

        if analysis_available:

            st.success("Analysis results available.")

            st.json(analysis)

        else:

            st.info("Run Code Analysis to generate this report.")

        st.divider()

        # Review section

        st.subheader("🤖 Code Review")

        if review_available:

            st.success("Code review results available.")

            reviews = review.get("reviews", [])

            severity_counts = {}

            for issue in reviews:

                severity = issue.get(
                    "severity",
                    "Unknown",
                ).capitalize()

                severity_counts[severity] = (
                    severity_counts.get(severity, 0) + 1
                )

            if severity_counts:

                st.write("**Severity Distribution**")

                st.bar_chart(severity_counts)

            for index, issue in enumerate(reviews, start=1):

                with st.expander(
                    f"{index}. {issue.get('rule_name', 'Code Issue')}"
                ):

                    st.write("**Description:**", issue.get("message"))
                    st.write("**Explanation:**", issue.get("explanation"))
                    st.write("**Impact:**", issue.get("impact"))
                    st.info(issue.get("fix_suggestion"))

        else:

            st.info("Run AI Code Review to generate this report.")

        st.divider()

        # Test generation section

        st.subheader("🧪 Automated Test Generation")

        if tests_available:

            st.success("Test generation results available.")

            st.metric(
                "Functions Discovered",
                test_generation.get("total_functions", 0),
            )

            st.metric(
                "Tests Generated",
                generated_tests,
            )

            st.code(
                test_generation.get("test_code", ""),
                language="python",
            )

        else:

            st.info(
                "Generate pytest code to include it in this report."
            )

        st.divider()

        # Export consolidated report

        st.subheader("📥 Export Project Report")

        report = {
            "project_name": project_name,
            "upload_id": upload_id,
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "analysis": analysis,
            "code_review": review,
            "test_generation": test_generation,
        }

        report_json = json.dumps(
            report,
            indent=4,
            ensure_ascii=False,
        )

        st.download_button(
            label="⬇️ Download Complete Project Report",
            data=report_json,
            file_name="devpilot_project_report.json",
            mime="application/json",
            use_container_width=True,
        )

        st.success(
            "Your consolidated project report is ready."
        )