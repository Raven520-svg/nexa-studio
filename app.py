import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="NEXA STUDIO",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- COLORS & DESIGN ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #10172A, #191333, #10172A);
    color: #F8FAFC;
}
section[data-testid="stSidebar"] {
    background: #17172D;
    border-right: 1px solid #45336B;
}
h1, h2, h3 { color: #FFFFFF !important; }
p, label, .stMarkdown { color: #E2E8F0; }
.hero {
    padding: 35px 25px;
    border-radius: 22px;
    background: linear-gradient(115deg, #7138C8, #B52D91, #263E9C);
    margin-bottom: 22px;
}
.hero h1 { font-size: 42px; color: white !important; }
.hero p { font-size: 17px; color: #F5EFFF; }
.tile {
    background: #20203D;
    border: 1px solid #453B70;
    padding: 20px;
    border-radius: 17px;
    min-height: 125px;
    margin-bottom: 12px;
}
.tile h3 { margin: 0 0 8px 0; }
.small { color: #BFC5E5; font-size: 14px; }
.stButton > button {
    background: linear-gradient(90deg, #8B5CF6, #D946A6);
    color: white;
    border: 0;
    border-radius: 12px;
    min-height: 44px;
    font-weight: bold;
}
.stButton > button:hover {
    border: 1px solid #FFFFFF;
    color: white;
}
.stTextArea textarea, .stTextInput input {
    background: #171A32 !important;
    color: white !important;
    border: 1px solid #66518E !important;
    border-radius: 10px !important;
}
div[data-baseweb="select"] > div {
    background: #171A32;
    color: white;
    border-color: #66518E;
}
hr { border-color: #40375F; }
</style>
""", unsafe_allow_html=True)

# ---------- SESSION DATA ----------
if "lyrics" not in st.session_state:
    st.session_state.lyrics = ""
if "style" not in st.session_state:
    st.session_state.style = ""
if "projects" not in st.session_state:
    st.session_state.projects = []
if "step" not in st.session_state:
    st.session_state.step = 1

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("# 🎧 NEXA")
    st.caption("YOUR PRIVATE AI MUSIC STUDIO")
    st.markdown("---")

    page = st.radio(
        "YOUR WORKSPACE",
        [
            "🏠 Home",
            "✨ Create a Song",
            "🎙️ Recording Studio",
            "🥁 Beat Lab",
            "🎚️ Mix & Master",
            "🎵 My Songs",
            "🚀 Release Music",
            "⚙️ Settings"
        ],
        label_visibility="visible"
    )
    st.markdown("---")
    st.markdown("💜 **PRIVATE WORKSPACE**")
    st.caption("Your music. Your creativity. Your next era.")

# ---------- HOME ----------
if page == "🏠 Home":
    st.markdown("""
    <div class="hero">
        <h1>Make the music in your mind. 🎶</h1>
        <p>Write it. Sing it. Produce it. Make it yours.</p>
        <p>Welcome to your personal AI music studio.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("✨ CREATE A NEW SONG", use_container_width=True):
        st.session_state.step = 1
        st.session_state.page_request = "✨ Create a Song"
        st.rerun()

    st.markdown("## 🎨 Your creative studio")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="tile">
        <h3>✨ AI Song Maker</h3>
        <div class="small">Turn your lyrics into music.</div>
        </div>
        <div class="tile">
        <h3>🎙️ Recording Studio</h3>
        <div class="small">Record and improve your vocals.</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="tile">
        <h3>🥁 Beat Lab</h3>
        <div class="small">Explore beats, instruments and rhythm.</div>
        </div>
        <div class="tile">
        <h3>🎚️ Mix & Master</h3>
        <div class="small">Polish your music and sound.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("## 🎵 Your recent projects")
    if st.session_state.projects:
        for project in st.session_state.projects:
            st.markdown(
                f"<div class='tile'><h3>🎧 {project['title']}</h3>"
                f"<div class='small'>{project['genre']}</div></div>",
                unsafe_allow_html=True
            )
    else:
        st.info("Your songs will appear here after you save your first project.")

# ---------- CREATE SONG ----------
elif page == "✨ Create a Song":
    st.markdown("# ✨ Create your song")
    st.caption("Start with your lyrics. Choose your sound afterward.")

    step = st.session_state.step

    st.progress(0.33 if step == 1 else 0.66 if step == 2 else 1.0)
    st.caption(f"STEP {step} OF 3")

    if step == 1:
        st.markdown("## 📝 Step 1 — Your lyrics")
        st.write("Paste your lyrics below or upload a text file.")

        uploaded = st.file_uploader(
            "Upload lyrics (.txt)",
            type=["txt"]
        )
        if uploaded:
            try:
                st.session_state.lyrics = uploaded.getvalue().decode("utf-8")
            except UnicodeDecodeError:
                st.error("Please upload a UTF-8 text file.")

        st.session_state.lyrics = st.text_area(
            "YOUR LYRICS",
            value=st.session_state.lyrics,
            height=280,
            placeholder="""[Verse 1]
Write your first verse here...

[Chorus]
Write your chorus here...

[Verse 2]
Continue your story here...""",
            key="lyrics_editor"
        )

        st.caption(f"Characters: {len(st.session_state.lyrics)}")

        if st.button("CONTINUE TO SOUND →", use_container_width=True):
            if not st.session_state.lyrics.strip():
                st.warning("Please enter your lyrics first.")
            else:
                st.session_state.step = 2
                st.rerun()

    elif step == 2:
        st.markdown("## 🎨 Step 2 — Describe your sound")
        st.write("Tell the AI how you want your lyrics to sound.")

        st.markdown("### 🎼 Your music description")
        st.session_state.style = st.text_area(
            "DESCRIBE YOUR MUSIC",
            value=st.session_state.style,
            height=150,
            placeholder="Example: Slow emotional Afro-fusion, deep male vocals, soft piano, gentle drums, atmospheric background and a catchy chorus."
        )

        st.markdown("### 🎭 Choose your genre")
        genre = st.selectbox(
            "GENRE",
            [
                "Afrobeat", "Afro-fusion", "Afropop",
                "R&B", "Hip-hop", "Rap", "Gospel",
                "Pop", "Dancehall", "Reggae", "Amapiano",
                "Soul", "Jazz", "Rock", "Country",
                "Electronic", "Classical", "Other"
            ]
        )

        st.markdown("### 🎤 Voice")
        voice = st.selectbox(
            "VOCAL STYLE",
            [
                "AI male vocals",
                "AI female vocals",
                "My own recorded vocals",
                "Instrumental only"
            ]
        )

        st.markdown("### 🌈 Mood")
        mood = st.selectbox(
            "MOOD",
            [
                "Emotional", "Romantic", "Happy",
                "Sad", "Chill", "Energetic",
                "Spiritual", "Dark", "Motivational",
                "Aggressive", "Dreamy"
            ]
        )

        st.markdown("### 🔎 Artist inspiration")
        st.caption("Search for an artist to describe the musical qualities you like.")
        artists = [
            "Omah Lay", "Burna Boy", "Wizkid", "Tems",
            "Davido", "Asake", "Rema", "Ayra Starr",
            "SZA", "Drake", "Bruno Mars", "Adele",
            "Chris Brown", "Other"
        ]
        artist_search = st.text_input("SEARCH ARTISTS")
        matches = [
            a for a in artists
            if artist_search.lower() in a.lower()
        ] if artist_search else artists

        artist = st.selectbox(
            "ARTIST INSPIRATION",
            ["None"] + matches
        )

        st.caption(
            "We'll use general musical characteristics as inspiration, "
            "not copy an artist's exact melody, recording, or signature voice."
        )

        st.markdown("### ⏱️ Song length")
        duration = st.select_slider(
            "TARGET LENGTH",
            options=["1 min", "2 min", "3 min", "4 min", "5 min"],
            value="3 min"
        )

        st.session_state.song_settings = {
            "genre": genre,
            "voice": voice,
            "mood": mood,
            "artist": artist,
            "duration": duration
        }

        a, b = st.columns(2)
        with a:
            if st.button("← BACK TO LYRICS", use_container_width=True):
                st.session_state.step = 1
                st.rerun()
        with b:
            if st.button("REVIEW SONG →", use_container_width=True):
                if not st.session_state.style.strip():
                    st.warning("Please describe the sound you want.")
                else:
                    st.session_state.step = 3
                    st.rerun()

    else:
        st.markdown("## 🎧 Step 3 — Review your song")
        settings = st.session_state.get("song_settings", {})

        st.markdown("### 📝 Your lyrics")
        st.text_area(
            "LYRICS PREVIEW",
            value=st.session_state.lyrics,
            height=180,
            disabled=True
        )

        st.markdown("### 🎨 Your production settings")
        st.write("**Sound:**", st.session_state.style)
        for key, value in settings.items():
            st.write(f"**{key.title()}:** {value}")

        st.info(
            "The song-generation engine isn't connected yet. "
            "This version saves your creative settings so we can "
            "connect a real AI music service next."
        )

        title = st.text_input(
            "NAME YOUR SONG",
            placeholder="e.g. Midnight Feelings"
        )

        a, b = st.columns(2)
        with a:
            if st.button("← EDIT SOUND", use_container_width=True):
                st.session_state.step = 2
                st.rerun()
        with b:
            if st.button("💾 SAVE PROJECT", use_container_width=True):
                if not title.strip():
                    st.warning("Please enter a song title.")
                else:
                    st.session_state.projects.append({
                        "title": title,
                        "lyrics": st.session_state.lyrics,
                        "style": st.session_state.style,
                        "genre": settings.get("genre", "Other"),
                        "settings": settings
                    })
                    st.session_state.step = 1
                    st.session_state.lyrics = ""
                    st.session_state.style = ""
                    st.success("Your project has been saved in this session!")

# ---------- RECORDING ----------
elif page == "🎙️ Recording Studio":
    st.markdown("# 🎙️ Recording Studio")
    st.write("Record your own voice or upload an existing recording.")
    st.markdown("### 🎤 Upload vocals")
    vocal = st.file_uploader(
        "Choose an audio file",
        type=["wav", "mp3", "m4a", "ogg"]
    )
    if vocal:
        st.audio(vocal)
        st.success("Audio loaded for preview.")
    st.markdown("### 🎛️ Vocal settings")
    st.slider("Vocal volume", 0, 100, 80)
    st.slider("Noise reduction", 0, 100, 40)
    st.slider("Reverb", 0, 100, 20)
    st.slider("Pitch correction", 0, 100, 0)
    st.info("Recording and audio processing will be connected in a later version.")

# ---------- BEAT LAB ----------
elif page == "🥁 Beat Lab":
    st.markdown("# 🥁 Beat Lab")
    st.write("Plan the rhythm and instrumentation for your music.")
    beat = st.selectbox(
        "BEAT STYLE",
        ["Afrobeat groove", "Afro-fusion", "Amapiano",
         "Trap", "R&B", "Pop", "Gospel", "Dancehall"]
    )
    bpm = st.slider("TEMPO (BPM)", 50, 200, 105)
    instruments = st.multiselect(
        "CHOOSE INSTRUMENTS",
        ["Drums", "Piano", "Bass", "Guitar",
         "Synth", "Strings", "Percussion", "Organ"],
        default=["Drums", "Bass", "Piano"]
    )
    st.write("**Your beat:**", beat)
    st.write("**Tempo:**", bpm, "BPM")
    st.write("**Instruments:**", ", ".join(instruments))
    st.info("Beat generation and a playable instrument library are planned for the next version.")

# ---------- MIX & MASTER ----------
elif page == "🎚️ Mix & Master":
    st.markdown("# 🎚️ Mix & Master")
    st.write("Set up how you want your final song to sound.")
    st.slider("Vocal level", 0, 100, 80)
    st.slider("Instrumental level", 0, 100, 75)
    st.slider("Bass", 0, 100, 50)
    st.slider("Treble", 0, 100, 50)
    st.slider("Compression", 0, 100, 35)
    st.slider("Stereo width", 0, 100, 50)
    st.selectbox("MASTERING PRESET", [
        "Balanced", "Warm", "Punchy",
        "Bright", "Deep bass", "Vocal focus"
    ])
    st.info("These are planning controls for now. Actual audio mastering requires a processing engine.")

# ---------- MY SONGS ----------
elif page == "🎵 My Songs":
    st.markdown("# 🎵 My Songs")
    st.write("Your private creative library.")
    if not st.session_state.projects:
        st.info("You haven't saved any projects in this session yet.")
    else:
        for i, project in enumerate(st.session_state.projects):
            with st.expander("🎧 " + project["title"]):
                st.write("**Genre:**", project["genre"])
                st.write("**Sound:**", project["style"])
                st.text_area(
                    "Lyrics",
                    value=project["lyrics"],
                    height=150,
                    key=f"saved_{i}"
                )
                st.download_button(
                    "⬇️ Download lyrics",
                    data=project["lyrics"],
                    file_name=project["title"] + ".txt",
                    mime="text/plain",
                    key=f"download_{i}"
                )

# ---------- RELEASE ----------
elif page == "🚀 Release Music":
    st.markdown("# 🚀 Release My Music")
    st.write("Prepare your song for future distribution.")
    st.text_input("ARTIST NAME")
    st.text_input("SONG TITLE")
    st.text_input("RELEASE DATE")
    st.file_uploader("UPLOAD COVER ART", type=["png", "jpg", "jpeg"])
    st.multiselect(
        "PLATFORMS",
        ["Spotify", "YouTube Music", "Audiomack",
         "Apple Music", "Boomplay", "Deezer"]
    )
    rights = st.checkbox("I confirm I have the rights to distribute this music.")
    st.button("PREPARE RELEASE", disabled=not rights)
    st.caption("Distribution is not connected yet. No music will be sent to any platform.")

# ---------- SETTINGS ----------
elif page == "⚙️ Settings":
    st.markdown("# ⚙️ Settings")
    st.write("Personalize your workspace.")
    st.selectbox("APP THEME", ["Colorful midnight", "Purple dream", "Ocean blue"])
    st.checkbox("Keep my projects private", value=True, disabled=True)
    st.info("Your projects are currently saved in your browser session only. Persistent private storage will be added later.")

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#A8A8C7;'>"
    "NEXA STUDIO · CREATE YOUR NEXT ERA 🎧"
    "</p>",
    unsafe_allow_html=True
)

