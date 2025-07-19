# YouTube Video Note

A powerful tool that automatically generates comprehensive notes from YouTube videos, including transcriptions, summaries, and key moment screenshots.

## Features

- **YouTube Video Download**: Easily download videos from YouTube URLs
- **Automatic Transcription**: Generate accurate transcriptions with timestamps
- **AI-Powered Summarization**: Create concise, informative summaries of video content
- **Intelligent Screenshot Capture**: Automatically identify and capture screenshots at key moments
- **Enhanced Summary Generation**: Integrate screenshots into summaries for visual context
- **Organized Results**: All outputs are neatly organized by video ID

## Requirements

- Python 3.13 or higher
- uv (Python package manager)
- FFmpeg (for video processing)
- OpenAI API key (for AI features)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/yt-video-note.git
   cd yt-video-note
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
   > For more details see the `.env.example` file in the project root for configuration options and required environment variables.

## Usage

Run the main script:

```bash
make run
```

The application will:
1. Prompt you to enter a YouTube URL
2. Download the video
3. Generate a transcription with timestamps
4. Create an AI-powered summary
5. Capture screenshots at key moments
6. Enhance the summary with relevant screenshots
7. Save all outputs to the `results/[video_id]/` directory

## Output Files

For each processed video, the following files are generated in the `results/[video_id]/` directory:

- `video.mp4`: The downloaded video
- `transcription.txt`: Full transcription with timestamps
- `summary-raw.md`: Initial AI-generated summary
- `summary.md`: Enhanced summary with screenshots
- `screenshots/`: Directory containing screenshots at key timestamps

## Dependencies

- dotenv: Environment variable management
- ffmpeg-python: Video processing
- langchain[openai]: AI language model integration
- langgraph: AI agent creation
- openai-whisper: Speech-to-text transcription
- rich: Enhanced terminal output
- yt-dlp: YouTube video downloading

## License

[MIT LICENSE](./LICENSE)

## Acknowledgements

- This project uses OpenAI's models for AI-powered features
- Thanks to the developers of all the open-source libraries used in this project