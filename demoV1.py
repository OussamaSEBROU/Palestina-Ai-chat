import streamlit as st
import google.generativeai as genai
import time
import os
import requests
from PIL import Image
import io
import base64
import uuid # Added for unique chat IDs
from streamlit_copy_to_clipboard import st_copy_to_clipboard # Added for copy functionality

# --- Original Configuration and Model Setup --- Start ---
# Configure Gemini with your API key
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    # Try to get it from Streamlit secrets if not in env var
    try:
        google_api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        st.error("Google API Key not found. Please set it as an environment variable or Streamlit secret.")
        st.stop()

genai.configure(api_key=google_api_key)

# Load Gemini models
# Wrap model loading in a try-except block for better error handling
try:
    model_text = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest", # Using a recommended model, adjust if needed
        generation_config=genai.types.GenerationConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_output_tokens=4000
        ),
        # Add safety settings if needed, e.g.:
        # safety_settings=[
        #     { "category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE" },
        #     { "category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE" },
        #     { "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE" },
        #     { "category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE" },
        # ]
    )
except Exception as e:
    st.error(f"Failed to load Generative Model: {e}")
    st.stop()

# --- Original Configuration and Model Setup --- End ---

# --- Original Helper Functions --- Start ---
# Enhanced prompt template for Palestine-related questions with more reliable sources
def build_palestine_prompt(user_question):
    # This function remains largely the same, defining the persona and instructions.
    # Context will be handled by passing message history separately.
    return f"""
You are an expert assistant dedicated to providing accurate, in-depth, and highly informative answers specifically about Palestine and related issues.

Your answers should focus entirely on Palestine-related topics. If the question is not related to Palestine, respond with: "Sorry! I'm trained just about Palestine Issue."

Respond to the user question with:
- Historical background with accurate timeline and context
- Structure your response like a professional news article or academic report with clear sections
- Base your information on trusted sources such as:
  * Al Jazeera (aljazeera.com) - Known for comprehensive coverage of Middle East issues
  * Metras (https://metras.co/) - Provides in-depth analysis on Palestinian affairs
  * Electronic Intifada (electronicintifada.net) - News and analysis on Palestine
  * Anadolu Agency (aa.com.tr) - Turkish state-run news agency with Middle East coverage
  * Palestine Chronicle (palestinechronicle.com) - Palestinian perspective on news
  * Institute for Palestine Studies (palestine-studies.org) - Academic research
  * B'Tselem (btselem.org) - Israeli human rights organization documenting abuses
  * Human Rights Watch (hrw.org) - International human rights monitoring
  * Amnesty International (amnesty.org) - Global human rights organization
  * United Nations Relief and Works Agency (unrwa.org) - UN agency for Palestinian refugees
  * UN Office for the Coordination of Humanitarian Affairs (ochaopt.org) - UN humanitarian reports
  * Academic books by scholars like Ilan Pappé, Edward Said, Rashid Khalidi, and Noam Chomsky
  * Peer-reviewed journals on Middle Eastern studies and international relations
  * Palestinian academic institutions and research centers
  * Historical archives and primary source documents

- Include specific citations when possible (e.g., "According to Al Jazeera's reporting on [date]..." or "As documented by Human Rights Watch in their [year] report...") and real links.
- Provide factual, well-researched information on current events with accurate reporting
- Include relevant statistics and data from credible sources when discussing the humanitarian situation
- The answer should be in the same language as the input (be careful with this point)
- The response should be well-organized, ordered, and presented in a professional journalistic hystorics style.
- Use titles and subtitles for clarity and structure when appropriate
- Present content in a clear, accessible manner while maintaining factual accuracy
- Ensure information is not biased towards Israel and remains truthful to Palestinian experiences
- When discussing boycotts or resistance, provide factual information about international law and human rights perspectives
- Length: If the response needs details, make it detailed not exceeding 2000 tokens but in a complete answer. For direct questions, make it concise (depending on the question), while remaining comprehensive within that limit.

Do not include information irrelevant to Palestine or unrelated topics.
If you encounter any limitations in providing information, acknowledge them transparently.

User question:
{user_question}

Your answer (detailed, accurate, context-aware):
"""

# Ask Gemini Pro for an in-depth response with improved error handling and context
def ask_about_palestine_with_context(user_question, chat_history):
    # Construct the history in the format expected by the API
    api_history = []
    system_instruction = build_palestine_prompt("") # Get the base instruction
    # Find the start of the user question placeholder to remove it
    instruction_end_marker = "User question:"
    if instruction_end_marker in system_instruction:
        system_instruction = system_instruction.split(instruction_end_marker)[0].strip()

    # Add system instruction if the API supports it or prepend to the first user message if not.
    # For gemini-1.5-flash, we can include it implicitly via the prompt structure or explicitly if supported.
    # Let's structure history correctly:
    for msg in chat_history:
        role = 'user' if msg['role'] == 'user' else 'model' # API uses 'model' for assistant
        api_history.append({'role': role, 'parts': [msg['content']]})

    # Add the current user question
    # We apply the prompt structure here, but the core instruction is implicitly carried by the model
    # or should be part of the history if the API requires it.
    # Let's try sending the raw user question as the last part of the history.
    api_history.append({'role': 'user', 'parts': [user_question]})

    # Prepend the main instruction to the history for clarity if needed
    # This depends on how the specific model handles system prompts vs history
    # Let's try adding the core instruction as the very first 'user' message conceptually
    # Or rely on the model remembering instructions from the initial prompt structure.
    # A safer approach for context: use start_chat if issues arise.
    # For now, attempt with generate_content and formatted history.

    # Construct the final prompt including the base instructions and the latest question
    # This might be redundant if history works well, but ensures instructions are present.
    # final_prompt_text = build_palestine_prompt(user_question)

    try:
        # Pass the history to the model
        # The model should use the history for context and follow instructions
        response = model_text.generate_content(api_history)
        return response.text
    except Exception as e:
        error_message = str(e)
        st.error(f"Error generating response: {error_message}") # Show error in UI
        # Handle specific error types
        if "quota" in error_message.lower():
            return "❌ API quota exceeded. Please try again later or contact the administrator."
        elif "blocked" in error_message.lower() or "safety" in error_message.lower():
            # Try to get more details if available
            try:
                details = response.prompt_feedback
                return f"❌ The response was blocked due to safety concerns: {details}. Please rephrase your question or try a different topic related to Palestine."
            except:
                 return "❌ The response was blocked due to safety concerns. Please rephrase your question or try a different topic related to Palestine."
        elif "timeout" in error_message.lower():
            return "❌ The request timed out. Please try again with a more specific question."
        else:
            # Log the full error for debugging if possible
            print(f"Unhandled API Error: {error_message}")
            return f"❌ An unexpected error occurred while getting the response. Please try again or contact support."

