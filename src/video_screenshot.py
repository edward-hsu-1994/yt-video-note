import os
import asyncio
import ffmpeg
from typing import NamedTuple, Union


class Position(NamedTuple):
    """
    Represents a single coordinate point (x, y).
    """
    x: int
    y: int

class VideoScreenshot:
    """
    A class to handle video screenshots, including getting full and cropped images.
    """

    def __init__(self, ffmpeg_path: Union[str, None] = None):
        """
        Initializes the VideoScreenshot class.
        Args:
            ffmpeg_path (Union[str, None]): Path to the ffmpeg executable. If None, it will use the system's default.
        """
        self._ffmpeg_path = ffmpeg_path or "ffmpeg"

    async def _run_ffmpeg_command(self, stream, desc: str) -> bytes:
        """
        Internal helper to run ffmpeg commands and handle output/errors.
        Args:
            stream: The ffmpeg-python stream object representing the command.
            desc (str): A description for error messages.
        Returns:
            bytes: The stdout data from the ffmpeg process.
        Raises:
            RuntimeError: If ffmpeg fails or an unexpected error occurs.
        """
        try:
            process = stream.run_async(pipe_stdout=True, pipe_stderr=True, cmd=self._ffmpeg_path)



            # Read stdout
            stdout = process.stdout.read()
            stderr = process.stderr.read()


            process.wait()  # Ensure the FFmpeg process has finished executing


            # Check FFmpeg process return code; non-zero indicates an error
            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg error for {desc}: {stderr.decode('utf-8')}")
            return stdout
        except ffmpeg.Error as e:
            # Catch errors specifically from ffmpeg-python, which wrap FFmpeg process errors
            raise RuntimeError(f"FFmpeg command failed for {desc}: {e.stderr.decode('utf-8')}")
        except Exception as e:
            # Catch any other unexpected errors
            raise RuntimeError(f"An unexpected error occurred during {desc}: {e}")

    async def get_image(self, video_path: str, timestamp: float = 0.0) -> bytes:
        """
        Get the image with the given video_path and timestamp.
        Args:
            video_path (str): The path to the video file.
            timestamp (float): The timestamp in seconds. Defaults to 0.0.
        Returns:
            bytes: The image data in bytes.
        """
        # Check if the video file exists
        if not os.path.exists(video_path):
            raise FileExistsError(f"Video file not found: {video_path}")

        stream = (
            ffmpeg
            .input(video_path, ss=timestamp)
            .output('pipe:1', vframes=1, format='image2', vcodec='mjpeg', qscale=5)
        )

        result = await self._run_ffmpeg_command(stream, f"get_image from {video_path} at {timestamp}s")

        return result

    async def get_cropped_image(self, video_path: str, top_left: Position, bottom_right: Position,
                                timestamp: float = 0.0) -> bytes:
        """
        Get a cropped image from the video at a specific timestamp.
        Args:
            video_path (str): The path to the video file.
            top_left (Position): The top-left corner of the crop region.
            bottom_right (Position): The bottom-right corner of the crop region.
            timestamp (float): The timestamp in seconds. Defaults to 0.0.
        Returns:
            bytes: The cropped image data in bytes.
        """
        # Check if the video file exists
        if not os.path.exists(video_path):
            raise FileExistsError(f"Video file not found: {video_path}")
        # Check if the coordinates are valid (top_left must be strictly above and to the left of bottom_right)
        if not (top_left.x < bottom_right.x and top_left.y < bottom_right.y):
            raise ValueError("Invalid crop coordinates: top_left must be strictly to the top-left of bottom_right.")

        # Calculate crop dimensions and starting coordinates
        width = bottom_right.x - top_left.x
        height = bottom_right.y - top_left.y
        x = top_left.x
        y = top_left.y

        stream = (
            ffmpeg
            .input(video_path, ss=timestamp)
            .output('pipe:1', vframes=1, vf=f'crop={width}:{height}:{x}:{y}', format='image2', vcodec='mjpeg', qscale=2)
        )
        return await self._run_ffmpeg_command(stream,
                                              f"get_cropped_image from {video_path} at {timestamp}s (crop {x},{y},{width},{height})")
                                              
    async def get_multi_image(self, video_path: str, timestamps: list[float]) -> list[bytes]:
        """
        Get multiple images from the video at different timestamps.
        Args:
            video_path (str): The path to the video file.
            timestamps (list[float]): List of timestamps in seconds.
        Returns:
            list[bytes]: List of image data in bytes, corresponding to each timestamp.
        """
        # Check if the video file exists
        if not os.path.exists(video_path):
            raise FileExistsError(f"Video file not found: {video_path}")
            
        # Check if timestamps is a non-empty list
        if not timestamps:
            raise ValueError("Timestamps list cannot be empty")
            
        # Process each timestamp and collect results
        results = []
        for timestamp in timestamps:
            image_bytes = await self.get_image(video_path, timestamp)
            results.append(image_bytes)
            
        return results
        
    async def get_multi_cropped_image(self, video_path: str, top_left: Position, bottom_right: Position,
                                     timestamps: list[float]) -> list[bytes]:
        """
        Get multiple cropped images from the video at different timestamps.
        Args:
            video_path (str): The path to the video file.
            top_left (Position): The top-left corner of the crop region.
            bottom_right (Position): The bottom-right corner of the crop region.
            timestamps (list[float]): List of timestamps in seconds.
        Returns:
            list[bytes]: List of cropped image data in bytes, corresponding to each timestamp.
        """
        # Check if the video file exists
        if not os.path.exists(video_path):
            raise FileExistsError(f"Video file not found: {video_path}")
            
        # Check if timestamps is a non-empty list
        if not timestamps:
            raise ValueError("Timestamps list cannot be empty")
            
        # Check if the coordinates are valid
        if not (top_left.x < bottom_right.x and top_left.y < bottom_right.y):
            raise ValueError("Invalid crop coordinates: top_left must be strictly to the top-left of bottom_right.")
            
        # Process each timestamp and collect results
        results = []
        for timestamp in timestamps:
            cropped_image_bytes = await self.get_cropped_image(video_path, top_left, bottom_right, timestamp)
            results.append(cropped_image_bytes)
            
        return results


