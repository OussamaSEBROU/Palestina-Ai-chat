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
        max_output_tokens=4000  # Increased token limit for deeper, longer responses
    )
)

# Enhanced prompt template for Palestine-related questions with trusted sources
def build_palestine_prompt(user_question):
    return f"""
You are an expert assistant dedicated to providing accurate, in-depth, and highly informative answers specifically about Palestine and related issues.

Your answers should focus entirely on Palestine-related topics. If the question is not related to Palestine, respond with: "Sorry! I'm trained just about Palestine Issue."

Respond to the user question with:
- Historical background with accurate timeline and context
- Structure your response like a professional news article or academic report with clear sections
- Base your information on trusted sources such as:
  * Al Jazeera (aljazeera.com) - Known for comprehensive coverage of Middle East issues
  * Metras (https://metras.co/) - Provides in-depth analysis on Palestinian affairs
  * https://www.aa.com.tr/ar
  * Academic books and peer-reviewed articles on Palestinian history and politics
  * Reports from human rights organizations (B'Tselem, Human Rights Watch, Amnesty International)
  * United Nations documents and resolutions
  * Palestinian academic institutions and research centers
- Include specific citations when possible (e.g., "According to Al Jazeera's reporting on [date]...")
- Provide factual, well-researched information on current events with accurate reporting
- Include relevant statistics and data from credible sources when discussing the humanitarian situation
- The answer should be in the same language as the input (be careful with this point)
- The response should be well-organized, ordered, and presented in a professional journalistic style
- Use titles and subtitles for clarity and structure when appropriate
- Present content in a clear, accessible manner while maintaining factual accuracy
- Ensure information is not biased towards Israel and remains truthful to Palestinian experiences
- When discussing boycotts or resistance, provide factual information about international law and human rights perspectives
- **Length**: If the response needs details, make it detailed not exceeding 1500 tokens but in a complete answer. For direct questions, make it concise (depending on the question), while remaining comprehensive within that limit.

Do not include information irrelevant to Palestine or unrelated topics.
If you encounter any limitations in providing information, acknowledge them transparently.

User question:
{user_question}

Your answer (detailed, accurate, context-aware, based on trusted sources):
"""

# Ask Gemini Pro for an in-depth response with improved error handling and news article formatting
def ask_about_palestine(user_question):
    prompt = build_palestine_prompt(user_question)
    try:
        response = model_text.generate_content(prompt)
        raw_text = response.text
        
        # Format the response to look more like a news article if it doesn't already have proper formatting
        if not any(header in raw_text for header in ["# ", "## ", "### "]):
            # Try to identify a title from the first line or create one
            lines = raw_text.split('\n')
            if len(lines) > 0 and len(lines[0]) < 100:  # First line is likely a title
                title = lines[0]
                content = '\n'.join(lines[1:])
            else:
                # Create a title based on the question
                title = f"Analysis: {user_question}"
                content = raw_text
            
            # Format as news article with proper sections
            formatted_text = f"""# {title.strip()}

*Source: Palestine AI Analysis based on Al Jazeera, Metras.co, and other trusted sources*

{content.strip()}

---
*This analysis is based on factual reporting from trusted sources including Al Jazeera, Metras.co, human rights organizations, and academic research on Palestine.*
"""
            return formatted_text
        else:
            # If it already has formatting, just add the source line at the top and citation at the bottom
            lines = raw_text.split('\n')
            source_line = "*Source: Palestine AI Analysis based on Al Jazeera, Metras.co, and other trusted sources*\n\n"
            citation_line = "\n\n---\n*This analysis is based on factual reporting from trusted sources, and academic research on Palestine.*"
            
            # Find the first heading
            for i, line in enumerate(lines):
                if line.startswith('#'):
                    # Insert source line after the first heading
                    lines.insert(i+1, source_line)
                    break
            
            # Add citation at the end
            lines.append(citation_line)
            return '\n'.join(lines)
            
    except Exception as e:
        error_message = str(e)
        # Handle specific error types
        if "quota" in error_message.lower():
            return "❌ API quota exceeded. Please try again later or contact the administrator."
        elif "blocked" in error_message.lower() or "safety" in error_message.lower():
            return "❌ The response was blocked due to safety concerns. Please rephrase your question or try a different topic related to Palestine."
        elif "timeout" in error_message.lower():
            return "❌ The request timed out. Please try again with a more specific question."
        else:
            return f"❌ Error getting response: {error_message}. Please try again or contact support."

