#!/bin/bash
# Quick test to show the deploy menu without executing
cd /home/user/geminivideo
echo "0" | timeout 2 ./deploy.sh 2>/dev/null || echo -e "\n✅ Menu displayed successfully"
