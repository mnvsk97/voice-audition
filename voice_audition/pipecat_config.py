"""
Generate drop-in Pipecat pipeline configuration for a recommended voice.
"""

from __future__ import annotations

from .models import Provider, Voice

_TEMPLATES: dict[Provider, str] = {
    Provider.CARTESIA: '''from pipecat.services.cartesia import CartesiaTTSService

tts = CartesiaTTSService(
    api_key=os.getenv("CARTESIA_API_KEY"),
    voice_id="{voice_id}",  # {name}
    model_id="sonic-2",
    language="en",
)''',

    Provider.ELEVENLABS: '''from pipecat.services.elevenlabs import ElevenLabsTTSService

tts = ElevenLabsTTSService(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
    voice_id="{voice_id}",  # {name}
    model="eleven_turbo_v2_5",
)''',

    Provider.DEEPGRAM: '''from pipecat.services.deepgram import DeepgramTTSService

tts = DeepgramTTSService(
    api_key=os.getenv("DEEPGRAM_API_KEY"),
    voice="{voice_id}",  # {name}
)''',

    Provider.OPENAI: '''from pipecat.services.openai import OpenAITTSService

tts = OpenAITTSService(
    api_key=os.getenv("OPENAI_API_KEY"),
    voice="{voice_id}",  # {name}
    model="tts-1",
)''',

    Provider.PLAYHT: '''from pipecat.services.playht import PlayHTTTSService

tts = PlayHTTTSService(
    api_key=os.getenv("PLAYHT_API_KEY"),
    user_id=os.getenv("PLAYHT_USER_ID"),
    voice="{voice_id}",  # {name}
)''',

    Provider.RIME: '''from pipecat.services.rime import RimeTTSService

tts = RimeTTSService(
    api_key=os.getenv("RIME_API_KEY"),
    voice="{voice_id}",  # {name}
    model="mist",
)''',

    Provider.AZURE: '''from pipecat.services.azure import AzureTTSService

tts = AzureTTSService(
    api_key=os.getenv("AZURE_SPEECH_KEY"),
    region=os.getenv("AZURE_SPEECH_REGION"),
    voice="{voice_id}",  # {name}
)''',

    Provider.GOOGLE: '''from pipecat.services.google import GoogleTTSService

tts = GoogleTTSService(
    voice_name="{voice_id}",  # {name}
)''',
}


def generate_pipecat_config(voice: Voice) -> str:
    template = _TEMPLATES.get(voice.provider, "# No Pipecat template for {provider}")
    return template.format(
        voice_id=voice.provider_voice_id,
        name=voice.name,
        provider=voice.provider.value,
    )
