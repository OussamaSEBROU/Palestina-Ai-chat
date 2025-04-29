import streamlit as st
import google.generativeai as genai
import time
import os
import uuid # To generate unique IDs for chats
# Removed unused imports: requests, Image, io, base64

# --- Configuration and Initialization ---

# Configure Gemini with API key
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    try:
        google_api_key = st.secrets["GOOGLE_API_KEY"]
    except Exception as e:
        st.error(f"GOOGLE_API_KEY not found. Please set it as an environment variable or Streamlit secret. Error: {e}")
        st.stop()

try:
    genai.configure(api_key=google_api_key)
except Exception as e:
    st.error(f"Failed to configure Gemini: {e}")
    st.stop()

# Load Gemini model
# Using a model that supports chat history well
MODEL_NAME = "gemini-1.5-flash-latest"
try:
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        # System instruction can be set here or when starting chat
        system_instruction="""You are an expert assistant dedicated to providing accurate, in-depth, and highly informative answers specifically about Palestine and related issues based ONLY on the provided context and trusted sources. Your answers should focus entirely on Palestine-related topics. If the question is not related to Palestine, respond with: \"Sorry! I'm trained just about Palestine Issue.\" Structure your response professionally, cite sources if possible (like Al Jazeera, HRW, UNRWA, B'Tselem, Institute for Palestine Studies), use the same language as the input, and maintain factual accuracy without bias towards Israel. Keep answers comprehensive but concise where appropriate.""",
        generation_config=genai.types.GenerationConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_output_tokens=4000
        )
    )
except Exception as e:
    st.error(f"Failed to load Gemini model '{MODEL_NAME}': {e}")
    st.stop()

# --- Session State Initialization ---

def initialize_session_state():
    # Navigation state
    if 'show_chat' not in st.session_state:
        st.session_state.show_chat = True
    if 'show_boycott' not in st.session_state:
        st.session_state.show_boycott = False
    if 'show_education' not in st.session_state:
        st.session_state.show_education = False

    # Language state
    if 'language' not in st.session_state:
        st.session_state.language = 'english' # Default language

    # Chat history state
    if "history" not in st.session_state:
        st.session_state.history = [] # List to store all chat sessions

    # Current active chat state
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None # No chat selected initially

    # Initialize first chat if history is empty
    if not st.session_state.history:
        chat_id = str(uuid.uuid4())
        st.session_state.history.append({
            "id": chat_id,
            "name": "New Chat",
            "messages": [] # Start with no messages
        })
        st.session_state.current_chat_id = chat_id

# --- Helper Functions ---

# Function to get the currently active chat dictionary
def get_current_chat():
    if st.session_state.current_chat_id:
        for chat in st.session_state.history:
            if chat["id"] == st.session_state.current_chat_id:
                return chat
    return None

# Function to generate chat name from first message
def generate_chat_name(message_content):
    words = message_content.split()
    return " ".join(words[:5]) + ("..." if len(words) > 5 else "")

# Function to simulate typing effect
def typing_effect(text, placeholder, delay=0.003):
    if len(text) > 1000: delay = 0.001 # Faster for long text
    output = ""
    for char in text:
        output += char
        placeholder.markdown(f"<div style='line-height: 1.5;'>{output}</div>", unsafe_allow_html=True)
        time.sleep(delay)
    # Final update to ensure complete text is shown without cursor/delay issues
    placeholder.markdown(f"<div style='line-height: 1.5;'>{text}</div>", unsafe_allow_html=True)

# Function to check if query is related to Palestine (simplified)
def is_palestine_related(query):
    palestine_keywords = [
        "palestine", "palestinian", "gaza", "west bank", "jerusalem", "al-quds",
        "israel", "occupation", "intifada", "nakba", "hamas", "fatah", "plo", "bds",
        "settlement", "settler", "zionism", "al-aqsa", "unrwa", "refugee",
        "apartheid", "wall", "checkpoint", "blockade", "resistance", "idf",
        "1948", "1967", "human rights", "international law", "un resolution"
        # Add more keywords if needed
    ]
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in palestine_keywords)

# Ask Gemini with context using ChatSession
def ask_gemini_with_context(user_question, chat_session):
    try:
        # Send message using the existing chat session
        response = chat_session.send_message(user_question)
        return response.text
    except Exception as e:
        error_message = str(e)
        st.error(f"Error generating response: {error_message}")
        # Handle specific errors if needed
        if "quota" in error_message.lower():
            return "❌ API quota exceeded. Please try again later or contact the administrator."
        elif "blocked" in error_message.lower() or "safety" in error_message.lower():
            return "❌ The response was blocked due to safety concerns. Please rephrase your question or try a different topic related to Palestine."
        elif "timeout" in error_message.lower():
            return "❌ The request timed out. Please try again."
        else:
            return f"❌ An error occurred: {error_message}."

