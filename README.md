## AI Pipeline (Default)

The bot now uses **Google nano-banana AI** as the default image generation method, with automatic fallback to placeholder processing on any AI errors.

- **FIRST image**: `CRYBB_STYLE_URL` (public URL to `assets/crybb.jpeg`)
- **SECOND image**: target user's PFP URL
- **Prompt (fixed)**:

```
change the clothes of the first character to the clothes of the character in the second image, if needed change his hair color, skin color, eyes color and tattoos in case they are different from the original image. keep the style consistent to the one in the first image. VERY IMPORTANT, always keep the tears. Keep the identity cues and overall composition from the second image.
```

- **Required env**: `REPLICATE_API_TOKEN`, `CRYBB_STYLE_URL`, `IMAGE_PIPELINE=ai`

Quick test:

```bash
export REPLICATE_API_TOKEN=...
export CRYBB_STYLE_URL=https://<your-host>/crybb.jpeg
export IMAGE_PIPELINE=ai
python3 tools/run_ai_smoke.py --pfp-url "https://pbs.twimg.com/profile_images/..."
```

## Project Status

This project has been **lean-down optimized**:

- ✅ Removed unused overlay/facial recognition code
- ✅ Consolidated Twitter client implementations
- ✅ Streamlined to AI-first pipeline with placeholder fallback
- ✅ Eliminated dead test files and unused dependencies
- ✅ Production-ready with minimal footprint

# CryBB Maker Bot

A production-ready Twitter bot that transforms profile pictures with custom overlays or placeholder effects.

## Features

- 🐦 Listens for mentions to `@crybbmaker`
- 🎨 Applies custom overlay (if `overlay.png` exists) or placeholder effects
- ⚡ Real-time processing and replies
- 🚦 Built-in rate limiting (5 requests per user per hour)
- 🏥 Health check endpoint for PaaS deployment
- 🖥️ DigitalOcean droplet ready
- 🧪 Comprehensive test suite

## Getting Started

### Prerequisites

- Python 3.11+
- Twitter Developer Account with API access
- DigitalOcean account (for production deployment)

### Quick Start

1. **Clone and setup:**

   ```bash
   git clone <your-repo>
   cd crybbmaker-bot
   make setup
   ```

2. **Configure environment:**

   ```bash
   # Edit .env file with your Twitter API credentials
   nano .env
   ```

3. **Install dependencies:**

   ```bash
   make install
   ```

4. **Run the bot:**
   ```bash
   make run
   ```

### Environment Configuration

Copy `env.example` to `.env` and fill in your Twitter API credentials:

```bash
API_KEY=your_api_key
API_SECRET=your_api_secret
ACCESS_TOKEN=your_access_token
ACCESS_SECRET=your_access_secret
BEARER_TOKEN=your_bearer_token
BOT_HANDLE=crybbmaker
POLL_SECONDS=15
PORT=8000
```

### Testing

Run the test suite:

```bash
make test
```

## DigitalOcean Deployment

### 1. Create Droplet

1. **Create a new droplet:**

   - Choose Ubuntu 22.04 LTS
   - Select appropriate size (Basic $6/month is sufficient)
   - Add your SSH key
   - Enable monitoring

2. **Connect to your droplet:**
   ```bash
   ssh root@YOUR_DROPLET_IP
   ```

### 2. Initial Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/YOURUSERNAME/crybb-bot.git /opt/crybb-bot
   ```

2. **Run the deployment script:**

   ```bash
   cd /opt/crybb-bot
   chmod +x scripts/deploy.sh
   ./scripts/deploy.sh
   ```

3. **Upload your .env file:**

   ```bash
   # From your local machine
   scp .env root@YOUR_DROPLET_IP:/tmp/.env

   # On the droplet
   sudo cp /tmp/.env /opt/crybb-bot/.env
   sudo chown root:root /opt/crybb-bot/.env
   sudo chmod 600 /opt/crybb-bot/.env
   ```

   **Important:** The `.env` file must be located at `/opt/crybb-bot/.env` on the droplet. The systemd service reads it via `EnvironmentFile=/opt/crybb-bot/.env`.

4. **Run security hardening:**
   ```bash
   chmod +x scripts/harden.sh
   ./scripts/harden.sh
   ```

### 3. Service Management

The bot runs as a systemd service. Use these commands to manage it:

```bash
# Check status
sudo systemctl status crybb-bot

# View logs
journalctl -u crybb-bot -f

# Restart bot
sudo systemctl restart crybb-bot

# Stop bot
sudo systemctl stop crybb-bot

# Start bot
sudo systemctl start crybb-bot
```

### 4. Verify Configuration

After deployment, verify that your environment variables are loaded correctly:

```bash
# Check service logs for configuration status
journalctl -u crybb-bot -f | grep -E "CONFIG:|Boot:"

# Expected output should show:
# CONFIG: IMAGE_PIPELINE=ai
# CONFIG: CRYBB_STYLE_URL=https://crybb-assets-...crybb.jpeg
# CONFIG: REPLICATE_API_TOKEN=r8_...
# CONFIG: AI pipeline validation passed
# Boot: env loaded, proceeding with pipeline init
```

If you see `<missing>` for `CRYBB_STYLE_URL`, the `.env` file is not being loaded properly. Check:

- File exists: `ls -la /opt/crybb-bot/.env`
- Service configuration: `systemctl cat crybb-bot | grep EnvironmentFile`

### 5. Updates

To update the bot with new code:

```bash
# Quick update script
chmod +x scripts/update.sh
./scripts/update.sh
```

Or manually:

```bash
cd /opt/crybb-bot
sudo git pull
sudo systemctl restart crybb-bot
```

### 5. Monitoring

- **Health check:** `curl http://localhost:8000/health`
- **Metrics:** `curl http://localhost:8000/metrics`
- **Logs:** `journalctl -u crybb-bot -f`

