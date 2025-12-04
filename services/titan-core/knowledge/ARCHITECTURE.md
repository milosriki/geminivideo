# Knowledge Base Hot-Reload System - Architecture

**Agent 14: Knowledge Base Hot-Reload Engineer**

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                              │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  React Frontend (KnowledgeManager.tsx)                        │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐    │  │
│  │  │Category  │ │ Version  │ │  JSON    │ │Import/Export │    │  │
│  │  │ Selector │ │ History  │ │ Editor   │ │   Controls   │    │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘    │  │
│  └───────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTP REST API
┌───────────────────────────────▼─────────────────────────────────────┐
│                        API LAYER (FastAPI)                           │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  REST Endpoints (api.py)                                      │  │
│  │                                                                │  │
│  │  POST   /knowledge/upload           Upload new version        │  │
│  │  GET    /knowledge/{category}       Download knowledge        │  │
│  │  GET    /knowledge/{category}/versions  List versions         │  │
│  │  POST   /knowledge/activate/{cat}/{ver}  Activate version     │  │
│  │  DELETE /knowledge/{cat}/versions/{ver}  Delete version       │  │
│  │  GET    /knowledge/status            Get status               │  │
│  │  POST   /knowledge/reload            Trigger reload           │  │
│  │  POST   /knowledge/validate          Validate data            │  │
│  │                                                                │  │
│  │  Pydantic Models:                                             │  │
│  │  - UploadRequest, VersionInfoResponse, CategoryStatus         │  │
│  └───────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                               │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  KnowledgeBaseManager (manager.py)                            │  │
│  │                                                                │  │
│  │  Storage Methods:                Hot-Reload Methods:          │  │
│  │  • upload_knowledge()            • subscribe_to_updates()     │  │
│  │  • download_knowledge()          • unsubscribe()              │  │
│  │  • list_versions()               • trigger_reload()           │  │
│  │  • delete_version()              • get_current_version()      │  │
│  │  • activate_version()            • reload_all()               │  │
│  │                                                                │  │
│  │  Internal Components:                                         │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐      │  │
│  │  │  Version   │  │   Cache    │  │    Callback        │      │  │
│  │  │ Management │  │  Manager   │  │  Subscriptions     │      │  │
│  │  └────────────┘  └────────────┘  └────────────────────┘      │  │
│  │                                                                │  │
│  │  Thread Safety: RLock for all operations                      │  │
│  └───────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                      STORAGE ABSTRACTION                             │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  StorageBackend (Abstract Base Class)                         │  │
│  │                                                                │  │
│  │  Interface:                                                    │  │
│  │  • save(path, data) -> bool                                   │  │
│  │  • load(path) -> Optional[bytes]                              │  │
│  │  • delete(path) -> bool                                       │  │
│  │  • list_files(prefix) -> List[str]                            │  │
│  │  • exists(path) -> bool                                       │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌──────────────────────────┐    ┌──────────────────────────────┐   │
│  │ LocalFileSystemBackend   │    │     GCSBackend              │   │
│  │                          │    │   (Placeholder)              │   │
│  │ • File-based storage     │    │ • Cloud storage              │   │
│  │ • Default backend        │    │ • Bucket-based               │   │
│  │ • Auto-create dirs       │    │ • Future implementation      │   │
│  └──────────────────────────┘    └──────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                      PERSISTENT STORAGE                              │
│                                                                       │
│  Local Filesystem: /home/user/geminivideo/data/knowledge_base/       │
│                                                                       │
│  {category}/                                                          │
│  ├── metadata.json           # Version metadata, active version      │
│  └── versions/                                                        │
│      ├── 20231201_120000_abc123.json                                │
│      ├── 20231202_150000_def456.json                                │
│      └── 20231203_180000_ghi789.json                                │
│                                                                       │
│  Categories:                                                          │
│  • brand_guidelines/         • hook_templates/                       │
│  • competitor_analysis/      • storyboard_templates/                 │
│  • industry_benchmarks/      • winning_patterns/                     │
└───────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### Upload Flow

