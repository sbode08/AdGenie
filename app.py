import streamlit as st
import streamlit.components.v1 as components
import openai
from datetime import datetime
import json
import os
import stripe
import requests

# Configure page
st.set_page_config(
    page_title="AdGenie - AI Marketing Content Generator",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark mode friendly styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    :root {
        font-family: 'Inter', sans-serif;
        color: #ffffff;
        background-color: #0a0e27;
    }

    body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 2rem;
        color: #ffffff;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        display: block;
        width: fit-content;
        margin: 0 auto 2rem;
    }
    .section-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.45rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        color: #e3eaf9;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.75rem;
        background-color: rgba(70, 130, 180, 0.14);
        border-left: 4px solid #5b84f0;
        margin-bottom: 1rem;
    }
    .copy-btn {
        background: linear-gradient(135deg, #5b84f0 0%, #3a5bb8 100%);
        border: none;
        color: white;
        padding: 12px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        font-size: 0.95rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        margin: 8px 0;
        cursor: pointer;
        border-radius: 999px;
        box-shadow: 0 10px 30px rgba(42, 75, 155, 0.2);
        transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
    }
    .copy-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 14px 38px rgba(42, 75, 155, 0.28);
        opacity: 0.98;
    }
    .copy-btn:active {
        transform: translateY(0);
    }
    .copy-msg {
        font-size: 0.9rem;
        color: #9bdcff;
        font-family: 'Inter', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize OpenRouter API
def init_openrouter():
    """Initialize OpenRouter API with secret key"""
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    if not api_key:
        st.error("❌ OPENROUTER_API_KEY not found in st.secrets. Please add it to .streamlit/secrets.toml")
        st.stop()
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )
    return client

# Initialize Stripe
def init_stripe():
    """Initialize Stripe with secret key"""
    stripe_key = st.secrets.get("STRIPE_SECRET_KEY")
    if not stripe_key:
        st.error("❌ STRIPE_SECRET_KEY not found in st.secrets. Please add it to .streamlit/secrets.toml")
        st.stop()
    stripe.api_key = stripe_key

# Initialize session state
def init_session():
    """Set up default state for history, users, and authentication"""
    if "content_history" not in st.session_state:
        st.session_state.content_history = []

    if "users" not in st.session_state:
        # Check if this is a demo environment
        is_demo = st.secrets.get("DEMO_MODE", "false").lower() == "true"
        
        st.session_state.users = {
            "admin": {"password": "admin123", "role": "admin", "usage_count": 0, "is_premium": True},
        }
        
        # Only add demo user in demo mode
        if is_demo:
            st.session_state.users["demo@example.com"] = {
                "password": "demo123",
                "role": "user",
                "usage_count": 0,
                "is_premium": False,
                "name": "Demo User",
                "signup_date": "2024-01-01"
            }

    if "current_user" not in st.session_state:
        st.session_state.current_user = None

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Login"

    if "user_content" not in st.session_state:
        st.session_state.user_content = {}

    if "payment_pending" not in st.session_state:
        st.session_state.payment_pending = False

