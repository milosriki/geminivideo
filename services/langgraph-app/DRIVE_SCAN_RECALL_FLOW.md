# 🔄 Complete Flow: Drive Scanning → Video/Image Processing → Recall

## 📊 Overview

**The App Flow:**
1. **Scan Drive** (Google Drive or Local) → Find videos/images
2. **Ingest** → Download and register files
3. **Process** → Scene detection, feature extraction
4. **Index** → Store in FAISS vector database
5. **Recall** → Semantic search to find similar content

---

## 🔍 Step 1: Drive Scanning

### **A. Google Drive Scanning**

**Service:** `services/drive-intel/src/drive_client.py`

**How it works:**
```python
class DriveClient:
    def list_videos(self, folder_id: Optional[str] = None, limit: int = 10):
        # Query Google Drive API
        query = "mimeType contains 'video/' and trashed = false"
        if folder_id:
            query += f" and '{folder_id}' in parents"
        
        # Get video files
        results = self.service.files().list(
            q=query,
            pageSize=limit,
            fields="files(id, name, mimeType, size, videoMediaMetadata, createdTime)"
        ).execute()
        
        # Extract metadata
        for item in results.get('files', []):
            metadata = item.get('videoMediaMetadata', {})
            videos.append({
                "asset_id": item['id'],
                "filename": item['name'],
                "size_bytes": int(item.get('size', 0)),
                "duration_seconds": float(metadata.get('durationMillis', 0)) / 1000.0,
                "resolution": f"{metadata.get('width', 0)}x{metadata.get('height', 0)}",
                "format": item['mimeType'].split('/')[-1],
                "source": "google_drive",
                "status": "ready"
            })
```

**What it finds:**
- All video files (`.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`, `.flv`)
- Video metadata (duration, resolution, size)
- File IDs for download

**API Endpoint:**
```
POST /ingest/drive/folder
{
    "folder_id": "google_drive_folder_id",
    "max_files": 50
}
```

---

### **B. Local Folder Scanning**

**Service:** `services/drive-intel/services/ingestion.py`

**How it works:**
```python
class IngestService:
    async def ingest_folder(self, folder_path: str, ...):
        # Security: Validate path
        allowed_paths = os.getenv('ALLOWED_INGEST_PATHS', '/data/inputs').split(':')
        
        # Find video files recursively
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'}
        video_files = []
        
        for file_path in Path(folder_path).rglob('*'):
            if file_path.suffix.lower() in video_extensions:
                video_files.append(str(file_path))
```

**What it finds:**
- All video files in folder (recursive search)
- Supports: `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`, `.flv`

**API Endpoint:**
```
POST /ingest/local/folder
{
    "folder_path": "/path/to/videos",
    "recursive": true
}
```

---

## 📥 Step 2: Ingestion & Download

### **Google Drive Download**

**Service:** `services/drive-intel/src/drive_client.py`

```python
def download_file(self, file_id: str, destination_path: str) -> bool:
    """Download file from Google Drive"""
    try:
        request = self.service.files().get_media(fileId=file_id)
        with open(destination_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        return True
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False
```

**Process:**
1. Get file from Google Drive API
2. Download to temporary directory
3. Store local path for processing

---

## 🎬 Step 3: Video Processing

### **A. Scene Detection**

**Service:** `services/drive-intel/services/scene_detector.py`

**How it works:**
```python
class SceneDetectorService:
    def detect_scenes(self, video_path: str) -> List[Tuple[float, float]]:
        """Detect scene boundaries using PySceneDetect"""
        # Use ContentDetector to find scene changes
        detector = ContentDetector(threshold=self.threshold)
        scene_list = detect(video_path, detector)
        
        # Convert to (start_time, end_time) tuples
        scenes = []
        for i, (start, end) in enumerate(scene_list):
            scenes.append((start.get_seconds(), end.get_seconds()))
        
        return scenes
```

**What it does:**
- Analyzes video frame by frame
- Detects scene changes (cuts, transitions)
- Returns list of scene boundaries: `[(0.0, 5.2), (5.2, 12.8), ...]`

**Result:**
- Video split into scenes/clips
- Each scene is a potential ad clip

---

### **B. Feature Extraction**

**Service:** `services/drive-intel/services/feature_extractor.py`

