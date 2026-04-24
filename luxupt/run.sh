#!/usr/bin/env bash

# Source bashio library
source /usr/lib/bashio/bashio

bashio::log.info "Starting LuxUPT Add-on..."

# =============================================================================
# Read UniFi Protect Configuration
# =============================================================================
if bashio::config.exists 'unifi_protect.api_key'; then
    export UNIFI_PROTECT_API_KEY=$(bashio::config 'unifi_protect.api_key')
fi

if bashio::config.exists 'unifi_protect.base_url'; then
    export UNIFI_PROTECT_BASE_URL=$(bashio::config 'unifi_protect.base_url')
fi

export UNIFI_PROTECT_VERIFY_SSL=$(bashio::config 'unifi_protect.verify_ssl')

# =============================================================================
# Read Web Configuration
# =============================================================================
if bashio::config.exists 'web.username'; then
    export WEB_USERNAME=$(bashio::config 'web.username')
fi

if bashio::config.exists 'web.password'; then
    export WEB_PASSWORD=$(bashio::config 'web.password')
fi

# =============================================================================
# Read Logging Configuration
# =============================================================================
LOG_LEVEL=$(bashio::config 'log_level')
export LOGGING_LEVEL="${LOG_LEVEL^^}"  # Convert to uppercase

# =============================================================================
# Set Output Paths
# =============================================================================
# Use /share for HA integration
export IMAGE_OUTPUT_PATH="/share/luxupt/images"
export VIDEO_OUTPUT_PATH="/share/luxupt/videos"
export THUMBNAIL_CACHE_PATH="/share/luxupt/thumbnails"

# SQLite DB Path (store in /share so it persists and is backed up)
export SQLITE_DB_PATH="/share/luxupt/data.db"

# Create directories
mkdir -p "${IMAGE_OUTPUT_PATH}"
mkdir -p "${VIDEO_OUTPUT_PATH}"
mkdir -p "${THUMBNAIL_CACHE_PATH}"

# =============================================================================
# Start Application
# =============================================================================
bashio::log.info "Configuration loaded, starting LuxUPT application..."

cd /app/luxupt
exec ./entrypoint.sh