# Function to simulate typing effect (remains the same)
def typing_effect(text, placeholder, delay=0.003):
    if not isinstance(text, str):
        text = str(text) # Ensure text is a string

    if len(text) > 1000:
        delay = 0.001

    output = ""
    # Use the provided placeholder
    for char in text:
        output += char
        placeholder.markdown(f"<div style='line-height: 1.5;'>{output}</div>", unsafe_allow_html=True)
        time.sleep(delay)
    # Final update to ensure the full text is displayed correctly
    placeholder.markdown(f"<div style='line-height: 1.5;'>{output}</div>", unsafe_allow_html=True)


# Function to check if query is related to Palestine (remains the same)
def is_palestine_related(query):
    palestine_keywords = [
        "palestine", "palestinian", "gaza", "west bank", "jerusalem", "al-quds",
        "israel", "israeli", "occupation", "intifada", "nakba", "hamas", "fatah",
        "plo", "bds", "boycott", "settlement", "settler", "zionism", "zionist",
        "al-aqsa", "dome of rock", "hebron", "ramallah", "bethlehem", "nablus",
        "jenin", "rafah", "khan younis", "unrwa", "refugee", "right of return",
        "oslo", "two-state", "one-state", "apartheid", "wall", "barrier",
        "checkpoint", "blockade", "olive", "resistance", "martyr", "shahid",
        "idf", "arab", "middle east", "levant", "holy land", "balfour",
        "1948", "1967", "intifada", "uprising", "protest", "demonstration",
        "solidarity", "human rights", "international law", "un resolution",
        "occupation", "colonization", "annexation", "displacement", "demolition",
        "prisoner", "detention", "administrative detention", "hunger strike",
        "flotilla", "aid", "humanitarian", "ceasefire", "peace process",
        "negotiation", "mediation", "conflict", "war", "attack", "bombing",
        "airstrike", "rocket", "tunnel", "border", "crossing", "siege",
        "sanction", "embargo", "economy", "water", "electricity", "infrastructure",
        "education", "health", "culture", "heritage", "identity", "diaspora",
        "return", "citizenship", "stateless", "nationality", "flag", "keffiyeh",
        "olive tree", "key", "map", "border", "1948", "1967", "partition",
        "resolution", "un", "unesco", "icj", "icc", "amnesty", "hrw", "btselem",
        "pchr", "al haq", "adalah", "badil", "passia", "miftah", "pngo",
        "pflp", "dflp", "jihad", "islamic", "christian", "muslim", "jew",
        "holy site", "temple mount", "haram al-sharif", "church of nativity",
        "ibrahimi mosque", "cave of patriarchs", "rachel's tomb", "joseph's tomb",
        "from the river to the sea", "free palestine", "save palestine"
    ]
    query_lower = query.lower()
    for keyword in palestine_keywords:
        if keyword in query_lower:
            return True
    return False

