# Cloud Desktop / VM Setup Guide (Error-Free)

This guide is designed for a fresh **Ubuntu/Debian** cloud machine (AWS EC2, Google Compute Engine, DigitalOcean, or a Cloud Desktop).

## 1. Prepare the System (The "Bulletproof" Script)

Run this single block of commands to install all necessary dependencies (Docker, Git, Python) and configure permissions. This avoids 99% of common errors.

```bash
# Update system and install prerequisites
sudo apt-get update && sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    git \
    python3 \
    python3-pip \
    make

# Install Docker (Official Script)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to the docker group (avoids "permission denied" errors)
sudo usermod -aG docker $USER

# Install Docker Compose (if not included in plugin)
sudo apt-get install -y docker-compose-plugin

# Activate group changes (so you don't have to logout/login)
newgrp docker
```

## 2. Clone the Repository

```bash
git clone https://github.com/milosriki/geminivideo.git
cd geminivideo
```

## 3. Configure Secrets (Crucial Step)

You cannot run the app without the `.env` file. Since it's not in git, you must create it.

1.  **Create the file:**
    ```bash
    cp .env.example .env
    nano .env
    ```

2.  **Paste your keys:**
    *   Use `Ctrl+V` to paste your API keys (Gemini, OpenAI, Anthropic, Meta, Firebase).
    *   Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

## 4. Launch the Application

Now that dependencies and secrets are ready, launch the system.

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Start everything (this will take ~5-10 mins on first run to download models)
./scripts/start-all.sh
```

## 5. Accessing the App

*   **If using a Cloud VM (SSH):** You need to forward ports or open firewall rules.
    *   **Frontend:** Open port `3000`
    *   **API:** Open port `8000`
    *   *SSH Tunnel (Secure way):* `ssh -L 3000:localhost:3000 -L 8000:localhost:8000 user@your-cloud-ip`
    *   Then open `http://localhost:3000` on your local laptop.

*   **If using a Remote Desktop (GUI):**
    *   Open the browser inside the remote desktop.
    *   Go to `http://localhost:3000`.

## Common Troubleshooting

*   **"Docker daemon not running":** Run `sudo service docker start`.
*   **"Permission denied":** Run `newgrp docker` again or restart the machine.
*   **"No space left on device":** Cloud VMs often have small disks. Ensure you have at least 20GB free.
    *   Check with: `df -h`
    *   Clean up: `docker system prune -a`
