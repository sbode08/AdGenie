import streamlit as st
import subprocess
import time
import signal
import sys
from pyngrok import ngrok

def main():
    """Launch AdGenie with ngrok tunneling for public access"""

    st.title("🚀 AdGenie Public Launcher")
    st.info("This tool will make your AdGenie app accessible to anyone on the internet!")

    # Get ngrok auth token (optional but recommended)
    auth_token = st.text_input(
        "🔑 Ngrok Auth Token (optional but recommended)",
        type="password",
        help="Get your free token from https://dashboard.ngrok.com/get-started/your-authtoken"
    )

    if st.button("🌐 Make App Public", type="primary"):
        if auth_token:
            try:
                ngrok.set_auth_token(auth_token)
                st.success("✅ Auth token set!")
            except Exception as e:
                st.error(f"❌ Invalid auth token: {e}")
                return

        try:
            # Kill any existing streamlit processes
            try:
                subprocess.run(["taskkill", "/f", "/im", "streamlit.exe"], capture_output=True)
            except:
                pass

            # Start ngrok tunnel
            st.info("🔄 Starting ngrok tunnel...")
            public_url = ngrok.connect(8501, "http")
            st.success(f"✅ Public URL: {public_url}")

            # Start Streamlit app
            st.info("🚀 Starting AdGenie...")
            process = subprocess.Popen([
                "streamlit", "run", "app.py",
                "--server.headless", "true",
                "--server.port", "8501"
            ])

            st.balloons()
            st.markdown("## 🎉 Your app is now public!")
            st.markdown(f"**Share this link:** {public_url}")
            st.markdown("---")
            st.markdown("### 📋 Instructions for others:")
            st.markdown("1. Copy the public URL above")
            st.markdown("2. Share it with anyone you want")
            st.markdown("3. They can access your AdGenie app from anywhere!")

            # Keep the tunnel alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                st.info("🛑 Shutting down...")
                ngrok.disconnect(public_url)
                process.terminate()

        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.info("💡 Make sure ngrok is installed and you have an internet connection")

if __name__ == "__main__":
    main()