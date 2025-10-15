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
        self.cookies_file = os.getenv('YOUTUBE_COOKIES_FILE', 'cookies.txt')  # Configurable cookies file path
        self.youtube_cookies_txt = "YOUTUBE_COOKIES.txt"  # Alternative cookies file
        self.cookies_content = os.getenv('YOUTUBE_COOKIES_CONTENT')  # Cookies content as env var
    
    def _create_cookies_file_from_env(self) -> Optional[str]:
        """Create temporary cookies file from environment variable content"""
        if not self.cookies_content:
            return None
        
        try:
            import tempfile
            temp_cookies_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_cookies_file.write(self.cookies_content)
            temp_cookies_file.close()
            logger.info(f"Created temporary cookies file: {temp_cookies_file.name}")
            return temp_cookies_file.name
        except Exception as e:
            logger.error(f"Failed to create cookies file from environment: {str(e)}")
            return None
    
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
            
            # Try multiple cookie sources in order of preference
            cookies_used = False
            
            # 1. Try primary cookies file
            if self.cookies_file and os.path.exists(self.cookies_file):
                ydl_opts['cookiefile'] = self.cookies_file
                logger.info(f"Using cookies from: {self.cookies_file}")
                cookies_used = True
            # 2. Try alternative cookies file
            elif os.path.exists(self.youtube_cookies_txt):
                ydl_opts['cookiefile'] = self.youtube_cookies_txt
                logger.info(f"Using cookies from: {self.youtube_cookies_txt}")
                cookies_used = True
            else:
                # 3. Try to extract cookies from browser if available (only in development)
                try:
                    # Check if we're in a production environment
                    is_production = (
                        os.getenv('RENDER') or 
                        os.getenv('HEROKU') or 
                        os.getenv('VERCEL') or
                        '/opt/render/' in os.getcwd() or
                        '/app/' in os.getcwd()
                    )
                    
                    if not is_production:
                        # Try multiple browsers
                        for browser in ['chrome', 'firefox', 'edge', 'safari']:
                            try:
                                ydl_opts['cookiesfrombrowser'] = (browser,)
                                logger.info(f"Attempting to use {browser} cookies for authentication")
                                cookies_used = True
                                break
                            except Exception as browser_e:
                                logger.debug(f"Failed to get {browser} cookies: {str(browser_e)}")
                                continue
                    else:
                        logger.info("Production environment detected, skipping browser cookies")
                except Exception as e:
                    logger.info(f"Browser cookies not available: {str(e)}")
                    pass
            
            if not cookies_used:
                logger.warning("No cookies available - may encounter access restrictions for some videos")
            
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
            error_msg = str(e)
            logger.error(f"Failed to get video info: {error_msg}")
            print(f"❌ Failed to get video info: {error_msg}")
            
            # Provide more helpful error messages for common authentication issues
            if "Sign in to confirm you're not a bot" in error_msg or "cookies" in error_msg.lower():
                user_friendly_error = (
                    "This video requires authentication. Please ensure you have valid YouTube cookies configured. "
                    "You may need to export fresh cookies from your browser while logged into YouTube."
                )
            elif "Private video" in error_msg:
                user_friendly_error = "This is a private video that cannot be accessed."
            elif "Video unavailable" in error_msg:
                user_friendly_error = "This video is unavailable or has been removed."
            elif "age-restricted" in error_msg.lower():
                user_friendly_error = "This age-restricted video requires authentication. Please configure YouTube cookies."
            else:
                user_friendly_error = f"Failed to fetch video information: {error_msg}"
            
            return {
                "success": False,
                "error": user_friendly_error
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
            
            # Try multiple cookie sources in order of preference
            cookies_used = False
            
            # 1. Try primary cookies file
            if self.cookies_file and os.path.exists(self.cookies_file):
                ydl_opts['cookiefile'] = self.cookies_file
                logger.info(f"Using cookies from: {self.cookies_file}")
                cookies_used = True
            # 2. Try alternative cookies file
            elif os.path.exists(self.youtube_cookies_txt):
                ydl_opts['cookiefile'] = self.youtube_cookies_txt
                logger.info(f"Using cookies from: {self.youtube_cookies_txt}")
                cookies_used = True
            else:
                # 3. Try to extract cookies from browser if available (only in development)
                try:
                    # Check if we're in a production environment
                    is_production = (
                        os.getenv('RENDER') or 
                        os.getenv('HEROKU') or 
                        os.getenv('VERCEL') or
                        '/opt/render/' in os.getcwd() or
                        '/app/' in os.getcwd()
                    )
                    
                    if not is_production:
                        # Try multiple browsers
                        for browser in ['chrome', 'firefox', 'edge', 'safari']:
                            try:
                                ydl_opts['cookiesfrombrowser'] = (browser,)
                                logger.info(f"Attempting to use {browser} cookies for authentication")
                                cookies_used = True
                                break
                            except Exception as browser_e:
                                logger.debug(f"Failed to get {browser} cookies: {str(browser_e)}")
                                continue
                    else:
                        logger.info("Production environment detected, skipping browser cookies")
                except Exception as e:
                    logger.info(f"Browser cookies not available: {str(e)}")
                    pass
            
            if not cookies_used:
                logger.warning("No cookies available - may encounter access restrictions for some videos")
            
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
            error_msg = str(e)
            logger.error(f"Audio download failed: {error_msg}")
            print(f"❌ Audio download failed: {error_msg}")
            
            # Provide more helpful error messages for common authentication issues
            if "Sign in to confirm you're not a bot" in error_msg or "cookies" in error_msg.lower():
                user_friendly_error = (
                    "This video requires authentication. Please ensure you have valid YouTube cookies configured. "
                    "You may need to export fresh cookies from your browser while logged into YouTube."
                )
            elif "Private video" in error_msg:
                user_friendly_error = "This is a private video that cannot be accessed."
            elif "Video unavailable" in error_msg:
                user_friendly_error = "This video is unavailable or has been removed."
            elif "age-restricted" in error_msg.lower():
                user_friendly_error = "This age-restricted video requires authentication. Please configure YouTube cookies."
            else:
                user_friendly_error = f"Failed to download audio: {error_msg}"
            
            return {
                "success": False,
                "error": user_friendly_error
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
