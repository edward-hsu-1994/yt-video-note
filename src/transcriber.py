import os
import asyncio
import tempfile
import ffmpeg
from typing import Union, Optional, Dict, Any

class Transcriber:
    """
    A class to handle video transcription using OpenAI's Whisper model.
    Converts MP4 media files to text subtitles.

    Note: This class requires the following dependencies:
    - ffmpeg-python (already in project dependencies)
    - openai-whisper (needs to be installed: pip install openai-whisper)
    """

    def __init__(self, ffmpeg_path: Union[str, None] = None, model_size: str = "large-v3-turbo"):
        """
        Initializes the Transcriber class.

        Args:
            ffmpeg_path (Union[str, None]): Path to the ffmpeg executable. If None, it will use the system's default.
            model_size (str): Size of the Whisper model to use. Options: "tiny", "base", "small", "medium", "large".
                              Default: "large-v3-turbo".
        """
        self._ffmpeg_path = ffmpeg_path or "ffmpeg"
        self._model_size = model_size
        self._whisper_model = None  # Lazy-loaded when needed

    async def _load_whisper_model(self):
        """
        Loads the Whisper model if it hasn't been loaded yet.

        Raises:
            ImportError: If the whisper package is not installed.
        """
        if self._whisper_model is None:
            try:
                import whisper
            except ImportError:
                raise ImportError(
                    "The whisper package is not installed. "
                    "Please install it using: pip install openai-whisper"
                )

            # Load the model in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            self._whisper_model = await loop.run_in_executor(
                None, lambda: whisper.load_model(self._model_size)
            )

    async def _extract_audio(self, media_path: str) -> str:
        """
        Extracts audio from a media file using ffmpeg.

        Args:
            media_path (str): Path to the media file.

        Returns:
            str: Path to the extracted audio file.

        Raises:
            FileExistsError: If the media file doesn't exist.
            RuntimeError: If ffmpeg fails to extract the audio.
        """
        if not os.path.exists(media_path):
            raise FileExistsError(f"media file not found: {media_path}")

        # Create a temporary file for the audio
        temp_audio_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_audio_path = temp_audio_file.name
        temp_audio_file.close()

        try:
            # Extract audio using ffmpeg
            stream = (
                ffmpeg
                .input(media_path)
                .output(temp_audio_path, acodec='pcm_s16le', ac=1, ar='16k')
            )

            # Run the ffmpeg command
            process = stream.run_async(pipe_stdout=True, pipe_stderr=True, cmd=self._ffmpeg_path, overwrite_output=True)
            process.wait()

            # Check for errors
            if process.returncode != 0:
                stderr = process.stderr.read()
                raise RuntimeError(f"FFmpeg error extracting audio: {stderr.decode('utf-8')}")

            return temp_audio_path

        except Exception as e:
            # Clean up the temporary file if an error occurs
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
            raise RuntimeError(f"Failed to extract audio from video: {e}")

    async def transcribe_with_timestamps(self, video_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribes a media file to text with timestamps using Whisper.

        Args:
            video_path (str): Path to the media file.
            language (Optional[str]): Language code for transcription (e.g., "en", "zh", "ja").
                                     If None, Whisper will auto-detect the language.

        Returns:
            Dict[str, Any]: A dictionary containing the transcription results with segments and timestamps.

        Raises:
            FileExistsError: If the media file doesn't exist.
            ImportError: If the whisper package is not installed.
            RuntimeError: If transcription fails.
        """
        # Check if the media file exists
        if not os.path.exists(video_path):
            raise FileExistsError(f"media file not found: {video_path}")

        # Load the Whisper model
        await self._load_whisper_model()

        # Extract audio from the video
        audio_path = await self._extract_audio(video_path)

        try:
            # Prepare transcription options
            options: Dict[str, Any] = {}
            if language:
                options["language"] = language

            # Run transcription in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._whisper_model.transcribe(audio_path, **options)
            )

            return result

        finally:
            # Clean up the temporary audio file
            if os.path.exists(audio_path):
                os.unlink(audio_path)

    async def transcribe(self, video_path: str, language: Optional[str] = None) -> str:
        """
        Transcribes a media file to text using Whisper.

        Args:
            video_path (str): Path to the media file.
            language (Optional[str]): Language code for transcription (e.g., "en", "zh", "ja").
                                     If None, Whisper will auto-detect the language.

        Returns:
            str: The transcribed text.

        Raises:
            FileExistsError: If the media file doesn't exist.
            ImportError: If the whisper package is not installed.
            RuntimeError: If transcription fails.
        """
        transcribe_with_timestamps = await self.transcribe_with_timestamps(video_path, language)

        transcribe_str = ""
        for segment in  transcribe_with_timestamps["segments"]:
            transcribe_str += segment["text"] or ""
            transcribe_str += "\n"

        return transcribe_str.strip()

    async def transcribe_with_timestamps_str(self, video_path: str, language: Optional[str] = None) -> str:
        """
        Transcribes a media file and returns a formatted string with timestamps for each segment.

        Args:
            video_path (str): Path to the media file.
            language (Optional[str]): Language code for transcription (e.g., "en", "zh", "ja").
                                     If None, Whisper will auto-detect the language.

        Returns:
            str: The transcribed text.

        Raises:
            FileExistsError: If the media file doesn't exist.
            ImportError: If the whisper package is not installed.
            RuntimeError: If transcription fails.
        """

        transcribe_with_timestamps = await self.transcribe_with_timestamps(video_path, language)

        transcribe_str = ""
        for segment in transcribe_with_timestamps["segments"]:
            start = segment["start"]
            end = segment["end"]
            text = segment["text"]
            transcribe_str += f"[{start:.2f}s - {end:.2f}s] {text}\n"

        return transcribe_str.strip()


# --- Usage Example ---
async def main():
    # Create a Transcriber instance
    transcriber = Transcriber()

    # Example media file path
    print("Please provide the media file path: ")
    video_file = input().strip()

    if not os.path.exists(video_file):
        raise FileExistsError(f"media file '{video_file}' does not exist.")

    try:
        # Transcribe the video
        print(f"Transcribing '{video_file}'...")
        text = await transcriber.transcribe(video_file)
        print(f"Transcription result:\n{text}")

        # Transcribe with timestamps
        print(f"\nTranscribing '{video_file}' with timestamps...")
        result = await transcriber.transcribe_with_timestamps_str(video_file)

        # Print segments with timestamps
        print("\nSegments with timestamps:")
        print(f"Transcription with timestamps:\n{result}")

    except ImportError as e:
        print(f"Error: {e}")
        print("Please install the required dependencies.")
    except FileExistsError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())