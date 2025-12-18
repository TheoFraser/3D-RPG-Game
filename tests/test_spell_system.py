"""Tests for the spell casting system."""
import unittest
import glm
from game.spell_system import (
    SpellType, SpellElement, StatusEffect, SpellCaster,
    SpellManager, SPELL_DEFINITIONS, SpellProjectile
)
from game.player import Player
from game.enemy import Enemy, EnemyType


class TestSpellDefinitions(unittest.TestCase):
    """Test spell definitions and stats."""

    def test_all_spell_types_have_definitions(self):
        """Verify all spell types have definitions."""
        for spell_type in SpellType:
            self.assertIn(spell_type, SPELL_DEFINITIONS,
                         f"Spell type {spell_type.name} missing definition")

    def test_spell_damage_scaling(self):
        """Test spell damage scales with level."""
        fireball = SPELL_DEFINITIONS[SpellType.FIREBALL]
        base_damage = fireball.stats.damage

        # Level 1 spell
        self.assertEqual(fireball.get_damage(), base_damage)

        # Level 5 spell (should be 1.8x base damage)
        fireball.level = 5
        expected_damage = base_damage * (1.0 + (5 - 1) * 0.2)
        self.assertAlmostEqual(fireball.get_damage(), expected_damage)

    def test_healing_spell_stats(self):
        """Test healing spell has correct stats."""
        heal = SPELL_DEFINITIONS[SpellType.HEAL]
        self.assertEqual(heal.element, SpellElement.HOLY)
        self.assertGreater(heal.stats.healing, 0)
        self.assertTrue(heal.is_self_target)
        self.assertTrue(heal.is_instant)

    def test_projectile_spell_has_speed(self):
        """Test projectile spells have projectile speed."""
        fireball = SPELL_DEFINITIONS[SpellType.FIREBALL]
        self.assertTrue(fireball.is_projectile)
        self.assertGreater(fireball.stats.projectile_speed, 0)
        self.assertGreater(fireball.stats.range, 0)


