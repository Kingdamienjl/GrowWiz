# GrowWiz Deployment Guide

## 🚀 Production Deployment Instructions

### Pre-Deployment Checklist
- [x] All core features implemented and tested
- [x] Demo content removed
- [x] Error handling implemented
- [x] Security audit completed
- [x] Dependencies documented
- [x] Environment configuration ready

## 📋 Git Commands for Release

### 1. Commit Current Changes
```bash
# Add all files to staging
git add .

# Commit with release message
git commit -m "🚀 Release v1.0.0 - Production Ready GrowWiz

✅ Features Implemented:
- Strain identification system with image upload
- Advanced care sheet generation
- Interactive plant visualization on calendar
- Growing tips database with search
- Environmental monitoring and automation
- Comprehensive grow session management
- Professional UI with responsive design

🔧 Technical Improvements:
- Removed all demo/placeholder content
- Fixed care sheet generation errors
- Implemented proper error handling
- Added comprehensive logging
- Optimized database operations
- Security hardening completed

🎯 Production Status: Ready for deployment
📊 Test Coverage: Comprehensive test suite
🔒 Security: No exposed credentials
💾 Data: Robust backup and recovery"
```

### 2. Create Release Tag
```bash
# Create annotated tag for release
git tag -a v1.0.0 -m "GrowWiz v1.0.0 - Production Release

Complete cannabis growing management system with:
- Strain identification and care sheets
- Interactive grow calendar
- Environmental monitoring
- Automation engine
- Professional web interface

Ready for production deployment."
```

### 3. Push to GitHub
```bash
# Push commits and tags
git push origin main
git push origin v1.0.0
```

## 🌐 Deployment Options

### Option 1: Local Production Server
```bash
# Install dependencies
pip install -r requirements.txt

# Set production environment
cp .env.example .env
# Edit .env file with production settings

# Run production server
python app.py
```

### Option 2: Docker Deployment
```bash
# Create Dockerfile (see below)
docker build -t growwiz:v1.0.0 .
docker run -d -p 5000:5000 --name growwiz-prod growwiz:v1.0.0
```

### Option 3: Cloud Deployment (Heroku)
```bash
# Install Heroku CLI and login
heroku create growwiz-app
heroku config:set GROWWIZ_ENVIRONMENT=PRODUCTION
git push heroku main
```

### Option 4: VPS/Server Deployment
```bash
# On your server
git clone https://github.com/yourusername/GrowWiz.git
cd GrowWiz
pip install -r requirements.txt
cp .env.example .env
# Configure .env for production
python app.py
```

## 🐳 Docker Configuration

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs temp_strain_data

# Set environment variables
ENV PYTHONPATH=/app
ENV GROWWIZ_ENVIRONMENT=PRODUCTION
ENV HOST=0.0.0.0
ENV PORT=5000

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run application
CMD ["python", "app.py"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  growwiz:
    build: .
    ports:
      - "5000:5000"
    environment:
      - GROWWIZ_ENVIRONMENT=PRODUCTION
      - HOST=0.0.0.0
      - PORT=5000
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## ⚙️ Production Environment Setup

### Required Environment Variables (.env)
```bash
# Production Configuration
GROWWIZ_ENVIRONMENT=PRODUCTION
HOST=0.0.0.0
PORT=5000
DEBUG=false
SECRET_KEY=your-secure-secret-key-here

# Hardware Configuration
HARDWARE_PLATFORM=raspberry_pi
SIMULATION_MODE=false  # Set to true if no hardware

# Database
DATABASE_PATH=data/growwiz.db
BACKUP_INTERVAL=24

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/growwiz.log

# Security
ENABLE_API_DOCS=false  # Disable in production
API_RATE_LIMIT=100
```

## 🔒 Security Checklist

- [x] No hardcoded secrets in code
- [x] Environment variables for sensitive data
- [x] Proper .gitignore for credentials
- [x] API rate limiting implemented
- [x] Input validation on all endpoints
- [x] Error messages don't expose internals
- [x] HTTPS ready (configure reverse proxy)

## 📊 Monitoring & Maintenance

### Log Monitoring
```bash
# Monitor application logs
tail -f logs/growwiz.log

# Check error logs
grep ERROR logs/growwiz.log
```

### Database Backup
```bash
# Backup database
cp data/growwiz.db data/backup/growwiz_$(date +%Y%m%d).db
```

### Health Checks
- Application: `http://your-domain:5000/`
- API Status: `http://your-domain:5000/api/status`
- Database: Check log files for connection errors

## 🚀 Post-Deployment Steps

1. **Verify Application**:
   - Test all major features
   - Check sensor readings (if hardware connected)
   - Verify database operations

2. **Set Up Monitoring**:
   - Configure log rotation
   - Set up health check alerts
   - Monitor resource usage

3. **User Documentation**:
   - Create user manual
   - Set up support channels
   - Prepare training materials

4. **Future Enhancements**:
   - Google Drive integration (when credentials available)
   - Email notifications
   - Mobile app development

## 📞 Support & Troubleshooting

### Common Issues
- **Port conflicts**: Change PORT in .env
- **Permission errors**: Check file permissions
- **Database issues**: Verify DATABASE_PATH exists
- **Sensor errors**: Enable SIMULATION_MODE if no hardware

### Getting Help
- Check logs in `logs/growwiz.log`
- Review error messages in browser console
- Verify environment configuration
- Test with SIMULATION_MODE=true first

---

**Deployment Status**: Ready for Production ✅  
**Version**: 1.0.0  
**Last Updated**: January 2025