"""Workflow manifest definitions for portable ComfyUI workflows."""

from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from pydantic import BaseModel, Field
from enum import Enum

if TYPE_CHECKING:
    from .discovery import NodeAliasResolver
    from .model_mapping import ModelRegistry


class InputType(str, Enum):
    """Types of node inputs."""

    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOLEAN = "boolean"
    IMAGE = "image"
    LATENT = "latent"
    MODEL = "model"
    CLIP = "clip"
    VAE = "vae"
    CONDITIONING = "conditioning"
    MASK = "mask"
    NODE_LINK = "node_link"


class NodeInput(BaseModel):
    """Definition of a node input."""

    type: InputType
    default: Optional[Any] = None
    required: bool = True
    # For NODE_LINK type: [node_id, output_slot]
    link_reference: Optional[List[Union[str, int]]] = None


class NodeInputMapping(BaseModel):
    """Mapping of logical input names to node inputs."""

    mappings: Dict[str, NodeInput] = Field(default_factory=dict)

    def get_input(self, name: str) -> Optional[NodeInput]:
        return self.mappings.get(name)

    def add_mapping(self, name: str, input_def: NodeInput) -> None:
        self.mappings[name] = input_def


class OutputDefinition(BaseModel):
    """Definition of a workflow output with type information."""

    node_id: str
    output_key: str
    output_type: str = "image"
    slot_index: int = 0
    description: Optional[str] = None


class NodeOutput(BaseModel):
    """Definition of a node output."""

    name: str
    type: str
    slot_index: int = 0


class NodeDefinition(BaseModel):
    """Definition of a workflow node.

    Uses logical node types that get resolved to actual ComfyUI class names
    via the NodeAliasResolver.
    """

    logical_type: str = Field(
        ..., description="Logical node type (e.g., 'load_image', 'checkpoint_loader')"
    )
    alias_priority: List[str] = Field(
        default_factory=list, description="Priority list of actual class names to try"
    )
    inputs: Dict[str, Union[NodeInput, Any]] = Field(default_factory=dict)
    outputs: List[NodeOutput] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


class WorkflowOutput(BaseModel):
    """Definition of expected workflow output."""

    node_id: str
    output_key: str  # e.g., "images", "gifs", "video"
    output_type: str = "image"  # "image", "video", "latent", etc.
    slot_index: int = 0


