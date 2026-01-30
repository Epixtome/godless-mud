#!/bin/bash
echo "Starting Godless MUD..."
nohup python3 -u godless_mud.py > server.log 2>&1 &
echo "Server running in background. Logs at server.log"
#asdsdfsdfsdgfsdg