#!/usr/bin/env bash
# Bot service entrypoint: starts PulseAudio with our virtual sink, waits for
# the socket to be ready, then launches the FastAPI server.
#
# We run PulseAudio in *user* mode (not --system) since system mode requires a
# real OS user and is documented as not for general use. A long
# --exit-idle-time=-1 keeps it alive for the lifetime of the container even
# when no client is connected.
set -euo pipefail

PULSE_SOCKET="${PULSE_SERVER#unix:}"
PULSE_SOCKET="${PULSE_SOCKET:-/tmp/pulseaudio.socket}"

# Clean any stale socket from previous runs.
rm -f "$PULSE_SOCKET"

# Start PulseAudio. The --file flag points at our config which loads:
#   - module-native-protocol-unix on $PULSE_SOCKET
#   - module-null-sink sink_name=vaktram_sink
#   - sets vaktram_sink as the default
pulseaudio \
  --start \
  --exit-idle-time=-1 \
  --file=/etc/pulse/default.pa \
  --log-target=stderr \
  -vvv

# Wait up to 10s for the socket to appear before starting the API.
for i in $(seq 1 20); do
  if [ -S "$PULSE_SOCKET" ]; then
    echo "PulseAudio socket ready at $PULSE_SOCKET"
    break
  fi
  sleep 0.5
done

if [ ! -S "$PULSE_SOCKET" ]; then
  echo "PulseAudio socket never appeared — audio capture will fail" >&2
  exit 1
fi

# Verify the virtual sink is loaded; if not, load it on the fly so the
# capture path works even if pulseaudio.conf was overridden.
if ! pactl list short sinks | grep -q vaktram_sink; then
  echo "Loading vaktram_sink module..."
  pactl load-module module-null-sink \
    sink_name=vaktram_sink \
    sink_properties=device.description=Vaktram_Virtual_Sink
  pactl set-default-sink vaktram_sink
fi

echo "PulseAudio ready. Default sink:"
pactl get-default-sink || true

exec uvicorn bot.main:app --host 0.0.0.0 --port "${BOT_SERVICE_PORT:-8001}"