# Function to get detailed boycott data EN (remains the same)
def get_boycott_data_EN():
    return {
        "Food & Beverages": {
            "companies": [
                {"name": "Starbucks", "reason": "Howard Schultz, founder and major shareholder of Starbucks, is a staunch supporter of Israel who invests heavily in Israel's economy, including a recent $1.7 billion investment in cybersecurity startup Wiz.", "action": "Don't buy Starbucks products. Don't sell Starbucks products. Don't work for Starbucks.", "alternatives": ["Caffe Nero", "Local independent cafes", "Local Arab cafes"]},
                {"name": "Coca-Cola", "reason": "Coca-Cola has a bottling plant in the Atarot Industrial Zone, an illegal Israeli settlement in occupied East Jerusalem. The company continues to support Israel's economy despite human rights violations.", "action": "Boycott all Coca-Cola products, including Sprite, Fanta, and other associated brands.", "alternatives": ["Local beverage brands", "Homemade sparkling water", "Natural juices"]},
                {"name": "McDonald's", "reason": "McDonald's Israel provided thousands of free meals to Israeli soldiers during military operations in Gaza. The Israeli franchise has openly supported military actions against Palestinians.", "action": "Don't eat at McDonald's.", "alternatives": ["Local restaurants", "Local fast food chains"]},
                {"name": "Nestlé", "reason": "Nestlé has been operating in Israel since 1995 and has production facilities in contested areas. The company has been criticized for exploiting Palestinian water resources.", "action": "Avoid Nestlé products, including bottled water, cereals, and dairy products.", "alternatives": ["Local brands", "Artisanal products", "Filtered tap water"]},
                {"name": "PepsiCo", "reason": "PepsiCo operates in Israel and has facilities in contested territories. The company continues its activities despite calls for boycott.", "action": "Avoid all PepsiCo products, including Lay's chips, Doritos, and Pepsi beverages.", "alternatives": ["Local beverages", "Locally manufactured snacks"]},
                {"name": "Sabra Hummus", "reason": "Sabra is a joint venture between PepsiCo and the Strauss Group, an Israeli company that provides support to elite units of the Israeli military involved in human rights violations.", "action": "Don't buy Sabra hummus.", "alternatives": ["Homemade hummus", "Local Arab hummus brands"]}
            ]
        },
        "Technology": {
            "companies": [
                {"name": "HP (Hewlett-Packard)", "reason": "HP provides technologies used in Israel's control and surveillance system, including for military checkpoints. Its technologies are used to maintain the apartheid and segregation system.", "action": "Don't buy HP products, including computers, printers, and supplies.", "alternatives": ["Lenovo", "Brother", "Epson", "Asian brands"]},
                {"name": "Microsoft", "reason": "Microsoft invested $1.5 billion in an Israeli AI company and has a major R&D center in Israel. The company works closely with the Israeli military to develop military technologies.", "action": "Use open source alternatives when possible.", "alternatives": ["Linux", "LibreOffice", "Open source alternatives"]},
                {"name": "Google", "reason": "Google signed a $1.2 billion cloud computing contract with the Israeli government (Project Nimbus). This technology is used for surveillance and targeting of Palestinians.", "action": "Use alternative search engines and services.", "alternatives": ["DuckDuckGo", "ProtonMail", "Firefox"]},
                {"name": "Apple", "reason": "Apple has significant investments in Israel and collaborates with Israeli companies involved in surveillance and military technology.", "action": "Consider alternatives to Apple products.", "alternatives": ["Samsung", "Xiaomi", "Huawei", "Android phones"]},
                {"name": "Intel", "reason": "Intel is one of the largest employers in the Israeli tech sector with several plants and R&D centers. The company contributes significantly to Israel's economy.", "action": "Prefer AMD processors when possible.", "alternatives": ["AMD", "ARM", "Other processor manufacturers"]}
            ]
        },
        "Fashion & Clothing": {
            "companies": [
                {"name": "Puma", "reason": "Puma sponsors the Israel Football Association, which includes teams in illegal settlements. This support legitimizes the occupation and violations of international law.", "action": "Don't buy Puma products.", "alternatives": ["Adidas", "New Balance", "Local brands", "Li-Ning"]},
                {"name": "Skechers", "reason": "Skechers has stores in illegal Israeli settlements and maintains business partnerships in Israel, contributing to the occupation economy.", "action": "Boycott Skechers shoes and clothing.", "alternatives": ["Brooks", "ASICS", "Ethical brands"]},
                {"name": "H&M", "reason": "H&M operates stores in Israel, including in contested areas. The company has ignored calls to cease operations in occupied territories.", "action": "Don't shop at H&M.", "alternatives": ["Ethical fashion brands", "Second-hand clothing"]},
                {"name": "Zara", "reason": "Zara has stores in Israel and sources from Israeli suppliers. The brand has been criticized for its lack of ethical stance regarding the occupation.", "action": "Avoid shopping at Zara.", "alternatives": ["Local brands", "Independent boutiques"]},
                {"name": "Victoria's Secret", "reason": "Victoria's Secret is owned by L Brands, which has significant investments in Israel and stores in contested areas.", "action": "Boycott Victoria's Secret products.", "alternatives": ["Ethical lingerie brands", "Local brands"]}
            ]
        },
        "Cosmetics": {
            "companies": [
                {"name": "L'Oréal", "reason": "L'Oréal operates in Israel and has acquired Israeli cosmetics companies. The company has facilities in contested territories and benefits from the occupation.", "action": "Boycott L'Oréal products and its associated brands.", "alternatives": ["The Body Shop", "Lush", "Natural brands", "Halal cosmetics"]},
                {"name": "Estée Lauder", "reason": "Estée Lauder chairman, Ronald Lauder, is a strong supporter of Israel and funds pro-Israel organizations. He has publicly defended Israeli military actions against Palestinians.", "action": "Don't buy Estée Lauder products and its associated brands.", "alternatives": ["Ethical brands", "Local brands"]},
                {"name": "Revlon", "reason": "Revlon has significant operations in Israel and has been criticized for its support of Israeli policies.", "action": "Avoid Revlon products.", "alternatives": ["Cruelty-free brands", "Vegan cosmetics"]}
            ]
        },
        "Finance": {
            "companies": [
                {"name": "AXA", "reason": "AXA invests in Israeli banks that finance illegal settlements in occupied Palestinian territory.", "action": "Divest from AXA and choose ethical insurance providers.", "alternatives": ["Ethical insurance companies", "Local providers"]}
            ]
        },
        "Services": {
            "companies": [
                {"name": "G4S/Allied Universal", "reason": "G4S provides security services and equipment to Israeli prisons where Palestinian political prisoners are held, often without trial and under harsh conditions. It also services checkpoints and settlements.", "action": "Campaign against G4S contracts.", "alternatives": ["Local security companies", "Ethical service providers"]}
            ]
        }
    }