```
User
  │
  │ 1. Upload JSON data
  ▼
React UI
  │
  │ 2. POST /knowledge/upload
  │    { category, data, description, author }
  ▼
FastAPI
  │
  │ 3. Validate request
  │ 4. Call manager.upload_knowledge()
  ▼
KnowledgeBaseManager
  │
  │ 5. Validate category & data
  │ 6. Generate version ID + checksum
  │ 7. Check for duplicates
  ▼
StorageBackend
  │
  │ 8. Save to disk
  │    {category}/versions/{version_id}.json
  ▼
Filesystem
  │
  │ 9. Update metadata
  │ 10. Auto-activate if first version
  ◄─┘
  │
  │ 11. Return version ID
  ▼
User (Confirmation)
```

### Hot-Reload Flow

```
Service A                    KnowledgeBaseManager               Service B
  │                                  │                              │
  │ 1. subscribe_to_updates()        │                              │
  │──────────────────────────────────>                              │
  │                                  │                              │
  │ 2. Returns subscription_id       │                              │
  <──────────────────────────────────│                              │
  │                                  │                              │
  │                                  │  3. activate_version()        │
  │                                  <──────────────────────────────│
  │                                  │                              │
  │                                  │  4. Clear cache               │
  │                                  │  5. Update active version     │
  │                                  │  6. Save metadata             │
  │                                  │                              │
  │  7. callback(cat, new, old)      │                              │
  <──────────────────────────────────│                              │
  │                                  │                              │
  │  8. Reload application state     │                              │
  │                                  │                              │
  ▼                                  ▼                              ▼
```

### Version Management Flow

```
┌─────────────┐
│   Upload    │  New version created
│  Version 1  │  (auto-activated)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Active    │  Version 1 is active
│  Version 1  │
└──────┬──────┘
       │
       │  Upload Version 2
       ▼
┌─────────────┐     ┌─────────────┐
│  Version 1  │     │  Version 2  │  Version 1 still active
│  (Active)   │     │ (Inactive)  │  (new version not auto-activated)
└──────┬──────┘     └──────┬──────┘
       │                   │
       │  Activate Version 2
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│  Version 1  │     │  Version 2  │  Version 2 now active
│ (Inactive)  │     │  (Active)   │  Subscribers notified
└──────┬──────┘     └──────┬──────┘
       │                   │
       │  Rollback (activate Version 1)
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│  Version 1  │     │  Version 2  │  Rolled back to Version 1
│  (Active)   │     │ (Inactive)  │  Subscribers notified
└─────────────┘     └──────┬──────┘
                           │
                           │  Delete Version 2
                           ▼
                    ┌─────────────┐
                    │   Deleted   │  Cannot delete active version
                    └─────────────┘
```

## Component Interaction

```
┌──────────────────────────────────────────────────────────────────┐
│                        External Services                          │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Titan Core   │  │  Meta Ads    │  │  Other Agents        │   │
│  │   Engine     │  │   Library    │  │  (1-15)              │   │
│  └───────┬──────┘  └───────┬──────┘  └──────────┬───────────┘   │
└──────────┼──────────────────┼────────────────────┼───────────────┘
           │                  │                    │
           │  Subscribe       │  Upload            │  Download
           ▼                  ▼                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                   KnowledgeBaseManager                            │
│                                                                    │
│  Manages:                                                          │
│  • brand_guidelines      ← Titan Core uses for brand voice        │
│  • competitor_analysis   ← Meta Ads Library updates this          │
│  • industry_benchmarks   ← ML agents contribute data              │
│  • hook_templates        ← Shared across all agents               │
│  • storyboard_templates  ← Used by video generation               │
│  • winning_patterns      ← Updated by performance analysis        │
│                                                                    │
│  On Update:                                                        │
│  1. Notifies all subscribers via callbacks                        │
│  2. Subscribers reload their state                                │
│  3. New knowledge immediately available                           │
└────────────────────────────────────────────────────────────────────┘
```

## Class Hierarchy

```
KnowledgeBaseManager
├── Storage
│   ├── LocalFileSystemBackend (implemented)
│   └── GCSBackend (placeholder)
│
├── Versioning
│   ├── VersionInfo (dataclass)
│   ├── Version ID generation
│   └── Checksum validation
│
├── Hot-Reload
│   ├── Callback subscriptions
│   ├── Notification system
│   └── Cache invalidation
│
└── Thread Safety
    ├── RLock for critical sections
    └── Isolated callback execution
```

## State Machine

