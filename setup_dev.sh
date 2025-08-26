#!/bin/bash
set -e

echo "🚀 Setting up WyreStorm NetworkHD Home Assistant Integration Development Environment"

# Create development directories
echo "📁 Creating development directories..."
mkdir -p ha-dev/config/custom_components
mkdir -p ha-dev/config/.storage
mkdir -p custom_components/wyrestorm_networkhd
mkdir -p tests

# Create basic HA configuration
echo "⚙️ Creating Home Assistant configuration..."
cat > ha-dev/config/configuration.yaml << 'EOF'
# Loads default set of integrations. Do not remove.
default_config:

# Load frontend themes from the themes folder
frontend:
  themes: !include_dir_merge_named themes

# Enable the logger
logger:
  default: info
  logs:
    custom_components.wyrestorm_networkhd: debug
    wyrestorm_networkhd: debug

# Enable development mode
developer:

# Text to speech
tts:
  - platform: google_translate

automation: !include automations.yaml
script: !include scripts.yaml
scene: !include scenes.yaml
EOF

# Create empty automation files
touch ha-dev/config/automations.yaml
touch ha-dev/config/scripts.yaml 
touch ha-dev/config/scenes.yaml

# Create themes directory
mkdir -p ha-dev/config/themes
echo "# Custom themes go here" > ha-dev/config/themes/.gitkeep

# Make sure Docker can write to these directories
chmod -R 755 ha-dev/config

echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Run: docker-compose up -d"
echo "2. Wait for HA to start (check logs: docker-compose logs -f homeassistant)"
echo "3. Open http://localhost:8123"
echo "4. Complete the HA setup wizard"
echo "5. Your integration will be available in Configuration > Integrations"
echo ""
echo "Development commands:"
echo "• Start:   docker-compose up -d"
echo "• Stop:    docker-compose down" 
echo "• Logs:    docker-compose logs -f homeassistant"
echo "• Restart: docker-compose restart homeassistant"