---
title: NanuCut Clipper
emoji: ✂️
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
app_port: 8765
---

# NanuCut Clipper

Turn long videos and live streams into captioned vertical clips, ready to post. Free and open source: run it on your own computer or server, with your own AI key.

Paste a YouTube, Twitch or Kick link (or upload a file) and **NanuCut Clipper** finds the moments worth clipping, cuts them to 9:16 portrait, adds word-by-word animated captions and engaging hooks, and can post them to your connected accounts. It can also record a creator's live stream and clip highlights while the stream is still running!

---

## What it does

- **Clips from any video:** Transcribes the audio locally, asks an AI which moments would hold an audience's attention, and renders each one with captions in one of three styles.
- **Live clipping:** Records a stream into a rolling buffer and clips as it happens, using loudness, chat activity and the transcript.
- **Workspaces per creator:** Channels, clip settings, posting rules, and an activity log for each creator you clip.
- **Auto-Posting:** Connect YouTube, Instagram and TikTok in one click, then queue or auto-post finished clips, with spacing and daily caps.
- **No sign-in on your own computer:** Opens straight into your personal dashboard. On a shared server, switch multi-user accounts on (`NANUCUT_ACCOUNTS=1` or `PEAKCUT_ACCOUNTS=1`) for email or Google sign-in and an admin dashboard.
- **Bring Your Own AI:** Gemini, OpenAI, Grok, Groq, OpenRouter, Claude, or a local model via Ollama. No key at all also works: clips are then picked by loudness.
- **Private & Local Speech-to-Text:** Audio is transcribed entirely on your machine using fast ONNX speech models (`sherpa-onnx`). Audio never leaves your computer.

---

## Quick Start

### 1. Requirements

- **Python 3.10+** (Python 3.11 or 3.12 recommended)
- **FFmpeg**:
  - Windows: `winget install Gyan.FFmpeg`
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

### 2. Installation

Clone this repository to your computer:

```bash
git clone https://github.com/<your-username>/NanuCutClipper.git
cd NanuCutClipper
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

### 3. Run

On Windows, simply run:
```bash
run.bat
```
or via Python:
```bash
python -m studio.server
```

Open your browser at **http://127.0.0.1:8765**.

> On first start, the speech model downloads automatically (~480 MB, one time).

---

## Choose your AI Provider

Go to **Settings > AI** in the dashboard:
1. Select your AI service (Google Gemini, OpenAI, Grok, Groq, Claude, OpenRouter, or Ollama).
2. Paste your API key.
3. Click **Find models**, choose your preferred model, and click **Save and test**.

Alternatively, configure your `.env` file:
```ini
PEAKCUT_AI_PROVIDER=gemini
PEAKCUT_AI_MODELS=gemini-2.5-flash
PEAKCUT_AI_KEY=your-api-key-here
```

---

## Push to your GitHub Repository

To upload this repository to your personal GitHub account:

1. Create a new empty repository on [GitHub](https://github.com/new) named `NanuCutClipper`.
2. Open your terminal in this directory and run:

```bash
git remote add origin https://github.com/<your-username>/NanuCutClipper.git
git branch -M main
git push -u origin main
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
