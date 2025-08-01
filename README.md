# Instagram Reel Authenticity Checker

## Setup Instructions

After cloning the repository, follow these steps to set up the project:

### 1. Create Environment File
Create a `.env` file in the root directory with your Google Gemini API key:

```.env
GOOGLE_API_KEY="your gemini api key"
```

### 2. Set Up Virtual Environment
Open Command Prompt or PowerShell and run:
```bash
python -m venv venv
```

### 3. Activate Virtual Environment
**On Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**On Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
uvicorn main:app --reload
```

The application will be available at `http://localhost:8000`

## Base URL

```
http://localhost:8000
```

## API Endpoints

### 1. Get Instagram Reel/Post Video Information

Retrieves video information from Instagram URLs including video URL, dimensions, and metadata.

**Endpoint:** `GET /api/getLink`

**Query Parameters:**
- `url` (required): Instagram post, reel, or share URL

**Supported URL Formats:**
- `https://www.instagram.com/p/{post-id}/`
- `https://www.instagram.com/reel/{reel-id}/`
- `https://www.instagram.com/reels/{reel-id}/`
- `https://www.instagram.com/share/{share-id}/`

#### Request Example

```bash
GET http://localhost:8000/api/getLink?url=https://www.instagram.com/p/ABC123/
```

#### Response Format

**Success Response (200 OK):**
```json
{
  "filename": "instagram_video_1703123456789.mp4",
  "width": "1080",
  "height": "1920",
  "videoUrl": "https://scontent.cdninstagram.com/v/t66.30100-16/12345678_n.mp4"
}
```

**Error Responses:**

**400 Bad Request - Invalid URL:**
```json
{
  "error": "Invalid Instagram URL"
}
```

**400 Bad Request - URL Validation Error:**
```json
{
  "error": "URL does not match Instagram post, reel, or share format"
}
```

**400 Bad Request - Missing URL:**
```json
{
  "error": "URL is required"
}
```

**400 Bad Request - Invalid Post URL:**
```json
{
  "error": "Invalid Post URL - Could not extract ID"
}
```

**400 Bad Request - Video Not Accessible:**
```json
{
  "error": "Video link for this post is not public or accessible."
}
```

**500 Internal Server Error:**
```json
{
  "error": "Failed to fetch Instagram page: 404"
}
```

### 2. Download and Compress Video

Downloads a video from a URL and compresses it for storage.

**Endpoint:** `POST /api/downloadAndCompress`

**Request Body:**
```json
{
  "url": "https://scontent.cdninstagram.com/v/t66.30100-16/12345678_n.mp4",
  "filename": "instagram_video_1703123456789.mp4"
}
```

**Request Fields:**
- `url` (required): Direct URL to the video file
- `filename` (required): Name for the downloaded file

#### Request Example

```bash
curl -X POST http://localhost:8000/api/downloadAndCompress \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://scontent.cdninstagram.com/v/t66.30100-16/12345678_n.mp4",
    "filename": "instagram_video_1703123456789.mp4"
  }'
```

#### Response Format

**Success Response (200 OK):**
```json
{
  "success": true,
  "path": "/reels/instagram_video_1703123456789.mp4"
}
```

**Error Responses:**

**400 Bad Request - Missing Parameters:**
```json
{
  "error": "URL and filename are required"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Failed to download and compress reel"
}
```

### 3. Generate Video Description

Generates a description from a video file using AI analysis.

**Endpoint:** `POST /api/videoDescription`

**Request Body:**
```json
{
  "videoUrl": "/reels/instagram_video_1703123456789.mp4"
}
```

**Request Fields:**
- `videoUrl` (required): Path to the video file

#### Request Example

```bash
curl -X POST http://localhost:8000/api/videoDescription \
  -H "Content-Type: application/json" \
  -d '{
    "videoUrl": "/reels/instagram_video_1703123456789.mp4"
  }'
```

#### Response Format

**Success Response (200 OK):**
```json
{
  "description": "This video shows a person dancing to upbeat music in a well-lit room..."
}
```

**Error Responses:**

**500 Internal Server Error:**
```json
{
  "error": "Failed to generate video description",
  "details": "Error details here"
}
```

### 4. Process Reel (Combined Endpoint)

Performs the complete workflow: retrieves video information, downloads and compresses the video, then generates a description.

**Endpoint:** `POST /api/processReel`

**Request Body:**
```json
{
  "url": "https://www.instagram.com/p/ABC123/"
}
```

**Request Fields:**
- `url` (required): Instagram post, reel, or share URL

#### Request Example

```bash
curl -X POST http://localhost:8000/api/processReel \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.instagram.com/p/ABC123/"
  }'
```

#### Response Format

**Success Response (200 OK):**
```json
{
  "success": true,
  "description": "This video shows a person dancing to upbeat music in a well-lit room..."
}
```

**Error Responses:**

**400 Bad Request - Missing URL:**
```json
{
  "error": "URL is required"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Failed to process reel"
}
```

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `filename` | String | Unique filename for the video (timestamp-based) |
| `width` | String | Video width in pixels |
| `height` | String | Video height in pixels |
| `videoUrl` | String | Direct URL to the video file |
| `success` | Boolean | Indicates if the operation was successful |
| `path` | String | File path where the video was saved |
| `description` | String | AI-generated description of the video content |
