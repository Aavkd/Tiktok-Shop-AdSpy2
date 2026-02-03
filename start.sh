#!/bin/bash
# Start Node.js signature service in background
node index.js &
NODE_PID=$!

# Wait for service to be ready (simple sleep or curl loop)
echo "Waiting for signature service..."
sleep 5

# Run Python monitor
# Pass arguments if any (for local docker run with args)
# But also rely on Apify Input via environment if available
python3 src/monitor.py "$@"

# Kill Node service when Python finishes
kill $NODE_PID
