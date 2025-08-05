// GrowWiz Dashboard JavaScript

class GrowWizDashboard {
    constructor() {
        this.apiBase = window.location.origin;
        this.updateInterval = 5000; // 5 seconds
        this.chart = null;
        this.isConnected = false;
        
        this.init();
    }
    
    async init() {
        console.log('Initializing GrowWiz Dashboard...');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize chart
        this.initChart();
        
        // Start data updates
        this.startUpdates();
        
        // Test connection
        await this.testConnection();
        
        console.log('Dashboard initialized successfully');
    }
    
    setupEventListeners() {
        // Image upload
        const uploadArea = document.getElementById('uploadArea');
        const imageUpload = document.getElementById('imageUpload');
        
        uploadArea.addEventListener('click', () => imageUpload.click());
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = 'var(--primary-color)';
        });
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.borderColor = 'var(--border-color)';
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = 'var(--border-color)';
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleImageUpload(files[0]);
            }
        });
        
        imageUpload.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleImageUpload(e.target.files[0]);
            }
        });
        
        // Chat functionality
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendMessage');
        
        sendButton.addEventListener('click', () => this.sendChatMessage());
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendChatMessage();
            }
        });
        
        // Automation controls
        this.setupAutomationControls();
        
        // Emergency stop
        document.getElementById('emergencyStop').addEventListener('click', () => {
            this.emergencyStop();
        });
        
        // Refresh automation
        document.getElementById('refreshAutomation').addEventListener('click', () => {
            this.updateAutomationStatus();
        });
    }
    
    setupAutomationControls() {
        const devices = ['fan', 'heater', 'humidifier', 'pump', 'lights', 'co2'];
        
        devices.forEach(device => {
            const toggle = document.getElementById(`${device}Toggle`);
            if (toggle) {
                toggle.addEventListener('change', (e) => {
                    this.toggleDevice(device, e.target.checked);
                });
            }
        });
    }
    
    initChart() {
        const ctx = document.getElementById('environmentChart').getContext('2d');
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Temperature (°C)',
                        data: [],
                        borderColor: '#F44336',
                        backgroundColor: 'rgba(244, 67, 54, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Humidity (%)',
                        data: [],
                        borderColor: '#2196F3',
                        backgroundColor: 'rgba(33, 150, 243, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Soil Moisture (%)',
                        data: [],
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'CO2 (ppm)',
                        data: [],
                        borderColor: '#FF9800',
                        backgroundColor: 'rgba(255, 152, 0, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Temperature (°C) / Humidity (%) / Soil Moisture (%)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'CO2 (ppm)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });
    }
    
    async testConnection() {
        try {
            const response = await fetch(`${this.apiBase}/health`);
            if (response.ok) {
                this.setConnectionStatus(true);
            } else {
                this.setConnectionStatus(false);
            }
        } catch (error) {
            console.error('Connection test failed:', error);
            this.setConnectionStatus(false);
        }
    }
    
    setConnectionStatus(connected) {
        this.isConnected = connected;
        const statusDot = document.getElementById('connectionStatus');
        const statusText = document.getElementById('connectionText');
        
        if (connected) {
            statusDot.className = 'status-dot connected';
            statusText.textContent = 'Connected';
        } else {
            statusDot.className = 'status-dot disconnected';
            statusText.textContent = 'Disconnected';
        }
    }
    
    startUpdates() {
        // Update sensor data
        this.updateSensorData();
        setInterval(() => this.updateSensorData(), this.updateInterval);
        
        // Update automation status
        this.updateAutomationStatus();
        setInterval(() => this.updateAutomationStatus(), this.updateInterval * 2);
        
        // Update activity
        this.updateActivity();
        setInterval(() => this.updateActivity(), this.updateInterval * 3);
    }
    
    async updateSensorData() {
        try {
            const response = await fetch(`${this.apiBase}/sensors/current`);
            if (!response.ok) throw new Error('Failed to fetch sensor data');
            
            const data = await response.json();
            this.displaySensorData(data);
            this.updateChart(data);
            this.setConnectionStatus(true);
            
        } catch (error) {
            console.error('Error updating sensor data:', error);
            this.setConnectionStatus(false);
        }
    }
    
    displaySensorData(data) {
        // Update temperature
        const tempElement = document.getElementById('temperature');
        const tempStatus = document.getElementById('tempStatus');
        if (data.temperature !== null) {
            tempElement.textContent = `${data.temperature}°C`;
            tempStatus.textContent = this.getSensorStatus(data.temperature, 18, 28);
            tempStatus.className = `sensor-status ${this.getSensorStatusClass(data.temperature, 18, 28)}`;
        }
        
        // Update humidity
        const humidityElement = document.getElementById('humidity');
        const humidityStatus = document.getElementById('humidityStatus');
        if (data.humidity !== null) {
            humidityElement.textContent = `${data.humidity}%`;
            humidityStatus.textContent = this.getSensorStatus(data.humidity, 40, 60);
            humidityStatus.className = `sensor-status ${this.getSensorStatusClass(data.humidity, 40, 60)}`;
        }
        
        // Update soil moisture
        const soilElement = document.getElementById('soilMoisture');
        const soilStatus = document.getElementById('soilStatus');
        if (data.soil_moisture !== null) {
            soilElement.textContent = `${data.soil_moisture}%`;
            soilStatus.textContent = this.getSensorStatus(data.soil_moisture, 30, 70);
            soilStatus.className = `sensor-status ${this.getSensorStatusClass(data.soil_moisture, 30, 70)}`;
        }
        
        // Update CO2
        const co2Element = document.getElementById('co2');
        const co2Status = document.getElementById('co2Status');
        if (data.co2 !== null) {
            co2Element.textContent = `${data.co2} ppm`;
            co2Status.textContent = this.getSensorStatus(data.co2, 400, 1200);
            co2Status.className = `sensor-status ${this.getSensorStatusClass(data.co2, 400, 1200)}`;
        }
    }
    
    getSensorStatus(value, min, max) {
        if (value < min) return 'Low';
        if (value > max) return 'High';
        return 'Normal';
    }
    
    getSensorStatusClass(value, min, max) {
        if (value < min || value > max) return 'warning';
        return '';
    }
    
    updateChart(data) {
        if (!this.chart || !data.timestamp) return;
        
        const time = new Date(data.timestamp * 1000).toLocaleTimeString();
        const maxPoints = 20;
        
        // Add new data point
        this.chart.data.labels.push(time);
        this.chart.data.datasets[0].data.push(data.temperature);
        this.chart.data.datasets[1].data.push(data.humidity);
        this.chart.data.datasets[2].data.push(data.soil_moisture);
        this.chart.data.datasets[3].data.push(data.co2);
        
        // Remove old data points
        if (this.chart.data.labels.length > maxPoints) {
            this.chart.data.labels.shift();
            this.chart.data.datasets.forEach(dataset => dataset.data.shift());
        }
        
        this.chart.update('none');
    }
    
    async handleImageUpload(file) {
        if (!file.type.startsWith('image/')) {
            this.showNotification('Please select an image file', 'error');
            return;
        }
        
        this.showLoading(true);
        
        try {
            const formData = new FormData();
            formData.append('image', file);
            
            const response = await fetch(`${this.apiBase}/plant/diagnose`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) throw new Error('Failed to diagnose plant');
            
            const result = await response.json();
            this.displayDiagnosisResult(result);
            
        } catch (error) {
            console.error('Error diagnosing plant:', error);
            this.showNotification('Failed to diagnose plant image', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    displayDiagnosisResult(result) {
        const resultDiv = document.getElementById('diagnosisResult');
        const contentDiv = document.getElementById('diagnosisContent');
        
        if (result.error) {
            contentDiv.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>${result.error_message || 'Diagnosis failed'}</p>
                </div>
            `;
        } else {
            let html = `
                <div class="diagnosis-info">
                    <h5>Primary Diagnosis: ${result.primary_diagnosis || 'Unknown'}</h5>
                    <p>Confidence: ${(result.confidence * 100).toFixed(1)}%</p>
                </div>
            `;
            
            if (result.recommendations && result.recommendations.length > 0) {
                html += `
                    <div class="recommendations">
                        <h6>Recommendations:</h6>
                        <ul>
                            ${result.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
            
            contentDiv.innerHTML = html;
        }
        
        resultDiv.style.display = 'block';
    }
    
    async sendChatMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Add user message to chat
        this.addChatMessage(message, 'user');
        input.value = '';
        
        try {
            const response = await fetch(`${this.apiBase}/ai/advice`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question: message })
            });
            
            if (!response.ok) throw new Error('Failed to get AI advice');
            
            const result = await response.json();
            this.addChatMessage(result.advice || 'Sorry, I could not provide advice at this time.', 'bot');
            
        } catch (error) {
            console.error('Error getting AI advice:', error);
            this.addChatMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    }
    
    addChatMessage(message, sender) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const icon = sender === 'user' ? 'fas fa-user' : 'fas fa-robot';
        
        messageDiv.innerHTML = `
            <i class="${icon}"></i>
            <div class="message-content">
                <p>${message}</p>
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    async updateAutomationStatus() {
        try {
            const response = await fetch(`${this.apiBase}/automation/status`);
            if (!response.ok) throw new Error('Failed to fetch automation status');
            
            const data = await response.json();
            this.displayAutomationStatus(data);
            
        } catch (error) {
            console.error('Error updating automation status:', error);
        }
    }
    
    displayAutomationStatus(data) {
        const deviceStates = data.device_states || {};
        
        Object.keys(deviceStates).forEach(device => {
            const toggle = document.getElementById(`${device}Toggle`);
            const status = document.getElementById(`${device}Status`);
            
            if (toggle && status) {
                const isOn = deviceStates[device];
                toggle.checked = isOn;
                status.textContent = isOn ? 'ON' : 'OFF';
                status.className = `device-status ${isOn ? 'on' : 'off'}`;
            }
        });
    }
    
    async toggleDevice(device, state) {
        try {
            const response = await fetch(`${this.apiBase}/automation/control`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    device: device,
                    action: state ? 'on' : 'off'
                })
            });
            
            if (!response.ok) throw new Error('Failed to control device');
            
            const result = await response.json();
            this.showNotification(`${device} turned ${state ? 'on' : 'off'}`, 'success');
            
        } catch (error) {
            console.error('Error controlling device:', error);
            this.showNotification(`Failed to control ${device}`, 'error');
            
            // Revert toggle state
            const toggle = document.getElementById(`${device}Toggle`);
            if (toggle) toggle.checked = !state;
        }
    }
    
    async emergencyStop() {
        if (!confirm('Are you sure you want to perform an emergency stop? This will turn off all devices.')) {
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBase}/automation/emergency-stop`, {
                method: 'POST'
            });
            
            if (!response.ok) throw new Error('Failed to perform emergency stop');
            
            this.showNotification('Emergency stop activated - all devices turned off', 'warning');
            this.updateAutomationStatus();
            
        } catch (error) {
            console.error('Error performing emergency stop:', error);
            this.showNotification('Failed to perform emergency stop', 'error');
        }
    }
    
    async updateActivity() {
        try {
            const response = await fetch(`${this.apiBase}/activity/recent`);
            if (!response.ok) throw new Error('Failed to fetch activity');
            
            const activities = await response.json();
            this.displayActivity(activities);
            
        } catch (error) {
            console.error('Error updating activity:', error);
        }
    }
    
    displayActivity(activities) {
        const activityList = document.getElementById('activityList');
        
        if (!activities || activities.length === 0) {
            activityList.innerHTML = '<div class="activity-item"><i class="fas fa-info-circle"></i><span>No recent activity</span></div>';
            return;
        }
        
        activityList.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <i class="fas fa-${this.getActivityIcon(activity.type)}"></i>
                <span>${activity.message}</span>
                <time>${this.formatTime(activity.timestamp)}</time>
            </div>
        `).join('');
    }
    
    getActivityIcon(type) {
        const icons = {
            'sensor': 'thermometer-half',
            'automation': 'cogs',
            'diagnosis': 'camera',
            'system': 'server',
            'error': 'exclamation-triangle'
        };
        return icons[type] || 'info-circle';
    }
    
    formatTime(timestamp) {
        const now = Date.now() / 1000;
        const diff = now - timestamp;
        
        if (diff < 60) return 'Just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.classList.add('show');
        } else {
            overlay.classList.remove('show');
        }
    }
    
    showNotification(message, type = 'info') {
        const container = document.getElementById('notificationContainer');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        container.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.growwiz = new GrowWizDashboard();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (window.growwiz) {
        if (document.hidden) {
            console.log('Page hidden - pausing updates');
        } else {
            console.log('Page visible - resuming updates');
            window.growwiz.testConnection();
        }
    }
});

// Handle window resize for chart
window.addEventListener('resize', () => {
    if (window.growwiz && window.growwiz.chart) {
        window.growwiz.chart.resize();
    }
});