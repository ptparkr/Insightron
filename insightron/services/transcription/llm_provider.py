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
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RestorationResult:
    """Result from LLM-based text restoration"""
    original_text: str
    restored_text: str
    processing_time: float
    tokens_used: int = 0
    model_name: str = ""
    success: bool = True
    error: Optional[str] = None


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
    def restore_text(self, text: str, context: Optional[str] = None) -> RestorationResult:
        """
        Restore punctuation and fix phonetic errors in text.
        
        Args:
            text: Raw transcribed text
            context: Optional context from previous chunks
            
        Returns:
            RestorationResult object
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured correctly"""
        pass
    
    def _build_restoration_prompt(self, text: str, context: Optional[str] = None) -> str:
        """
        Build the prompt for text restoration.
        
        Args:
            text: Text to restore
            context: Optional context
            
        Returns:
            Formatted prompt string
        """
        prompt = """You are a text restoration assistant. Your task is to:
1. Add proper punctuation (periods, commas, question marks, exclamation points)
2. Fix phonetic errors (homophones, mishearings)
3. Preserve the original meaning and word order
4. Do NOT add, remove, or rearrange words unless fixing clear errors

"""
        
        if context:
            prompt += f"Context from previous text:\n{context}\n\n"
        
        prompt += f"""Raw transcribed text to restore:
{text}

Restored text:"""
        
        return prompt
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry.
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Function result or raises last exception
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


class LocalLLMProvider(BaseLLMProvider):
    """Provider for local LLMs using transformers library"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize local LLM provider.
        
        Args:
            config: Configuration with model_name, device, quantization, etc.
        """
        super().__init__(config)
        
        self.model_name = config.get('model_name', 'microsoft/phi-3-mini-4k-instruct')
        self.device = config.get('device', 'auto')
        self.quantization = config.get('quantization', '4bit')
        self.max_tokens = config.get('max_tokens', 2000)
        self.temperature = config.get('temperature', 0.3)
        
        self.model = None
        self.tokenizer = None
        self._initialized = False
    
    def _lazy_load_model(self):
        """Lazy load the model when first needed"""
        if self._initialized:
            return
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
            import torch
            
            logger.info(f"Loading local LLM: {self.model_name}")
            
            # Configure quantization if requested
            quantization_config = None
            if self.quantization == '4bit':
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            elif self.quantization == '8bit':
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True
                )
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Load model
            model_kwargs = {
                'pretrained_model_name_or_path': self.model_name,
                'trust_remote_code': True
            }
            
            if quantization_config:
                model_kwargs['quantization_config'] = quantization_config
                model_kwargs['device_map'] = 'auto'
            elif self.device != 'auto':
                model_kwargs['device_map'] = self.device
            else:
                model_kwargs['device_map'] = 'auto'
            
            self.model = AutoModelForCausalLM.from_pretrained(**model_kwargs)
            
            self._initialized = True
            logger.info(f"Successfully loaded {self.model_name}")
            
        except ImportError as e:
            logger.error(f"Failed to import transformers: {e}")
            logger.error("Install with: pip install transformers torch accelerate bitsandbytes")
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
    
    def restore_text(self, text: str, context: Optional[str] = None) -> RestorationResult:
        """
        Restore text using local LLM.
        
        Args:
            text: Raw text to restore
            context: Optional context from previous chunks
            
        Returns:
            RestorationResult object
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
            # Build prompt
            prompt = self._build_restoration_prompt(text, context)
            
            # Tokenize
            inputs = self.tokenizer(prompt, return_tensors="pt")
            if self.device not in ['auto', 'cpu']:
                inputs = inputs.to(self.device)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_tokens,
                    temperature=self.temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the restored text (after the prompt)
            restored_text = full_response[len(prompt):].strip()
            
            # Clean up any artifacts
            if not restored_text:
                restored_text = text
            
            processing_time = time.time() - start_time
            tokens_used = outputs.shape[1]
            
            logger.info(f"Text restored in {processing_time:.2f}s ({tokens_used} tokens)")
            
            return RestorationResult(
                original_text=text,
                restored_text=restored_text,
                processing_time=processing_time,
                tokens_used=tokens_used,
                model_name=self.model_name,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error during text restoration: {e}")
            return RestorationResult(
                original_text=text,
                restored_text=text,
                processing_time=time.time() - start_time,
                success=False,
                error=str(e)
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
    
    def restore_text(self, text: str, context: Optional[str] = None) -> RestorationResult:
        """
        Restore text using OpenAI API.
        
        Args:
            text: Raw text to restore
            context: Optional context
            
        Returns:
            RestorationResult object
        """
        start_time = time.time()
        
        self._lazy_load_client()
        
        if self.client is None:
            return RestorationResult(
                original_text=text,
                restored_text=text,
                processing_time=time.time() - start_time,
                success=False,
                error="OpenAI client not initialized"
            )
        
        try:
            prompt = self._build_restoration_prompt(text, context)
            
            response = self._retry_with_backoff(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a text restoration assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            restored_text = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens
            processing_time = time.time() - start_time
            
            logger.info(f"OpenAI restoration completed in {processing_time:.2f}s ({tokens_used} tokens)")
            
            return RestorationResult(
                original_text=text,
                restored_text=restored_text,
                processing_time=processing_time,
                tokens_used=tokens_used,
                model_name=self.model,
                success=True
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
        
        return LLMProviderFactory.create_provider(provider_type, provider_config)