# Generate marketing content using Gemini
def generate_marketing_content(product_name: str, product_description: str, tone: str, target_audience: str, client):
    """Call OpenRouter API to generate marketing content for multiple platforms"""

    prompt = f"""You are a senior growth marketing expert and copywriter specializing in helping STARTUPS grow into large, high-visibility brands. Your job is to create high-impact marketing content that helps small startups compete with big companies by being creative, viral, and conversion-focused.

Product Name: {product_name}
Product Description: {product_description}
Tone: {tone}
Target Audience: {target_audience}

Context:
- This product is from a startup with limited budget
- The goal is maximum reach, engagement, and virality (especially on social media)
- Content should feel modern, fresh, and highly shareable
- Adapt the tone to be: {tone}
- Target audience is: {target_audience}

Generate comprehensive, detailed ad copy for the following platforms. Make each piece of content engaging, conversion-focused, and optimized for its platform. Use the EXACT format shown below:

TIKTOK AD:
[Write a compelling 100-150 word TikTok caption with emojis, hashtags, and a strong call-to-action that would perform well on TikTok]

INSTAGRAM AD:
[Write a detailed 150-200 word Instagram caption with storytelling elements, emojis, and engagement hooks that would work well for Instagram posts or stories]

GOOGLE ADS:
HEADLINE: [Your headline here - max 30 chars] | DESCRIPTION: [Your description here - max 90 chars]

LINKEDIN AD:
[Write a professional 200-250 word LinkedIn post that positions the startup as innovative, includes industry insights, and has a clear value proposition for B2B connections]

GROWTH-FOCUSED HASHTAGS:
[Your 10 hashtags here, separated by spaces]

Rules for content creation:
- Think like a viral growth marketer
- Adapt tone to be: {tone}
- Target audience: {target_audience}
- Avoid corporate tone - be bold and creative
- Focus on emotion and shareability
- Make the startup feel innovative and modern
- Use language that resonates with the target audience"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"❌ Error generating content: {str(e)}")
        return None

# Parse the generated content
def parse_generated_content(raw_content: str):
    """Parse the Gemini response into structured sections"""
    sections = {
        "tiktok_ad": "",
        "instagram_ad": "",
        "google_ads": {"headline": "", "description": ""},
        "linkedin_ad": "",
        "hashtags": []
    }

    try:
        # Split content by numbered sections
        lines = raw_content.split('\n')
        current_section = None
        tiktok_lines = []
        instagram_lines = []
        google_lines = []
        linkedin_lines = []
        hashtags_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for section headers (flexible matching for both old and new formats)
            if ('TIKTOK AD:' in line.upper() or ('1.' in line and 'TIKTOK' in line.upper())):
                current_section = 'tiktok'
                continue
            elif ('INSTAGRAM AD:' in line.upper() or ('2.' in line and 'INSTAGRAM' in line.upper())):
                current_section = 'instagram'
                continue
            elif ('GOOGLE ADS:' in line.upper() or ('3.' in line and 'GOOGLE' in line.upper())):
                current_section = 'google'
                continue
            elif ('LINKEDIN AD:' in line.upper() or ('4.' in line and 'LINKEDIN' in line.upper())):
                current_section = 'linkedin'
                continue
            elif ('GROWTH-FOCUSED HASHTAGS:' in line.upper() or ('5.' in line and 'HASHTAGS' in line.upper())):
                current_section = 'hashtags'
                continue

            # Add content to current section
            if current_section == 'tiktok':
                tiktok_lines.append(line)
            elif current_section == 'instagram':
                instagram_lines.append(line)
            elif current_section == 'google':
                google_lines.append(line)
            elif current_section == 'linkedin':
                linkedin_lines.append(line)
            elif current_section == 'hashtags':
                hashtags_lines.append(line)

        # Process each section
        sections["tiktok_ad"] = '\n'.join(tiktok_lines).strip()
        sections["instagram_ad"] = '\n'.join(instagram_lines).strip()
        sections["linkedin_ad"] = '\n'.join(linkedin_lines).strip()

        # Process Google Ads - split into headline and description
        google_content = '\n'.join(google_lines).strip()
        
        # Try multiple parsing strategies
        headline = ""
        description = ""
        
        # Strategy 1: Look for explicit HEADLINE: and DESCRIPTION: format
        if "HEADLINE:" in google_content.upper() and "DESCRIPTION:" in google_content.upper():
            # Extract headline
            headline_start = google_content.upper().find("HEADLINE:")
            headline_end = google_content.upper().find("DESCRIPTION:")
            if headline_end > headline_start:
                headline = google_content[headline_start + 9:headline_end].strip()
            
            # Extract description
            description_start = google_content.upper().find("DESCRIPTION:")
            description = google_content[description_start + 12:].strip()
        
        # Strategy 2: Look for | separator
        elif '|' in google_content:
            parts = google_content.split('|', 1)
            if len(parts) >= 2:
                headline = parts[0].strip()
                description = parts[1].strip()
        
        # Strategy 3: Look for : separator
        elif ':' in google_content and google_content.count(':') >= 2:
            parts = google_content.split(':', 2)
            if len(parts) >= 3:
                headline = parts[1].strip()
                description = parts[2].strip()
        
        # Strategy 4: If only one line, assume it's the description
        elif '\n' not in google_content and len(google_content) < 50:
            description = google_content
        
        # Strategy 5: Multiple lines - first line headline, rest description
        elif '\n' in google_content:
            lines = google_content.split('\n', 1)
            headline = lines[0].strip()
            if len(lines) > 1:
                description = lines[1].strip()
        
        # Strategy 6: Fallback - put everything in description
        else:
            description = google_content
        
        # Clean up and validate
        headline = headline.strip('*').strip()  # Remove markdown formatting
        description = description.strip('*').strip()
        
        # Ensure reasonable lengths
        if len(headline) > 30:
            headline = headline[:30]
        if len(description) > 90:
            description = description[:90]
        
        sections["google_ads"]["headline"] = headline
        sections["google_ads"]["description"] = description

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
        # Fallback: try to extract content using string search
        try:
            sections["tiktok_ad"] = extract_section_content(raw_content, "TIKTOK")
            sections["instagram_ad"] = extract_section_content(raw_content, "INSTAGRAM")
            sections["linkedin_ad"] = extract_section_content(raw_content, "LINKEDIN")
            
            # Extract Google Ads
            google_section = extract_section_content(raw_content, "GOOGLE")
            if google_section:
                # Use the same improved parsing logic
                google_content = google_section.strip()
                headline = ""
                description = ""
                
                # Strategy 1: Look for explicit HEADLINE: and DESCRIPTION: format
                if "HEADLINE:" in google_content.upper() and "DESCRIPTION:" in google_content.upper():
                    # Extract headline - find text between HEADLINE: and |
                    headline_start = google_content.upper().find("HEADLINE:")
                    headline_text = google_content[headline_start + 9:].strip()
                    
                    # Find the separator (| or DESCRIPTION:)
                    pipe_pos = headline_text.find("|")
                    desc_pos = headline_text.upper().find("DESCRIPTION:")
                    
                    if pipe_pos != -1 and (desc_pos == -1 or pipe_pos < desc_pos):
                        headline = headline_text[:pipe_pos].strip()
                    elif desc_pos != -1:
                        headline = headline_text[:desc_pos].strip()
                    else:
                        headline = headline_text.strip()
                    
                    # Extract description
                    description_start = google_content.upper().find("DESCRIPTION:")
                    if description_start != -1:
                        description = google_content[description_start + 12:].strip()
                    elif pipe_pos != -1 and headline_start + 9 + pipe_pos + 1 < len(google_content):
                        description = google_content[headline_start + 9 + pipe_pos + 1:].strip()
                
                # Strategy 2: Look for | separator
                elif '|' in google_content:
                    parts = google_content.split('|', 1)
                    if len(parts) >= 2:
                        headline = parts[0].strip()
                        description = parts[1].strip()
                
                # Strategy 3: Multiple lines
                elif '\n' in google_content:
                    lines = google_content.split('\n', 1)
                    headline = lines[0].strip()
                    if len(lines) > 1:
                        description = lines[1].strip()
                
                # Clean up
                headline = headline.strip('*').strip()
                description = description.strip('*').strip()
                
                sections["google_ads"]["headline"] = headline
                sections["google_ads"]["description"] = description
                
                sections["google_ads"]["headline"] = headline
                sections["google_ads"]["description"] = description
                sections["google_ads"]["description"] = description
            
            # Extract hashtags
            hashtags_section = extract_section_content(raw_content, "HASHTAGS")
            if hashtags_section:
                hashtags = [word.strip() for word in hashtags_section.split() if word.startswith('#')]
                sections["hashtags"] = hashtags[:10]
                
        except:
            pass
        return sections

def extract_section_content(text: str, keyword: str):
    """Extract content for a specific section using keyword search"""
    lines = text.split('\n')
    content_lines = []
    capture = False
    
    for line in lines:
        line = line.strip()
        # Check for section header match (flexible)
        if keyword.upper() in line.upper():
            capture = True
            continue
        # Stop capturing when we hit the next section header
        elif capture and line and any(
            section in line.upper() for section in 
            ['TIKTOK AD:', 'INSTAGRAM AD:', 'GOOGLE ADS:', 'LINKEDIN AD:', 'GROWTH-FOCUSED HASHTAGS:',
             '1. TIKTOK', '2. INSTAGRAM', '3. GOOGLE', '4. LINKEDIN', '5. HASHTAGS']
        ):
            break
        elif capture and line:
            content_lines.append(line)
    
    return '\n'.join(content_lines).strip()

def copy_button(text, label, key):
    """Create a copy button that actually copies to clipboard."""
    safe_text = (
        text
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("\n", "\\n")
        .replace("\r", "")
        .replace('"', '\\"')
    )
    html = f"""
    <button class="copy-btn" onclick="copyToClipboard(`{safe_text}`, '{key}')">
        📋 {label}
    </button>
    <span id="copy-msg-{key}" style="margin-left: 10px; color: #00ff00;"></span>
    <script>
    function copyToClipboard(text, key) {{
        if (navigator.clipboard && window.isSecureContext) {{
            navigator.clipboard.writeText(text).then(function() {{
                showMessage(key, 'Copied!');
            }}).catch(function(err) {{
                console.error('Failed to copy: ', err);
                fallbackCopyTextToClipboard(text, key);
            }});
        }} else {{
            fallbackCopyTextToClipboard(text, key);
        }}
    }}

    function fallbackCopyTextToClipboard(text, key) {{
        var textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {{
            var successful = document.execCommand('copy');
            if (successful) {{
                showMessage(key, 'Copied!');
            }} else {{
                showMessage(key, 'Copy failed. Please copy manually.');
            }}
        }} catch (err) {{
            console.error('Fallback: Oops, unable to copy', err);
            showMessage(key, 'Copy failed. Please copy manually.');
        }}
        document.body.removeChild(textArea);
    }}

    function showMessage(key, message) {{
        const msg = document.getElementById('copy-msg-' + key);
        if (msg) {{
            msg.innerText = message;
            setTimeout(function() {{
                msg.innerText = '';
            }}, 3000);
        }}
    }}
    </script>
    """
    components.html(html, height=60)

def calculate_potential_reach(platform, text, hashtags):
    """Calculate potential magnetic reach score based on platform, text length, and hashtags."""
    import random

    # Base reach ranges by platform
    base_ranges = {
        "tiktok": (5000, 15000),
        "instagram": (4000, 12000),
        "linkedin": (500, 3000)
    }

    if platform not in base_ranges:
        return "0k"

    min_reach, max_reach = base_ranges[platform]

    # Start with random base reach
    reach = random.randint(min_reach, max_reach)

    # Apply hashtag bonus (15% increase if more than 3 hashtags)
    if len(hashtags) > 3:
        reach = int(reach * 1.15)

    # Apply text length penalty (10% decrease if shorter than 100 characters)
    if len(text.strip()) < 100:
        reach = int(reach * 0.9)

    # Format with 'k' suffix
    if reach >= 1000:
        formatted = f"{reach / 1000:.1f}k"
    else:
        formatted = str(reach)

    return formatted

def get_strategic_insight():
    """Return a random strategic insight for premium users."""
    import random

    insights = [
        "High reach potential: Your copy uses high-energy trigger words that match current trends.",
        "Strategic length: The word count is optimized for mobile-scroll retention.",
        "Polarity Match: The tone effectively bridges the gap between your brand and the target audience."
    ]

    return random.choice(insights)

# User authentication functions
def login_user(email, password):
    """Authenticate user login"""
    if not email or not password:
        return False

    email_key = email.strip().lower()
    if email_key in st.session_state.users:
        user = st.session_state.users[email_key]
        if user["password"] == password:
            st.session_state.current_user = email_key
            return True
    return False

def register_user(email, password, name):
    """Register a new user"""
    if not email or not password or not name:
        return False, "Please fill in all fields"

    email_key = email.strip().lower()
    if email_key in st.session_state.users:
        return False, "Email already exists"
    
    st.session_state.users[email_key] = {
        "password": password,
        "role": "user",
        "usage_count": 0,
        "is_premium": False,
        "name": name,
        "signup_date": datetime.now().strftime("%Y-%m-%d")
    }
    st.session_state.user_content[email_key] = []
    return True, "Registration successful"

def check_usage_limit():
    """Check if current user has exceeded free usage limit"""
    if st.session_state.current_user:
        user = st.session_state.users[st.session_state.current_user]
        return user["usage_count"] >= 3 and not user["is_premium"]
    return False

def increment_usage():
    """Increment usage count for current user"""
    if st.session_state.current_user:
        st.session_state.users[st.session_state.current_user]["usage_count"] += 1

def save_user_content(content_data):
    """Save generated content to user's personal history"""
    if st.session_state.current_user:
        if st.session_state.current_user not in st.session_state.user_content:
            st.session_state.user_content[st.session_state.current_user] = []
        st.session_state.user_content[st.session_state.current_user].append(content_data)