# Function to simulate typing effect with improved performance
def typing_effect(text, delay=0.005):
    # For very long responses, reduce the typing effect to improve performance
    if len(text) > 1000:
        delay = 0.001
    
    output = ""
    placeholder = st.empty()
    for char in text:
        output += char
        placeholder.markdown(f"<div style='line-height: 1.5;'>{output}</div>", unsafe_allow_html=True)
        time.sleep(delay)

# Companies that support Israel (for boycott section) with verified alternatives
def get_boycott_companies():
    companies = {
        "Technology": {
            "Companies": [
                "Google", "Apple", "Microsoft", "Meta (Facebook)", "Amazon", "Intel", "HP", "IBM", "Oracle", "Cisco",
                "Dell", "Nvidia", "PayPal", "Wix", "Fiverr", "Monday.com", "Check Point", "Mobileye", "Waze", "Zoom"
            ],
            "Alternatives": [
                "Ecosia - Ethical search engine that plants trees (ecosia.org)", 
                "DuckDuckGo - Privacy-focused search engine (duckduckgo.com)",
                "Xiaomi/Oppo - Smartphone alternatives to Apple",
                "Linux Mint/Ubuntu - Free open-source alternatives to Windows", 
                "Element/Signal - Secure messaging alternatives to WhatsApp", 
                "Temu/Shein - Online shopping alternatives to Amazon", 
                "AMD Ryzen processors - Alternative to Intel", 
                "Acer/Asus - Computer alternatives to HP/Dell", 
                "LibreOffice/OpenOffice - Free alternatives to Microsoft Office",
                "ProtonMail/Tutanota - Privacy-focused email alternatives to Gmail",
                "Firefox/Tor Browser - Privacy-focused browsers"
            ]
        },
        "Food & Beverage": {
            "Companies": [
                "McDonald's", "Coca-Cola", "PepsiCo", "Nestlé", "Starbucks", "Burger King", "Domino's Pizza",
                "KFC", "Pizza Hut", "Subway", "Heinz", "Danone", "Mars", "Mondelez (Oreo)", "Kellogg's", 
                "Häagen-Dazs", "Sabra Hummus", "Strauss Group"
            ],
            "Alternatives": [
                "Al Baik - Popular Middle Eastern fast food chain", 
                "Almarai - Middle Eastern dairy and food producer",
                "Vimto - Popular alternative beverage in Middle East",
                "Mecca Cola - Alternative to Coca-Cola from France",
                "Zamzam Cola - Iranian alternative to American soft drinks",
                "Local coffee shops and cafes instead of Starbucks", 
                "Local bakeries and restaurants instead of fast food chains",
                "Alokozay Tea - Middle Eastern tea brand",
                "Ulker - Turkish confectionery company",
                "Pinar - Turkish dairy and food company"
            ]
        },
        "Fashion & Retail": {
            "Companies": [
                "H&M", "Zara", "Puma", "Nike", "Adidas", "Victoria's Secret", "Calvin Klein", "Tommy Hilfiger",
                "Marks & Spencer", "ASOS", "Skechers", "The North Face", "Timberland", "Levi's", "Gap", "Old Navy",
                "Ralph Lauren", "Lacoste", "Hugo Boss", "Uniqlo"
            ],
            "Alternatives": [
                "Li-Ning - Chinese sportswear company", 
                "Anta Sports - Chinese sportswear company",
                "Peak Sport - Chinese athletic footwear and apparel company",
                "361 Degrees - Chinese sportswear company",
                "Asics - Japanese sportswear company",
                "LC Waikiki - Turkish clothing company",
                "DeFacto - Turkish clothing retailer",
                "Koton - Turkish fashion retailer",
                "Splash - Middle Eastern fashion retailer",
                "Shukr - Islamic clothing company",
                "Modanisa - Islamic fashion retailer"
            ]
        },
        "Entertainment & Media": {
            "Companies": [
                "Disney", "Warner Bros", "Netflix", "Spotify", "Universal Music Group",
                "Fox", "Paramount", "Sony Pictures", "MGM", "DreamWorks", "NBC Universal",
                "CNN", "BBC", "New York Times", "The Washington Post", "The Guardian"
            ],
            "Alternatives": [
                "Al Jazeera - Qatar-based news network (aljazeera.com)", 
                "TRT World - Turkish public broadcaster (trtworld.com)",
                "Metras - Palestinian news and analysis (metras.co)",
                "Middle East Eye - Independent news organization (middleeasteye.net)",
                "Anghami - Middle Eastern music streaming service",
                "Shahid - Arabic streaming service from MBC Group",
                "Wavo - Middle Eastern streaming service",
                "StarzPlay - MENA region streaming service",
                "Press TV - Iranian news network",
                "CGTN - Chinese international news channel"
            ]
        },
        "Sports": {
            "Companies": [
                "Puma", "Nike", "Adidas", "Under Armour", "New Balance", "Reebok",
                "Wilson", "Spalding", "Gatorade", "Fitbit", "Garmin"
            ],
            "Alternatives": [
                "Li-Ning - Chinese sportswear company", 
                "Anta Sports - Chinese sportswear company",
                "Peak Sport - Chinese athletic footwear and apparel company",
                "361 Degrees - Chinese sportswear company",
                "Asics - Japanese sportswear company",
                "Fila - Italian/South Korean sportswear company",
                "Mizuno - Japanese sports equipment company",
                "Decathlon - French sporting goods retailer",
                "Xiaomi Mi Band - Alternative to Fitbit",
                "Huawei Watch - Alternative to Garmin"
            ]
        },
        "Cosmetics & Personal Care": {
            "Companies": [
                "L'Oréal", "Estée Lauder", "Clinique", "MAC Cosmetics", "Revlon", "Maybelline",
                "Garnier", "Dove", "Nivea", "Johnson & Johnson", "Colgate-Palmolive", "Procter & Gamble"
            ],
            "Alternatives": [
                "Mikyajy - Middle Eastern cosmetics brand", 
                "Flormar - Turkish cosmetics brand",
                "Golden Rose - Turkish cosmetics brand",
                "Farmasi - Turkish beauty and personal care company",
                "Hemani - Pakistani natural products company",
                "Wardah - Indonesian halal cosmetics",
                "One Two Cosmetics - Malaysian cosmetics brand",
                "Lush - Ethical cosmetics company with strong stance against occupation",
                "The Body Shop - Ethical cosmetics company",
                "Dr. Organic - Natural skincare products"
            ]
        },
        "Travel & Hospitality": {
            "Companies": [
                "Airbnb", "Booking.com", "Expedia", "TripAdvisor", "Marriott", "Hilton",
                "InterContinental", "Hyatt", "Delta Airlines", "American Airlines", "United Airlines"
            ],
            "Alternatives": [
                "Almosafer - Middle Eastern travel booking platform", 
                "Rehlat - Middle Eastern travel booking platform",
                "Tajawal - Middle Eastern travel booking platform",
                "HotelsCombined - Travel metasearch engine",
                "Qatar Airways - Middle Eastern airline",
                "Emirates - Middle Eastern airline",
                "Etihad Airways - Middle Eastern airline",
                "Turkish Airlines - Turkish airline",
                "Royal Jordanian - Jordanian airline",
                "Oman Air - Omani airline"
            ]
        }
    }
    return companies

