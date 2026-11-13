import hashlib
import json
from datetime import datetime, timezone

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

def get_api_data(endpoint):
    """
    Fetch data from the FastAPI backend.
    Returns (data, error).
    """
    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=15,
        )

        if response.status_code == 200:
            return response.json(), None

        try:
            error = response.json()
        except ValueError:
            error = response.text

        return None, error

    except requests.RequestException as exc:
        return None, str(exc)

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
            "Project History",
            "Code Analysis",
            "AI Code Review",
            "Proposed Fixes",
            "Accepted Fix History",
            "Test Generator",
            "Test Runner",
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

        # Live Dashboard Metrics

    st.subheader("📊 Project Overview")

    metrics = {}
    metrics_available = False

    if backend_online:
        try:
            response = requests.get(
                f"{API_URL}/api/v1/dashboard/summary",
                timeout=5,
            )

            response.raise_for_status()

            dashboard_data = response.json()

            metrics = dashboard_data.get(
                "summary",
                dashboard_data,
            )

            metrics_available = True

        except (requests.RequestException, ValueError) as exc:
            st.warning(
                f"Unable to load dashboard metrics: {exc}"
            )
    else:
        st.warning(
            "Start the backend to view live dashboard metrics."
        )

    if metrics_available:

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Projects Analyzed</div>
                    <div class="metric-value">
                        {metrics.get("projects_analyzed", 0)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Issues Detected</div>
                    <div class="metric-value">
                        {metrics.get("total_issues", 0)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Tests Generated</div>
                    <div class="metric-value">
                        {metrics.get("total_tests_generated", 0)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col4:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Code Reviews</div>
                    <div class="metric-value">
                        {metrics.get("total_code_reviews", 0)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")
        execution_col1, execution_col2, execution_col3, execution_col4 = (
            st.columns(4)
        )
        execution_metrics = [
            (
                execution_col1,
                "Test Executions",
                metrics.get("total_test_executions", 0),
            ),
            (
                execution_col2,
                "Tests Passed",
                metrics.get("total_tests_passed", 0),
            ),
            (
                execution_col3,
                "Tests Failed",
                metrics.get("total_tests_failed", 0),
            ),
            (
                execution_col4,
                "Latest Execution",
                str(metrics.get("latest_execution_status") or "N/A").upper(),
            ),
        ]

        for column, label, value in execution_metrics:
            with column:
                st.metric(label, value)

                # Security Overview

        st.divider()

        st.subheader("Security Overview")

        security_score = metrics.get("security_score", 100)
        total_security = metrics.get("total_security_issues", 0)

        security_col1, security_col2, security_col3 = st.columns(3)

        with security_col1:
            st.metric(
                "Security Score",
                f"{security_score}/100",
                help=(
                    "Heuristic score based on detected security issues. "
                    "This is not a formal security rating."
                ),
            )

        with security_col2:
            st.metric(
                "Security Issues",
                total_security,
            )

        with security_col3:
            st.metric(
                "High-Risk Issues",
                metrics.get("high_risk_security_issues", 0),
            )

        risk_col1, risk_col2 = st.columns(2)

        with risk_col1:
            st.metric(
                "Medium-Risk Issues",
                metrics.get("medium_risk_security_issues", 0),
            )

        with risk_col2:
            st.metric(
                "Low-Risk Issues",
                metrics.get("low_risk_security_issues", 0),
            )

        st.markdown("#### Vulnerability Breakdown")

        security_rule_counts = metrics.get(
            "security_rule_counts",
            {},
        )

        rule_labels = {
            "SEC001": "Hardcoded Secrets",
            "SEC002": "Potential SQL Injection",
            "SEC003": "Unsafe Shell Execution",
            "SEC004": "Unsafe Deserialization",
            "SEC005": "Weak Cryptographic Hash",
        }

        rule_columns = st.columns(5)

        for column, (rule_id, label) in zip(
            rule_columns,
            rule_labels.items(),
        ):
            with column:
                st.metric(
                    rule_id,
                    security_rule_counts.get(rule_id, 0),
                    help=label,
                )

        st.caption(
            "Security score is heuristic. Findings are based on "
            "static AST pattern detection and may include false "
            "positives or miss vulnerabilities."
        )

    else:
        first_row = st.columns(4)
        second_row = st.columns(4)
        metric_labels = [
            "Projects Analyzed",
            "Issues Detected",
            "Tests Generated",
            "Code Reviews",
            "Test Executions",
            "Tests Passed",
            "Tests Failed",
            "Latest Execution",
        ]

        for column, label in zip(first_row + second_row, metric_labels):
            with column:
                st.metric(label, "N/A")

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
                        st.session_state.pop("analysis_result", None)
                        st.session_state.pop("review_result", None)
                        st.session_state.pop("test_generation_result", None)
                        st.session_state.pop("test_execution_result", None)
                        st.session_state.pop("test_execution_upload_id", None)
                        st.session_state.pop("fix_result", None)
                        st.session_state.pop("accepted_fix_result", None)
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

    st.title("🤖 AI Code Review & Debugging")

    st.write(
        "Understand code issues, investigate their root causes, "
        "and follow practical debugging recommendations."
    )

    upload_id = st.session_state.get("upload_id")

    if not upload_id:

        st.warning(
            "No project uploaded. Please upload a project first."
        )

    else:

        st.success("Project ready for intelligent code review.")

        st.write(
            "**Project:**",
            st.session_state.get("uploaded_file_name", "Unknown"),
        )

        if st.button(
            "🚀 Analyze & Debug My Code",
            use_container_width=True,
        ):

            with st.spinner(
                "Analyzing source code and investigating potential causes..."
            ):

                try:

                    response = requests.post(
                        f"{API_URL}/api/v1/review/{upload_id}",
                        timeout=60,
                    )

                    if response.status_code == 200:

                        result = response.json()

                        st.session_state["review_result"] = result

                        st.success(
                            "Intelligent code review completed!"
                        )

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
                f"Review provider: "
                f"{result.get('review_provider', 'N/A')}"
            )

            st.divider()

            st.subheader("🔍 Detailed Code Review")

            if reviews:

                for index, issue in enumerate(reviews, start=1):

                    severity = issue.get("severity", "Unknown")

                    rule_id = issue.get("rule_id", "N/A")

                    with st.expander(
                        f"{index}. {issue.get('rule_name', 'Code Issue')} "
                        f"— {severity.upper()}",
                        expanded=(index == 1),
                    ):

                        # Issue information
                        st.markdown("### 📌 Issue Information")

                        info_col1, info_col2 = st.columns(2)

                        with info_col1:

                            st.markdown(
                                f"**Rule:** `{rule_id}`"
                            )

                            st.markdown(
                                f"**Category:** "
                                f"{issue.get('category', 'N/A')}"
                            )

                        with info_col2:

                            st.markdown(
                                f"**File:** "
                                f"`{issue.get('file_path', 'N/A')}`"
                            )

                            st.markdown(
                                f"**Line:** {issue.get('line', 'N/A')}"
                            )

                        st.markdown("### 📝 Issue Description")

                        st.write(
                            issue.get("message", "No description available.")
                        )

                        st.markdown("### 💡 Explanation")

                        st.write(
                            issue.get("explanation", "N/A")
                        )

                        # Root cause
                        st.divider()

                        st.markdown("### 🔍 Root Cause Analysis")

                        st.info(
                            issue.get(
                                "root_cause",
                                "Root cause information is unavailable.",
                            )
                        )

                        # Source code context
                        st.markdown("### 💻 Source Code Context")

                        if issue.get("context_available"):

                            st.code(
                                issue.get("code_context", ""),
                                language="python",
                            )

                            st.caption(
                                "The arrow (>) identifies the reported "
                                "issue line."
                            )

                        else:

                            st.warning(
                                "Source context is unavailable for this issue."
                            )

                        # Debugging steps
                        st.divider()

                        st.markdown("### 🛠️ Debugging Guide")

                        debugging_steps = issue.get(
                            "debugging_steps",
                            [],
                        )

                        if debugging_steps:

                            for step_number, step in enumerate(
                                debugging_steps,
                                start=1,
                            ):

                                st.markdown(
                                    f"**Step {step_number}.** {step}"
                                )

                        else:

                            st.write(
                                "No debugging steps are available."
                            )

                        # Impact
                        st.divider()

                        st.markdown("### ⚠️ Potential Impact")

                        st.write(
                            issue.get("impact", "N/A")
                        )

                        # Suggested fix
                        st.markdown("### 🔧 Suggested Fix")

                        st.success(
                            issue.get(
                                "fix_suggestion",
                                "No suggestion available.",
                            )
                        )

                        # Confidence
                        st.divider()

                        st.markdown("### 🎯 Confidence Assessment")

                        confidence_level = issue.get(
                            "confidence_level",
                            "low",
                        ).capitalize()

                        confidence_col1, confidence_col2 = st.columns(2)

                        with confidence_col1:

                            st.metric(
                                "Analysis Confidence",
                                confidence_level,
                            )

                        with confidence_col2:

                            st.metric(
                                "Original Issue Confidence",
                                f"{issue.get('confidence', 0) * 100:.1f}%",
                            )

                        if not issue.get("context_available", False):

                            st.caption(
                                "Note: Source context was unavailable. "
                                "Interpret the analysis accordingly."
                            )

            else:

                st.success(
                    "Excellent! No code issues were found."
                )

            st.divider()

            st.caption(
                "DevPilot AI uses offline, rule-based analysis. "
                "Root-cause explanations are recommendations, "
                "not proof of runtime behavior."
            )

            with st.expander("View Complete API Response"):

                st.json(result)

elif page == "Proposed Fixes":

    st.title("🛠️ Proposed Code Fixes")

    st.write(
        "Generate, inspect, and validate proposed code fixes "
        "without modifying your original uploaded source."
    )

    st.divider()

    upload_id = st.session_state.get("upload_id")

    if not upload_id:

        st.warning(
            "No project uploaded. Please upload a Python project first."
        )

    else:

        st.success("Project ready for proposed fixes.")

        st.write(
            "**Project:**",
            st.session_state.get("uploaded_file_name", "Unknown"),
        )

        st.code(upload_id)

        # Retrieve existing analysis results.

        analysis = st.session_state.get("analysis_result")

        if not analysis or analysis.get("upload_id") != upload_id:

            st.info(
                "Run code analysis first to identify issues "
                "for which fixes can be proposed."
            )

            if st.button("🔍 Analyze Project", use_container_width=True):

                with st.spinner("Analyzing project..."):

                    try:

                        response = requests.post(
                            f"{API_URL}/api/v1/analyze/{upload_id}",
                            timeout=60,
                        )

                        if response.status_code == 200:

                            analysis = response.json()

                            st.session_state["analysis_result"] = analysis

                            st.success("Analysis completed!")

                            st.rerun()

                        else:

                            st.error(
                                f"Analysis failed: {response.text}"
                            )

                    except requests.RequestException as exc:

                        st.error(f"Backend connection error: {exc}")

        else:

            issues = analysis.get("issues", [])

            st.subheader("🔍 Detected Issues")

            st.metric("Total Issues", len(issues))

            if not issues:

                st.success(
                    "No issues detected. Your project looks clean!"
                )

            else:

                # Build readable issue labels.

                issue_options = {}

                for index, issue in enumerate(issues):

                    label = (
                        f"{issue.get('rule_id', 'Unknown')} | "
                        f"{issue.get('file_path', 'Unknown file')} | "
                        f"Line {issue.get('line', '?')} | "
                        f"{issue.get('severity', 'Unknown')}"
                    )

                    issue_options[label] = index

                selected_label = st.selectbox(
                    "Select an issue to generate a proposed fix",
                    list(issue_options.keys()),
                )

                selected_issue = issues[
                    issue_options[selected_label]
                ]

                with st.expander("Selected Issue Details"):

                    st.write(
                        "**Rule:**",
                        selected_issue.get("rule_id"),
                    )

                    st.write(
                        "**File:**",
                        selected_issue.get("file_path"),
                    )

                    st.write(
                        "**Line:**",
                        selected_issue.get("line"),
                    )

                    st.write(
                        "**Description:**",
                        selected_issue.get("message"),
                    )

                    st.write(
                        "**Suggested Fix:**",
                        selected_issue.get("suggestion", "Not available"),
                    )

                st.divider()

                if st.button(
                    "✨ Generate Proposed Fix",
                    use_container_width=True,
                ):

                    request_data = {
                        "file_path": selected_issue["file_path"],
                        "rule_id": selected_issue["rule_id"],
                        "line": selected_issue["line"],
                    }

                    with st.spinner(
                        "Generating and validating proposed fix..."
                    ):

                        try:

                            response = requests.post(
                                f"{API_URL}/api/v1/fix/{upload_id}",
                                json=request_data,
                                timeout=30,
                            )

                            if response.status_code == 200:

                                fix_result = response.json()

                                st.session_state["fix_result"] = fix_result
                                st.session_state["fix_issue_key"] = (
                                    selected_issue.get("file_path"),
                                    selected_issue.get("rule_id"),
                                    selected_issue.get("line"),
                                )
                                st.session_state["fix_issue_key"] = (
                                    selected_issue.get("file_path"),
                                    selected_issue.get("rule_id"),
                                    selected_issue.get("line"),
                                )

                                st.success(
                                    "Proposed fix generated successfully!"
                                )

                            else:

                                try:
                                    error = response.json()
                                except ValueError:
                                    error = response.text

                                st.error(
                                    f"Fix generation failed: {error}"
                                )

                        except requests.RequestException as exc:

                            st.error(
                                f"Backend connection error: {exc}"
                            )

                # Display only the proposal generated for the currently selected issue.
                fix_result = st.session_state.get("fix_result")
                current_issue_key = (
                    selected_issue.get("file_path"),
                    selected_issue.get("rule_id"),
                    selected_issue.get("line"),
                )
                saved_issue_key = st.session_state.get("fix_issue_key")

                if (
                    fix_result
                    and fix_result.get("upload_id") == upload_id
                    and saved_issue_key == current_issue_key
                ):

                    st.divider()
                    st.subheader("📊 Fix Generation Result")

                    if fix_result.get("supported"):
                        st.success(fix_result.get("message", ""))
                    else:
                        st.warning(fix_result.get("message", ""))

                    validation_passed = fix_result.get("validation_passed")

                    if validation_passed is True:
                        st.success("✅ AST Validation Passed")
                    elif validation_passed is False:
                        st.error("❌ AST Validation Failed")
                    else:
                        st.info("AST validation was not performed.")

                    st.caption(fix_result.get("validation_message") or "")

                    original_code = fix_result.get("original_code")
                    proposed_code = fix_result.get("proposed_code")

                    if original_code is not None:
                        st.subheader("🔄 Original vs Proposed Code")
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("### Original Code")
                            st.code(original_code, language="python")

                        with col2:
                            st.markdown("### Proposed Code")
                            if proposed_code is not None:
                                st.code(proposed_code, language="python")
                            else:
                                st.info("No proposed code was generated.")

                    diff = fix_result.get("diff")
                    if diff:
                        st.subheader("📝 Code Difference")
                        st.code(diff, language="diff")

                    st.divider()
                    st.info(
                        "Accepting saves a separate version under the accepted-fixes "
                        "storage area. Your original uploaded source remains unchanged."
                    )

                    can_accept = (
                        fix_result.get("supported") is True
                        and validation_passed is True
                        and isinstance(proposed_code, str)
                    )

                    if can_accept:
                        if st.button(
                            "✅ Accept & Save Fix",
                            use_container_width=True,
                            type="primary",
                        ):
                            accept_request = {
                                "file_path": selected_issue["file_path"],
                                "rule_id": selected_issue["rule_id"],
                                "line": selected_issue["line"],
                            }

                            with st.spinner("Revalidating and saving accepted version..."):
                                try:
                                    accept_response = requests.post(
                                        f"{API_URL}/api/v1/fix/{upload_id}/accept",
                                        json=accept_request,
                                        timeout=30,
                                    )

                                    if accept_response.status_code in (200, 201):
                                        accepted_data = accept_response.json()
                                        st.session_state["accepted_fix_result"] = {
                                            "upload_id": upload_id,
                                            "issue_key": current_issue_key,
                                            "data": accepted_data,
                                        }
                                        st.success(
                                            "Fix accepted and saved as a separate version."
                                        )
                                    else:
                                        try:
                                            accept_error = accept_response.json()
                                        except ValueError:
                                            accept_error = accept_response.text
                                        st.error(
                                            f"Unable to save accepted fix: {accept_error}"
                                        )

                                except requests.RequestException as exc:
                                    st.error(f"Backend connection error: {exc}")

                    else:
                        st.warning(
                            "This proposal cannot be accepted. A supported fix "
                            "and successful AST validation are required."
                        )

                    accepted_state = st.session_state.get("accepted_fix_result")
                    if (
                        accepted_state
                        and accepted_state.get("upload_id") == upload_id
                        and accepted_state.get("issue_key") == current_issue_key
                    ):
                        accepted_data = accepted_state.get("data", {})
                        accepted_fix_id = accepted_data.get("fix_id")
                        if not accepted_fix_id:
                            accepted_fix_id = accepted_data.get("id")
                        if not accepted_fix_id and isinstance(
                            accepted_data.get("fix"), dict
                        ):
                            accepted_fix_id = accepted_data["fix"].get("id")

                        st.success("Saved accepted version successfully.")
                        if accepted_fix_id:
                            st.write("**Accepted Fix ID:**")
                            st.code(accepted_fix_id)
                        st.caption(
                            "Open Accepted Fix History to inspect the saved version "
                            "and verify its SHA-256 hash."
                        )

                    if st.button(
                        "❌ Reject Proposal",
                        use_container_width=True,
                    ):
                        st.session_state.pop("fix_result", None)
                        st.session_state.pop("fix_issue_key", None)
                        st.session_state.pop("accepted_fix_result", None)
                        st.success("Proposal dismissed.")
                        st.rerun()

                elif fix_result and fix_result.get("upload_id") == upload_id:
                    st.info(
                        "The displayed proposal belongs to a different issue. "
                        "Generate a new proposal for the currently selected issue."
                    )

elif page == "Accepted Fix History":

    st.title("📚 Accepted Fix History")

    st.write(
        "Browse saved fix versions, inspect their metadata, "
        "and verify the SHA-256 integrity of accepted code."
    )

    st.divider()

    # Load projects so accepted fixes can be browsed for any upload.
    projects_data, projects_error = get_api_data("/api/v1/projects/")

    if projects_error:
        st.error(f"Unable to load projects: {projects_error}")
    else:
        projects = projects_data.get("projects", [])

        if not projects:
            st.info("No uploaded projects are available yet.")
        else:
            project_options = {
                (
                    f"{project.get('original_filename', 'Project')} "
                    f"({project.get('upload_id', '')[:8]})"
                ): project.get("upload_id")
                for project in projects
            }

            selected_project_label = st.selectbox(
                "Select a project",
                list(project_options.keys()),
                key="accepted_fix_project",
            )
            selected_upload_id = project_options[selected_project_label]

            st.caption(f"Upload ID: {selected_upload_id}")

            history_data, history_error = get_api_data(
                f"/api/v1/fix/{selected_upload_id}/accepted"
            )

            if history_error:
                st.error(f"Unable to load accepted fixes: {history_error}")
            else:
                accepted_fixes = history_data.get("accepted_fixes", [])

                st.metric(
                    "Accepted Fix Versions",
                    history_data.get("total", len(accepted_fixes)),
                )

                if not accepted_fixes:
                    st.info(
                        "No fixes have been accepted for this project yet. "
                        "Generate a proposal and use the Accept action to save one."
                    )
                else:
                    display_records = []

                    for record in accepted_fixes:
                        display_records.append(
                            {
                                "Fix ID": record.get("id", ""),
                                "Rule": record.get("rule_id", ""),
                                "File": record.get("file_path", ""),
                                "Line": record.get("line", ""),
                                "Accepted At": record.get("created_at", ""),
                            }
                        )

                    st.dataframe(
                        display_records,
                        use_container_width=True,
                        hide_index=True,
                    )

                    st.divider()
                    st.subheader("🔍 Inspect Accepted Version")

                    fix_options = {}

                    for index, record in enumerate(accepted_fixes, start=1):
                        fix_id = record.get("id")

                        label = (
                            f"{record.get('rule_id', 'Unknown rule')} | "
                            f"{record.get('file_path', 'Unknown file')} | "
                            f"Line {record.get('line', '?')} | "
                            f"{record.get('created_at', 'Unknown date')} | "
                            f"Version {index}"
                        )

                        if fix_id:
                            fix_options[label] = fix_id

                    if not fix_options:
                        st.warning(
                            "The API returned accepted-fix records without fix IDs."
                        )
                    else:
                        selected_fix_label = st.selectbox(
                            "Choose an accepted fix",
                            list(fix_options.keys()),
                            key=f"accepted_fix_record_{selected_upload_id}",
                        )
                        selected_fix_id = fix_options[selected_fix_label]

                        if st.button(
                            "📖 Load Accepted Code",
                            use_container_width=True,
                        ):
                            with st.spinner("Loading and verifying accepted code..."):
                                detail_data, detail_error = get_api_data(
                                    f"/api/v1/fix/{selected_upload_id}/accepted/"
                                    f"{selected_fix_id}"
                                )

                                if detail_error:
                                    st.error(
                                        f"Unable to retrieve accepted version: "
                                        f"{detail_error}"
                                    )
                                    st.session_state.pop(
                                        "accepted_fix_detail",
                                        None,
                                    )
                                else:
                                    st.session_state["accepted_fix_detail"] = {
                                        "upload_id": selected_upload_id,
                                        "fix_id": selected_fix_id,
                                        "data": detail_data,
                                    }

                        detail_state = st.session_state.get(
                            "accepted_fix_detail"
                        )

                        if (
                            detail_state
                            and detail_state.get("upload_id") == selected_upload_id
                            and detail_state.get("fix_id") == selected_fix_id
                        ):
                            detail_data = detail_state.get("data", {})
                            fix_record = detail_data.get("fix", {})
                            accepted_code = detail_data.get("accepted_code")

                            st.divider()
                            st.subheader("🛡️ Integrity Verification")

                            expected_hash = fix_record.get("accepted_sha256")

                            if isinstance(accepted_code, str) and expected_hash:
                                actual_hash = hashlib.sha256(
                                    accepted_code.encode("utf-8")
                                ).hexdigest()

                                if actual_hash == expected_hash:
                                    st.success(
                                        "SHA-256 verification passed. "
                                        "The retrieved code matches the saved hash."
                                    )
                                else:
                                    st.error(
                                        "SHA-256 verification failed. "
                                        "The retrieved code does not match the "
                                        "stored hash. Code preview is blocked."
                                    )

                                col1, col2 = st.columns(2)

                                with col1:
                                    st.caption("Stored accepted SHA-256")
                                    st.code(expected_hash, language="text")

                                with col2:
                                    st.caption("Calculated SHA-256")
                                    st.code(actual_hash, language="text")

                                if actual_hash == expected_hash:
                                    st.subheader("✅ Accepted Code")

                                    st.code(
                                        accepted_code,
                                        language="python",
                                    )

                                    st.download_button(
                                        label="⬇️ Download Verified Accepted Code",
                                        data=accepted_code,
                                        file_name="accepted.py",
                                        mime="text/x-python",
                                        use_container_width=True,
                                    )
                            else:
                                st.error(
                                    "Integrity verification could not be performed "
                                    "because the accepted code or stored SHA-256 "
                                    "value is missing. Code preview is blocked."
                                )

                            st.divider()
                            st.subheader("📋 Fix Metadata")

                            metadata_col1, metadata_col2 = st.columns(2)

                            with metadata_col1:
                                st.write(
                                    "**Rule:**",
                                    fix_record.get("rule_id", "N/A"),
                                )
                                st.write(
                                    "**File:**",
                                    fix_record.get("file_path", "N/A"),
                                )
                                st.write(
                                    "**Line:**",
                                    fix_record.get("line", "N/A"),
                                )

                            with metadata_col2:
                                st.write(
                                    "**Accepted At:**",
                                    fix_record.get("created_at", "N/A"),
                                )
                                st.write(
                                    "**Original SHA-256:**",
                                    fix_record.get("original_sha256", "N/A"),
                                )
                                st.write(
                                    "**Accepted SHA-256:**",
                                    fix_record.get("accepted_sha256", "N/A"),
                                )

                            st.info(
                                "The original uploaded source remains unchanged. "
                                "This page displays the separately saved accepted "
                                "version. The current API provides the original "
                                "file hash, but not the original source text, so "
                                "a side-by-side source comparison is not available."
                            )

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




elif page == "Test Runner":

    st.title("▶️ Docker Test Runner")

    st.write(
        "Execute generated pytest tests inside an isolated Docker container "
        "and inspect saved execution results."
    )

    st.divider()

    # Load saved projects from the backend. This works even when Streamlit's
    # session state has been reset.
    projects_data, projects_error = get_api_data("/api/v1/projects/")

    if projects_error:
        st.error(f"Unable to load uploaded projects: {projects_error}")
    else:
        projects = projects_data.get("projects", [])

        if not projects:
            st.info("No uploaded projects found. Upload a Python file or ZIP project first.")
        else:
            project_options = {
                (
                    f"{project.get('original_filename', 'Project')} "
                    f"({project.get('upload_id', '')[:8]})"
                ): project.get("upload_id")
                for project in projects
                if project.get("upload_id")
            }

            if not project_options:
                st.warning("The backend returned projects without valid upload IDs.")
            else:
                # Prefer the current project when it exists in the saved list.
                current_upload_id = st.session_state.get("upload_id")
                option_labels = list(project_options.keys())
                default_index = 0

                for index, label in enumerate(option_labels):
                    if project_options[label] == current_upload_id:
                        default_index = index
                        break

                selected_project_label = st.selectbox(
                    "Select an uploaded project",
                    option_labels,
                    index=default_index,
                    key="test_runner_project_selector",
                )
                upload_id = project_options[selected_project_label]

                # Keep the selected project available to the other pages.
                st.session_state["upload_id"] = upload_id
                selected_project = next(
                    (
                        project for project in projects
                        if project.get("upload_id") == upload_id
                    ),
                    {},
                )
                st.session_state["uploaded_file_name"] = selected_project.get(
                    "original_filename",
                    selected_project_label,
                )

                st.success(
                    f"Selected project: "
                    f"{selected_project.get('original_filename', selected_project_label)}"
                )
                st.caption(f"Upload ID: {upload_id}")

                st.divider()

                generation_data, generation_error = get_api_data(
                    f"/api/v1/generate-tests/{upload_id}/latest"
                )

                if generation_error:
                    st.warning(
                        "No saved test-generation result was found for this project. "
                        "Open Test Generator and generate tests first."
                    )
                    with st.expander("Generation lookup details"):
                        st.write(generation_error)
                else:
                    generation_result = generation_data.get(
                        "result",
                        generation_data,
                    )
                    generated_count = generation_result.get("total_tests", 0)
                    generation_success = generation_result.get("success", False)

                    gen_col1, gen_col2 = st.columns(2)
                    gen_col1.metric("Generated Tests", generated_count)
                    gen_col2.metric(
                        "Generation Status",
                        "Ready"
                        if generation_success and generated_count > 0
                        else "Check",
                    )

                    if generated_count <= 0:
                        st.warning(
                            "The latest generation contains no tests. "
                            "Generate supported tests before running the suite."
                        )
                    else:
                        st.info(
                            "Tests run in Docker with network access disabled, "
                            "a read-only workspace, and resource limits."
                        )

                        if st.button(
                            "🚀 Run Generated Tests",
                            type="primary",
                            use_container_width=True,
                            key=f"run_generated_tests_{upload_id}",
                        ):
                            with st.spinner(
                                "Running pytest inside the isolated Docker container..."
                            ):
                                try:
                                    execution_response = requests.post(
                                        f"{API_URL}/api/v1/execute-tests/{upload_id}",
                                        timeout=45,
                                    )

                                    if execution_response.status_code == 200:
                                        execution_result = execution_response.json()
                                        st.session_state["test_execution_result"] = (
                                            execution_result
                                        )
                                        st.session_state["test_execution_upload_id"] = (
                                            upload_id
                                        )
                                        st.success("Test execution completed.")
                                    else:
                                        try:
                                            execution_error = execution_response.json()
                                        except ValueError:
                                            execution_error = execution_response.text
                                        st.error(
                                            f"Test execution failed "
                                            f"({execution_response.status_code}): "
                                            f"{execution_error}"
                                        )

                                except requests.Timeout:
                                    st.error(
                                        "The request timed out. Check the backend "
                                        "terminal and Docker container status."
                                    )
                                except requests.RequestException as exc:
                                    st.error(f"Backend connection error: {exc}")

                # Load the latest saved execution from the API. This restores
                # results after a browser refresh or Streamlit restart.
                latest_data, latest_error = get_api_data(
                    f"/api/v1/execute-tests/{upload_id}/latest"
                )

                session_result = st.session_state.get("test_execution_result")
                session_upload_id = st.session_state.get(
                    "test_execution_upload_id"
                )

                if session_result and session_upload_id == upload_id:
                    execution_result = session_result
                elif not latest_error:
                    execution_result = latest_data.get("result", latest_data)
                else:
                    execution_result = None

                if execution_result:
                    st.divider()
                    st.subheader("📊 Latest Execution Results")

                    execution_status = execution_result.get(
                        "status",
                        "unknown",
                    ).lower()

                    if execution_status == "passed":
                        st.success("All generated tests passed.")
                    elif execution_status == "failed":
                        st.error("Some generated tests failed.")
                    else:
                        st.warning(
                            f"Execution status: {execution_status.upper()}"
                        )

                    metric_columns = st.columns(5)
                    metric_values = [
                        ("Total", execution_result.get("tests_total", 0)),
                        ("Passed", execution_result.get("passed", 0)),
                        ("Failed", execution_result.get("failed", 0)),
                        ("Skipped", execution_result.get("skipped", 0)),
                        ("Errors", execution_result.get("errors", 0)),
                    ]

                    for column, (label, value) in zip(
                        metric_columns,
                        metric_values,
                    ):
                        column.metric(label, value)

                    duration = execution_result.get("duration_seconds")
                    result_col1, result_col2 = st.columns(2)
                    result_col1.metric(
                        "Execution Time",
                        f"{duration:.2f} sec"
                        if isinstance(duration, (int, float))
                        else "N/A",
                    )
                    result_col2.metric(
                        "Exit Code",
                        execution_result.get("exit_code", "N/A"),
                    )

                    st.caption(
                        f"Test file: {execution_result.get('test_file', 'N/A')}"
                    )

                    failure_details = execution_result.get("failure_details", [])
                    if failure_details:
                        st.subheader("❌ Failure Details")
                        st.code("\n".join(failure_details), language="text")

                    with st.expander("Standard Output", expanded=True):
                        st.code(
                            execution_result.get("stdout")
                            or "(No standard output)",
                            language="text",
                        )

                    with st.expander("Standard Error"):
                        st.code(
                            execution_result.get("stderr")
                            or "(No standard error)",
                            language="text",
                        )

                    with st.expander("Complete Execution Response"):
                        st.json(execution_result)

                st.divider()
                st.subheader("🕘 Execution History")

                history_data, history_error = get_api_data(
                    f"/api/v1/execute-tests/{upload_id}/history"
                )

                if history_error:
                    st.error(
                        f"Unable to load execution history: {history_error}"
                    )
                else:
                    executions = history_data.get("executions", [])
                    st.metric(
                        "Saved Executions",
                        history_data.get(
                            "total_executions",
                            len(executions),
                        ),
                    )

                    if not executions:
                        st.info(
                            "No test executions have been saved for this project yet."
                        )
                    else:
                        history_rows = []

                        for record in executions:
                            saved_result = record.get("result", {})
                            history_rows.append(
                                {
                                    "Execution ID": record.get("id", ""),
                                    "Status": saved_result.get(
                                        "status",
                                        "unknown",
                                    ).upper(),
                                    "Total": saved_result.get("tests_total", 0),
                                    "Passed": saved_result.get("passed", 0),
                                    "Failed": saved_result.get("failed", 0),
                                    "Duration (sec)": saved_result.get(
                                        "duration_seconds"
                                    ),
                                    "Created At": record.get("created_at", ""),
                                }
                            )

                        st.dataframe(
                            history_rows,
                            use_container_width=True,
                            hide_index=True,
                        )

                        execution_options = {}
                        for record in executions:
                            record_id = record.get("id")
                            if record_id is not None:
                                saved_result = record.get("result", {})
                                label = (
                                    f"Run #{record_id} — "
                                    f"{saved_result.get('status', 'unknown').upper()} — "
                                    f"{record.get('created_at', 'Unknown date')}"
                                )
                                execution_options[label] = record

                        if execution_options:
                            selected_run_label = st.selectbox(
                                "Inspect a saved execution",
                                list(execution_options.keys()),
                                key=f"inspect_execution_{upload_id}",
                            )
                            selected_record = execution_options[
                                selected_run_label
                            ]
                            with st.expander("Saved execution details"):
                                st.json(selected_record.get("result", {}))


elif page == "Project History":

    st.title("📂 Project History")

    st.write(
        "Explore your previously uploaded projects "
        "and access their saved analysis, review, "
        "and test generation results."
    )

    st.divider()

    # Fetch all uploaded projects

    with st.spinner("Loading project history..."):

        projects_data, error = get_api_data(
            "/api/v1/projects/"
        )

    if error:

        st.error(
            f"Unable to load projects: {error}"
        )

    else:

        projects = projects_data.get("projects", [])

        total_projects = len(projects)

        st.metric(
            "Total Uploaded Projects",
            total_projects,
        )

        st.divider()

        if not projects:

            st.info(
                "No projects found. Upload your first "
                "Python project to get started."
            )

        else:

            st.subheader("📁 Uploaded Projects")

            # Display project information

            display_projects = [
                {
                    "Project Name": project.get(
                        "original_filename"
                    ),
                    "Type": project.get("upload_type"),
                    "Uploaded At": project.get("created_at"),
                    "Upload ID": project.get("upload_id"),
                }
                for project in projects
            ]

            st.dataframe(
                display_projects,
                use_container_width=True,
                hide_index=True,
            )

            st.divider()

            # Select a project

            st.subheader("🔍 Explore Project")

            project_options = {
                (
                    f"{project.get('original_filename')} "
                    f"({project.get('upload_id', '')[:8]})"
                ): project.get("upload_id")
                for project in projects
            }

            selected_project_name = st.selectbox(
                "Select a project",
                list(project_options.keys()),
            )

            selected_upload_id = project_options[
                selected_project_name
            ]

            # Fetch selected project details

            project_data, project_error = get_api_data(
                f"/api/v1/projects/{selected_upload_id}"
            )

            if project_error:

                st.error(
                    f"Unable to retrieve project details: "
                    f"{project_error}"
                )

            else:

                project = project_data.get("project", {})

                st.success("Project details loaded successfully.")

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        "**Filename:**",
                        project.get("original_filename"),
                    )

                    st.write(
                        "**Upload Type:**",
                        project.get("upload_type"),
                    )

                with col2:

                    st.write(
                        "**Uploaded At:**",
                        project.get("created_at"),
                    )

                    st.write(
                        "**Upload ID:**",
                        selected_upload_id,
                    )

                st.divider()

                # Retrieve saved history

                st.subheader("📊 Saved Project Results")

                history_endpoints = [
                    (
                        "🔍 Code Analysis",
                        f"/api/v1/analysis/"
                        f"{selected_upload_id}/history",
                        "analyses",
                    ),
                    (
                        "🤖 Code Review",
                        f"/api/v1/review/"
                        f"{selected_upload_id}/history",
                        "reviews",
                    ),
                    (
                        "🧪 Test Generation",
                        f"/api/v1/generate-tests/"
                        f"{selected_upload_id}/history",
                        "history",
                    ),
                    (
                        "▶️ Test Execution",
                        f"/api/v1/execute-tests/"
                        f"{selected_upload_id}/history",
                        "executions",
                    ),
                ]

                for title, endpoint, result_key in history_endpoints:

                    with st.expander(title, expanded=True):

                        history_data, history_error = get_api_data(
                            endpoint
                        )

                        if history_error:

                            st.error(
                                f"Unable to load history: "
                                f"{history_error}"
                            )

                        else:

                            history = history_data.get(
                                result_key,
                                [],
                            )

                            if not history:

                                st.info(
                                    "No saved results available yet."
                                )

                            else:

                                st.success(
                                    f"{len(history)} saved record(s) found."
                                )

                                for index, record in enumerate(
                                    history,
                                    start=1,
                                ):

                                    result = record.get(
                                        "result",
                                        record,
                                    )

                                    created_at = record.get(
                                        "created_at",
                                        "Unknown date",
                                    )

                                    with st.expander(
                                        f"Record {index} — {created_at}"
                                    ):

                                        st.json(result)

                st.divider()

                st.caption(
                    "DevPilot AI | Persistent Project History"
                )

elif page == "Reports":

    st.title("📊 Project Reports")

    st.write(
        "View your project's code analysis, code review, "
        "automated test generation, and test execution results."
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

        # Retrieve persisted test execution data, including after a Streamlit
        # refresh or restart.
        execution_latest_data, execution_latest_error = get_api_data(
            f"/api/v1/execute-tests/{upload_id}/latest"
        )
        if execution_latest_error:
            test_execution_latest = {}
        else:
            test_execution_latest = execution_latest_data.get(
                "result",
                execution_latest_data,
            )

        execution_history_data, execution_history_error = get_api_data(
            f"/api/v1/execute-tests/{upload_id}/history"
        )
        if execution_history_error:
            test_execution_history = []
        else:
            test_execution_history = execution_history_data.get(
                "executions",
                [],
            )

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

        # Test execution section

        st.subheader("▶️ Automated Test Execution")

        if test_execution_latest:
            execution_status = str(
                test_execution_latest.get("status", "unknown")
            ).upper()
            if execution_status == "PASSED":
                st.success("Latest generated-test execution passed.")
            elif execution_status == "FAILED":
                st.error("Latest generated-test execution contains failures.")
            else:
                st.warning(f"Latest execution status: {execution_status}")

            execution_columns = st.columns(5)
            execution_values = [
                ("Status", execution_status),
                ("Total", test_execution_latest.get("tests_total", 0)),
                ("Passed", test_execution_latest.get("passed", 0)),
                ("Failed", test_execution_latest.get("failed", 0)),
                ("Skipped", test_execution_latest.get("skipped", 0)),
            ]
            for column, (label, value) in zip(
                execution_columns,
                execution_values,
            ):
                column.metric(label, value)

            duration = test_execution_latest.get("duration_seconds")
            if isinstance(duration, (int, float)):
                st.caption(f"Execution duration: {duration:.2f} seconds")

            failure_details = test_execution_latest.get("failure_details", [])
            if failure_details:
                with st.expander("Latest execution failure details"):
                    st.code("\\n".join(failure_details), language="text")
        else:
            st.info(
                "No saved test execution is available for this project yet. "
                "Run generated tests from the Test Runner page."
            )

        if test_execution_history:
            with st.expander("View saved test execution history"):
                execution_rows = []
                for record in test_execution_history:
                    saved_result = record.get("result", {})
                    execution_rows.append(
                        {
                            "Execution ID": record.get("id", ""),
                            "Status": str(
                                saved_result.get("status", "unknown")
                            ).upper(),
                            "Total": saved_result.get("tests_total", 0),
                            "Passed": saved_result.get("passed", 0),
                            "Failed": saved_result.get("failed", 0),
                            "Created At": record.get("created_at", ""),
                        }
                    )
                st.dataframe(
                    execution_rows,
                    use_container_width=True,
                    hide_index=True,
                )
        elif execution_history_error:
            st.warning(
                f"Unable to load execution history: {execution_history_error}"
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
            "test_execution_latest": test_execution_latest,
            "test_execution_history": test_execution_history,
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