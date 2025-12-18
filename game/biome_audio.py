"""Biome-specific ambient audio system.

Provides atmospheric sounds that change based on the player's current biome,
time of day, and weather conditions.
"""
import pygame
import config
from game.logger import get_logger
from typing import Dict, List, Optional

logger = get_logger(__name__)


class AudioLayer:
    """A single audio layer (e.g., wind, birds, water)."""

    def __init__(self, name: str, file_path: str, base_volume: float = 0.5):
        """
        Initialize an audio layer.

        Args:
            name: Layer name
            file_path: Path to audio file
            base_volume: Base volume level (0.0-1.0)
        """
        self.name = name
        self.file_path = file_path
        self.base_volume = base_volume
        self.current_volume = 0.0
        self.target_volume = 0.0
        self.channel: Optional[pygame.mixer.Channel] = None
        self.sound: Optional[pygame.mixer.Sound] = None
        self.is_playing = False
        self.fade_speed = 0.5  # Volume change per second

    def load(self) -> bool:
        """
        Load the audio file.

        Returns:
            bool: True if loaded successfully
        """
        try:
            # Check if file exists
            import os
            if not os.path.exists(self.file_path):
                logger.warning(f"Audio file not found: {self.file_path} (skipping {self.name})")
                return False

            self.sound = pygame.mixer.Sound(self.file_path)
            logger.debug(f"Loaded audio layer: {self.name}")
            return True
        except Exception as e:
            logger.warning(f"Failed to load audio layer {self.name}: {e}")
            return False

    def play(self, loop: bool = True):
        """
        Start playing the layer.

        Args:
            loop: Whether to loop the sound
        """
        if self.sound is None:
            return

        if not self.is_playing:
            self.channel = self.sound.play(loops=-1 if loop else 0)
            if self.channel:
                self.channel.set_volume(0.0)  # Start silent
                self.is_playing = True
                logger.debug(f"Started playing: {self.name}")

    def stop(self):
        """Stop playing the layer."""
        if self.is_playing and self.channel:
            self.channel.stop()
            self.is_playing = False
            self.current_volume = 0.0

    def set_target_volume(self, volume: float):
        """
        Set the target volume for smooth transition.

        Args:
            volume: Target volume (0.0-1.0)
        """
        self.target_volume = max(0.0, min(1.0, volume))

    def update(self, delta_time: float):
        """
        Update volume smoothly.

        Args:
            delta_time: Time since last update
        """
        if not self.is_playing or self.channel is None:
            return

        # Smoothly transition to target volume
        if abs(self.current_volume - self.target_volume) > 0.01:
            if self.current_volume < self.target_volume:
                self.current_volume += self.fade_speed * delta_time
                self.current_volume = min(self.current_volume, self.target_volume)
            else:
                self.current_volume -= self.fade_speed * delta_time
                self.current_volume = max(self.current_volume, self.target_volume)

            self.channel.set_volume(self.current_volume * self.base_volume)


class BiomeAudioProfile:
    """Audio profile for a specific biome."""

    def __init__(self, biome_id: int, name: str):
        """
        Initialize a biome audio profile.

        Args:
            biome_id: Biome ID
            name: Biome name
        """
        self.biome_id = biome_id
        self.name = name
        self.layers: Dict[str, float] = {}  # layer_name -> target_volume

    def set_layer_volume(self, layer_name: str, volume: float):
        """
        Set volume for a layer in this biome.

        Args:
            layer_name: Name of the audio layer
            volume: Volume level (0.0-1.0)
        """
        self.layers[layer_name] = max(0.0, min(1.0, volume))

    def get_layer_volume(self, layer_name: str) -> float:
        """
        Get volume for a layer.

        Args:
            layer_name: Layer name

        Returns:
            float: Volume level (0.0 if not set)
        """
        return self.layers.get(layer_name, 0.0)