# Payment processing with Stripe
def create_checkout_session(plan_type):
    """Create a Stripe checkout session for payment"""
    init_stripe()
    
    if plan_type == "basic":
        price_id = st.secrets.get("STRIPE_BASIC_PRICE_ID")  # You'll need to create these in Stripe dashboard
        price = 9.99
    elif plan_type == "pro":
        price_id = st.secrets.get("STRIPE_PRO_PRICE_ID")
        price = 19.99
    else:
        return None
    
    if not price_id:
        st.error("❌ Stripe price ID not configured. Please add STRIPE_BASIC_PRICE_ID and STRIPE_PRO_PRICE_ID to .streamlit/secrets.toml")
        return None
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{st.secrets.get('APP_URL', 'http://localhost:8501')}/?success=true&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{st.secrets.get('APP_URL', 'http://localhost:8501')}/?canceled=true",
            metadata={
                'user_email': st.session_state.current_user,
                'plan_type': plan_type
            }
        )
        return checkout_session
    except Exception as e:
        st.error(f"❌ Error creating checkout session: {str(e)}")
        return None

def process_payment_success(session_id):
    """Process successful payment from Stripe webhook or redirect"""
    try:
        init_stripe()
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            user_email = session.metadata.get('user_email')
            plan_type = session.metadata.get('plan_type')
            
            if user_email and user_email in st.session_state.users:
                st.session_state.users[user_email]["is_premium"] = True
                st.session_state.users[user_email]["plan_type"] = plan_type
                st.session_state.users[user_email]["subscription_id"] = session.subscription
                st.success("✅ Payment successful! Welcome to premium!")
                return True
    except Exception as e:
        st.error(f"❌ Error processing payment: {str(e)}")
    return False

