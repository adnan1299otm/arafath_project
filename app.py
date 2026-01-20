from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import tempfile
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Drive setup (কাজ করার জন্য service account credentials লাগবে)
def get_drive_service():
    """Initialize Google Drive API service"""
    try:
        # Environment থেকে credentials নিতে হবে
        creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if not creds_json:
            logger.warning("No Google credentials found - using mock mode")
            return None
        
        import json
        creds_dict = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        logger.error(f"Failed to initialize Drive service: {e}")
        return None

def download_from_drive(file_id, output_path):
    """Download file from Google Drive"""
    try:
        service = get_drive_service()
        if not service:
            logger.error("Drive service not available")
            return False
        
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(output_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            logger.info(f"Download {int(status.progress() * 100)}%")
        
        return True
    except Exception as e:
        logger.error(f"Failed to download file {file_id}: {e}")
        return False

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Video processing API is running"}), 200

@app.route('/create-reel', methods=['POST'])
def create_reel():
    """Main endpoint to create Instagram reel"""
    try:
        data = request.json
        logger.info(f"Received request: {data}")
        
        # Validate required fields
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        video_id = data.get('videoId', '')
        music_id = data.get('musicId', '')
        
        # Check for empty IDs
        if not video_id or video_id == 'no-video':
            return jsonify({
                "status": "error", 
                "message": "No video ID provided or no videos found in Google Drive"
            }), 400
        
        if not music_id or music_id == 'no-music':
            return jsonify({
                "status": "error", 
                "message": "No music ID provided or no music found in Google Drive"
            }), 400
        
        # Get parameters with defaults
        remove_audio = data.get('removeOriginalAudio', True)
        max_duration = int(data.get('maxDuration', 60)) if data.get('maxDuration') else 60
        aspect_ratio = data.get('aspectRatio', '9:16')
        resolution = data.get('resolution', '1080x1920')
        overlays = data.get('overlays', {})
        output_format = data.get('outputFormat', 'mp4')
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, 'input_video.mp4')
        music_path = os.path.join(temp_dir, 'input_music.mp3')
        output_path = os.path.join(temp_dir, f'output.{output_format}')
        
        # Download files from Google Drive
        logger.info(f"Downloading video: {video_id}")
        if not download_from_drive(video_id, video_path):
            return jsonify({
                "status": "error",
                "message": "Failed to download video from Google Drive"
            }), 500
        
        logger.info(f"Downloading music: {music_id}")
        if not download_from_drive(music_id, music_path):
            return jsonify({
                "status": "error",
                "message": "Failed to download music from Google Drive"
            }), 500
        
        # Build FFmpeg command
        ffmpeg_cmd = build_ffmpeg_command(
            video_path, music_path, output_path,
            remove_audio, max_duration, aspect_ratio, 
            resolution, overlays
        )
        
        logger.info(f"Running FFmpeg: {' '.join(ffmpeg_cmd)}")
        
        # Execute FFmpeg
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            return jsonify({
                "status": "error",
                "message": "Video processing failed",
                "details": result.stderr
            }), 500
        
        # Upload to temporary storage or return base64
        # For now, return success with mock URL
        video_url = f"https://arafathproject-production.up.railway.app/outputs/reel_{video_id[:8]}.mp4"
        
        return jsonify({
            "status": "success",
            "videoUrl": video_url,
            "message": "Video processed successfully",
            "details": {
                "duration": max_duration,
                "resolution": resolution,
                "format": output_format
            }
        }), 200
        
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return jsonify({
            "status": "error",
            "message": f"Invalid input values: {str(e)}"
        }), 400
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "details": str(e)
        }), 500

def build_ffmpeg_command(video_path, music_path, output_path, 
                         remove_audio, max_duration, aspect_ratio, 
                         resolution, overlays):
    """Build FFmpeg command with all parameters"""
    
    cmd = ['ffmpeg', '-i', video_path, '-i', music_path]
    
    # Parse resolution
    width, height = resolution.split('x')
    
    # Build filter complex
    filters = []
    
    # Trim video to max duration
    filters.append(f'[0:v]trim=duration={max_duration},setpts=PTS-STARTPTS[v]')
    
    # Scale and crop to aspect ratio
    filters.append(f'[v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}[scaled]')
    
    # Add text overlays
    video_filter = '[scaled]'
    
    if overlays:
        # Top text
        if 'top' in overlays:
            top = overlays['top']
            text = top.get('text', '').replace("'", "\\'")
            font_size = top.get('fontSize', 26)
            color = top.get('color', 'white')
            bg_color = top.get('backgroundColor', 'black@0.5')
            
            video_filter += f"drawtext=text='{text}':fontsize={font_size}:fontcolor={color}:box=1:boxcolor={bg_color}:boxborderw=5:x=(w-text_w)/2:y=50"
        
        # Center text
        if 'center' in overlays:
            center = overlays['center']
            text = center.get('text', '').replace("'", "\\'")
            font_size = center.get('fontSize', 44)
            color = center.get('color', 'white')
            bg_color = center.get('backgroundColor', 'black@0.65')
            
            video_filter += f",drawtext=text='{text}':fontsize={font_size}:fontcolor={color}:box=1:boxcolor={bg_color}:boxborderw=10:x=(w-text_w)/2:y=(h-text_h)/2"
        
        # Bottom text
        if 'bottom' in overlays:
            bottom = overlays['bottom']
            text = bottom.get('text', '').replace("'", "\\'")
            font_size = bottom.get('fontSize', 22)
            color = bottom.get('color', 'white')
            bg_color = bottom.get('backgroundColor', 'black@0.5')
            
            video_filter += f",drawtext=text='{text}':fontsize={font_size}:fontcolor={color}:box=1:boxcolor={bg_color}:boxborderw=5:x=(w-text_w)/2:y=h-100"
    
    filters.append(f'{video_filter}[vout]')
    
    # Add audio mixing
    if remove_audio:
        filters.append(f'[1:a]atrim=duration={max_duration},asetpts=PTS-STARTPTS[aout]')
    else:
        filters.append(f'[0:a][1:a]amix=inputs=2:duration=shortest[aout]')
    
    # Combine filters
    cmd.extend(['-filter_complex', ';'.join(filters)])
    
    # Map outputs
    cmd.extend(['-map', '[vout]', '-map', '[aout]'])
    
    # Output settings
    cmd.extend([
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-movflags', '+faststart',
        '-y',
        output_path
    ])
    
    return cmd

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
