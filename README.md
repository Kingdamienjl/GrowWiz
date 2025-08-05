# GrowWiz 🌿

GrowWiz is an AI-powered cultivation assistant that helps manage indoor grow rooms — primarily for cannabis but extendable to similar plants like tomatoes, peppers, or herbs. It combines:

- **Web-scraped expert grow guides** from forums, blogs, and cultivation sites
- **Plant problem diagnosis via image** using AI-powered classification
- **Real-time sensor monitoring** (temperature, humidity, soil moisture, CO2)
- **Automated grow room control** with trigger-based device management
- **Comprehensive web dashboard** for monitoring and control
- **CLI tools** for command-line management

Primary platform: Raspberry Pi (any model) with GPIO support. Accessible via web dashboard, CLI, or API.

## Project Status 📊

**Current Status**: ✅ **Complete** - All core modules implemented and tested

| Module | Status | Progress |
|--------|--------|----------|
| 🌡️ Sensor Integration | ✅ Complete | 100% |
| 🤖 Plant Classifier | ✅ Complete | 100% |
| 🕷️ Web Scraper | ✅ Complete | 100% |
| ⚡ Automation Engine | ✅ Complete | 100% |
| 💾 Database Management | ✅ Complete | 100% |
| 🌐 Web Dashboard | ✅ Complete | 100% |
| 🖥️ CLI Interface | ✅ Complete | 100% |
| 🧪 Test Suite | ✅ Complete | 100% |

**Owner**: Chris  
**Last Updated**: December 2024

## Features

### 🔍 Plant Problem Diagnosis
- Image-based plant health analysis
- Disease and deficiency identification
- Treatment recommendations

### 📊 Environmental Monitoring
- Temperature and humidity tracking
- Soil moisture monitoring
- CO2 level measurement
- Historical data logging

### 📚 Knowledge Base
- Web-scraped grow guides
- Expert cultivation tips
- Strain-specific information

### 🤖 AI Assistant
- Natural language plant care queries
- Personalized growing advice
- Problem troubleshooting

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd growwiz

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run the application
python src/main.py
```

## Hardware Requirements

### Minimum Setup
- Raspberry Pi Zero 2 W
- MicroSD card (32GB+)
- DHT22 sensor (temperature/humidity)
- Soil moisture sensor
- Camera module

### Advanced Setup
- CO2 sensor (MH-Z19B)
- pH sensor
- Light intensity sensor
- Relay modules for automation

## Configuration

Edit the `.env` file to configure:
- Sensor pins and settings
- API keys for external services
- Network configuration
- Dashboard settings

## Usage

### Web Dashboard
Access the dashboard at `http://your-pi-ip:8080`

### CLI Interface
```bash
# Check plant health
python src/cli.py diagnose --image path/to/plant.jpg

# Monitor sensors
python src/cli.py monitor

# Get growing advice
python src/cli.py advice "My leaves are yellowing"
```

## API Endpoints

- `GET /api/sensors` - Current sensor readings
- `POST /api/diagnose` - Upload image for diagnosis
- `GET /api/history` - Historical data
- `POST /api/advice` - Get AI advice

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions, please open a GitHub issue or contact the development team.