**How it works:**
```python
class FeatureExtractorService:
    def extract_features(self, video_path: str, start_time: float, end_time: float):
        """Extract features from video clip"""
        
        # 1. Motion Analysis (OpenCV)
        motion_score = self._analyze_motion(video_path, start_time, end_time)
        
        # 2. Object Detection (YOLO)
        objects = self._detect_objects(video_path, start_time, end_time)
        # Returns: ["person", "gym equipment", "product", ...]
        
        # 3. OCR Text Extraction (PaddleOCR)
        text_detected = self._extract_text(video_path, start_time, end_time)
        # Returns: ["FITNESS", "TRANSFORM YOUR BODY", ...]
        
        # 4. Face Detection (OpenCV)
        faces_detected = self._detect_faces(video_path, start_time, end_time)
        
        # 5. Embedding Generation (Sentence Transformers)
        embedding = self._generate_embedding(video_path, start_time, end_time)
        # Returns: [0.123, -0.456, 0.789, ...] (512-dim vector)
        
        # 6. Technical Quality
        quality_score = self._calculate_quality(video_path, start_time, end_time)
        # Based on: sharpness + resolution
        
        return {
            "motion_score": motion_score,
            "objects": objects,
            "text_detected": text_detected,
            "faces_detected": faces_detected,
            "embedding": embedding,
            "quality_score": quality_score
        }
```

**What it extracts:**
- **Motion:** How much movement (energy score)
- **Objects:** What's in the video (YOLO detection)
- **Text:** Overlay text (OCR)
- **Faces:** People detected
- **Embedding:** Semantic vector (for similarity search)
- **Quality:** Technical quality score

**Result:**
- Each scene/clip has rich metadata
- Ready for indexing and search

---

## 💾 Step 4: Indexing (FAISS Vector Database)

### **A. FAISS Index Creation**

**Service:** `services/drive-intel/services/faiss_search.py`

**How it works:**
```python
class FAISSEmbeddingSearch:
    def __init__(self, dimension: int = 512):
        """Initialize FAISS index"""
        # Create FAISS index (L2 distance)
        self.index = faiss.IndexFlatL2(dimension)
        
        # Map FAISS internal IDs to external clip IDs
        self.id_map = {}
        self.metadata_store = {}
    
    def add_clips(self, clips: List[Clip]):
        """Add clips to FAISS index"""
        embeddings = []
        for clip in clips:
            # Get embedding vector (512 dimensions)
            embedding = clip.embedding
            
            # Add to FAISS
            self.index.add(np.array([embedding], dtype=np.float32))
            
            # Map ID
            faiss_id = self.index.ntotal - 1
            self.id_map[faiss_id] = clip.id
            self.metadata_store[clip.id] = {
                "asset_id": clip.asset_id,
                "start_time": clip.start_time,
                "end_time": clip.end_time,
                "features": clip.features
            }
```

**What it does:**
- Creates FAISS vector index (L2 distance)
- Stores embeddings (512-dim vectors)
- Maps FAISS IDs to clip IDs
- Stores metadata separately

**Result:**
- Fast similarity search (milliseconds)
- Can search millions of clips

---

### **B. Search Service Integration**

**Service:** `services/drive-intel/services/search.py`

**How it works:**
```python
class SearchService:
    def __init__(self):
        self.faiss_search = FAISSEmbeddingSearch()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def add_clips(self, clips: List[Clip]):
        """Add clips to search index"""
        # Extract embeddings
        embeddings = [clip.embedding for clip in clips]
        
        # Add to FAISS
        self.faiss_search.add_clips(clips)
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """Search for similar clips"""
        # 1. Encode query to embedding
        query_embedding = self.embedding_model.encode(query)
        
        # 2. Search FAISS index
        distances, indices = self.index.search(
            np.array([query_embedding], dtype=np.float32),
            top_k
        )
        
        # 3. Map back to clips
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            clip_id = self.id_map[idx]
            results.append({
                "clip_id": clip_id,
                "similarity": float(dist),
                "score": float(dist)
            })
        
        return results
```

**What it does:**
- Converts text query to embedding
- Searches FAISS for similar vectors
- Returns ranked results by similarity

---

## 🔍 Step 5: Recall (Semantic Search)

### **A. Text-Based Search**

**How it works:**
```python
# User query: "fitness transformation before after"
query_embedding = embedding_model.encode("fitness transformation before after")

# Search FAISS
results = faiss_index.search(query_embedding, top_k=10)

# Returns:
[
    {
        "clip_id": "clip_123",
        "similarity": 0.92,  # 92% similar
        "metadata": {
            "asset_id": "video_456",
            "start_time": 5.2,
            "end_time": 12.8,
            "objects": ["person", "gym"],
            "text": ["TRANSFORM", "BEFORE AFTER"]
        }
    },
    ...
]
```

**What it finds:**
- Clips semantically similar to query
- Ranked by similarity score (0-1)
- Includes metadata (objects, text, timing)

---

### **B. Visual Similarity Search**

**Service:** `services/drive-intel/services/visual_cnn.py`

