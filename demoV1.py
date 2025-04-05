import streamlit as st
import google.generativeai as genai
import time
import os

# Configure Gemini with your API key
google_api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=google_api_key)

# Load Gemini models
model_text = genai.GenerativeModel(
    model_name="gemini-2.0-flash-thinking-exp-01-21",
    generation_config=genai.types.GenerationConfig(
        temperature=0.7,
        top_p=0.95,
        top_k=40,
        max_output_tokens=4000  # Increase token limit for deeper, longer responses
    )
)

# Prompt template for Palestine-related questions
def build_palestine_prompt(user_question):
    return f"""
You are an expert assistant dedicated to providing accurate, in-depth, and highly informative answers specifically about Palestine and related issues.

Your answers should focus entirely on Palestine, including its history, current events, humanitarian issues, political context, and geopolitical relations. If not, say "Sorry! I'm trained just about Palestine Issue."

Respond to the user question with:
- Detailed historical background,
- Rely on precise, scientific, and historical sources,with Very trustworthy sources, 
- Well-researched current events,
- Conversation coherence,
- Insight into the humanitarian situation,
- The answer should be in the same language as the input (be careful in that point).
- The response should be well-organized, logically ordered, and presented in a profeesional style.
- Titles and subtitles should have proper sizes for clarity and structure.
- The content should be easy to read, with relevant details presented clearly and concisely, 
- The results must not be biased towards Israel and should be reliable and truthful, 
- **Length**: if the The response need details make it detailed not exceeding  than **2000 tokens** but in complet answer. But if the question are direct make it less (depend the questios), and be comprehensive within that limit.
Do not include information irrelevant to Palestine or unrelated topics.

User question:
{user_question}

Your answer (detailed, accurate, context-aware):
"""

# Ask Gemini Pro for an in-depth response
def ask_about_palestine(user_question):
    prompt = build_palestine_prompt(user_question)
    try:
        response = model_text.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error getting response: {str(e)}"

# Function to simulate typing effect
def typing_effect(text, delay=0.005):
    output = ""
    for char in text:
        output += char
        st.markdown(f"<p>{output}</p>", unsafe_allow_html=True)
        time.sleep(delay)

# App UI
def main():
    st.set_page_config(page_title="Palestina AI Bot", page_icon="🕊️", layout="wide")

    # Sidebar
    with st.sidebar:
        # Help Section (expanded first)
        with st.expander("Help", expanded=True):
            st.markdown("### How to Use the App")
            st.markdown("""
- **Ask Questions**: You can ask anything related to **Palestine's history, current events, or humanitarian issues**.
- **Multi-Languages Supported**: You can ask in any language.
- **Dark Mode**: To switch to dark mode, go to **Settings** > **Choose app theme** > **Dark Mode**.
- **App Features**:
  - **In-depth answers** focused only on Palestine.
  - **Context-aware** responses tailored to your question.
  - **Accurate, detailed information** backed by AI.
            """)
        st.markdown("---")
        
        # About Us Section (collapsed)
        with st.expander("About Us", expanded=False):
            st.markdown("#### Palestina AI Chat")
            st.markdown("This app was developed to provide in-depth, AI-powered insights into the Palestinian cause.")
            st.markdown("""
          
            **Version:** 1.0.0
          
            #### Features
            - AI-Powered Insights about Palestine
            - Focus on History, Humanitarian Issues, and Current Events
            - Multi-Language Support
            - Accurate and Context-Aware Responses

           © 2025 Palestina AI Team. All rights reserved.

            [Contact Us](mailto:your-email@example.com?subject=Palestine%20Info%20Bot%20Inquiry&body=Dear%20Palestine%20Info%20Bot%20Team,%0A%0AWe%20are%20writing%20to%20inquire%20about%20[your%20inquiry]%2C%20specifically%20[details%20of%20your%20inquiry].%0A%0A[Provide%20additional%20context%20and%20details%20here].%0A%0APlease%20let%20us%20know%20if%20you%20require%20any%20further%20information%20from%20our%20end.%0A%0ASincerely,%0A[Your%20Company%20Name]%0A[Your%20Name]%0A[Your%20Title]%0A[Your%20Phone%20Number]%0A[Your%20Email%20Address])
            """)

    st.title("Palestina AI - From the river to the sea ")

    # Quote of the Day section in a professional style
    st.markdown("""
    <div style="border-left: 4px solid #1f77b4; padding-left: 15px; margin-top: 20px; font-size: 1.2em; font-weight: bold; color: #1f77b4;">
        "The issue of Palestine is a trial that God has tested your conscience, resolve, wealth, and unity with."
    </div>
    <div style="text-align: right; color: #555555; font-style: italic;">
        — Al-Bashir Al-Ibrahimi
    </div>
    """, unsafe_allow_html=True)

    user_question = st.text_input("Ask about Palestine (history, events, humanitarian issues, etc):")

    if user_question:
        with st.spinner("Generating answer..."):
            answer = ask_about_palestine(user_question)
            
            # Typing effect for response
            with st.empty():  # Create an empty placeholder to display the typing effect
                typing_effect(answer)

if __name__ == "__main__":
    main()
