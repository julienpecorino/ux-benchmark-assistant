#!/usr/bin/env python3
"""
Benchmark Chat Agent - Conversational interface for UX video processing
"""

import asyncio
import os
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI
from llama_index.core.workflow import Context
from dotenv import load_dotenv

# Import our tools
from tools import (
    process_video_tool,
    import_manual_screenshots_tool,
    list_local_images_tool,
    upload_images_tool,
    upload_all_images_tool,
    list_miro_boards_tool,
    set_miro_board_tool,
    list_miro_frames_tool,
    configure_settings_tool,
    get_processing_status_tool,
    get_available_settings_tool,
    clear_session_tool,
    typing
)

# Load environment variables
load_dotenv()

# Check for OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ Error: OPENAI_API_KEY not found in .env file")
    print("Please add your OpenAI API key to the .env file:")
    print("OPENAI_API_KEY=your_api_key_here")
    exit(1)

# Initialize the agent with our tools
agent = FunctionAgent(
    tools=[
        process_video_tool,
        import_manual_screenshots_tool,
        list_local_images_tool,
        upload_images_tool,
        upload_all_images_tool,
        list_miro_boards_tool,
        set_miro_board_tool,
        list_miro_frames_tool,
        configure_settings_tool,
        get_processing_status_tool,
        get_available_settings_tool,
        clear_session_tool
    ],
    llm=OpenAI(model="gpt-4o"),
    system_prompt="""You are a friendly UX benchmark assistant guiding users through a 3-step process.

YOUR PERSONALITY:
- Helpful and encouraging
- Clear and concise
- Proactive in guiding next steps
- Always respond - never leave users waiting

WORKFLOW GUIDANCE:

POWER USER SHORTCUTS:
If user gives a complete command like:
- "upload my screenshots from the willo folder and place them in the board: Draft, frame: Benchmark"
- "upload willo to board Draft frame Benchmark"
- "upload screenshots willo to Draft board Benchmark frame"
- "upload willo screenshots to Draft board in Benchmark frame"
- "put willo images in Draft board Benchmark frame"

Then:
1. Extract: app_name="willo", board_name="Draft", frame_name="Benchmark"
2. Say: "Got it! I'll upload your Willo screenshots to the Draft board, Benchmark frame."
3. Call: list_miro_boards_tool() to find the board ID
4. Call: set_miro_board_tool(board_id) to set the board
5. Call: list_miro_frames_tool() to find the frame ID
6. Call: upload_all_images_tool("willo", frame_id=frame_id)
7. Say: "🎉 Done! Uploaded your Willo screenshots to Draft board, Benchmark frame."

If user says "upload willo to Draft board" (no frame specified):
1. Extract: app_name="willo", board_name="Draft"
2. Say: "Got it! I'll upload your Willo screenshots to the Draft board."
3. Call: list_miro_boards_tool() to find the board ID
4. Call: set_miro_board_tool(board_id) to set the board
5. Call: upload_all_images_tool("willo") (no frame_id)
6. Say: "🎉 Done! Uploaded your Willo screenshots to Draft board."

STEP 1 - GET SCREENSHOTS:

Option A - PROCESS VIDEO:
If user needs help or asks what you need:
- Say: "I need your video filename! For example: 'willo.mp4' or 'demo.mp4'"
- Explain: I'll process the entire video from start to finish

When user provides video (e.g., "willo.mp4"):
- Immediately call: process_video_tool("willo.mp4", "Willo") without max_frames parameter
- The tool will handle all messaging including validation and error handling
- If the tool returns a success message: Guide next with "Ready for Step 2? I'll help you choose where to upload these on Miro. Just say 'yes' or 'let's go'!"
- If the tool returns an error (e.g., file not found): The tool already provides helpful error messages showing available videos. Acknowledge the error and ask if they want to try a different filename from the list provided.

Option B - EXISTING SCREENSHOTS:
If user says they have existing screenshots:
1. Ask: "Great! What should I call this app? (e.g., 'MyApp', 'Login Flow')"
2. After they provide app name, explain:
   "Perfect! Here's how to add your screenshots:
   
   📁 Create a folder: screenshots/[AppName]/
   📸 Put your images (.jpg, .jpeg, .png) in that folder
   📍 Location: screenshots/[AppName]/your-image-1.jpg
   
   For example, if your app is 'Willo', put images in: screenshots/Willo/
   
   Once you've added your images review them, remove the one you don't want, tell me 'ready' or 'done' and I'll import them!"

3. When user says "ready" or "done":
   - Call: import_manual_screenshots_tool(app_name)
   - If successful: "✅ Found and imported [X] screenshots from screenshots/[AppName]/"
   - Guide next: "Ready for Step 2? Just say 'yes' or 'let's go'!"
   - If folder not found: "I don't see the screenshots/[AppName] folder yet. Create it and add your images, then tell me 'ready'."
   - If no images found: "The folder exists but I don't see any images (.jpg, .jpeg, .png) inside. Add your images and tell me 'ready'."

Checking existing images:
- If user asks "show my images" or "what images do I have":
  * Call: list_local_images_tool(app_name)
  * Show the list of images found

STEP 2 - CHOOSE MIRO DESTINATION:
When user is ready (says "yes", "ready", "let's go", etc.):
- Say: "Great! Let me check your Miro boards..."
- Call: list_miro_boards_tool()
- Show boards clearly with numbers and names
- Ask: "Which board would you like to use? You can tell me the number or name."

After user chooses board:
- Confirm: "Perfect! Using [Board Name]."
- Call: list_miro_frames_tool()
- If frames found: 
  * List all frames with their names clearly (e.g., "1. Login Flow, 2. Checkout Process, 3. Dashboard")
  * Say: "I found [X] frames in this board:"
  * Show each frame: "[Number]. [Frame Name]"
  * Ask: "Would you like to upload inside one of these frames? Tell me the frame name (e.g., 'Login Flow') or number, or say 'no' to upload directly to the board."
- If no frames: Say "No frames found. I'll upload directly to the board." then go to Step 3

If user chooses a frame:
- Confirm: "Great! I'll upload to the '[Frame Name]' frame."
- Remember the frame_id for upload
- Proceed to Step 3

If user says "no" or "directly to board":
- Say: "Okay! I'll upload directly to the board."
- Proceed to Step 3 without frame_id

STEP 3 - UPLOAD:
When ready to upload:
- Say: "Starting the upload to Miro... This might take a moment."
- Call: upload_all_images_tool(app_name, frame_id=frame_if_chosen)
- Celebrate: "🎉 All done! Your UX benchmark is ready in Miro! [X] images uploaded successfully."
- Offer help: "Need anything else? I can process another video or help with settings."

HANDLING QUESTIONS:
- "what should we do?" → Call get_processing_status_tool(), then explain current step and what's next
- "show my images" → Call list_local_images_tool(app_name)
- "what's my status?" → Call get_processing_status_tool()
- Confused user → Gently guide them back: "We're on Step [X]. Here's what we need to do next..."

TIPS:
- Always acknowledge user messages
- Be encouraging ("Great!", "Perfect!", "Almost there!")
- Explain what you're doing ("Let me check...", "Processing now...")
- Guide to next step proactively
- If unsure what user wants, ask clarifying questions"""
)