# Function to get detailed boycott data AR (remains the same)
def get_boycott_data_AR():
    return {
        "الأغذية والمشروبات": {
            "companies": [
                {"name": "ستاربكس", "reason": "هوارد شولتز، مؤسس ستاربكس والمساهم الرئيسي فيها، هو مؤيد قوي لإسرائيل ويستثمر بكثافة في اقتصادها، بما في ذلك استثمار حديث بقيمة 1.7 مليار دولار في شركة الأمن السيبراني Wiz.", "action": "لا تشتري منتجات ستاربكس. لا تبيع منتجات ستاربكس. لا تعمل في ستاربكس.", "alternatives": ["كافيه نيرو", "المقاهي المحلية المستقلة", "المقاهي العربية المحلية"]},
                {"name": "كوكا كولا", "reason": "تمتلك شركة كوكا كولا مصنع تعبئة في منطقة عطروت الصناعية، وهي مستوطنة إسرائيلية غير شرعية في القدس الشرقية المحتلة. تواصل الشركة دعم اقتصاد إسرائيل على الرغم من انتهاكات حقوق الإنسان.", "action": "قاطع جميع منتجات كوكا كولا، بما في ذلك سبرايت وفانتا والعلامات التجارية الأخرى المرتبطة بها.", "alternatives": ["العلامات التجارية المحلية للمشروبات", "المياه الغازية محلية الصنع", "العصائر الطبيعية"]},
                {"name": "ماكدونالدز", "reason": "قدمت ماكدونالدز إسرائيل آلاف الوجبات المجانية للجنود الإسرائيليين خلال العمليات العسكرية في غزة. وقد دعمت السلسلة الإسرائيلية علنًا الأعمال العسكرية ضد الفلسطينيين.", "action": "لا تأكل في ماكدونالدز.", "alternatives": ["المطاعم المحلية", "سلاسل الوجبات السريعة المحلية"]},
                {"name": "نستله", "reason": "تعمل نستله في إسرائيل منذ عام 1995 ولديها منشآت إنتاج في مناطق متنازع عليها. وقد تم انتقاد الشركة لاستغلالها موارد المياه الفلسطينية.", "action": "تجنب منتجات نستله، بما في ذلك المياه المعبأة والحبوب ومنتجات الألبان.", "alternatives": ["العلامات التجارية المحلية", "المنتجات الحرفية", "مياه الصنبور المفلترة"]},
                {"name": "بيبسيكو", "reason": "تعمل بيبسيكو في إسرائيل ولديها منشآت في مناطق متنازع عليها. تواصل الشركة أنشطتها على الرغم من دعوات المقاطعة.", "action": "تجنب جميع منتجات بيبسيكو، بما في ذلك رقائق ليز ودوريتوس ومشروبات بيبسي.", "alternatives": ["المشروبات المحلية", "الوجبات الخفيفة المصنعة محليًا"]},
                {"name": "صبرا حمص", "reason": "صبرا هو مشروع مشترك بين بيبسيكو ومجموعة شتراوس، وهي شركة إسرائيلية تقدم الدعم لوحدات النخبة في الجيش الإسرائيلي المتورطة في انتهاكات حقوق الإنسان.", "action": "لا تشتري حمص صبرا.", "alternatives": ["الحمص محلي الصنع", "العلامات التجارية المحلية للحمص العربي"]}
            ]
        },
        "التكنولوجيا": {
            "companies": [
                {"name": "إتش بي (هيوليت باكارد)", "reason": "توفر إتش بي التقنيات المستخدمة في نظام المراقبة والتحكم الإسرائيلي، بما في ذلك نقاط التفتيش العسكرية. تُستخدم تقنياتها للحفاظ على نظام الفصل العنصري والتمييز.", "action": "لا تشتري منتجات إتش بي، بما في ذلك أجهزة الكمبيوتر والطابعات والمستلزمات.", "alternatives": ["لينوفو", "براذر", "إبسون", "العلامات التجارية الآسيوية"]},
                {"name": "مايكروسوفت", "reason": "استثمرت مايكروسوفت 1.5 مليار دولار في شركة ذكاء اصطناعي إسرائيلية ولديها مركز رئيسي للبحث والتطوير في إسرائيل. تعمل الشركة بشكل وثيق مع الجيش الإسرائيلي لتطوير التقنيات العسكرية.", "action": "استخدم بدائل مفتوحة المصدر كلما أمكن ذلك.", "alternatives": ["لينكس", "ليبر أوفيس", "بدائل مفتوحة المصدر"]},
                {"name": "جوجل", "reason": "وقعت جوجل عقدًا للحوسبة السحابية بقيمة 1.2 مليار دولار مع الحكومة الإسرائيلية (مشروع نيمبوس). تُستخدم هذه التكنولوجيا للمراقبة واستهداف الفلسطينيين.", "action": "استخدم محركات بحث وخدمات بديلة.", "alternatives": ["DuckDuckGo", "ProtonMail", "Firefox"]},
                {"name": "آبل", "reason": "لدى آبل استثمارات كبيرة في إسرائيل وتتعاون مع شركات إسرائيلية متورطة في المراقبة والتكنولوجيا العسكرية.", "action": "فكر في بدائل لمنتجات آبل.", "alternatives": ["سامسونج", "شاومي", "هواوي", "هواتف أندرويد"]},
                {"name": "إنتل", "reason": "تعد إنتل واحدة من أكبر أرباب العمل في قطاع التكنولوجيا الإسرائيلي مع العديد من المصانع ومراكز البحث والتطوير. تساهم الشركة بشكل كبير في اقتصاد إسرائيل.", "action": "فضل معالجات AMD كلما أمكن ذلك.", "alternatives": ["AMD", "ARM", "الشركات المصنعة الأخرى للمعالجات"]}
            ]
        },
        "الأزياء والملابس": {
            "companies": [
                {"name": "بوما", "reason": "ترعى بوما الاتحاد الإسرائيلي لكرة القدم، الذي يضم فرقًا في المستوطنات غير الشرعية. هذا الدعم يضفي الشرعية على الاحتلال وانتهاكات القانون الدولي.", "action": "لا تشتري منتجات بوما.", "alternatives": ["أديداس", "نيو بالانس", "العلامات التجارية المحلية", "لي نينغ"]},
                {"name": "سكيتشرز", "reason": "لدى سكيتشرز متاجر في المستوطنات الإسرائيلية غير الشرعية وتحافظ على شراكات تجارية في إسرائيل، مما يساهم في اقتصاد الاحتلال.", "action": "قاطع أحذية وملابس سكيتشرز.", "alternatives": ["بروكس", "أسيكس", "العلامات التجارية الأخلاقية"]},
                {"name": "إتش آند إم", "reason": "تدير إتش آند إم متاجر في إسرائيل، بما في ذلك في المناطق المتنازع عليها. تجاهلت الشركة الدعوات لوقف عملياتها في الأراضي المحتلة.", "action": "لا تتسوق في إتش آند إم.", "alternatives": ["العلامات التجارية للأزياء الأخلاقية", "الملابس المستعملة"]},
                {"name": "زارا", "reason": "لدى زارا متاجر في إسرائيل وتستورد من موردين إسرائيليين. تم انتقاد العلامة التجارية لعدم اتخاذها موقفًا أخلاقيًا بشأن الاحتلال.", "action": "تجنب التسوق في زارا.", "alternatives": ["العلامات التجارية المحلية", "المحلات المستقلة"]},
                {"name": "فيكتوريا سيكريت", "reason": "فيكتوريا سيكريت مملوكة لشركة L Brands، التي لديها استثمارات كبيرة في إسرائيل ومتاجر في المناطق المتنازع عليها.", "action": "قاطع منتجات فيكتوريا سيكريت.", "alternatives": ["العلامات التجارية للملابس الداخلية الأخلاقية", "العلامات التجارية المحلية"]}
            ]
        },
        "مستحضرات التجميل": {
            "companies": [
                {"name": "لوريال", "reason": "تعمل لوريال في إسرائيل واستحوذت على شركات مستحضرات تجميل إسرائيلية. تمتلك الشركة منشآت في مناطق متنازع عليها وتستفيد من الاحتلال.", "action": "قاطع منتجات لوريال والعلامات التجارية المرتبطة بها.", "alternatives": ["ذا بودي شوب", "لاش", "العلامات التجارية الطبيعية", "مستحضرات التجميل الحلال"]},
                {"name": "إستي لودر", "reason": "رئيس مجلس إدارة إستي لودر، رونالد لودر، هو مؤيد قوي لإسرائيل ويمول المنظمات الموالية لإسرائيل. وقد دافع علنًا عن الأعمال العسكرية الإسرائيلية ضد الفلسطينيين.", "action": "لا تشتري منتجات إستي لودر والعلامات التجارية المرتبطة بها.", "alternatives": ["العلامات التجارية الأخلاقية", "العلامات التجارية المحلية"]},
                {"name": "ريفلون", "reason": "لدى ريفلون عمليات كبيرة في إسرائيل وقد تم انتقادها لدعمها للسياسات الإسرائيلية.", "action": "تجنب منتجات ريفلون.", "alternatives": ["العلامات التجارية الخالية من القسوة", "مستحضرات التجميل النباتية"]}
            ]
        },
        "التمويل": {
            "companies": [
                {"name": "أكسا", "reason": "تستثمر أكسا في البنوك الإسرائيلية التي تمول المستوطنات غير الشرعية في الأراضي الفلسطينية المحتلة.", "action": "اسحب استثماراتك من أكسا واختر مقدمي خدمات تأمين أخلاقيين.", "alternatives": ["شركات التأمين الأخلاقية", "المقدمون المحليون"]}
            ]
        },
        "الخدمات": {
            "companies": [
                {"name": "جي فور إس / ألايد يونيفرسال", "reason": "توفر جي فور إس خدمات ومعدات أمنية للسجون الإسرائيلية حيث يُحتجز السجناء السياسيون الفلسطينيون، غالبًا دون محاكمة وفي ظروف قاسية. كما تخدم نقاط التفتيش والمستوطنات.", "action": "قم بحملات ضد عقود جي فور إس.", "alternatives": ["شركات الأمن المحلية", "مقدمو الخدمات الأخلاقيون"]}
            ]
        }
    }

