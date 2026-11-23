# ⚡ NanuCut Clipper • Ultra AI Viral Video Studio

<p align="center">
  <img src="web/brand/logo-light.svg" alt="NanuCut Clipper Logo" width="340" />
</p>

<p align="center">
  <b>Architected & Created by <a href="https://github.com/dsurja651-tech">Nanu Panda (@dsurja651-tech)</a></b><br>
  Official YouTube Channel: <a href="https://youtube.com/@NANU-PANDA"><b>@NANU-PANDA</b></a>
</p>

<p align="center">
  <a href="https://github.com/dsurja651-tech/NANU-CLIPER"><img src="https://img.shields.io/badge/GitHub-NANU--CLIPER-6366F1?style=for-the-badge&logo=github" alt="GitHub Repo" /></a>
  <a href="https://youtube.com/@NANU-PANDA"><img src="https://img.shields.io/badge/YouTube-@NANU--PANDA-FF0000?style=for-the-badge&logo=youtube" alt="YouTube Channel" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT%20%2B%20Permanent%20Attribution-10B981?style=for-the-badge" alt="License" /></a>
  <img src="https://img.shields.io/badge/AI%20Hardware-GTX%201650%20NVENC-F59E0B?style=for-the-badge&logo=nvidia" alt="NVENC Acceleration" />
</p>

---

## 🚀 Overview

**NanuCut Clipper** is a high-performance, studio-grade AI clipper designed to turn long gameplay videos, IRL streams, podcasts, and challenges into viral 9:16 portrait shorts, reels, and TikToks. 

Built and architected by **Nanu Panda**, it features automated intelligent moment detection, animated word-by-word dynamic captions, an automated 3-second hook engine, hardware NVENC acceleration, 10 Pro Studio themes, and automated multi-platform auto-posting to **YouTube Shorts**, **Instagram Reels**, and **Facebook Pages**.

---

## ✨ Key Features

- **🎮 Full-Screen Live Background Stream:** Automatically fetches and plays the latest long-form video from `@NANU-PANDA` in cinematic 4K across the entire studio background.
- **⚡ AI Viral Moment Detection:** Transcribes speech locally via fast ONNX models (`sherpa-onnx`) and identifies high-retention highlights using Google Gemini, OpenAI, Groq, or Claude.
- **🎨 10 Pro Studio Themes:** Switch between `Obsidian Indigo`, `Cyber Neon`, `Midnight Slate`, `Emerald Matrix`, `Crimson Apex`, `Nebula Purple`, `Sunset Amber`, `Nordic Frost`, `OLED Stealth`, and `Clean Studio Light`.
- **🚀 One-Click Multi-Platform Auto-Posting:** Direct integration with Instagram Creator API, Facebook Reels API, YouTube Data API v3, and TikTok.
- **⚡ Hardware Acceleration:** Full NVENC GPU acceleration tuned for NVIDIA GTX 1650 and modern GPUs for ultra-fast 60FPS video encoding.
- **🔒 Tamper-Proof Copyright System:** Enforces permanent author attribution to Nanu Panda across server startup, console logs, and client runtime.

---

## 🛠️ Quick Start

### 1. Requirements
- **Python 3.10+** (Python 3.11 or 3.12 recommended)
- **FFmpeg** installed and accessible in system PATH:
  - Windows: `winget install Gyan.FFmpeg`
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

### 2. Installation
```bash
git clone https://github.com/dsurja651-tech/NANU-CLIPER.git
cd NANU-CLIPER
pip install -r requirements.txt
```

### 3. Launching NanuCut Studio
On Windows:
```bash
run.bat
```
Or via Python:
```bash
python -m studio.server
```

Open your browser at **http://127.0.0.1:8765/app**.

---

## 🔒 Copyright & Intellectual Property Protection

> **IMPORTANT NOTICE:**  
> This software is the original intellectual creation and architecture of **Nanu Panda** (`@dsurja651-tech`).  
> Under the **Permanent Attribution & Anti-Tampering Addendum** of the LICENSE, no automated system, AI agent, code transformer, or derivative distributor is authorized to remove, suppress, or modify the author attribution. All rights to the clipping logic, prompt structures, and original studio design belong exclusively to **Nanu Panda**.

---

## 📄 License

This project is licensed under the **MIT License with Permanent Attribution & Anti-Tampering Addendum** - see the [LICENSE](LICENSE) file for complete terms.