# Social Media Posting Functions
def post_to_tiktok(content, hashtags):
    """Post content to TikTok (simplified - would need TikTok for Developers API)"""
    # Note: TikTok API requires developer account and specific permissions
    # This is a placeholder for the actual implementation
    api_key = st.secrets.get("TIKTOK_API_KEY")
    if not api_key:
        return False, "TikTok API not configured"
    
    try:
        # This would need actual TikTok API implementation
        # For now, just simulate success
        st.info("🎵 TikTok posting would be implemented here with TikTok for Developers API")
        return True, "TikTok video post simulated (API integration needed)"
    except Exception as e:
        return False, f"TikTok posting failed: {str(e)}"
    """Post content to TikTok (simplified - would need TikTok for Developers API)"""
    # Note: TikTok API requires developer account and specific permissions
    # This is a placeholder for the actual implementation
    api_key = st.secrets.get("TIKTOK_API_KEY")
    if not api_key:
        return False, "TikTok API not configured"
    
    try:
        # This would need actual TikTok API implementation
        # For now, just simulate success
        st.info("🎵 TikTok posting would be implemented here with TikTok for Developers API")
        return True, "TikTok video post simulated (API integration needed)"
    except Exception as e:
        return False, f"TikTok posting failed: {str(e)}"

def post_to_instagram(content, hashtags):
    """Post content to Instagram (simplified - would need Meta Graph API)"""
    access_token = st.secrets.get("INSTAGRAM_ACCESS_TOKEN")
    if not access_token:
        return False, "Instagram API not configured"
    
    try:
        # This would need actual Instagram Graph API implementation
        # For now, just simulate success
        st.info("📸 Instagram posting would be implemented here with Meta Graph API")
        return True, "Instagram post simulated (API integration needed)"
    except Exception as e:
        return False, f"Instagram posting failed: {str(e)}"