class BiomeAudioManager:
    """
    Manages ambient audio based on biome, time of day, and weather.

    Features:
    - Smooth transitions between biomes
    - Day/night variations
    - Weather-based audio changes
    - Multiple audio layers per biome
    """

    def __init__(self):
        """Initialize the biome audio manager."""
        self.layers: Dict[str, AudioLayer] = {}
        self.biome_profiles: Dict[int, BiomeAudioProfile] = {}
        self.current_biome = config.BIOME_GRASSLANDS
        self.master_volume = 0.7
        self.enabled = True

        # Initialize pygame mixer if not already done
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
                logger.info("Initialized pygame mixer for audio")
            except Exception as e:
                logger.error(f"Failed to initialize pygame mixer: {e}")
                self.enabled = False
                return

        # Create audio layers (these would reference actual audio files)
        self._create_audio_layers()

        # Create biome profiles
        self._create_biome_profiles()

        logger.info("Biome audio manager initialized")

    def _create_audio_layers(self):
        """Create all audio layers."""
        # Using generated placeholder WAV files

        # Base ambient layers
        self._add_layer("wind_gentle", "assets/audio/ambient/wind_gentle.wav", 0.4)
        self._add_layer("wind_strong", "assets/audio/ambient/wind_strong.wav", 0.6)
        self._add_layer("birds_day", "assets/audio/ambient/birds_day.wav", 0.3)
        self._add_layer("crickets_night", "assets/audio/ambient/crickets_night.wav", 0.3)
        self._add_layer("water_stream", "assets/audio/ambient/water_stream.wav", 0.4)
        self._add_layer("forest_ambience", "assets/audio/ambient/forest_ambience.wav", 0.5)
        self._add_layer("cave_drips", "assets/audio/ambient/cave_drips.wav", 0.3)
        self._add_layer("desert_wind", "assets/audio/ambient/desert_wind.wav", 0.5)
        self._add_layer("snow_wind", "assets/audio/ambient/snow_wind.wav", 0.5)
        self._add_layer("rain_light", "assets/audio/ambient/rain_light.wav", 0.6)
        self._add_layer("rain_heavy", "assets/audio/ambient/rain_heavy.wav", 0.7)
        self._add_layer("thunder", "assets/audio/ambient/thunder.wav", 0.8)

        logger.info(f"Created {len(self.layers)} audio layers")

    def _add_layer(self, name: str, file_path: str, base_volume: float):
        """
        Add an audio layer.

        Args:
            name: Layer name
            file_path: Path to audio file
            base_volume: Base volume level
        """
        layer = AudioLayer(name, file_path, base_volume)
        self.layers[name] = layer

    def _create_biome_profiles(self):
        """Create audio profiles for each biome."""
        # Grasslands - peaceful meadow
        grasslands = BiomeAudioProfile(config.BIOME_GRASSLANDS, "Grasslands")
        grasslands.set_layer_volume("wind_gentle", 0.5)
        grasslands.set_layer_volume("birds_day", 0.7)
        grasslands.set_layer_volume("crickets_night", 0.6)
        self.biome_profiles[config.BIOME_GRASSLANDS] = grasslands

        # Enchanted Forest - magical woodland
        forest = BiomeAudioProfile(config.BIOME_ENCHANTED_FOREST, "Enchanted Forest")
        forest.set_layer_volume("wind_gentle", 0.3)
        forest.set_layer_volume("birds_day", 0.9)
        forest.set_layer_volume("crickets_night", 0.8)
        forest.set_layer_volume("forest_ambience", 1.0)
        forest.set_layer_volume("water_stream", 0.4)
        self.biome_profiles[config.BIOME_ENCHANTED_FOREST] = forest

        # Crystal Caves - mystical echoing caverns
        caves = BiomeAudioProfile(config.BIOME_CRYSTAL_CAVES, "Crystal Caves")
        caves.set_layer_volume("cave_drips", 0.8)
        caves.set_layer_volume("wind_gentle", 0.2)
        self.biome_profiles[config.BIOME_CRYSTAL_CAVES] = caves

        # Floating Islands - windy heights
        islands = BiomeAudioProfile(config.BIOME_FLOATING_ISLANDS, "Floating Islands")
        islands.set_layer_volume("wind_strong", 1.0)
        islands.set_layer_volume("birds_day", 0.5)
        self.biome_profiles[config.BIOME_FLOATING_ISLANDS] = islands

        # Ancient Ruins - desolate and quiet
        ruins = BiomeAudioProfile(config.BIOME_ANCIENT_RUINS, "Ancient Ruins")
        ruins.set_layer_volume("desert_wind", 0.7)
        ruins.set_layer_volume("wind_gentle", 0.4)
        self.biome_profiles[config.BIOME_ANCIENT_RUINS] = ruins

        logger.info(f"Created {len(self.biome_profiles)} biome audio profiles")

    def load_all_layers(self):
        """Load all audio layers (call this during game initialization)."""
        if not self.enabled:
            return

        loaded_count = 0
        for layer in self.layers.values():
            if layer.load():
                loaded_count += 1

        logger.info(f"Loaded {loaded_count}/{len(self.layers)} audio layers")

    def start(self):
        """Start playing ambient audio."""
        if not self.enabled:
            return

        for layer in self.layers.values():
            layer.play(loop=True)

        logger.info("Started ambient audio playback")

    def stop(self):
        """Stop all ambient audio."""
        for layer in self.layers.values():
            layer.stop()

        logger.info("Stopped ambient audio playback")

    def set_biome(self, biome_id: int):
        """
        Change the current biome.

        Args:
            biome_id: New biome ID
        """
        if biome_id == self.current_biome:
            return

        self.current_biome = biome_id
        self._update_layer_targets()

        profile = self.biome_profiles.get(biome_id)
        if profile:
            logger.debug(f"Changed biome audio to: {profile.name}")

    def set_time_of_day(self, time_normalized: float):
        """
        Update audio based on time of day.

        Args:
            time_normalized: Time as 0.0-1.0 (0.0 = midnight, 0.5 = noon)
        """
        # Day time (6am - 8pm)
        is_day = 0.25 < time_normalized < 0.8

        # Adjust day/night layers
        for layer_name, layer in self.layers.items():
            if "day" in layer_name:
                # Fade in during day
                if is_day:
                    layer.target_volume = layer.base_volume
                else:
                    layer.target_volume = 0.0
            elif "night" in layer_name:
                # Fade in during night
                if not is_day:
                    layer.target_volume = layer.base_volume
                else:
                    layer.target_volume = 0.0

    def set_weather(self, weather_type: str, intensity: float = 1.0):
        """
        Update audio based on weather.

        Args:
            weather_type: Weather type name (e.g., "rain", "storm", "clear")
            intensity: Weather intensity (0.0-1.0)
        """
        # Reset weather layers
        for layer_name in ["rain_light", "rain_heavy", "thunder"]:
            if layer_name in self.layers:
                self.layers[layer_name].set_target_volume(0.0)

        # Apply weather audio
        if weather_type == "rain":
            if intensity < 0.5:
                self.layers["rain_light"].set_target_volume(intensity * 2.0)
            else:
                self.layers["rain_heavy"].set_target_volume((intensity - 0.5) * 2.0)
        elif weather_type == "storm":
            self.layers["rain_heavy"].set_target_volume(1.0)
            self.layers["thunder"].set_target_volume(intensity)
            # Increase wind during storms
            self.layers["wind_strong"].set_target_volume(intensity)

    def _update_layer_targets(self):
        """Update target volumes for all layers based on current biome."""
        profile = self.biome_profiles.get(self.current_biome)
        if not profile:
            return

        # Set target volumes based on biome profile
        for layer_name, layer in self.layers.items():
            target = profile.get_layer_volume(layer_name)
            layer.set_target_volume(target)

    def update(self, delta_time: float, biome_id: int, time_of_day: float = 0.5):
        """
        Update ambient audio.

        Args:
            delta_time: Time since last update
            biome_id: Current biome ID
            time_of_day: Time as 0.0-1.0
        """
        if not self.enabled:
            return

        # Update biome if changed
        self.set_biome(biome_id)

        # Update time-based layers
        self.set_time_of_day(time_of_day)

        # Update all layer volumes
        for layer in self.layers.values():
            layer.update(delta_time)

    def set_master_volume(self, volume: float):
        """
        Set master volume for all ambient audio.

        Args:
            volume: Volume level (0.0-1.0)
        """
        self.master_volume = max(0.0, min(1.0, volume))

    def enable(self):
        """Enable ambient audio."""
        self.enabled = True
        self.start()

    def disable(self):
        """Disable ambient audio."""
        self.enabled = False
        self.stop()


# Global instance
_biome_audio_manager = None


def get_biome_audio_manager() -> BiomeAudioManager:
    """Get or create the global biome audio manager."""
    global _biome_audio_manager
    if _biome_audio_manager is None:
        _biome_audio_manager = BiomeAudioManager()
    return _biome_audio_manager
