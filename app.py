import streamlit as st
import os
import time
import warnings
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from yt_dlp import YoutubeDL, DownloadError
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import subprocess

# Suppress warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Define the SpotifyMusicDownloader class
class SpotifyMusicDownloader:
    def __init__(self):
        self.islinkVerified = False
        self.YTDLAudioFormat = "webm"  # Download as WebM to ensure compatibility
        self.bitrate = "320"
        client_id = st.secrets["client_id"]
        client_secret = st.secrets["client_secret"]
        # Configure Spotify API credentials
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id, client_secret))
        
        # Configure YT-DLP options
        self.ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [],
            "outtmpl": "./downloads/%(title)s.%(ext)s",
        }

        # Chrome options
        self.browserProfile = webdriver.ChromeOptions()
        self.browserProfile.add_argument("--headless=old")
        self.browserProfile.add_argument("--log-level=3")
        self.browserProfile.add_argument("--disable-notifications")
        self.browserProfile.add_argument("--disable-gpu")
        self.browserProfile.add_argument("window-size=1920,1080")
        self.browserProfile.add_experimental_option("excludeSwitches", ["enable-logging"])

    def searchAndRetrieveSpotifyLink(self, song_name):
        results = self.sp.search(q=song_name, limit=1, type='track')
        if results['tracks']['items']:
            track = results['tracks']['items'][0]
            return track['external_urls']['spotify']
        else:
            return None

    def executeChrome(self):
        service = Service(ChromeDriverManager().install())
        self.browser = webdriver.Chrome(service=service, options=self.browserProfile)

    def soloDownloader(self, song_input):
        if "https://open.spotify.com/track" not in song_input:
            song_input = self.searchAndRetrieveSpotifyLink(song_input)
            if not song_input:
                st.error("🚫 No results found. Please try a different song name.")
                return

        st.info(f"🔗 Found Spotify URL: {song_input}")
        self.islinkVerified = True

        self.executeChrome()
        self.browser.get(song_input)
        time.sleep(2)

        try:
            trackName = self.browser.find_element(By.TAG_NAME, "h1").text
        except Exception:
            st.error("❌ Could not extract the track name. The page structure might have changed.")
            self.browser.quit()
            return

        st.info("🔎 Searching for the song on YouTube...")
        self.browser.get(f"https://www.youtube.com/results?search_query={trackName}")
        try:
            trackLink = self.browser.find_element(By.XPATH, '//*[@id="dismissible"]/ytd-thumbnail/a').get_attribute("href")
        except Exception:
            st.error("❌ Could not find the track on YouTube. Please try a different song.")
            self.browser.quit()
            return

        st.info("⬇️ Downloading...")

        downloads_dir = "./downloads"
        os.makedirs(downloads_dir, exist_ok=True)

        try:
            self.ydl_opts["outtmpl"] = f"{downloads_dir}/%(title)s.%(ext)s"
            with YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([trackLink])
        except DownloadError as e:
            st.error(f"❌ Download failed: {e}")
            self.browser.quit()
            return

        matching_files = [file for file in os.listdir(downloads_dir) if trackName in file]
        if not matching_files:
            st.error("✔️ Download completed, but the file could not be found.")
            self.browser.quit()
            return

        webm_path = os.path.join(downloads_dir, matching_files[0])
        mp3_path = os.path.splitext(webm_path)[0] + ".mp3"
        self.convert_to_mp3(webm_path, mp3_path)

    def convert_to_mp3(self, webm_path, mp3_path):
        try:
            st.info("🔄 Converting to MP3...")
            command = f'ffmpeg -i "{webm_path}" -vn -ab 320k -ar 44100 -y "{mp3_path}"'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)

            if result.returncode == 0 and os.path.exists(mp3_path):
                st.success("🎉 Conversion successful! 🎵")
                with open(mp3_path, "rb") as file:
                    st.download_button(
                        label="💾 Download MP3",
                        data=file,
                        file_name=os.path.basename(mp3_path),
                        mime="audio/mpeg"
                    )
            else:
                st.error(f"❌ Conversion failed. Error: {result.stderr}")
        except Exception as e:
            st.error(f"❌ An error occurred during conversion: {e}")


# Streamlit app setup
# Streamlit app setup
st.set_page_config(page_title="Spotify Music Downloader", page_icon="🎵", layout="wide")
st.sidebar.title("Options")
option = st.sidebar.radio("Select an action (More to come!):", ["Download Song by Name/URL"])

st.markdown("<h1 style='text-align: center;'>🎵 Spotify Music Downloader</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Easily search and download songs from Spotify and YouTube!</p>", unsafe_allow_html=True)

if option == "Download Song by Name/URL":
    song_input = st.text_input("Enter the song name or Spotify URL:", placeholder="e.g., 'Blinding Lights'")
    if st.button("Download 🎧"):
        if song_input:
            with st.spinner("Preparing your download..."):
                downloader = SpotifyMusicDownloader()
                downloader.soloDownloader(song_input)
        else:
            st.warning("⚠️ Please enter a song name or URL.")
st.header("")
st.header("")

# Add an image at the bottom of the page
st.markdown("<hr style='border:1px solid #ddd;'>", unsafe_allow_html=True)  # Separator line
st.markdown("<p style='text-align: center;'>Thank you for using Spotify Music Downloader!</p>", unsafe_allow_html=True)
st.write("")
st.image("music-note.png", caption="Enjoy your free music :D 🎵", use_container_width=True)

for i in range(5):
    st.write("")
# CSS for footer styling
footer_style = """
<style>
.footer {
    flex-shrink: 0;
    color: #999999;
    text-align: center;
    margin-top: 2em;
    font-size: 0.8em;
}
</style>
"""

# Add footer content
st.markdown(footer_style, unsafe_allow_html=True)
st.markdown('<div class="footer">This app uses Spotify Web API to search and find the song URL and yt-dlp library to download them.</div>', unsafe_allow_html=True)
st.write("")
st.markdown('<div class="footer">A project by Kevin Chang</div>', unsafe_allow_html=True)