class TestSpellCaster(unittest.TestCase):
    """Test spell caster mechanics."""

    def setUp(self):
        """Set up test spell caster."""
        self.caster = SpellCaster(max_mana=100.0)

    def test_initial_mana_is_full(self):
        """Test spell caster starts with full mana."""
        self.assertEqual(self.caster.current_mana, self.caster.max_mana)
        self.assertEqual(self.caster.max_mana, 100.0)

    def test_add_known_spell(self):
        """Test adding spells to known spells."""
        self.caster.add_known_spell(SpellType.FIREBALL)
        self.assertEqual(len(self.caster.known_spells), 1)
        self.assertEqual(self.caster.known_spells[0].spell_type, SpellType.FIREBALL)

    def test_equip_spell_to_slot(self):
        """Test equipping spell to quick slot."""
        self.caster.add_known_spell(SpellType.FIREBALL)
        success = self.caster.equip_spell(SpellType.FIREBALL, 0)

        self.assertTrue(success)
        self.assertIsNotNone(self.caster.equipped_spells[0])
        self.assertEqual(self.caster.equipped_spells[0].spell_type, SpellType.FIREBALL)

    def test_cannot_equip_unknown_spell(self):
        """Test cannot equip spell that isn't known."""
        success = self.caster.equip_spell(SpellType.METEOR, 0)
        self.assertFalse(success)
        self.assertIsNone(self.caster.equipped_spells[0])

    def test_casting_consumes_mana(self):
        """Test casting spell consumes mana."""
        self.caster.add_known_spell(SpellType.MAGIC_MISSILE)
        spell = SPELL_DEFINITIONS[SpellType.MAGIC_MISSILE]

        initial_mana = self.caster.current_mana
        mana_cost = spell.get_mana_cost()

        success = self.caster.start_cast(spell)
        self.assertTrue(success)
        self.assertEqual(self.caster.current_mana, initial_mana - mana_cost)

    def test_cannot_cast_without_mana(self):
        """Test cannot cast spell without enough mana."""
        self.caster.current_mana = 5.0  # Not enough for most spells
        self.caster.add_known_spell(SpellType.FIREBALL)
        spell = SPELL_DEFINITIONS[SpellType.FIREBALL]

        success = self.caster.start_cast(spell)
        self.assertFalse(success)

    def test_instant_spell_completes_immediately(self):
        """Test instant cast spells complete immediately."""
        self.caster.add_known_spell(SpellType.HEAL)
        spell = SPELL_DEFINITIONS[SpellType.HEAL]

        self.caster.start_cast(spell)
        # Instant spells complete immediately
        self.assertFalse(self.caster.is_casting)

    def test_spell_cooldown_applied(self):
        """Test spell goes on cooldown after casting."""
        self.caster.add_known_spell(SpellType.HEAL)
        spell = SPELL_DEFINITIONS[SpellType.HEAL]

        # Cast instant spell (it completes immediately and sets cooldown)
        self.caster.start_cast(spell)

        # Cooldown should be set after instant cast completes
        self.assertIn(SpellType.HEAL, self.caster.spell_cooldowns)
        self.assertGreater(self.caster.spell_cooldowns[SpellType.HEAL], 0)

    def test_cannot_cast_on_cooldown(self):
        """Test cannot cast spell while on cooldown."""
        self.caster.add_known_spell(SpellType.HEAL)
        spell = SPELL_DEFINITIONS[SpellType.HEAL]

        # Cast instant spell once (completes immediately)
        self.caster.start_cast(spell)

        # Spell should now be on cooldown
        self.assertIn(SpellType.HEAL, self.caster.spell_cooldowns)

        # Try to cast again immediately
        can_cast, reason = self.caster.can_cast_spell(spell)

        self.assertFalse(can_cast)
        self.assertIn("cooldown", reason.lower())

    def test_mana_regenerates_over_time(self):
        """Test mana regenerates over time."""
        self.caster.current_mana = 50.0
        initial_mana = self.caster.current_mana

        # Update for 1 second
        self.caster.update(1.0)

        # Mana should have regenerated
        self.assertGreater(self.caster.current_mana, initial_mana)
        expected_mana = min(100.0, initial_mana + self.caster.mana_regen_rate * 1.0)
        self.assertAlmostEqual(self.caster.current_mana, expected_mana)

    def test_mana_does_not_exceed_max(self):
        """Test mana does not regenerate above max."""
        self.caster.current_mana = 95.0

        # Regenerate for 10 seconds (would give 100 mana)
        self.caster.update(10.0)

        # Should cap at max mana
        self.assertEqual(self.caster.current_mana, self.caster.max_mana)

    def test_status_effect_application(self):
        """Test status effects can be applied."""
        self.caster.add_status_effect(StatusEffect.BURNING, duration=5.0, intensity=1.0)

        self.assertTrue(self.caster.has_status_effect(StatusEffect.BURNING))
        self.assertEqual(self.caster.get_status_effect_multiplier(StatusEffect.BURNING), 1.0)

    def test_status_effect_expires(self):
        """Test status effects expire after duration."""
        self.caster.add_status_effect(StatusEffect.FROZEN, duration=1.0)

        # Update for 1.5 seconds
        self.caster.update(1.5)

        # Effect should have expired
        self.assertFalse(self.caster.has_status_effect(StatusEffect.FROZEN))


class TestSpellProjectile(unittest.TestCase):
    """Test spell projectile mechanics."""

    def test_projectile_moves_over_time(self):
        """Test projectile moves in direction."""
        spell = SPELL_DEFINITIONS[SpellType.FIREBALL]
        position = glm.vec3(0, 0, 0)
        direction = glm.vec3(1, 0, 0)

        projectile = SpellProjectile(
            spell=spell,
            position=position,
            direction=direction,
            caster_id=1
        )

        # Update for 1 second
        projectile.update(1.0)

        # Projectile should have moved
        expected_distance = spell.stats.projectile_speed * 1.0
        self.assertAlmostEqual(projectile.position.x, expected_distance, places=1)

    def test_projectile_expires_after_lifetime(self):
        """Test projectile expires after max lifetime."""
        spell = SPELL_DEFINITIONS[SpellType.MAGIC_MISSILE]
        projectile = SpellProjectile(
            spell=spell,
            position=glm.vec3(0, 0, 0),
            direction=glm.vec3(1, 0, 0),
            caster_id=1,
            max_lifetime=1.0
        )

        # Update past max lifetime
        is_active = projectile.update(1.5)

        self.assertFalse(is_active)

    def test_projectile_collision_detection(self):
        """Test projectile detects collision with target."""
        spell = SPELL_DEFINITIONS[SpellType.ICE_SHARD]
        projectile = SpellProjectile(
            spell=spell,
            position=glm.vec3(5, 0, 0),
            direction=glm.vec3(1, 0, 0),
            caster_id=1
        )

        # Target at same position
        target_position = glm.vec3(5.5, 0, 0)

        # Should detect collision
        hit = projectile.check_collision(target_position, target_radius=1.0)
        self.assertTrue(hit)

    def test_projectile_no_collision_when_far(self):
        """Test projectile doesn't collide with distant targets."""
        spell = SPELL_DEFINITIONS[SpellType.FIREBALL]
        projectile = SpellProjectile(
            spell=spell,
            position=glm.vec3(0, 0, 0),
            direction=glm.vec3(1, 0, 0),
            caster_id=1
        )

        # Target far away
        target_position = glm.vec3(100, 0, 0)

        hit = projectile.check_collision(target_position, target_radius=1.0)
        self.assertFalse(hit)


