# 📺 IPTV Stream Quality Tester

![Python](https://img.shields.io/badge/python-v3.7+-blue.svg)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macOS-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

A comprehensive Python GUI application for testing and analyzing IPTV stream quality. Test multiple channels simultaneously and generate detailed reports with resolution, FPS, bitrate, and codec information.

![IPTV Tester Demo](https://via.placeholder.com/800x400/2196F3/ffffff?text=IPTV+Stream+Quality+Tester)

## ✨ Features

- **📁 M3U Playlist Support** - Load from local files or remote URLs
- **🔐 Xtream Codes Integration** - Direct API authentication and channel loading  
- **📊 Channel Group Selection** - Test specific channel categories
- **⚡ Multi-threaded Testing** - Efficient parallel stream analysis
- **📈 Quality Analysis** - Extract resolution, FPS, bitrate, and codec data
- **📋 Multiple Export Formats**:
  - CSV for spreadsheet analysis
  - TXT for detailed reports with statistics
  - PNG pie charts showing quality distribution
- **🎯 Real-time Progress Tracking** - Live testing status and progress bars
- **🖥️ User-friendly GUI** - Intuitive tabbed interface built with Tkinter

## 🛠️ Tech Stack

- **Language**: Python 3.7+
- **GUI Framework**: Tkinter (built-in)
- **Stream Analysis**: FFmpeg/FFprobe
- **Data Visualization**: Matplotlib
- **HTTP Requests**: Requests library
- **Data Processing**: NumPy

## 📋 Prerequisites

### Required Software
- **Python 3.7 or higher**
- **FFmpeg** - Download from [ffmpeg.org](https://ffmpeg.org/download.html)
  - Windows: Add to system PATH
  - Linux: `sudo apt-get install ffmpeg` 
  - macOS: `brew install ffmpeg`

### Python Dependencies
pip install requests matplotlib numpy


## 🚀 Installation

1. **Clone the repository**
git clone https://github.com/yourusername/iptv-stream-tester.git
cd iptv-stream-tester

2. **Install dependencies**
pip install -r requirements.txt

text

3. **Verify FFmpeg installation**
ffprobe -version

text

4. **Run the application**
python iptv_tester.py

text

## 📖 Usage Guide

### 🔧 M3U Playlist Testing

1. **Load Playlist**
- **From File**: Click "Load from File" and select your `.m3u` file
- **From URL**: Enter the M3U URL and click "Load from URL"

2. **Select Channel Groups**
- View all available channel groups in the listbox
- Use multi-select to choose specific groups
- Click "Select All" or "Deselect All" for quick selection

3. **Start Testing**
- Click "Start Testing" to begin quality analysis
- Monitor real-time progress in the progress bar
- Stop testing anytime with "Stop Testing"

### 🔐 Xtream Codes Testing

1. **Enter Credentials**
Server URL: http://your-server.com:8080
Username: your_username
Password: your_password

text

2. **Connect and Load**
- Click "Connect" to authenticate and load channels
- Select desired channel groups
- Begin testing process

### 📊 Viewing Results

Navigate to the **"Test Results"** tab to view:
- Channel name and group
- Video resolution (e.g., 1920x1080)
- Frame rate (FPS)
- Bitrate (Kbps/Mbps)
- Video codec
- Test status

### 📈 Export Options

- **CSV Export**: Spreadsheet-compatible format
- **TXT Export**: Detailed report with statistics
- **Pie Chart**: Visual quality distribution (resolution+FPS combinations)

## 📊 Sample Output

### Text Report Structure
==========================================
IPTV STREAM TEST RESULTS
Generated: 2025-10-04 20:42:15
Total Channels Tested: 183
SUMMARY STATISTICS
Successful Tests: 156
Failed Tests: 27
Success Rate: 85.2%

RESOLUTION DISTRIBUTION
1280x720: 87 channels (55.8%)
1920x1080: 48 channels (30.8%)
720x576: 12 channels (7.7%)

text

### Pie Chart Categories
- `720p60` - 720p at 60 FPS
- `1080p30` - 1080p at 30 FPS  
- `SD25` - Standard definition at 25 FPS

## ⚙️ Configuration

### Supported Stream Formats
- **HLS** (HTTP Live Streaming)
- **MPEG-TS** (Transport Stream)
- **MP4** streams
- **WebM** containers

### Testing Parameters
- **Timeout**: 20 seconds per channel
- **Analysis Duration**: 10 seconds
- **Probe Size**: 10MB maximum

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**
git checkout -b feature/amazing-feature

text
3. **Make your changes**
4. **Commit with descriptive messages**
git commit -m 'Add amazing feature'

text
5. **Push to your branch**
git push origin feature/amazing-feature

text
6. **Open a Pull Request**


## 🙏 Acknowledgments

- **FFmpeg Team** - For the powerful media analysis tools
- **Python Community** - For excellent libraries and documentation

---

⭐ **If this project helped you, please consider giving it a star!** ⭐

Made with ❤️ for the IPTV community
