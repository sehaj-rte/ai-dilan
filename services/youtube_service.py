import os
import tempfile
import logging
from typing import Dict, Any, List, Optional
import yt_dlp
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class YouTubeService:
    """Service to extract audio from YouTube videos"""
    
    def __init__(self):
        self.max_chunk_size_mb = 20  # Max chunk size for ElevenLabs (20MB to be safe)
        self.chunk_duration_minutes = 10  # Split audio into 10-minute chunks
        self.cookies_file = os.getenv('YOUTUBE_COOKIES_FILE', None)  # Optional cookies file path
    
    def get_video_info(self, youtube_url: str) -> Dict[str, Any]:
        """Get video metadata without downloading"""
        try:
            logger.info(f"Fetching video info for: {youtube_url}")
            print(f"📺 Fetching video info from YouTube...")
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            # Add cookies file if specified
            if self.cookies_file and os.path.exists(self.cookies_file):
                ydl_opts['cookiefile'] = self.cookies_file
                logger.info(f"Using cookies from: {self.cookies_file}")
            else:
                # Try to extract cookies from browser if available (only in development)
                try:
                    # Check if we're in a production environment (common indicators)
                    is_production = (
                        os.getenv('RENDER') or 
                        os.getenv('HEROKU') or 
                        os.getenv('VERCEL') or
                        '/opt/render/' in os.getcwd() or
                        '/app/' in os.getcwd()
                    )
                    
                    if not is_production:
                        ydl_opts['cookiesfrombrowser'] = ('chrome',)
                        logger.info("Using Chrome cookies for authentication")
                    else:
                        logger.info("Production environment detected, skipping browser cookies")
                except Exception as e:
                    # Browser cookies not available, continue without them
                    logger.info(f"Browser cookies not available: {str(e)}")
                    pass
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                
                video_info = {
                    "success": True,
                    "title": info.get('title', 'Unknown'),
                    "duration": info.get('duration', 0),  # in seconds
                    "duration_formatted": self._format_duration(info.get('duration', 0)),
                    "channel": info.get('uploader', 'Unknown'),
                    "description": info.get('description', ''),
                    "thumbnail": info.get('thumbnail', ''),
                    "upload_date": info.get('upload_date', ''),
                    "view_count": info.get('view_count', 0),
                }
                
                logger.info(f"Video info retrieved: {video_info['title']} ({video_info['duration_formatted']})")
                print(f"✅ Video found: {video_info['title']} - {video_info['duration_formatted']}")
                
                return video_info
                
        except Exception as e:
            logger.error(f"Failed to get video info: {str(e)}")
            print(f"❌ Failed to get video info: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to fetch video information: {str(e)}"
            }
    
    def download_audio(self, youtube_url: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Download audio from YouTube video
        
        Args:
            youtube_url: YouTube video URL
            output_path: Optional output path, if None uses temp directory
            
        Returns:
            Dict with success status and audio file path
        """
        try:
            logger.info(f"Starting audio download from: {youtube_url}")
            print(f"⬇️ Downloading audio from YouTube...")
            
            # Create temp directory if no output path specified
            if output_path is None:
                temp_dir = tempfile.mkdtemp()
                output_path = os.path.join(temp_dir, "audio")
            
            # yt-dlp options for audio extraction
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': False,
                'no_warnings': False,
                'progress_hooks': [self._progress_hook],
            }
            
            # Add cookies file if specified
            if self.cookies_file and os.path.exists(self.cookies_file):
                ydl_opts['cookiefile'] = self.cookies_file
                logger.info(f"Using cookies from: {self.cookies_file}")
            else:
                # Try to extract cookies from browser if available (only in development)
                try:
                    # Check if we're in a production environment (common indicators)
                    is_production = (
                        os.getenv('RENDER') or 
                        os.getenv('HEROKU') or 
                        os.getenv('VERCEL') or
                        '/opt/render/' in os.getcwd() or
                        '/app/' in os.getcwd()
                    )
                    
                    if not is_production:
                        ydl_opts['cookiesfrombrowser'] = ('chrome',)
                        logger.info("Using Chrome cookies for authentication")
                    else:
                        logger.info("Production environment detected, skipping browser cookies")
                except Exception as e:
                    # Browser cookies not available, continue without them
                    logger.info(f"Browser cookies not available: {str(e)}")
                    pass
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                
                # The actual output file will have .mp3 extension
                audio_file = f"{output_path}.mp3"
                
                if not os.path.exists(audio_file):
                    raise FileNotFoundError(f"Downloaded audio file not found: {audio_file}")
                
                file_size = os.path.getsize(audio_file)
                
                logger.info(f"Audio downloaded successfully: {audio_file} ({file_size} bytes)")
                print(f"✅ Audio downloaded: {self._format_file_size(file_size)}")
                
                return {
                    "success": True,
                    "audio_path": audio_file,
                    "file_size": file_size,
                    "title": info.get('title', 'Unknown'),
                    "duration": info.get('duration', 0),
                }
                
        except Exception as e:
            logger.error(f"Audio download failed: {str(e)}")
            print(f"❌ Audio download failed: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to download audio: {str(e)}"
            }
    
    def split_audio_into_chunks(self, audio_path: str, chunk_duration_minutes: int = 10) -> List[str]:
        """
        Split audio file into smaller chunks
        
        Args:
            audio_path: Path to audio file
            chunk_duration_minutes: Duration of each chunk in minutes
            
        Returns:
            List of paths to audio chunks
        """
        try:
            logger.info(f"Splitting audio into {chunk_duration_minutes}-minute chunks")
            print(f"✂️ Splitting audio into {chunk_duration_minutes}-minute chunks...")
            
            # Load audio file
            audio = AudioSegment.from_mp3(audio_path)
            
            # Calculate chunk size in milliseconds
            chunk_size_ms = chunk_duration_minutes * 60 * 1000
            
            # Get total duration
            total_duration_ms = len(audio)
            total_chunks = (total_duration_ms // chunk_size_ms) + (1 if total_duration_ms % chunk_size_ms else 0)
            
            logger.info(f"Audio duration: {total_duration_ms/1000:.1f}s, will create {total_chunks} chunks")
            print(f"📊 Audio duration: {self._format_duration(total_duration_ms/1000)}, creating {total_chunks} chunks")
            
            chunk_paths = []
            
            for i in range(0, total_duration_ms, chunk_size_ms):
                chunk_num = (i // chunk_size_ms) + 1
                
                # Extract chunk
                chunk = audio[i:i + chunk_size_ms]
                
                # Create chunk filename
                base_path = os.path.splitext(audio_path)[0]
                chunk_path = f"{base_path}_chunk_{chunk_num}.mp3"
                
                # Export chunk
                chunk.export(chunk_path, format="mp3", bitrate="192k")
                chunk_paths.append(chunk_path)
                
                chunk_size = os.path.getsize(chunk_path)
                logger.info(f"Created chunk {chunk_num}/{total_chunks}: {chunk_path} ({chunk_size} bytes)")
                print(f"✅ Chunk {chunk_num}/{total_chunks}: {self._format_file_size(chunk_size)}")
            
            return chunk_paths
            
        except Exception as e:
            logger.error(f"Failed to split audio: {str(e)}")
            print(f"❌ Failed to split audio: {str(e)}")
            raise
    
    def cleanup_files(self, file_paths: List[str]):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up {file_path}: {str(e)}")
    
    def _progress_hook(self, d):
        """Progress hook for yt-dlp"""
        if d['status'] == 'downloading':
            if 'total_bytes' in d:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                print(f"⬇️ Downloading: {percent:.1f}%", end='\r')
            elif '_percent_str' in d:
                print(f"⬇️ Downloading: {d['_percent_str']}", end='\r')
        elif d['status'] == 'finished':
            print(f"\n✅ Download complete, converting to MP3...")
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to HH:MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

# Create singleton instance
youtube_service = YouTubeService()