```
┌─────────────────┐
│  No Knowledge   │
└────────┬────────┘
         │
         │ upload_knowledge()
         ▼
┌─────────────────┐
│  Version 1      │
│  (Auto-Active)  │
└────────┬────────┘
         │
         ├─── upload_knowledge() ───> Version 2 (Inactive)
         │
         ├─── activate_version() ───> Switch active version
         │
         ├─── trigger_reload() ─────> Reload from storage
         │
         ├─── delete_version() ─────> Remove inactive version
         │
         └─── download_knowledge() ──> Get current data
```

## Callback System

```
┌────────────────────────────────────────────────────────────┐
│                 Callback Subscription                       │
│                                                              │
│  Subscriber 1                                               │
│  ┌────────────┐                                             │
│  │ callback_1 │───┐                                         │
│  └────────────┘   │                                         │
│                   │                                         │
│  Subscriber 2     │                                         │
│  ┌────────────┐   │    ┌──────────────────────────┐       │
│  │ callback_2 │───┼────>  _subscribers dict       │       │
│  └────────────┘   │    │  {                        │       │
│                   │    │   sub_id_1: callback_1   │       │
│  Subscriber 3     │    │   sub_id_2: callback_2   │       │
│  ┌────────────┐   │    │   sub_id_3: callback_3   │       │
│  │ callback_3 │───┘    │  }                        │       │
│  └────────────┘        └──────────┬────────────────┘       │
│                                   │                         │
│                                   │ On activate_version()   │
│                                   ▼                         │
│                        ┌──────────────────────┐            │
│                        │  _notify_subscribers │            │
│                        │                      │            │
│                        │  for each callback:  │            │
│                        │    try:              │            │
│                        │      callback(...)   │            │
│                        │    except:           │            │
│                        │      log error       │            │
│                        └──────────────────────┘            │
└────────────────────────────────────────────────────────────┘
```

## Performance Characteristics

```
Operation              Time Complexity    Space Complexity    Notes
─────────────────────────────────────────────────────────────────────
upload_knowledge       O(1)               O(n)                n = data size
download_knowledge     O(1)               O(n)                Cached reads
list_versions          O(m)               O(m)                m = num versions
activate_version       O(1)               O(1)                + cache clear
trigger_reload         O(1)               O(n)                Reload from disk
subscribe              O(1)               O(1)                Add to dict
notify_subscribers     O(k)               O(1)                k = num subscribers
```

## Security Model

```
┌────────────────────────────────────────────────────────┐
│                   Security Layers                       │
│                                                          │
│  Layer 1: Input Validation                              │
│  ┌────────────────────────────────────────────────┐    │
│  │ • Category validation                          │    │
│  │ • Data structure validation                    │    │
│  │ • Type checking (Pydantic)                     │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  Layer 2: Data Integrity                                │
│  ┌────────────────────────────────────────────────┐    │
│  │ • SHA256 checksums                             │    │
│  │ • Duplicate detection                          │    │
│  │ • Atomic updates                               │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  Layer 3: Access Control (Future)                       │
│  ┌────────────────────────────────────────────────┐    │
│  │ • Authentication middleware                    │    │
│  │ • Role-based permissions                       │    │
│  │ • API key validation                           │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  Layer 4: Storage Security                              │
│  ┌────────────────────────────────────────────────┐    │
│  │ • File system permissions                      │    │
│  │ • Encryption at rest (future)                  │    │
│  │ • Secure deletion                              │    │
│  └────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Production Deployment                    │
│                                                               │
│  ┌───────────────┐         ┌───────────────┐                │
│  │  Load         │         │   Frontend    │                │
│  │  Balancer     │◄────────│   (React)     │                │
│  └───────┬───────┘         └───────────────┘                │
│          │                                                    │
│          ├────────┬────────┬────────┐                       │
│          ▼        ▼        ▼        ▼                       │
│    ┌─────────┐ ┌─────────┐ ┌─────────┐                     │
│    │ API     │ │ API     │ │ API     │  (Horizontal        │
│    │ Server 1│ │ Server 2│ │ Server 3│   Scaling)          │
│    └────┬────┘ └────┬────┘ └────┬────┘                     │
│         │           │           │                            │
│         └───────────┴───────────┘                            │
│                     │                                         │
│                     ▼                                         │
│         ┌───────────────────────┐                            │
│         │  Shared Storage       │                            │
│         │  (GCS / NFS)          │                            │
│         └───────────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

---

**Architecture Design by Agent 14: Knowledge Base Hot-Reload Engineer**
**Last Updated: 2025-12-01**
