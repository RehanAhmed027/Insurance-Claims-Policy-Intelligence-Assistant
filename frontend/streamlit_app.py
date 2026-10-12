import requests
import streamlit as st

API_URL = "http://127.0.0.1:8001"

st.set_page_config(
    page_title="Insurance Intelligence",
    page_icon="🛡️",
)

st.title("Insurance Claims & Policy Intelligence")

product_name = st.selectbox(
    "Policy product — optional for claim questions",
    [
        "",
        "Health Secure Plus",
        "Family Care Gold",
        "Senior Health Shield",
        "Maternity Protect",
        "Critical Care Elite",
        "Car Shield Plus",
        "Motor Protect Comprehensive",
        "Two Wheeler Secure",
        "Global Travel Secure",
        "Student Travel Protect",
    ],
    format_func=lambda value: value or "Auto-detect",
)

st.caption(
    "Try: What is the status of CLM300500? "
    "Or: What is the maternity waiting period?"
)

with st.form("question_form"):
    question = st.text_area(
        "Your question",
        placeholder="Enter an insurance question",
    )

    submitted = st.form_submit_button("Ask Assistant")

if submitted:
    question = question.strip()

    if len(question) < 3:
        st.warning(
            "Please enter a question of at least 3 characters."
        )

    elif len(question) > 2000:
        st.warning(
            "Please keep your question within 2,000 characters."
        )

    else:
        try:
            with st.spinner(
                "Checking records and policy evidence..."
            ):
                response = requests.post(
                    f"{API_URL}/ask",
                    json={
                        "question": question,
                        "product_name": product_name,
                    },
                    timeout=180,
                )

            if response.ok:
                result = response.json()

                st.caption(f"Route: {result['route']}")
                st.markdown(result["answer"])

                sources = result.get("sources", [])

                if sources:
                    with st.expander("Retrieved policy evidence"):
                        for source in sources:
                            st.write(
                                f"**{source['evidence_id']}**"
                            )
                            st.write(source["text"])
                            st.divider()

                warnings = result.get("warnings", [])

                if warnings:
                    with st.expander("Review warnings"):
                        for warning in warnings:
                            st.warning(warning)

            else:
                try:
                    detail = response.json().get(
                        "detail",
                        "The API could not complete the request."
                    )
                except ValueError:
                    detail = (
                        "The API could not complete the request. "
                        "Check the FastAPI terminal."
                    )

                st.error(detail)
                st.caption(
                    f"API status: {response.status_code}"
                )

        except requests.exceptions.Timeout:
            st.error(
                "The request timed out. "
                "Check the FastAPI terminal before retrying."
            )

        except requests.exceptions.ConnectionError:
            st.error(
                "Cannot connect to FastAPI. "
                "Start the API server on port 8000."
            )

        except requests.exceptions.RequestException:
            st.error(
                "Request failed. Check the FastAPI terminal."
            )