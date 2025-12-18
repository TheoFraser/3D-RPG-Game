"""Sound effect management."""
import pygame
import numpy as np
from pygame import mixer
from game.logger import get_logger

logger = get_logger(__name__)


class SoundManager:
    """Manages sound effects."""

    def __init__(self, enabled=True):
        """Initialize the sound manager."""
        self.enabled = enabled
        if self.enabled:
            try:
                mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                self.sounds = {}
                self.generate_sounds()
            except pygame.error as e:
                logger.warning(f"Audio initialization failed: {e}")
                self.enabled = False

    def generate_sounds(self):
        """Generate simple procedural sound effects."""
        if not self.enabled:
            return

        # Footstep sound (low thud)
        self.sounds['footstep'] = self.generate_tone(100, 0.1, volume=0.3)

        # Jump sound (rising pitch)
        self.sounds['jump'] = self.generate_sweep(200, 400, 0.15, volume=0.4)

        # Collect sound (high ping)
        self.sounds['collect'] = self.generate_tone(800, 0.2, volume=0.5)

        # Door open sound (low to mid sweep)
        self.sounds['door_open'] = self.generate_sweep(150, 250, 0.3, volume=0.4)

        # Lever pull sound (click)
        self.sounds['lever'] = self.generate_tone(300, 0.1, volume=0.5)

        # Button press (short beep)
        self.sounds['button'] = self.generate_tone(400, 0.08, volume=0.5)

        # Success/unlock sound (ascending notes)
        self.sounds['unlock'] = self.generate_chord([400, 500, 600], 0.3, volume=0.4)

    def generate_tone(self, frequency, duration, volume=0.5):
        """Generate a simple tone."""
        sample_rate = 22050
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)

        # Generate sine wave
        wave = np.sin(2 * np.pi * frequency * t)

        # Apply envelope (fade in/out)
        envelope = np.ones_like(wave)
        fade_samples = int(sample_rate * 0.01)  # 10ms fade
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)

        wave = wave * envelope * volume

        # Convert to 16-bit integers
        wave = (wave * 32767).astype(np.int16)

        # Make stereo
        stereo = np.column_stack((wave, wave))

        return pygame.sndarray.make_sound(stereo)

    def generate_sweep(self, start_freq, end_freq, duration, volume=0.5):
        """Generate a frequency sweep."""
        sample_rate = 22050
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)

        # Linear frequency sweep
        freq = np.linspace(start_freq, end_freq, samples)
        phase = 2 * np.pi * np.cumsum(freq) / sample_rate
        wave = np.sin(phase)

        # Apply envelope
        envelope = np.ones_like(wave)
        fade_samples = int(sample_rate * 0.01)
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)

        wave = wave * envelope * volume

        # Convert to 16-bit
        wave = (wave * 32767).astype(np.int16)
        stereo = np.column_stack((wave, wave))

        return pygame.sndarray.make_sound(stereo)

    def generate_chord(self, frequencies, duration, volume=0.3):
        """Generate a chord (multiple frequencies)."""
        sample_rate = 22050
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)

        # Sum all frequencies
        wave = np.zeros(samples)
        for freq in frequencies:
            wave += np.sin(2 * np.pi * freq * t)

        wave = wave / len(frequencies)  # Normalize

        # Apply envelope
        envelope = np.ones_like(wave)
        fade_samples = int(sample_rate * 0.02)
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)

        wave = wave * envelope * volume

        # Convert to 16-bit
        wave = (wave * 32767).astype(np.int16)
        stereo = np.column_stack((wave, wave))

        return pygame.sndarray.make_sound(stereo)

    def play(self, sound_name):
        """Play a sound effect."""
        if self.enabled and sound_name in self.sounds:
            self.sounds[sound_name].play()

    def cleanup(self):
        """Clean up audio resources."""
        if self.enabled:
            mixer.quit()
