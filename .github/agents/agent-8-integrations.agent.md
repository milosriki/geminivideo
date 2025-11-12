# Agent 8: API Integration Engineer

## Your Mission
Implement Google Drive API and GCS storage integration.

## Priority: MEDIUM (Wait for Agent 1 DB)

## Tasks

### 1. Install Dependencies
```bash
pip install google-cloud-storage google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 2. Google Drive Integration
Create `services/drive-intel/src/integrations/drive.py`:
```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class DriveClient:
    def __init__(self):
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Drive API"""
        creds = None

        # Load saved credentials
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)

    def list_videos_in_folder(self, folder_id: str):
        """List all video files in a Drive folder"""
        query = f"'{folder_id}' in parents and mimeType contains 'video/'"

        results = self.service.files().list(
            q=query,
            pageSize=100,
            fields="files(id, name, mimeType, size, createdTime)"
        ).execute()

        return results.get('files', [])

    def download_video(self, file_id: str, output_path: str):
        """Download video file from Drive"""
        from googleapiclient.http import MediaIoBaseDownload
        import io

        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%")

        # Write to file
        fh.seek(0)
        with open(output_path, 'wb') as f:
            f.write(fh.read())

        return output_path

    def get_file_metadata(self, file_id: str):
        """Get file metadata"""
        return self.service.files().get(
            fileId=file_id,
            fields='id, name, mimeType, size, videoMediaMetadata, createdTime'
        ).execute()

# Global client
drive_client = DriveClient()
```

### 3. GCS Storage Integration
Create `services/gateway-api/src/storage/gcs.ts`:
```typescript
import { Storage } from '@google-cloud/storage';
import * as fs from 'fs';
import * as path from 'path';

export class GCSKnowledgeStore {
  private storage: Storage;
  private bucketName: string;

  constructor(bucketName: string) {
    this.storage = new Storage();
    this.bucketName = bucketName;
  }

  async uploadKnowledge(category: string, fileName: string, content: Buffer) {
    const file = this.storage.bucket(this.bucketName).file(`knowledge/${category}/${fileName}`);

    await file.save(content, {
      metadata: {
        contentType: 'application/json',
        uploadedAt: new Date().toISOString()
      }
    });

    return `gs://${this.bucketName}/knowledge/${category}/${fileName}`;
  }

  async downloadKnowledge(category: string, fileName: string): Promise<Buffer> {
    const file = this.storage.bucket(this.bucketName).file(`knowledge/${category}/${fileName}`);
    const [contents] = await file.download();
    return contents;
  }

  async listKnowledge(category: string): Promise<string[]> {
    const [files] = await this.storage.bucket(this.bucketName).getFiles({
      prefix: `knowledge/${category}/`
    });

    return files.map(file => file.name);
  }

  async syncLocalToGCS(localPath: string, gcsPath: string) {
    const files = fs.readdirSync(localPath);

    for (const file of files) {
      const filePath = path.join(localPath, file);
      const stat = fs.statSync(filePath);

      if (stat.isFile()) {
        const contents = fs.readFileSync(filePath);
        await this.uploadKnowledge(gcsPath, file, contents);
        console.log(`Synced: ${file} -> gs://${this.bucketName}/${gcsPath}/${file}`);
      }
    }
  }

  async getActiveVersion(category: string): Promise<any> {
    try {
      const metaFile = `knowledge/${category}/_meta.json`;
      const file = this.storage.bucket(this.bucketName).file(metaFile);
      const [contents] = await file.download();
      return JSON.parse(contents.toString());
    } catch (error) {
      return { version: '1.0.0', active_files: [] };
    }
  }

  async activateVersion(category: string, version: string, files: string[]) {
    const metaFile = `knowledge/${category}/_meta.json`;
    const meta = {
      version,
      active_files: files,
      activated_at: new Date().toISOString()
    };

    const file = this.storage.bucket(this.bucketName).file(metaFile);
    await file.save(JSON.stringify(meta, null, 2));

    return meta;
  }
}

// Global instance
export const knowledgeStore = new GCSKnowledgeStore(
  process.env.GCS_BUCKET || 'ai-studio-bucket-208288753973-us-west1'
);
```

### 4. Update Drive Intel Service
Update `services/drive-intel/src/main.py`:
```python
from integrations.drive import drive_client

@app.post("/ingest/drive/folder")
async def ingest_drive_folder(folder_id: str, db: Session = Depends(get_db)):
    """Ingest videos from Google Drive folder"""
    try:
        # List videos
        videos = drive_client.list_videos_in_folder(folder_id)

        asset_ids = []
        for video in videos:
            # Download video
            temp_path = f"/tmp/{video['id']}.mp4"
            drive_client.download_video(video['id'], temp_path)

            # Create asset
            asset = Asset(
                path=temp_path,
                filename=video['name'],
                size_bytes=int(video.get('size', 0)),
                duration_seconds=0,  # Will be extracted
                resolution="unknown",
                format="mp4",
                status="processing",
                source="google_drive"
            )
            db.add(asset)
            db.commit()
            db.refresh(asset)

            asset_ids.append(str(asset.asset_id))

            # Trigger processing
            asyncio.create_task(process_asset(str(asset.asset_id), db))

        return {
            "folder_id": folder_id,
            "assets_ingested": len(asset_ids),
            "asset_ids": asset_ids
        }
    except Exception as e:
        raise HTTPException(500, f"Drive ingestion failed: {str(e)}")
```

### 5. Update Gateway API Knowledge Endpoints
Update `services/gateway-api/src/knowledge.ts`:
```typescript
import { Router } from 'express';
import { knowledgeStore } from './storage/gcs';
import multer from 'multer';

const upload = multer({ storage: multer.memoryStorage() });
const router = Router();

router.post('/upload', upload.single('file'), async (req, res) => {
  try {
    const { category, subcategory } = req.body;
    const file = req.file;

    if (!file) {
      return res.status(400).json({ error: 'No file provided' });
    }

    const path = subcategory ? `${category}/${subcategory}` : category;
    const gcsPath = await knowledgeStore.uploadKnowledge(path, file.originalname, file.buffer);

    res.json({
      upload_id: Date.now().toString(),
      gcs_path: gcsPath,
      status: 'uploaded',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/activate', async (req, res) => {
  const { category, version, files } = req.body;

  try {
    const meta = await knowledgeStore.activateVersion(category, version, files);

    res.json({
      status: 'active',
      version: meta.version,
      activated_at: meta.activated_at,
      affected_services: ['drive-intel', 'video-agent', 'meta-publisher']
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/status', async (req, res) => {
  const { category } = req.query;

  try {
    const meta = await knowledgeStore.getActiveVersion(category as string);
    const files = await knowledgeStore.listKnowledge(category as string);

    res.json({
      category,
      active_version: meta.version,
      last_updated: meta.activated_at,
      files: files.map(f => ({
        name: f,
        gcs_path: `gs://${knowledgeStore.bucketName}/${f}`
      }))
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
```

### 6. Sync Script
Create `scripts/sync_config_to_gcs.sh`:
```bash
#!/bin/bash

BUCKET="ai-studio-bucket-208288753973-us-west1"

echo "Syncing config to GCS..."
gsutil -m rsync -r ./shared/config gs://${BUCKET}/config/

echo "Syncing knowledge base..."
gsutil -m rsync -r ./knowledge gs://${BUCKET}/knowledge/

echo "Sync complete!"
```

## Deliverables
- [ ] Google Drive API integration
- [ ] Video download from Drive
- [ ] GCS knowledge store
- [ ] Knowledge upload/activate/status endpoints
- [ ] Config sync script
- [ ] Tests for integrations

## Branch
`agent-8-api-integrations`

## Blockers
- **Agent 1** (needs DB)
- Google Cloud credentials setup (manual)

## Who Depends On You
- Agent 10 (DevOps needs sync scripts)