def post_to_linkedin(content):
    """Post content to LinkedIn"""
    access_token = st.secrets.get("LINKEDIN_ACCESS_TOKEN")
    if not access_token:
        return False, "LinkedIn API not configured"
    
    try:
        # LinkedIn API posting
        url = "https://api.linkedin.com/v2/ugcPosts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Get user profile info first using modern LinkedIn API endpoint
        profile_url = "https://api.linkedin.com/v2/me"
        profile_response = requests.get(profile_url, headers=headers)
        
        if profile_response.status_code != 200:
            return False, f"Failed to get LinkedIn profile: {profile_response.status_code} - {profile_response.text}"
        
        profile_data = profile_response.json()
        author = f"urn:li:person:{profile_data.get('id')}"
        
        post_data = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        response = requests.post(url, headers=headers, json=post_data)
        if response.status_code == 201:
            return True, "Posted to LinkedIn successfully"
        else:
            return False, f"LinkedIn posting failed: {response.text}"
    except Exception as e:
        return False, f"LinkedIn posting failed: {str(e)}"

def post_to_social_media(platform, content_data):
    """Post generated content to selected social media platform"""
    if platform == "tiktok":
        content = content_data.get("tiktok_ad", "")
        hashtags = content_data.get("hashtags", [])
        return post_to_tiktok(content, hashtags)
    elif platform == "instagram":
        content = content_data.get("instagram_ad", "")
        hashtags = content_data.get("hashtags", [])
        return post_to_instagram(content, hashtags)
    elif platform == "linkedin":
        content = content_data.get("linkedin_ad", "")
        return post_to_linkedin(content)
    else:
        return False, "Unsupported platform"