class TestSpellManager(unittest.TestCase):
    """Test spell manager system."""

    def test_create_projectile_spell(self):
        """Test creating projectile spell."""
        manager = SpellManager()
        spell = SPELL_DEFINITIONS[SpellType.FIREBALL]

        projectile = manager.cast_projectile_spell(
            spell=spell,
            position=glm.vec3(0, 0, 0),
            direction=glm.vec3(1, 0, 0),
            caster_id=1
        )

        self.assertIsNotNone(projectile)
        self.assertEqual(len(manager.active_projectiles), 1)
        self.assertEqual(manager.active_projectiles[0], projectile)

    def test_projectiles_update(self):
        """Test all projectiles update."""
        manager = SpellManager()
        spell = SPELL_DEFINITIONS[SpellType.MAGIC_MISSILE]

        # Create multiple projectiles
        for i in range(3):
            manager.cast_projectile_spell(
                spell=spell,
                position=glm.vec3(i * 10, 0, 0),
                direction=glm.vec3(1, 0, 0),
                caster_id=1
            )

        self.assertEqual(len(manager.active_projectiles), 3)

        # Update manager
        manager.update(0.1)

        # All projectiles should still be active
        self.assertEqual(len(manager.active_projectiles), 3)

    def test_expired_projectiles_removed(self):
        """Test expired projectiles are removed."""
        manager = SpellManager()
        spell = SPELL_DEFINITIONS[SpellType.FIREBALL]  # Use FIREBALL instead of LIGHTNING

        projectile = manager.cast_projectile_spell(
            spell=spell,
            position=glm.vec3(0, 0, 0),
            direction=glm.vec3(1, 0, 0),
            caster_id=1
        )
        projectile.max_lifetime = 0.5

        # Update past lifetime
        manager.update(1.0)

        # Projectile should be removed
        self.assertEqual(len(manager.active_projectiles), 0)


class TestPlayerSpellIntegration(unittest.TestCase):
    """Test spell system integration with player."""

    def test_player_has_spell_caster(self):
        """Test player has spell caster."""
        player = Player(position=glm.vec3(0, 0, 0))
        self.assertIsNotNone(player.spell_caster)
        self.assertIsInstance(player.spell_caster, SpellCaster)

    def test_player_starts_with_spells(self):
        """Test player starts with basic spells."""
        player = Player(position=glm.vec3(0, 0, 0))

        # Should have Magic Missile and Heal
        self.assertGreater(len(player.spell_caster.known_spells), 0)
        self.assertGreater(len(player.spell_caster.equipped_spells), 0)

    def test_player_can_cast_spell(self):
        """Test player can cast spell from slot."""
        player = Player(position=glm.vec3(0, 0, 0))
        spell_manager = SpellManager()

        # Cast spell from slot 0 (Magic Missile)
        success = player.cast_spell(0, spell_manager)

        # Should succeed if player has mana
        if player.spell_caster.current_mana >= 15:  # Magic Missile cost
            self.assertTrue(success)

    def test_player_cannot_cast_from_empty_slot(self):
        """Test player cannot cast from empty spell slot."""
        player = Player(position=glm.vec3(0, 0, 0))
        spell_manager = SpellManager()

        # Clear slot 5
        player.spell_caster.equipped_spells[5] = None

        # Try to cast from empty slot
        success = player.cast_spell(5, spell_manager)
        self.assertFalse(success)


if __name__ == '__main__':
    unittest.main()