# --- Usage Example ---
async def main():
    screenshot_manager = VideoScreenshot()
    
    # Create temp directories for test files and output
    os.makedirs("./temp", exist_ok=True)
    
    video_file = "./temp/test_video.mp4"  # Use a local path that's guaranteed to exist

    # Create a dummy video file for testing if it doesn't exist
    if not os.path.exists(video_file):
        print(f"Creating a dummy video file '{video_file}' for testing...")
        try:
            # Use ffmpeg to create a simple 5-second black video
            (
                ffmpeg.input('color=black:s=640x480', f='lavfi', t=5)
                .output(video_file, pix_fmt='yuv420p', r=25)
                .run(overwrite_output=True)  # Run synchronously to create the file
            )
            print(f"Dummy video '{video_file}' created.")
        except Exception as e:
            print(f"Failed to create dummy video: {e}")
            print("Please ensure ffmpeg is installed and accessible in your PATH.")
            return

    try:
        # 1. Get a full image
        print(f"Getting full image from '{video_file}' at timestamp 1.5s...")
        full_image_bytes = await screenshot_manager.get_image(video_file, timestamp=1.5)
        with open("./temp/full_screenshot.jpg", "wb") as f:
            f.write(full_image_bytes)
        print("Full image saved to full_screenshot.jpg")

        # 2. Get a cropped image
        print(f"Getting cropped image from '{video_file}' at timestamp 2.0s...")
        top_left_pos = Position(x=100, y=50)
        bottom_right_pos = Position(x=400, y=300)
        cropped_image_bytes = await screenshot_manager.get_cropped_image(
            video_file, top_left_pos, bottom_right_pos, timestamp=2.0
        )
        with open("./temp/cropped_screenshot.jpg", "wb") as f:
            f.write(cropped_image_bytes)
        print("Cropped image saved to cropped_screenshot.jpg")
        
        # 3. Get multiple images
        print(f"Getting multiple images from '{video_file}' at different timestamps...")
        timestamps = [0.5, 1.0, 1.5, 2.0, 2.5]
        multi_images = await screenshot_manager.get_multi_image(video_file, timestamps)
        for i, image_bytes in enumerate(multi_images):
            with open(f"./temp/multi_screenshot_{i}.jpg", "wb") as f:
                f.write(image_bytes)
        print(f"Saved {len(multi_images)} images from multiple timestamps")
        
        # 4. Get multiple cropped images
        print(f"Getting multiple cropped images from '{video_file}' at different timestamps...")
        multi_cropped_images = await screenshot_manager.get_multi_cropped_image(
            video_file, top_left_pos, bottom_right_pos, timestamps
        )
        for i, image_bytes in enumerate(multi_cropped_images):
            with open(f"./temp/multi_cropped_screenshot_{i}.jpg", "wb") as f:
                f.write(image_bytes)
        print(f"Saved {len(multi_cropped_images)} cropped images from multiple timestamps")

        # 5. Test invalid crop coordinates
        print("Testing invalid crop coordinates...")
        try:
            await screenshot_manager.get_cropped_image(
                video_file, Position(x=400, y=300), Position(x=100, y=50), timestamp=0.0
            )
        except ValueError as e:
            print(f"Caught expected error: {e}")
            
        # 6. Test empty timestamps list
        print("Testing empty timestamps list...")
        try:
            await screenshot_manager.get_multi_image(video_file, [])
        except ValueError as e:
            print(f"Caught expected error: {e}")

        # 7. Test non-existent file
        print("Testing non-existent video file...")
        try:
            await screenshot_manager.get_image("non_existent_video.mp4")
        except FileExistsError as e:
            print(f"Caught expected error: {e}")

    except Exception as e:
        print(f"An error occurred during testing: {e}")
    finally:
        # Clean up the dummy video file
        if os.path.exists(video_file):
            print(f"Cleaning up dummy video file '{video_file}'...")
            os.remove(video_file)


if __name__ == "__main__":
    asyncio.run(main())
