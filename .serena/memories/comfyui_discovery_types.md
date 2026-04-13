# ComfyUI Discovery Types

This file defines the core types for the ComfyUI discovery and capability system.

## Key Types

### Node Types
- `InputType` - Enum of ComfyUI input types (STRING, INT, FLOAT, COMBO, etc.)
- `NodeInputSpec` - Specification for a single node input
- `NodeOutputSpec` - Specification for a single node output
- `NodeSpec` - Complete specification for a ComfyUI node type

### Model Types
- `ModelType` - Enum of model types (CHECKPOINT, VAE, LORA, etc.)
- `ModelRequirement` - A model required by a workflow with logical ID

### Workflow Types
- `OutputSpec` - Expected workflow output specification
- `NodeAlias` - Mapping for node name drift (canonical + aliases)

### Response Types
- `ObjectInfoResponse` - Parsed /object_info response
- `SystemStatsResponse` - Parsed /system_stats response