class WorkflowManifest(BaseModel):
    """Manifest for a portable ComfyUI workflow.

    This defines the workflow structure using logical node types and
    model identifiers that get resolved at runtime based on the target
    ComfyUI installation's capabilities.
    """

    name: str
    description: str
    version: str = "1.0.0"

    # Node definitions keyed by node ID
    nodes: Dict[str, NodeDefinition]

    # Expected outputs
    outputs: List[WorkflowOutput]

    # Model mappings required
    required_models: Dict[str, str] = Field(
        default_factory=dict, description="Logical model ID -> model type mapping"
    )

    # Default values for parameters
    defaults: Dict[str, Any] = Field(default_factory=dict)

    def to_comfyui_workflow(
        self,
        node_resolver: "NodeAliasResolver",
        model_registry: "ModelRegistry",
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Convert manifest to actual ComfyUI workflow dict.

        Args:
            node_resolver: Resolves logical node types to actual class names
            model_registry: Resolves logical model IDs to actual filenames
            parameters: Runtime parameters to inject into inputs

        Returns:
            ComfyUI-compatible workflow dict

        Raises:
            MissingNodeError: If a node type cannot be resolved
            MissingModelError: If a model mapping cannot be resolved
        """
        from .exceptions import MissingNodeError, MissingModelError

        workflow = {}
        parameters = parameters or {}

        for node_id, node_def in self.nodes.items():
            # Resolve node type to actual class name
            resolved_type = node_resolver.resolve(
                node_def.logical_type, node_def.alias_priority
            )

            if not resolved_type:
                available = node_resolver.get_available_nodes()
                raise MissingNodeError(
                    logical_node=node_def.logical_type,
                    attempted_aliases=node_def.alias_priority
                    or [node_def.logical_type],
                    available_nodes=available,
                )

            # Build inputs dict
            inputs = {}
            for input_name, input_def in node_def.inputs.items():
                if isinstance(input_def, NodeInput):
                    if input_def.type == InputType.NODE_LINK:
                        inputs[input_name] = input_def.link_reference
                    elif input_name in parameters:
                        inputs[input_name] = parameters[input_name]
                    elif input_def.default is not None:
                        inputs[input_name] = input_def.default
                    elif input_def.required:
                        raise ValueError(
                            f"Required input '{input_name}' not provided for node {node_id}"
                        )
                else:
                    # Direct value
                    if isinstance(input_def, str) and input_def.startswith("model:"):
                        # Resolve model reference
                        logical_model = input_def[6:]  # Remove "model:" prefix
                        model_type = self.required_models.get(
                            logical_model, "checkpoints"
                        )
                        resolved_model = model_registry.resolve(
                            logical_model, model_type
                        )
                        if not resolved_model:
                            available = model_registry.list_models(model_type)
                            raise MissingModelError(
                                logical_model=logical_model,
                                model_type=model_type,
                                available_models=available,
                            )
                        inputs[input_name] = resolved_model
                    elif isinstance(input_def, str) and input_def.startswith("param:"):
                        # Parameter reference
                        param_name = input_def[6:]  # Remove "param:" prefix
                        if param_name in parameters:
                            inputs[input_name] = parameters[param_name]
                        elif input_name in self.defaults:
                            inputs[input_name] = self.defaults[input_name]
                    else:
                        inputs[input_name] = input_def

            workflow[node_id] = {"class_type": resolved_type, "inputs": inputs}

        return workflow


# Predefined manifests for common workflows

BACKGROUND_REPLACEMENT_MANIFEST = WorkflowManifest(
    name="background_replacement",
    description="Replace background of product image using inpainting",
    version="1.0.0",
    nodes={
        "1": NodeDefinition(
            logical_type="load_image_base64",
            alias_priority=["LoadImageBase64", "Load Image (Base64)"],
            inputs={"image_base64": NodeInput(type=InputType.STRING)},
            outputs=[NodeOutput(name="IMAGE", type="IMAGE", slot_index=0)],
        ),
        "2": NodeDefinition(
            logical_type="sam_loader",
            alias_priority=["SAMModelLoader", "SAM Model Loader"],
            inputs={"model_name": "model:sam_vit_h"},
            outputs=[NodeOutput(name="SAM_MODEL", type="SAM_MODEL", slot_index=0)],
        ),
        "3": NodeDefinition(
            logical_type="grounding_dino_sam",
            alias_priority=["GroundingDinoSAMSegment", "GroundingDINO SAM Segment"],
            inputs={
                "image": NodeInput(type=InputType.NODE_LINK, link_reference=["1", 0]),
                "sam_model": NodeInput(
                    type=InputType.NODE_LINK, link_reference=["2", 0]
                ),
                "prompt": NodeInput(
                    type=InputType.STRING, default="product, main object"
                ),
                "threshold": NodeInput(type=InputType.FLOAT, default=0.3),
            },
            outputs=[
                NodeOutput(name="IMAGE", type="IMAGE", slot_index=0),
                NodeOutput(name="MASK", type="MASK", slot_index=1),
            ],
        ),
        "4": NodeDefinition(
            logical_type="checkpoint_loader",
            alias_priority=[
                "CheckpointLoaderSimple",
                "CheckpointLoader",
                "Load Checkpoint",
            ],
            inputs={"ckpt_name": "model:sdxl_base"},
            outputs=[
                NodeOutput(name="MODEL", type="MODEL", slot_index=0),
                NodeOutput(name="CLIP", type="CLIP", slot_index=1),
                NodeOutput(name="VAE", type="VAE", slot_index=2),
            ],
        ),
        "5": NodeDefinition(
            logical_type="clip_encode",
            alias_priority=["CLIPTextEncode", "CLIP Text Encode"],
            inputs={
                "text": "param:prompt",
                "clip": NodeInput(type=InputType.NODE_LINK, link_reference=["4", 1]),
            },
            outputs=[
                NodeOutput(name="CONDITIONING", type="CONDITIONING", slot_index=0)
            ],
        ),
        "6": NodeDefinition(
            logical_type="clip_encode",
            alias_priority=["CLIPTextEncode", "CLIP Text Encode"],
            inputs={
                "text": NodeInput(
                    type=InputType.STRING, default="blurry, low quality, distorted"
                ),
                "clip": NodeInput(type=InputType.NODE_LINK, link_reference=["4", 1]),
            },
            outputs=[
                NodeOutput(name="CONDITIONING", type="CONDITIONING", slot_index=0)
            ],
        ),
        "7": NodeDefinition(
            logical_type="inpaint_conditioning",
            alias_priority=["InpaintModelConditioning", "Inpaint Model Conditioning"],
            inputs={
                "positive": NodeInput(
                    type=InputType.NODE_LINK, link_reference=["5", 0]
                ),
                "negative": NodeInput(
                    type=InputType.NODE_LINK, link_reference=["6", 0]
                ),
                "vae": NodeInput(type=InputType.NODE_LINK, link_reference=["4", 2]),
                "pixels": NodeInput(type=InputType.NODE_LINK, link_reference=["1", 0]),
                "mask": NodeInput(type=InputType.NODE_LINK, link_reference=["3", 1]),
                "noise_mask": NodeInput(type=InputType.BOOLEAN, default=True),
            },
            outputs=[
                NodeOutput(name="CONDITIONING", type="CONDITIONING", slot_index=0),
                NodeOutput(name="CONDITIONING", type="CONDITIONING", slot_index=1),
                NodeOutput(name="LATENT", type="LATENT", slot_index=2),
            ],
        ),
        "8": NodeDefinition(
            logical_type="ksampler",
            alias_priority=["KSampler", "KSamplerAdvanced"],
            inputs={
                "model": NodeInput(type=InputType.NODE_LINK, link_reference=["4", 0]),
                "positive": NodeInput(
                    type=InputType.NODE_LINK, link_reference=["7", 0]
                ),
                "negative": NodeInput(
                    type=InputType.NODE_LINK, link_reference=["7", 1]
                ),
                "latent_image": NodeInput(
                    type=InputType.NODE_LINK, link_reference=["7", 2]
                ),
                "seed": NodeInput(type=InputType.INT, default=0),
                "steps": NodeInput(type=InputType.INT, default=30),
                "cfg": NodeInput(type=InputType.FLOAT, default=7.5),
                "sampler_name": NodeInput(type=InputType.STRING, default="dpmpp_2m"),
                "scheduler": NodeInput(type=InputType.STRING, default="karras"),
                "denoise": NodeInput(type=InputType.FLOAT, default=0.85),
            },
            outputs=[NodeOutput(name="LATENT", type="LATENT", slot_index=0)],
        ),
        "9": NodeDefinition(
            logical_type="vae_decode",
            alias_priority=["VAEDecode", "VAE Decode"],
            inputs={
                "samples": NodeInput(type=InputType.NODE_LINK, link_reference=["8", 0]),
                "vae": NodeInput(type=InputType.NODE_LINK, link_reference=["4", 2]),
            },
            outputs=[NodeOutput(name="IMAGE", type="IMAGE", slot_index=0)],
        ),
        "10": NodeDefinition(
            logical_type="image_composite_masked",
            alias_priority=["ImageCompositeMasked", "Image Composite Masked"],
            inputs={
                "destination": NodeInput(
                    type=InputType.NODE_LINK, link_reference=["9", 0]
                ),
                "source": NodeInput(type=InputType.NODE_LINK, link_reference=["1", 0]),
                "mask": NodeInput(type=InputType.NODE_LINK, link_reference=["3", 1]),
                "x": NodeInput(type=InputType.INT, default=0),
                "y": NodeInput(type=InputType.INT, default=0),
                "resize_source": NodeInput(type=InputType.BOOLEAN, default=False),
                "resize_source": NodeInput(type=InputType.BOOLEAN, default=False),
            },
            outputs=[NodeOutput(name="IMAGE", type="IMAGE", slot_index=0)],
        ),
        "11": NodeDefinition(
            logical_type="save_image",
            alias_priority=["SaveImage", "Save Image"],
            inputs={
                "images": NodeInput(type=InputType.NODE_LINK, link_reference=["10", 0]),
                "filename_prefix": NodeInput(
                    type=InputType.STRING, default="opensns_ad"
                ),
            },
            outputs=[],
        ),
    },
    outputs=[
        WorkflowOutput(
            node_id="11", output_key="images", output_type="image", slot_index=0
        )
    ],
    required_models={"sam_vit_h": "sams", "sdxl_base": "checkpoints"},
    defaults={
        "prompt": "professional product photography, advertisement, clean studio background, soft lighting"
    },
)


TEXT_TO_IMAGE_MANIFEST = WorkflowManifest(
    name="text_to_image",
    description="Generate image from text prompt using SDXL (no input image required)",
    version="1.0.0",
    nodes={
        "1": NodeDefinition(
            logical_type="checkpoint_loader",
            alias_priority=[
                "CheckpointLoaderSimple",
                "CheckpointLoader",
                "Load Checkpoint",
            ],
            inputs={"ckpt_name": "model:sdxl_base"},
            outputs=[
                NodeOutput(name="MODEL", type="MODEL", slot_index=0),
                NodeOutput(name="CLIP", type="CLIP", slot_index=1),
                NodeOutput(name="VAE", type="VAE", slot_index=2),
            ],
        ),
        "2": NodeDefinition(
            logical_type="clip_encode",
            alias_priority=["CLIPTextEncode", "CLIP Text Encode"],
            inputs={
                "text": "param:prompt",
                "clip": NodeInput(type=InputType.NODE_LINK, link_reference=["1", 1]),
            },
            outputs=[
                NodeOutput(name="CONDITIONING", type="CONDITIONING", slot_index=0)
            ],
        ),
        "3": NodeDefinition(
            logical_type="clip_encode",
            alias_priority=["CLIPTextEncode", "CLIP Text Encode"],
            inputs={
                "text": NodeInput(
                    type=InputType.STRING,
                    default="blurry, low quality, distorted, watermark, text, ugly, deformed, noisy, grainy",
                ),
                "clip": NodeInput(type=InputType.NODE_LINK, link_reference=["1", 1]),
            },
            outputs=[
                NodeOutput(name="CONDITIONING", type="CONDITIONING", slot_index=0)
            ],
        ),
        "4": NodeDefinition(
            logical_type="empty_latent_image",
            alias_priority=["EmptyLatentImage", "Empty Latent Image"],
            inputs={
                "width": NodeInput(type=InputType.INT, default=1024),
                "height": NodeInput(type=InputType.INT, default=1024),
                "batch_size": NodeInput(type=InputType.INT, default=1),
            },
            outputs=[NodeOutput(name="LATENT", type="LATENT", slot_index=0)],
        ),
        "5": NodeDefinition(
            logical_type="ksampler",
            alias_priority=["KSampler", "KSamplerAdvanced"],
            inputs={
                "model": NodeInput(type=InputType.NODE_LINK, link_reference=["1", 0]),
                "positive": NodeInput(
                    type=InputType.NODE_LINK, link_reference=["2", 0]
                ),
                "negative": NodeInput(
                    type=InputType.NODE_LINK, link_reference=["3", 0]
                ),
                "latent_image": NodeInput(
                    type=InputType.NODE_LINK, link_reference=["4", 0]
                ),
                "seed": NodeInput(type=InputType.INT, default=0),
                "steps": NodeInput(type=InputType.INT, default=25),
                "cfg": NodeInput(type=InputType.FLOAT, default=7.0),
                "sampler_name": NodeInput(type=InputType.STRING, default="dpmpp_2m"),
                "scheduler": NodeInput(type=InputType.STRING, default="karras"),
                "denoise": NodeInput(type=InputType.FLOAT, default=1.0),
            },
            outputs=[NodeOutput(name="LATENT", type="LATENT", slot_index=0)],
        ),
        "6": NodeDefinition(
            logical_type="vae_decode",
            alias_priority=["VAEDecode", "VAE Decode"],
            inputs={
                "samples": NodeInput(type=InputType.NODE_LINK, link_reference=["5", 0]),
                "vae": NodeInput(type=InputType.NODE_LINK, link_reference=["1", 2]),
            },
            outputs=[NodeOutput(name="IMAGE", type="IMAGE", slot_index=0)],
        ),
        "7": NodeDefinition(
            logical_type="save_image",
            alias_priority=["SaveImage", "Save Image"],
            inputs={
                "images": NodeInput(type=InputType.NODE_LINK, link_reference=["6", 0]),
                "filename_prefix": NodeInput(
                    type=InputType.STRING, default="opensns_ad"
                ),
            },
            outputs=[],
        ),
    },
    outputs=[
        WorkflowOutput(
            node_id="7", output_key="images", output_type="image", slot_index=0
        )
    ],
    required_models={"sdxl_base": "checkpoints"},
    defaults={
        "prompt": "professional product photography, advertisement, clean studio background, soft lighting, commercial quality, 4k"
    },
)


ANIMATEDIFF_V3_MANIFEST = WorkflowManifest(
    name="animatediff_v3",
    description="Generate video from image using AnimateDiff v3 with standard sampling (MPS-compatible)",
    version="1.0.0",
    nodes={
        # 1: Load SD1.5 checkpoint
        "1": NodeDefinition(
            logical_type="checkpoint_loader",
            alias_priority=[
                "CheckpointLoaderSimple",
                "CheckpointLoader",
                "Load Checkpoint",
            ],
            inputs={"ckpt_name": "model:sd15_base"},
            outputs=[
                NodeOutput(name="MODEL", type="MODEL", slot_index=0),
                NodeOutput(name="CLIP", type="CLIP", slot_index=1),
                NodeOutput(name="VAE", type="VAE", slot_index=2),
            ],
        ),
        # 2: Load source image
        "2": NodeDefinition(
            logical_type="load_image",
            alias_priority=["LoadImage", "Load Image"],
            inputs={"image": NodeInput(type=InputType.STRING)},
            outputs=[NodeOutput(name="IMAGE", type="IMAGE", slot_index=0)],
        ),
        # 3: Resize source image to 512x512 (SD1.5 native resolution)
        "3": NodeDefinition(
            logical_type="image_scale",
            alias_priority=["ImageScale", "Image Scale"],
            inputs={
                "image": NodeInput(type=InputType.NODE_LINK, link_reference=["2", 0]),
                "upscale_method": NodeInput(type=InputType.STRING, default="lanczos"),
                "width": NodeInput(type=InputType.INT, default=512),
                "height": NodeInput(type=InputType.INT, default=512),
                "crop": NodeInput(type=InputType.STRING, default="center"),
            },
            outputs=[NodeOutput(name="IMAGE", type="IMAGE", slot_index=0)],
        ),
        # 4: Positive prompt encoding
        "4": NodeDefinition(
            logical_type="clip_encode",
            alias_priority=["CLIPTextEncode", "CLIP Text Encode"],
            inputs={
                "text": "param:prompt",
                "clip": NodeInput(type=InputType.NODE_LINK, link_reference=["1", 1]),
            },
            outputs=[
                NodeOutput(name="CONDITIONING", type="CONDITIONING", slot_index=0)
            ],
        ),
        # 5: Negative prompt encoding
        "5": NodeDefinition(
            logical_type="clip_encode",
            alias_priority=["CLIPTextEncode", "CLIP Text Encode"],
            inputs={
                "text": NodeInput(
                    type=InputType.STRING,
                    default="blurry, low quality, distorted, watermark, text, ugly, static, no motion",
                ),
                "clip": NodeInput(type=InputType.NODE_LINK, link_reference=["1", 1]),
            },
            outputs=[
                NodeOutput(name="CONDITIONING", type="CONDITIONING", slot_index=0)
            ],
        ),
        # 6: VAE encode resized source image → use as initial latent
        # This gives img2vid behavior: first frame = source image
        "6": NodeDefinition(
            logical_type="vae_encode",
            alias_priority=["VAEEncode", "VAE Encode"],
            inputs={
                "pixels": NodeInput(type=InputType.NODE_LINK, link_reference=["3", 0]),
                "vae": NodeInput(type=InputType.NODE_LINK, link_reference=["1", 2]),
            },
            outputs=[NodeOutput(name="LATENT", type="LATENT", slot_index=0)],
        ),
        "6b": NodeDefinition(
            logical_type="repeat_latent_batch",
            alias_priority=["RepeatLatentBatch", "Repeat Latent Batch"],
            inputs={
                "samples": NodeInput(type=InputType.NODE_LINK, link_reference=["6", 0]),
                "amount": NodeInput(type=InputType.INT, default=16),
            },
            outputs=[NodeOutput(name="LATENT", type="LATENT", slot_index=0)],
        ),
        # 7: Load AnimateDiff v3 motion model (standard, not LCM)
        "7": NodeDefinition(
            logical_type="animatediff_loader",
            alias_priority=[
                "ADE_LoadAnimateDiffModel",
                "Load AnimateDiff Model",
            ],
            inputs={
                "model_name": NodeInput(
                    type=InputType.STRING,
                    default="v3_sd15_mm.ckpt",
                ),
            },
            outputs=[
                NodeOutput(name="MOTION_MODEL", type="MOTION_MODEL_ADE", slot_index=0),
            ],
        ),
        # 8: Apply AnimateDiff motion model (standard, not I2V)
        "8": NodeDefinition(
            logical_type="animatediff_apply",
            alias_priority=[
                "ADE_ApplyAnimateDiffModel",
                "Apply AnimateDiff Model",
            ],
            inputs={
                "motion_model": NodeInput(
                    type=InputType.NODE_LINK, link_reference=["7", 0]
                ),
                "start_percent": NodeInput(type=InputType.FLOAT, default=0.0),
                "end_percent": NodeInput(type=InputType.FLOAT, default=1.0),
            },
            outputs=[
                NodeOutput(name="M_MODELS", type="M_MODELS", slot_index=0),
            ],
        ),
        # 9: Use Evolved Sampling with autoselect beta schedule (not LCM)
        "9": NodeDefinition(
            logical_type="use_evolved_sampling",
            alias_priority=[
                "ADE_UseEvolvedSampling",
                "Use Evolved Sampling",
            ],
            inputs={
                "model": NodeInput(type=InputType.NODE_LINK, link_reference=["1", 0]),
                "beta_schedule": NodeInput(type=InputType.STRING, default="autoselect"),
                "m_models": NodeInput(
                    type=InputType.NODE_LINK, link_reference=["8", 0]
                ),
            },
            outputs=[
                NodeOutput(name="MODEL", type="MODEL", slot_index=0),
            ],
        ),
        # 10: KSampler with standard settings (euler, 20 steps, cfg 7.5)
        # Uses VAE-encoded source image as latent_image for img2vid effect
        # denoise < 1.0 preserves source image content while adding motion
        "10": NodeDefinition(
            logical_type="ksampler",
            alias_priority=["KSampler", "KSamplerAdvanced"],
            inputs={
                "model": NodeInput(type=InputType.NODE_LINK, link_reference=["9", 0]),
                "positive": NodeInput(
                    type=InputType.NODE_LINK, link_reference=["4", 0]
                ),
                "negative": NodeInput(
                    type=InputType.NODE_LINK, link_reference=["5", 0]
                ),
                "latent_image": NodeInput(
                    type=InputType.NODE_LINK, link_reference=["6b", 0]
                ),
                "seed": NodeInput(type=InputType.INT, default=0),
                "steps": NodeInput(type=InputType.INT, default=20),
                "cfg": NodeInput(type=InputType.FLOAT, default=7.5),
                "sampler_name": NodeInput(type=InputType.STRING, default="euler"),
                "scheduler": NodeInput(type=InputType.STRING, default="normal"),
                "denoise": NodeInput(type=InputType.FLOAT, default=0.55),
            },
            outputs=[NodeOutput(name="LATENT", type="LATENT", slot_index=0)],
        ),
        # 11: VAE decode to images
        "11": NodeDefinition(
            logical_type="vae_decode",
            alias_priority=["VAEDecode", "VAE Decode"],
            inputs={
                "samples": NodeInput(
                    type=InputType.NODE_LINK, link_reference=["10", 0]
                ),
                "vae": NodeInput(type=InputType.NODE_LINK, link_reference=["1", 2]),
            },
            outputs=[NodeOutput(name="IMAGE", type="IMAGE", slot_index=0)],
        ),
        # 12: Combine frames into video
        "12": NodeDefinition(
            logical_type="video_combine",
            alias_priority=["VHS_VideoCombine", "Video Combine", "VHS VideoCombine"],
            inputs={
                "images": NodeInput(type=InputType.NODE_LINK, link_reference=["11", 0]),
                "frame_rate": NodeInput(type=InputType.INT, default=8),
                "loop_count": NodeInput(type=InputType.INT, default=0),
                "pingpong": NodeInput(type=InputType.BOOLEAN, default=False),
                "save_output": NodeInput(type=InputType.BOOLEAN, default=True),
                "filename_prefix": NodeInput(
                    type=InputType.STRING, default="opensns_video"
                ),
                "format": NodeInput(type=InputType.STRING, default="video/h264-mp4"),
            },
            outputs=[
                NodeOutput(name="VIDEO", type="VIDEO", slot_index=0),
                NodeOutput(name="GIF", type="GIF", slot_index=1),
            ],
        ),
    },
    outputs=[
        WorkflowOutput(
            node_id="12", output_key="gifs", output_type="video", slot_index=1
        ),
        WorkflowOutput(
            node_id="12", output_key="video", output_type="video", slot_index=0
        ),
    ],
    required_models={
        "sd15_base": "checkpoints",
    },
    defaults={
        "prompt": "Smooth product showcase, professional advertisement, gentle motion",
        "num_frames": 16,
        "frame_rate": 8,
    },
)
