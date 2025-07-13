# Habit Monitor CLI

A real-time webcam monitoring application that detects bad habits like shirt chewing and face touching using Roboflow workflows, providing immediate audio feedback to help break these habits.

## Features

- **Real-time habit detection** using Roboflow workflows
- **Audio warnings** when bad habits are detected
- **Time tracking** to monitor habit duration and frequency
- **Live CLI dashboard** with real-time statistics
- **Cross-platform support** (Windows, macOS, Linux)
- **Configurable detection thresholds** and settings
- **Session statistics** and habit analytics

## Prerequisites

- Python 3.7+
- Webcam/camera access
- Roboflow inference server running via Docker
- Roboflow API key
- A trained Roboflow workflow for habit detection

## Quick Start

1. **Clone or download** this repository
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment variables**:
   ```bash
   cp env.example .env
   # Edit .env with your API key and settings
   ```
4. **Start monitoring** (includes automatic validation):
   ```bash
   python3 habit_monitor.py
   ```

## Detailed Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Roboflow Setup

No need to run a local inference server! The application uses Roboflow's cloud inference through the `inference` package, which provides optimized performance and automatic updates.

### 3. Configure Environment Variables

Create a `.env` file from the example template:

```bash
cp env.example .env
```

Then edit `.env` to set your configuration:

```bash
# Required: Your Roboflow API key
ROBOFLOW_API_KEY=your-actual-api-key-here

# Required: Your Roboflow workspace name
WORKSPACE_NAME=your-workspace-name

# Required: Your workflow ID
WORKFLOW_ID=your-workflow-id

# Optional: Adjust detection sensitivity
CONFIDENCE_THRESHOLD=0.5

# Optional: Camera settings
CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480

# Optional: Audio and display settings
ENABLE_AUDIO_WARNINGS=true
AUDIO_WARNING_COOLDOWN=5
SHOW_WEBCAM_FEED=false
```

All configuration is now managed through environment variables loaded from the `.env` file. You can still override any setting using command-line flags.

> **Note**: The `.env` file approach makes it easy to manage different configurations for different environments (development, production, etc.) and keeps sensitive data like API keys out of your code.

#### Configuration Precedence (highest to lowest):
1. **Command-line arguments** - `--confidence 0.8`
2. **Environment variables** - `export CONFIDENCE_THRESHOLD=0.7`
3. **`.env` file** - `CONFIDENCE_THRESHOLD=0.6`
4. **Default values** - Built-in defaults in `config.py`

#### Benefits of .env Configuration:
- ✅ **Security**: API keys and sensitive data stay in `.env` (which should not be committed to git)
- ✅ **Flexibility**: Different settings for development, testing, and production
- ✅ **Convenience**: No need to modify Python files for configuration changes
- ✅ **Portability**: Easy to share configurations or deploy to different environments

### 🚀 **New Simplified Architecture**

This version now uses Roboflow's `InferencePipeline` which provides:
- ✅ **Built-in webcam handling** - No manual OpenCV camera management
- ✅ **Optimized workflow execution** - Better performance than manual HTTP requests
- ✅ **Automatic error recovery** - Robust handling of network/camera issues
- ✅ **Cloud-based inference** - No need to run local Docker containers
- ✅ **Simplified codebase** - Removed camera.py and workflow.py (~250 lines of code eliminated)
- ✅ **Automatic timestamped logging** - Each session creates a unique log file in `logs/`

### 4. Test the Setup

The application will automatically validate your setup when you run it. To see just the configuration without starting monitoring:

```bash
python3 habit_monitor.py --show-config
```

## Usage

### Basic Usage

```bash
python3 habit_monitor.py
```

### Command Line Options

```bash
python3 habit_monitor.py --help
```

Options:
- `--workspace`: Roboflow workspace name (default: from config.py)
- `--workflow-id`: Workflow ID for habit detection (default: from config.py)
- `--confidence`: Confidence threshold for detection (default: from config.py)
- `--camera`: Camera index to use (default: from config.py)
- `--skip-validation`: Skip setup validation (not recommended)
- `--show-config`: Show current configuration and exit

### Examples

