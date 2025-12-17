from pathlib import Path
from typing import Optional
import os


class TranscriptionService:
    """
    Transcription service with deterministic mock output

    Phase 4 will replace this with actual STT provider integration
    """

    async def transcribe_audio(self, audio_path: Path) -> dict:
        """
        Transcribe audio file to text

        Currently returns deterministic mock transcription based on file metadata.
        This allows the workflow to proceed end-to-end without external dependencies.

        TODO: Phase 4 - Replace with actual STT provider integration:

        Option 1 - OpenAI Whisper API:
            import openai
            with open(audio_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe("whisper-1", audio_file)
            return {
                "text": transcript.text,
                "status": "completed",
                "confidence": None,
                "language": transcript.language,
                "duration": transcript.duration
            }

        Option 2 - AssemblyAI:
            import assemblyai as aai
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(str(audio_path))
            return {
                "text": transcript.text,
                "status": "completed",
                "confidence": transcript.confidence,
                "language": "en",
                "duration": transcript.audio_duration
            }

        Option 3 - Google Speech-to-Text:
            from google.cloud import speech
            client = speech.SpeechClient()
            with open(audio_path, "rb") as audio_file:
                content = audio_file.read()
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(...)
            response = client.recognize(config=config, audio=audio)
            return {
                "text": " ".join([result.alternatives[0].transcript for result in response.results]),
                "status": "completed",
                "confidence": response.results[0].alternatives[0].confidence,
                "language": "en-US",
                "duration": None
            }

        Args:
            audio_path: Path to the audio file to transcribe

        Returns:
            dict: {
                "text": str - Transcribed text
                "status": str - "completed" or "failed"
                "confidence": float - Transcription confidence (0-1)
                "language": str - Detected language
                "duration": float - Audio duration in seconds
            }

        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If audio file is invalid
        """
        # Validate audio file exists
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Validate file is not empty
        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            raise ValueError("Audio file is empty")

        # Generate deterministic mock transcription based on file metadata
        # This allows testing the full workflow without real STT
        transcription_text = self._generate_mock_transcription(audio_path, file_size)

        # Calculate mock duration (assume ~1 minute per MB as rough estimate)
        estimated_duration = (file_size / 1024 / 1024) * 60.0

        return {
            "text": transcription_text,
            "status": "completed",
            "confidence": 0.95,  # Mock high confidence
            "language": "en-US",
            "duration": round(estimated_duration, 2)
        }

    def _generate_mock_transcription(self, audio_path: Path, file_size: int) -> str:
        """
        Generate deterministic mock transcription for testing

        In production, this would be replaced with actual STT output.
        The mock is based on file metadata to be deterministic.

        Args:
            audio_path: Path to audio file
            file_size: Size of audio file in bytes

        Returns:
            str: Mock transcription text
        """
        filename = audio_path.stem
        size_mb = file_size / 1024 / 1024

        # Generate a realistic sales call transcription template
        # Use file size to vary the conversation length
        if size_mb < 1:
            # Short call (< 1MB ~ < 1 minute)
            return (
                f"Agent: Hi, this is calling from our sales team. "
                f"I wanted to reach out about our solution. "
                f"Customer: Thanks for calling. Can you send me some information? "
                f"Agent: Absolutely, I'll send that right over. "
                f"Customer: Great, thanks. "
                f"Agent: Have a great day!"
            )
        elif size_mb < 5:
            # Medium call (1-5MB ~ 1-5 minutes)
            return (
                f"Agent: Good morning! This is calling from the sales team. "
                f"How are you doing today? "
                f"Customer: I'm doing well, thanks. What's this regarding? "
                f"Agent: I wanted to discuss how our platform can help streamline your workflow. "
                f"We've worked with companies similar to yours and seen great results. "
                f"Customer: Interesting. What kind of results are we talking about? "
                f"Agent: On average, our clients see a 30% improvement in efficiency. "
                f"We focus on automating repetitive tasks so your team can focus on high-value work. "
                f"Customer: That sounds promising. Can you tell me more about pricing? "
                f"Agent: Of course. Our pricing is based on team size and features needed. "
                f"Would it make sense to schedule a demo call next week? "
                f"Customer: Yes, let's do that. Tuesday afternoon works for me. "
                f"Agent: Perfect! I'll send you a calendar invite. "
                f"Looking forward to showing you what we can do. "
                f"Customer: Sounds good, talk to you then. "
                f"Agent: Thanks for your time!"
            )
        else:
            # Long call (> 5MB ~ > 5 minutes)
            return (
                f"Agent: Good afternoon! This is calling from the sales team. "
                f"Thanks for taking the time to speak with me today. "
                f"Customer: No problem. I've been looking into solutions like yours. "
                f"Agent: That's great to hear. Can you tell me a bit about what prompted your search? "
                f"Customer: Well, we're currently using a mix of spreadsheets and manual processes. "
                f"It's becoming hard to scale as we grow. We're at about 50 employees now. "
                f"Agent: I completely understand. That's actually a common pain point we help solve. "
                f"Many of our clients were in a similar situation before switching to our platform. "
                f"Can I ask, what's your biggest challenge right now? "
                f"Customer: Honestly, it's tracking everything across different teams. "
                f"Sales, marketing, and customer success all use different tools. "
                f"We lose a lot of information in the handoffs. "
                f"Agent: That makes total sense. Our platform provides a unified view across all teams. "
                f"Everything lives in one place, so nothing falls through the cracks. "
                f"Customer: How long does implementation typically take? "
                f"Agent: Great question. For a team your size, we usually see full implementation "
                f"within 4-6 weeks. We provide white-glove onboarding and training. "
                f"Customer: What about data migration from our current systems? "
                f"Agent: We handle that as part of onboarding. Our team will work with you "
                f"to map your existing data and migrate it securely. "
                f"Customer: And pricing? What should we expect? "
                f"Agent: For a team of 50, you'd be looking at our Professional plan. "
                f"That starts at $5,000 per month, but includes everything - "
                f"unlimited users, all features, dedicated support, and implementation. "
                f"Customer: That's actually less than I expected. We're paying more now "
                f"for multiple tools that don't talk to each other. "
                f"Agent: Exactly. Most clients find they save money by consolidating tools. "
                f"Plus, the productivity gains more than pay for themselves. "
                f"Would you be interested in seeing a demo? I can show you "
                f"how it would work specifically for your use case. "
                f"Customer: Yes, I think that would be helpful. "
                f"Can we include our Head of Operations in that call? "
                f"Agent: Absolutely. The more stakeholders we can include, the better. "
                f"How does next Wednesday at 2 PM look for you? "
                f"Customer: Let me check... Yes, that works. "
                f"Agent: Perfect. I'll send a calendar invite with a Zoom link. "
                f"I'll also include some case studies from similar companies. "
                f"Customer: That would be great. Looking forward to it. "
                f"Agent: Excellent. Thanks so much for your time today. "
                f"I'm excited to show you what we can do. "
                f"Customer: Thanks. Talk to you next week. "
                f"Agent: Have a great rest of your day!"
            )

    def get_transcription_status(self, call_id: int) -> dict:
        """
        Get status of transcription job

        TODO: Phase 4 - Implement status checking for async transcription jobs

        For background job queues (Celery/RQ):
            from celery.result import AsyncResult
            task = AsyncResult(task_id)
            return {
                "status": task.status,
                "progress": task.info.get("progress", 0) if task.info else 0
            }
        """
        return {
            "status": "completed",
            "progress": 100
        }
