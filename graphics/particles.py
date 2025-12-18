"""Particle system for environmental and combat effects."""
import glm
import random
import moderngl
from typing import List, Optional
from enum import Enum, auto
import numpy as np


class ParticleType(Enum):
    """Types of particle effects."""
    FIREFLY = auto()           # Glowing particles for enchanted forest
    DUST = auto()              # Floating dust for ruins/caves
    SPARKLE = auto()           # Magical sparkles
    SNOW = auto()              # Snow particles
    RAIN = auto()              # Rain drops
    EMBERS = auto()            # Fire embers
    LEAVES = auto()            # Falling leaves


class Particle:
    """Individual particle instance."""

    def __init__(self, position: glm.vec3, velocity: glm.vec3, lifetime: float,
                 particle_type: ParticleType):
        """
        Initialize particle.

        Args:
            position: Starting position
            velocity: Initial velocity
            lifetime: How long particle lives (seconds)
            particle_type: Type of particle
        """
        self.position = glm.vec3(position)
        self.velocity = glm.vec3(velocity)
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.particle_type = particle_type
        self.size = 0.1
        self.color = glm.vec3(1.0, 1.0, 1.0)
        self.alpha = 1.0
        self.gravity_scale = 0.0

        # Type-specific initialization
        self._init_by_type()

    def _init_by_type(self):
        """Initialize particle properties based on type."""
        if self.particle_type == ParticleType.FIREFLY:
            self.size = 0.05 + random.random() * 0.05
            self.color = glm.vec3(0.8 + random.random() * 0.2, 1.0, 0.5 + random.random() * 0.3)
            self.gravity_scale = 0.0
            # Fireflies drift gently
            self.velocity.y = random.uniform(-0.2, 0.5)

        elif self.particle_type == ParticleType.DUST:
            self.size = 0.02 + random.random() * 0.03
            self.color = glm.vec3(0.8, 0.7, 0.6)
            self.gravity_scale = -0.1  # Very slow fall
            self.velocity.y = random.uniform(-0.1, 0.3)

        elif self.particle_type == ParticleType.SPARKLE:
            self.size = 0.03 + random.random() * 0.04
            colors = [
                glm.vec3(1.0, 0.8, 0.3),  # Gold
                glm.vec3(0.5, 0.8, 1.0),  # Blue
                glm.vec3(1.0, 0.5, 1.0),  # Purple
            ]
            self.color = random.choice(colors)
            self.gravity_scale = 0.0

        elif self.particle_type == ParticleType.SNOW:
            self.size = 0.03 + random.random() * 0.03
            self.color = glm.vec3(1.0, 1.0, 1.0)
            self.gravity_scale = -0.5
            self.velocity.y = random.uniform(-0.5, -0.2)

        elif self.particle_type == ParticleType.RAIN:
            self.size = 0.02
            self.color = glm.vec3(0.6, 0.7, 0.8)
            self.gravity_scale = -8.0
            self.velocity.y = random.uniform(-5.0, -3.0)

        elif self.particle_type == ParticleType.EMBERS:
            self.size = 0.04 + random.random() * 0.04
            self.color = glm.vec3(1.0, 0.4 + random.random() * 0.3, 0.1)
            self.gravity_scale = 0.0
            self.velocity.y = random.uniform(0.5, 1.5)

        elif self.particle_type == ParticleType.LEAVES:
            self.size = 0.08 + random.random() * 0.08
            self.color = glm.vec3(0.8 + random.random() * 0.2, 0.5, 0.2)
            self.gravity_scale = -0.3
            self.velocity.y = random.uniform(-0.5, -0.2)

    def update(self, delta_time: float) -> bool:
        """
        Update particle.

        Args:
            delta_time: Time since last frame

        Returns:
            True if particle is still alive, False otherwise
        """
        # Update lifetime
        self.lifetime -= delta_time
        if self.lifetime <= 0:
            return False

        # Apply velocity
        self.position += self.velocity * delta_time

        # Apply gravity
        if self.gravity_scale != 0.0:
            self.velocity.y += self.gravity_scale * delta_time

        # Update alpha based on lifetime
        life_ratio = self.lifetime / self.max_lifetime
        if life_ratio < 0.2:
            # Fade out
            self.alpha = life_ratio * 5.0
        else:
            self.alpha = 1.0

        # Type-specific updates
        if self.particle_type == ParticleType.FIREFLY:
            # Pulsing glow
            pulse = (1.0 + glm.sin(self.lifetime * 5.0)) * 0.5
            self.alpha = 0.5 + pulse * 0.5

        return True


