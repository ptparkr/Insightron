# LLM Integration in Insightron

Insightron leverages Large Language Models (LLMs) to significantly enhance transcription quality through **Contextual Restoration** (Multi-Pass Pass 2). This guide explains how to enable, configure, and optimize LLM usage within Insightron.

---

## 🚀 Overview: Why Use LLMs?

While Whisper is excellent at acoustic transcription, it occasionally makes phonetic errors or misses complex punctuation. The LLM integration in Insightron performs a "second pass" over the transcribed text to:

1.  **Add Proper Punctuation**: Correctly place periods, commas, and question marks based on grammatical structure.
2.  **Fix Phonetic Errors**: Correct mishearings and homophones (e.g., "there" vs "their") using surrounding context.
3.  **Ensure Flow**: Improve paragraphing and overall readability without altering the original meaning.

---

## 🛠️ Enabling LLM Features

LLM features are part of the **Multi-Pass Transcription Pipeline**. To use them, you must enable Multi-Pass in your `config.yaml`.

### 1. Enable Multi-Pass
Open `config.yaml` and find the `multi_pass` section:

```yaml
multi_pass:
  enabled: true  # Set this to true
  chunk_duration: 30
  chunk_overlap: 2
```

### 2. Configure Contextual Restoration
Ensure the `contextual_restoration` sub-section is enabled:

```yaml
  contextual_restoration:
    enabled: true
    provider: "local" # Options: "local" or "openai"
```

---

## 💻 Option 1: Local LLMs (Recommended for Privacy)

Using a local model means no data leaves your machine and there are no API fees. This requires a decent GPU or enough RAM for CPU inference.

### 📦 Setup
If you haven't installed the LLM dependencies yet, run:
```bash
pip install transformers torch accelerate bitsandbytes
```

### ⚙️ Configuration
In `config.yaml`, configure the `local_model` settings:

```yaml
    local_model:
      # Recommended high-quality, lightweight model
      model_name: "Qwen/Qwen2.5-3B-Instruct" 
      
      # Device: "auto" (uses GPU if available), "cpu", or "cuda"
      device: "auto"
      
      # Quantization: "4bit" (lowest RAM usage) or "8bit"
      quantization: "4bit"
      
      temperature: 0.3
      max_tokens: 2000
```

*Note: The first time you use a local model, Insightron will download it from Hugging Face (~2.5GB for Qwen2.5-3B).*

---

## 🌐 Option 2: API Providers (OpenAI)

If you have limited hardware or want a faster experience without downloading large files, use an API provider.

### ⚙️ Configuration
Update the `provider` and `api_settings` in `config.yaml`:

```yaml
    provider: "openai"
    
    api_settings:
      # Leave empty to use the OPENAI_API_KEY environment variable
      api_key: "your-api-key-here"
      
      # Options: "gpt-3.5-turbo", "gpt-4", etc.
      model: "gpt-3.5-turbo"
      
      temperature: 0.3
```

---

## 💡 Best Practices

1.  **Selection of Provider**: If you have a machine with 8GB+ VRAM, **Local (4-bit)** is excellent. If you are on a thin laptop, **OpenAI** is significantly faster.
2.  **Model Choice**: The default `Qwen/Qwen2.5-3B-Instruct` is highly optimized for instruction-following and fits in roughly 3GB of VRAM when quantized to 4-bit.
3.  **Temperature**: Keep the `temperature` low (0.1 - 0.3). Higher temperatures might cause the LLM to "hallucinate" or add its own thoughts to the transcription, which we want to avoid.

---

## ⚠️ Troubleshooting

-   **Memory Errors (Local)**: If you get "CUDA Out of Memory," try changing `quantization` to `4bit` or switching `device` to `cpu`.
-   **Slow Processing**: LLM restoration adds an additional delay after the acoustic transcription. This is normal. Smaller chunks (`chunk_duration: 30`) help keep the latency predictable.
-   **Missing Dependencies**: Ensure you've installed the `transformers` library if using local models.
