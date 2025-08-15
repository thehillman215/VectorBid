
#!/usr/bin/env python3
"""
Smart server starter that finds available ports
"""

import os
import socket
import subprocess
import sys

def find_free_port(start_port=5000, max_attempts=10):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                print(f"✅ Found available port: {port}")
                return port
        except OSError:
            print(f"⚠️ Port {port} is in use, trying next...")
            continue
    
    print(f"❌ No free ports found in range, using fallback port 8080")
    return 8080

def start_gunicorn():
    """Start Gunicorn with automatic port detection"""
    port = find_free_port(5000)
    
    # Validate port number (defensive programming)
    if not isinstance(port, int) or port < 1 or port > 65535:
        raise ValueError(f"Invalid port number: {port}")
    
    # Set environment variable for other parts of the app
    os.environ['PORT'] = str(port)
    
    # Build gunicorn command
    cmd = [
        'gunicorn',
        '--bind', f'0.0.0.0:{port}',
        '--reuse-port',
        '--reload',
        'main:app'
    ]
    
    print(f"🚀 Starting Gunicorn on port {port}")
    print(f"📱 Your app will be available at: https://{os.environ.get('REPL_SLUG', 'your-repl')}-{os.environ.get('REPL_OWNER', 'username')}.replit.app:{port}")
    
    # Start Gunicorn
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_gunicorn()