# --- Static Data Functions (Boycott, Education) ---
# Keep these functions as they were in the original code
# (get_boycott_data_EN, get_boycott_data_AR, get_educational_resources_EN, get_educational_resources_AR)
# ... (Paste the full functions here from the original code) ...
# Function to get detailed boycott data
def get_boycott_data_EN():
    # Predefined boycott data based on research
    boycott_data = {
        "Food & Beverages": {
            "companies": [
                {
                    "name": "Starbucks",
                    "reason": "Howard Schultz, founder and major shareholder of Starbucks, is a staunch supporter of Israel who invests heavily in Israel's economy, including a recent $1.7 billion investment in cybersecurity startup Wiz.",
                    "action": "Don't buy Starbucks products. Don't sell Starbucks products. Don't work for Starbucks.",
                    "alternatives": ["Caffe Nero", "Local independent cafes", "Local Arab cafes"]
                },
                {
                    "name": "Coca-Cola",
                    "reason": "Coca-Cola has a bottling plant in the Atarot Industrial Zone, an illegal Israeli settlement in occupied East Jerusalem. The company continues to support Israel's economy despite human rights violations.",
                    "action": "Boycott all Coca-Cola products, including Sprite, Fanta, and other associated brands.",
                    "alternatives": ["Local beverage brands", "Homemade sparkling water", "Natural juices"]
                },
                {
                    "name": "McDonald's",
                    "reason": "McDonald's Israel provided thousands of free meals to Israeli soldiers during military operations in Gaza. The Israeli franchise has openly supported military actions against Palestinians.",
                    "action": "Don't eat at McDonald's.",
                    "alternatives": ["Local restaurants", "Local fast food chains"]
                },
                {
                    "name": "Nestlé",
                    "reason": "Nestlé has been operating in Israel since 1995 and has production facilities in contested areas. The company has been criticized for exploiting Palestinian water resources.",
                    "action": "Avoid Nestlé products, including bottled water, cereals, and dairy products.",
                    "alternatives": ["Local brands", "Artisanal products", "Filtered tap water"]
                },
                {
                    "name": "PepsiCo",
                    "reason": "PepsiCo operates in Israel and has facilities in contested territories. The company continues its activities despite calls for boycott.",
                    "action": "Avoid all PepsiCo products, including Lay's chips, Doritos, and Pepsi beverages.",
                    "alternatives": ["Local beverages", "Locally manufactured snacks"]
                },
                {
                    "name": "Sabra Hummus",
                    "reason": "Sabra is a joint venture between PepsiCo and the Strauss Group, an Israeli company that provides support to elite units of the Israeli military involved in human rights violations.",
                    "action": "Don't buy Sabra hummus.",
                    "alternatives": ["Homemade hummus", "Local Arab hummus brands"]
                }
            ]
        },
        "Technology": {
            "companies": [
                {
                    "name": "HP (Hewlett-Packard)",
                    "reason": "HP provides technologies used in Israel's control and surveillance system, including for military checkpoints. Its technologies are used to maintain the apartheid and segregation system.",
                    "action": "Don't buy HP products, including computers, printers, and supplies.",
                    "alternatives": ["Lenovo", "Brother", "Epson", "Asian brands"]
                },
                {
                    "name": "Microsoft",
                    "reason": "Microsoft invested $1.5 billion in an Israeli AI company and has a major R&D center in Israel. The company works closely with the Israeli military to develop military technologies.",
                    "action": "Use open source alternatives when possible.",
                    "alternatives": ["Linux", "LibreOffice", "Open source alternatives"]
                },
                {
                    "name": "Google",
                    "reason": "Google signed a $1.2 billion cloud computing contract with the Israeli government (Project Nimbus). This technology is used for surveillance and targeting of Palestinians.",
                    "action": "Use alternative search engines and services.",
                    "alternatives": ["DuckDuckGo", "ProtonMail", "Firefox"]
                },
                {
                    "name": "Apple",
                    "reason": "Apple has significant investments in Israel and collaborates with Israeli companies involved in surveillance and military technology.",
                    "action": "Consider alternatives to Apple products.",
                    "alternatives": ["Samsung", "Xiaomi", "Huawei", "Android phones"]
                },
                {
                    "name": "Intel",
                    "reason": "Intel is one of the largest employers in the Israeli tech sector with several plants and R&D centers. The company contributes significantly to Israel's economy.",
                    "action": "Prefer AMD processors when possible.",
                    "alternatives": ["AMD", "ARM", "Other processor manufacturers"]
                }
            ]
        },
        "Fashion & Clothing": {
            "companies": [
                {
                    "name": "Puma",
                    "reason": "Puma sponsors the Israel Football Association, which includes teams in illegal settlements. This support legitimizes the occupation and violations of international law.",
                    "action": "Don't buy Puma products.",
                    "alternatives": ["Adidas", "New Balance", "Local brands", "Li-Ning"]
                },
                {
                    "name": "Skechers",
                    "reason": "Skechers has stores in illegal Israeli settlements and maintains business partnerships in Israel, contributing to the occupation economy.",
                    "action": "Boycott Skechers shoes and clothing.",
                    "alternatives": ["Brooks", "ASICS", "Ethical brands"]
                },
                {
                    "name": "H&M",
                    "reason": "H&M operates stores in Israel, including in contested areas. The company has ignored calls to cease operations in occupied territories.",
                    "action": "Don't shop at H&M.",
                    "alternatives": ["Ethical fashion brands", "Second-hand clothing"]
                },
                {
                    "name": "Zara",
                    "reason": "Zara has stores in Israel and sources from Israeli suppliers. The brand has been criticized for its lack of ethical stance regarding the occupation.",
                    "action": "Avoid shopping at Zara.",
                    "alternatives": ["Local brands", "Independent boutiques"]
                },
                {
                    "name": "Victoria's Secret",
                    "reason": "Victoria's Secret is owned by L Brands, which has significant investments in Israel and stores in contested areas.",
                    "action": "Boycott Victoria's Secret products.",
                    "alternatives": ["Ethical lingerie brands", "Local brands"]
                }
            ]
        },
        "Cosmetics": {
            "companies": [
                {
                    "name": "L'Oréal",
                    "reason": "L'Oréal operates in Israel and has acquired Israeli cosmetics companies. The company has facilities in contested territories and benefits from the occupation.",
                    "action": "Boycott L'Oréal products and its associated brands.",
                    "alternatives": ["The Body Shop", "Lush", "Natural brands", "Halal cosmetics"]
                },
                {
                    "name": "Estée Lauder",
                    "reason": "Estée Lauder chairman, Ronald Lauder, is a strong supporter of Israel and funds pro-Israel organizations. He has publicly defended Israeli military actions against Palestinians.",
                    "action": "Don't buy Estée Lauder products and its associated brands.",
                    "alternatives": ["Ethical cosmetics brands", "Natural products"]
                },
                {
                    "name": "Yves Saint Laurent Beauty / YSL Beauty",
                    "reason": "YSL Beauty is owned by L'Oréal Group, which operates in Israel and has ties to Israeli companies involved in the occupation.",
                    "action": "Avoid YSL Beauty products.",
                    "alternatives": ["Ethical cosmetics brands", "Natural products"]
                },
                {
                    "name": "Garnier",
                    "reason": "Garnier is a subsidiary of L'Oréal that provided free products to Israeli soldiers during military operations in Gaza.",
                    "action": "Don't buy Garnier products.",
                    "alternatives": ["Natural hair products", "Local brands"]
                }
            ]
        },
        "Finance": {
            "companies": [
                {
                    "name": "eToro",
                    "reason": "eToro is an Israeli online trading company that supports Israel's economy and contributes to taxes that fund the occupation.",
                    "action": "Use other trading and investment platforms.",
                    "alternatives": ["Alternative trading platforms", "Ethical banks"]
                },
                {
                    "name": "PayPal",
                    "reason": "PayPal operates in Israel but refuses to provide its services to Palestinians in the occupied territories, creating blatant economic discrimination.",
                    "action": "Use alternatives to PayPal when possible.",
                    "alternatives": ["Wise", "Local banking services", "Bank transfers"]
                },
                {
                    "name": "Citibank",
                    "reason": "Citibank has significant investments in Israel and finances projects in occupied territories, contributing to the expansion of illegal settlements.",
                    "action": "Avoid using Citibank services.",
                    "alternatives": ["Local banks", "Credit unions", "Ethical banks"]
                }
            ]
        },
        "Other": {
            "companies": [
                {
                    "name": "SodaStream",
                    "reason": "SodaStream operated a factory in an illegal Israeli settlement in the occupied West Bank before relocating due to pressure. The company continues to benefit from discriminatory policies.",
                    "action": "Don't buy SodaStream products.",
                    "alternatives": ["Bottled sparkling water", "Other carbonation systems"]
                },
                {
                    "name": "Volvo Heavy Machinery",
                    "reason": "Volvo heavy equipment is used for demolishing Palestinian homes and building illegal settlements. These machines are essential tools of the occupation.",
                    "action": "Raise awareness about the use of Volvo equipment in occupied territories.",
                    "alternatives": ["Other heavy equipment manufacturers"]
                },
                {
                    "name": "Caterpillar",
                    "reason": "Caterpillar bulldozers are used to demolish Palestinian homes and build the illegal separation wall. These machines are specially modified for military demolitions.",
                    "action": "Boycott Caterpillar products and raise awareness about their use.",
                    "alternatives": ["Other construction equipment manufacturers"]
                },
                {
                    "name": "Airbnb",
                    "reason": "Airbnb lists properties in illegal Israeli settlements in occupied Palestinian territory, thus legitimizing the occupation and profiting from stolen land.",
                    "action": "Don't use Airbnb for your travel bookings.",
                    "alternatives": ["Booking.com (with vigilance)", "Local hotels", "Independent hostels"]
                },
                {
                    "name": "TripAdvisor",
                    "reason": "TripAdvisor promotes tourist attractions in illegal settlements without mentioning their illegal status under international law.",
                    "action": "Avoid using TripAdvisor, particularly for Middle East travel.",
                    "alternatives": ["Independent travel guides", "Local recommendations"]
                }
            ]
        }
    }
    return boycott_data

