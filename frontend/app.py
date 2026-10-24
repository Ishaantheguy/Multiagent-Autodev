import os
import time

import requests
import streamlit as st


# --------------------------------------------------
# Configuration
# --------------------------------------------------

API_BASE_URL = os.getenv(
    "AUTODEV_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

GENERATE_ENDPOINT = f"{API_BASE_URL}/generate"

# Maximum time to wait for project generation (30 minutes).
REQUEST_TIMEOUT = (10, 1800)


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="AutoDev | AI Software Engineer",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# --------------------------------------------------
# Styling
# --------------------------------------------------

st.markdown(
    """
    <style>
        .block-container {
            max-width: 900px;
            padding-top: 3rem;
            padding-bottom: 3rem;
        }

        .hero {
            text-align: center;
            padding: 1.5rem 0 2rem 0;
        }

        .hero h1 {
            font-size: 3rem;
            font-weight: 750;
            margin-bottom: 0.5rem;
        }

        .hero p {
            font-size: 1.1rem;
            opacity: 0.75;
        }

        .section-heading {
            font-size: 1.25rem;
            font-weight: 650;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }

        .stButton > button {
            width: 100%;
            min-height: 3rem;
            font-weight: 600;
        }

        .footer {
            text-align: center;
            opacity: 0.6;
            font-size: 0.85rem;
            padding-top: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Header
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <h1>🛠️ AutoDev</h1>
        <p>Your autonomous AI software engineering team.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write(
    "Describe the application you want to build. "
    "AutoDev will analyze your requirements, design the architecture, "
    "generate the code, and prepare a ZIP archive for download."
)

st.divider()


# --------------------------------------------------
# Requirements input
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">What would you like to build?</div>',
    unsafe_allow_html=True,
)

with st.form("generation_form"):
    request_text = st.text_area(
        "Software requirements",
        height=260,
        placeholder=(
            "Example:\n\n"
            "Build a FastAPI task management application with SQLite.\n"
            "- Implement CRUD endpoints for tasks.\n"
            "- Validate request data using Pydantic.\n"
            "- Include unit tests using pytest.\n"
            "- Provide requirements.txt and a README.md.\n"
            "- Use a clean Python package structure."
        ),
        help=(
            "Describe the required functionality, technology stack, "
            "expected files, and testing requirements."
        ),
    )

    submitted = st.form_submit_button(
        "🚀 Generate Project",
        type="primary",
        use_container_width=True,
    )


# --------------------------------------------------
# Generation and download
# --------------------------------------------------

if submitted:
    cleaned_request = request_text.strip()

    if len(cleaned_request) < 10:
        st.error(
            "Please describe your project in at least 10 characters."
        )

    elif len(cleaned_request) > 10000:
        st.error(
            "Your requirements are too long. "
            "Please limit them to 10,000 characters."
        )

    else:
        st.session_state.pop("generated_zip", None)
        st.session_state.pop("generated_filename", None)
        st.session_state.pop("last_request", None)

        progress_container = st.container()

        with progress_container:
            st.subheader("Building your project")

            status_placeholder = st.empty()
            progress_bar = st.progress(0)

            stages = [
                "Submitting your requirements...",
                "Analyzing requirements and designing the architecture...",
                "Generating application code...",
                "Preparing the project archive...",
            ]

            status_placeholder.info(stages[0])
            progress_bar.progress(5)

            started_at = time.monotonic()

            try:
                # The backend performs the entire generation process
                # and returns the ZIP archive directly.
                with requests.post(
                    GENERATE_ENDPOINT,
                    json={"request": cleaned_request},
                    headers={"Accept": "application/zip"},
                    stream=True,
                    timeout=REQUEST_TIMEOUT,
                ) as response:

                    if not response.ok:
                        try:
                            error_data = response.json()
                            detail = error_data.get(
                                "detail",
                                response.text,
                            )
                        except ValueError:
                            detail = response.text

                        raise RuntimeError(
                            f"Backend returned HTTP "
                            f"{response.status_code}: {detail}"
                        )

                    content_type = response.headers.get(
                        "content-type",
                        "",
                    ).lower()

                    if "application/zip" not in content_type:
                        # Avoid treating a JSON or HTML error response
                        # as a downloadable ZIP file.
                        body = response.content[:4000].decode(
                            "utf-8",
                            errors="replace",
                        )

                        raise RuntimeError(
                            "The backend did not return a ZIP archive. "
                            f"Content-Type: {content_type or 'unknown'}. "
                            f"Response: {body}"
                        )

                    status_placeholder.info(
                        "Generation finished. Receiving project files..."
                    )
                    progress_bar.progress(80)

                    chunks = []

                    for chunk in response.iter_content(
                        chunk_size=64 * 1024
                    ):
                        if chunk:
                            chunks.append(chunk)

                    zip_data = b"".join(chunks)

                if not zip_data:
                    raise RuntimeError(
                        "The backend returned an empty ZIP response."
                    )

                # Basic ZIP signature validation.
                if not zip_data.startswith(b"PK"):
                    raise RuntimeError(
                        "The returned data does not appear to be "
                        "a valid ZIP archive."
                    )

                elapsed = time.monotonic() - started_at

                st.session_state["generated_zip"] = zip_data
                st.session_state["generated_filename"] = (
                    "autodev-project.zip"
                )
                st.session_state["last_request"] = cleaned_request
                st.session_state["generation_time"] = elapsed

                progress_bar.progress(100)
                status_placeholder.success(
                    f"Project generated successfully in "
                    f"{elapsed:.1f} seconds!"
                )

            except requests.Timeout:
                status_placeholder.empty()
                progress_bar.empty()

                st.error(
                    "The request timed out while waiting for AutoDev. "
                    "The backend may still be processing your request. "
                    "Check the remote backend logs before submitting "
                    "the same request again."
                )

            except requests.ConnectionError:
                status_placeholder.empty()
                progress_bar.empty()

                st.error(
                    "Could not connect to the AutoDev backend. "
                    "Verify that the backend is running and your "
                    "SSH port-forwarding tunnel is active."
                )

            except requests.RequestException as exc:
                status_placeholder.empty()
                progress_bar.empty()

                st.error(f"Request failed: {exc}")

            except RuntimeError as exc:
                status_placeholder.empty()
                progress_bar.empty()

                st.error(str(exc))

            except Exception as exc:
                status_placeholder.empty()
                progress_bar.empty()

                st.error(
                    f"An unexpected error occurred: "
                    f"{type(exc).__name__}: {exc}"
                )


# --------------------------------------------------
# Persistent download section
# --------------------------------------------------

if st.session_state.get("generated_zip"):
    st.divider()

    st.subheader("📦 Your project is ready!")

    st.write(
        "Download the generated project archive. "
        "Extract it locally to inspect the source code, "
        "configuration files, documentation, and tests."
    )

    st.download_button(
        label="⬇️ Download Project ZIP",
        data=st.session_state["generated_zip"],
        file_name=st.session_state.get(
            "generated_filename",
            "autodev-project.zip",
        ),
        mime="application/zip",
        type="primary",
        use_container_width=True,
        key="download_project_zip",
    )

    generation_time = st.session_state.get("generation_time")

    if generation_time is not None:
        st.caption(
            f"Generation time: {generation_time:.1f} seconds"
        )

    with st.expander("View submitted requirements"):
        st.text(st.session_state.get("last_request", ""))


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.markdown(
    """
    <div class="footer">
        AutoDev · Autonomous Software Engineering
    </div>
    """,
    unsafe_allow_html=True,
)
