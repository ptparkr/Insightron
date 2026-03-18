/**
 * Insightron Web Application Logic
 * Vanilla JS
 */

 class App {
    constructor() {
        this.currentView = 'single';
        this.statusEl = document.getElementById('system-status');
        this.statusDot = document.querySelector('.status-dot');
        this.terminalLog = document.getElementById('terminal-log');
        
        // State
        this.singleFile = null;
        this.batchFiles = [];
        this.isRecording = false;
        
        // WebSocket / Audio Context for Realtime
        this.ws = null;
        this.audioContext = null;
        this.mediaStream = null;
        this.audioScriptProcessor = null;
        this.visualizerCanvas = document.getElementById('audio-visualizer');
        this.visualizerCtx = this.visualizerCanvas.getContext('2d');
        this.animationId = null;
        this.audioLevel = 0;

        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupFileInputs();
        this.setupButtons();
        this.setupRealtime();
        this.loadSettings();

        // Handle canvas resize
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());

        this.log("UI Initialized. Waiting for server connection...", "info");
    }

    /* --- Navigation --- */
    setupNavigation() {
        const navBtns = document.querySelectorAll('.nav-btn');
        navBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const target = e.currentTarget.dataset.target;
                
                // Update active state
                navBtns.forEach(b => b.classList.remove('active'));
                e.currentTarget.classList.add('active');

                // Update views
                document.querySelectorAll('.view-section').forEach(view => {
                    view.classList.add('hidden');
                    view.classList.remove('active');
                });
                const newView = document.getElementById(`view-${target}`);
                newView.classList.remove('hidden');
                
                // Trigger reflow to restart animation
                void newView.offsetWidth;
                newView.classList.add('active');

                this.currentView = target;
                this.updateHeaderTitles(target);
            });
        });
    }

    updateHeaderTitles(view) {
        const titles = {
            'single': { title: 'Single File Transcription', desc: 'Transcribe a single audio file with high accuracy.' },
            'batch': { title: 'Batch Mode Transcription', desc: 'Process many audio files at once.' },
            'realtime': { title: 'Realtime Transcription', desc: 'Transcribe live audio from your microphone.' },
            'settings': { title: 'Application Settings', desc: 'Configure AI models and language preferences.' }
        };
        document.getElementById('current-view-title').textContent = titles[view].title;
        document.getElementById('current-view-desc').textContent = titles[view].desc;
    }

    /* --- File Inputs --- */
    setupFileInputs() {
        // Single File
        const singleUploadArea = document.getElementById('single-upload');
        const singleInput = document.getElementById('single-file-input');
        
        singleUploadArea.addEventListener('dragover', (e) => { e.preventDefault(); singleUploadArea.classList.add('dragover'); });
        singleUploadArea.addEventListener('dragleave', () => singleUploadArea.classList.remove('dragover'));
        singleUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            singleUploadArea.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                this.handleSingleFileSelect(e.dataTransfer.files[0]);
            }
        });
        singleInput.addEventListener('change', (e) => {
            if (e.target.files.length) this.handleSingleFileSelect(e.target.files[0]);
        });

        // Batch Files
        const batchUploadArea = document.getElementById('batch-upload');
        const batchInput = document.getElementById('batch-file-input');
        
        batchUploadArea.addEventListener('dragover', (e) => { e.preventDefault(); batchUploadArea.classList.add('dragover'); });
        batchUploadArea.addEventListener('dragleave', () => batchUploadArea.classList.remove('dragover'));
        batchUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            batchUploadArea.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                this.batchFiles = Array.from(e.dataTransfer.files);
                this.updateBatchDisplay();
            }
        });
        batchInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                this.batchFiles = Array.from(e.target.files);
                this.updateBatchDisplay();
            }
        });
    }

    handleSingleFileSelect(file) {
        this.singleFile = file;
        const display = document.getElementById('single-selected-file');
        display.querySelector('.filename').textContent = file.name;
        display.classList.remove('hidden');
        document.getElementById('btn-transcribe-single').disabled = false;
        this.log(`Selected single file: ${file.name}`);
    }

    removeSingleFile() {
        this.singleFile = null;
        document.getElementById('single-file-input').value = "";
        document.getElementById('single-selected-file').classList.add('hidden');
        document.getElementById('btn-transcribe-single').disabled = true;
    }

    updateBatchDisplay() {
        const display = document.getElementById('batch-selected-files');
        const validExts = ['mp3', 'wav', 'm4a', 'flac', 'mp4', 'ogg', 'aac', 'wma'];
        
        // Filter out non-audio/video files heuristically if from folder
        let count = this.batchFiles.length;
        
        display.querySelector('.filename').textContent = `${count} files selected`;
        display.classList.remove('hidden');
        document.getElementById('btn-transcribe-batch').disabled = count === 0;
        this.log(`Selected ${count} files for batch processing.`);
    }

    /* --- Actions --- */
    setupButtons() {
        document.getElementById('btn-transcribe-single').addEventListener('click', () => this.transcribeSingle());
        document.getElementById('btn-transcribe-batch').addEventListener('click', () => this.transcribeBatch());
        document.getElementById('btn-save-settings').addEventListener('click', () => this.saveSettings());
    }

    setStatus(status, type = 'info') {
        this.statusEl.textContent = status;
        this.statusDot.className = 'status-dot'; // reset
        if (type === 'success') this.statusDot.classList.add('green');
        else if (type === 'error') this.statusDot.classList.add('red');
        else if (type === 'warning' || type === 'processing') this.statusDot.classList.add('orange');
        else this.statusDot.classList.add('green');
    }

    showProgress(text = "Processing...") {
        document.getElementById('main-progress').classList.remove('hidden');
        document.querySelector('#main-progress .progress-text').textContent = text;
        this.setStatus(text, 'processing');
    }

    hideProgress() {
        document.getElementById('main-progress').classList.add('hidden');
        this.setStatus('Systems Ready', 'success');
    }

    log(message, type = 'normal') {
        const line = document.createElement('div');
        line.className = `log-line ${type}`;
        
        const timestamp = new Date().toLocaleTimeString('en-US', {hour12: false});
        line.textContent = `[${timestamp}] ${message}`;
        
        this.terminalLog.appendChild(line);
        this.terminalLog.scrollTop = this.terminalLog.scrollHeight;
    }

    async transcribeSingle() {
        if (!this.singleFile) return;
        
        const formData = new FormData();
        formData.append('file', this.singleFile);
        
        this.showProgress("Transcribing File...");
        document.getElementById('btn-transcribe-single').disabled = true;
        this.log(`Uploading ${this.singleFile.name}...`, "info");

        try {
            const resp = await fetch('/api/transcribe', {
                method: 'POST',
                body: formData
            });
            const data = await resp.json();
            
            if (resp.ok) {
                this.log(`Transcription complete! Saved to ${data.filename}`, "success");
            } else {
                this.log(`Error: ${data.detail}`, "error");
            }
        } catch (e) {
            this.log(`Failed to connect to server: ${e.message}`, "error");
        } finally {
            this.hideProgress();
            document.getElementById('btn-transcribe-single').disabled = false;
        }
    }

    async transcribeBatch() {
        if (this.batchFiles.length === 0) return;
        
        const formData = new FormData();
        this.batchFiles.forEach(f => formData.append('files', f));
        
        this.showProgress(`Batch Processing ${this.batchFiles.length} files...`);
        document.getElementById('btn-transcribe-batch').disabled = true;
        this.log(`Starting batch upload...`, "info");

        try {
            const resp = await fetch('/api/batch', {
                method: 'POST',
                body: formData
            });
            const data = await resp.json();
            
            if (resp.ok) {
                this.log(`Batch complete! ${data.successful} processed, ${data.failed} failed.`, "success");
            } else {
                this.log(`Error: ${data.detail}`, "error");
            }
        } catch (e) {
            this.log(`Failed to run batch: ${e.message}`, "error");
        } finally {
            this.hideProgress();
            document.getElementById('btn-transcribe-batch').disabled = false;
        }
    }

    /* --- Settings --- */
    async loadSettings() {
        try {
            const resp = await fetch('/api/settings');
            if (resp.ok) {
                const data = await resp.json();
                document.getElementById('setting-model').value = data.model || 'medium';
                document.getElementById('setting-language').value = data.language || 'auto';
                document.getElementById('setting-formatting').value = data.formatting || 'auto';
            }
        } catch (e) {
            console.error("Failed to load settings", e);
        }
    }

    async saveSettings() {
        const btn = document.getElementById('btn-save-settings');
        const ogText = btn.textContent;
        btn.textContent = "Saving...";
        btn.disabled = true;

        const payload = {
            model: document.getElementById('setting-model').value,
            language: document.getElementById('setting-language').value,
            formatting: document.getElementById('setting-formatting').value
        };

        try {
            const resp = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            if (resp.ok) {
                this.log("Settings saved successfully.", "success");
            } else {
                this.log("Failed to save settings.", "error");
            }
        } catch (e) {
            this.log(`Error saving settings: ${e.message}`, "error");
        } finally {
            btn.textContent = ogText;
            btn.disabled = false;
        }
    }

    /* --- Realtime / Web Audio API --- */
    async setupRealtime() {
        document.getElementById('btn-refresh-mic').addEventListener('click', () => this.refreshMicrophones());
        document.getElementById('btn-record').addEventListener('click', () => this.toggleRecording());
        
        await this.refreshMicrophones();
        this.renderVisualizer();
    }

    async refreshMicrophones() {
        const select = document.getElementById('mic-select');
        select.innerHTML = '<option>Requesting access...</option>';
        
        try {
            // Request permission to list devices labels
            await navigator.mediaDevices.getUserMedia({ audio: true });
            const devices = await navigator.mediaDevices.enumerateDevices();
            const audioDevices = devices.filter(d => d.kind === 'audioinput');
            
            select.innerHTML = '';
            if (audioDevices.length === 0) {
                select.innerHTML = '<option>No microphones found</option>';
            } else {
                audioDevices.forEach(d => {
                    const opt = document.createElement('option');
                    opt.value = d.deviceId;
                    opt.textContent = d.label || `Microphone ${select.length + 1}`;
                    select.appendChild(opt);
                });
            }
        } catch (e) {
            select.innerHTML = '<option value="">Permission denied</option>';
            this.log('Microphone access denied: ' + e.message, 'error');
        }
    }

    async toggleRecording() {
        const btn = document.getElementById('btn-record');
        
        if (this.isRecording) {
            this.stopRecording();
            btn.classList.remove('recording');
            btn.querySelector('.btn-text').textContent = 'START RECORDING';
            btn.classList.add('btn-danger');
            btn.classList.remove('btn-secondary');
        } else {
            const success = await this.startRecording();
            if (success) {
                btn.classList.add('recording');
                btn.querySelector('.btn-text').textContent = 'STOP RECORDING';
                btn.classList.remove('btn-danger');
                btn.classList.add('btn-secondary');
            }
        }
    }

    async startRecording() {
        this.log("Initializing WebSocket for Realtime...", "info");
        const deviceId = document.getElementById('mic-select').value;
        if (!deviceId) {
            alert('Please select a microphone or grant permissions.');
            return false;
        }

        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 16000 // Whisper expects 16kHz
            });

            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: { deviceId: { exact: deviceId } }
            });

            // WebSocket Connection
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            this.ws = new WebSocket(`${protocol}//${window.location.host}/api/realtime`);
            
            this.ws.onopen = () => {
                this.log("Connected to Realtime Transcription Engine.", "success");
                this.setStatus("Recording Live...", "processing");
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'transcript') {
                    this.log(`🗣️ ${data.text}`, (data.is_final ? "success" : "normal"));
                } else if (data.type === 'error') {
                    this.log(`WebSocket Error: ${data.message}`, "error");
                }
            };
            
            this.ws.onerror = (e) => this.log("WebSocket connection error.", "error");

            // Process Audio
            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            const bufferSize = 4096;
            this.audioScriptProcessor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);
            
            source.connect(this.audioScriptProcessor);
            this.audioScriptProcessor.connect(this.audioContext.destination);
            
            this.audioScriptProcessor.onaudioprocess = (e) => {
                const inputData = e.inputBuffer.getChannelData(0);
                
                // Calculate level for visualizer
                let sum = 0;
                for (let i = 0; i < inputData.length; i++) {
                    sum += inputData[i] * inputData[i];
                }
                const rms = Math.sqrt(sum / inputData.length);
                this.audioLevel = Math.min(1.0, rms * 5.0); // Boost level visually

                // Send raw float32 to backend
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(inputData.buffer);
                }
            };

            this.isRecording = true;
            return true;
        } catch (e) {
            this.log(`Error starting recording: ${e.message}`, "error");
            return false;
        }
    }

    stopRecording() {
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }
        if (this.audioScriptProcessor) {
            this.audioScriptProcessor.disconnect();
            this.audioScriptProcessor = null;
        }
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
        if (this.ws) {
            // Signal EOF
            if (this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: "eof" }));
            }
            // wait a tick before closing to send EOF
            setTimeout(() => {
                this.ws.close();
                this.ws = null;
            }, 500);
        }
        
        this.audioLevel = 0;
        this.isRecording = false;
        this.setStatus("Systems Ready", "success");
        this.log("Recording stopped and session closed.", "info");
    }

    /* --- Visualizer --- */
    resizeCanvas() {
        const container = this.visualizerCanvas.parentElement;
        this.visualizerCanvas.width = container.clientWidth;
        this.visualizerCanvas.height = container.clientHeight;
    }

    renderVisualizer() {
        const width = this.visualizerCanvas.width;
        const height = this.visualizerCanvas.height;
        const ctx = this.visualizerCtx;
        
        ctx.clearRect(0, 0, width, height);

        if (width > 0 && height > 0) {
            const numBars = 64;
            const barWidth = (width / numBars) - 2;
            const center = height / 2;

            for (let i = 0; i < numBars; i++) {
                // Generate a pseudo-random bar height modified by real audio level
                // Creates a nice symmetric waveform effect
                const distanceFromCenter = Math.abs((numBars/2) - i) / (numBars/2);
                const randomScale = 0.2 + (Math.sin(Date.now() / 100 + i) * 0.5 + 0.5) * 0.8;
                
                // Base idle animation + audio level reaction
                const idleLevel = 0.05 * (1 - distanceFromCenter);
                const activeLevel = this.audioLevel * randomScale * (1 - (Math.pow(distanceFromCenter, 2)));
                
                const currentLevel = Math.max(idleLevel, activeLevel);
                const barHeight = Math.max(2, currentLevel * height);
                
                const x = i * (width / numBars);
                
                // Draw gradient bar
                const gradient = ctx.createLinearGradient(0, center - barHeight/2, 0, center + barHeight/2);
                gradient.addColorStop(0, 'rgba(88, 166, 255, 0)');
                gradient.addColorStop(0.5, 'var(--primary)');
                gradient.addColorStop(1, 'rgba(88, 166, 255, 0)');
                
                ctx.fillStyle = gradient;
                
                // Rounded bar
                ctx.beginPath();
                ctx.roundRect(x, center - barHeight/2, barWidth, barHeight, 4);
                ctx.fill();
            }
        }
        
        this.animationId = requestAnimationFrame(() => this.renderVisualizer());
    }
}

// Initialize when ready
window.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