# Function to display boycott info (remains the same, but ensure it's called correctly)
def display_boycott_info(language):
    if language == "English":
        boycott_data = get_boycott_data_EN()
        st.subheader("Companies to Boycott and Why")
    else:
        boycott_data = get_boycott_data_AR()
        st.subheader("الشركات التي يجب مقاطعتها ولماذا")

    for category, data in boycott_data.items():
        with st.expander(f"**{category}**"):
            for company in data["companies"]:
                st.markdown(f"**{company['name']}**")
                st.markdown(f"**Reason:** {company['reason']}")
                st.markdown(f"**Action:** {company['action']}")
                st.markdown(f"**Alternatives:** {', '.join(company['alternatives'])}")
                st.markdown("---")

# --- Original Helper Functions --- End ---

# --- New Helper Functions --- Start ---

# Function to generate a short title from the first message
def generate_chat_title(first_message):
    words = first_message.split()
    title = " ".join(words[:5])
    if len(words) > 5:
        title += "..."
    # Handle empty message case
    if not title:
        title = "Empty Chat"
    return title

# --- New Helper Functions --- End ---

# --- Main Application Logic --- Start ---
def main():
    # --- Page Config and Language Selection (Original) --- Start ---
    st.set_page_config(page_title="Palestine AI", page_icon="🇵🇸", layout="wide")

    # Language selection
    language = st.sidebar.selectbox("Select Language / اختر اللغة", ["English", "العربية"], index=0)

    # --- Page Config and Language Selection (Original) --- End ---

    # --- Session State Initialization (New) --- Start ---
    if 'chat_histories' not in st.session_state:
        st.session_state.chat_histories = {}
    if 'chat_titles' not in st.session_state:
        st.session_state.chat_titles = {}
    if 'current_chat_id' not in st.session_state or st.session_state.current_chat_id not in st.session_state.chat_histories:
        # Start with a default new chat if no valid chat is selected
        new_chat_id = str(uuid.uuid4())
        st.session_state.current_chat_id = new_chat_id
        st.session_state.chat_histories[new_chat_id] = []
        st.session_state.chat_titles[new_chat_id] = "New Chat" if language == "English" else "محادثة جديدة"
    # --- Session State Initialization (New) --- End ---

    # --- Sidebar Enhancements (New & Original) --- Start ---
    st.sidebar.title("Palestine AI 🇵🇸")

    # Professional Styling for Sidebar
    st.sidebar.markdown("""
    <style>
        /* General Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #f8f9fa; /* Lighter background */
            padding: 10px;
        }
        [data-testid="stSidebar"] h1 {
            color: #004165; /* Dark blue title */
            text-align: center;
            margin-bottom: 20px;
        }
        /* Sidebar Buttons (New Chat & History) */
        .stButton>button {
            width: 100%;
            border-radius: 8px; /* Slightly more rounded */
            margin-bottom: 8px; /* Increased spacing */
            text-align: left;
            padding: 10px 15px; /* Increased padding */
            background-color: #ffffff; /* White background */
            border: 1px solid #dee2e6; /* Lighter border */
            color: #495057; /* Darker text */
            transition: background-color 0.3s ease, box-shadow 0.3s ease;
            font-weight: 500; /* Medium weight */
            overflow: hidden; /* Prevent text overflow */
            text-overflow: ellipsis; /* Add ellipsis for long titles */
            white-space: nowrap; /* Keep title on one line */
        }
        .stButton>button:hover {
            background-color: #e9ecef; /* Subtle hover */
            color: #212529;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05); /* Add slight shadow on hover */
        }
        /* Active Chat Button Styling */
        .stButton>button.active_chat {
            background-color: #cfe2ff; /* Light blue for active chat */
            border-color: #9ec5fe;
            color: #07408c;
            font-weight: 600; /* Bolder for active */
        }
        /* New Chat Button Specific Styling */
        .stButton>button[kind="secondary"] {
             background-color: #0d6efd; /* Blue background */
             color: white;
             border: none;
             font-weight: 600;
        }
        .stButton>button[kind="secondary"]:hover {
             background-color: #0b5ed7; /* Darker blue on hover */
             color: white;
        }
        /* Sidebar Section Headers */
        .sidebar-section-header {
            font-size: 0.9em; /* Smaller header */
            font-weight: 600;
            margin-top: 20px;
            margin-bottom: 10px;
            color: #6c757d; /* Grey color */
            text-transform: uppercase; /* Uppercase */
            letter-spacing: 0.5px;
        }
        /* Sidebar Toggles */
        .stToggle {
            padding-left: 5px; /* Align toggles slightly */
        }
        /* Sidebar Separator */
        [data-testid="stSidebar"] hr {
            margin-top: 15px;
            margin-bottom: 15px;
        }
    </style>
    """, unsafe_allow_html=True)

    # New Chat Button
    new_chat_label = "➕ New Chat" if language == "English" else "➕ محادثة جديدة"
    # Use kind="secondary" for potential different styling via CSS if needed
    if st.sidebar.button(new_chat_label, key="new_chat_button", type="primary"):
        new_chat_id = str(uuid.uuid4())
        st.session_state.current_chat_id = new_chat_id
        st.session_state.chat_histories[new_chat_id] = []
        st.session_state.chat_titles[new_chat_id] = "New Chat" if language == "English" else "محادثة جديدة"
        st.rerun() # Rerun to reflect the new chat selection

    # Chat History List
    history_label = "Chat History" if language == "English" else "سجل المحادثات"
    st.sidebar.markdown(f"<div class='sidebar-section-header'>{history_label}</div>", unsafe_allow_html=True)

    # Display chats, most recent first (using creation order implicitly for now)
    chat_ids = list(st.session_state.chat_titles.keys())
    # Simple reverse chronological order (newest first)
    for chat_id in reversed(chat_ids):
        title = st.session_state.chat_titles[chat_id]
        is_active = chat_id == st.session_state.current_chat_id
        # Use a custom approach to style the button if active
        # Streamlit doesn't directly support adding classes to buttons easily
        # We use the button's state visually
        button_type = "primary" if is_active else "secondary"
        if st.sidebar.button(title, key=f"chat_{chat_id}", type=button_type):
            if not is_active:
                st.session_state.current_chat_id = chat_id
                st.rerun()

    # --- Original Sidebar Content (Boycott Info & Resources) --- Start ---
    st.sidebar.markdown("--- ")
    boycott_header = "Boycott Information" if language == "English" else "معلومات المقاطعة"
    st.sidebar.markdown(f"<div class='sidebar-section-header'>{boycott_header}</div>", unsafe_allow_html=True)
    show_boycott = st.sidebar.toggle("Show Boycott List" if language == "English" else "إظهار قائمة المقاطعة", value=False, key="toggle_boycott")

    st.sidebar.markdown("--- ")
    resources_header = "Educational Resources" if language == "English" else "مصادر تعليمية"
    st.sidebar.markdown(f"<div class='sidebar-section-header'>{resources_header}</div>", unsafe_allow_html=True)
    show_resources = st.sidebar.toggle("Show Resources" if language == "English" else "إظهار المصادر", value=False, key="toggle_resources")
    # --- Original Sidebar Content (Boycott Info & Resources) --- End ---

    # --- Sidebar Enhancements (New & Original) --- End ---

    # --- Main Area --- Start ---
    # Professional Styling for Main Area
    st.markdown("""
    <style>
        /* Main chat container */
        .main .block-container {
            padding-top: 2rem; /* Add some space at the top */
            padding-bottom: 2rem;
        }
        /* Chat input container */
        [data-testid="stChatInput"] {
            background-color: #f8f9fa; /* Match sidebar bg */
            border-top: 1px solid #dee2e6; /* Add separator line */
            padding: 1rem 1.5rem;
        }
        [data-testid="stChatInput"] textarea {
            border: 1px solid #ced4da;
            border-radius: 8px;
            padding: 10px 12px;
            background-color: #ffffff;
        }
        [data-testid="stChatInput"] textarea:focus {
            border-color: #86b7fe; /* Highlight focus */
            box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
        }
        /* Chat messages */
        .stChatMessage {
            border-radius: 12px; /* More rounded messages */
            padding: 14px 18px; /* Slightly larger padding */
            margin-bottom: 12px;
            max-width: 80%; /* Slightly narrower max width */
            box-shadow: 0 1px 3px rgba(0,0,0,0.08); /* Softer shadow */
            border: none; /* Remove default border */
            line-height: 1.6; /* Improve readability */
        }
        /* User message styling */
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageContentUser"]) {
            background-color: #d1e7fd; /* Lighter blue for user */
            margin-left: auto; /* Align user messages to the right */
        }
        /* Assistant message styling */
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageContentAssistant"]) {
            background-color: #ffffff; /* White for assistant */
            border: 1px solid #e9ecef; /* Very light border */
            margin-right: auto; /* Align assistant messages to the left */
        }
        /* Styling for the content inside messages */
        [data-testid="stChatMessageContent"] p {
             margin-bottom: 0.5em; /* Space between paragraphs */
        }
        [data-testid="stChatMessageContent"] ul, [data-testid="stChatMessageContent"] ol {
             padding-left: 20px; /* Indent lists */
        }
        /* Copy button container */
        .copy-button-container {
            text-align: right; /* Align button to the right */
            margin-top: 5px; /* Space above button */
            margin-bottom: -5px; /* Pull it slightly closer to message bottom */
            opacity: 0.7; /* Make it less prominent initially */
            transition: opacity 0.3s ease;
        }
        /* Show copy button on hover (optional, might be tricky with touch) */
        /* .stChatMessage:hover .copy-button-container { opacity: 1; } */
        .copy-button-container button {
            background-color: transparent !important;
            border: none !important;
            color: #6c757d !important; /* Grey icon */
            padding: 0 !important;
            font-size: 1.1em !important; /* Slightly larger icon */
            line-height: 1;
        }
        .copy-button-container button:hover {
            color: #212529 !important; /* Darker on hover */
            background-color: transparent !important;
        }
        /* Style for the chat container itself */
        [data-testid="stVerticalBlock"]:has([data-testid="stChatMessage"]) {
            padding-right: 10px; /* Add padding for scrollbar */
        }
    </style>
    """, unsafe_allow_html=True)

    # Display Boycott Info if toggled
    if show_boycott:
        display_boycott_info(language)

    # Display Resources if toggled
    if show_resources:
        if language == "English":
            st.subheader("Reliable Sources for Palestine Information")
            st.markdown("Here are some recommended sources for accurate information:")
            st.markdown("- **Al Jazeera:** [aljazeera.com](https://www.aljazeera.com/) - Comprehensive Middle East coverage.")
            st.markdown("- **Electronic Intifada:** [electronicintifada.net](https://electronicintifada.net/) - News, commentary, analysis.")
            st.markdown("- **B'Tselem:** [btselem.org](https://www.btselem.org/) - Israeli Information Center for Human Rights in the Occupied Territories.")
            st.markdown("- **Institute for Palestine Studies:** [palestine-studies.org](https://www.palestine-studies.org/) - Academic research on Palestine.")
            st.markdown("- **UNRWA:** [unrwa.org](https://www.unrwa.org/) - UN Agency for Palestine Refugees.")
            st.markdown("- **Human Rights Watch (HRW):** [hrw.org/middle-east/n-africa/israel/palestine](https://www.hrw.org/middle-east/n-africa/israel/palestine) - Reports on human rights.")
            st.markdown("- **Amnesty International:** [amnesty.org/en/location/middle-east-and-north-africa/israel-and-occupied-palestinian-territories/](https://www.amnesty.org/en/location/middle-east-and-north-africa/israel-and-occupied-palestinian-territories/) - Human rights reports.")
        else:
            st.subheader("مصادر موثوقة للمعلومات حول فلسطين")
            st.markdown("إليك بعض المصادر الموصى بها للحصول على معلومات دقيقة:")
            st.markdown("<p style='text-align: right; margin-bottom: 8px;'><a href='https://www.aljazeera.com/' style='color: #1f77b4; text-decoration: underline;'>الجزيرة</a> - تغطية شاملة لقضايا الشرق الأوسط.</p>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: right; margin-bottom: 8px;'><a href='https://electronicintifada.net/' style='color: #1f77b4; text-decoration: underline;'>الانتفاضة الإلكترونية</a> - أخبار وتعليقات وتحليلات ومواد مرجعية حول فلسطين.</p>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: right; margin-bottom: 8px;'><a href='https://www.btselem.org/' style='color: #1f77b4; text-decoration: underline;'>بتسيلم</a> - مركز المعلومات الإسرائيلي لحقوق الإنسان في الأراضي المحتلة.</p>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: right; margin-bottom: 8px;'><a href='https://www.palestine-studies.org/' style='color: #1f77b4; text-decoration: underline;'>معهد الدراسات الفلسطينية</a> - أبحاث أكاديمية حول فلسطين.</p>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: right; margin-bottom: 8px;'><a href='https://www.unrwa.org/' style='color: #1f77b4; text-decoration: underline;'>الأونروا</a> - وكالة الأمم المتحدة لإغاثة وتشغيل اللاجئين الفلسطينيين.</p>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: right; margin-bottom: 8px;'><a href='https://www.hrw.org/ar/middle-east/n-africa/israel/palestine' style='color: #1f77b4; text-decoration: underline;'>هيومن رايتس ووتش</a> - تقارير حول حقوق الإنسان.</p>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: right; margin-bottom: 8px;'><a href='https://www.amnesty.org/ar/location/middle-east-and-north-africa/israel-and-occupied-palestinian-territories/' style='color: #1f77b4; text-decoration: underline;'>منظمة العفو الدولية</a> - تقارير حقوق الإنسان.</p>", unsafe_allow_html=True)

    st.markdown("--- ") # Separator

    # --- Chat Interface (New & Modified) --- Start ---
    # Use a container with a fixed height for the main chat area to make it scrollable
    chat_container = st.container(height=600) # Adjust height as needed

    current_chat_id = st.session_state.current_chat_id
    current_history = st.session_state.chat_histories.get(current_chat_id, [])

    with chat_container:
        # Display existing messages for the current chat
        for i, message in enumerate(current_history):
            role = message["role"]
            content = message["content"]
            avatar = "👤" if role == "user" else "🇵🇸"
            with st.chat_message(role, avatar=avatar):
                st.markdown(content, unsafe_allow_html=True)
                # Add copy button for assistant messages using the component
                if role == "assistant":
                    # Unique key for each copy button instance
                    copy_key = f"copy_{current_chat_id}_{message.get('timestamp', i)}"
                    # Use columns for layout if needed, or place directly
                    # Place the button subtly below the message content
                    st.markdown("<div class='copy-button-container'>", unsafe_allow_html=True)
                    st_copy_to_clipboard(text=content, label="📋 Copy", key=copy_key)
                    st.markdown("</div>", unsafe_allow_html=True)

    # Chat input field - Placed outside the scrollable container
    prompt_text = "Ask about Palestine..." if language == "English" else "...اسأل عن فلسطين"
    user_input = st.chat_input(prompt_text, key=f"chat_input_{current_chat_id}")

    if user_input:
        # Check if the query is related to Palestine (Original Logic)
        if not is_palestine_related(user_input):
            response_text = "Sorry! I'm trained just about Palestine Issue." if language == "English" else "!عذراً أنا مدرب فقط حول قضية فلسطين"
            # Add user message and the restricted response to history
            st.session_state.chat_histories[current_chat_id].append({"role": "user", "content": user_input, "timestamp": time.time()})
            st.session_state.chat_histories[current_chat_id].append({"role": "assistant", "content": response_text, "timestamp": time.time()})
            # No need to rerun here, let the rerun after potential AI response handle it
        else:
            # Add user message to history
            st.session_state.chat_histories[current_chat_id].append({"role": "user", "content": user_input, "timestamp": time.time()})

            # Generate title if it's the first message and title is still default
            if len(st.session_state.chat_histories[current_chat_id]) == 1 and st.session_state.chat_titles[current_chat_id] in ["New Chat", "محادثة جديدة"]:
                new_title = generate_chat_title(user_input)
                st.session_state.chat_titles[current_chat_id] = new_title

            # Display user message immediately (will be redisplayed on rerun, but provides instant feedback)
            # This part can be removed if double display is an issue, rely solely on rerun
            # with chat_container:
            #      with st.chat_message("user", avatar="👤"):
            #         st.markdown(user_input, unsafe_allow_html=True)

            # Get AI response with context
            # Prepare placeholder for the AI response *before* calling the API
            with chat_container:
                with st.chat_message("assistant", avatar="🇵🇸"):
                    placeholder = st.empty() # Placeholder for typing effect

            # Fetch history *before* adding the potential new assistant message
            history_for_api = st.session_state.chat_histories[current_chat_id]
            ai_response = ask_about_palestine_with_context(user_input, history_for_api)

            # Add AI response to history *before* displaying it with typing effect
            st.session_state.chat_histories[current_chat_id].append({"role": "assistant", "content": ai_response, "timestamp": time.time()})

            # Display AI response using typing effect in the placeholder created earlier
            # This needs to happen *after* adding to history but *before* rerun
            # typing_effect(ai_response, placeholder) # This won't work correctly with rerun logic
            # Instead, we rely on the rerun to display the full history including the new message.

        # Rerun to update the chat display and sidebar title if changed
        st.rerun()

    # --- Chat Interface (New & Modified) --- End ---

    # --- Main Area --- End ---

    # --- Footer (Original) --- Start ---
    st.markdown("--- ")
    st.markdown("<div style='text-align: center; padding: 10px; color: #6c757d;'>Palestine AI - Developed by Elkalem-Imrou Height School in collaboration with Erinov Company</div>", unsafe_allow_html=True)
    # --- Footer (Original) --- End ---

# --- Main Application Logic --- End ---

if __name__ == "__main__":
    main()

