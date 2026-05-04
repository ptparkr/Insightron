#!/usr/bin/env python3
"""
LLM Provider Abstraction for Insightron Multi-Pass Transcription
Supports local models and API-based LLMs for contextual text restoration.
"""

import os
import logging
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RestorationResult:
    """Result from LLM-based text restoration"""
    original_text: str
    restored_text: str
    processing_time: float = 0.0
    # Optional segment-level restored texts; when present this should be aligned
    # 1:1 with the ASR segments used to build the chunk.
    segment_texts: Optional[List[str]] = None
    tokens_used: int = 0
    model_name: str = ""
    success: bool = True
    error: Optional[str] = None
    flags: List[str] = field(default_factory=list)
    stitched: bool = False


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM provider.
        
        Args:
            config: Configuration dictionary for the provider
        """
        self.config = config
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1.0)
    
    @abstractmethod
    def restore_text(
        self,
        text: str,
        prev_clean: Optional[str] = None,
        next_raw: Optional[str] = None,
        segment_count: Optional[int] = None,
    ) -> RestorationResult:
        """
        Restore punctuation and fix phonetic errors in text using v2 philosophy.
        
        Args:
            text: Raw transcribed text (current chunk)
            prev_clean: Optional cleaned text from previous chunk
            next_raw: Optional raw text from next chunk (lookahead)
            segment_count: Optional number of ASR segments represented in this chunk.
                When provided, the model is encouraged (but not required) to return
                a segment-aligned list of restored texts in segment_texts.
            
        Returns:
            RestorationResult object
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured correctly"""
        pass
    
    def _build_restoration_instructions(self) -> str:
        """
        Build system instructions for restoration.

        The provider may set `prompt_profile` in config to bias the style:
        This also defines the JSON contract expected from the model.
        - thinking_session
        - meeting_notes
        - study_notes
        """
        prompt_profile = (self.config.get("prompt_profile") or "").strip().lower()

        profile_hint = ""
        if prompt_profile == "thinking_session":
            profile_hint = (
                "\nSTYLE BIAS:\n"
                "- Preserve the speaker's stream-of-consciousness tone.\n"
                "- Improve clarity and sentence boundaries without rewriting ideas.\n"
            )
        elif prompt_profile == "meeting_notes":
            profile_hint = (
                "\nSTYLE BIAS:\n"
                "- Prefer crisp sentence boundaries.\n"
                "- Preserve explicit action verbs and commitments.\n"
                "- Do NOT output bullets or headings; just clean text.\n"
            )
        elif prompt_profile == "study_notes":
            profile_hint = (
                "\nSTYLE BIAS:\n"
                "- Preserve technical terms and symbols.\n"
                "- Be conservative when correcting domain language; flag uncertainty.\n"
            )

        system_content = (
            "You are the Post-Transcription Quality Engine for Insightron.\n"
            "Your job is to REPAIR, ALIGN, and CLARIFY messy speech-to-text output from ~30-second chunks.\n\n"
            "NORTH STAR: Same meaning. Fewer errors. Zero hallucinations.\n"
            f"{profile_hint}\n"
            "STAGE 1 — Mechanical Cleanup (Deterministic)\n"
            "- Remove strict filler noise (uh, um, er, ah)\n"
            "- Collapse repeated words/phrases caused by overlap\n"
            "- Fix casing, spacing, punctuation\n\n"
            "STAGE 2 — Boundary Intelligence (High ROI)\n"
            "- If a sentence starts mid-thought → stitch with prev_clean_chunk\n"
            "- If a sentence cuts off → allow completion using next_raw_chunk\n"
            "- Remove duplicated fragments across chunk boundaries\n"
            "- If unsure, LEAVE IT UNCHANGED and flag it.\n\n"
            "STAGE 3 — Semantic Repair (Conservative)\n"
            "- Correct obvious ASR errors using local context.\n"
            "- For technical/domain terms, ONLY repair if you are at least ~90% confident.\n"
            '- If unsure, LEAVE IT UNCHANGED and add "uncertain_term" to flags.\n\n'
            "STAGE 4 — No formatting\n"
            "- Output plain text only (no Markdown, no bullets, no headings).\n\n"
            "STAGE 5 — Confidence Signaling\n"
            "- Attach flags: low_audio_confidence, uncertain_term, possible_domain_error\n\n"
            "OUTPUT FORMAT (JSON ONLY):\n"
            "Return EXACTLY this JSON object and nothing else. The segment_texts field is OPTIONAL:\n"
            "{\n"
            '  \"clean_text\": \"...\",\n'
            '  \"flags\": [\"...\"],\n'
            "  \"stitched\": true/false,\n"
            "  \"segment_texts\": [\"segment1 text\", \"segment2 text\", \"...\"]\n"
            "}"
        )
        return system_content

    def _build_restoration_user_content(
        self,
        text: str,
        prev_clean: Optional[str] = None,
        next_raw: Optional[str] = None,
        segment_count: Optional[int] = None,
    ) -> str:
        """
        Build user content for restoration.

        When segment_count is provided, we inform the model how many ASR segments
        are represented in this chunk so it can optionally emit a segment-aligned
        list in segment_texts.
        """
        lines: List[str] = []
        if segment_count is not None:
            lines.append(f"segment_count: {segment_count}")
        if prev_clean:
            lines.append(f"prev_clean_chunk: {prev_clean}")
        lines.append(f"raw_chunk: {text}")
        if next_raw:
            lines.append(f"next_raw_chunk: {next_raw}")
        return "\n".join(lines) + "\n"

    def _build_restoration_prompt(
        self,
        text: str,
        prev_clean: Optional[str] = None,
        next_raw: Optional[str] = None,
        segment_count: Optional[int] = None,
    ) -> str:
        """
        Build the prompt for text restoration based on 5-stage philosophy.
        """
        system_content = self._build_restoration_instructions()
        user_content = self._build_restoration_user_content(
            text, prev_clean=prev_clean, next_raw=next_raw, segment_count=segment_count
        )

        # Detect model type
        is_llama = "llama" in self.config.get('model_name', '').lower() if hasattr(self, 'config') else False
        
        if is_llama:
            prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_content}<|eot_id|>"
            prompt += f"<|start_header_id|>user<|end_header_id|>\n\n{user_content}<|eot_id|>"
            prompt += "<|start_header_id|>assistant<|end_header_id|>\n\n"
        else:
            prompt = f"<|im_start|>system\n{system_content}\n<|im_end|>\n"
            prompt += f"<|im_start|>user\n{user_content}\n<|im_end|>\n"
            prompt += "<|im_start|>assistant\n"
        
        return prompt
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry.
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed: {e}")
        
        raise last_exception

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response, handling potential formatting issues.
        """
        import json
        import re
        
        # Try direct parse first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
            
        # Try extracting from code blocks
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try finding the first '{' and last '}'
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            try:
                return json.loads(response_text[start_idx:end_idx+1])
            except json.JSONDecodeError:
                pass
                
        # Fallback: return a dummy structure if parsing fails
        logger.warning(f"Failed to parse JSON from response: {response_text[:100]}...")
        return {
            "clean_text": response_text,
            "flags": ["parsing_error"],
            "stitched": False
        }


