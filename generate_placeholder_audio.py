"""Generate improved placeholder ambient audio files for the game."""
import numpy as np
import wave
import os

def generate_layered_noise(duration=60, sample_rate=44100, layers=5, volume=0.3):
    """
    Generate multi-layered brown noise for richer ambient sounds.

    Args:
        duration: Length in seconds
        sample_rate: Sample rate in Hz
        layers: Number of frequency layers
        volume: Overall volume

    Returns:
        Audio data as int16 array
    """
    samples = int(duration * sample_rate)
    result = np.zeros(samples, dtype=np.float32)

    for layer in range(layers):
        # Generate white noise
        noise = np.random.uniform(-1, 1, samples)

        # Apply brown noise filter with different coefficients per layer
        alpha = 0.92 + (layer * 0.015)  # Vary filtering per layer
        filtered = np.zeros_like(noise)
        filtered[0] = noise[0]

        for i in range(1, len(noise)):
            filtered[i] = filtered[i-1] * alpha + noise[i] * (1 - alpha)

        # Normalize
        filtered = filtered / np.max(np.abs(filtered))

        # Add amplitude modulation for natural variation
        mod_freq = 0.05 + (layer * 0.02)  # Very slow modulation
        modulation = 0.7 + 0.3 * np.sin(2 * np.pi * mod_freq * np.linspace(0, duration, samples))
        filtered *= modulation

        # Layer weight (lower layers stronger)
        weight = 1.0 / (layer + 1)
        result += filtered * weight

    # Normalize
    result = result / np.max(np.abs(result))

    # Apply seamless loop envelope (fade edges to same value)
    fade_length = int(0.1 * sample_rate)  # 100ms fade
    fade_in = np.linspace(0, 1, fade_length)
    fade_out = np.linspace(1, 0, fade_length)

    # Crossfade beginning and end
    result[:fade_length] = result[:fade_length] * fade_in + result[-fade_length:] * fade_out

    return (result * volume * 32767).astype(np.int16)

def generate_natural_tone(duration=60, sample_rate=44100, base_freq=200, harmonics=5, volume=0.2):
    """
    Generate a natural-sounding tone with harmonics and variation.

    Args:
        duration: Length in seconds
        sample_rate: Sample rate in Hz
        base_freq: Base frequency in Hz
        harmonics: Number of harmonic overtones
        volume: Overall volume

    Returns:
        Audio data as int16 array
    """
    samples = int(duration * sample_rate)
    t = np.linspace(0, duration, samples, False)
    result = np.zeros(samples, dtype=np.float32)

    # Add fundamental and harmonics
    for h in range(harmonics):
        harmonic_num = h + 1
        freq = base_freq * harmonic_num
        amplitude = 1.0 / harmonic_num  # Harmonics decrease in amplitude

        # Add slight frequency modulation for natural character
        freq_mod = 1.0 + 0.002 * np.sin(2 * np.pi * 0.1 * t)
        wave = np.sin(2 * np.pi * freq * freq_mod * t)

        result += wave * amplitude

    # Amplitude modulation for breathing effect
    breath_mod = 0.8 + 0.2 * np.sin(2 * np.pi * 0.05 * t)
    result *= breath_mod

    # Normalize
    result = result / np.max(np.abs(result))

    # Seamless loop
    fade_length = int(0.5 * sample_rate)
    fade = np.ones(samples)
    fade[:fade_length] = np.linspace(0, 1, fade_length)
    fade[-fade_length:] = np.linspace(1, 0, fade_length)

    # Ensure loop point continuity
    loop_offset = result[0] - result[-1]
    ramp = np.linspace(0, loop_offset, samples)
    result = result - ramp

    result *= fade

    return (result * volume * 32767).astype(np.int16)

def generate_water_sound(duration=60, sample_rate=44100, volume=0.25):
    """Generate flowing water sound using filtered noise."""
    samples = int(duration * sample_rate)

    # Multiple noise layers at different frequencies
    water = np.zeros(samples, dtype=np.float32)

    # High frequency hiss (splashing)
    noise1 = np.random.uniform(-1, 1, samples)
    # Light filtering
    for i in range(1, len(noise1)):
        noise1[i] = noise1[i-1] * 0.3 + noise1[i] * 0.7
    water += noise1 * 0.5

    # Mid frequency (flowing)
    noise2 = np.random.uniform(-1, 1, samples)
    for i in range(1, len(noise2)):
        noise2[i] = noise2[i-1] * 0.7 + noise2[i] * 0.3

    # Add slow modulation
    mod = 0.7 + 0.3 * np.sin(2 * np.pi * 0.2 * np.linspace(0, duration, samples))
    water += noise2 * mod * 0.8

    # Normalize
    water = water / np.max(np.abs(water))

    # Seamless loop
    fade_length = int(0.2 * sample_rate)
    water[:fade_length] *= np.linspace(0, 1, fade_length)
    water[-fade_length:] *= np.linspace(1, 0, fade_length)

    return (water * volume * 32767).astype(np.int16)

