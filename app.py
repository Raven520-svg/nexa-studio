import streamlit as st
from pathlib import Path
from datetime import datetime
import tempfile
import os
import json

# Optional dependency used to communicate with Hugging Face Spaces
try:
    from gradio_client import Client, handle_file
except ImportError:
    Client = None
    handle_file = None


# ============================================================
# NEXA STUDIO
# AI MUSIC CREATION STUDIO
# ============================================================

st.set_page_config(
    page_title="NEXA STUDIO",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# COLORFUL FUTURISTIC DESIGN
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(circle at 10% 10%, rgba(110,70,255,.20), transparent 30%),
            radial-gradient(circle at 90% 20%, rgba(255,50,150,.18), transparent 30%),
            radial-gradient(circle at 50% 90%, rgba(0,220,255,.10), transparent 35%),
            #080A14;
        color: white;
    }

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, #0C1022 0%, #11142B 50%, #090B17 100%);
        border-right: 1px solid rgba(255,255,255,.08);
    }

    .nexa-title {
        font-size: 3.2rem;
        font-weight: 900;
        letter-spacing: 4px;
        background: linear-gradient(
            90deg,
            #8B5CF6,
            #EC4899,
            #22D3EE,
            #F59E0B
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 5px;
    }

    .nexa-subtitle {
        text-align: center;
        color: #B8BDD6;
        font-size: 1.05rem;
        margin-bottom: 30px;
    }

    .hero {
        padding: 45px 30px;
        border-radius: 28px;
        background:
            linear-gradient(
                135deg,
                rgba(124,58,237,.30),
                rgba(236,72,153,.20),
                rgba(14,165,233,.15)
            );
        border: 1px solid rgba(255,255,255,.10);
        text-align: center;
        margin-bottom: 25px;
    }

    .hero h1 {
        font-size: 3rem;
        margin-bottom: 10px;
    }

    .hero p {
        color: #D4D7E8;
        font-size: 1.1rem;
    }

    .card {
        padding: 25px;
        border-radius: 20px;
        background: rgba(255,255,255,.045);
        border: 1px solid rgba(255,255,255,.08);
        margin-bottom: 18px;
    }

    .step {
        display: inline-block;
        padding: 7px 14px;
        border-radius: 50px;
        background: linear-gradient(90deg,#7C3AED,#EC4899);
        color: white;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .status {
        padding: 15px;
        border-radius: 15px;
        background: rgba(34,211,238,.08);
        border: 1px solid rgba(34,211,238,.20);
        margin: 15px 0;
    }

    .small-muted {
        color: #969CB8;
        font-size: .88rem;
    }

    footer {
        text-align: center;
        color: #777C99;
        margin-top: 60px;
        padding: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "page": "🏠 Home",
    "lyrics": "",
    "style": "",
    "genre": "Afrofusion",
    "vocal": "Male",
    "mood": "Emotional",
    "artist": "None",
    "bpm": 100,
    "projects": [],
    "generated_audio": None,
    "generation_status": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HEARTMULA ENGINE
# ============================================================

HEARTMULA_SPACE = "projectlosangeles/HeartMuLa"


def get_heartmula_client():
    """Connect to the public HeartMuLa Hugging Face Space."""

    if Client is None:
        raise RuntimeError(
            "gradio_client is not installed. "
            "Add gradio_client to requirements.txt."
        )

    return Client(HEARTMULA_SPACE)


def inspect_heartmula_api(client):
    """
    Ask the Space what API endpoints are available.
    This prevents us from hard-coding an endpoint that may change.
    """

    try:
        return client.view_api(return_format="dict")
    except TypeError:
        return client.view_api()


def find_generation_endpoint(api_info):
    """
    Find a likely music-generation endpoint.

    We look for names such as:
    /generate
    /generate_music
    /predict
    """

    candidates = [
        "/generate",
        "/generate_music",
        "/generate_song",
        "/predict"
    ]

    if isinstance(api_info, dict):
        named_endpoints = api_info.get("named_endpoints", {})

        for candidate in candidates:
            if candidate in named_endpoints:
                return candidate

        # Fall back to first named endpoint
        if named_endpoints:
            return list(named_endpoints.keys())[0]

    return None


def generate_song(lyrics, tags):
    """
    Generate a song using the HeartMuLa Hugging Face Space.

    IMPORTANT:
    The exact Space endpoint can change, so this function first
    inspects the Space rather than assuming a fixed API.
    """

    client = get_heartmula_client()

    api_info = inspect_heartmula_api(client)

    endpoint = find_generation_endpoint(api_info)

    if not endpoint:
        raise RuntimeError(
            "Could not find a music generation endpoint on the "
            "HeartMuLa Space."
        )

    st.session_state.generation_status = (
        f"Connected to HeartMuLa. Endpoint: {endpoint}"
    )

    # --------------------------------------------------------
    # First attempt:
    # Most HeartMuLa Spaces expose lyrics + tags as inputs.
    # --------------------------------------------------------

    try:
        result = client.predict(
            lyrics,
            tags,
            api_name=endpoint
        )
        return result

    except Exception as first_error:

        # ----------------------------------------------------
        # Some Spaces expose named parameters instead.
        # Try a second call using keyword arguments.
        # ----------------------------------------------------

        try:
            result = client.predict(
                lyrics=lyrics,
                tags=tags,
                api_name=endpoint
            )
            return result

        except Exception as second_error:

            raise RuntimeError(
                "HeartMuLa was reached, but its current API "
                "input format did not match the NEXA connector.\n\n"
                f"First attempt: {first_error}\n\n"
                f"Second attempt: {second_error}"
            )


def extract_audio_result(result):
    """
    Try to find an audio filepath from the result returned by Gradio.
    """

    if result is None:
        return None

    # Direct filepath
    if isinstance(result, str):
        if result.endswith((".mp3", ".wav", ".flac", ".ogg", ".m4a")):
            return result

    # Tuple/list result
    if isinstance(result, (tuple, list)):
        for item in result:

            if isinstance(item, str):
                if item.endswith(
                    (".mp3", ".wav", ".flac", ".ogg", ".m4a")
                ):
                    return item

            if isinstance(item, dict):
                for key in ["path", "url", "name"]:
                    value = item.get(key)

                    if isinstance(value, str):
                        if value.endswith(
                            (".mp3", ".wav", ".flac", ".ogg", ".m4a")
                        ):
                            return value

    # Dictionary result
    if isinstance(result, dict):
        for key in ["path", "url", "audio", "output"]:

            value = result.get(key)

            if isinstance(value, str):
                return value

            if isinstance(value, dict):
                for subkey in ["path", "url", "name"]:
                    subvalue = value.get(subkey)

                    if isinstance(subvalue, str):
                        if subvalue.endswith(
                            (".mp3", ".wav", ".flac", ".ogg", ".m4a"
                        )):
                            return subvalue

    return None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="text-align:center;">
            <div style="font-size:2.5rem;">🎧</div>
            <h2>NEXA STUDIO</h2>
            <p class="small-muted">
                Step Into Your Next Sound
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    pages = [
        "🏠 Home",
        "✨ Create a Song",
        "🎙️ Recording Studio",
        "🥁 Beat Lab",
        "🎚️ Mix & Master",
        "🎵 My Songs",
        "🚀 Release Music",
        "⚙️ Settings"
    ]

    st.session_state.page = st.radio(
        "Studio",
        pages,
        index=pages.index(st.session_state.page)
    )

    st.divider()

    st.markdown(
        """
        <div class="small-muted">
        🎤 AI Song Creation<br>
        🥁 Beat Production<br>
        🎚️ Mixing & Mastering<br>
        🎵 Private Music Library
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# HOME
# ============================================================

if st.session_state.page == "🏠 Home":

    st.markdown(
        """
        <div class="hero">
            <div class="nexa-title">NEXA STUDIO</div>
            <div class="nexa-subtitle">
                Your private AI-powered music creation space
            </div>

            <h1>🎵 Turn Your Lyrics Into Music</h1>

            <p>
                Write your lyrics. Describe the sound.
                Build your next song.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="card">
                <h2>✍️ Lyrics</h2>
                <p>
                Start with your own words and structure
                your song into verses, chorus and bridge.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div class="card">
                <h2>🎤 AI Vocals</h2>
                <p>
                Generate a complete musical performance
                using the HeartMuLa engine.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            """
            <div class="card">
                <h2>🥁 Production</h2>
                <p>
                Describe your genre, mood, instruments,
                rhythm and overall sound.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("### 🚀 Start Creating")

    if st.button(
        "✨ CREATE A NEW SONG",
        type="primary",
        use_container_width=True
    ):
        st.session_state.page = "✨ Create a Song"
        st.rerun()


# ============================================================
# CREATE A SONG
# ============================================================

elif st.session_state.page == "✨ Create a Song":

    st.markdown(
        '<div class="nexa-title">CREATE A SONG</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="nexa-subtitle">'
        'Lyrics → Sound → AI Music'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # STEP 1
    # --------------------------------------------------------

    st.markdown(
        '<div class="step">STEP 1</div>',
        unsafe_allow_html=True
    )

    st.header("✍️ Write Your Lyrics")

    uploaded_lyrics = st.file_uploader(
        "Upload a .txt lyric file",
        type=["txt"]
    )

    if uploaded_lyrics:
        try:
            st.session_state.lyrics = uploaded_lyrics.read().decode(
                "utf-8"
            )
        except Exception:
            st.error("Could not read the lyric file.")

    lyrics = st.text_area(
        "Lyrics",
        value=st.session_state.lyrics,
        height=300,
        placeholder="""[Intro]

Yeah yeah...

[Verse]
Write your verse here...

[Chorus]
Write your chorus here...

[Verse]
Write your second verse...

[Bridge]
Write your bridge...

[Outro]
Write your outro...""",
        key="lyrics_box"
    )

    st.session_state.lyrics = lyrics

    st.caption(
        f"{len(lyrics)} characters"
    )

    # --------------------------------------------------------
    # STEP 2
    # --------------------------------------------------------

    st.markdown(
        '<div class="step">STEP 2</div>',
        unsafe_allow_html=True
    )

    st.header("🎧 Describe Your Sound")

    st.write(
        "Tell NEXA STUDIO how you want the song to feel."
    )

    style = st.text_area(
        "Sound description",
        value=st.session_state.style,
        height=130,
        placeholder=(
            "Example: Emotional Nigerian Afrofusion with "
            "deep bass, smooth drums, atmospheric synths, "
            "melodic vocals and a catchy chorus."
        )
    )

    st.session_state.style = style

    c1, c2 = st.columns(2)

    with c1:

        genre = st.selectbox(
            "Genre",
            [
                "Afrofusion",
                "Afrobeat",
                "Afropop",
                "R&B",
                "Amapiano",
                "Pop",
                "Hip-Hop",
                "Soul",
                "Reggae",
                "Dancehall",
                "Other"
            ],
            index=0
        )

        mood = st.selectbox(
            "Mood",
            [
                "Emotional",
                "Chill",
                "Romantic",
                "Dark",
                "Happy",
                "Energetic",
                "Melancholic",
                "Spiritual",
                "Confident",
                "Dreamy"
            ]
        )

    with c2:

        vocal = st.selectbox(
            "Vocal style",
            [
                "Male",
                "Female",
                "Soft",
                "Powerful",
                "Melodic",
                "Soulful"
            ]
        )

        bpm = st.slider(
            "Approximate BPM",
            min_value=60,
            max_value=180,
            value=100,
            step=1
        )

    st.session_state.genre = genre
    st.session_state.mood = mood
    st.session_state.vocal = vocal
    st.session_state.bpm = bpm

    artist = st.selectbox(
        "🎨 Artist inspiration",
        [
            "None",
            "Omah Lay",
            "Burna Boy",
            "Tems",
            "Wizkid",
            "Rema",
            "Asake",
            "Fireboy DML",
            "Ayra Starr",
            "Davido"
        ]
    )

    st.session_state.artist = artist

    st.info(
        "Artist inspiration is treated as a broad musical reference. "
        "NEXA STUDIO will not intentionally copy an artist's exact "
        "voice, recording or melody."
    )

    # --------------------------------------------------------
    # BUILD TAGS
    # --------------------------------------------------------

    tags = (
        f"{genre},"
        f"{mood},"
        f"{vocal} vocals,"
        f"{bpm} BPM,"
        f"{style}"
    )

    if artist != "None":
        tags += (
            f", contemporary Nigerian sound"
        )

    # --------------------------------------------------------
    # STEP 3
    # --------------------------------------------------------

    st.markdown(
        '<div class="step">STEP 3</div>',
        unsafe_allow_html=True
    )

    st.header("🎵 Generate Your Song")

    with st.expander("View HeartMuLa generation tags"):
        st.code(tags)

    if not lyrics.strip():
        st.warning(
            "Enter your lyrics before generating."
        )

    elif len(lyrics) < 20:
        st.warning(
            "Your lyrics are very short. Add more lyrics "
            "for a more complete song."
        )

    else:

        generate = st.button(
            "🔥 GENERATE SONG",
            type="primary",
            use_container_width=True
        )

        if generate:

            with st.spinner(
                "Connecting to HeartMuLa and generating your song..."
            ):

                try:

                    result = generate_song(
                        lyrics=lyrics,
                        tags=tags
                    )

                    audio_path = extract_audio_result(result)

                    if audio_path:

                        st.session_state.generated_audio = audio_path
                        st.session_state.generation_status = (
                            "Song generated successfully."
                        )

                        # Save project metadata
                        project = {
                            "title": "NEXA Song",
                            "lyrics": lyrics,
                            "tags": tags,
                            "genre": genre,
                            "mood": mood,
                            "vocal": vocal,
                            "bpm": bpm,
                            "created_at": datetime.now().isoformat(),
                            "audio": audio_path
                        }

                        st.session_state.projects.append(
                            project
                        )

                        st.success(
                            "🎉 Your song has been generated!"
                        )

                    else:

                        st.error(
                            "HeartMuLa returned a result, "
                            "but NEXA STUDIO could not identify "
                            "the audio file."
                        )

                        with st.expander(
                            "Technical result"
                        ):
                            st.write(result)

                except Exception as e:

                    st.error(
                        "The HeartMuLa connection did not complete."
                    )

                    st.warning(
                        "This does not necessarily mean the model "
                        "failed. The Hugging Face Space may have "
                        "changed its API endpoint or input format."
                    )

                    with st.expander(
                        "Technical details"
                    ):
                        st.exception(e)

    # --------------------------------------------------------
    # AUDIO PLAYER
    # --------------------------------------------------------

    if st.session_state.generated_audio:

        st.divider()

        st.header("🎧 Your Generated Song")

        audio_path = st.session_state.generated_audio

        try:

            st.audio(
                audio_path,
                format="audio/mpeg"
            )

            # Download
            if os.path.exists(audio_path):

                with open(audio_path, "rb") as audio_file:

                    st.download_button(
                        "⬇️ DOWNLOAD SONG",
                        data=audio_file.read(),
                        file_name="nexa_song.mp3",
                        mime="audio/mpeg",
                        use_container_width=True
                    )

        except Exception as e:

            st.error(
                f"Could not play the generated audio: {e}"
            )


# ============================================================
# RECORDING STUDIO
# ============================================================

elif st.session_state.page == "🎙️ Recording Studio":

    st.markdown(
        '<div class="nexa-title">RECORDING STUDIO</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="nexa-subtitle">'
        'Record and prepare your vocals'
        '</div>',
        unsafe_allow_html=True
    )

    st.header("🎙️ Upload Your Vocal")

    vocal_file = st.file_uploader(
        "Upload a vocal recording",
        type=["wav", "mp3", "m4a", "ogg"]
    )

    if vocal_file:

        st.audio(vocal_file)

        st.success(
            "Vocal uploaded successfully."
        )

    st.divider()

    st.subheader("🎚️ Vocal Processing")

    c1, c2 = st.columns(2)

    with c1:

        noise_reduction = st.slider(
            "Noise Reduction",
            0,
            100,
            50
        )

        pitch_correction = st.slider(
            "Pitch Correction",
            0,
            100,
            30
        )

    with c2:

        reverb = st.slider(
            "Reverb",
            0,
            100,
            20
        )

        vocal_volume = st.slider(
            "Vocal Volume",
            0,
            100,
            80
        )

    st.info(
        "The recording controls are ready. "
        "Advanced vocal processing will be connected "
        "to the audio-processing engine in the next stage."
    )


# ============================================================
# BEAT LAB
# ============================================================

elif st.session_state.page == "🥁 Beat Lab":

    st.markdown(
        '<div class="nexa-title">BEAT LAB</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="nexa-subtitle">'
        'Build the instrumental foundation'
        '</div>',
        unsafe_allow_html=True
    )

    beat_style = st.selectbox(
        "Beat style",
        [
            "Afrobeat",
            "Afrofusion",
            "Amapiano",
            "R&B",
            "Hip-Hop",
            "Dancehall",
            "Pop",
            "Ambient"
        ]
    )

    beat_bpm = st.slider(
        "BPM",
        60,
        180,
        100
    )

    instruments = st.multiselect(
        "Instruments",
        [
            "Drums",
            "Bass",
            "Piano",
            "Guitar",
            "Synth",
            "Strings",
            "Percussion",
            "Pads"
        ],
        default=[
            "Drums",
            "Bass",
            "Percussion"
        ]
    )

    st.write(
        f"**Selected:** {beat_style} • {beat_bpm} BPM"
    )

    st.write(
        " • ".join(instruments)
        if instruments
        else "No instruments selected."
    )

    if st.button(
        "🥁 GENERATE BEAT",
        type="primary",
        use_container_width=True
    ):

        st.info(
            "Beat generation will use the same AI music "
            "engine architecture. Full instrumental-only "
            "generation is being connected separately."
        )


# ============================================================
# MIX & MASTER
# ============================================================

elif st.session_state.page == "🎚️ Mix & Master":

    st.markdown(
        '<div class="nexa-title">MIX & MASTER</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="nexa-subtitle">'
        'Shape your final sound'
        '</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("🎚️ Mix")

        volume = st.slider(
            "Volume",
            0,
            100,
            80
        )

        bass = st.slider(
            "Bass",
            -12,
            12,
            0
        )

        mid = st.slider(
            "Mid",
            -12,
            12,
            0
        )

        treble = st.slider(
            "Treble",
            -12,
            12,
            0
        )

    with col2:

        st.subheader("✨ Effects")

        compression = st.slider(
            "Compression",
            0,
            100,
            40
        )

        reverb_mix = st.slider(
            "Reverb",
            0,
            100,
            20
        )

        stereo_width = st.slider(
            "Stereo Width",
            0,
            200,
            100
        )

        mastering = st.selectbox(
            "Mastering preset",
            [
                "Clean",
                "Streaming",
                "Loud",
                "Warm",
                "Afrobeats"
            ]
        )

    st.info(
        "Mixing and mastering controls are prepared. "
        "Audio DSP processing will be connected in the "
        "next production stage."
    )


# ============================================================
# MY SONGS
# ============================================================

elif st.session_state.page == "🎵 My Songs":

    st.markdown(
        '<div class="nexa-title">MY SONGS</div>',
        unsafe_allow_html=True
    )

    if not st.session_state.projects:

        st.info(
            "You haven't created any songs in this session yet."
        )

    else:

        for i, project in enumerate(
            reversed(st.session_state.projects)
        ):

            with st.expander(
                f"🎵 {project.get('title', 'NEXA Song')} "
                f"— {project.get('genre', '')}"
            ):

                st.write(
                    f"**Mood:** {project.get('mood', '')}"
                )

                st.write(
                    f"**Vocal:** {project.get('vocal', '')}"
                )

                st.write(
                    f"**BPM:** {project.get('bpm', '')}"
                )

                st.text_area(
                    "Lyrics",
                    project.get("lyrics", ""),
                    height=180,
                    key=f"song_lyrics_{i}"
                )

                audio = project.get("audio")

                if audio and os.path.exists(audio):

                    st.audio(audio)

                    with open(audio, "rb") as f:

                        st.download_button(
                            "⬇️ Download",
                            f.read(),
                            file_name=f"nexa_song_{i+1}.mp3",
                            mime="audio/mpeg",
                            key=f"download_{i}"
                        )


# ============================================================
# RELEASE MUSIC
# ============================================================

elif st.session_state.page == "🚀 Release Music":

    st.markdown(
        '<div class="nexa-title">RELEASE MUSIC</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="nexa-subtitle">'
        'Prepare your song for distribution'
        '</div>',
        unsafe_allow_html=True
    )

    artist_name = st.text_input(
        "Artist name"
    )

    song_title = st.text_input(
        "Song title"
    )

    release_date = st.date_input(
        "Release date"
    )

    cover = st.file_uploader(
        "Cover artwork",
        type=["png", "jpg", "jpeg"]
    )

    platforms = st.multiselect(
        "Platforms",
        [
            "Spotify",
            "Apple Music",
            "YouTube Music",
            "Audiomack",
            "Boomplay",
            "Amazon Music",
            "Deezer",
            "TikTok"
        ]
    )

    rights = st.checkbox(
        "I confirm that I have the rights to distribute this music."
    )

    if st.button(
        "🚀 PREPARE RELEASE",
        type="primary",
        use_container_width=True
    ):

        if not artist_name or not song_title:

            st.warning(
                "Enter your artist name and song title."
            )

        elif not rights:

            st.warning(
                "Confirm your music rights first."
            )

        else:

            st.success(
                "Release information prepared."
            )

            st.info(
                "Direct distribution will be added later "
                "through a music distributor. Spotify and "
                "other major platforms generally receive "
                "independent releases through distributors."
            )


# ============================================================
# SETTINGS
# ============================================================

elif st.session_state.page == "⚙️ Settings":

    st.markdown(
        '<div class="nexa-title">SETTINGS</div>',
        unsafe_allow_html=True
    )

    theme = st.selectbox(
        "Studio appearance",
        [
            "NEXA Aurora",
            "Midnight",
            "Cosmic",
            "Electric"
        ]
    )

    st.checkbox(
        "Private studio mode",
        value=True,
        disabled=True
    )

    st.info(
        "NEXA STUDIO is currently designed as a private "
        "personal workspace. Songs are stored only in the "
        "current Streamlit session unless persistent storage "
        "is added."
    )

    st.divider()

    st.subheader("🎵 Music Engine")

    st.write(
        "Current engine: HeartMuLa via Hugging Face Space"
    )

    st.write(
        f"Space: `{HEARTMULA_SPACE}`"
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <footer>
        🎧 <strong>NEXA STUDIO</strong><br>
        Step Into Your Next Sound
    </footer>
    """,
    unsafe_allow_html=True
)
