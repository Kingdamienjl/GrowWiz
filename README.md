# GrowWiz 🌿

GrowWiz is an AI-powered cultivation assistant that helps manage indoor grow rooms — primarily for cannabis but extendable to similar plants like tomatoes, peppers, or herbs. It combines:

- **Web-scraped expert grow guides** from forums, blogs, and cultivation sites using advanced Hyperbrowser technology
- **Plant problem diagnosis via image** using AI-powered classification
- **Real-time sensor monitoring** (temperature, humidity, soil moisture, CO2)
- **Automated grow room control** with trigger-based device management
- **Comprehensive strain database** with 231+ enhanced strain profiles
- **Comprehensive web dashboard** for monitoring and control
- **CLI tools** for command-line management

Primary platform: Raspberry Pi (any model) with GPIO support. Accessible via web dashboard, CLI, or API.

## Project Status 📊

**Current Status**: ✅ **Complete** - All core modules implemented and tested

| Module | Status | Progress | Description |
|--------|--------|----------|-------------|
| 🌡️ Sensor Integration | ✅ Complete | 100% | DHT22, soil moisture, CO2 monitoring |
| 🤖 Plant Classifier | ✅ Complete | 100% | AI-powered plant health diagnosis |
| 🕷️ Web Scraper | ✅ Complete | 100% | Hyperbrowser-powered content extraction |
| 🧬 Strain Database | ✅ Complete | 100% | 231 enhanced strain profiles with THC/CBD data |
| ⚡ Automation Engine | ✅ Complete | 100% | Trigger-based device control |
| 💾 Database Management | ✅ Complete | 100% | JSON-based data storage |
| 🌐 Web Dashboard | ✅ Complete | 100% | Real-time monitoring interface |
| 🖥️ CLI Interface | ✅ Complete | 100% | Command-line management tools |
| 🧪 Test Suite | ✅ Complete | 100% | Comprehensive testing framework |

**Owner**: Chris  
**Last Updated**: January 2025

## Features

### 🔍 Plant Problem Diagnosis
- Image-based plant health analysis using AI
- Disease and deficiency identification
- Treatment recommendations with confidence scores
- Support for multiple plant types

### 📊 Environmental Monitoring
- Real-time temperature and humidity tracking
- Soil moisture monitoring with alerts
- CO2 level measurement and logging
- Historical data visualization
- Automated data logging to JSON files

### 🧬 Enhanced Strain Database
- **231 comprehensive strain profiles** with detailed information
- **THC/CBD content extraction** from descriptions
- **Cleaned strain names** for better searchability
- **Strain type classification** (Indica, Sativa, Hybrid)
- **Medical uses and effects** documentation
- **Flavor profiles** and growing characteristics

### 📚 Knowledge Base
- Web-scraped grow guides using Hyperbrowser technology
- Expert cultivation tips from 15+ cannabis databases
- Strain-specific growing information
- Problem diagnosis and treatment guides

### 🤖 AI Assistant
- Natural language plant care queries
- Personalized growing advice based on strain data
- Problem troubleshooting with image analysis
- Integration with Athena AI for advanced insights

## Hardware Requirements & Parts List

### Essential Components