class LocalLLMProvider(BaseLLMProvider):
    """
    Provider for local LLMs using transformers library.
    Optimized for Intel i5-1235U (CPU inference).
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize local LLM provider.
        
        Args:
            config: Configuration with model_name, device, quantization, etc.
        """
        super().__init__(config)
        
        # Default to Qwen2.5-7B-Instruct for high-quality logic
        self.model_name = config.get('model_name', 'Qwen/Qwen2.5-7B-Instruct')
        self.device = config.get('device', 'cpu') # Force CPU for i5-1235U stability
        
        # For CPU, we typically use 4-bit (via bitsandbytes on Linux/WSL) 
        # or just half-precision torch if available.
        # On Windows i5-1235U, float32 is most stable, but we'll try torch.bfloat16 or float16 if supported.
        self.quantization = config.get('quantization', None) 
        
        # Token Management Question: How does max_new_tokens affect transcript quality?
        # Answer: If set too low (e.g. < 256), the model may cut off mid-sentence, 
        # making the transcript look broken. For 0.5B models on i5, 
        # a window of 512-4096 is recommended for long-form contextual restoration.
        self.max_tokens = config.get('max_tokens', 2048) 
        self.temperature = config.get('temperature', 0.2)
        
        self.model = None
        self.tokenizer = None
        self._initialized = False
    
    def _check_connectivity(self) -> bool:
        """Check for internet connectivity for model download"""
        import socket
        try:
            # Try to connect to a reliable host (HuggingFace or Google)
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except (socket.timeout, socket.error):
            return False

    def _lazy_load_model(self):
        """Lazy load the model when first needed"""
        if self._initialized:
            return
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
            import torch
            from huggingface_hub import scan_cache_dir
            
            logger.info(f"Loading local LLM: {self.model_name}")
            
            # 1. Validate local files or check connectivity
            is_cached = any(repo.repo_id == self.model_name for repo in scan_cache_dir().repos)
            if not is_cached:
                logger.info(f"Model {self.model_name} not found in cache. Checking connectivity...")
                if not self._check_connectivity():
                    raise ConnectionError(f"Internet connection unavailable and model '{self.model_name}' not cached.")
                logger.info("Connectivity confirmed. Starting download...")
            
            # i5-1235U specific optimization: use CPU inference with appropriate precision
            # Note: bitsandbytes 4-bit/8-bit is primarily for CUDA. 
            # For CPU, we rely on torch's default or quantized weights if provided in gguf/onnx.
            # Here we follow conventional transformers loading.
            
            # Load tokenizer
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
            
            # Load model
            logger.info(f"Loading model weights (device={self.device})...")
            
            model_kwargs = {
                'pretrained_model_name_or_path': self.model_name,
                'trust_remote_code': True,
                'device_map': self.device,
            }
            
            # Use bfloat16 for i5 if supported, otherwise float32 for maximum CPU stability
            if torch.cuda.is_available(): # Backwards compatibility if user has GPU
                 model_kwargs['torch_dtype'] = torch.float16
                 model_kwargs['device_map'] = 'auto'
            else:
                 # CPU optimization: float32 for maximum stability on Windows
                 model_kwargs['torch_dtype'] = torch.float32 
            
            # Configuration for quantization if requested
            if self.quantization == '4bit':
                logger.info("Enabling 4-bit quantization...")
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                    llm_int8_enable_fp32_cpu_offload=not torch.cuda.is_available()
                )
                model_kwargs['quantization_config'] = bnb_config
            elif self.quantization == '8bit':
                logger.info("Enabling 8-bit quantization...")
                bnb_config = BitsAndBytesConfig(
                    load_in_8bit=True,
                    llm_int8_enable_fp32_cpu_offload=not torch.cuda.is_available()
                )
                model_kwargs['quantization_config'] = bnb_config
            
            # Note for i5-1235U: bitsandbytes often requires a CUDA GPU or WSL.
            # On native Windows CPU, we primarily rely on standard torch loading
            # unless using a quantized model format like GGUF/ONNX.
            
            self.model = AutoModelForCausalLM.from_pretrained(**model_kwargs)
            
            self._initialized = True
            logger.info(f"Successfully loaded {self.model_name}")
            
        except ImportError as e:
            logger.error(f"Failed to import transformers: {e}")
            self._initialized = False
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            self._initialized = False
    
    def is_available(self) -> bool:
        """Check if local LLM is available"""
        try:
            import transformers
            import torch
            return True
        except ImportError:
            return False
    
    def restore_text(self, text: str, prev_clean: Optional[str] = None, next_raw: Optional[str] = None) -> RestorationResult:
        """
        Restore text using local LLM with v2 philosophy.
        """
        start_time = time.time()
        
        # Lazy load model
        self._lazy_load_model()
        
        if not self._initialized or self.model is None:
            return RestorationResult(
                original_text=text,
                restored_text=text,
                processing_time=time.time() - start_time,
                success=False,
                error="Model not initialized"
            )
        
        try:
            import torch
            # Build prompt
            logger.info("Building v2 restoration prompt...")
            prompt = self._build_restoration_prompt(
                text, prev_clean=prev_clean, next_raw=next_raw, segment_count=None
            )
            
            # Tokenize
            logger.info("Tokenizing input...")
            inputs = self.tokenizer(prompt, return_tensors="pt")
            if self.device not in ['auto', 'cpu']:
                inputs = inputs.to(self.device)
            
            # Generate
            logger.info(f"Generating v2 restoration (max_new_tokens={self.max_tokens})...")
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_tokens,
                    temperature=self.temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            logger.info("Generation complete, decoding...")
            
            # Decode
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract content after prompt
            actual_response = full_response[len(prompt):].strip() if full_response.startswith(prompt) else full_response
            
            # Parse JSON
            parsed = self._parse_json_response(actual_response)
            
            processing_time = time.time() - start_time
            tokens_used = outputs.shape[1]
            
            logger.info(f"Text restored in {processing_time:.2f}s ({tokens_used} tokens)")

            segment_texts = parsed.get("segment_texts")
            if segment_texts is not None and not isinstance(segment_texts, list):
                logger.warning("segment_texts present but not a list; ignoring this field.")
                segment_texts = None

            return RestorationResult(
                original_text=text,
                restored_text=parsed.get("clean_text", text),
                segment_texts=segment_texts,
                processing_time=processing_time,
                tokens_used=tokens_used,
                model_name=self.model_name,
                success=True,
                flags=parsed.get("flags", []),
                stitched=parsed.get("stitched", False),
            )
            
        except Exception as e:
            logger.error(f"Error during text restoration: {e}")
            return RestorationResult(
                original_text=text,
                restored_text=text,
                segment_texts=None,
                processing_time=time.time() - start_time,
                success=False,
                error=str(e),
                flags=["restoration_error"],
            )


