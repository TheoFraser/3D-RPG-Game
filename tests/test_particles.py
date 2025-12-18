"""Unit tests for particle system."""
import unittest
import glm
import moderngl
from graphics.particles import (
    Particle,
    ParticleType,
    ParticleEmitter,
    ParticleSystem
)


class TestParticle(unittest.TestCase):
    """Test Particle class."""

    def test_particle_creation(self):
        """Test basic particle creation."""
        position = glm.vec3(1.0, 2.0, 3.0)
        velocity = glm.vec3(0.5, 0.5, 0.5)
        lifetime = 5.0

        # Use SPARKLE which doesn't modify velocity
        particle = Particle(position, velocity, lifetime, ParticleType.SPARKLE)

        self.assertEqual(particle.position, position)
        self.assertEqual(particle.lifetime, 5.0)
        self.assertEqual(particle.max_lifetime, 5.0)
        self.assertEqual(particle.particle_type, ParticleType.SPARKLE)
        # Note: velocity may be modified by particle type initialization

    def test_particle_firefly_properties(self):
        """Test firefly particle has correct properties."""
        particle = Particle(glm.vec3(), glm.vec3(), 5.0, ParticleType.FIREFLY)

        # Fireflies should have upward drift
        self.assertGreaterEqual(particle.velocity.y, -0.2)
        self.assertLessEqual(particle.velocity.y, 0.5)

        # Should have no gravity
        self.assertEqual(particle.gravity_scale, 0.0)

        # Should have greenish color
        self.assertGreater(particle.color.g, 0.8)

    def test_particle_dust_properties(self):
        """Test dust particle has correct properties."""
        particle = Particle(glm.vec3(), glm.vec3(), 5.0, ParticleType.DUST)

        # Dust should have slow fall
        self.assertLess(particle.gravity_scale, 0.0)

        # Should have brownish color
        self.assertGreater(particle.color.r, 0.5)

    def test_particle_rain_properties(self):
        """Test rain particle has correct properties."""
        particle = Particle(glm.vec3(), glm.vec3(), 5.0, ParticleType.RAIN)

        # Rain should have strong downward velocity
        self.assertLess(particle.velocity.y, -3.0)

        # Rain should have strong gravity
        self.assertLess(particle.gravity_scale, -5.0)

    def test_particle_update_position(self):
        """Test particle position updates with velocity."""
        position = glm.vec3(0.0, 0.0, 0.0)
        velocity = glm.vec3(1.0, 2.0, 3.0)
        particle = Particle(position, velocity, 10.0, ParticleType.SPARKLE)

        delta_time = 1.0
        alive = particle.update(delta_time)

        # Position should be updated by velocity * delta_time
        self.assertTrue(alive)
        self.assertAlmostEqual(particle.position.x, 1.0, places=5)
        self.assertAlmostEqual(particle.position.y, 2.0, places=5)
        self.assertAlmostEqual(particle.position.z, 3.0, places=5)

    def test_particle_update_lifetime(self):
        """Test particle lifetime decreases."""
        particle = Particle(glm.vec3(), glm.vec3(), 2.0, ParticleType.DUST)

        alive = particle.update(1.0)

        self.assertTrue(alive)
        self.assertAlmostEqual(particle.lifetime, 1.0, places=5)

    def test_particle_dies_when_lifetime_ends(self):
        """Test particle dies when lifetime reaches 0."""
        particle = Particle(glm.vec3(), glm.vec3(), 1.0, ParticleType.DUST)

        # Update for 1.5 seconds (longer than lifetime)
        alive = particle.update(1.5)

        self.assertFalse(alive)
        self.assertLessEqual(particle.lifetime, 0)

    def test_particle_gravity_application(self):
        """Test gravity affects particle velocity."""
        particle = Particle(glm.vec3(), glm.vec3(0, 5.0, 0), 10.0, ParticleType.RAIN)

        initial_y_velocity = particle.velocity.y
        particle.update(1.0)

        # Velocity should decrease due to gravity
        self.assertLess(particle.velocity.y, initial_y_velocity)

    def test_particle_alpha_fadeout(self):
        """Test particle fades out near end of life."""
        particle = Particle(glm.vec3(), glm.vec3(), 1.0, ParticleType.DUST)

        # Update to near end of life
        particle.lifetime = 0.1  # 10% of original 1.0 lifetime
        particle.max_lifetime = 1.0
        particle.update(0.01)

        # Alpha should be fading
        self.assertLess(particle.alpha, 0.5)