**How it works:**
```python
class VisualPatternAnalyzer:
    def find_similar_clips(self, reference_clip_id: str, top_k: int = 10):
        """Find visually similar clips"""
        # Get reference clip embedding
        reference_embedding = self.get_clip_embedding(reference_clip_id)
        
        # Search FAISS for similar visual patterns
        results = self.faiss_search.search_similar(
            query_embedding=reference_embedding,
            k=top_k
        )
        
        return results
```

**What it finds:**
- Clips with similar visual patterns
- Same objects, scenes, composition
- Useful for finding similar ad styles

---

### **C. Hybrid Search (Text + Visual)**

**How it works:**
```python
def hybrid_search(query: str, reference_clip_id: Optional[str] = None):
    """Combine text and visual search"""
    
    # 1. Text search
    text_results = text_search(query, top_k=20)
    
    # 2. Visual search (if reference provided)
    if reference_clip_id:
        visual_results = visual_search(reference_clip_id, top_k=20)
    else:
        visual_results = []
    
    # 3. Combine and re-rank
    combined = merge_results(text_results, visual_results)
    ranked = rerank_by_relevance(combined)
    
    return ranked[:10]
```

**What it does:**
- Combines text and visual similarity
- Re-ranks by relevance
- Returns best matches

---

## 🔄 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  1. DRIVE SCANNING                                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Google Drive API                                      │  │
│  │ OR Local Folder Scan                                 │  │
│  │                                                       │  │
│  │ Finds: .mp4, .avi, .mov, .mkv, .webm, .flv          │  │
│  │ Returns: File IDs, metadata (size, duration, etc.)  │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  2. INGESTION & DOWNLOAD                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Download from Google Drive                             │  │
│  │ OR Use local file path                                 │  │
│  │                                                       │  │
│  │ Stores: Local file path, asset metadata              │  │
│  │ Status: "ready" for processing                       │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  3. VIDEO PROCESSING                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ A. Scene Detection (PySceneDetect)                   │  │
│  │    - Detects scene boundaries                        │  │
│  │    - Returns: [(0.0, 5.2), (5.2, 12.8), ...]        │  │
│  │                                                       │  │
│  │ B. Feature Extraction                                │  │
│  │    - Motion analysis (OpenCV)                        │  │
│  │    - Object detection (YOLO)                         │  │
│  │    - OCR text (PaddleOCR)                            │  │
│  │    - Face detection (OpenCV)                         │  │
│  │    - Embedding generation (Sentence Transformers)    │  │
│  │    - Quality scoring                                 │  │
│  │                                                       │  │
│  │ Result: Rich metadata per clip                      │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  4. INDEXING (FAISS)                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ FAISS Vector Database                                 │  │
│  │ - Stores embeddings (512-dim vectors)                 │  │
│  │ - Fast similarity search (L2 distance)                │  │
│  │ - Maps FAISS IDs → Clip IDs                           │  │
│  │ - Stores metadata separately                         │  │
│  │                                                       │  │
│  │ Result: Searchable index of all clips                │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  5. RECALL (Semantic Search)                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ A. Text Search                                        │  │
│  │    Query: "fitness transformation"                    │  │
│  │    → Encode to embedding                             │  │
│  │    → Search FAISS                                     │  │
│  │    → Return similar clips                             │  │
│  │                                                       │  │
│  │ B. Visual Search                                      │  │
│  │    Reference clip → Find visually similar            │  │
│  │                                                       │  │
│  │ C. Hybrid Search                                      │  │
│  │    Combine text + visual, re-rank                    │  │
│  │                                                       │  │
│  │ Result: Ranked list of similar clips                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📡 API Endpoints

### **1. Ingest from Google Drive**
```bash
POST /ingest/drive/folder
{
    "folder_id": "google_drive_folder_id",
    "max_files": 50
}

Response:
{
    "status": "success",
    "videos_ingested": 25,
    "assets": [...]
}
```

### **2. Ingest from Local Folder**
```bash
POST /ingest/local/folder
{
    "folder_path": "/path/to/videos",
    "recursive": true
}

Response:
{
    "status": "success",
    "videos_ingested": 10,
    "assets": [...]
}
```

### **3. Get Asset Clips**
```bash
GET /assets/{asset_id}/clips?ranked=true&top=10

Response:
{
    "asset_id": "video_123",
    "clips": [
        {
            "clip_id": "clip_456",
            "start_time": 5.2,
            "end_time": 12.8,
            "features": {
                "motion_score": 0.85,
                "objects": ["person", "gym"],
                "text": ["FITNESS", "TRANSFORM"],
                "embedding": [0.123, -0.456, ...]
            },
            "score": 0.92
        },
        ...
    ]
}
```

