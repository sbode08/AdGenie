# 🧞 AdGenie - AI Marketing Content Generator

A Streamlit app that uses Google Gemini API to generate engaging marketing content for your products.

## Features

✨ **AI-Powered Content Generation**
- Generate viral advertisements designed for social media
- Create compelling startup-friendly product descriptions
- Get 10 growth-focused hashtags optimized for reach

🔐 **Admin Dashboard**
- Password-protected admin panel
- View all generated content history
- Manage user list (mock data)
- Clear all data with confirmation

💾 **Session-Based Storage**
- No database required
- All data stored in Streamlit session state
- Clean, simple architecture

🎨 **Beautiful UI**
- Dark mode friendly design
- Responsive layout
- Emoji-rich interface

## Setup Instructions

### 1. Prerequisites
- Python 3.9+
- pip package manager

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Get Your Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your API key

### 4. Configure Secrets
Edit `.streamlit/secrets.toml` and replace `your-api-key-here` with your actual API key:

```toml
GEMINI_API_KEY = "your-actual-api-key"
```

### 5. Run the App
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

### Generator Page
1. Enter your product name
2. Describe your product
3. Click "Generate Marketing Content"
4. View and copy the generated content (ads, description, hashtags)

### Admin Panel
1. Click on "Admin Panel" in the sidebar
2. Enter password: `admin123`
3. Access features:
   - **Content Log**: View all generated content
   - **User List**: See registered users
   - **Actions**: Clear all data and view statistics

## Project Structure

```
ad genie third attempt/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
└── .streamlit/
    ├── secrets.toml               # API keys (add your Gemini key here)
    └── config.toml                # Streamlit configuration
```

## Code Structure

### `init_session()`
Initializes Streamlit session state with:
- `content_history`: List of generated content
- `users`: Mock user data
- `admin_logged_in`: Admin authentication state
- `current_page`: Current page being viewed

### `generator_page()`
Main UI for the AI tool:
- Product input form
- Content generation with Gemini API
- Results display with copy buttons

### `admin_page()`
Password-protected dashboard with:
- Login form
- Content log viewer
- User list display
- Admin actions (clear data, statistics)

### `main()`
Navigation logic to switch between pages using sidebar radio buttons

## Customization

### Change Admin Password
Edit `admin_page()` function and change:
```python
if password == "admin123":  # Change this password
```

### Modify Gemini Prompt
Edit the `generate_marketing_content()` function to customize the AI instructions

### Add More Features
You can easily extend the app by:
- Adding more sections to the admin dashboard
- Creating additional content generation options
- Implementing custom styling

## API Costs

The app uses the **Gemini 2.5 Flash** model, which is:
- Very fast
- Cost-effective
- Great for marketing content generation

Monitor your usage at [Google Cloud Console](https://console.cloud.google.com/)

## Troubleshooting

**Error: "GEMINI_API_KEY not found"**
- Make sure `.streamlit/secrets.toml` exists
- Verify you've added your API key correctly
- Restart the Streamlit app

**Error: "API key invalid"**
- Check your API key is correct at [Google AI Studio](https://aistudio.google.com/app/apikey)
- Make sure there are no extra spaces in the key

**Admin Panel Not Responding**
- Clear browser cookies or use incognito mode
- Restart Streamlit with: `streamlit run app.py --logger.level=debug`

## License

This project is open source and available for personal and commercial use.

## 🚀 Deploying on Streamlit Cloud

### Prerequisites
- GitHub account with your AdGenie repository
- Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))
- Your Gemini API key ready

### Step-by-Step Deployment

1. **Go to Streamlit Cloud**
   - Visit: https://share.streamlit.io
   - Sign in with your GitHub account

2. **Deploy Your App**
   - Click "New app"
   - Select your GitHub repository
   - Choose the branch (usually `main`)
   - Set the main file path to: `app.py`

3. **Add Your API Key**
   - Once deployed, click on the app menu (3 dots)
   - Go to "Settings"
   - Scroll to "Secrets"
   - Add your secret:
     ```
     GEMINI_API_KEY = "your-actual-api-key-here"
     ```
   - Save and the app will auto-refresh

4. **Your App is Live! 🎉**
   - Streamlit Cloud automatically gives you a public URL
   - URL format: `https://your-app-name.streamlit.app`
   - Share this URL with anyone!

### Tips for Streamlit Cloud
- Free tier available with 1 app per account
- Apps auto-refresh when you push code changes to GitHub
- No need to keep `secrets.toml` in Git (Streamlit Cloud manages secrets)
- Monitor usage in your account dashboard

## Alternative Deployment Options

### Option 2: Ngrok (Quick Testing)
For instant public access without GitHub:

```bash
# Run the public launcher
streamlit run public_launcher.py
```

### Option 3: Other Cloud Platforms
- Heroku, Google Cloud Run, AWS, DigitalOcean
- See platform-specific Streamlit deployment guides