# Login page
def login_page():
    """User login and registration page"""
    st.markdown('<div class="main-header">Welcome to AdGenie</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.markdown("### Login to Your Account")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary", use_container_width=True):
            if login_user(email, password):
                st.success("✅ Login successful!")
                st.session_state.current_page = "Generator"
                st.rerun()
            else:
                # Check if this is demo mode
                is_demo = st.secrets.get("DEMO_MODE", "false").lower() == "true"
                if is_demo:
                    st.error("❌ Invalid email or password. Use demo@example.com / demo123 for the demo account.")
                else:
                    st.error("❌ Invalid email or password. Please check your credentials and try again.")
    
    with tab2:
        st.markdown("### Create New Account")
        name = st.text_input("Full Name", key="reg_name")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
        
        if st.button("Register", type="primary", use_container_width=True):
            if password != confirm_password:
                st.error("❌ Passwords do not match")
            elif not name or not email or not password:
                st.error("❌ Please fill in all fields")
            else:
                success, message = register_user(email, password, name)
                if success:
                    st.success(f"✅ {message}")
                    st.session_state.current_page = "Generator"
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

# Payment page
def payment_page():
    """Payment options for premium access"""
    st.markdown('<div class="main-header">Upgrade to Premium</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-box">You\'ve reached the free usage limit. Choose a plan below to unlock more features. This is a demo payment flow and does not process real charges.</div>', unsafe_allow_html=True)

    if "selected_payment_plan" not in st.session_state:
        st.session_state.selected_payment_plan = None
    if "payment_details_submitted" not in st.session_state:
        st.session_state.payment_details_submitted = False

    if st.session_state.payment_details_submitted:
        st.success("✅ Payment details submitted successfully.")
        st.info("This is a non-functional demo checkout. No real payment was processed.")
        if st.button("Return to Generator", use_container_width=True):
            st.session_state.payment_pending = False
            st.session_state.payment_details_submitted = False
            st.session_state.selected_payment_plan = None
            st.rerun()
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🚀 Pro Plan")
        st.markdown("**$19.99/month**")
        st.markdown("- Unlimited ad generation")
        st.markdown("- Content analytics with potential reach estimation")
        st.markdown("- Quick social media access (TikTok, Instagram, LinkedIn)")
        st.markdown("- AI-driven caption suggestions")
        if st.button("Choose Pro", type="primary", use_container_width=True, key="choose_pro"):
            st.session_state.selected_payment_plan = "pro"

    with col2:
        st.markdown("### 🌐 Premium Plan")
        st.markdown("**$29.99/month**")
        st.markdown("- Everything in Pro")
        st.markdown("- Strategic insights with 'Analyze Why' feature")
        st.markdown("- Advanced content performance analytics")
        st.markdown("- Priority support and early access to new features")
        if st.button("Choose Premium", type="primary", use_container_width=True, key="choose_premium"):
            st.session_state.selected_payment_plan = "premium"

    if st.session_state.selected_payment_plan:
        plan_name = st.session_state.selected_payment_plan.title()
        st.markdown(f"### Checkout for {plan_name} Plan")
        st.markdown("_Enter your details below to continue. This is a demo form only._")

        with st.form("demo_payment_form"):
            payer_name = st.text_input("Full name", placeholder="John Doe")
            paypal_email = st.text_input("PayPal email", placeholder="example@paypal.com")
            paypal_account = st.text_input("PayPal account name", placeholder="Your PayPal account name")
            notes = st.text_area("Additional notes", placeholder="Optional: billing company, campaign goals, or social media handles")
            paid = st.form_submit_button("Submit payment details")

            if paid:
                if st.session_state.current_user and st.session_state.current_user in st.session_state.users:
                    st.session_state.users[st.session_state.current_user]["is_premium"] = True
                    st.session_state.users[st.session_state.current_user]["plan_type"] = st.session_state.selected_payment_plan
                    st.session_state.users[st.session_state.current_user]["subscription_id"] = f"demo_{st.session_state.selected_payment_plan}"
                st.session_state.payment_pending = False
                st.session_state.payment_details_submitted = True
                st.success("Payment demo complete. Your plan is active for this session.")
                st.info("No real charge was made. This is a placeholder checkout page.")

# Main generator page
def generator_page():
    """The main UI for the AI tool"""
    if not st.session_state.current_user:
        st.error("Please login first")
        return
    
    user = st.session_state.users[st.session_state.current_user]
    st.markdown(f'<div class="main-header">AdGenie - Welcome {user["name"]}</div>', unsafe_allow_html=True)
    
    # Usage indicator
    usage_count = user["usage_count"]
    is_premium = user["is_premium"]
    
    if not is_premium:
        if usage_count < 3:
            st.info(f"Free uses remaining: {3 - usage_count}")
        else:
            st.error("You've reached the free usage limit. Please upgrade to continue.")
            if st.button("Upgrade Now", type="primary"):
                st.session_state.payment_pending = True
                st.rerun()
            return
    
    st.markdown('<div class="info-box">💡 Enter your product details and let AI create captivating marketing content for multiple platforms!</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<p class="section-title">Product Information</p>', unsafe_allow_html=True)
        
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
        
        # New inputs for tone and target audience
        col_a, col_b = st.columns(2)
        with col_a:
            tone = st.selectbox(
                "🎭 Tone",
                ["Casual & Friendly", "Professional", "Energetic & Bold", "Humorous", "Inspirational", "Urgent"],
                help="Choose the tone for your ads"
            )
        with col_b:
            target_audience = st.selectbox(
                "👥 Target Audience",
                ["Gen Z (18-24)", "Millennials (25-40)", "Professionals (25-55)", "Families", "Tech Enthusiasts", "Small Business Owners"],
                help="Who is your target audience?"
            )
    
    with col2:
        st.markdown('<p class="section-title">Options</p>', unsafe_allow_html=True)
        st.info("Your content will be saved to your personal dashboard")
    
    # Generate button with custom gradient styling
    st.markdown("""
    <style>
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        color: white !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 35px rgba(102, 126, 234, 0.4) !important;
        opacity: 0.95 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("✨ Generate Marketing Content", type="primary", use_container_width=True):
        if not product_name or not product_description:
            st.error("⚠️ Please fill in both product name and description!")
        else:
            with st.spinner("🤖 AdGenie is working its magic..."):
                client = init_openrouter()
                raw_content = generate_marketing_content(product_name, product_description, tone, target_audience, client)
                
                if raw_content:
                    # Debug: Show raw content for troubleshooting
                    with st.expander("Debug: Raw AI Response"):
                        st.code(raw_content, language="text")
                    
                    content_data = parse_generated_content(raw_content)
                    content_data["product_name"] = product_name
                    content_data["product_description"] = product_description
                    content_data["tone"] = tone
                    content_data["target_audience"] = target_audience
                    content_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Save to user's personal content
                    save_user_content(content_data)
                    
                    # Increment usage for non-premium users
                    if not is_premium:
                        increment_usage()
                    
                    st.success("✅ Content generated successfully!")
                    st.session_state.show_results = True
    
    # Display results
    if st.session_state.get("show_results", False) and st.session_state.user_content.get(st.session_state.current_user):
        latest = st.session_state.user_content[st.session_state.current_user][-1]
        st.markdown("---")
        st.markdown('<p class="section-title">Generated Content</p>', unsafe_allow_html=True)
        
        # Platform-specific ads
        tabs = st.tabs(["TikTok", "Instagram", "Google Ads", "LinkedIn", "Hashtags"])
        
        with tabs[0]:
            st.markdown("#### 🎵 TikTok Ad")
            if latest["tiktok_ad"].strip():
                st.markdown(f'<div style="font-size: 0.9em; font-weight: normal; line-height: 1.6;">{latest["tiktok_ad"].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
                copy_button(latest["tiktok_ad"], "Copy TikTok Ad", "tiktok")
            else:
                st.warning("No TikTok ad content generated")
        
        with tabs[1]:
            st.markdown("#### Instagram Ad")
            if latest["instagram_ad"].strip():
                st.markdown(f'<div style="font-size: 0.9em; font-weight: normal; line-height: 1.6;">{latest["instagram_ad"].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
                copy_button(latest["instagram_ad"], "Copy Instagram Ad", "instagram")
            else:
                st.warning("No Instagram ad content generated")
        
        with tabs[2]:
            st.markdown("#### Google Ads")
            if latest['google_ads']['headline'] or latest['google_ads']['description']:
                st.markdown(f"**Headline:** {latest['google_ads']['headline']}")
                st.markdown(f"**Description:** {latest['google_ads']['description']}")
                google_text = f"{latest['google_ads']['headline']}\n{latest['google_ads']['description']}"
                copy_button(google_text, "Copy Google Ads", "google")
            else:
                st.warning("No Google Ads content generated")
        
        with tabs[3]:
            st.markdown("#### LinkedIn Ad")
            if latest["linkedin_ad"].strip():
                st.markdown(f'<div style="font-size: 0.9em; font-weight: normal; line-height: 1.6;">{latest["linkedin_ad"].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
                copy_button(latest["linkedin_ad"], "Copy LinkedIn Ad", "linkedin")
            else:
                st.warning("No LinkedIn ad content generated")
        
        with tabs[4]:
            st.markdown("#### Growth-Focused Hashtags")
            if latest["hashtags"]:
                hashtags_str = " ".join(latest["hashtags"])
                st.code(hashtags_str, language="text")
                copy_button(hashtags_str, "Copy Hashtags", "hashtags")
            else:
                st.warning("No hashtags generated")
    elif st.session_state.get("show_results", False):
        st.session_state.show_results = False
        
        # Post-Generation Analytics Dashboard
        st.markdown("---")
        st.markdown('<p class="section-title">📊 Content Analytics</p>', unsafe_allow_html=True)
        
        # Potential Reach Badge
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Calculate reach for the most relevant platform (TikTok as default)
            reach_score = calculate_potential_reach("tiktok", latest.get("tiktok_ad", ""), latest.get("hashtags", []))
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 1rem; 
                        border-radius: 12px; 
                        text-align: center; 
                        color: white; 
                        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📈</div>
                <div style="font-size: 1.2rem; font-weight: 600;">Potential Magnetic Reach</div>
                <div style="font-size: 1.8rem; font-weight: 700; margin-top: 0.5rem;">{reach_score}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Analyze Why Feature
            if not is_premium:
                st.button("🔍 Unlock Insights", disabled=True, use_container_width=True, 
                         help="Upgrade to Premium to access strategic insights about your content performance")
            else:
                if st.button("🔍 Analyze Why", type="secondary", use_container_width=True):
                    insight = get_strategic_insight()
                    st.success(f"💡 **Strategic Insight:** {insight}")
        
        # Disclaimer
        st.markdown("""
        <div style="font-size: 0.8rem; color: #888; text-align: center; margin-top: 1rem; font-style: italic;">
        Estimation based on copy quality and current platform algorithms. Real-world results may vary.
        </div>
        """, unsafe_allow_html=True)
        
        # Social Media Posting for Premium Users
        if is_premium:
            st.markdown("---")
            st.markdown('<p class="section-title">🚀 Premium Feature: Quick Social Media Access</p>', unsafe_allow_html=True)
            st.markdown("Quickly access your social media platforms to share your generated content!")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.link_button("📱 Post to TikTok", "https://www.tiktok.com/", type="secondary", use_container_width=True)
            
            with col2:
                st.link_button("📸 Post to Instagram", "https://www.instagram.com/", type="secondary", use_container_width=True)
            
            with col3:
                st.link_button("💼 Post to LinkedIn", "https://www.linkedin.com/", type="secondary", use_container_width=True)
            
            st.info("💡 Configure your social media API keys in `.streamlit/secrets.toml` to enable posting")

# Admin page
def admin_page():
    """The password-protected admin dashboard"""
    
    if not st.session_state.admin_logged_in:
        st.markdown('<div class="main-header">Admin Login</div>', unsafe_allow_html=True)
        
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
        st.markdown('<div class="main-header">Admin Dashboard</div>', unsafe_allow_html=True)
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.admin_logged_in = False
            st.rerun()
        
        st.markdown("---")
        
        # Tabs for different admin sections
        tab1, tab2, tab3, tab4 = st.tabs(["All Content", "Users", "Revenue", "Actions"])
        
        # Content Log Tab
        with tab1:
            st.markdown('<p class="section-title">📋 All User Content</p>', unsafe_allow_html=True)
            
            total_content = sum(len(content_list) for content_list in st.session_state.user_content.values())
            st.write(f"**Total Content Generated:** {total_content}")
            st.markdown("---")
            
            for user_email, content_list in st.session_state.user_content.items():
                if content_list:
                    user_info = st.session_state.users.get(user_email, {})
                    with st.expander(f"👤 {user_info.get('name', user_email)} ({len(content_list)} items)"):
                        for i, content in enumerate(content_list, 1):
                            st.write(f"**#{i} - {content['product_name']}** ({content['timestamp']})")
                            st.write(f"Tone: {content.get('tone', 'N/A')} | Audience: {content.get('target_audience', 'N/A')}")
                            st.markdown("---")
        
        # User List Tab
        with tab2:
            st.markdown('<p class="section-title">👥 User Management</p>', unsafe_allow_html=True)
            
            users_data = []
            for email, user_data in st.session_state.users.items():
                if user_data.get("role") == "user":
                    users_data.append({
                        "Email": email,
                        "Name": user_data.get("name", "N/A"),
                        "Usage": user_data.get("usage_count", 0),
                        "Premium": "Yes" if user_data.get("is_premium") else "No",
                        "Signup": user_data.get("signup_date", "N/A")
                    })
            
            st.write(f"**Total Users:** {len(users_data)}")
            st.markdown("---")
            
            if users_data:
                # Display as table
                st.table(users_data)
        
        # Revenue Tab
        with tab3:
            st.markdown('<p class="section-title">💰 Revenue Analytics</p>', unsafe_allow_html=True)
            
            premium_users = sum(1 for user in st.session_state.users.values() if user.get("is_premium"))
            total_revenue = premium_users * 9.99  # Assuming basic plan
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Premium Users", premium_users)
            with col2:
                st.metric("Monthly Revenue", f"${total_revenue:.2f}")
            with col3:
                st.metric("Conversion Rate", f"{premium_users/max(1, len([u for u in st.session_state.users.values() if u.get('role')=='user']))*100:.1f}%")
        
        # Actions Tab
        with tab4:
            st.markdown('<p class="section-title">Admin Actions</p>', unsafe_allow_html=True)
            
            st.warning("⚠️ Dangerous Zone - Use with caution!")
            
            if st.button("🗑️ Clear All User Content", use_container_width=True, type="secondary"):
                if st.button("⚠️ CONFIRM: Clear All Data", use_container_width=True, type="primary"):
                    st.session_state.user_content = {}
                    for user in st.session_state.users.values():
                        if user.get("role") == "user":
                            user["usage_count"] = 0
                    st.success("✅ All user content cleared!")
                    st.rerun()
            
            st.markdown("---")
            
            # Statistics
            st.markdown('<p class="section-title">Platform Statistics</p>', unsafe_allow_html=True)
            
            total_users = len([u for u in st.session_state.users.values() if u.get("role") == "user"])
            total_content = sum(len(content_list) for content_list in st.session_state.user_content.values())
            total_hashtags = sum(len(content.get("hashtags", [])) for content_list in st.session_state.user_content.values() for content in content_list)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Users", total_users)
            with col2:
                st.metric("Total Generations", total_content)
            with col3:
                st.metric("Total Hashtags", total_hashtags)

# User dashboard
def user_dashboard():
    """User's personal dashboard to view their saved content"""
    if not st.session_state.current_user:
        st.error("Please login first")
        return
    
    user = st.session_state.users[st.session_state.current_user]
    st.markdown(f'<div class="main-header">Your Dashboard - {user["name"]}</div>', unsafe_allow_html=True)
    
    user_content = st.session_state.user_content.get(st.session_state.current_user, [])
    
    if not user_content:
        st.info("You haven't generated any content yet. Head to the Generator to create your first ad!")
        return
    
    st.write(f"**Total Content Generated:** {len(user_content)}")
    st.markdown("---")
    
    for i, content in enumerate(reversed(user_content), 1):  # Show latest first
        with st.expander(f"#{len(user_content)-i+1} - {content['product_name']} ({content['timestamp']})"):
            st.write(f"**Tone:** {content.get('tone', 'N/A')}")
            st.write(f"**Target Audience:** {content.get('target_audience', 'N/A')}")
            
            # Quick preview of each platform
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📱 TikTok:**")
                st.write(content["tiktok_ad"][:100] + "..." if len(content["tiktok_ad"]) > 100 else content["tiktok_ad"])
            
            with col2:
                st.markdown("**Instagram:**")
                st.write(content["instagram_ad"][:100] + "..." if len(content["instagram_ad"]) > 100 else content["instagram_ad"])
            
            col3, col4 = st.columns(2)
            with col3:
                st.markdown("**Google:**")
                st.write(content["google_ads"]["headline"])
            
            with col4:
                st.markdown("**LinkedIn:**")
                st.write(content["linkedin_ad"][:100] + "..." if len(content["linkedin_ad"]) > 100 else content["linkedin_ad"])

# Main navigation logic
def main():
    """Main function with navigation logic"""
    init_session()
    
    # Sidebar navigation
    st.sidebar.markdown("## AdGenie Navigation")
    
    if st.session_state.current_user:
        user = st.session_state.users[st.session_state.current_user]
        st.sidebar.markdown(f"**Welcome, {user['name']}!**")
        
        if user.get("is_premium"):
            st.sidebar.markdown("🌟 **Premium User**")
        else:
            usage_left = max(0, 3 - user.get("usage_count", 0))
            st.sidebar.markdown(f"**Free uses left: {usage_left}**")
        
        st.sidebar.markdown("---")
        
        page_options = ["Generator", "My Dashboard", "Admin Panel", "Logout"]
    else:
        page_options = ["Login"]
    
    page = st.sidebar.radio(
        "Select Page:",
        page_options,
        key="page_selector"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 About AdGenie")
    st.sidebar.info(
        "AdGenie is your AI-powered marketing content generator. "
        "Create captivating ads for multiple platforms in seconds!"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔧 Settings")
    st.sidebar.write("Dark mode: Always On 🌙")
    
    # Fix stale payment state if user is already premium
    if st.session_state.payment_pending and st.session_state.current_user:
        user = st.session_state.users.get(st.session_state.current_user, {})
        if user.get("is_premium"):
            st.session_state.payment_pending = False

    # Route to appropriate page
    if st.session_state.payment_pending:
        payment_page()
    elif page == "Login" or not st.session_state.current_user:
        login_page()
    elif page == "Generator":
        generator_page()
    elif page == "My Dashboard":
        user_dashboard()
    elif page == "Admin Panel":
        admin_page()
    elif page == "Logout":
        st.session_state.current_user = None
        st.session_state.current_page = "Login"
        st.rerun()

# Run the app
if __name__ == "__main__":
    main()
