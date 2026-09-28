import streamlit as st
import os
import re
import json
import tempfile
from pathlib import Path
from datetime import datetime

# =========================================================
# NEXA STUDIO
# AI MUSIC CREATION STUDIO
# =========================================================

st.set_page_config(
    page_title="NEXA STUDIO",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# HEARTMULA CONNECTION
# =========================================================

try:
    from gradio_client import Client
    GRADIO_AVAILABLE = True
except Exception:
    GRADIO_AVAILABLE = False


# Current HeartMuLa ZeroGPU Space
HEARTMULA_SPACE = "Thebeachingwaulrus/heartmula"

# The current Space exposes the generation function with
# these six inputs:
#
# lyrics
# tags
# max_duration_seconds
# temperature
# topk
# cfg_scale
#
# We intentionally do NOT try to discover a fake /generate
# endpoint.


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "page": "Home",
    "lyrics": "",
    "sound_description": "",
    "genre": "Afrobeat",
    "mood": "Energetic",
    "vocal_style": "Male",
    "bpm": 100,
    "artist": "None",
    "generated_audio": None,
    "generated_title": "",
    "generation_message": "",
    "projects": [],
    "recording": None,
    "beat_file": None,
    "master_file": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
<style>

.stApp {
    background:
        radial-gradient(circle at 10% 10%, rgba(255,0,120,0.12), transparent 28%),
        radial-gradient(circle at 90% 20%, rgba(0,200,255,0.12), transparent 30%),
        radial-gradient(circle at 50% 90%, rgba(120,0,255,0.10), transparent 30%),
        #08090f;
    color: #ffffff;
}

section[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, #10121d 0%, #090a10 100%);
    border-right: 1px solid rgba(255,255,255,0.08);
}

.nexa-logo {
    font-size: 32px;
    font-weight: 900;
    letter-spacing: 3px;
    background: linear-gradient(90deg,#ff2ea6,#7c5cff,#00d9ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.nexa-subtitle {
    color: #9ea4b7;
    font-size: 13px;
    margin-bottom: 25px;
}

.hero {
    padding: 45px 30px;
    border-radius: 28px;
    background:
        linear-gradient(
            135deg,
            rgba(255,46,166,0.18),
            rgba(124,92,255,0.16),
            rgba(0,217,255,0.12)
        );
    border: 1px solid rgba(255,255,255,0.09);
    margin-bottom: 25px;
}

.hero h1 {
    font-size: 52px;
    line-height: 1.0;
    margin-bottom: 15px;
}

.hero p {
    color: #c2c6d4;
    font-size: 17px;
    max-width: 750px;
}

.card {
    background: rgba(20,22,34,0.78);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 18px;
}

.card h3 {
    margin-top: 0;
}

.feature-card {
    min-height: 170px;
}

.gradient-text {
    background: linear-gradient(90deg,#ff2ea6,#7c5cff,#00d9ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.status-good {
    padding: 12px 16px;
    border-radius: 12px;
    background: rgba(0,220,140,0.10);
    border: 1px solid rgba(0,220,140,0.25);
    color: #8fffd0;
}

.status-warning {
    padding: 12px 16px;
    border-radius: 12px;
    background: rgba(255,180,0,0.10);
    border: 1px solid rgba(255,180,0,0.25);
    color: #ffd66b;
}

.small-muted {
    color: #8c92a6;
    font-size: 13px;
}

div.stButton > button {
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.12);
    min-height: 45px;
    font-weight: 700;
}

div.stButton > button:hover {
    border-color: rgba(255,46,166,0.65);
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# HELPERS
# =========================================================

def go(page):
    st.session_state.page = page
    st.rerun()


def clean_tags(text):
    """
    Convert the user's natural-language description into
    useful HeartMuLa-style comma-separated tags.
    """

    text = text.lower().strip()

    replacements = {
        "afrobeats": "afrobeat",
        "afro beat": "afrobeat",
        "afro fusion": "afrofusion",
        "afro-fusion": "afrofusion",
        "rnb": "r&b",
        "r&b": "r&b",
        "hip hop": "hip-hop",
        "hiphop": "hip-hop",
        "male voice": "male vocals",
        "female voice": "female vocals",
        "sad": "emotional",
        "happy": "uplifting",
        "slow": "slow tempo",
        "fast": "upbeat",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def build_heartmula_tags(
    genre,
    mood,
    vocal_style,
    bpm,
    sound_description,
    artist,
):
    tags = []

    # Genre
    if genre:
        tags.append(genre.lower())

    # Mood
    if mood:
        tags.append(mood.lower())

    # Vocal
    if vocal_style:
        tags.append(f"{vocal_style.lower()} vocals")

    # BPM
    if bpm:
        if bpm < 80:
            tags.append("slow tempo")
        elif bpm < 105:
            tags.append("mid tempo")
        elif bpm < 125:
            tags.append("upbeat")
        else:
            tags.append("fast tempo")

    # Artist inspiration is converted to broad characteristics.
    # We do NOT ask the model to copy an artist's exact voice,
    # recording, melody, or song.
    artist_styles = {
        "Omah Lay": "melodic afrobeat, emotional, atmospheric",
        "Burna Boy": "afrofusion, rhythmic, warm bass",
        "Tems": "soulful afrobeat, atmospheric, smooth",
        "Wizkid": "afrobeats, melodic, smooth groove",
        "Rema": "modern afrobeat, energetic, catchy",
        "Davido": "afrobeats, energetic, rhythmic",
        "Asake": "afrobeats, amapiano influence, percussive",
        "Fireboy DML": "melodic afrobeat, emotional, smooth",
        "None": "",
    }

    if artist in artist_styles:
        style = artist_styles[artist]
        if style:
            tags.extend([x.strip() for x in style.split(",")])

    # Natural-language description
    if sound_description:
        description = clean_tags(sound_description)

        # Only keep useful musical words.
        useful_words = [
            "hot",
            "lively",
            "dark",
            "soft",
            "smooth",
            "melodic",
            "emotional",
            "romantic",
            "energetic",
            "dance",
            "club",
            "acoustic",
            "piano",
            "guitar",
            "bass",
            "drums",
            "synth",
            "synthesizer",
            "percussion",
            "atmospheric",
            "dreamy",
            "cinematic",
            "street",
            "urban",
            "spiritual",
            "soulful",
            "catchy",
            "uplifting",
        ]

        for word in useful_words:
            if word in description:
                tags.append(word)

    # Remove duplicates while preserving order
    final_tags = []

    for tag in tags:
        tag = tag.strip()

        if not tag:
            continue

        if tag not in final_tags:
            final_tags.append(tag)

    return ",".join(final_tags)


def normalize_audio_result(result):
    """
    Gradio can return a filepath, URL, dictionary, tuple, or list
    depending on its version. Try to locate the audio output.
    """

    if result is None:
        return None

    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        for key in ["path", "url", "value"]:
            if key in result and result[key]:
                return normalize_audio_result(result[key])

    if isinstance(result, (list, tuple)):
        for item in result:
            found = normalize_audio_result(item)
            if found:
                return found

    return None


def download_remote_file(path_or_url):
    """
    Download a generated file when Gradio gives us a remote URL.
    """

    if not path_or_url:
        return None

    if os.path.exists(path_or_url):
        return path_or_url

    try:
        import requests

        response = requests.get(path_or_url, timeout=180)
        response.raise_for_status()

        suffix = ".wav"

        if ".mp3" in path_or_url.lower():
            suffix = ".mp3"

        temp = tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False
        )

        temp.write(response.content)
        temp.close()

        return temp.name

    except Exception:
        return None


def generate_with_heartmula(
    lyrics,
    tags,
    duration,
    temperature,
    topk,
    cfg_scale,
):
    """
    Connect to the current HeartMuLa ZeroGPU Space.

    IMPORTANT:
    We use the actual six inputs exposed by the current Space.
    """

    if not GRADIO_AVAILABLE:
        raise RuntimeError(
            "gradio_client is not installed. "
            "Add gradio_client to requirements.txt."
        )

    if not lyrics.strip():
        raise ValueError("Please enter your lyrics.")

    if not tags.strip():
        raise ValueError("Please provide a sound/style description.")

    # Connect to the CURRENT working Space.
    client = Client(HEARTMULA_SPACE)

    # Exact current function exposed by the Space.
    result = client.predict(
        lyrics,
        tags,
        int(duration),
        float(temperature),
        int(topk),
        float(cfg_scale),
        api_name="/generate_music",
    )

    audio_path = normalize_audio_result(result)

    if not audio_path:
        raise RuntimeError(
            "HeartMuLa completed the request but did not return "
            "an audio file."
        )

    # Download remote result if necessary.
    local_path = download_remote_file(audio_path)

    if local_path:
        return local_path

    return audio_path


def save_project(title, lyrics, tags, audio_path):
    project = {
        "title": title,
        "lyrics": lyrics,
        "tags": tags,
        "audio": audio_path,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    st.session_state.projects.insert(0, project)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        '<div class="nexa-logo">NEXA</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="nexa-subtitle">STEP INTO YOUR NEXT ERA</div>',
        unsafe_allow_html=True,
    )

    menu_items = [
        ("🏠", "Home"),
        ("🎵", "Create a Song"),
        ("🎙️", "Recording Studio"),
        ("🥁", "Beat Lab"),
        ("🎚️", "Mix & Master"),
        ("💿", "My Songs"),
        ("🚀", "Release Music"),
        ("⚙️", "Settings"),
    ]

    for icon, name in menu_items:

        if st.button(
            f"{icon}  {name}",
            key=f"menu_{name}",
            use_container_width=True,
        ):
            go(name)

    st.divider()

    st.markdown(
        """
        <div class="small-muted">
        NEXA STUDIO<br>
        AI-powered music creation
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# HOME
# =========================================================

if st.session_state.page == "Home":

    st.markdown(
        """
        <div class="hero">
            <h1>
                Make Music.<br>
                <span class="gradient-text">Enter Your Next Era.</span>
            </h1>
            <p>
                Turn your lyrics and ideas into original music,
                experiment with sounds, record vocals, mix your
                tracks and build your personal music library.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="card feature-card">
                <h3>🎵 AI Song Creator</h3>
                <p>
                Give NEXA your lyrics and describe how you want
                the song to feel.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="card feature-card">
                <h3>🎙️ Recording Studio</h3>
                <p>
                Upload or record vocals and prepare them for
                your production workflow.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="card feature-card">
                <h3>🥁 Beat Lab</h3>
                <p>
                Build your sound around beats, instruments,
                tempo and production ideas.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Start Creating")

    if st.button(
        "✨ Create My First Song",
        use_container_width=True,
        type="primary",
    ):
        go("Create a Song")


# =========================================================
# CREATE A SONG
# =========================================================

elif st.session_state.page == "Create a Song":

    st.title("🎵 Create a Song")

    st.caption(
        "Lyrics → Sound Direction → AI Generation → Your Song"
    )

    # -----------------------------------------------------
    # STEP 1
    # -----------------------------------------------------

    st.markdown(
        '<div class="card"><h3>1. Your Lyrics</h3></div>',
        unsafe_allow_html=True,
    )

    uploaded_lyrics = st.file_uploader(
        "Upload lyrics",
        type=["txt"],
        key="lyrics_upload",
    )

    if uploaded_lyrics:
        try:
            uploaded_text = uploaded_lyrics.read().decode("utf-8")
            st.session_state.lyrics = uploaded_text
        except Exception:
            st.error("Could not read that lyrics file.")

    lyrics = st.text_area(
        "Lyrics",
        value=st.session_state.lyrics,
        height=300,
        placeholder="""[Verse]
Write your verse here...

[Pre-Chorus]
Build the emotion...

[Chorus]
Write your hook here...

[Verse 2]
Continue the story...

[Bridge]
Change the feeling...

[Chorus]
Bring the hook back...""",
    )

    st.session_state.lyrics = lyrics

    st.info(
        "Tip: Use sections such as [Verse], [Chorus], "
        "[Bridge] and [Outro] to give the model structure."
    )

    # -----------------------------------------------------
    # STEP 2
    # -----------------------------------------------------

    st.markdown(
        '<div class="card"><h3>2. Tell NEXA How It Should Sound</h3></div>',
        unsafe_allow_html=True,
    )

    sound_description = st.text_area(
        "Describe the sound in your own words",
        value=st.session_state.sound_description,
        placeholder=(
            "Example: Hot and lively Afrobeat with heavy drums, "
            "deep bass, catchy melody and a late-night Nigerian vibe."
        ),
        height=120,
    )

    st.session_state.sound_description = sound_description

    c1, c2 = st.columns(2)

    with c1:

        genre = st.selectbox(
            "Genre",
            [
                "Afrobeat",
                "Afrofusion",
                "Amapiano",
                "R&B",
                "Pop",
                "Hip-Hop",
                "Dancehall",
                "Soul",
                "Gospel",
                "Alternative",
                "Other",
            ],
            index=0,
        )

        mood = st.selectbox(
            "Mood",
            [
                "Energetic",
                "Chill",
                "Emotional",
                "Romantic",
                "Dark",
                "Happy",
                "Uplifting",
                "Melancholic",
                "Aggressive",
                "Dreamy",
                "Spiritual",
            ],
        )

    with c2:

        vocal_style = st.selectbox(
            "Vocal Style",
            [
                "Male",
                "Female",
                "Soft Male",
                "Soft Female",
                "Powerful Male",
                "Powerful Female",
                "Mixed",
            ],
        )

        bpm = st.slider(
            "Tempo / BPM",
            min_value=60,
            max_value=160,
            value=100,
            step=1,
        )

    artist = st.selectbox(
        "Artist / Sound Inspiration",
        [
            "None",
            "Omah Lay",
            "Burna Boy",
            "Tems",
            "Wizkid",
            "Rema",
            "Davido",
            "Asake",
            "Fireboy DML",
        ],
    )

    st.caption(
        "Artist inspiration is translated into broad musical "
        "characteristics. NEXA does not attempt to copy an artist's "
        "exact voice, recording or melody."
    )

    # -----------------------------------------------------
    # HEARTMULA TAGS
    # -----------------------------------------------------

    generated_tags = build_heartmula_tags(
        genre,
        mood,
        vocal_style,
        bpm,
        sound_description,
        artist,
    )

    with st.expander("🔧 Advanced AI generation settings"):

        duration = st.slider(
            "Maximum song duration",
            min_value=30,
            max_value=180,
            value=60,
            step=10,
            help="HeartMuLa currently allows up to 180 seconds in this Space.",
        )

        temperature = st.slider(
            "Creativity / Temperature",
            min_value=0.1,
            max_value=2.0,
            value=1.0,
            step=0.1,
        )

        topk = st.slider(
            "Top-K",
            min_value=1,
            max_value=100,
            value=50,
            step=1,
        )

        cfg_scale = st.slider(
            "CFG Scale",
            min_value=1.0,
            max_value=3.0,
            value=1.5,
            step=0.1,
        )

        st.text_input(
            "Generated HeartMuLa tags",
            value=generated_tags,
            disabled=True,
        )

    # -----------------------------------------------------
    # GENERATE
    # -----------------------------------------------------

    st.markdown("---")

    if st.button(
        "🚀 GENERATE MY SONG",
        type="primary",
        use_container_width=True,
    ):

        if not lyrics.strip():
            st.error("Please enter your lyrics first.")

        elif not sound_description.strip():
            st.error(
                "Please describe how you want the song to sound."
            )

        else:

            with st.status(
                "Connecting to HeartMuLa...",
                expanded=True,
            ) as status:

                try:

                    st.write(
                        "Preparing your lyrics and musical style..."
                    )

                    tags = generated_tags

                    st.write(
                        f"Style tags: {tags}"
                    )

                    st.write(
                        "Sending the request to the HeartMuLa "
                        "music model..."
                    )

                    audio_path = generate_with_heartmula(
                        lyrics=lyrics,
                        tags=tags,
                        duration=duration,
                        temperature=temperature,
                        topk=topk,
                        cfg_scale=cfg_scale,
                    )

                    st.session_state.generated_audio = audio_path

                    title = (
                        f"NEXA Song "
                        f"{datetime.now().strftime('%Y%m%d-%H%M')}"
                    )

                    st.session_state.generated_title = title

                    save_project(
                        title,
                        lyrics,
                        tags,
                        audio_path,
                    )

                    status.update(
                        label="Song generated successfully! 🎉",
                        state="complete",
                    )

                except Exception as e:

                    status.update(
                        label="Generation failed",
                        state="error",
                    )

                    st.error(
                        "HeartMuLa could not generate the song."
                    )

                    st.code(
                        str(e),
                        language="text",
                    )

                    st.warning(
                        "If the HeartMuLa Space is sleeping, "
                        "wait a little and try again. The Space "
                        "may need to wake up and load its model."
                    )

    # -----------------------------------------------------
    # AUDIO RESULT
    # -----------------------------------------------------

    if st.session_state.generated_audio:

        st.markdown("---")

        st.success("🎉 Your generated track is ready!")

        st.audio(
            st.session_state.generated_audio
        )

        try:

            with open(
                st.session_state.generated_audio,
                "rb",
            ) as audio_file:

                file_data = audio_file.read()

            filename = (
                st.session_state.generated_title
                .replace(" ", "_")
                + ".wav"
            )

            st.download_button(
                "⬇️ Download Song",
                data=file_data,
                file_name=filename,
                mime="audio/wav",
                use_container_width=True,
            )

        except Exception:
            st.info(
                "The audio was generated, but the local download "
                "file could not be prepared."
            )


# =========================================================
# RECORDING STUDIO
# =========================================================

elif st.session_state.page == "Recording Studio":

    st.title("🎙️ Recording Studio")

    st.markdown(
        """
        <div class="card">
        <h3>Record or Upload Your Vocals</h3>
        <p>
        Bring your own voice into your NEXA project.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    audio_upload = st.file_uploader(
        "Upload a vocal recording",
        type=["wav", "mp3", "m4a", "ogg"],
    )

    if audio_upload:

        st.session_state.recording = audio_upload

        st.success("Vocal recording uploaded.")

        st.audio(audio_upload)

    st.markdown("### Vocal Processing")

    col1, col2 = st.columns(2)

    with col1:
        noise_reduction = st.checkbox(
            "Noise Reduction",
            value=True,
        )

        pitch_correction = st.checkbox(
            "Pitch Correction",
            value=False,
        )

        vocal_reverb = st.checkbox(
            "Vocal Reverb",
            value=True,
        )

    with col2:
        vocal_delay = st.checkbox(
            "Vocal Delay",
            value=False,
        )

        vocal_compression = st.checkbox(
            "Compression",
            value=True,
        )

        stereo_vocal = st.checkbox(
            "Stereo Width",
            value=False,
        )

    st.info(
        "The recording workspace is ready for the next audio-processing "
        "stage. Actual processing will be connected separately from "
        "HeartMuLa generation."
    )


# =========================================================
# BEAT LAB
# =========================================================

elif st.session_state.page == "Beat Lab":

    st.title("🥁 Beat Lab")

    st.markdown(
        """
        <div class="card">
        <h3>Build Your Instrumental</h3>
        <p>
        Create the production foundation for your song.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:

        st.selectbox(
            "Beat Style",
            [
                "Afrobeat",
                "Afrofusion",
                "Amapiano",
                "R&B",
                "Hip-Hop",
                "Dancehall",
                "Pop",
            ],
        )

        st.slider(
            "BPM",
            60,
            160,
            100,
        )

    with col2:

        st.multiselect(
            "Instruments",
            [
                "Drums",
                "Bass",
                "Piano",
                "Guitar",
                "Synth",
                "Percussion",
                "Pads",
                "Strings",
            ],
            default=["Drums", "Bass"],
        )

        st.selectbox(
            "Beat Energy",
            [
                "Chill",
                "Smooth",
                "Medium",
                "Energetic",
                "Club",
            ],
            index=3,
        )

    uploaded_beat = st.file_uploader(
        "Upload your own beat",
        type=["wav", "mp3", "m4a"],
    )

    if uploaded_beat:

        st.session_state.beat_file = uploaded_beat

        st.audio(uploaded_beat)

        st.success("Beat added to your workspace.")

    if st.button(
        "🥁 Generate Instrumental",
        use_container_width=True,
    ):
        st.info(
            "HeartMuLa song generation is currently connected "
            "through Create a Song. Dedicated Beat Lab generation "
            "will use the same music engine in a later module."
        )


# =========================================================
# MIX & MASTER
# =========================================================

elif st.session_state.page == "Mix & Master":

    st.title("🎚️ Mix & Master")

    st.markdown(
        """
        <div class="card">
        <h3>Prepare Your Track</h3>
        <p>
        Control the final character of your song.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    source_audio = st.file_uploader(
        "Upload track for mixing/mastering",
        type=["wav", "mp3", "m4a"],
    )

    if source_audio:

        st.session_state.master_file = source_audio

        st.audio(source_audio)

        st.markdown("### Mixing")

        c1, c2 = st.columns(2)

        with c1:

            st.slider(
                "Volume",
                -20.0,
                10.0,
                0.0,
            )

            st.slider(
                "Bass",
                -12.0,
                12.0,
                0.0,
            )

            st.slider(
                "Mid",
                -12.0,
                12.0,
                0.0,
            )

        with c2:

            st.slider(
                "Treble",
                -12.0,
                12.0,
                0.0,
            )

            st.slider(
                "Compression",
                0.0,
                100.0,
                35.0,
            )

            st.slider(
                "Stereo Width",
                0.0,
                100.0,
                50.0,
            )

        st.selectbox(
            "Mastering Preset",
            [
                "Balanced",
                "Loud",
                "Warm",
                "Bright",
                "Streaming",
                "Club",
            ],
        )

        if st.button(
            "✨ Process Track",
            type="primary",
            use_container_width=True,
        ):
            st.info(
                "The controls are prepared. Actual DSP processing "
                "will be connected in the audio-processing module."
            )

    else:

        st.info(
            "Upload a generated song or vocal/beat mix to begin."
        )


# =========================================================
# MY SONGS
# =========================================================

elif st.session_state.page == "My Songs":

    st.title("💿 My Songs")

    projects = st.session_state.projects

    if not projects:

        st.markdown(
            """
            <div class="card">
            <h3>Your music library is empty.</h3>
            <p>
            Generate your first song and it will appear here.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "🎵 Create a Song",
            use_container_width=True,
        ):
            go("Create a Song")

    else:

        for index, project in enumerate(projects):

            with st.container(border=True):

                st.subheader(
                    project["title"]
                )

                st.caption(
                    f"Created: {project['created']}"
                )

                st.caption(
                    f"Style: {project['tags']}"
                )

                if project.get("audio"):

                    try:
                        st.audio(
                            project["audio"]
                        )

                        with open(
                            project["audio"],
                            "rb",
                        ) as audio_file:

                            st.download_button(
                                "⬇️ Download",
                                audio_file.read(),
                                file_name=(
                                    project["title"]
                                    .replace(" ", "_")
                                    + ".wav"
                                ),
                                mime="audio/wav",
                                key=f"download_{index}",
                            )

                    except Exception:
                        st.warning(
                            "The saved audio file is no longer "
                            "available in this session."
                        )


# =========================================================
# RELEASE MUSIC
# =========================================================

elif st.session_state.page == "Release Music":

    st.title("🚀 Release Music")

    st.markdown(
        """
        <div class="card">
        <h3>Take Your Music to the World</h3>
        <p>
        NEXA can prepare your release information, artwork,
        metadata and files for distribution.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    platforms = st.multiselect(
        "Target Platforms",
        [
            "Spotify",
            "Apple Music",
            "YouTube Music",
            "Audiomack",
            "Boomplay",
        ],
        default=[
            "Spotify",
            "YouTube Music",
        ],
    )

    title = st.text_input(
        "Song Title"
    )

    artist_name = st.text_input(
        "Artist Name"
    )

    cover = st.file_uploader(
        "Cover Artwork",
        type=["png", "jpg", "jpeg"],
    )

    if st.button(
        "Prepare Release",
        type="primary",
        use_container_width=True,
    ):

        if not title or not artist_name:

            st.warning(
                "Enter your song title and artist name."
            )

        else:

            st.success(
                "Release information prepared."
            )

            st.info(
                "Music is normally delivered to streaming services "
                "through a music distributor rather than by directly "
                "uploading an ordinary audio file to Spotify."
            )


# =========================================================
# SETTINGS
# =========================================================

elif st.session_state.page == "Settings":

    st.title("⚙️ Settings")

    st.markdown(
        "### NEXA STUDIO"

    )

    st.write(
        "Private AI music workspace"
    )

    st.markdown("---")

    st.markdown("### HeartMuLa")

    st.code(
        HEARTMULA_SPACE,
        language="text",
    )

    st.markdown(
        """
        <div class="status-good">
        ✓ NEXA is configured to use the current HeartMuLa
        ZeroGPU Space.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown("### About Artist Inspiration")

    st.write(
        "Artist inspiration is used only to translate a requested "
        "sound into broad musical characteristics. The app does not "
        "attempt to reproduce an artist's exact voice, recording, "
        "melody or copyrighted song."
    )

    st.markdown("---")

    st.markdown("### Technical Information")

    st.write(
        "HeartMuLa accepts lyrics and musical tags. NEXA converts "
        "your natural-language sound description into those tags."
)
