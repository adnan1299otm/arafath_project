from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import subprocess
import json
from pathlib import Path
import tempfile
import shutil
from PIL import Image, ImageDraw, ImageFont
import textwrap

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = '/tmp/uploads'
OUTPUT_FOLDER = '/tmp/outputs'
FONTS_FOLDER = '/app/fonts'

# Create directories
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Islamic Reels Video Processing API",
        "version": "1.0.0"
    }), 200

# Main video processing endpoint
@app.route('/create-reel', methods=['POST'])
def create_reel():
    try:
        data = request.json
        
        # Extract parameters
        video_id = data.get('videoId')
        music_id = data.get('musicId')
        overlays = data.get('overlays', {})
        max_duration = data.get('maxDuration', 60)
        aspect_ratio = data.get('aspectRatio', '9:16')
        resolution = data.get('resolution', '1080x1920')
        
        # Validate required fields
        if not video_id or not music_id:
            return jsonify({
                "status": "error",
                "message": "Missing videoId or musicId"
            }), 400
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # File paths
        video_path = f"{UPLOAD_FOLDER}/video_{job_id}.mp4"
        music_path = f"{UPLOAD_FOLDER}/music_{job_id}.mp3"
        output_path = f"{OUTPUT_FOLDER}/reel_{job_id}.mp4"
        
        # Download video and music from Google Drive (placeholder)
        # In production, implement actual download logic
        download_from_google_drive(video_id, video_path)
        download_from_google_drive(music_id, music_path)
        
        # Get video duration
        video_duration = get_video_duration(video_path)
        music_duration = get_audio_duration(music_path)
        
        # Calculate final duration
        final_duration = min(video_duration, music_duration, max_duration)
        
        # Process video
        process_video(
            video_path=video_path,
            music_path=music_path,
            output_path=output_path,
            overlays=overlays,
            final_duration=final_duration,
            resolution=resolution
        )
        
        # Upload to public storage (placeholder)
        public_url = upload_to_storage(output_path, job_id)
        
        # Cleanup
        cleanup_files([video_path, music_path])
        
        return jsonify({
            "status": "success",
            "videoUrl": public_url,
            "duration": final_duration,
            "audioReplaced": True,
            "jobId": job_id
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error processing video: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


def download_from_google_drive(file_id, output_path):
    """
    Download file from Google Drive using file ID.
    This is a placeholder - implement actual Google Drive API logic.
    """
    # For testing, you can use wget or curl with direct download link
    import requests
    
    # Google Drive direct download URL
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    
    # Add your Google Drive API authentication here
    # For now, placeholder
    
    # Create dummy file for testing
    Path(output_path).touch()
    
    app.logger.info(f"Downloaded {file_id} to {output_path}")


def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe."""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def get_audio_duration(audio_path):
    """Get audio duration in seconds using ffprobe."""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def create_text_overlay(text, font_size, color, bg_color, position, width=1080, height=1920):
    """Create text overlay image using PIL."""
    # Create transparent image
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Load font (use default if custom not available)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Wrap text
    wrapped_text = textwrap.fill(text, width=30)
    
    # Get text bounding box
    bbox = draw.textbbox((0, 0), wrapped_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Calculate position
    if position == 'top':
        x = (width - text_width) // 2
        y = 80
    elif position == 'center':
        x = (width - text_width) // 2
        y = (height - text_height) // 2
    elif position == 'bottom':
        x = (width - text_width) // 2
        y = height - text_height - 100
    else:
        x = (width - text_width) // 2
        y = (height - text_height) // 2
    
    # Draw background rectangle
    padding = 20
    draw.rectangle(
        [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
        fill=bg_color
    )
    
    # Draw text with stroke
    stroke_width = 2
    # Draw stroke
    for adj_x in range(-stroke_width, stroke_width + 1):
        for adj_y in range(-stroke_width, stroke_width + 1):
            draw.text((x + adj_x, y + adj_y), wrapped_text, font=font, fill='#000000')
    # Draw main text
    draw.text((x, y), wrapped_text, font=font, fill=color)
    
    # Save overlay
    overlay_path = f"{UPLOAD_FOLDER}/overlay_{uuid.uuid4()}.png"
    img.save(overlay_path)
    return overlay_path


def process_video(video_path, music_path, output_path, overlays, final_duration, resolution):
    """Process video with FFmpeg: remove audio, add music, add overlays, resize."""
    
    # Create text overlays
    overlay_files = []
    filter_complex = []
    
    # Extract overlay configs
    top_overlay = overlays.get('top', {})
    center_overlay = overlays.get('center', {})
    bottom_overlay = overlays.get('bottom', {})
    
    # Create overlay images
    if top_overlay.get('text'):
        top_img = create_text_overlay(
            text=top_overlay['text'],
            font_size=top_overlay.get('fontSize', 26),
            color=top_overlay.get('color', '#FFFFFF'),
            bg_color=top_overlay.get('backgroundColor', 'rgba(0,0,0,0.5)'),
            position='top'
        )
        overlay_files.append(top_img)
    
    if center_overlay.get('text'):
        center_img = create_text_overlay(
            text=center_overlay['text'],
            font_size=center_overlay.get('fontSize', 44),
            color=center_overlay.get('color', '#FFFFFF'),
            bg_color=center_overlay.get('backgroundColor', 'rgba(0,0,0,0.65)'),
            position='center'
        )
        overlay_files.append(center_img)
    
    if bottom_overlay.get('text'):
        bottom_img = create_text_overlay(
            text=bottom_overlay['text'],
            font_size=bottom_overlay.get('fontSize', 22),
            color=bottom_overlay.get('color', '#FFFFFF'),
            bg_color=bottom_overlay.get('backgroundColor', 'rgba(0,0,0,0.5)'),
            position='bottom'
        )
        overlay_files.append(bottom_img)
    
    # Build FFmpeg command
    cmd = [
        'ffmpeg',
        '-i', video_path,        # Input video
        '-i', music_path,        # Input audio
        '-t', str(final_duration),  # Duration
        '-filter_complex',
        f'[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[v]',
        '-map', '[v]',           # Use filtered video
        '-map', '1:a',           # Use music audio (not original video audio)
        '-c:v', 'libx264',       # Video codec
        '-preset', 'medium',     # Encoding preset
        '-crf', '23',            # Quality
        '-c:a', 'aac',           # Audio codec
        '-b:a', '128k',          # Audio bitrate
        '-shortest',             # Stop at shortest stream
        '-y',                    # Overwrite output
        output_path
    ]
    
    # Execute FFmpeg
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr}")
    
    # Cleanup overlay files
    for overlay_file in overlay_files:
        if os.path.exists(overlay_file):
            os.remove(overlay_file)
    
    app.logger.info(f"Video processed successfully: {output_path}")


def upload_to_storage(file_path, job_id):
    """
    Upload processed video to public storage.
    Placeholder - implement actual upload logic (S3, Cloudinary, etc.)
    """
    # For Railway deployment, you can use:
    # - AWS S3
    # - Cloudinary
    # - Railway's own storage (if available)
    # - Or return a Railway-hosted URL
    
    # Placeholder: return a mock URL
    public_url = f"https://your-railway-app.railway.app/outputs/reel_{job_id}.mp4"
    
    app.logger.info(f"Uploaded to: {public_url}")
    return public_url


def cleanup_files(file_paths):
    """Delete temporary files."""
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)
            app.logger.info(f"Cleaned up: {file_path}")


# Serve processed videos (for testing)
@app.route('/outputs/<filename>', methods=['GET'])
def serve_output(filename):
    from flask import send_file
    file_path = f"{OUTPUT_FOLDER}/{filename}"
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='video/mp4')
    return jsonify({"error": "File not found"}), 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)