import streamlit as st
import google.generativeai as genai
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="🧞 AdGenie - AI Marketing Content Generator",
    page_icon="🧞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark mode friendly styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .section-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: rgba(70, 130, 180, 0.2);
        border-left: 4px solid #4682B4;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize Gemini API
def init_gemini():
    """Initialize Gemini API with secret key"""
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ GEMINI_API_KEY not found in st.secrets. Please add it to .streamlit/secrets.toml")
        st.stop()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash')

# Initialize session state
def init_session():
    """Set up default state for history and users"""
    if "content_history" not in st.session_state:
        st.session_state.content_history = []
    
    if "users" not in st.session_state:
        st.session_state.users = [
            {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "signup_date": "2024-01-15"},
            {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "signup_date": "2024-02-20"},
            {"id": 3, "name": "Carol White", "email": "carol@example.com", "signup_date": "2024-03-10"},
            {"id": 4, "name": "David Brown", "email": "david@example.com", "signup_date": "2024-03-25"},
        ]
    
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Generator"

# Generate marketing content using Gemini
def generate_marketing_content(product_name: str, product_description: str, model):
    """Call Gemini API to generate marketing content"""
    
    prompt = f"""You are a senior growth marketing expert and copywriter specializing in helping STARTUPS grow into large, high-visibility brands. Your job is to create high-impact marketing content that helps small startups compete with big companies by being creative, viral, and conversion-focused.

Product Name: {product_name}
Product Description: {product_description}

Context:
- This product is from a startup with limited budget
- The goal is maximum reach, engagement, and virality (especially on social media)
- Content should feel modern, fresh, and highly shareable

Return your response in this format:

1. 📢 VIRAL ADVERTISEMENT:
[Write a highly engaging, attention-grabbing ad designed for social media - make it bold, creative, and viral]

2. 📝 STARTUP-FRIENDLY PRODUCT DESCRIPTION:
[Write a clear but compelling description in 2-3 sentences - avoid corporate tone]

3. 🚀 GROWTH-FOCUSED HASHTAGS:
[Provide exactly 10 hashtags optimized for reach and discoverability - think viral and trendy]

Rules for content creation:
- Think like a viral growth marketer
- Avoid corporate tone - be bold and creative
- Focus on emotion and shareability
- Make the startup feel innovative and modern
- Use language that resonates with Gen Z and millennials"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"❌ Error generating content: {str(e)}")
        return None

# Parse the generated content
def parse_generated_content(raw_content: str):
    """Parse the Gemini response into structured sections"""
    sections = {
        "viral_ad": "",
        "product_description": "",
        "hashtags": []
    }

    try:
        # Split content by numbered sections
        lines = raw_content.split('\n')
        current_section = None
        viral_ad_lines = []
        description_lines = []
        hashtags_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for section headers
            if line.startswith('1.') and 'VIRAL ADVERTISEMENT' in line:
                current_section = 'viral_ad'
                continue
            elif line.startswith('2.') and 'STARTUP-FRIENDLY PRODUCT DESCRIPTION' in line:
                current_section = 'description'
                continue
            elif line.startswith('3.') and 'GROWTH-FOCUSED HASHTAGS' in line:
                current_section = 'hashtags'
                continue

            # Add content to current section
            if current_section == 'viral_ad':
                viral_ad_lines.append(line)
            elif current_section == 'description':
                description_lines.append(line)
            elif current_section == 'hashtags':
                hashtags_lines.append(line)

        # Process viral ad
        sections["viral_ad"] = '\n'.join(viral_ad_lines).strip()

        # Process product description
        sections["product_description"] = '\n'.join(description_lines).strip()

        # Process hashtags - extract only hashtag lines
        hashtags = []
        for line in hashtags_lines:
            # Look for lines that contain hashtags
            if '#' in line:
                # Split by spaces and filter hashtags
                parts = line.split()
                for part in parts:
                    if part.startswith('#'):
                        hashtags.append(part.strip())

        sections["hashtags"] = hashtags[:10]

        return sections
    except Exception as e:
        st.error(f"Error parsing content: {str(e)}")
        return sections

# Main generator page
def generator_page():
    """The main UI for the AI tool"""
    st.markdown('<div class="main-header">🧞 AdGenie - Marketing Content Generator</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="info-box">💡 Enter your product details and let AI create captivating marketing content for you!</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<p class="section-title">📝 Product Information</p>', unsafe_allow_html=True)
        
        product_name = st.text_input(
            "Product Name 🏷️",
            placeholder="e.g., SmartWater Bottle",
            help="Enter the name of your product"
        )
        
        product_description = st.text_area(
            "Product Description 📖",
            placeholder="Describe what your product does and its key features...",
            height=120,
            help="Provide a detailed description of your product"
        )
    
    with col2:
        st.markdown('<p class="section-title">⚙️ Options</p>', unsafe_allow_html=True)
        st.info("💾 Your content will be saved to the content log")
    
    # Generate button
    if st.button("✨ Generate Marketing Content", type="primary", use_container_width=True):
        if not product_name or not product_description:
            st.error("⚠️ Please fill in both product name and description!")
        else:
            with st.spinner("🤖 AdGenie is working its magic..."):
                model = init_gemini()
                raw_content = generate_marketing_content(product_name, product_description, model)
                
                if raw_content:
                    content_data = parse_generated_content(raw_content)
                    content_data["product_name"] = product_name
                    content_data["product_description"] = product_description
                    content_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Save to history
                    st.session_state.content_history.append(content_data)
                    
                    st.success("✅ Content generated successfully!")
                    st.session_state.show_results = True
    
    # Display results
    if st.session_state.get("show_results", False) and st.session_state.content_history:
        latest = st.session_state.content_history[-1]
        
        st.markdown("---")
        st.markdown('<p class="section-title">📊 Generated Content</p>', unsafe_allow_html=True)
        
        # Viral advertisement section
        st.markdown("#### 📢 Viral Advertisement")
        st.markdown(f'<div style="font-size: 0.9em; font-weight: normal; line-height: 1.6;">{latest["viral_ad"].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
        
        # Hashtags
        st.markdown("#### #️⃣ Growth-Focused Hashtags")
        hashtags_str = " ".join(latest["hashtags"])
        st.code(hashtags_str, language="text")
        
        # Copy buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Copy Ad", use_container_width=True):
                st.write(latest["viral_ad"])
        
        with col2:
            if st.button("📋 Copy Hashtags", use_container_width=True):
                st.write(" ".join(latest["hashtags"]))

# Admin page
def admin_page():
    """The password-protected admin dashboard"""
    
    if not st.session_state.admin_logged_in:
        st.markdown('<div class="main-header">🔐 Admin Login</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="info-box">Enter the admin password to access the dashboard</div>', unsafe_allow_html=True)
        
        password = st.text_input("🔑 Admin Password", type="password", placeholder="Enter admin password")
        
        if st.button("Login", type="primary", use_container_width=True):
            if password == "admin123":
                st.session_state.admin_logged_in = True
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Incorrect password. Try again.")
    
    else:
        # Admin dashboard
        st.markdown('<div class="main-header">⚙️ Admin Dashboard</div>', unsafe_allow_html=True)
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.admin_logged_in = False
            st.rerun()
        
        st.markdown("---")
        
        # Tabs for different admin sections
        tab1, tab2, tab3 = st.tabs(["📋 Content Log", "👥 User List", "⚡ Actions"])
        
        # Content Log Tab
        with tab1:
            st.markdown('<p class="section-title">📋 Content Generation Log</p>', unsafe_allow_html=True)
            
            if not st.session_state.content_history:
                st.info("No content generated yet.")
            else:
                st.write(f"**Total Generations:** {len(st.session_state.content_history)}")
                st.markdown("---")
                
                for i, content in enumerate(st.session_state.content_history, 1):
                    with st.expander(f"#{i} - {content['product_name']} ({content['timestamp']})"):
                        st.write(f"**Product Name:** {content['product_name']}")
                        st.write(f"**Original Description:** {content['product_description']}")
                        st.write(f"**Generated At:** {content['timestamp']}")
                        st.markdown("---")
                        st.write("**📢 Viral Ad:**")
                        st.write(content['viral_ad'])
                        st.markdown("---")
                        st.write("**📝 Generated Description:**")
                        st.write(content.get('product_description', 'N/A'))
                        st.markdown("---")
                        st.write("**#️⃣ Hashtags:**")
                        st.write(" ".join(content['hashtags']))
        
        # User List Tab
        with tab2:
            st.markdown('<p class="section-title">👥 User List</p>', unsafe_allow_html=True)
            
            st.write(f"**Total Users:** {len(st.session_state.users)}")
            st.markdown("---")
            
            # Display users in a table format
            for user in st.session_state.users:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"**{user['name']}**")
                with col2:
                    st.write(f"📧 {user['email']}")
                with col3:
                    st.write(f"📅 {user['signup_date']}")
                with col4:
                    st.write(f"ID: {user['id']}")
                st.divider()
        
        # Actions Tab
        with tab3:
            st.markdown('<p class="section-title">⚡ Admin Actions</p>', unsafe_allow_html=True)
            
            st.warning("⚠️ Dangerous Zone - Use with caution!")
            
            if st.button("🗑️ Clear All Content History", use_container_width=True, type="secondary"):
                if st.button("⚠️ CONFIRM: Clear All Data", use_container_width=True, type="primary"):
                    st.session_state.content_history = []
                    st.success("✅ All content history cleared!")
                    st.rerun()
            
            st.markdown("---")
            
            # Statistics
            st.markdown('<p class="section-title">📊 Statistics</p>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Generations", len(st.session_state.content_history))
            
            with col2:
                st.metric("Total Users", len(st.session_state.users))
            
            with col3:
                st.metric("Total Hashtags Generated", sum(len(c["hashtags"]) for c in st.session_state.content_history))

# Main navigation logic
def main():
    """Main function with navigation logic"""
    init_session()
    
    # Sidebar navigation
    st.sidebar.markdown("## 🧞 AdGenie Navigation")
    
    page = st.sidebar.radio(
        "Select Page:",
        ["Generator", "Admin Panel"],
        key="page_selector"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 About AdGenie")
    st.sidebar.info(
        "AdGenie is your AI-powered marketing content generator. "
        "Create captivating ads, product descriptions, and hashtags in seconds!"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔧 Settings")
    st.sidebar.write("Dark mode: Always On 🌙")
    
    # Route to appropriate page
    if page == "Generator":
        generator_page()
    elif page == "Admin Panel":
        admin_page()

# Run the app
if __name__ == "__main__":
    main()
