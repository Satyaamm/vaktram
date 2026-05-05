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

# Wipe ALL pulseaudio state from the previous container run. Without this,
# the FIRST run succeeds (clean slate) but every restart fails with
# "Daemon startup failed" because pulseaudio left:
#   • /tmp/pulseaudio.socket            ← the socket itself
#   • /tmp/pulse-runtime/cli + pid + …   ← runtime state, locked by old PID
#   • /root/.config/pulse/<machine-id>*  ← stamps with cookies and IDs
# The first launch creates them fresh; the second sees them and refuses
# to start a new instance. We delete everything so each restart is a
# clean slate.
rm -f "$PULSE_SOCKET"
rm -rf /tmp/pulse-runtime /tmp/pulse-* /root/.config/pulse 2>/dev/null || true

# CRITICAL: PULSE_SERVER tells *clients* where the daemon lives. The daemon
# itself, on seeing PULSE_SERVER set, thinks "a daemon is already running
# at that path" and refuses to start with:
#   "User-configured server at unix:..., refusing to start/autospawn."
# Strip the var for the duration of the daemon launch, then restore it
# below so uvicorn / ffmpeg can connect.
SAVED_PULSE_SERVER="${PULSE_SERVER:-}"
unset PULSE_SERVER

# pulseaudio also refuses --start as root unless we either (a) pass
# --system, which needs a real `pulse` OS user, or (b) set
# PULSE_RUNTIME_PATH so it stops complaining about the default
# /run/user/0 path. We take path (b): the warning "not intended to run
# as root" is benign — what blocks startup is the PULSE_SERVER detection
# above plus the missing runtime path.
export PULSE_RUNTIME_PATH="${PULSE_RUNTIME_PATH:-/tmp/pulse-runtime}"
mkdir -p "$PULSE_RUNTIME_PATH"

# Start PulseAudio explicitly in the background. We use --daemonize rather
# than --start because --start runs a "server already running?" check via
# PULSE_SERVER which behaves unpredictably in containers. --daemonize is
# the unambiguous "fork into the background" path.
#
# The --file flag points at our config which loads:
#   - module-native-protocol-unix on $PULSE_SOCKET
#   - module-null-sink sink_name=vaktram_sink
#   - sets vaktram_sink as the default
pulseaudio \
  --daemonize=yes \
  --exit-idle-time=-1 \
  --disallow-exit \
  --file=/etc/pulse/default.pa \
  --log-target=stderr \
  -vvv || {
    echo "pulseaudio --daemonize failed; tailing system logs for context:" >&2
    pulseaudio --check && echo "(daemon already running)" >&2 || true
    exit 1
  }

# Restore PULSE_SERVER for everything we exec from here down (clients).
if [ -n "$SAVED_PULSE_SERVER" ]; then
  export PULSE_SERVER="$SAVED_PULSE_SERVER"
fi

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

exec uvicorn bot.main:app --host 0.0.0.0 --port "${BOT_SERVICE_PORT:-1003}"
