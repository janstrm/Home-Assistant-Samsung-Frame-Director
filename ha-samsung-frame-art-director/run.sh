#!/usr/bin/with-contenv bashio

# Fetch configuration options using bashio
TV_IP=$(bashio::config 'tv')
PHOTO_FILTER=$(bashio::config 'photo_filter')
MATTE=$(bashio::config 'matte')
MATTE_COLOR=$(bashio::config 'matte_color')
AI_ENABLED=$(bashio::config 'ai_art_enabled')
ROTATION_INTERVAL=$(bashio::config 'rotation_interval')
ENSURE_ONLY=$(bashio::config 'ensure_art_mode_only')
DEBUG_ENABLED=$(bashio::config 'debug')

mkdir -p /media/frame

bashio::log.info "Starting Samsung Frame Art Changer..."
bashio::log.info "Target TV IP: ${TV_IP}"
bashio::log.info "Matte setting: ${MATTE}"

if bashio::config.true 'debug'; then
  bashio::log.level "debug"
fi

AI_PROMPT=$(bashio::config 'ai_art_prompt')
API_KEY=$(bashio::config 'api_key')

exec python3 art.py \
  --ip "${TV_IP}" \
  --filter "${PHOTO_FILTER}" \
  --matte "${MATTE}" \
  --matte-color "${MATTE_COLOR}" \
  --rotation-interval "${ROTATION_INTERVAL}" \
  $(bashio::config.true 'ai_art_enabled' && echo --ai-art) \
  $(bashio::config.true 'ensure_art_mode_only' && echo --show-only) \
  $(bashio::config.true 'debug' && echo --debug) \
  --prompt "${AI_PROMPT}" \
  --api-key "${API_KEY}"