def get_boycott_data_AR():
    boycott_data = {
        "الأغذية والمشروبات": {
            "companies": [
                {
                    "name": "Starbucks",
                    "reason1": "هوارد شولتز، مؤسس ستاربكس والمساهم الرئيسي فيها، هو داعم قوي لإسرائيل ويستثمر بكثافة في اقتصادها، بما في ذلك استثمار حديث بقيمة 1.7 مليار دولار في شركة الأمن السيبراني الإسرائيلية الناشئة 'Wiz'.",
                    "action1": "لا تشتري منتجات ستاربكس. لا تبيع منتجات ستاربكس. لا تعمل في ستاربكس.",
                    "alternatives1": ["Caffe Nero", "مقاهي محلية مستقلة", "مقاهي عربية محلية"]
                },
                {
                    "name": "Coca-Cola",
                    "reason1": "تمتلك كوكا كولا مصنع تعبئة في منطقة عطروت الصناعية، وهي مستوطنة إسرائيلية غير شرعية في القدس الشرقية المحتلة. تواصل الشركة دعم اقتصاد دولة الاحتلال رغم انتهاكات حقوق الإنسان.",
                    "action1": "قاطع جميع منتجات كوكا كولا، بما في ذلك سبرايت وفانتا والعلامات التجارية الأخرى المرتبطة بها.",
                    "alternatives1": ["علامات تجارية محلية للمشروبات", "مياه غازية محضرة في المنزل", "عصائر طبيعية"]
                },
                {
                    "name": "McDonald's",
                    "reason1": "قدمت ماكدونالدز إسرائيل آلاف الوجبات المجانية لجنود جيش الاحتلال الإسرائيلي خلال العمليات العسكرية في غزة. وقد دعم الامتياز الإسرائيلي علنًا الأعمال العسكرية ضد الفلسطينيين.",
                    "action1": "لا تأكل في ماكدونالدز.",
                    "alternatives1": ["مطاعم محلية", "سلاسل مطاعم وجبات سريعة محلية"]
                },
                {
                    "name": "Nestlé",
                    "reason1": "تعمل نستله في إسرائيل منذ عام 1995 ولديها منشآت إنتاج في مناطق متنازع عليها. تعرضت الشركة لانتقادات لاستغلالها موارد المياه الفلسطينية بشكل مجحف.",
                    "action1": "تجنب منتجات نستله، بما في ذلك المياه المعبأة، وحبوب الإفطار، ومنتجات الألبان.",
                    "alternatives1": ["علامات تجارية محلية", "منتجات حرفية محلية", "مياه صنبور مفلترة"]
                },
                {
                    "name": "PepsiCo",
                    "reason1": "تعمل بيبسيكو في إسرائيل ولديها منشآت في الأراضي المتنازع عليها. تواصل الشركة أنشطتها متجاهلة دعوات المقاطعة الدولية.",
                    "action1": "تجنب جميع منتجات بيبسيكو، بما في ذلك رقائق ليز ودوريتوس ومشروبات بيبسي.",
                    "alternatives1": ["مشروبات محلية", "وجبات خفيفة مصنعة محليًا"]
                },
                {
                    "name": "Sabra Hummus",
                    "reason1": "صبرا هو مشروع مشترك بين بيبسيكو ومجموعة شتراوس، وهي شركة إسرائيلية تقدم الدعم المادي والمعنوي لوحدات النخبة في جيش الاحتلال الإسرائيلي المتورطة في انتهاكات حقوق الإنسان.",
                    "action1": "لا تشتري حمص صبرا.",
                    "alternatives1": ["حمص محضر في المنزل", "علامات تجارية عربية محلية للحمص"]
                }
            ]
        },
        "التكنولوجيا": {
            "companies": [
                {
                    "name": "HP",
                    "reason1": "توفر إتش بي التقنيات المستخدمة في نظام السيطرة والمراقبة الإسرائيلي، بما في ذلك تقنيات نقاط التفتيش العسكرية. تُستخدم تقنياتها لترسيخ نظام الفصل العنصري والتمييز ضد الفلسطينيين.",
                    "action1": "لا تشتري منتجات إتش بي، بما في ذلك أجهزة الكمبيوتر والطابعات والمستلزمات.",
                    "alternatives1": ["Lenovo", "Brother", "Epson", "علامات تجارية آسيوية أخرى"]
                },
                {
                    "name": "Microsoft",
                    "reason1": "استثمرت مايكروسوفت 1.5 مليار دولار في شركة ذكاء اصطناعي إسرائيلية ولديها مركز رئيسي للبحث والتطوير في إسرائيل. تتعاون الشركة بشكل وثيق مع جيش الاحتلال لتطوير تقنيات عسكرية متقدمة.",
                    "action1": "استخدم بدائل مفتوحة المصدر قدر الإمكان.",
                    "alternatives1": ["Linux", "LibreOffice", "بدائل برمجية مفتوحة المصدر"]
                },
                {
                    "name": "Google",
                    "reason1": "وقعت جوجل عقدًا للحوسبة السحابية بقيمة 1.2 مليار دولار مع الحكومة الإسرائيلية (مشروع نيمبوس). تُستخدم هذه التكنولوجيا الفائقة في مراقبة الفلسطينيين وتسهيل استهدافهم.",
                    "action1": "استخدم محركات بحث وخدمات بديلة.",
                    "alternatives1": ["DuckDuckGo", "ProtonMail", "Firefox"]
                },
                {
                    "name": "Apple",
                    "reason1": "لدى آبل استثمارات ضخمة في إسرائيل وتتعاون مع شركات إسرائيلية متورطة بشكل مباشر في تطوير تكنولوجيا المراقبة والتكنولوجيا العسكرية المستخدمة ضد الفلسطينيين.",
                    "action1": "ابحث بجدية عن بدائل لمنتجات آبل.",
                    "alternatives1": ["Samsung", "Xiaomi", "Huawei", "هواتف بنظام أندرويد"]
                },
                {
                    "name": "Intel",
                    "reason1": "تُعد إنتل من أكبر جهات التوظيف في قطاع التكنولوجيا الإسرائيلي وتمتلك العديد من المصانع ومراكز البحث والتطوير. تساهم الشركة بشكل حيوي ومباشر في دعم اقتصاد دولة الاحتلال.",
                    "action1": "فضل معالجات AMD على معالجات إنتل كلما أمكن.",
                    "alternatives1": ["AMD", "ARM", "شركات تصنيع معالجات أخرى"]
                }
            ]
        },
        "الأزياء والملابس": {
            "companies": [
                {
                    "name": "Puma",
                    "reason1": "ترعى بوما الاتحاد الإسرائيلي لكرة القدم، الذي يضم فرقًا من المستوطنات غير الشرعية المقامة على أراضٍ فلسطينية محتلة. هذا الدعم يضفي شرعية زائفة على الاحتلال وانتهاكاته للقانون الدولي.",
                    "action1": "لا تشتري منتجات بوما.",
                    "alternatives1": ["Adidas", "New Balance", "علامات تجارية محلية", "Li-Ning"]
                },
                {
                    "name": "Skechers",
                    "reason1": "تمتلك سكيتشرز متاجر في المستوطنات الإسرائيلية غير الشرعية وتحافظ على شراكات تجارية في إسرائيل، مما يساهم بشكل مباشر في دعم اقتصاد الاحتلال.",
                    "action1": "قاطع أحذية وملابس سكيتشرز.",
                    "alternatives1": ["Brooks", "ASICS", "علامات تجارية تلتزم بالمعايير الأخلاقية"]
                },
                {
                    "name": "H&M",
                    "reason1": "تدير إتش آند إم متاجر في إسرائيل، بما في ذلك في مناطق متنازع عليها. تجاهلت الشركة بشكل مستمر الدعوات لوقف عملياتها التجارية في الأراضي المحتلة.",
                    "action1": "لا تتسوق في إتش آند إم.",
                    "alternatives1": ["علامات تجارية للأزياء الأخلاقية", "ملابس مستعملة", "أسواق الملابس المحلية"]
                },
                {
                    "name": "Zara",
                    "reason1": "لدى زارا متاجر في إسرائيل وتعتمد على موردين إسرائيليين. تعرضت العلامة التجارية لانتقادات شديدة بسبب افتقارها لموقف أخلاقي واضح تجاه الاحتلال ومعاناة الفلسطينيين.",
                    "action1": "تجنب التسوق في زارا.",
                    "alternatives1": ["علامات تجارية محلية", "متاجر بوتيك مستقلة"]
                },
                {
                    "name": "Victoria's Secret",
                    "reason1": "فيكتوريا سيكريت مملوكة لشركة L Brands، التي لديها استثمارات كبيرة ومؤثرة في إسرائيل ومتاجر في مناطق متنازع عليها.",
                    "action1": "قاطع منتجات فيكتوريا سيكريت.",
                    "alternatives1": ["علامات تجارية للملابس الداخلية الأخلاقية", "علامات تجارية محلية"]
                }
            ]
        },
        "مستحضرات التجميل": {
            "companies": [
                {
                    "name": "L'Oréal",
                    "reason1": "تنشط لوريال بقوة في السوق الإسرائيلي واستحوذت على شركات مستحضرات تجميل إسرائيلية. تمتلك الشركة منشآت في الأراضي المتنازع عليها وتستفيد بشكل مباشر من استمرار الاحتلال.",
                    "action1": "قاطع منتجات لوريال وجميع العلامات التجارية التابعة لها.",
                    "alternatives1": ["The Body Shop", "Lush", "علامات تجارية طبيعية", "مستحضرات تجميل حلال"]
                },
                {
                    "name": "Estée Lauder",
                    "reason1": "رئيس مجلس إدارة إستي لودر، رونالد لودر، هو داعم متشدد لإسرائيل ويمول منظمات صهيونية متطرفة. دافع علنًا وبشكل متكرر عن الاعتداءات العسكرية الإسرائيلية ضد الفلسطينيين.",
                    "action1": "لا تشتري منتجات إستي لودر والعلامات التجارية المرتبطة بها.",
                    "alternatives1": ["علامات تجارية لمستحضرات التجميل الأخلاقية", "منتجات طبيعية وعضوية"]
                },
                {
                    "name": "إيف سان لوران بيوتي  / YSL Beauty",
                    "reason1": "إيف سان لوران بيوتي مملوكة لمجموعة لوريال، التي تعمل في إسرائيل ولها علاقات وثيقة بشركات إسرائيلية متورطة في الاحتلال.",
                    "action1": "تجنب منتجات إيف سان لوران بيوتي.",
                    "alternatives1": ["علامات تجارية لمستحضرات التجميل الأخلاقية", "منتجات طبيعية بديلة"]
                },
                {
                    "name": "Garnier",
                    "reason1": "غارنييه هي علامة تجارية تابعة لـ لوريال، وقد قامت بتوزيع منتجات مجانية كهدايا لجنود جيش الاحتلال الإسرائيلي خلال العمليات العسكرية الوحشية في غزة.",
                    "action1": "لا تشتري منتجات غارنييه.",
                    "alternatives1": ["منتجات شعر طبيعية", "علامات تجارية محلية للعناية بالشعر"]
                }
            ]
        },
        "المالية": {
            "companies": [
                {
                    "name": "eToro",
                    "reason1": "إي تورو هي شركة تداول إلكتروني إسرائيلية تدعم بشكل مباشر اقتصاد دولة الاحتلال وتساهم في الضرائب التي تمول سياسات الاحتلال والاستيطان.",
                    "action1": "استخدم منصات تداول واستثمار بديلة وغير داعمة للاحتلال.",
                    "alternatives1": ["منصات تداول بديلة", "بنوك تلتزم بالمعايير الأخلاقية"]
                },
                {
                    "name": "PayPal",
                    "reason1": "تعمل باي بال في إسرائيل لكنها ترفض بعناد تقديم خدماتها للفلسطينيين في الأراضي المحتلة (الضفة الغربية وغزة)، مما يخلق نظام تمييز اقتصادي صارخ وغير مقبول.",
                    "action1": "استخدم بدائل لباي بال كلما أمكن.",
                    "alternatives1": ["Wise (TransferWise سابقاً)", "خدمات مصرفية محلية موثوقة", "تحويلات بنكية مباشرة"]
                },
                {
                    "name": "Citibank",
                    "reason1": "لدى سيتي بنك استثمارات مالية ضخمة في إسرائيل ويمول مشاريع بنية تحتية في الأراضي المحتلة، مما يساهم بشكل مباشر في توسيع المستوطنات غير الشرعية وتثبيت الاحتلال.",
                    "action1": "تجنب استخدام خدمات سيتي بنك المصرفية.",
                    "alternatives1": ["بنوك محلية", "اتحادات ائتمانية", "بنوك تلتزم بالمعايير الأخلاقية"]
                }
            ]
        },
        "أخرى": {
            "companies": [
                {
                    "name": "SodaStream",
                    "reason1": "كانت صودا ستريم تدير مصنعًا رئيسيًا في مستوطنة ميشور أدوميم الإسرائيلية غير الشرعية في الضفة الغربية المحتلة قبل أن تنقله تحت ضغط المقاطعة الدولية. لا تزال الشركة تستفيد من سياسات الاحتلال التمييزية.",
                    "action1": "لا تشتري منتجات صودا ستريم.",
                    "alternatives1": ["مياه غازية معبأة من مصادر أخرى", "أنظمة كربنة منزلية بديلة"]
                },
                {
                    "name": "Volvo",
                    "reason1": "تُستخدم معدات وآليات شركة فولفو الثقيلة بشكل ممنهج في هدم منازل الفلسطينيين وتجريف أراضيهم الزراعية، بالإضافة إلى بناء المستوطنات غير الشرعية وجدار الفصل العنصري. هذه الآليات هي أدوات أساسية لفرض سياسات الاحتلال.",
                    "action1": "انشر الوعي حول تورط معدات فولفو في جرائم الاحتلال في الأراضي الفلسطينية.",
                    "alternatives1": ["شركات تصنيع معدات ثقيلة أخرى (مع التحقق من عدم تورطها)"]
                },
                {
                    "name": "Caterpillar",
                    "reason1": "تُستخدم جرافات كاتربيلر المدرعة والمعدلة خصيصًا لأغراض عسكرية في هدم منازل الفلسطينيين وتدمير البنية التحتية وبناء جدار الفصل العنصري غير القانوني. تعتبر هذه الجرافات رمزًا لسياسات الهدم والتدمير الإسرائيلية.",
                    "action1": "قاطع منتجات كاتربيلر وانشر الوعي حول استخدام آلياتها كأدوات للاحتلال.",
                    "alternatives1": ["شركات تصنيع معدات بناء أخرى (مع التحقق من عدم تورطها)"]
                },
                {
                    "name": "Airbnb",
                    "reason1": "تعرض منصة إير بي إن بي عقارات للإيجار في المستوطنات الإسرائيلية غير الشرعية المقامة على أراضٍ فلسطينية مسلوبة في الأراضي المحتلة، مما يضفي شرعية على الاحتلال ويتربح بشكل مباشر من سرقة الأراضي الفلسطينية.",
                    "action1": "لا تستخدم إير بي إن بي لحجوزات السفر والإقامة.",
                    "alternatives1": ["Booking.com (مع التحقق من عدم وجود عقارات في المستوطنات)", "فنادق محلية", "بيوت ضيافة ونزل مستقلة"]
                },
                {
                    "name": "TripAdvisor",
                    "reason1": "يروج موقع تريب أدفايزر لمناطق الجذب السياحي والأنشطة المقامة في المستوطنات الإسرائيلية غير الشرعية دون الإشارة إلى وضعها غير القانوني بموجب القانون الدولي، مما يساهم في تطبيع الاحتلال.",
                    "action1": "تجنب استخدام تريب أدفايزر، خاصة عند التخطيط للسفر في منطقة الشرق الأوسط.",
                    "alternatives1": ["أدلة سفر مستقلة وموثوقة", "توصيات من مصادر محلية", "مدونات سفر ملتزمة أخلاقياً"]
                }
            ]
        }
    }
    return boycott_data