#### Raspberry Pi Setup
- **Raspberry Pi 4 Model B (4GB RAM)** - $75
  - [Amazon Link](https://www.amazon.com/Raspberry-Model-2019-Quad-Bluetooth/dp/B07TC2BK1X)
- **MicroSD Card (64GB Class 10)** - $15
  - [Amazon Link](https://www.amazon.com/SanDisk-Ultra-microSDXC-Memory-Adapter/dp/B08GY9NYRM)
- **Raspberry Pi Power Supply (USB-C, 5V 3A)** - $10
  - [Amazon Link](https://www.amazon.com/Raspberry-Model-Official-SC0218/dp/B07W8XHMJZ)

#### Environmental Sensors
- **DHT22 Temperature/Humidity Sensor** - $8
  - [Amazon Link](https://www.amazon.com/HiLetgo-Temperature-Humidity-Electronic-Practice/dp/B0795F19W6)
  - Accuracy: ±0.5°C, ±2-5% RH
  - Operating Range: -40°C to 80°C, 0-100% RH

- **Capacitive Soil Moisture Sensor v1.2** - $6
  - [Amazon Link](https://www.amazon.com/Gikfun-Capacitive-Moisture-Corrosion-Resistant/dp/B07H3P1NRM)
  - Corrosion-resistant design
  - Analog output for precise readings

- **MH-Z19B CO2 Sensor** - $25
  - [Amazon Link](https://www.amazon.com/MH-Z19B-Infrared-Carbon-Dioxide-Sensor/dp/B07R551Y1X)
  - Range: 0-5000ppm
  - UART/PWM output

#### Optional Advanced Sensors
- **pH Sensor Kit (Analog)** - $35
  - [Amazon Link](https://www.amazon.com/Gravity-Analog-Sensor-Arduino-Raspberry/dp/B01BVGQX3Q)
  - Range: 0-14 pH
  - Temperature compensation

- **TDS/EC Sensor** - $20
  - [Amazon Link](https://www.amazon.com/Gravity-Analog-Electrical-Conductivity-Arduino/dp/B07BQZPX4Q)
  - Measures nutrient concentration

- **BH1750 Light Intensity Sensor** - $5
  - [Amazon Link](https://www.amazon.com/HiLetgo-BH1750FVI-Digital-Intensity-Arduino/dp/B01DLG4NZC)
  - Range: 1-65535 lux
  - I2C interface

#### Camera & Imaging
- **Raspberry Pi Camera Module v2** - $25
  - [Amazon Link](https://www.amazon.com/Raspberry-Pi-Camera-Module-Megapixel/dp/B01ER2SKFS)
  - 8MP sensor for plant health imaging

#### Automation & Control
- **8-Channel 5V Relay Module** - $12
  - [Amazon Link](https://www.amazon.com/ELEGOO-Channel-Optocoupler-Arduino-Raspberry/dp/B01HEQF5HU)
  - Controls lights, fans, pumps, etc.

- **12V DC Fan (120mm)** - $15
  - [Amazon Link](https://www.amazon.com/ARCTIC-F12-PWM-PST-Pressure-Optimized/dp/B00NTUJTAK)
  - For air circulation

#### Connectivity & Accessories
- **Breadboard & Jumper Wires Kit** - $10
  - [Amazon Link](https://www.amazon.com/Elegoo-EL-CP-004-Multicolored-Breadboard-arduino/dp/B01EV70C78)

- **GPIO Extension Board** - $8
  - [Amazon Link](https://www.amazon.com/GeeekPi-Raspberry-GPIO-Extension-Board/dp/B07P9W5SQS)

- **Waterproof Enclosure** - $20
  - [Amazon Link](https://www.amazon.com/LeMotech-Waterproof-Electrical-Junction-200x120x75mm/dp/B075DHBQQ7)

### Total Cost Estimate
- **Basic Setup**: ~$150 (Pi + essential sensors)
- **Advanced Setup**: ~$280 (all components)

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/growwiz.git
cd growwiz

# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies (Raspberry Pi)
sudo apt update
sudo apt install -y python3-pip python3-venv git

# Configure environment
cp .env.example .env
# Edit .env with your sensor pins and API keys

# Initialize the database
python src/database_manager.py --init

# Run the application
python app.py
```

## Configuration

### GPIO Pin Configuration
Edit the `.env` file to configure sensor pins:

```env
# Sensor GPIO Pins
DHT22_PIN=4
SOIL_MOISTURE_PIN=0  # ADC channel
CO2_SENSOR_TX=14
CO2_SENSOR_RX=15

# Relay Control Pins
LIGHT_RELAY_PIN=18
FAN_RELAY_PIN=19
PUMP_RELAY_PIN=20
HEATER_RELAY_PIN=21

# API Configuration
HYPERBROWSER_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Dashboard Settings
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
DEBUG=False
```

## Usage

### Web Dashboard
Access the dashboard at `http://your-pi-ip:5000`

Features:
- Real-time sensor monitoring
- Strain database browser (231 strains)
- Plant health diagnosis via image upload
- Automation trigger management
- Historical data visualization

### CLI Interface
```bash
# Monitor sensors
python src/sensor_manager.py

# Diagnose plant health
python src/plant_classifier.py --image path/to/plant.jpg

# Scrape growing tips
python src/grow_tip_scraper.py --count 50

# View strain database
python src/strain_scraper.py --list
```

## API Endpoints

### Core Endpoints
- `GET /api/status` - System status and sensor readings
- `GET /api/sensors` - Current sensor data
- `POST /api/diagnose` - Plant health diagnosis
- `GET /api/automation/triggers` - Automation rules

### Strain Database
- `GET /api/strains/list` - Browse strain database (231 strains)
- `POST /api/scrape-strains` - Initiate strain scraping
- `GET /api/scraping-status` - Check scraping progress

### Growing Tips
- `GET /api/tips/search` - Search growing tips
- `POST /api/tips/scrape` - Scrape new tips

## Data Files

The system maintains several data files:
- `data/final_reconstructed_strains.json` - Enhanced strain database (231 strains)
- `data/scraped_tips.json` - Growing tips and guides
- `data/sensor_readings.json` - Historical sensor data
- `data/automation_logs.json` - Automation event logs

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - see LICENSE file for details.

## Support & Community

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check the `/docs` folder for detailed guides
- **Discord**: Join our growing community (link coming soon)

## Acknowledgments

- **Hyperbrowser** for advanced web scraping capabilities
- **OpenAI** for AI-powered plant diagnosis
- **Raspberry Pi Foundation** for the amazing hardware platform
- **Cannabis cultivation community** for sharing knowledge and expertise

---

**Built with ❤️ by Chris and the GrowWiz community**