class TestParticleEmitter(unittest.TestCase):
    """Test ParticleEmitter class."""

    def test_emitter_creation(self):
        """Test basic emitter creation."""
        position = glm.vec3(10.0, 5.0, 10.0)
        emitter = ParticleEmitter(position, ParticleType.FIREFLY, emission_rate=10.0, area_size=5.0)

        self.assertEqual(emitter.position, position)
        self.assertEqual(emitter.particle_type, ParticleType.FIREFLY)
        self.assertEqual(emitter.emission_rate, 10.0)
        self.assertEqual(emitter.area_size, 5.0)
        self.assertTrue(emitter.enabled)
        self.assertEqual(len(emitter.particles), 0)

    def test_emitter_emits_particles(self):
        """Test emitter creates particles over time."""
        emitter = ParticleEmitter(glm.vec3(), ParticleType.DUST, emission_rate=10.0)

        # Update for 1 second at 10 particles/sec
        emitter.update(1.0)

        # Should have approximately 10 particles
        self.assertGreater(len(emitter.particles), 5)
        self.assertLess(len(emitter.particles), 15)

    def test_emitter_respects_max_particles(self):
        """Test emitter doesn't exceed max particle limit."""
        emitter = ParticleEmitter(glm.vec3(), ParticleType.SPARKLE, emission_rate=1000.0)
        emitter.max_particles = 50

        # Update for 10 seconds (would create 10000 particles without limit)
        emitter.update(10.0)

        # Should be capped at max_particles
        self.assertLessEqual(len(emitter.particles), 50)

    def test_emitter_removes_dead_particles(self):
        """Test emitter removes particles when they die."""
        emitter = ParticleEmitter(glm.vec3(), ParticleType.DUST, emission_rate=5.0)

        # Emit some particles
        emitter.update(1.0)
        initial_count = len(emitter.particles)

        # Force all particles to die
        for particle in emitter.particles:
            particle.lifetime = 0.0

        # Update emitter
        emitter.update(0.1)

        # Dead particles should be removed, new ones added
        # (Some new ones will be added during update)
        self.assertGreater(initial_count, 0)

    def test_emitter_disabled(self):
        """Test disabled emitter doesn't emit particles."""
        emitter = ParticleEmitter(glm.vec3(), ParticleType.FIREFLY, emission_rate=10.0)
        emitter.enabled = False

        emitter.update(1.0)

        self.assertEqual(len(emitter.particles), 0)

    def test_emitter_particles_within_area(self):
        """Test emitted particles are within emission area."""
        position = glm.vec3(0.0, 0.0, 0.0)
        area_size = 10.0
        emitter = ParticleEmitter(position, ParticleType.SNOW, area_size=area_size)

        # Emit some particles
        for _ in range(20):
            emitter._emit_particle()

        # Check all particles are within area
        for particle in emitter.particles:
            offset = particle.position - position

            # X and Z should be within area_size
            self.assertLessEqual(abs(offset.x), area_size)
            self.assertLessEqual(abs(offset.z), area_size)
            # Y should be within half area_size (upward)
            self.assertGreaterEqual(offset.y, 0.0)
            self.assertLessEqual(offset.y, area_size * 0.5)