## Usage

### Basic Usage

Tweet a mention to your bot:

```
@crybbmaker @jack make me crybb
```

The bot will:

1. Extract `@jack` as the target
2. Download Jack's profile picture
3. Apply transformation (overlay or placeholder)
4. Reply with the processed image

### Target Extraction

- **With target:** `@crybbmaker @username make me crybb` → processes `@username`
- **Without target:** `@crybbmaker make me crybb` → processes the author's profile

### Custom Branding

To add your custom overlay:

1. Create a transparent PNG file named `overlay.png`
2. Place it in the project root
3. The bot will automatically use it for all transformations

The overlay will be:

- Scaled to 60% of the profile picture width
- Centered horizontally
- Positioned at 35% from the top

### Placement Modes

```
PLACEMENT_MODE=auto         # landmarks → static fallback
LANDMARK_SCALE_K=2.4
LANDMARK_Y_OFFSET_K=0.10
```

## Architecture

### Project Structure

```
crybbmaker-bot/
├── src/
│   ├── main.py              # Main processing loop
│   ├── config.py            # Configuration management
│   ├── twitter_client.py   # Twitter API client
│   ├── image_processor.py   # Image transformation
│   ├── rate_limiter.py      # Rate limiting
│   ├── storage.py          # Persistence layer
│   ├── server.py           # FastAPI health server
│   └── utils.py            # Utility functions
├── scripts/                 # Deployment scripts
│   ├── deploy.sh           # Initial deployment
│   ├── update.sh           # Quick updates
│   └── harden.sh           # Security hardening
├── tests/                   # Test suite
├── overlay.png             # Optional custom overlay
├── requirements.txt        # Dependencies
└── Makefile               # Development commands
```

### Key Components

- **Twitter Client:** Handles API authentication and interactions using Tweepy v1.1 and v2
- **Image Processor:** Applies overlays or placeholder effects with Pillow
- **Rate Limiter:** In-memory sliding window rate limiting
- **Storage:** JSON-based persistence for `since_id` tracking
- **Health Server:** FastAPI endpoint for PaaS health checks

## API Endpoints

- `GET /health` - Health check endpoint
- `GET /metrics` - Basic metrics and status

## Rate Limiting

- **Limit:** 5 requests per user per hour
- **Window:** Sliding 1-hour window
- **Storage:** In-memory (resets on restart)

## Error Handling

The bot handles various error scenarios gracefully:

- **Rate limit exceeded:** Friendly throttle message
- **Profile image not found:** Error message with fallback image
- **Processing errors:** Generic error message
- **API errors:** Automatic retry with exponential backoff

### Retries

API and HTTP calls are retried with exponential backoff and jitter. Rate limits (TooManyRequests) are respected with sleep before retrying.

## Local Overlay Testing

## Backend Verification (No Posting)

Run capability probe:

```bash
python tools/probe_x_api.py
```

If mentions or media upload are blocked by your API tier, use safer modes:

```bash
# mock, fully offline
export TWITTER_MODE=mock
python tools/simulate_once.py
ls outbox/*/media.jpg

# dryrun, live reads (if keys), no posts
export TWITTER_MODE=dryrun
python tools/simulate_once.py
open outbox/*/reply.json
```

Test overlay placement and styling without Twitter API:

1. **Setup test images:**

   ```bash
   # Create test directory and add sample images
   mkdir -p test_images
   # Add your .png/.jpg/.jpeg files to test_images/
   ```

2. **Run overlay tests:**

   ```bash
   cd crybb
   python test_overlay.py --grayscale yes --scale 0.6 --y-factor 0.35
   ```

3. **View results:**
   - Processed images: `test_output/overlay_*.jpg`
   - Contact sheet: `test_output/contact_sheet.jpg`

### Test Options

- `--overlay Crybb.png` - Overlay image path (default: Crybb.png)
- `--grayscale yes|no` - Convert base images to grayscale
- `--smart-placement auto|on|off` - Use OpenCV for face detection
- `--scale 0.60` - Overlay scale factor (0-1)
- `--y-factor 0.35` - Vertical position (0-1)

### Smart Placement

If OpenCV is installed, the script can detect faces and position overlays above the eye line:

```bash
pip install opencv-python  # Optional dependency
python test_overlay.py --smart-placement on
```

## Development

### Adding Features

The codebase is designed for easy extension:

1. **New image effects:** Extend `ImageProcessor` class
2. **Different storage:** Implement new `Storage` backend
3. **Enhanced rate limiting:** Modify `RateLimiter` class
4. **Additional APIs:** Extend `TwitterClient` class

### Future Enhancements

- [ ] Mediapipe face landmarks for precise overlay placement
- [ ] Opt-out list and admin blocklist
- [ ] Redis/SQLite storage for production
- [ ] Webhook ingestion (Account Activity API)
- [ ] Multiple overlay support

## Troubleshooting

### Common Issues

1. **"Missing required environment variables"**

   - Ensure all Twitter API credentials are set in `.env`

2. **"Could not fetch profile image"**

   - Target user may have private profile or deleted account

3. **"Rate limit exceeded"**

   - User has exceeded 5 requests per hour limit

4. **Service not starting**
   - Check systemd logs: `journalctl -u crybb-bot -f`
   - Verify .env file permissions: `ls -la /opt/crybb-bot/.env`
   - Check Python virtual environment: `/opt/crybb-bot/venv/bin/python3 --version`

### Logs

The bot provides detailed logging for debugging:

- Mention processing status
- Image processing results
- API interaction logs
- Error messages with context

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:

- Create an issue on GitHub
- Check the troubleshooting section
- Review the test suite for usage examples
