# ComfyUI Portability Foundation

Created a new portability foundation at `backend/app/services/comfyui/` to enable portable ComfyUI workflows.
This is a newer implementation that supersedes the `comfyui_portability` package.

## Components

### 1. Types (`types.py`)
Core type definitions:
- `NodeSpec`, `NodeInputSpec`, `NodeOutputSpec` - Node schema definitions
- `ModelRequirement`, `ModelType` - Model requirements
- `OutputSpec` - Expected output specifications
- `NodeAlias` - Alias mappings for node name drift
- `ObjectInfoResponse`, `SystemStatsResponse` - API response types

### 2. Discovery Client (`discovery.py`)
- `ComfyUIDiscoveryClient` - Queries `/object_info` and `/system_stats` endpoints
- Parses node specifications from ComfyUI responses
- Handles various input spec formats (COMBO, primitives, etc.)

### 3. Alias Resolution (`aliases.py`)
- Known alias mappings for node name drift
- `SEGMENT_ANYTHING_ALIASES` - SAM node variations
- `COGVIDEO_ALIASES` - CogVideoX wrapper variations
- `VIDEO_COMBINE_ALIASES` - Video combine node variations
- Functions: `build_alias_index()`, `get_canonical_name()`, `get_all_known_names_for()`

### 4. Capability Analysis (`capability.py`)
- `CapabilityAnalyzer` - Evaluates workflow compatibility
- `CompatibilityResult` - Detailed compatibility report
- Checks for missing nodes, models, and schema mismatches
- Resolves aliases during compatibility checks

### 5. Workflow Manifests (`manifest.py`)
- `WorkflowManifest` - Portable workflow definition
- `NodeRequirement` - Node requirements with schema validation
- `WorkflowManifestLoader` - Load manifests from JSON files
- Default loader at `manifests/` directory

### 6. Workflow Manifest Files (`manifests/`)
- `sdxl_background_replace_v1.json` - SDXL background replacement workflow
- `cogvideox_i2v_v1.json` - CogVideoX image-to-video workflow

## Usage

```python
from app.services.comfyui import (
    ComfyUIDiscoveryClient,
    CapabilityAnalyzer,
    load_manifest,
)

# Discover backend capabilities
client = ComfyUIDiscoveryClient("http://localhost:8188")
object_info = await client.get_object_info()

# Check workflow compatibility
analyzer = CapabilityAnalyzer(object_info)
manifest = load_manifest("sdxl_background_replace_v1")
result = analyzer.check_compatibility(manifest)

if result.is_compatible:
    print("Workflow can run on this backend!")
else:
    print(f"Missing nodes: {result.missing_nodes}")
```

## Testing

Run tests with:
```bash
cd backend && pytest tests/test_comfyui_discovery.py -v
```