class OpenAIProvider(BaseLLMProvider):
    """Provider for OpenAI API"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenAI provider.
        
        Args:
            config: Configuration with api_key, model, etc.
        """
        super().__init__(config)
        
        self.api_key = config.get('api_key') or os.environ.get('OPENAI_API_KEY')
        self.model = config.get('model', 'gpt-3.5-turbo')
        self.max_tokens = config.get('max_tokens', 2000)
        self.temperature = config.get('temperature', 0.3)
        
        self.client = None
    
    def _lazy_load_client(self):
        """Lazy load OpenAI client"""
        if self.client is not None:
            return
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized")
        except ImportError:
            logger.error("OpenAI library not installed. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def is_available(self) -> bool:
        """Check if OpenAI is available"""
        if not self.api_key:
            return False
        try:
            import openai
            return True
        except ImportError:
            return False
    
    def restore_text(self, text: str, prev_clean: Optional[str] = None, next_raw: Optional[str] = None) -> RestorationResult:
        """
        Restore text using OpenAI API with v2 philosophy.
        """
        start_time = time.time()
        
        self._lazy_load_client()
        
        if self.client is None:
            return RestorationResult(
                original_text=text,
                restored_text=text,
                processing_time=time.time() - start_time,
                success=False,
                error="OpenAI client not initialized",
                flags=["restoration_disabled"],
            )
        
        try:
            system_content = self._build_restoration_instructions()
            user_content = self._build_restoration_user_content(
                text, prev_clean=prev_clean, next_raw=next_raw, segment_count=None
            )
            
            response = self._retry_with_backoff(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            raw_response = response.choices[0].message.content.strip()
            parsed = self._parse_json_response(raw_response)

            tokens_used = response.usage.total_tokens
            processing_time = time.time() - start_time
            
            logger.info(f"OpenAI restoration completed in {processing_time:.2f}s ({tokens_used} tokens)")

            segment_texts = parsed.get("segment_texts")
            if segment_texts is not None and not isinstance(segment_texts, list):
                logger.warning("segment_texts present but not a list; ignoring this field.")
                segment_texts = None

            return RestorationResult(
                original_text=text,
                restored_text=parsed.get("clean_text", text),
                segment_texts=segment_texts,
                processing_time=processing_time,
                tokens_used=tokens_used,
                model_name=self.model,
                success=True,
                flags=parsed.get("flags", []),
                stitched=parsed.get("stitched", False),
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return RestorationResult(
                original_text=text,
                restored_text=text,
                processing_time=time.time() - start_time,
                success=False,
                error=str(e)
            )


class LLMProviderFactory:
    """Factory for creating LLM providers"""
    
    @staticmethod
    def create_provider(provider_type: str, config: Dict[str, Any]) -> BaseLLMProvider:
        """
        Create an LLM provider based on type.
        
        Args:
            provider_type: Type of provider ('local', 'openai', 'anthropic', 'google')
            config: Configuration dictionary
            
        Returns:
            BaseLLMProvider instance
            
        Raises:
            ValueError: If provider type is unknown
        """
        provider_type = provider_type.lower()
        
        if provider_type == 'local':
            return LocalLLMProvider(config)
        elif provider_type == 'openai':
            return OpenAIProvider(config)
        elif provider_type in ['anthropic', 'google']:
            # Placeholder for future implementation
            logger.warning(f"{provider_type} provider not yet implemented, falling back to local")
            return LocalLLMProvider(config)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
    
    @staticmethod
    def create_from_config(multi_pass_config: Dict[str, Any]) -> BaseLLMProvider:
        """
        Create provider from multi-pass config section.
        
        Args:
            multi_pass_config: Multi-pass config dictionary
            
        Returns:
            BaseLLMProvider instance
        """
        restoration_config = multi_pass_config.get('contextual_restoration', {})
        provider_type = restoration_config.get('provider', 'local')
        
        if provider_type == 'local':
            provider_config = restoration_config.get('local_model', {})
        else:
            provider_config = restoration_config.get('api_settings', {})
        
        # Add common settings
        provider_config['max_retries'] = restoration_config.get('max_retries', 3)
        provider_config['prompt_profile'] = restoration_config.get('prompt_profile')
        
        return LLMProviderFactory.create_provider(provider_type, provider_config)