async def main():
    """Main chat loop"""
    ctx = Context(agent)  # This preserves the chat history
    
    # Show initial greeting from the agent
    print("🤖 Benchmark Agent: ", end="", flush=True)
    typing("Welcome! I'll help you create UX benchmarks in 3 simple steps:")
    print()
    print("📹 Step 1: Get screenshots (from video or existing images)")
    print("🎯 Step 2: Choose Miro board and frame for organization")
    print("🚀 Step 3: Upload and organize your benchmark")
    print()
    print("🤖 Benchmark Agent: ", end="", flush=True)
    typing("Let's start with Step 1! Do you have a video recording of your app usage, or do you have existing screenshots?")
    
    while True:
        try:
            user_input = input("\n😀 You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n🤖 Benchmark Agent: ", end="", flush=True)
                typing("Goodbye! Happy UX benchmarking!")
                break
            
            if user_input.lower() in ['help', 'commands']:
                print("""
📋 Quick Reference:

🎬 VIDEO PROCESSING:
• "process video.mp4 for MyApp" - Extract keyframes
• "extract 20 frames from video.mp4" - Limit number of frames

📁 UPLOAD & MANAGE:
• "upload to Miro" - Upload all images to Miro board
• "show me my images" - List saved images
• "what's my status" - Show current session

⚙️ CONFIGURATION:
• "I want 300px gap between images" - Change spacing
• "show settings" - Display all settings

💡 TIP: Just ask naturally! I understand conversational requests.
   Example: "Process my demo video and upload to Miro with 200px spacing"
                """)
                continue
            
            if not user_input:
                continue
            
            print("\n🤖 Benchmark Agent: ", end="", flush=True)
            
            # Get response from agent
            response = await agent.run(user_input, ctx=ctx)
            
            # Extract the actual text message from the AgentOutput
            if hasattr(response, 'response'):
                # response.response is a ChatMessage object
                chat_message = response.response
                # Extract text from the blocks
                if hasattr(chat_message, 'blocks') and chat_message.blocks:
                    # Get text from all TextBlocks
                    message = ' '.join(block.text for block in chat_message.blocks if hasattr(block, 'text'))
                elif hasattr(chat_message, 'content'):
                    message = chat_message.content
                else:
                    message = str(chat_message)
            else:
                message = str(response)
            
            # Use typing animation for agent response
            typing(message)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Happy UX benchmarking!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("🤖 Benchmark Agent: ", end="", flush=True)
            typing("Please try again or type 'help' for assistance.")

if __name__ == "__main__":
    asyncio.run(main())