# App UI with enhanced professional features
def main():
    st.set_page_config(
        page_title="Palestine AI Bot", 
        page_icon="🕊️", 
        layout="wide"
    )

    # Custom CSS for a more professional look
    st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .stTextInput > div > div > input {
        border-radius: 10px;
    }
    .stButton > button {
        border-radius: 10px;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
    }
    .stExpander {
        border-radius: 10px;
        border: 1px solid #e6e6e6;
    }
    h1, h2, h3 {
        color: #1f77b4;
    }
    .quote-box {
        border-left: 4px solid #1f77b4;
        padding-left: 15px;
        margin-top: 20px;
        font-size: 1.2em;
        font-weight: bold;
        color: #1f77b4;
    }
    .quote-author {
        text-align: right;
        color: #555555;
        font-style: italic;
    }
    .team-member {
        padding: 5px 0;
        border-bottom: 1px solid #f0f0f0;
    }
    .boycott-category {
        font-weight: bold;
        color: #d62728;
        margin-top: 10px;
    }
    .boycott-company {
        margin-left: 15px;
        padding: 2px 0;
    }
    .boycott-alternative {
        margin-left: 15px;
        padding: 2px 0;
        color: #2ca02c;
    }
    .footer {
        text-align: center;
        margin-top: 30px;
        padding: 10px;
        font-size: 0.8em;
        color: #666;
    }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/0/00/Flag_of_Palestine.svg", width=250)
        st.title("Palestine AI")
        
        # Team Section
        with st.expander("Our Team", expanded=False):
            st.markdown("### Elkalem-Imrou Height School")
            st.markdown("In collaboration with Erinov Company")
            st.markdown("#### Team Members:")
            
            team_members = [
                "Nchachebi Abdelghani",
                "Khtara Hafssa",
                "Sirine Adoun",
                "Ycine Boukermouch",
                "Chihani Zineb",
                "Chihani Bouchra",
                "Mahdia Abouna",
                "Rahma Elalouani",
                "Redouan Rekik Sadek",
                "Abdellatif Abdelnour",
                "Abderhman Daoud",
                "Bahedi Bouchra",
                "Chacha Abdelazize",
                "Meriama Hadjyahya",
                "Adouad Sanae",
                "Yasser Kasbi",
                "Gueddi Amine",
                "Youcef Abbouna"
            ]
            
            for member in team_members:
                st.markdown(f"<div class='team-member'>• {member}</div>", unsafe_allow_html=True)
        
        # Boycott Section
        with st.expander("Stand With Gaza - Boycott", expanded=False):
            st.markdown("### Companies Supporting Israel")
            st.markdown("""
            The boycott movement aims to apply economic and political pressure on Israel to comply with international law and Palestinian rights. 
            Below is a list of companies that have been identified as supporting Israel, along with alternatives you can use instead:
            """)
            
            companies = get_boycott_companies()
            for category, data in companies.items():
                st.markdown(f"<div class='boycott-category'>{category}</div>", unsafe_allow_html=True)
                
                # Display companies to boycott
                st.markdown("<div style='margin-left: 15px;'><strong>Companies to Boycott:</strong></div>", unsafe_allow_html=True)
                for company in data["Companies"]:
                    st.markdown(f"<div class='boycott-company'>• {company}</div>", unsafe_allow_html=True)
                
                # Display alternatives
                st.markdown("<div style='margin-left: 15px; margin-top: 10px; color: #2ca02c;'><strong>Alternatives:</strong></div>", unsafe_allow_html=True)
                for alternative in data["Alternatives"]:
                    st.markdown(f"<div class='boycott-alternative'>✓ {alternative}</div>", unsafe_allow_html=True)
                
                st.markdown("<hr style='margin: 15px 0; border-color: #f0f0f0;'>", unsafe_allow_html=True)
            
            st.markdown("""
            ### How to Support Gaza
            
            1. **Boycott Products**: Avoid purchasing products from companies supporting Israel
            2. **Choose Alternatives**: Use the suggested alternatives or find local options
            3. **Raise Awareness**: Share information about the situation in Gaza
            4. **Donate**: Support humanitarian organizations working in Gaza
            5. **Advocate**: Contact your representatives to demand action
            6. **Join Protests**: Participate in peaceful demonstrations
            
            Remember that economic pressure through boycotts has historically been an effective non-violent resistance strategy.
            """)
        
        # Help Section
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
        
        # About Us Section
        with st.expander("About Us", expanded=False):
            st.markdown("#### Palestine AI Chat")
            st.markdown("This app was developed to provide in-depth, AI-powered insights into the Palestinian cause.")
            st.markdown("""
            **Version:** 1.1.0
            
            #### Features
            - AI-Powered Insights about Palestine
            - Focus on History, Humanitarian Issues, and Current Events
            - Multi-Language Support
            - Accurate and Context-Aware Responses
            - Boycott Information and Support Resources
            
            © 2025 Palestine AI Team. All rights reserved.
            
            [Contact Us](mailto:your-email@example.com?subject=Palestine%20Info%20Bot%20Inquiry&body=Dear%20Palestine%20Info%20Bot%20Team,%0A%0AWe%20are%20writing%20to%20inquire%20about%20[your%20inquiry]%2C%20specifically%20[details%20of%20your%20inquiry].%0A%0A[Provide%20additional%20context%20and%20details%20here].%0A%0APlease%20let%20us%20know%20if%20you%20require%20any%20further%20information%20from%20our%20end.%0A%0ASincerely,%0A[Your%20Company%20Name]%0A[Your%20Name]%0A[Your%20Title]%0A[Your%20Phone%20Number]%0A[Your%20Email%20Address])
            """)

    # Main content area
    st.title("Palestine AI - From the river to the sea")

    # Quote of the Day section in a professional style
    st.markdown("""
    <div class="quote-box">
        "The issue of Palestine is a trial that God has tested your conscience, resolve, wealth, and unity with."
    </div>
    <div class="quote-author">
        — Al-Bashir Al-Ibrahimi
    </div>
    """, unsafe_allow_html=True)

    # Gaza Photos Section - Documentation of Israeli Actions
    st.markdown("## Documenting Israeli Actions in Gaza")
    st.markdown("""
    <div style="background-color: rgba(220, 53, 69, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <p style="font-size: 0.9em; color: #721c24;">
            <strong>Warning:</strong> The following section contains images that document the humanitarian crisis in Gaza. 
            These images may be disturbing but serve as important documentation of the situation.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Photo gallery with 3 columns
    photo_col1, photo_col2, photo_col3 = st.columns(3)
    
    with photo_col1:
        st.image("https://cdnuploads.aa.com.tr/uploads/Contents/2024/10/29/thumbs_b_c_c3c8c68631ffe978cd8a667c29ea324c.jpg?v=231426", 
                caption="Israel Has Killed 11,825 Students Since October 7, 2023
According to a report by the Ministry of Education and Higher Education, the victims include 11,057 school students from Gaza and 681 university students.")
        st.image("https://cdnuploads.aa.com.tr/uploads/Contents/2025/04/12/thumbs_b_c_07f091fd689a62b74ba88ac82f792a7a.jpg?v=132104", 
                caption="Water Turned into a Slow Killing Weapon for Palestinians
The Government Media Office stated in a statement that Israel recently cut the two water lines of the "Mekorot" company connecting to East Gaza and the Central Governorate, amid a systematic destruction of the water sector since the beginning of the genocide.")
    
    with photo_col2:
        st.image("https://cdnuploads.aa.com.tr/uploads/Contents/2024/02/12/thumbs_b_c_f8bcb411a278fb1651f1202ba8e881ca.jpg?v=101455", 
                caption="Displaced Palestinians: We Are Staying in Rafah and Will Not Leave")
        st.image("https://cdnuploads.aa.com.tr/uploads/Contents/2024/04/01/thumbs_b_c_62b1f7cf295ca688d9250ae060b99f13.jpg?v=232954", 
                caption="Al-Shifa Medical Complex: Witness to Israel’s Crimes (Report)
Marwan Abu Sa’da, the hospital’s administrative director, told Anadolu: The Israeli army booby-trapped the hospital buildings, destroyed them, and set fire to the oxygen stations, power generators, and all departments.")
    
    with photo_col3:
        st.image("https://cdnuploads.aa.com.tr/uploads/Contents/2025/04/15/thumbs_b_c_5d0659ec6a4e53bed7da27b61e5d4bc7.jpg?v=191857", 
                caption="The food that entered Gaza during the ceasefire period,according to a statement by the agency on the "X" platform.")
        st.image("https://cdnuploads.aa.com.tr/uploads/Contents/2025/04/15/thumbs_b_c_48ad44ea9ec8a40efe3c13d73064c648.jpg?v=010802", 
                caption="Set to Receive 3,000 U.S. Aerial Munitions Soon to Continue Gaza War The Hebrew newspaper reported that the army is also expected to receive over 10,000 additional aerial munitions to replenish stockpiles depleted by fighting on multiple fronts.")
    
    st.markdown("""
    <div style="font-size: 0.9em; margin-top: 10px; margin-bottom: 30px; color: #555;">
        These images document the humanitarian crisis in Gaza since October 7, 2023. For more documentation and reporting, visit 
        <a href="https://www.aljazeera.com/where/palestine/" target="_blank">Al Jazeera Palestine coverage</a> or 
        <a href="https://metras.co/" target="_blank">Metras.co</a>.
    </div>
    """, unsafe_allow_html=True)

    # Information cards in a grid layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Historical Context
        Palestine has a rich history dating back thousands of years. The region has been home to diverse populations and has been under various rulers throughout history, including the Ottoman Empire and British Mandate before the establishment of Israel in 1948.
        """)
    
    with col2:
        st.markdown("""
        ### Current Situation
        The ongoing conflict has resulted in significant humanitarian challenges for Palestinians, particularly in Gaza where blockades have restricted access to essential resources and services since 2007.
        """)

    # User input section with enhanced styling
    st.markdown("<hr style='margin: 30px 0;'>", unsafe_allow_html=True)
    st.markdown("### Ask Your Question")
    st.markdown("Get accurate, detailed information about Palestine's history, current events, and humanitarian issues.")
    
    user_question = st.text_input("", placeholder="Type your question about Palestine here...")
    
    # Add a submit button for better UX
    submit_button = st.button("Get Answer")

    # Process the question when submitted
    if user_question and submit_button:
        with st.spinner("Generating comprehensive answer..."):
            answer = ask_about_palestine(user_question)
            
            # Create a container with better styling for the answer
            answer_container = st.container()
            with answer_container:
                st.markdown("<div style='background-color: #f0f7fb; padding: 20px; border-radius: 10px; border-left: 5px solid #1f77b4;'>", unsafe_allow_html=True)
                # Typing effect for response
                with st.empty():  # Create an empty placeholder to display the typing effect
                    typing_effect(answer)
                st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("<div class='footer'>Palestine AI - Developed by Elkalem-Imrou Height School in collaboration with Erinov Company</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
