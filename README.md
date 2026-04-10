# Microbiology in Agriculture - Study App

An interactive web app for studying Microbiology in Agriculture, built from university lecture content.

## Features

- **13 lectures** across 5 weeks with detailed explanations and analogies
- **260 quiz questions** (20 per lecture) - recall, understanding, and scenario-based
- **56+ educational images** from Wikimedia Commons
- **45 YouTube videos** from Khan Academy, Amoeba Sisters, Ninja Nerd, CrashCourse
- **Text-to-speech** using native macOS voices
- **Search** across all content
- **Progress tracking** with localStorage
- **Dark/light mode**
- **Responsive design**

## Quick Start

```bash
python3 micro_server.py
```

This starts a local server at `http://localhost:8742` and opens your browser automatically. The server provides text-to-speech using your Mac's built-in voices.

## Files

- `MicrobiologyStudy.html` - The complete single-file web app (544 KB)
- `micro_server.py` - Local Python server for TTS support

## Requirements

- macOS (for native voice TTS)
- Python 3 (no dependencies needed)
- Any modern browser