```bash
# Basic monitoring (includes automatic validation)
python3 habit_monitor.py

# Show current configuration
python3 habit_monitor.py --show-config

# Skip validation (not recommended)
python3 habit_monitor.py --skip-validation

# Use a different camera
python3 habit_monitor.py --camera 1

# Use a different workspace
python3 habit_monitor.py --workspace my-other-workspace

# Adjust confidence threshold
python3 habit_monitor.py --confidence 0.7

# Logs are automatically saved to timestamped files
# Example: logs/habit_monitor_20250713_162834.log
python3 habit_monitor.py --confidence 0.8

# Use a specific workflow
python3 habit_monitor.py --workflow-id "my-habit-workflow"
```

## CLI Dashboard

The application displays a real-time dashboard with:

```
============================================================
           HABIT MONITOR - REAL-TIME STATUS
============================================================

Session Duration: 0:05:32
✅ No Bad Habits Detected

Statistics:
  Total Detections: 3
  Total Habit Time: 0:00:45
  Number of Sessions: 3
  Average Session: 0:00:15

Press Ctrl+C to stop monitoring
============================================================
```

## Configuration

Edit `config.py` to customize:

- **Detection settings**: Confidence threshold, inference interval
- **Camera settings**: Resolution, FPS, camera index
- **Audio settings**: Enable/disable warnings, cooldown periods
- **Display settings**: Refresh rate, webcam preview
- **Logging**: Log levels, file output

## Roboflow Workflow Setup

Your Roboflow workflow should:

1. **Accept image input** in base64 format
2. **Return predictions** with confidence scores
3. **Include habit classifications** (e.g., "shirt_chewing", "face_touching")

### Expected Workflow Response Format

```json
{
  "outputs": [
    {
      "predictions": [
        {
          "confidence": 0.85,
          "class": "shirt_chewing"
        }
      ]
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **Camera not detected**
   - Check camera permissions
   - Try different camera index: `--camera 1`
   - Test with other applications

2. **Roboflow server not responding**
   - Ensure Docker is running
   - Check server status: `curl http://localhost:9001/health`
   - Restart inference server

3. **API key issues**
   - Verify API key is set: `echo $ROBOFLOW_API_KEY`
   - Check API key validity in Roboflow dashboard

4. **Workflow errors**
   - Verify workflow ID in config.py
   - Test workflow in Roboflow dashboard
   - Check workflow input/output format

### Debug Mode

Enable debug logging in `config.py`:

```python
LOG_LEVEL = "DEBUG"
SHOW_WEBCAM_FEED = True  # Show camera preview
```

### Performance Issues

- Increase `INFERENCE_INTERVAL` for slower inference
- Reduce camera resolution in config
- Check system resources (CPU, memory)

## File Structure

```
better-riaz/
├── habit_monitor.py             # Main CLI entry point
├── config.py                   # Configuration loader (loads from .env)
├── env.example                 # Environment variables template
├── requirements.txt            # Python dependencies
├── README.md                  # This file
├── example_workflow_response.json  # Example workflow response format
└── lib/                       # Modular library components
    ├── __init__.py           # Package initialization
    ├── monitor.py            # Simplified monitor using InferencePipeline
    ├── audio.py              # Audio warning system
    ├── display.py            # CLI display and dashboard
    ├── stats.py              # Statistics and time tracking
    └── utils.py              # Utility functions
```

## Audio Warnings

The application plays audio warnings when habits are detected:

- **macOS**: Uses built-in system sounds
- **Windows**: Uses system beep
- **Linux**: Uses system audio
- **Fallback**: Terminal bell

## Statistics and Analytics

The application tracks:

- **Total session time**
- **Habit detection count**
- **Total habit time**
- **Individual habit sessions**
- **Average session duration**
- **Habit percentage** (habit time / total time)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Feel free to use, modify, and distribute.

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review configuration settings
3. Test with debug mode enabled
4. Check Roboflow workflow functionality

## Workflow Development Tips

For best results with your Roboflow workflow:

1. **Train with diverse lighting conditions**
2. **Include multiple angles and positions**
3. **Use high-quality training images**
4. **Test thoroughly before deployment**
5. **Monitor accuracy and adjust thresholds**

## Privacy and Security

- **Local processing**: All video processing happens locally
- **No data storage**: Frames are not saved unless configured
- **Secure API calls**: Only inference results are transmitted
- **Camera access**: Only used for real-time monitoring

---

**Happy habit breaking!** 🎯 