def get_educational_resources_AR():
    resources = {
        "History": [
            {
                "title": "The Nakba: Palestinian Exodus of 1948",
                "description1": "النكبة (كارثة بالعربية) تشير إلى التهجير الجماعي وتجريد الفلسطينيين من ممتلكاتهم أثناء إنشاء دولة إسرائيل في عام 1948. أُجبر أكثر من 750,000 فلسطيني على مغادرة منازلهم، وتم تدمير أكثر من 500 قرية فلسطينية.",
                "sources": [
                    {"name": "القدس إنفو - أكبر موقع مقدسي موثق على الانترنت", "url": "https://qudsinfo.com/"},
                    {"name": "Institute for Palestine Studies", "url": "https://www.palestine-studies.org/"},
                    {"name": "UN Archives", "url": "https://archives.un.org/"},
                    {"name": "Palestinian Journeys", "url": "https://www.paljourneys.org/en/timeline/highlight/165/nakba"},
                    {"name": "Metras", "url": "https://metras.co"},
                    {"name": "Anadolu Agency (Arabic)", "url": "https://www.aa.com.tr/ar"}
                ],
                "key_facts1": [
                    "تم تهجير أكثر من 750,000 فلسطيني",
                    "تم تدمير أكثر من 500 قرية فلسطينية",
                    "مصادرة 78٪ من الأراضي الفلسطينية التاريخية",
                    "إنشاء أطول أزمة لاجئين غير محلولة في العالم"
                ]
            },
            {
                "title": "The 1967 Occupation and Its Consequences",
                "description1": "في يونيو 1967، احتلت إسرائيل الضفة الغربية، والقدس الشرقية، وقطاع غزة، ومرتفعات الجولان، وشبه جزيرة سيناء خلال حرب الأيام الستة. هذا الاحتلال، الذي لا يزال مستمرًا حتى اليوم (باستثناء سيناء)، أدى إلى توسع المستوطنات الإسرائيلية غير القانونية ونظام من السيطرة العسكرية على السكان الفلسطينيين.",
                "sources": [
                    {"name": "القدس إنفو - أكبر موقع مقدسي موثق على الانترنت", "url": "https://qudsinfo.com/"},
                    {"name": "United Nations", "url": "https://www.un.org/unispal/"},
                    {"name": "B'Tselem", "url": "https://www.btselem.org/"},
                    {"name": "Human Rights Watch", "url": "https://www.hrw.org/middle-east/north-africa/israel/palestine"},
                    {"name": "Metras", "url": "https://metras.co"},
                    {"name": "Anadolu Agency (Arabic)", "url": "https://www.aa.com.tr/ar"}
                ],
                "key_facts1": [
                    "أكثر من 600,000 مستوطن إسرائيلي يعيشون بشكل غير قانوني في الضفة الغربية والقدس الشرقية",
                    "أكثر من 60٪ من الضفة الغربية تحت السيطرة الإسرائيلية الكاملة (المنطقة ج)",
                    "أكثر من 700 كم من الجدار الفاصل، والذي اعتبرته محكمة العدل الدولية غير قانوني",
                    "أكثر من 65 قرارًا من الأمم المتحدة تدين الاحتلال، وجميعها تم تجاهلها من قبل إسرائيل"
                ]
            }
        ],
        "Human_Rights": [
            {
                "title": "Israeli Military Detention of Palestinian Children",
                "description1": "تستمر إسرائيل في احتجاز الأطفال الفلسطينيين في السجون العسكرية، حيث يتم محاكمتهم أمام محاكم عسكرية. كثير من هؤلاء الأطفال يتم اعتقالهم من منازلهم ليلاً وتعرضهم للاعتداءات الجسدية والنفسية أثناء الاعتقال.",
                "sources": [
                    {"name": "القدس إنفو - أكبر موقع مقدسي موثق على الانترنت", "url": "https://qudsinfo.com/"},
                    {"name": "Defense for Children International - Palestine", "url": "https://www.dci-palestine.org/"},
                    {"name": "Amnesty International", "url": "https://www.amnesty.org/en/countries/middle-east-and-north-africa/israel-and-occupied-palestinian-territories/"},
                    {"name": "Metras", "url": "https://metras.co"},
                    {"name": "Anadolu Agency (Arabic)", "url": "https://www.aa.com.tr/ar"}
                ],
                "key_facts1": [
                    "تم احتجاز أكثر من 100,000 طفل فلسطيني منذ عام 1967",
                    "تحكم المحاكم العسكرية الإسرائيلية على الأطفال بعقوبات قاسية قد تصل إلى السجن لعدة سنوات",
                    "يتعرض الأطفال الفلسطينيون للتعذيب الجسدي والنفسي أثناء الاحتجاز"
                ]
            },
            {
                "title": "Israeli Settler Violence Against Palestinians",
                "description1": "العنف من قبل المستوطنين الإسرائيليين ضد الفلسطينيين يشمل الهجمات على الأشخاص والممتلكات. تتصاعد هذه الهجمات في الأراضي الفلسطينية المحتلة دون محاسبة، حيث تشهد المنطقة انتهاكات لحقوق الإنسان يومية.",
                "sources": [
                    {"name": "القدس إنفو - أكبر موقع مقدسي موثق على الانترنت", "url": "https://qudsinfo.com/"},
                    {"name": "Human Rights Watch", "url": "https://www.hrw.org/middle-east/north-africa/israel/palestine"},
                    {"name": "B'Tselem", "url": "https://www.btselem.org/"},
                    {"name": "Metras", "url": "https://metras.co"},
                    {"name": "Anadolu Agency (Arabic)", "url": "https://www.aa.com.tr/ar"}
                ],
                "key_facts1": [
                    "أكثر من 100 هجوم من قبل المستوطنين الإسرائيليين سنويًا ضد الفلسطينيين",
                    "المستوطنات الإسرائيلية غير القانونية تُعتبر بؤرًا للعنف ضد الفلسطينيين",
                    "غالبًا ما تمر الهجمات من قبل المستوطنين دون محاسبة من السلطات الإسرائيلية"
                ]
            }
        ],
        "Culture": [
            {
                "title": "Palestinian Cultural Heritage and Identity",
                "description1": "تتميز الثقافة الفلسطينية بتاريخ طويل من الفنون، والموسيقى، والآداب، والحرف اليدوية. رغم كل محاولات الطمس الثقافي، ظل الفلسطينيون يتمسكون بهويتهم من خلال الاحتفاظ بتقاليدهم وأغانيهم ورقصاتهم.",
                "sources": [
                    {"name": "القدس إنفو - أكبر موقع مقدسي موثق على الانترنت", "url": "https://qudsinfo.com/"},
                    {"name": "Palestinian Museum", "url": "https://www.palmuseum.org/"},
                    {"name": "Palestinian Heritage Foundation", "url": "https://www.palestinianheritage.org/"},
                    {"name": "Metras", "url": "https://metras.co"},
                    {"name": "Anadolu Agency (Arabic)", "url": "https://www.aa.com.tr/ar"}
                ],
                "key_facts1": [
                    "الرقص الفلسطيني (الدبكة) هو جزء أساسي من الثقافة الفلسطينية",
                    "تمثل الموسيقى الفلسطينية جزءًا كبيرًا من الهوية الوطنية الفلسطينية",
                    "تتضمن الحرف اليدوية الفلسطينية أدوات منزلية وزخارف تمثل الحياة اليومية الفلسطينية"
                ]
            },
            {
                "title": "Palestinian Literature and Poetry",
                "description1": "الأدب الفلسطيني يزخر بالكثير من الأعمال التي تعكس معاناة الشعب الفلسطيني وتاريخه. من بين أبرز الكتاب والشعراء الفلسطينيين: محمود درويش وغسان كنفاني.",
                "sources": [
                    {"name": "القدس إنفو - أكبر موقع مقدسي موثق على الانترنت", "url": "https://qudsinfo.com/"},
                    {"name": "Maqalati", "url": "https://www.maqalati.com/"},
                    {"name": "Palestinian Writers Union", "url": "https://www.pwu.ps/"},
                    {"name": "Metras", "url": "https://metras.co"},
                    {"name": "Anadolu Agency (Arabic)", "url": "https://www.aa.com.tr/ar"}
                ],
                "key_facts1": [
                    "محمود درويش هو أحد أبرز الشعراء الفلسطينيين",
                    "غسان كنفاني كان من أبرز الكتاب الفلسطينيين الذين ناضلوا من خلال الأدب",
                    "تُعد قصيدة 'على هذه الأرض' لمحمود درويش واحدة من أشهر القصائد الفلسطينية"
                ]
            }
        ],
        "Resistance": [
            {
                "title": "The Palestinian Resistance Movement",
                "description1": "تشكلت حركات المقاومة الفلسطينية منذ بداية الاحتلال الإسرائيلي، وهي تشمل العديد من الفصائل التي تسعى لاسترجاع حقوق الفلسطينيين وإنهاء الاحتلال.",
                "sources": [
                    {"name": "القدس إنفو - أكبر موقع مقدسي موثق على الانترنت", "url": "https://qudsinfo.com/"},
                    {"name": "Palestinian Authority", "url": "https://www.palestine.gov/"},
                    {"name": "Al-Qassam Brigades", "url": "https://www.qassam.ps/"},
                    {"name": "Metras", "url": "https://metras.co"},
                    {"name": "Anadolu Agency (Arabic)", "url": "https://www.aa.com.tr/ar"}
                ],
                "key_facts1": [
                    "حركة حماس هي إحدى الفصائل الرئيسية في المقاومة الفلسطينية",
                    "تأسست الجبهة الشعبية لتحرير فلسطين في عام 1967",
                    "حركات المقاومة تواصل نضالها ضد الاحتلال الإسرائيلي من خلال العديد من الأنشطة السياسية والعسكرية"
                ]
            },
            {
                "title": "Non-Violent Resistance: Popular Struggle",
                "description1": "يشمل النضال الشعبي الفلسطيني أساليب غير عنيفة مثل التظاهرات، والإضرابات، ووقفات الاحتجاج ضد الاحتلال الإسرائيلي والمستوطنات.",
                "sources": [
                    {"name": "القدس إنفو - أكبر موقع مقدسي موقف على الانترنت", "url": "https://qudsinfo.com/"},
                    {"name": "Palestinian Center for Nonviolence", "url": "https://www.palestiniannonviolence.org/"},
                    {"name": "International Solidarity Movement", "url": "https://palsolidarity.org/"},
                    {"name": "Metras", "url": "https://metras.co"},
                    {"name": "Anadolu Agency (Arabic)", "url": "https://www.aa.com.tr/ar"}
                ],
                "key_facts1": [
                    "الاحتجاجات غير العنيفة هي جزء من استراتيجية النضال الفلسطيني",
                    "العديد من الفلسطينيين يشاركون في مقاطعة المنتجات الإسرائيلية"
                ]
            }
        ]
    }
    return resources

