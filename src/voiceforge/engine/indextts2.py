"""IndexTTS-2 engine implementation."""

from __future__ import annotations

import os
from pathlib import Path

import torch
import torchaudio

from voiceforge.audio.utils import get_duration, scan_clips
from voiceforge.engine.base import EngineInfo, ProfileData, TTSEngine
from voiceforge.engine.registry import register
from voiceforge.profile.schema import VoiceProfile

_PROFILE_SENTINEL = "__profile_loaded__"

# Default model paths (relative to index-tts repo)
_DEFAULT_CFG = "checkpoints/config.yaml"
_DEFAULT_MODEL_DIR = "checkpoints"


def _find_indextts_root() -> Path:
    """Locate the index-tts installation directory."""
    try:
        import indextts
        return Path(indextts.__file__).resolve().parents[1]
    except (ImportError, AttributeError):
        # Fallback to known path
        return Path.home() / "workspaces" / "tts" / "index-tts"


@register("indextts2")
class IndexTTS2Engine(TTSEngine):
    """IndexTTS-2 voice cloning engine."""

    def __init__(self) -> None:
        self._tts = None  # Lazy-loaded

    def info(self) -> EngineInfo:
        return EngineInfo(
            name="indextts2",
            version="2.0.0",
            description="IndexTTS-2: Emotionally expressive auto-regressive zero-shot TTS",
        )

    def _ensure_loaded(self) -> None:
        """Lazily load the IndexTTS2 model."""
        if self._tts is not None:
            return

        from indextts.infer_v2 import IndexTTS2

        root = _find_indextts_root()
        cfg_path = str(root / _DEFAULT_CFG)
        model_dir = str(root / _DEFAULT_MODEL_DIR)

        self._tts = IndexTTS2(cfg_path=cfg_path, model_dir=model_dir, use_fp16=True)

    def extract_profile(
        self,
        clips_dir: Path,
        *,
        max_clips: int | None = None,
    ) -> ProfileData:
        self._ensure_loaded()
        tts = self._tts

        clips = scan_clips(clips_dir)
        if not clips:
            raise FileNotFoundError(f"No WAV files found in {clips_dir}")

        if max_clips is not None:
            clips = clips[:max_clips]

        # Step 1: Average CAMPPlus style across all clips
        styles: list[torch.Tensor] = []
        failed: list[str] = []
        with torch.no_grad():
            for clip in clips:
                try:
                    style = self._extract_style(clip)
                    styles.append(style)
                except Exception:
                    failed.append(clip.name)

        if not styles:
            raise RuntimeError("Failed to extract style from any clip")

        avg_style = torch.stack(styles).mean(dim=0)  # (1, 192)

        # Step 2: Extract sequence features from best clip
        best_clip = self._select_best_clip(clips_dir)
        best_clip_name = best_clip.name
        best_clip_duration = get_duration(best_clip)

        with torch.no_grad():
            spk_cond, _, s2mel_prompt, mel = self._extract_sequence_features(best_clip)

        tensors = {
            "style": avg_style.cpu(),
            "spk_cond": spk_cond.cpu(),
            "s2mel_prompt": s2mel_prompt.cpu(),
            "mel": mel.cpu(),
        }
        metadata = {
            "source_clips_count": len(styles),
            "failed_clips": failed,
            "best_clip_name": best_clip_name,
            "best_clip_duration": best_clip_duration,
        }
        return ProfileData(tensors=tensors, metadata=metadata)

    def synthesize(
        self,
        profile: VoiceProfile,
        text: str,
        output_path: Path,
        *,
        emotion_text: str | None = None,
        emotion_alpha: float = 1.0,
    ) -> Path:
        self._ensure_loaded()
        tts = self._tts

        # Inject profile tensors into the TTS cache
        device = tts.device
        tts.cache_s2mel_style = profile.tensors["style"].to(device)
        tts.cache_spk_cond = profile.tensors["spk_cond"].to(device)
        tts.cache_s2mel_prompt = profile.tensors["s2mel_prompt"].to(device)
        tts.cache_mel = profile.tensors["mel"].to(device)

        # Sentinel prevents cache invalidation
        tts.cache_spk_audio_prompt = _PROFILE_SENTINEL
        tts.cache_emo_cond = profile.tensors["spk_cond"].to(device)
        tts.cache_emo_audio_prompt = _PROFILE_SENTINEL

        output_path.parent.mkdir(parents=True, exist_ok=True)

        use_emo_text = emotion_text is not None
        tts.infer(
            spk_audio_prompt=_PROFILE_SENTINEL,
            text=text,
            output_path=str(output_path),
            use_emo_text=use_emo_text,
            emo_text=emotion_text,
            emo_alpha=emotion_alpha,
            verbose=True,
        )
        return output_path

    # -- Internal helpers --

    def _extract_style(self, audio_path: Path) -> torch.Tensor:
        """Extract CAMPPlus style embedding (1, 192) from a single clip."""
        import librosa

        tts = self._tts
        audio, sr = librosa.load(str(audio_path))
        audio = torch.tensor(audio).unsqueeze(0)

        max_samples = int(15 * sr)
        if audio.shape[1] > max_samples:
            audio = audio[:, :max_samples]

        audio_16k = torchaudio.transforms.Resample(sr, 16000)(audio)

        feat = torchaudio.compliance.kaldi.fbank(
            audio_16k.to(tts.device),
            num_mel_bins=80,
            dither=0,
            sample_frequency=16000,
        )
        feat = feat - feat.mean(dim=0, keepdim=True)
        return tts.campplus_model(feat.unsqueeze(0))  # (1, 192)

    def _extract_sequence_features(self, audio_path: Path):
        """Extract all sequence-level features from a single clip.

        Returns: (spk_cond, style, s2mel_prompt, mel)
        """
        import librosa

        tts = self._tts
        audio, sr = librosa.load(str(audio_path))
        audio = torch.tensor(audio).unsqueeze(0)

        max_samples = int(15 * sr)
        if audio.shape[1] > max_samples:
            audio = audio[:, :max_samples]

        audio_22k = torchaudio.transforms.Resample(sr, 22050)(audio)
        audio_16k = torchaudio.transforms.Resample(sr, 16000)(audio)

        # Semantic embedding (W2V-BERT layer 17)
        inputs = tts.extract_features(audio_16k, sampling_rate=16000, return_tensors="pt")
        input_features = inputs["input_features"].to(tts.device)
        attention_mask = inputs["attention_mask"].to(tts.device)
        spk_cond_emb = tts.get_emb(input_features, attention_mask)

        # Semantic codec
        _, S_ref = tts.semantic_codec.quantize(spk_cond_emb)

        # Mel spectrogram
        ref_mel = tts.mel_fn(audio_22k.to(spk_cond_emb.device).float())
        ref_target_lengths = torch.LongTensor([ref_mel.size(2)]).to(ref_mel.device)

        # Style (CAMPPlus)
        feat = torchaudio.compliance.kaldi.fbank(
            audio_16k.to(ref_mel.device),
            num_mel_bins=80,
            dither=0,
            sample_frequency=16000,
        )
        feat = feat - feat.mean(dim=0, keepdim=True)
        style = tts.campplus_model(feat.unsqueeze(0))

        # Length regulator
        prompt_condition = tts.s2mel.models["length_regulator"](
            S_ref, ylens=ref_target_lengths, n_quantizers=3, f0=None
        )[0]

        return spk_cond_emb, style, prompt_condition, ref_mel

    def _select_best_clip(self, clips_dir: Path) -> Path:
        """Select the longest clip (up to 15s) as reference."""
        clips = scan_clips(clips_dir)
        if not clips:
            raise FileNotFoundError(f"No WAV files found in {clips_dir}")

        best: Path | None = None
        best_dur = 0.0
        for clip in clips:
            dur = get_duration(clip)
            if dur > best_dur and dur <= 15.0:
                best_dur = dur
                best = clip

        if best is None:
            # All clips > 15s — just pick the first one (will be truncated)
            best = clips[0]

        return best
