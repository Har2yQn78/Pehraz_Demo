import streamlit as st
import requests
from PIL import Image
import io
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')
API_BASE = f"{BACKEND_URL}/api"

# Page config
st.set_page_config(
    page_title="PlantNet Identifier",
    page_icon="🌿",
    layout="wide"
)

# Title
st.title("🌿 PlantNet Plant Identifier")
st.markdown("Upload a plant image to identify the species and detect potential diseases")

# Sidebar
st.sidebar.header("Settings")
identification_mode = st.sidebar.radio(
    "Select Mode",
    ["Species Identification", "Disease Detection", "Both"]
)

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Upload Image")

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a plant image...",
        type=['jpg', 'jpeg', 'png'],
        help="Upload a clear image of the plant"
    )

    if uploaded_file is not None:
        # Display uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)

        # Organ selection for species identification
        if identification_mode in ["Species Identification", "Both"]:
            st.subheader("Select Plant Parts Visible")

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                has_leaf = st.checkbox("Leaf", value=True)
                has_flower = st.checkbox("Flower")
            with col_b:
                has_fruit = st.checkbox("Fruit")
                has_bark = st.checkbox("Bark")
            with col_c:
                has_habit = st.checkbox("Habit/Overall")
                has_other = st.checkbox("Other")

            # Collect selected organs
            organs = []
            if has_leaf: organs.append("leaf")
            if has_flower: organs.append("flower")
            if has_fruit: organs.append("fruit")
            if has_bark: organs.append("bark")
            if has_habit: organs.append("habit")
            if has_other: organs.append("other")

            if not organs:
                organs = ["leaf"]  # Default

        # Organ selection for disease detection
        if identification_mode in ["Disease Detection", "Both"]:
            st.subheader("Disease Detection Settings")
            disease_organ = st.selectbox(
                "Primary organ for disease detection",
                ["leaf", "flower", "fruit", "bark"],
                index=0
            )

        # Analyze button
        if st.button("🔍 Analyze Plant", type="primary", use_container_width=True):
            with col2:
                st.header("Results")

                # Species Identification
                if identification_mode in ["Species Identification", "Both"]:
                    with st.spinner("Identifying species..."):
                        try:
                            # Prepare request
                            uploaded_file.seek(0)
                            files = {'image': uploaded_file}
                            params = {'organs': ','.join(organs)}

                            # Make API request
                            response = requests.post(
                                f"{API_BASE}/identify",
                                files=files,
                                params=params,
                                timeout=30
                            )

                            if response.status_code == 200:
                                data = response.json()

                                st.success("✅ Species Identification Complete!")

                                # Display best match
                                if data.get('best_match'):
                                    st.subheader(f"Best Match: {data['best_match']}")

                                # Display results
                                st.markdown("### Top Matches")

                                for idx, result in enumerate(data.get('results', [])[:5], 1):
                                    with st.expander(
                                        f"{idx}. {result['scientific_name']} - {result['score']:.1f}% confidence",
                                        expanded=(idx == 1)
                                    ):
                                        st.markdown(f"**Scientific Name:** {result['scientific_name']}")

                                        if result.get('common_names'):
                                            st.markdown(f"**Common Names:** {', '.join(result['common_names'])}")

                                        if result.get('family'):
                                            st.markdown(f"**Family:** {result['family']}")

                                        if result.get('genus'):
                                            st.markdown(f"**Genus:** {result['genus']}")

                                        # Progress bar for confidence
                                        st.progress(result['score'] / 100)

                                # Show remaining requests if available
                                if data.get('remaining_identification_requests') is not None:
                                    st.info(f"ℹ️ Remaining API requests: {data['remaining_identification_requests']}")

                            else:
                                error_data = response.json()
                                st.error(f"❌ Error: {error_data.get('error', 'Unknown error')}")
                                if error_data.get('detail'):
                                    st.write(error_data['detail'])

                        except requests.exceptions.RequestException as e:
                            st.error(f"❌ Connection Error: Could not reach backend server")
                            st.write(f"Make sure the backend is running at {BACKEND_URL}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

                # Disease Detection
                if identification_mode in ["Disease Detection", "Both"]:
                    st.markdown("---")

                    with st.spinner("Detecting diseases..."):
                        try:
                            # Prepare request
                            uploaded_file.seek(0)
                            files = {'image': uploaded_file}
                            params = {'organ': disease_organ}

                            # Make API request
                            response = requests.post(
                                f"{API_BASE}/detect-disease",
                                files=files,
                                params=params,
                                timeout=30
                            )

                            if response.status_code == 200:
                                data = response.json()

                                st.success("✅ Disease Detection Complete!")

                                # Display best match
                                if data.get('best_match'):
                                    st.subheader(f"Most Likely: {data['best_match']}")

                                # Display results
                                st.markdown("### Disease Analysis")

                                if data.get('results'):
                                    for idx, result in enumerate(data.get('results', [])[:5], 1):
                                        with st.expander(
                                            f"{idx}. {result['disease_name']} - {result['score']:.1f}% probability",
                                            expanded=(idx == 1)
                                        ):
                                            st.markdown(f"**Disease:** {result['disease_name']}")

                                            if result.get('description'):
                                                st.markdown(f"**Description:** {result['description']}")

                                            # Progress bar for probability
                                            st.progress(result['score'] / 100)
                                else:
                                    st.info("No diseases detected or disease detection unavailable")

                            else:
                                error_data = response.json()
                                st.warning(f"⚠️ Disease Detection: {error_data.get('detail', 'Not available')}")

                        except Exception as e:
                            st.warning(f"⚠️ Disease detection unavailable: {str(e)}")

    else:
        with col2:
            st.info("👆 Upload an image to get started")

        st.markdown("""
        ### How to use:
        1. Upload a clear image of a plant
        2. Select which plant parts are visible in the image
        3. Choose identification mode (Species, Disease, or Both)
        4. Click "Analyze Plant" to get results

        ### Tips for best results:
        - Use clear, well-lit photos
        - Include flowers when possible (highest accuracy)
        - Avoid blurry or dark images
        - Show the plant part clearly
        """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
**Powered by:**
- [PlantNet API](https://my.plantnet.org/)
- Django + Django Ninja
- Streamlit
""")