def get_educational_resources_EN():
    resources = {
        "History": [
            {
                "title": "The Nakba: Palestinian Exodus of 1948",
                "description": "The Nakba (catastrophe in Arabic) refers to the mass expulsion and dispossession of Palestinians during the creation of the State of Israel in 1948. Over 750,000 Palestinians were forced to leave their homes, and more than 500 Palestinian villages were destroyed.",
                "sources": [
                    {"name": "quds info", "url": "https://qudsinfo.com/"},
                    {"name": "Institute for Palestine Studies", "url": "https://www.palestine-studies.org/"},
                    {"name": "UN Archives", "url": "https://archives.un.org/"},
                    {"name": "Palestinian Journeys", "url": "https://www.paljourneys.org/en/timeline/highlight/165/nakba"}
                ],
                "key_facts": [
                    "Over 750,000 Palestinians displaced",
                    "More than 500 Palestinian villages destroyed",
                    "Confiscation of 78% of historical Palestinian lands",
                    "Creation of the world's longest unresolved refugee crisis"
                ]
            },
            {
                "title": "The 1967 Occupation and Its Consequences",
                "description": "In June 1967, Israel occupied the West Bank, East Jerusalem, the Gaza Strip, the Golan Heights, and the Sinai Peninsula during the Six-Day War. This occupation, which continues today (except for Sinai), has led to the expansion of illegal Israeli settlements and a system of military control over the Palestinian population.",
                "sources": [
                    {"name": "United Nations", "url": "https://www.un.org/unispal/"},
                    {"name": "B'Tselem", "url": "https://www.btselem.org/"},
                    {"name": "Human Rights Watch", "url": "https://www.hrw.org/middle-east/north-africa/israel/palestine"}
                ],
                "key_facts": [
                    "Over 600,000 Israeli settlers live illegally in the West Bank and East Jerusalem",
                    "More than 60% of the West Bank is under full Israeli control (Area C)",
                    "Over 700 km of separation wall, declared illegal by the International Court of Justice",
                    "More than 65 UN resolutions condemning the occupation, all ignored by Israel"
                ]
            },
            {
                "title": "The Oslo Accords and the Failure of the Peace Process",
                "description": "The Oslo Accords, signed in 1993-1995, were supposed to lead to a two-state solution within a five-year timeframe. However, they failed due to continued Israeli settlement expansion, violations of the agreements, and lack of political will to resolve fundamental issues such as Jerusalem, refugees, and borders.",
                "sources": [
                    {"name": "quds info", "url": "https://qudsinfo.com/"},
                    {"name": "Oslo Accords documents", "url": "https://peacemaker.un.org/israelopt-osloaccord93"},
                    {"name": "United Nations", "url": "https://www.un.org/unispal/"},
                    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/features/2013/9/13/oslo-accords-the-road-to-nowhere"}
                ],
                "key_facts": [
                    "Division of the West Bank into Areas A, B, and C with different levels of control",
                    "Creation of the Palestinian Authority as an interim government",
                    "Tripling of Israeli settler numbers since the Oslo Accords",
                    "Territorial fragmentation making a viable Palestinian state increasingly impossible"
                ]
            },
            {
                "title": "The Gaza Blockade Since 2007",
                "description": "Since 2007, the Gaza Strip has been under a land, air, and sea blockade imposed by Israel and Egypt. This blockade has created a catastrophic humanitarian crisis, limiting access to food, medicine, electricity, and clean water for more than 2 million Palestinians living in this coastal enclave.",
                "sources": [
                    {"name": "UNRWA", "url": "https://www.unrwa.org/where-we-work/gaza-strip"},
                    {"name": "WHO", "url": "https://www.who.int/health-topics/occupied-palestinian-territory"},
                    {"name": "OCHA", "url": "https://www.ochaopt.org/location/gaza-strip"},
                    {"name": "Oxfam", "url": "https://www.oxfam.org/en/what-we-do/countries/occupied-palestinian-territory-and-israel"}
                ],
                "key_facts": [
                    "Over 2 million people live in an area of 365 km²",
                    "More than 95% of water is unfit for human consumption",
                    "Unemployment rate exceeding 45%, one of the highest in the world",
                    "Electricity available only 4-12 hours per day on average",
                    "More than 80% of the population depends on humanitarian aid"
                ]
            }
        ],
        "Human Rights": [
            {
                "title": "The Apartheid System in Occupied Palestine",
                "description": "Numerous human rights organizations, including Amnesty International, Human Rights Watch, and B'Tselem, have concluded that Israel practices apartheid against Palestinians. This system includes discriminatory laws, territorial segregation, movement restrictions, and unequal allocation of resources.",
                "sources": [
                    {"name": "quds info", "url": "https://qudsinfo.com/"},
                    {"name": "Amnesty International", "url": "https://www.amnesty.org/en/latest/campaigns/2022/02/israels-system-of-apartheid/"},
                    {"name": "Human Rights Watch", "url": "https://www.hrw.org/report/2021/04/27/threshold-crossed/israeli-authorities-and-crimes-apartheid-and-persecution"},
                    {"name": "B'Tselem", "url": "https://www.btselem.org/publications/fulltext/202101_this_is_apartheid"},
                    {"name": "Al-Haq", "url": "https://www.alhaq.org/"}
                ],
                "key_facts": [
                    "Two separate legal systems in the West Bank: civil law for settlers, military law for Palestinians",
                    "More than 65 discriminatory laws against Palestinian citizens of Israel",
                    "Complex permit system limiting Palestinians' freedom of movement",
                    "Unequal access to water: settlers receive 3-5 times more water than Palestinians"
                ]
            },
            {
                "title": "Administrative Detention and Political Prisoners",
                "description": "Israel extensively uses administrative detention to imprison Palestinians without charge or trial, based on 'secret evidence.' Thousands of Palestinians, including children, are detained in conditions that often violate international law.",
                "sources": [
                    {"name": "quds info", "url": "https://qudsinfo.com/"},
                    {"name": "Addameer", "url": "https://www.addameer.org/"},
                    {"name": "International Committee of the Red Cross", "url": "https://www.icrc.org/en/where-we-work/middle-east/israel-and-occupied-territories"},
                    {"name": "UNICEF", "url": "https://www.unicef.org/sop/"}
                ],
                "key_facts": [
                    "More than 800,000 Palestinians detained since 1967",
                    "Approximately 500-700 Palestinian children arrested each year",
                    "99.7% conviction rate in Israeli military courts",
                    "Systematic torture and mistreatment documented by human rights organizations"
                ]
            },
            {
                "title": "Restrictions on Freedom of Movement",
                "description": "Palestinians face a complex system of movement restrictions including checkpoints, the separation wall, settler-only roads, and a permit system that severely limits their ability to move freely in their own territory.",
                "sources": [
                    {"name": "OCHA", "url": "https://www.ochaopt.org/theme/movement-and-access"},
                    {"name": "B'Tselem", "url": "https://www.btselem.org/freedom_of_movement"},
                    {"name": "Machsom Watch", "url": "https://machsomwatch.org/en"}
                ],
                "key_facts": [
                    "More than 700 physical obstacles in the West Bank (checkpoints, roadblocks, etc.)",
                    "The separation wall extends for 712 km, 85% of which is inside the West Bank",
                    "Thousands of Palestinians separated from their agricultural lands by the wall",
                    "Complex permit system required to enter East Jerusalem, travel between Gaza and the West Bank, or access 'seam zones'"
                ]
            },
            {
                "title": "Home Demolitions and Forced Displacement",
                "description": "Israel regularly practices Palestinian home demolitions, either as punitive measures or under the pretext of lacking building permits (which are systematically denied to Palestinians). These practices constitute serious violations of international humanitarian law.",
                "sources": [
                    {"name": "quds info", "url": "https://qudsinfo.com/"},
                    {"name": "OCHA", "url": "https://www.ochaopt.org/data/demolition"},
                    {"name": "B'Tselem", "url": "https://www.btselem.org/topic/planning_and_building"},
                    {"name": "Al-Haq", "url": "https://www.alhaq.org/"},
                    {"name": "Norwegian Refugee Council", "url": "https://www.nrc.no/countries/middle-east/palestine/"}
                ],
                "key_facts": [
                    "More than 55,000 Palestinian homes demolished since 1967",
                    "Less than 2% of building permit applications approved for Palestinians in Area C",
                    "East Jerusalem particularly targeted for demolitions and settlement expansion",
                    "'Silent transfer' policy aimed at reducing Palestinian presence in strategic areas"
                ]
            }
        ],
        "Culture and Society": [
            {
                "title": "Palestinian Cultural Heritage",
                "description": "Palestinian culture is rich and diverse, with traditions dating back thousands of years. It includes distinctive cuisine, traditional arts such as embroidery, pottery, and calligraphy, as well as a rich literary and musical tradition.",
                "sources": [
                    {"name": "quds info", "url": "https://qudsinfo.com/"},
                    {"name": "Arab World Institute", "url": "https://www.imarabe.org/en"},
                    {"name": "Palestinian Museum", "url": "https://www.palmuseum.org/"},
                    {"name": "UNESCO", "url": "https://en.unesco.org/countries/palestine"}
                ],
                "key_facts": [
                    "Palestinian embroidery (tatreez) is inscribed on UNESCO's Intangible Cultural Heritage list",
                    "The olive tree is a central symbol of Palestinian identity and resistance",
                    "Dabke is a traditional dance performed at celebrations",
                    "Resistance poetry is an important form of cultural expression, with poets like Mahmoud Darwish"
                ]
            },
            {
                "title": "Palestinian Diaspora",
                "description": "Following the 1948 Nakba and ongoing occupation, a significant Palestinian diaspora has formed worldwide. These communities maintain strong ties to their homeland and play a crucial role in preserving Palestinian identity and advocating for Palestinian rights.",
                "sources": [
                    {"name": "UNRWA", "url": "https://www.unrwa.org/"},
                    {"name": "Institute for Palestine Studies", "url": "https://www.palestine-studies.org/"},
                    {"name": "Badil", "url": "https://www.badil.org/"}
                ],
                "key_facts": [
                    "More than 7 million Palestinian refugees and displaced persons worldwide",
                    "Significant Palestinian communities in Jordan, Lebanon, Syria, Chile, and the United States",
                    "The key (miftah) is a symbol of refugees' right of return",
                    "Intergenerational transmission of Palestinian memory and identity"
                ]
            },
            {
                "title": "Cultural and Artistic Resistance",
                "description": "In the face of occupation, Palestinians have developed various forms of cultural and artistic resistance. Palestinian art, music, literature, and cinema serve to preserve national identity, document the realities of occupation, and express aspirations for freedom and self-determination.",
                "sources": [
                    {"name": "Palestinian Film Festival", "url": "https://www.palestinefilminstitute.org/"},
                    {"name": "Dar Yusuf Nasri Jacir for Art and Research", "url": "https://darjacir.com/"},
                    {"name": "Edward Said Institute", "url": "https://www.edwardsaid.org/"}
                ],
                "key_facts": [
                    "Emergence of internationally recognized Palestinian cinema (Elia Suleiman, Hany Abu-Assad)",
                    "Street art and graffiti on the separation wall as a form of visual protest",
                    "Development of cultural festivals such as Palest'In & Out and the Palestine Literature Festival",
                    "Use of social media to document and share occupation realities"
                ]
            },
            {
                "title": "Education and Academic Resistance",
                "description": "Despite obstacles imposed by the occupation, Palestinians place high value on education. Palestinian universities are centers of knowledge production and intellectual resistance, although they are often targeted by Israeli forces.",
                "sources": [
                    {"name": "Birzeit University", "url": "https://www.birzeit.edu/en"},
                    {"name": "Right to Education Campaign", "url": "https://right2edu.birzeit.edu/"},
                    {"name": "PACBI", "url": "https://bdsmovement.net/pacbi"}
                ],
                "key_facts": [
                    "Literacy rates among the highest in the Arab world despite occupation",
                    "Palestinian universities regularly subjected to raids, closures, and restrictions",
                    "Development of Palestine Studies as an academic discipline",
                    "Academic boycott movement against institutions complicit in the occupation"
                ]
            }
        ],
        "Resistance and Solidarity": [
            {
                "title": "The BDS Movement (Boycott, Divestment, Sanctions)",
                "description": "Launched in 2005 by Palestinian civil society, the BDS movement calls for non-violent measures to pressure Israel to comply with international law and Palestinian rights. Inspired by the South African anti-apartheid movement, it has gained significant global support.",
                "sources": [
                    {"name": "quds info", "url": "https://qudsinfo.com/"},
                    {"name": "BDS National Committee", "url": "https://bdsmovement.net/"},
                    {"name": "Palestinian Campaign for the Academic and Cultural Boycott of Israel (PACBI)", "url": "https://bdsmovement.net/pacbi"}
                ],
                "key_facts": [
                    "Three main demands: end of occupation, equality for Palestinian citizens of Israel, right of return for refugees",
                    "Notable successes including divestment by pension funds and universities",
                    "Supported by unions, churches, social movements, and personalities worldwide",
                    "Targets institutions complicit in the occupation, not individuals"
                ]
            },
            {
                "title": "Non-violent Popular Resistance",
                "description": "Palestinians have a long tradition of non-violent popular resistance against occupation, including peaceful demonstrations, sit-ins, and non-violent direct actions. These movements are often violently suppressed by Israeli forces.",
                "sources": [
                    {"name": "Popular Struggle Coordination Committee", "url": "https://popularstruggle.org/"},
                    {"name": "Stop the Wall Campaign", "url": "https://www.stopthewall.org/"},
                    {"name": "Al-Haq", "url": "https://www.alhaq.org/"}
                ],
                "key_facts": [
                    "Villages like Bil'in, Ni'lin, and Nabi Saleh known for their weekly demonstrations against the wall",
                    "Use of video documentation and social media to expose violations",
                    "International participation through movements like the International Solidarity Movement",
                    "Systematic repression including arrests, detentions, and sometimes live fire against unarmed protesters"
                ]
            },
            {
                "title": "International Solidarity",
                "description": "The solidarity movement with Palestine has developed globally, involving civil society organizations, unions, religious groups, students, and human rights activists who support the Palestinian struggle for justice and self-determination.",
                "sources": [
                    {"name": "quds info", "url": "https://qudsinfo.com/"},
                    {"name": "Palestine Solidarity Campaign", "url": "https://www.palestinecampaign.org/"},
                    {"name": "Jewish Voice for Peace", "url": "https://jewishvoiceforpeace.org/"},
                    {"name": "BDS Movement", "url": "https://bdsmovement.net/"}
                ],
                "key_facts": [
                    "International Day of Solidarity with the Palestinian People celebrated on November 29",
                    "Divestment campaigns in universities and religious institutions",
                    "Gaza flotillas attempting to break the maritime blockade",
                    "Solidarity movements including progressive Jews opposed to Israeli policies"
                ]
            },
            {
                "title": "International Recognition of the State of Palestine",
                "description": "The diplomatic struggle for recognition of the State of Palestine is an important form of political resistance. To date, more than 140 countries have recognized the State of Palestine, although most Western powers have not yet done so.",
                "sources": [
                    {"name": "quds info", "url": "https://qudsinfo.com/"},
                    {"name": "United Nations", "url": "https://www.un.org/unispal/"},
                    {"name": "Palestine Liberation Organization", "url": "https://www.nad.ps/en"},
                    {"name": "Palestinian Ministry of Foreign Affairs", "url": "http://www.mofa.pna.ps/en/"}
                ],
                "key_facts": [
                    "In 2012, Palestine obtained non-member observer state status at the UN",
                    "Membership in various international organizations, including the International Criminal Court",
                    "Recognition by more than 140 countries out of 193 UN member states",
                    "Ongoing campaigns for recognition by Western countries"
                ]
            }
        ]
    }
    return resources