class ParticleEmitter:
    """Emits particles in a specific area."""

    def __init__(self, position: glm.vec3, particle_type: ParticleType,
                 emission_rate: float = 10.0, area_size: float = 10.0):
        """
        Initialize particle emitter.

        Args:
            position: Center position of emitter
            particle_type: Type of particles to emit
            emission_rate: Particles per second
            area_size: Size of emission area
        """
        self.position = glm.vec3(position)
        self.particle_type = particle_type
        self.emission_rate = emission_rate
        self.area_size = area_size
        self.particles: List[Particle] = []
        self.time_accumulator = 0.0
        self.enabled = True
        self.max_particles = 200  # Performance limit

    def update(self, delta_time: float):
        """Update emitter and all its particles."""
        if not self.enabled:
            return

        # Update existing particles
        self.particles = [p for p in self.particles if p.update(delta_time)]

        # Emit new particles
        if len(self.particles) < self.max_particles:
            self.time_accumulator += delta_time
            particles_to_emit = int(self.time_accumulator * self.emission_rate)

            if particles_to_emit > 0:
                self.time_accumulator -= particles_to_emit / self.emission_rate

                for _ in range(particles_to_emit):
                    if len(self.particles) >= self.max_particles:
                        break
                    self._emit_particle()

    def _emit_particle(self):
        """Emit a single particle."""
        # Random position within emission area
        offset = glm.vec3(
            random.uniform(-self.area_size, self.area_size),
            random.uniform(0, self.area_size * 0.5),
            random.uniform(-self.area_size, self.area_size)
        )
        pos = self.position + offset

        # Random velocity
        vel = glm.vec3(
            random.uniform(-0.5, 0.5),
            random.uniform(-0.5, 0.5),
            random.uniform(-0.5, 0.5)
        )

        # Lifetime based on particle type
        lifetime_ranges = {
            ParticleType.FIREFLY: (3.0, 6.0),
            ParticleType.DUST: (4.0, 8.0),
            ParticleType.SPARKLE: (1.0, 2.0),
            ParticleType.SNOW: (10.0, 15.0),
            ParticleType.RAIN: (2.0, 3.0),
            ParticleType.EMBERS: (2.0, 4.0),
            ParticleType.LEAVES: (5.0, 10.0),
        }
        lifetime = random.uniform(*lifetime_ranges.get(self.particle_type, (2.0, 4.0)))

        particle = Particle(pos, vel, lifetime, self.particle_type)
        self.particles.append(particle)


class ParticleSystem:
    """Manages all particle emitters and rendering."""

    def __init__(self, ctx: moderngl.Context):
        """
        Initialize particle system.

        Args:
            ctx: ModernGL context
        """
        self.ctx = ctx
        self.emitters: List[ParticleEmitter] = []
        self.enabled = True

    def create_emitter(self, position: glm.vec3, particle_type: ParticleType,
                      emission_rate: float = 10.0, area_size: float = 10.0) -> ParticleEmitter:
        """
        Create a new particle emitter.

        Args:
            position: Emitter position
            particle_type: Type of particles
            emission_rate: Particles per second
            area_size: Size of emission area

        Returns:
            Created emitter
        """
        emitter = ParticleEmitter(position, particle_type, emission_rate, area_size)
        self.emitters.append(emitter)
        return emitter

    def create_biome_emitters(self, biome_name: str, player_position: glm.vec3,
                             world_bounds: float = 50.0) -> List[ParticleEmitter]:
        """
        Create particle emitters appropriate for a biome.

        Args:
            biome_name: Name of the biome
            player_position: Player's current position
            world_bounds: Distance around player to place emitters

        Returns:
            List of created emitters
        """
        created = []

        if biome_name == "enchanted_forest":
            # Fireflies scattered around
            for _ in range(3):
                pos = player_position + glm.vec3(
                    random.uniform(-world_bounds, world_bounds),
                    random.uniform(1.0, 3.0),
                    random.uniform(-world_bounds, world_bounds)
                )
                emitter = self.create_emitter(pos, ParticleType.FIREFLY,
                                             emission_rate=5.0, area_size=15.0)
                created.append(emitter)

        elif biome_name == "ancient_ruins":
            # Dust particles
            for _ in range(2):
                pos = player_position + glm.vec3(
                    random.uniform(-world_bounds, world_bounds),
                    random.uniform(2.0, 5.0),
                    random.uniform(-world_bounds, world_bounds)
                )
                emitter = self.create_emitter(pos, ParticleType.DUST,
                                             emission_rate=8.0, area_size=20.0)
                created.append(emitter)

        elif biome_name == "crystal_caves":
            # Magical sparkles
            for _ in range(2):
                pos = player_position + glm.vec3(
                    random.uniform(-world_bounds, world_bounds),
                    random.uniform(1.0, 4.0),
                    random.uniform(-world_bounds, world_bounds)
                )
                emitter = self.create_emitter(pos, ParticleType.SPARKLE,
                                             emission_rate=15.0, area_size=10.0)
                created.append(emitter)

        return created

    def update(self, delta_time: float):
        """Update all particle emitters."""
        if not self.enabled:
            return

        for emitter in self.emitters:
            emitter.update(delta_time)

    def get_all_particles(self) -> List[Particle]:
        """Get all active particles from all emitters."""
        all_particles = []
        for emitter in self.emitters:
            all_particles.extend(emitter.particles)
        return all_particles

    def get_particle_count(self) -> int:
        """Get total number of active particles."""
        return sum(len(emitter.particles) for emitter in self.emitters)

    def clear_emitters(self):
        """Remove all emitters."""
        self.emitters.clear()

    def remove_distant_emitters(self, player_position: glm.vec3, max_distance: float = 100.0):
        """Remove emitters far from player to manage performance."""
        self.emitters = [
            e for e in self.emitters
            if glm.length(e.position - player_position) <= max_distance
        ]