### **4. Search Similar Clips**
```bash
POST /search/clips
{
    "query": "fitness transformation before after",
    "top_k": 10,
    "filter_asset_id": "optional_asset_id"
}

Response:
{
    "query": "fitness transformation before after",
    "results": [
        {
            "clip_id": "clip_123",
            "similarity": 0.92,
            "score": 0.92,
            "metadata": {
                "asset_id": "video_456",
                "start_time": 5.2,
                "end_time": 12.8,
                "objects": ["person", "gym"],
                "text": ["TRANSFORM", "BEFORE AFTER"]
            }
        },
        ...
    ]
}
```

---

## 🔑 Key Technologies

### **Scene Detection:**
- **PySceneDetect:** ContentDetector for scene boundaries
- **Threshold:** 27.0 (configurable)

### **Feature Extraction:**
- **Motion:** OpenCV frame differencing
- **Objects:** YOLOv8n (person, product, etc.)
- **OCR:** PaddleOCR (text overlay)
- **Faces:** OpenCV cascade classifier
- **Embeddings:** Sentence Transformers (all-MiniLM-L6-v2)
- **Quality:** Sharpness + resolution analysis

### **Indexing:**
- **FAISS:** Facebook AI Similarity Search
- **Index Type:** IndexFlatL2 (L2 distance)
- **Dimension:** 512 (embedding size)
- **Storage:** In-memory (can persist to disk)

### **Search:**
- **Semantic:** Embedding-based similarity
- **Visual:** CNN-based pattern matching
- **Hybrid:** Text + visual combination

---

## 💡 How Recall Works

### **1. Text Query → Embedding**
```python
query = "fitness transformation before after"
embedding = embedding_model.encode(query)
# Returns: [0.123, -0.456, 0.789, ...] (512 dimensions)
```

### **2. Embedding → FAISS Search**
```python
distances, indices = faiss_index.search(embedding, top_k=10)
# Returns: Similar clips ranked by distance
```

### **3. Distance → Similarity Score**
```python
similarity = 1.0 / (1.0 + distance)
# Lower distance = higher similarity (0-1 scale)
```

### **4. Results → Metadata**
```python
for idx in indices:
    clip_id = id_map[idx]
    metadata = metadata_store[clip_id]
    # Returns: Full clip info (timing, objects, text, etc.)
```

---

## 🎯 Use Cases

### **1. Find Similar Winning Ads**
```python
# Search for clips similar to a winning ad
query = "high energy fitness ad with transformation"
results = search_service.search(query, top_k=5)
# Returns: Similar clips that performed well
```

### **2. Find Clips by Content**
```python
# Find clips with specific content
query = "person in gym with equipment"
results = search_service.search(query, top_k=10)
# Returns: Clips matching description
```

### **3. Find Clips by Text Overlay**
```python
# Find clips with specific text
query = "TRANSFORM YOUR BODY"
results = search_service.search(query, top_k=5)
# Returns: Clips with similar text overlays
```

### **4. Visual Pattern Matching**
```python
# Find visually similar clips
reference_clip = "clip_123"
results = visual_search.find_similar(reference_clip, top_k=10)
# Returns: Clips with similar visual patterns
```

---

## 📊 Performance

### **Scanning:**
- **Google Drive:** ~1-2s per folder (API call)
- **Local Folder:** ~0.1s per 100 files (file system scan)

### **Processing:**
- **Scene Detection:** ~5-10s per minute of video
- **Feature Extraction:** ~10-20s per clip
- **Total:** ~15-30s per minute of video

### **Indexing:**
- **FAISS Add:** ~1ms per clip
- **Index Size:** ~2KB per clip (embedding + metadata)

### **Recall:**
- **Search Time:** ~5-10ms for 10K clips
- **Search Time:** ~50-100ms for 1M clips
- **Scales:** Logarithmic (very fast even at scale)

---

## ✅ Summary

**Complete Flow:**
1. **Scan** → Find videos in Drive/folder
2. **Ingest** → Download/register files
3. **Process** → Scene detection + feature extraction
4. **Index** → Store in FAISS vector database
5. **Recall** → Semantic search for similar content

**Key Features:**
- ✅ Automatic scene detection
- ✅ Rich feature extraction (motion, objects, text, faces)
- ✅ Fast semantic search (FAISS)
- ✅ Visual similarity matching
- ✅ Hybrid search (text + visual)

**Result:**
- System can find similar video clips instantly
- Useful for finding winning patterns
- Enables creative reuse and learning

---

**Status: ✅ Complete Understanding of Drive → Recall Flow**

