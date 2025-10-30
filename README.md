
# UX Video → Key Screens → Miro (Chat Agent Edition)

## 🎯 Goal
This tool **automates manual UX benchmarking tasks** for Designers, eliminating the tedious work of creating visual comparisons.

**Traditionally, designers spend hours:**
- Manually scrubbing through long video recordings frame by frame
- Identifying key screen transitions
- Manually taking screenshots
- Organizing and uploading images to Miro
- Aligning screenshots for side-by-side comparison

**This tool does all of that automatically:**
- 🤖 Detects **screen changes** in videos using intelligent algorithms
- 📸 Extracts **key screenshots** at the right moments (after transitions complete)
- 📤 Uploads directly to **Miro** through a conversational chat interface
- 📐 Arranges images **side-by-side** (horizontal layout) for easy comparison
- 🎯 Groups each app's screenshots together in separate rows

**Result**: Create professional UX benchmarks in minutes, not hours!

**New**: Chat with an AI agent instead of typing command-line arguments!

## 🤖 Chat Agent Features
- **Natural language processing**: "upload image from my myVideo.MP4 video"
- **Automatic parameter extraction**: "I want 300px gap between images"
- **Progress reporting**: Real-time updates during processing
- **Review workflow**: Save locally first, then upload selected images
- **Multi-video support**: Process multiple apps in one conversation
- **Memory efficient**: Chunked processing prevents memory issues

---

## ⚙️ Installation

### 1️⃣ Create and activate a Python virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate        # on macOS/Linux
# or
.\.venv\Scriptsctivate         # on Windows
```

### 2️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

---

## 🔐 Environment variables using `.env` file

The chat agent automatically loads variables from a `.env` file using `python-dotenv`.  
You **don't need to export them manually** each time.

### 1️⃣ Create your `.env` file
Copy the provided `.env.example` and rename it to `.env`:
```bash
cp .env.example .env
```

Then edit it and fill in your real values:
```bash
# OpenAI API Key (required for chat agent)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Miro API Credentials (required for uploading to Miro)
MIRO_TOKEN=eyJhbGci...      # Your Miro API token (boards:write scope)
MIRO_BOARD_ID=uXyZ123...    # Your Miro board ID
```

⚠️ **Important security note**
- Keep this file private — do **not** upload or share it.  
- If you use Git, add it to your `.gitignore`:
  ```
  .env
  ```

---

## 🚀 Usage

### 🤖 Chat Agent (Recommended)
Start the conversational chat agent:
```bash
python benchmark_agent.py
```

**Example conversation:**
```
🤖 Benchmark Agent: Welcome! I'll help you create UX benchmarks in 3 simple steps...

😀 You: myVideo.mp4
🤖 Benchmark Agent: Got it! Processing myVideo.mp4 from start to finish...
🤖 Benchmark Agent: ✅ Done! I extracted 42 keyframes and saved them to screenshots/MyVideo/

😀 You: upload myVideo to board Draft frame Benchmark
🤖 Benchmark Agent: Got it! I'll upload your MyVideo screenshots to the Draft board, Benchmark frame.
🤖 Benchmark Agent: 🎉 Done! Uploaded your MyVideo screenshots to Draft board, Benchmark frame.
```

**Or step-by-step:**
```
😀 You: myVideo.mp4
🤖 Benchmark Agent: Processing entire video...
🤖 Benchmark Agent: ✅ Done! 42 screenshots saved. Ready for Step 2?

😀 You: yes
🤖 Benchmark Agent: Great! Let me check your Miro boards...
🤖 Benchmark Agent: Which board would you like to use?

😀 You: Draft
🤖 Benchmark Agent: Perfect! I found 3 frames. Which frame?

😀 You: Benchmark
🤖 Benchmark Agent: 🎉 All done! 42 images uploaded to Benchmark frame!
```

### 📁 Video folder setup
**Important**: All video files must be placed in a `video/` folder in your project directory.

```bash
# Create the video folder
mkdir video

# Place your videos in the video folder
# video/demo.mp4
# video/app1.mp4
# video/app2.mp4

# Then start the chat agent
python benchmark_agent.py
```

### 🔧 Available Commands
- **Process video**: Just provide the filename! "myVideo.mp4" or "demo.mp4" (processes entire video)
- **Power user upload**: "upload myVideo to board Draft frame Benchmark" (one command does everything!)
- **List images**: "show me my images" or "list images for MyApp"
- **Upload to Miro**: "upload to Miro" or "proceed with upload"
- **Configure settings**: "set image width to 500" or "change spacing to 200"
- **Check status**: "what's my status" or "show settings"
- **Clear session**: "clear session" or "start over"
- **Help**: "help" or "commands"
- **Exit**: "exit" or "quit"

### 📊 Legacy Command Line (Still Available)
If you prefer the old command-line interface:
```bash
python Benchmark.py --video demo.mp4 --app "MyVideo" --image-width 600 --layout horizontal --image-spacing 100
```

**Note**: The `--max` parameter is now optional. By default, the entire video is processed.

---

### 🔧 Common options
| Option | Description |
|--------|--------------|
| `--max` | Max number of screenshots per app (default: 0 = processes entire video) |
| `--fps` | Sampling rate for change detection (default 2 fps) |
| `--diff` | Histogram change threshold (0..1); lower = more sensitive |
| `--stride` | Minimum distance between detected frames |
| `--image-width` | Resize width for screenshots (default 900 px) |
| `--layout` | Layout direction: `horizontal` (side-by-side) or `vertical` (top-to-bottom) |
| `--image-spacing` | Spacing between images in layout direction (default 100 px) |
| `--group-margin` | Space between different app groups (default 240 px) |
| `--start-x` | Starting X position on board (default 0) |
| `--start-y` | Starting Y position on board (default 0) |
| `--format` | Upload image format (jpeg/png) |
| `--jpeg-quality` | JPEG compression quality (50–95) |

---

### 🧠 Example board layout (Horizontal)
```
App A: [Screenshot 1] [Screenshot 2] [Screenshot 3]
App B: [Screenshot 1] [Screenshot 2] [Screenshot 3]
App C: [Screenshot 1] [Screenshot 2] [Screenshot 3]
```

Images are arranged side-by-side for easy comparison, with each app's screenshots in its own row.

---

### ✅ Output
After execution:
- Images uploaded directly to your existing Miro board (no frames created)
- Screenshots arranged side-by-side for easy comparison
- Each app's screenshots grouped in separate rows
- Clean horizontal layout with configurable spacing
- Perfect for building UX comparison boards