# --- UI Rendering Functions ---

def render_sidebar():
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/0/00/Flag_of_Palestine.svg", width=250)
        st.title("Palestine AI")

        # Language selector
        st.markdown('### Select Language')
        col1, col2 = st.columns(2)
        if col1.button('English', key='en_button', use_container_width=True):
            st.session_state.language = 'english'
            st.rerun() # Rerun to apply language change immediately
        if col2.button('العربية', key='ar_button', use_container_width=True):
            st.session_state.language = 'arabic'
            st.rerun()

        st.markdown("---")

        # Navigation buttons
        st.markdown("### Navigation")
        if st.button('Chat with Palestina AI', key='chat_button', use_container_width=True):
            st.session_state.show_chat = True
            st.session_state.show_boycott = False
            st.session_state.show_education = False
            st.rerun()
        if st.button('Boycott Information', key='boycott_button', use_container_width=True):
            st.session_state.show_chat = False
            st.session_state.show_boycott = True
            st.session_state.show_education = False
            st.rerun()
        if st.button('Educational Resources', key='education_button', use_container_width=True):
            st.session_state.show_chat = False
            st.session_state.show_boycott = False
            st.session_state.show_education = True
            st.rerun()

        st.markdown("---")

        # Chat History Section
        st.markdown("### Chat History")

        # New Chat Button
        if st.button("➕ New Chat", use_container_width=True):
            new_chat_id = str(uuid.uuid4())
            st.session_state.history.append({
                "id": new_chat_id,
                "name": "New Chat",
                "messages": []
            })
            st.session_state.current_chat_id = new_chat_id
            st.rerun()

        # Display existing chats
        # Display in reverse order (newest first)
        for chat in reversed(st.session_state.history):
            # Use chat ID in button key to ensure uniqueness
            if st.button(chat["name"], key=f"chat_{chat['id']}", use_container_width=True):
                st.session_state.current_chat_id = chat["id"]
                # Set navigation to chat view if not already there
                st.session_state.show_chat = True
                st.session_state.show_boycott = False
                st.session_state.show_education = False
                st.rerun()

        st.markdown("---")

        # Team, Help, About sections (keep as is)
        with st.expander("Our Team", expanded=False):
            st.markdown("### Elkalem-Imrou Height School")
            st.markdown("In collaboration with Erinov Company")
            st.markdown("#### Team Members:")
            team_members = [
                "Nchachebi Abdelghani", "Yasser kasbi", "Youcef Abbouna", "Gueddi amine",
                "Khtara Hafssa", "Sirine Adoun", "Ycine Boukermouch", "Chihani Zineb",
                "Chihani Bouchera", "Mehdia Abbouna", "Rahma Elalouani", "AbdeElrahman Daouad",
                "Redouan Rekik Sadek", "Abdellatif Abdelnour", "Bahedi Bouchera",
                "Chacha Abdelazize", "Meriama Hadjyahya", "Adaouad Sanae"
            ]
            for member in team_members: st.markdown(f"• {member}")
            st.markdown("---")
            st.markdown("Supervised by Mr.Oussama SEBROU")

        with st.expander("Help", expanded=False):
            st.markdown("### How to Use the App")
            st.markdown("""
            - Ask Questions: You can ask anything related to Palestine's history, current events, or humanitarian issues.
            - Multi-Languages Supported: You can ask in English or Arabic.
            - Chat History: Your conversations are saved in the sidebar. Click 'New Chat' to start fresh or select an old chat to continue.
            - Copy Messages: Click the copy icon (📋) next to an assistant's message to copy it.
            - Dark Mode: To switch to dark mode, go to Settings > Choose app theme > Dark Mode.
            - App Features:
              - In-depth answers focused only on Palestine.
              - Context-aware responses tailored to your question.
              - Accurate, detailed information backed by AI.
              - Educational Resources: Access reliable information about Palestine.
              - Boycott Information: Learn about companies supporting Israel and alternatives.
            """)
        st.markdown("---")

        with st.expander("About Us", expanded=False):
            st.markdown("#### Palestina AI")
            st.markdown("This app was developed to provide in-depth, AI-powered insights into the Palestinian cause.")
            st.markdown("""
            Version: 1.3.0 (Chat History Update)

            #### Features
            - AI-Powered Insights about Palestine
            - Focus on History, Humanitarian Issues, and Current Events
            - Multi-Language Support (English/Arabic)
            - Context-Aware Chat with History
            - Accurate and Detailed Responses
            - Boycott Information and Alternatives
            - Educational Resources

            © 2025 Palestina AI Team. All rights reserved.

            [Contact Us](mailto:your-email@example.com?subject=Palestine%20Info%20Bot%20Inquiry&body=Dear%20Palestine%20Info%20Bot%20Team,%0A%0AWe%20are%20writing%20to%20inquire%20about%20[your%20inquiry]%2C%20specifically%20[details%20of%20your%20inquiry].%0A%0A[Provide%20additional%20context%20and%20details%20here].%0A%0APlease%20let%20us%20know%20if%20you%20require%20any%20further%20information%20from%20our%20end.%0A%0ASincerely,%0A[Your%20Company%20Name]%0A[Your%20Name]%0A[Your%20Title]%0A[Your%20Phone%20Number]%0A[Your%20Email%20Address])
            """)

