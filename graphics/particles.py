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
    # Spell effect particles
    MAGIC_TRAIL = auto()       # Arcane magic trail
    FIRE_TRAIL = auto()        # Fire spell trail
    ICE_TRAIL = auto()         # Ice spell trail
    LIGHTNING_SPARK = auto()   # Lightning sparks
    HOLY_LIGHT = auto()        # Healing/holy light
    SPELL_IMPACT = auto()      # Generic spell impact explosion
    # Player progression effects
    LEVEL_UP = auto()          # Level-up celebration burst


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

        # Spell particle types
        elif self.particle_type == ParticleType.MAGIC_TRAIL:
            self.size = 0.06 + random.random() * 0.04
            self.color = glm.vec3(0.6 + random.random() * 0.2, 0.4 + random.random() * 0.2, 1.0)
            self.gravity_scale = 0.0
            # Slow drift
            self.velocity *= 0.3

        elif self.particle_type == ParticleType.FIRE_TRAIL:
            self.size = 0.07 + random.random() * 0.05
            # Orange to red
            self.color = glm.vec3(1.0, 0.5 + random.random() * 0.3, 0.1 + random.random() * 0.1)
            self.gravity_scale = 0.2  # Slight upward drift
            self.velocity.y += random.uniform(0.2, 0.5)

        elif self.particle_type == ParticleType.ICE_TRAIL:
            self.size = 0.05 + random.random() * 0.03
            # Light blue to white
            self.color = glm.vec3(0.7 + random.random() * 0.3, 0.9 + random.random() * 0.1, 1.0)
            self.gravity_scale = -0.2  # Slow fall
            self.velocity *= 0.2

        elif self.particle_type == ParticleType.LIGHTNING_SPARK:
            self.size = 0.04 + random.random() * 0.03
            # Bright yellow-white
            self.color = glm.vec3(1.0, 1.0, 0.8 + random.random() * 0.2)
            self.gravity_scale = 0.0
            # Rapid random movement
            self.velocity = glm.vec3(
                random.uniform(-2.0, 2.0),
                random.uniform(-2.0, 2.0),
                random.uniform(-2.0, 2.0)
            )

        elif self.particle_type == ParticleType.HOLY_LIGHT:
            self.size = 0.08 + random.random() * 0.06
            # Warm golden light
            self.color = glm.vec3(1.0, 0.9 + random.random() * 0.1, 0.6 + random.random() * 0.2)
            self.gravity_scale = 0.3  # Float upward
            self.velocity.y += random.uniform(0.5, 1.0)

        elif self.particle_type == ParticleType.SPELL_IMPACT:
            self.size = 0.1 + random.random() * 0.1
            # Bright flash
            self.color = glm.vec3(1.0, 1.0, 1.0)
            self.gravity_scale = 0.0
            # Explosive outward velocity
            speed = random.uniform(1.0, 3.0)
            direction = glm.normalize(glm.vec3(
                random.uniform(-1.0, 1.0),
                random.uniform(-1.0, 1.0),
                random.uniform(-1.0, 1.0)
            ))
            self.velocity = direction * speed

        elif self.particle_type == ParticleType.LEVEL_UP:
            self.size = 0.15 + random.random() * 0.1
            # Golden celebration particles with color variation
            gold_variation = random.random() * 0.3
            self.color = glm.vec3(1.0, 0.8 + gold_variation, gold_variation)
            self.gravity_scale = -0.5  # Float upward
            # Radial burst with upward bias
            horizontal_speed = random.uniform(1.0, 2.5)
            vertical_speed = random.uniform(2.0, 4.0)
            angle = random.uniform(0, 2 * 3.14159)
            self.velocity = glm.vec3(
                horizontal_speed * glm.cos(angle),
                vertical_speed,
                horizontal_speed * glm.sin(angle)
            )

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
        # Always update existing particles (even when emitter is disabled)
        self.particles = [p for p in self.particles if p.update(delta_time)]

        # Only emit new particles when emitter is enabled
        if not self.enabled:
            return

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
            # Spell particles (shorter lifetimes for performance)
            ParticleType.MAGIC_TRAIL: (0.3, 0.6),
            ParticleType.FIRE_TRAIL: (0.4, 0.8),
            ParticleType.ICE_TRAIL: (0.5, 1.0),
            ParticleType.LIGHTNING_SPARK: (0.1, 0.3),
            ParticleType.HOLY_LIGHT: (0.8, 1.5),
            ParticleType.SPELL_IMPACT: (0.2, 0.5),
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

    def create_spell_burst(self, position: glm.vec3, particle_type: ParticleType,
                          particle_count: int = 15):
        """
        Create a one-time particle burst for spell effects.

        Args:
            position: Position to spawn particles
            particle_type: Type of particles
            particle_count: Number of particles to spawn
        """
        for _ in range(particle_count):
            # Random velocity in all directions
            vel = glm.vec3(
                random.uniform(-1.5, 1.5),
                random.uniform(-1.5, 1.5),
                random.uniform(-1.5, 1.5)
            )

            # Get lifetime range
            lifetime_ranges = {
                ParticleType.MAGIC_TRAIL: (0.3, 0.6),
                ParticleType.FIRE_TRAIL: (0.4, 0.8),
                ParticleType.ICE_TRAIL: (0.5, 1.0),
                ParticleType.LIGHTNING_SPARK: (0.1, 0.3),
                ParticleType.HOLY_LIGHT: (0.8, 1.5),
                ParticleType.SPELL_IMPACT: (0.2, 0.5),
                ParticleType.LEVEL_UP: (1.0, 2.0),
            }
            lifetime = random.uniform(*lifetime_ranges.get(particle_type, (0.3, 0.8)))

            # Create particle directly (not through an emitter for one-time bursts)
            particle = Particle(glm.vec3(position), vel, lifetime, particle_type)

            # Add to a temporary emitter or create a burst emitter
            # Find or create a burst emitter
            burst_emitter = None
            for emitter in self.emitters:
                if (hasattr(emitter, 'is_burst') and emitter.is_burst and
                    glm.length(emitter.position - position) < 0.1):
                    burst_emitter = emitter
                    break

            if burst_emitter is None:
                # Create a disabled emitter just to hold burst particles
                burst_emitter = ParticleEmitter(position, particle_type,
                                               emission_rate=0.0, area_size=0.0)
                burst_emitter.enabled = False
                burst_emitter.is_burst = True
                self.emitters.append(burst_emitter)

            burst_emitter.particles.append(particle)

    def create_spell_trail_particle(self, position: glm.vec3, particle_type: ParticleType):
        """
        Create a single trail particle for continuous spell effects.

        Args:
            position: Position to spawn particle
            particle_type: Type of particle
        """
        vel = glm.vec3(
            random.uniform(-0.3, 0.3),
            random.uniform(-0.3, 0.3),
            random.uniform(-0.3, 0.3)
        )

        lifetime_ranges = {
            ParticleType.MAGIC_TRAIL: (0.3, 0.6),
            ParticleType.FIRE_TRAIL: (0.4, 0.8),
            ParticleType.ICE_TRAIL: (0.5, 1.0),
        }
        lifetime = random.uniform(*lifetime_ranges.get(particle_type, (0.3, 0.6)))

        particle = Particle(glm.vec3(position), vel, lifetime, particle_type)

        # Find or create trail emitter
        trail_emitter = None
        for emitter in self.emitters:
            if hasattr(emitter, 'is_trail') and emitter.is_trail:
                trail_emitter = emitter
                break

        if trail_emitter is None:
            trail_emitter = ParticleEmitter(position, particle_type,
                                           emission_rate=0.0, area_size=0.0)
            trail_emitter.enabled = False
            trail_emitter.is_trail = True
            self.emitters.append(trail_emitter)

        trail_emitter.particles.append(particle)

    def render(self, view_matrix, projection_matrix, mesh=None):
        """
        Render all particles.

        Args:
            view_matrix: Camera view matrix
            projection_matrix: Camera projection matrix
            mesh: Optional mesh to use for particle rendering
        """
        if not self.enabled:
            return

        all_particles = self.get_all_particles()
        if not all_particles:
            return

        # Render particles as small cubes/points
        # For now, particles are rendered by the main game loop
        # This method can be extended for custom particle rendering
        pass
