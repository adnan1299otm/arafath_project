\# Islamic Instagram Reels - Video Processing API



FFmpeg-based video processing API for creating Instagram Reels with text overlays.



\## Features

\- ✅ Remove original video audio

\- ✅ Add background music/nasheed

\- ✅ Add text overlays (top, center, bottom)

\- ✅ Resize to 9:16 vertical format (1080x1920)

\- ✅ Trim to max 60 seconds

\- ✅ Export as Instagram-compatible MP4



\## Tech Stack

\- \*\*Backend:\*\* Flask (Python)

\- \*\*Video Processing:\*\* FFmpeg

\- \*\*Text Rendering:\*\* Pillow (PIL)

\- \*\*Deployment:\*\* Railway / Render



---



\## 🚀 Deploy to Railway



\### Step 1: Create Railway Account

1\. Go to \[railway.app](https://railway.app)

2\. Sign up with GitHub



\### Step 2: Deploy from GitHub

1\. Create new GitHub repository

2\. Upload all files:

&nbsp;  - `app.py`

&nbsp;  - `requirements.txt`

&nbsp;  - `Dockerfile`

&nbsp;  - `railway.json`

3\. In Railway dashboard:

&nbsp;  - Click "New Project"

&nbsp;  - Select "Deploy from GitHub repo"

&nbsp;  - Choose your repository

&nbsp;  - Railway will auto-detect Dockerfile



\### Step 3: Configure Environment

\- Railway will automatically set `PORT=8080`

\- No additional env vars needed for basic setup



\### Step 4: Get Public URL

\- Railway will provide: `https://your-app.railway.app`

\- Use this URL in your n8n workflow



---



\## 🧪 Testing Locally



\### Install Dependencies

```bash

pip install -r requirements.txt

```



\### Install FFmpeg

\*\*Ubuntu/Debian:\*\*

```bash

sudo apt-get install ffmpeg

```



\*\*macOS:\*\*

```bash

brew install ffmpeg

```



\*\*Windows:\*\*

Download from \[ffmpeg.org](https://ffmpeg.org/download.html)



\### Run Server

```bash

python app.py

```



Server runs on: `http://localhost:8080`



---



\## 📡 API Endpoints



\### Health Check

```

GET /health

```



\*\*Response:\*\*

```json

{

&nbsp; "status": "healthy",

&nbsp; "service": "Islamic Reels Video Processing API",

&nbsp; "version": "1.0.0"

}

```



\### Create Reel

```

POST /create-reel

Content-Type: application/json

```



\*\*Request Body:\*\*

```json

{

&nbsp; "videoId": "google-drive-video-id",

&nbsp; "musicId": "google-drive-music-id",

&nbsp; "removeOriginalAudio": true,

&nbsp; "maxDuration": 60,

&nbsp; "aspectRatio": "9:16",

&nbsp; "resolution": "1080x1920",

&nbsp; "overlays": {

&nbsp;   "top": {

&nbsp;     "text": "Save the Lost Hadith",

&nbsp;     "fontSize": 26,

&nbsp;     "color": "#FFFFFF",

&nbsp;     "backgroundColor": "rgba(0,0,0,0.5)"

&nbsp;   },

&nbsp;   "center": {

&nbsp;     "text": "The best of you are those who are best to their families.",

&nbsp;     "fontSize": 44,

&nbsp;     "color": "#FFFFFF",

&nbsp;     "backgroundColor": "rgba(0,0,0,0.65)",

&nbsp;     "fontWeight": "bold"

&nbsp;   },

&nbsp;   "bottom": {

&nbsp;     "text": "Source: Tirmidhi 3895",

&nbsp;     "fontSize": 22,

&nbsp;     "color": "#FFFFFF",

&nbsp;     "backgroundColor": "rgba(0,0,0,0.5)"

&nbsp;   }

&nbsp; }

}

```



\*\*Response:\*\*

```json

{

&nbsp; "status": "success",

&nbsp; "videoUrl": "https://your-app.railway.app/outputs/reel\_123.mp4",

&nbsp; "duration": 45,

&nbsp; "audioReplaced": true,

&nbsp; "jobId": "uuid-here"

}

```



---



\## 🔒 Production Improvements



\### Add Authentication

```python

from functools import wraps



API\_KEY = os.environ.get('API\_KEY', 'your-secret-key')



def require\_api\_key(f):

&nbsp;   @wraps(f)

&nbsp;   def decorated(\*args, \*\*kwargs):

&nbsp;       auth = request.headers.get('Authorization', '')

&nbsp;       if not auth.startswith('Bearer ') or auth\[7:] != API\_KEY:

&nbsp;           return jsonify({"error": "Unauthorized"}), 401

&nbsp;       return f(\*args, \*\*kwargs)

&nbsp;   return decorated



@app.route('/create-reel', methods=\['POST'])

@require\_api\_key

def create\_reel():

&nbsp;   # ... existing code

```



\### Add Cloud Storage (AWS S3)

```python

import boto3



s3 = boto3.client('s3',

&nbsp;   aws\_access\_key\_id=os.environ.get('AWS\_ACCESS\_KEY\_ID'),

&nbsp;   aws\_secret\_access\_key=os.environ.get('AWS\_SECRET\_ACCESS\_KEY')

)



def upload\_to\_s3(file\_path, bucket, key):

&nbsp;   s3.upload\_file(file\_path, bucket, key, ExtraArgs={'ACL': 'public-read'})

&nbsp;   return f"https://{bucket}.s3.amazonaws.com/{key}"

```



---



\## 📊 Resource Usage



\*\*Estimated per video:\*\*

\- CPU: 30-60 seconds processing time

\- RAM: 200-500 MB

\- Storage: 50-100 MB temporary



\*\*Railway Free Tier:\*\*

\- 500 hours/month

\- Can process ~500-1000 videos/month



---



\## 🐛 Troubleshooting



\### FFmpeg not found

\- Ensure Dockerfile installs ffmpeg correctly

\- Railway should automatically include it



\### Memory issues

\- Reduce video quality in FFmpeg command

\- Use `-preset ultrafast` for faster processing



\### Timeout errors

\- Increase gunicorn timeout: `--timeout 600`



---



\## 📝 License

MIT License - Free to use for Islamic content creation