def render_main_content():
    lang = st.session_state.language

    # --- Static Content (Quote, Info Cards) ---
    if lang == 'english':
        st.title("Palestina AI - From the river to the sea")
        st.markdown("""
        <blockquote style="border-left: 4px solid #1f77b4; padding-left: 15px; margin-left: 0; font-size: 1.1em;">
        <p style="color: #1f77b4; font-weight: 600; font-size: 1.3em;">"The issue of Palestine is a trial that God has tested your conscience, resolve, wealth, and unity with."</p>
        <footer style="text-align: right; font-style: italic; font-weight: 500;">— Al-Bashir Al-Ibrahimi</footer>
        </blockquote>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1: st.markdown("### Historical Context\nPalestine is a land with a deep-rooted history... [rest of text]")
        with col2: st.markdown("### Current Situation\nThe Palestinian people continue to face severe humanitarian challenges... [rest of text]")
    else: # Arabic
        st.markdown("<h1 style='font-weight: 700;'>Palestina AI From the river to the sea</h1>", unsafe_allow_html=True)
        st.markdown("""<div dir="rtl" style="font-family: 'Arial', 'Helvetica', sans-serif; line-height: 1.6;">
        <blockquote style="border-right: 4px solid #1f77b4; padding-right: 15px; margin-right: 0; font-size: 1.1em;">
        <p style="color: #1f77b4; font-weight: 600; font-size: 1.3em;">"إن قضية فلسطين محنةٌ امتحن الله بها ضمائركم وهممكم وأموالكم ووحدتكم."</p>
        <footer style="text-align: left; font-style: italic; font-weight: 500;">— البشير الإبراهيمي</footer>
        </blockquote></div>""", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1: st.markdown("<div dir='rtl'>... [Arabic Historical Context] ...</div>", unsafe_allow_html=True)
        with col2: st.markdown("<div dir='rtl'>... [Arabic Current Situation] ...</div>", unsafe_allow_html=True)

    # --- Dynamic Content (Chat / Boycott / Education) ---
    if st.session_state.show_chat:
        render_chat_interface()
    elif st.session_state.show_boycott:
        render_boycott_info(lang)
    elif st.session_state.show_education:
        render_education_info(lang)

def render_chat_interface():
    lang = st.session_state.language
    current_chat = get_current_chat()

    if not current_chat:
        st.warning("No chat selected or history is empty. Please start a new chat.")
        return

    st.markdown(f"<h2 style='font-weight: 700; color: #1f77b4; margin-bottom: 18px;'>Chat: {current_chat['name']}</h2>", unsafe_allow_html=True)

    # Display existing messages
    for msg in current_chat["messages"]:
        role = msg["role"]
        # Ensure content is string; Gemini returns parts which might be complex
        content = " ".join(p.text for p in msg["parts"]) if isinstance(msg["parts"], list) else msg["parts"]
        with st.chat_message(role):
            st.markdown(content)
            # Add copy button for assistant messages
            if role == "model":
                 # Simple copy button using st.code for easy selection
                 if st.button("📋 Copy", key=f"copy_{current_chat['id']}_{msg['parts']}"): # Needs unique key
                     st.code(content, language=None)

    # Chat input
    prompt_text = "Ask about Palestine..." if lang == 'english' else "اسأل عن فلسطين..."
    if user_input := st.chat_input(prompt_text):
        # Check relevance (optional, but kept from original code)
        # if not is_palestine_related(user_input):
        #     st.warning("Please ask questions related to Palestine.")
        #     return

        # Add user message to current chat history
        current_chat["messages"].append({"role": "user", "parts": [user_input]})

        # Update chat name if it's the first message
        if current_chat["name"] == "New Chat" and len(current_chat["messages"]) == 1:
            current_chat["name"] = generate_chat_name(user_input)

        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(user_input)

        # Prepare context for Gemini
        # Convert messages to the format expected by start_chat (if needed, depends on API version)
        gemini_history = [] 
        for msg in current_chat["messages"][:-1]: # Exclude the latest user message for history
             role = msg["role"]
             parts = msg["parts"]
             # Ensure parts is a list of strings or compatible objects
             if isinstance(parts, str): parts = [parts]
             elif isinstance(parts, list) and all(isinstance(p, str) for p in parts):
                 pass # Already in good format
             elif isinstance(parts, list) and all(hasattr(p, 'text') for p in parts):
                 parts = [p.text for p in parts] # Extract text if they are Part objects
             else:
                 st.error(f"Unexpected message format: {msg}")
                 continue # Skip malformed message
             gemini_history.append({"role": role, "parts": parts})

        # Start or continue the chat session with history
        try:
            chat_session = model.start_chat(history=gemini_history)
        except Exception as e:
            st.error(f"Failed to start chat session: {e}")
            return

        # Get response from Gemini
        with st.spinner("Generating response..." if lang == 'english' else "جارٍ إنشاء الرد..."):
            response_text = ask_gemini_with_context(user_input, chat_session)

        # Display assistant response with typing effect
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            typing_effect(response_text, message_placeholder)
            # Add copy button for the new assistant message
            if st.button("📋 Copy", key=f"copy_{current_chat['id']}_new_{user_input[:10]}"): # Needs unique key
                st.code(response_text, language=None)

        # Add assistant response to current chat history
        # Ensure the format matches what Gemini expects for future history
        current_chat["messages"].append({"role": "model", "parts": [response_text]})

        # Rerun to update sidebar with new name and display message
        st.rerun()


def render_boycott_info(lang):
    if lang == 'english':
        st.markdown("## Boycott Information")
        # ... (Paste English boycott markdown and logic here) ...
        boycott_data = get_boycott_data_EN()
        boycott_tabs = st.tabs(list(boycott_data.keys()))
        for i, (category, tab) in enumerate(zip(boycott_data.keys(), boycott_tabs)):
            with tab:
                st.markdown(f"### {category}")
                for company in boycott_data[category]["companies"]:
                    with st.expander(f"{company['name']}", expanded=False):
                        st.markdown(f"**Reason:** {company['reason']}\n**Action:** {company['action']}\n**Alternatives:** {', '.join(company['alternatives'])}")
        # ... (Rest of English boycott section) ...
    else: # Arabic
        st.markdown("## معلومات المقاطعة", unsafe_allow_html=True)
        # ... (Paste Arabic boycott markdown and logic here) ...
        boycott_data = get_boycott_data_AR()
        boycott_tabs = st.tabs(list(boycott_data.keys()))
        for i, (category, tab) in enumerate(zip(boycott_data.keys(), boycott_tabs)):
            with tab:
                st.markdown(f"<div dir='rtl'><h3>{category}</h3></div>", unsafe_allow_html=True)
                for company in boycott_data[category]["companies"]:
                     with st.expander(f"{company['name']}", expanded=False):
                         st.markdown(f"<div dir='rtl'>**سبب المقاطعة:** {company['reason1']}<br>**الإجراء الموصى به:** {company['action1']}<br>**البدائل:** {', '.join(company['alternatives1'])}</div>", unsafe_allow_html=True)
        # ... (Rest of Arabic boycott section) ...

def render_education_info(lang):
    if lang == 'english':
        st.markdown("## Educational Resources")
        # ... (Paste English education markdown and logic here) ...
        resources = get_educational_resources_EN()
        education_tabs = st.tabs(list(resources.keys()))
        for i, (category, tab) in enumerate(zip(resources.keys(), education_tabs)):
            with tab:
                st.markdown(f"### {category}")
                for resource in resources[category]:
                    with st.expander(f"{resource['title']}", expanded=False):
                        st.markdown(f"{resource['description']}")
                        st.markdown("**Key Facts:**")
                        for fact in resource['key_facts']: st.markdown(f"- {fact}")
                        st.markdown("**Sources:**")
                        for source in resource['sources']: st.markdown(f"- [{source['name']}]({source['url']})")
        # ... (Rest of English education section) ...
    else: # Arabic
        st.markdown("## موارد تعليمية", unsafe_allow_html=True)
        # ... (Paste Arabic education markdown and logic here) ...
        resources = get_educational_resources_AR()
        education_tabs = st.tabs(list(resources.keys()))
        for i, (category, tab) in enumerate(zip(resources.keys(), education_tabs)):
            with tab:
                st.markdown(f"<div dir='rtl'><h3>{category}</h3></div>", unsafe_allow_html=True)
                for resource in resources[category]:
                    with st.expander(f"{resource['title']}", expanded=False):
                        st.markdown(f"<div dir='rtl'>{resource['description1']}</div>", unsafe_allow_html=True)
                        st.markdown("<div dir='rtl'>**حقائق رئيسية:**</div>", unsafe_allow_html=True)
                        for fact in resource['key_facts1']: st.markdown(f"<div dir='rtl'>- {fact}</div>", unsafe_allow_html=True)
                        st.markdown("<div dir='rtl'>**المصادر:**</div>", unsafe_allow_html=True)
                        for source in resource['sources']: st.markdown(f"<div dir='rtl'>- [{source['name']}]({source['url']})</div>", unsafe_allow_html=True)
        # ... (Rest of Arabic education section) ...

# --- Main App Logic ---

def main():
    # Configure page settings (must be the first Streamlit command)
    st.set_page_config(
        page_title="Palestina-AI",
        page_icon="🕊️",
        layout="wide",
        menu_items={
            'Get Help': None, # Simplified
            'Report a bug': None,
            'About': 'Palestina AI - Developed by Elkalem-Imrou Height School student in collaboration with Erinov Company. Version 1.3.0'
        }
    )

    # Initialize session state variables
    initialize_session_state()

    # Render the sidebar (including history and navigation)
    render_sidebar()

    # Render the main content area based on navigation state
    render_main_content()

    # Footer
    st.markdown("---")
    st.markdown("<div style='text-align: center;'>Palestine AI - Developed by Elkalem-Imrou Height School in collaboration with Erinov Company</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()


