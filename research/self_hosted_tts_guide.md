# Self-Hosting TTS Voices: A Practical Guide (2025-2026)

## 1. What Does It Take to Self-Host a TTS Voice?

### GPU Requirements

| Model Category | Example Models | Min VRAM | Recommended GPU | Can Run on CPU? |
|---|---|---|---|---|
| Tiny (< 100M params) | Kokoro (82M), Piper | 1-2 GB | CPU or any GPU | Yes, fast |
| Small (100-500M params) | Chatterbox (350M), StyleTTS2, Parler-TTS Mini (880M) | 4-8 GB | RTX 3060/4060, T4 | Slow but possible |
| Medium (500M-2B params) | XTTS v2, Parler-TTS Large (2.3B), F5-TTS | 8-16 GB | RTX 4090, A10, L4 | Impractical |
| Large (3B+) | Orpheus (3B), Fish Speech S2 Pro (4B) | 16-40 GB | A100 40GB, H100 MIG | No |

### Latency Achievable

Real-world time-to-first-byte (TTFB) numbers from documentation and benchmarks:

| Model | TTFB | RTF | Notes |
|---|---|---|---|
| Kokoro (82M) | ~50-100ms | Very fast | CPU-capable, ONNX optimized |
| Piper | ~30-80ms | Near-instant | Designed for Raspberry Pi |
| Chatterbox Turbo | ~100-150ms | Single-step diffusion | Optimized for voice agents |
| XTTS v2 | <200ms | ~0.3-0.5 | With streaming enabled |
| Orpheus (3B) | ~100-200ms | Real-time | Via vLLM; ~83 tokens/sec needed for real-time |
| Fish Speech S2 Pro | ~100ms | 0.195 RTF | On H200; needs 24GB+ VRAM |
| F5-TTS | ~253ms | 0.04 RTF | On L20 GPU, client-server mode |
| StyleTTS2 | ~150-300ms | Varies | Experimental streaming in forks |
| Bark | 2-10 sec | >1.0 | No streaming, generates full clips |

**Bottom line: Yes, sub-200ms TTFB is achievable** with Kokoro, Piper, XTTS, Orpheus, Fish Speech, and Chatterbox Turbo on appropriate hardware.

### Streaming Support

Models with native streaming audio output:
- **Kokoro**: Chunk-based generation
- **XTTS v2**: Native streaming, <200ms latency
- **Orpheus**: Streaming via vLLM, ~100-200ms
- **Fish Speech**: Native streaming with SGLang
- **Chatterbox Turbo**: Designed for streaming voice agents
- **F5-TTS**: Chunk inference mode
- **WhisperSpeech**: Streaming inference supported

Models that do NOT stream well:
- **Bark**: Generates full 13-second clips, no streaming
- **MARS5**: No streaming documented
- **StyleTTS2**: Only via unofficial forks

### Scaling: Concurrent Requests per GPU

Based on real deployment data:

| Setup | Concurrency |
|---|---|
| Orpheus 3B on H100 MIG (40GB) | 16-24 concurrent real-time streams |
| Fish Speech on H200 | High throughput (3,000+ tokens/sec, RTF < 0.5) |
| Kokoro on single CPU | 5-10 concurrent (it's tiny) |
| Piper on CPU | 10-20+ concurrent (extremely lightweight) |
| XTTS on A100 | ~5-10 concurrent streams (heavier model) |

### Infrastructure Requirements

**Minimum viable self-hosted stack:**
- Docker container with CUDA runtime
- NVIDIA GPU with appropriate VRAM
- Inference server: vLLM (for LLM-based TTS like Orpheus), or native Python server
- Load balancer (nginx/HAProxy) for multiple replicas
- Health checks and auto-restart

**Production stack:**
- Kubernetes with NVIDIA GPU operator
- NVIDIA Triton Inference Server or vLLM for batching
- Horizontal pod autoscaler based on GPU utilization
- Monitoring (Prometheus + Grafana for GPU metrics)
- CDN for audio caching (if applicable)
- Redis for request queuing

### Cost Comparison: Self-Hosted vs API

**API providers (per million characters, approximate 2025-2026 pricing):**
- ElevenLabs: $11-30/M chars (depending on plan)
- Cartesia: ~$8-15/M chars
- OpenAI TTS: ~$15/M chars
- Deepgram: ~$5-10/M chars

**Self-hosted on cloud GPU (estimated):**
- Kokoro on CPU (c5.xlarge): ~$0.17/hr = ~$125/month. At ~50 chars/sec, handles ~130M chars/month = **<$1/M chars**
- Orpheus on H100 MIG: ~$3.75/hr (Baseten) = ~$2,700/month. Handles 16-24 concurrent streams
- XTTS on A100: ~$2.50-4.00/hr = ~$1,800-2,900/month

**Breakeven point:** Self-hosting typically breaks even at ~10-50M characters/month depending on model choice. For lightweight models like Kokoro/Piper, even low volumes are cheaper self-hosted if you already have infrastructure.

---

## 2. Open Source TTS Models Worth Considering

### Tier 1: Production-Ready, Actively Maintained

#### Kokoro (hexgrad/kokoro) - 82M params
- **Status**: Most popular on HuggingFace (3.26K likes). Apache 2.0 license
- **Quality**: Comparable to models 10x its size. Based on StyleTTS2 architecture
- **Hardware**: Runs on CPU. 82M params fits anywhere
- **Languages**: EN, ES, FR, HI, IT, JA, PT-BR, ZH
- **Streaming**: Chunk-based
- **Best for**: Cost-sensitive deployments, edge/on-device, high concurrency
- **Install**: `pip install kokoro`
- **Replicate**: 85.7M runs (most-run TTS model on platform)

#### Orpheus TTS (canopyai/Orpheus-TTS) - 3B params
- **Status**: 6K GitHub stars. Based on Llama-3.2-3B
- **Quality**: Human-level speech with emotion/intonation control via tags
- **Hardware**: ~8-16GB VRAM (3B params); also runs on CPU via llama.cpp (slow)
- **Latency**: ~200ms streaming, ~100ms with input streaming
- **Streaming**: Native via vLLM
- **Concurrency**: 16-24 real-time streams on H100 MIG 40GB
- **Best for**: Expressive, emotional speech; voice agent applications
- **Deployment**: Baseten one-click, vLLM, llama.cpp

#### Fish Speech S2 Pro (fishaudio/fish-speech) - 4B params
- **Status**: Active development. 80+ languages
- **Quality**: State-of-the-art multilingual. Voice cloning from 10-30s reference
- **Hardware**: Minimum 24GB VRAM. Benchmarked on H200
- **Latency**: ~100ms TTFB, 0.195 RTF
- **Streaming**: Native with SGLang, continuous batching
- **Best for**: Multilingual production deployments, voice cloning
- **Note**: Trained on 10M+ hours of audio

#### Chatterbox (resemble-ai/chatterbox) - 350M-500M params
- **Status**: MIT license. By Resemble AI
- **Variants**: Turbo (350M, EN), Multilingual (500M, 23+ langs), Original (500M, EN)
- **Quality**: Competitive with ElevenLabs Turbo per benchmarks
- **Hardware**: Low VRAM (single-step diffusion in Turbo)
- **Features**: Voice cloning, emotion tags ([laugh], [cough]), Perth watermarking
- **Best for**: Voice agents needing low-latency + voice cloning
- **Replicate**: 257K+ runs

#### Piper (rhasspy/piper, now OHF-Voice/piper1-gpl)
- **Status**: Archived original, new development at OHF-Voice. GPL license
- **Quality**: Good for its size, not human-level
- **Hardware**: Runs on Raspberry Pi. Pure CPU, extremely fast
- **Languages**: 30+ languages, many voices
- **Streaming**: Yes
- **Best for**: Edge devices, embedded systems, privacy-first deployments
- **Limitation**: Less natural than neural models; no voice cloning

### Tier 2: Strong but with Caveats

#### XTTS v2 (coqui-ai/TTS)
- **Status**: 45K GitHub stars. MPL 2.0 license. Coqui company shut down but repo is community-maintained
- **Quality**: Good multilingual voice cloning
- **Hardware**: 4-8GB VRAM
- **Latency**: <200ms with streaming
- **Languages**: 16 languages
- **Caveat**: Company defunct, maintenance uncertain long-term. Pipecat and LiveKit both have XTTS integrations

#### F5-TTS (SWivid/F5-TTS) - Diffusion Transformer
- **Status**: 2.84K HuggingFace likes. Active development
- **Quality**: Good zero-shot voice cloning
- **Hardware**: Benchmarked on L20 GPU
- **Latency**: 253ms average TTFB (client-server)
- **Features**: Multi-speaker, voice chat mode, chunk inference
- **Best for**: Voice cloning applications where 250ms+ latency is acceptable

#### StyleTTS2 (yl4579/StyleTTS2)
- **Quality**: "Surpasses human recordings" on LJSpeech benchmark
- **Hardware**: Training needs 4x A100. Inference lighter (~4-8GB VRAM)
- **Streaming**: Experimental, third-party forks only
- **Caveat**: Single/multi-speaker but no easy voice cloning. Research-oriented

#### Parler-TTS (huggingface/parler-tts) - 880M / 2.3B params
- **Quality**: Good, trained on 45K hours of audiobooks
- **Hardware**: Mini (880M) fits on consumer GPU; Large (2.3B) needs 8-16GB
- **Features**: Control voice via natural language descriptions ("a calm female voice")
- **Streaming**: Supported
- **Best for**: When you need controllable voice characteristics without specific cloning

#### OpenVoice V2 (myshell-ai/OpenVoice)
- **Quality**: Good voice cloning, MIT license
- **Features**: Tone cloning, style control, cross-lingual capability
- **Languages**: EN, ES, FR, ZH, JA, KO
- **Best for**: Voice cloning specifically (use with another base TTS)

### Tier 3: Usable but Limited

#### Bark (suno-ai/bark) - MIT License
- **Hardware**: 12GB VRAM (full), 8GB (small)
- **Quality**: Can generate music, laughter, sound effects
- **Latency**: 2-10 seconds. No streaming. Generates 13-second clips
- **Best for**: Creative/expressive audio generation, NOT real-time voice agents

#### MARS5 (Camb-ai/MARS5-TTS)
- **Hardware**: ~750M + 450M params on GPU
- **Quality**: Good for challenging scenarios (sports, anime)
- **Streaming**: Not supported
- **Caveat**: Speed optimizations listed as "future work"

#### WhisperSpeech (collabora/WhisperSpeech)
- **Quality**: Good, based on inverting Whisper
- **Hardware**: 12x faster-than-real-time on RTX 4090
- **Features**: Voice cloning, streaming, Apache/MIT license
- **Caveat**: English only currently

### Emerging / Noteworthy (2025-2026)

#### Qwen3-TTS (Alibaba)
- 222.7K runs on Replicate. Voice cloning + design modes. Worth watching

#### Inworld TTS 1.5 (Inworld AI)
- Available on Replicate. <120-200ms latency. 15 languages. Emotion control
- Commercial but offered as API on Replicate

#### MiniMax Speech 2.8
- Available on Replicate and Together AI. 40+ languages. Voice cloning
- Commercial model, API access

---

## 3. Managed Inference Platforms for TTS

### Replicate
- **TTS models available**: Kokoro (85.7M runs!), XTTS v2, Chatterbox, Inworld TTS, MiniMax Speech, ElevenLabs, Qwen3-TTS
- **GPU pricing**: T4 $0.81/hr, L40S $3.51/hr, A100 $5.04/hr, H100 $5.49/hr
- **Billing**: Per-second for GPU time during inference
- **DX**: Push a Docker container or use their Python SDK. Cold starts of 5-30 sec typical
- **Best for**: Prototyping, low-to-medium volume, wrapping open source models
- **URL**: https://replicate.com/collections/text-to-speech (34+ TTS models)

### Baseten
- **TTS models**: Orpheus TTS one-click deploy, others via custom Truss packaging
- **GPU pricing**: T4 $0.63/hr, L4 $0.85/hr, A100 $4.00/hr, H100 $6.50/hr, H100 MIG $3.75/hr
- **Billing**: Pay only for active compute, not idle
- **Key data point**: Orpheus on H100 MIG handles 16-24 concurrent real-time streams
- **Best for**: Production TTS deployment with auto-scaling
- **URL**: https://www.baseten.co/library/orpheus-tts/

### Modal
- **TTS examples**: Chatterbox deployment guide, Moshi voice chatbot
- **GPU pricing**: T4 $0.59/hr, L4 $0.80/hr, A10 $1.10/hr, A100-80GB $2.50/hr, H100 $3.95/hr
- **Billing**: Per-second, pay only for compute used. No idle charges
- **Concurrency**: 10 GPUs (Starter), 50 GPUs (Team)
- **DX**: Python-first. Decorate functions with `@app.function(gpu="A100")`. Excellent developer experience
- **Best for**: Developers who want code-first deployment with minimal infrastructure
- **URL**: https://modal.com

### RunPod
- **GPU options**: Everything from RTX 3090 to H200
- **Serverless**: Sub-200ms cold starts with FlashBoot. Flex and Active workers
- **Billing**: Per-millisecond for serverless
- **Best for**: Raw GPU rental, custom Docker containers, budget-conscious scaling
- **URL**: https://www.runpod.io

### BentoML / BentoCloud
- **Features**: Deploy any model, auto-scaling, canary deployments, scale-to-zero
- **GPUs**: H100, MI300X, B200
- **DX**: Python SDK, define services as classes. Good for complex inference pipelines
- **Best for**: Teams wanting Kubernetes-grade deployment without managing K8s
- **URL**: https://www.bentoml.com

### TrueFoundry
- **Features**: Kubernetes-native, GPU orchestration, fractional GPU sharing (MIG/time-slicing)
- **Monitoring**: Built-in GPU memory and node health tracking
- **DX**: Supports containerized deployments with Grafana/Datadog integration
- **Best for**: Enterprise teams with existing K8s infrastructure
- **URL**: https://www.truefoundry.com

### Together AI
- **TTS models**: MiniMax Speech 2.6 Turbo, Cartesia Sonic-3 ($65/M tokens), Deepgram models
- **Note**: Limited TTS selection, more focused on LLMs
- **URL**: https://together.ai

### Fireworks AI
- **TTS**: No TTS models offered. Only ASR (Whisper)
- **URL**: https://fireworks.ai

---

## 4. Real-World Complexities

### Voice Cloning Legal Issues
- **Right of publicity**: Cloning a real person's voice without consent is illegal in many US states (CA, NY, TN, and others have specific laws)
- **EU AI Act**: Requires disclosure when AI-generated speech is used
- **FTC**: Has taken enforcement actions against deceptive AI voice cloning
- **Mitigation**: Always get explicit written consent. Some models (Chatterbox) include watermarking (Perth) for detection
- **Commercial safe zone**: Use pre-built voices from the model, or clone only voices you have rights to

### Quality vs Latency Tradeoffs
- **Diffusion models** (F5-TTS, Chatterbox): Quality improves with more diffusion steps, but latency increases. Chatterbox Turbo solves this with single-step distillation
- **Autoregressive models** (Orpheus, Fish Speech): Streaming-friendly but can hallucinate/repeat. Need careful temperature tuning
- **Non-autoregressive** (Kokoro, Piper): Fastest but less expressive
- **Rule of thumb**: For voice agents, prioritize latency (<200ms TTFB). For batch audiobook generation, prioritize quality

### Streaming Audio Format Compatibility
- **PCM/WAV**: Universal, no decoding overhead, large bandwidth
- **Opus**: Best for real-time (WebRTC default). Supported by Pipecat, LiveKit
- **MP3**: Wide compatibility but higher encoding latency
- **AAC**: Good for mobile apps
- **Key concern**: Your TTS model outputs raw audio (usually PCM/WAV), and you need to encode on-the-fly. Opus encoding adds ~5ms. Many models output 24kHz audio; voice agents typically need 16kHz or 24kHz

### Scaling to 100+ Concurrent Calls
- **Horizontal scaling**: Multiple GPU replicas behind load balancer
- **Request queuing**: Redis or RabbitMQ to buffer bursts
- **Autoscaling**: Scale replicas based on queue depth, not just GPU utilization
- **GPU sharing**: Small models (Kokoro) can serve many requests per GPU. Large models (Fish Speech) may need dedicated GPUs per few streams
- **Estimated hardware for 100 concurrent streams**:
  - Kokoro: 2-4 CPU instances
  - Orpheus: 5-7 H100 MIG instances
  - Fish Speech: 8-10 A100/H200 instances

### Monitoring, Failover, Redundancy
- **Metrics to track**: TTFB (p50, p95, p99), GPU utilization, VRAM usage, queue depth, error rate, audio quality (via MOS scoring on samples)
- **Failover**: Run replicas across availability zones. Use health checks on /synthesize endpoints
- **Graceful degradation**: Fall back to a lighter model (Kokoro) if primary model (Orpheus) is overloaded
- **Audio validation**: Check output isn't silence or corrupted before sending to client

### Integration with Voice Agent Frameworks

#### Pipecat
- **Built-in TTS support**: Cartesia, ElevenLabs, Deepgram, OpenAI, Fish, Kokoro, Piper, XTTS, and 20+ more
- **Self-hosted**: Direct integrations for Piper and XTTS. Kokoro supported natively
- **Custom**: Pluggable architecture lets you add any TTS via a service class
- **Audio format**: Handles streaming audio chunking internally

#### LiveKit
- **Built-in**: Cartesia, Deepgram, ElevenLabs, Inworld, Rime, xAI via LiveKit Inference
- **Plugins**: 30+ provider plugins for Python and Node.js
- **Self-hosted**: Not built-in, but custom TTS nodes can wrap any model
- **Note**: "LiveKit especially welcomes new TTS, STT, and LLM plugins"

---

## 5. When Does Self-Hosting Make Sense vs Using an API?

### Cost Breakeven Analysis

| Monthly Volume | Recommendation | Reasoning |
|---|---|---|
| < 1M chars/month | Use API | Not worth infrastructure overhead. ElevenLabs/Cartesia ~$10-30/month |
| 1-10M chars/month | API or lightweight self-host | Kokoro on a $50/mo CPU VM handles this easily |
| 10-50M chars/month | Self-host lightweight model | Clear savings. Kokoro/Piper: ~$50-150/mo vs $100-500/mo API |
| 50-500M chars/month | Self-host with GPU | Orpheus/Chatterbox on GPU: ~$1-3K/mo vs $500-5K/mo API. Quality parity reached |
| 500M+ chars/month | Definitely self-host | 5-20x savings vs API. Justify dedicated infrastructure team |

### Quality Comparison (Open Source vs Commercial, 2025-2026)

The gap has narrowed dramatically:
- **Kokoro 82M** matches or exceeds many commercial offerings for English
- **Orpheus 3B** is described as matching closed-source quality for expressive speech
- **Fish Speech S2 Pro** is competitive with ElevenLabs for multilingual
- **Chatterbox Turbo** benchmarks favorably against ElevenLabs Turbo and Cartesia Sonic

**Where commercial still wins:**
- Consistency across diverse inputs
- Broader language coverage with uniform quality
- Ready-made voice libraries (ElevenLabs has thousands)
- Zero infrastructure burden
- Enterprise SLAs and support

### Latency Comparison

| | Self-Hosted | API |
|---|---|---|
| Best case TTFB | 30-100ms (Piper/Kokoro on local GPU) | 100-200ms (Cartesia, ElevenLabs Turbo) |
| Typical TTFB | 100-300ms | 150-400ms |
| Worst case | 300-500ms (cold start, large model) | 500-2000ms (cold start, rate limits) |
| Network overhead | None (if colocated) | 20-100ms per hop |

Self-hosted wins on latency when colocated with your voice agent infrastructure.

### Privacy/Compliance Requirements

Self-host when:
- **HIPAA**: Patient voice data cannot leave your infrastructure
- **GDPR**: Audio data must stay in EU region (and your API provider doesn't offer EU endpoints)
- **Financial services**: Regulatory requirements for data residency
- **Government**: FedRAMP or similar compliance frameworks
- **IP protection**: Proprietary voice models or fine-tuned voices you don't want on third-party servers

---

## 6. Platform Deployment Experience

### Modal (Best DX for developers)
```python
# Example: Deploy Kokoro on Modal
import modal
app = modal.App("tts-kokoro")

@app.function(gpu="T4", image=modal.Image.pip_install("kokoro"))
def synthesize(text: str) -> bytes:
    from kokoro import KPipeline
    pipeline = KPipeline(lang_code='a')
    audio = pipeline(text)
    return audio
```
- Pros: Code-first, no Dockerfiles needed, auto-scaling, per-second billing
- Cons: Vendor lock-in, 10 GPU concurrency limit on Starter plan

### Replicate (Best for wrapping existing models)
- Many TTS models already deployed (Kokoro has 85.7M runs)
- Use existing models with zero setup: `replicate.run("jaaari/kokoro-82m", input={...})`
- Custom models via Cog (Docker-based packaging)
- Pros: Huge model library, simple API, no infrastructure
- Cons: Cold starts (5-30s), less control over optimization

### Baseten (Best for production TTS)
- One-click deploy for Orpheus TTS
- Truss framework for custom models
- Proven: 16-24 concurrent real-time Orpheus streams on H100 MIG
- Pros: Production-grade auto-scaling, no idle charges, fp8/fp16 optimization
- Cons: Smaller model library than Replicate

### TrueFoundry (Best for enterprise K8s teams)
- Deploy any containerized model on your own K8s cluster
- Fractional GPU sharing (run multiple small models on one GPU)
- Built-in monitoring with Grafana/Datadog
- Pros: Full control, works on your infra, GPU orchestration
- Cons: More setup required, enterprise-oriented pricing

---

## Summary Recommendations

### For voice agent startups (need low latency, moderate scale):
1. Start with **Kokoro** (82M) or **Chatterbox Turbo** (350M) on **Modal** or **Replicate**
2. Use **Pipecat** for voice agent framework integration
3. Graduate to **Baseten** or self-hosted K8s when hitting 50+ concurrent streams

### For multilingual production (80+ languages):
1. **Fish Speech S2 Pro** on A100/H200 via Baseten or self-hosted
2. Fall back to **ElevenLabs API** for languages not well-covered

### For maximum quality on English:
1. **Orpheus 3B** via vLLM on H100 MIG for expressive emotional speech
2. **Chatterbox Turbo** for fastest response with voice cloning

### For privacy/compliance:
1. Self-host **Kokoro** or **Piper** on your own infrastructure
2. Both have permissive licenses (Apache 2.0 / GPL respectively)

### For budget deployments:
1. **Kokoro** on CPU — handles production load at ~$50-150/month
2. **Piper** for embedded/edge devices — runs on Raspberry Pi