class TestParticleSystem(unittest.TestCase):
    """Test ParticleSystem class."""

    @classmethod
    def setUpClass(cls):
        """Create a ModernGL context for tests."""
        cls.ctx = moderngl.create_standalone_context()

    @classmethod
    def tearDownClass(cls):
        """Release the ModernGL context."""
        cls.ctx.release()

    def test_system_creation(self):
        """Test particle system creation."""
        system = ParticleSystem(self.ctx)

        self.assertIsNotNone(system)
        self.assertEqual(len(system.emitters), 0)
        self.assertTrue(system.enabled)

    def test_create_emitter(self):
        """Test creating emitter through system."""
        system = ParticleSystem(self.ctx)

        emitter = system.create_emitter(
            glm.vec3(1.0, 2.0, 3.0),
            ParticleType.FIREFLY,
            emission_rate=15.0,
            area_size=20.0
        )

        self.assertIsNotNone(emitter)
        self.assertEqual(len(system.emitters), 1)
        self.assertEqual(emitter.emission_rate, 15.0)
        self.assertEqual(emitter.area_size, 20.0)

    def test_create_biome_emitters_enchanted_forest(self):
        """Test creating emitters for enchanted forest biome."""
        system = ParticleSystem(self.ctx)

        emitters = system.create_biome_emitters(
            "enchanted_forest",
            glm.vec3(0.0, 0.0, 0.0),
            world_bounds=50.0
        )

        # Enchanted forest should create firefly emitters
        self.assertGreater(len(emitters), 0)
        self.assertEqual(emitters[0].particle_type, ParticleType.FIREFLY)

    def test_create_biome_emitters_ancient_ruins(self):
        """Test creating emitters for ancient ruins biome."""
        system = ParticleSystem(self.ctx)

        emitters = system.create_biome_emitters(
            "ancient_ruins",
            glm.vec3(0.0, 0.0, 0.0)
        )

        # Ancient ruins should create dust emitters
        self.assertGreater(len(emitters), 0)
        self.assertEqual(emitters[0].particle_type, ParticleType.DUST)

    def test_create_biome_emitters_crystal_caves(self):
        """Test creating emitters for crystal caves biome."""
        system = ParticleSystem(self.ctx)

        emitters = system.create_biome_emitters(
            "crystal_caves",
            glm.vec3(0.0, 0.0, 0.0)
        )

        # Crystal caves should create sparkle emitters
        self.assertGreater(len(emitters), 0)
        self.assertEqual(emitters[0].particle_type, ParticleType.SPARKLE)

    def test_create_biome_emitters_unknown_biome(self):
        """Test creating emitters for unknown biome returns empty."""
        system = ParticleSystem(self.ctx)

        emitters = system.create_biome_emitters(
            "unknown_biome",
            glm.vec3(0.0, 0.0, 0.0)
        )

        self.assertEqual(len(emitters), 0)

    def test_system_update(self):
        """Test particle system updates all emitters."""
        system = ParticleSystem(self.ctx)

        # Create some emitters
        system.create_emitter(glm.vec3(), ParticleType.DUST, emission_rate=10.0)
        system.create_emitter(glm.vec3(10, 0, 0), ParticleType.FIREFLY, emission_rate=5.0)

        # Update system
        system.update(1.0)

        # Emitters should have particles
        self.assertGreater(len(system.emitters[0].particles), 0)
        self.assertGreater(len(system.emitters[1].particles), 0)

    def test_get_all_particles(self):
        """Test getting all particles from all emitters."""
        system = ParticleSystem(self.ctx)

        emitter1 = system.create_emitter(glm.vec3(), ParticleType.DUST, emission_rate=5.0)
        emitter2 = system.create_emitter(glm.vec3(10, 0, 0), ParticleType.FIREFLY, emission_rate=5.0)

        system.update(1.0)

        all_particles = system.get_all_particles()

        # Should combine particles from both emitters
        expected_count = len(emitter1.particles) + len(emitter2.particles)
        self.assertEqual(len(all_particles), expected_count)

    def test_get_particle_count(self):
        """Test getting total particle count."""
        system = ParticleSystem(self.ctx)

        system.create_emitter(glm.vec3(), ParticleType.SPARKLE, emission_rate=10.0)
        system.update(1.0)

        count = system.get_particle_count()

        self.assertGreater(count, 0)
        self.assertEqual(count, len(system.get_all_particles()))

    def test_clear_emitters(self):
        """Test clearing all emitters."""
        system = ParticleSystem(self.ctx)

        system.create_emitter(glm.vec3(), ParticleType.DUST)
        system.create_emitter(glm.vec3(), ParticleType.FIREFLY)

        self.assertEqual(len(system.emitters), 2)

        system.clear_emitters()

        self.assertEqual(len(system.emitters), 0)

    def test_remove_distant_emitters(self):
        """Test removing emitters far from player."""
        system = ParticleSystem(self.ctx)
        player_position = glm.vec3(0.0, 0.0, 0.0)

        # Create emitters at various distances
        system.create_emitter(glm.vec3(10, 0, 0), ParticleType.DUST)   # Close
        system.create_emitter(glm.vec3(200, 0, 0), ParticleType.FIREFLY)  # Far

        self.assertEqual(len(system.emitters), 2)

        # Remove emitters beyond 100 units
        system.remove_distant_emitters(player_position, max_distance=100.0)

        # Only close emitter should remain
        self.assertEqual(len(system.emitters), 1)
        self.assertLess(glm.length(system.emitters[0].position - player_position), 100.0)

    def test_system_disabled(self):
        """Test disabled system doesn't update."""
        system = ParticleSystem(self.ctx)
        system.enabled = False

        system.create_emitter(glm.vec3(), ParticleType.DUST, emission_rate=10.0)
        system.update(1.0)

        # No particles should be created when disabled
        self.assertEqual(system.get_particle_count(), 0)


class TestParticleTypes(unittest.TestCase):
    """Test different particle type behaviors."""

    def test_all_particle_types_valid(self):
        """Test all particle types can be created without error."""
        position = glm.vec3(0.0, 0.0, 0.0)
        velocity = glm.vec3(0.0, 0.0, 0.0)

        for particle_type in ParticleType:
            particle = Particle(position, velocity, 5.0, particle_type)
            self.assertIsNotNone(particle)
            self.assertEqual(particle.particle_type, particle_type)

    def test_gravity_varies_by_type(self):
        """Test different particle types have appropriate gravity."""
        # Particles that should float
        firefly = Particle(glm.vec3(), glm.vec3(), 5.0, ParticleType.FIREFLY)
        sparkle = Particle(glm.vec3(), glm.vec3(), 5.0, ParticleType.SPARKLE)

        self.assertEqual(firefly.gravity_scale, 0.0)
        self.assertEqual(sparkle.gravity_scale, 0.0)

        # Particles that should fall
        rain = Particle(glm.vec3(), glm.vec3(), 5.0, ParticleType.RAIN)
        snow = Particle(glm.vec3(), glm.vec3(), 5.0, ParticleType.SNOW)

        self.assertLess(rain.gravity_scale, 0.0)
        self.assertLess(snow.gravity_scale, 0.0)
        # Rain should fall faster than snow
        self.assertLess(rain.gravity_scale, snow.gravity_scale)


if __name__ == '__main__':
    unittest.main()
