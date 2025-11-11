# Frontend - AI Ad Intelligence Suite

React + Vite frontend for the AI Ad Intelligence & Creation Suite.

## Features

- **Assets Management**: View and manage ingested video assets
- **Ranked Clips**: Browse clips ranked by engagement potential
- **Storyboard Builder**: Select and arrange clips for ad creation
- **Render Job UI**: Queue and monitor video rendering jobs

## Pages

1. **Assets** (`/`) - List all video assets with status
2. **Ranked Clips** (`/clips/:assetId`) - View ranked clips for an asset
3. **Render Job** (`/render`) - Create and monitor render jobs

## Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Configure the gateway URL:
- `VITE_GATEWAY_URL` - URL of the gateway API service

## Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Docker

```bash
# Build image
docker build -t frontend .

# Run container
docker run -p 80:80 frontend
```

## Tech Stack

- React 19
- TypeScript
- Vite 7
- React Router 6
- CSS Modules