def generate_rain(duration=60, sample_rate=44100, intensity=0.5, volume=0.3):
    """
    Generate rain sound with proper density.

    Args:
        intensity: 0.0 to 1.0, affects drop density
    """
    samples = int(duration * sample_rate)
    rain = np.zeros(samples, dtype=np.float32)

    # Base noise (rain on surfaces)
    base = generate_layered_noise(duration, sample_rate, layers=3, volume=1.0)
    rain = base.astype(np.float32) / 32767.0

    # Add individual drop impacts
    drop_rate = int(sample_rate * 0.01 / (intensity + 0.1))  # Drops per samples
    drop_length = int(0.05 * sample_rate)

    for i in range(0, samples, drop_rate):
        if np.random.random() < intensity:
            # Generate single drop sound
            drop = np.random.uniform(-1, 1, drop_length)
            # Exponential decay
            envelope = np.exp(-np.linspace(0, 8, drop_length))
            drop = drop * envelope

            # Add to rain sound
            end_idx = min(i + drop_length, samples)
            actual_length = end_idx - i
            rain[i:end_idx] += drop[:actual_length] * 0.1

    # Clip and normalize
    rain = np.clip(rain, -1, 1)

    return (rain * volume * 32767).astype(np.int16)

def save_wav(filename, audio_data, sample_rate=44100):
    """Save audio data as WAV file."""
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())

def main():
    """Generate all improved placeholder audio files."""
    output_dir = "assets/audio/ambient"
    os.makedirs(output_dir, exist_ok=True)

    print("Generating improved ambient audio files (this may take a minute)...")
    print("Each file is 60 seconds for seamless looping\n")

    # Wind sounds (layered noise at different intensities)
    print("  - wind_gentle.wav")
    save_wav(f"{output_dir}/wind_gentle.wav",
             generate_layered_noise(60, layers=4, volume=0.15))

    print("  - wind_strong.wav")
    save_wav(f"{output_dir}/wind_strong.wav",
             generate_layered_noise(60, layers=6, volume=0.25))

    # Bird sounds (multiple tones with variation)
    print("  - birds_day.wav")
    birds = generate_natural_tone(60, base_freq=1800, harmonics=3, volume=0.08)
    birds2 = generate_natural_tone(60, base_freq=2300, harmonics=2, volume=0.06)
    save_wav(f"{output_dir}/birds_day.wav",
             np.clip(birds.astype(np.int32) + birds2.astype(np.int32), -32767, 32767).astype(np.int16))

    # Cricket sounds (higher frequency modulated tone)
    print("  - crickets_night.wav")
    crickets_tone = generate_natural_tone(60, base_freq=3800, harmonics=2, volume=0.05)
    crickets_noise = generate_layered_noise(60, layers=2, volume=0.08)
    save_wav(f"{output_dir}/crickets_night.wav",
             np.clip(crickets_tone.astype(np.int32) + crickets_noise.astype(np.int32), -32767, 32767).astype(np.int16))

    # Water stream
    print("  - water_stream.wav")
    save_wav(f"{output_dir}/water_stream.wav", generate_water_sound(60, volume=0.2))

    # Forest ambience (layered low tones and soft noise)
    print("  - forest_ambience.wav")
    forest_tone = generate_natural_tone(60, base_freq=180, harmonics=4, volume=0.08)
    forest_noise = generate_layered_noise(60, layers=3, volume=0.12)
    save_wav(f"{output_dir}/forest_ambience.wav",
             np.clip(forest_tone.astype(np.int32) + forest_noise.astype(np.int32), -32767, 32767).astype(np.int16))

    # Cave drips (sparse rhythmic plinks)
    print("  - cave_drips.wav")
    samples = int(60 * 44100)
    drips = np.zeros(samples, dtype=np.float32)
    # Add random drips
    for _ in range(100):  # About 1.7 drips per second
        pos = np.random.randint(0, samples - 1000)
        drip_env = np.exp(-np.linspace(0, 15, 1000))
        drip = np.random.uniform(-1, 1, 1000) * drip_env * 0.3
        drips[pos:pos+1000] += drip
    # Add cave reverb (soft noise)
    drips += generate_layered_noise(60, layers=2, volume=0.05).astype(np.float32) / 32767.0
    save_wav(f"{output_dir}/cave_drips.wav",
             (np.clip(drips, -1, 1) * 32767).astype(np.int16))

    # Desert wind (lower frequency, sandier)
    print("  - desert_wind.wav")
    save_wav(f"{output_dir}/desert_wind.wav",
             generate_layered_noise(60, layers=5, volume=0.18))

    # Snow wind (softer, higher)
    print("  - snow_wind.wav")
    save_wav(f"{output_dir}/snow_wind.wav",
             generate_layered_noise(60, layers=4, volume=0.16))

    # Rain sounds
    print("  - rain_light.wav")
    save_wav(f"{output_dir}/rain_light.wav", generate_rain(60, intensity=0.3, volume=0.18))

    print("  - rain_heavy.wav")
    save_wav(f"{output_dir}/rain_heavy.wav", generate_rain(60, intensity=0.8, volume=0.25))

    # Thunder (low rumble with variation)
    print("  - thunder.wav")
    thunder_low = generate_natural_tone(60, base_freq=60, harmonics=5, volume=0.12)
    thunder_mid = generate_natural_tone(60, base_freq=120, harmonics=3, volume=0.08)
    thunder_noise = generate_layered_noise(60, layers=4, volume=0.10)
    thunder = np.clip(
        thunder_low.astype(np.int32) + thunder_mid.astype(np.int32) + thunder_noise.astype(np.int32),
        -32767, 32767
    ).astype(np.int16)
    save_wav(f"{output_dir}/thunder.wav", thunder)

    print(f"\nGenerated 12 high-quality ambient audio files in {output_dir}/")
    print("Each file is 60 seconds long and loops seamlessly.")
    print("Audio uses layered synthesis for richer, more natural sound.")

if __name__ == "__main__":
    main()
