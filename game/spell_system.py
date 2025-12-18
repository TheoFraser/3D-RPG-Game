"""Magic spell system for the RPG."""
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Callable, List
import glm
from game.logger import get_logger

logger = get_logger(__name__)


def get_spell_particle_type(element: 'SpellElement') -> str:
    """
    Get the particle type name for a spell element.

    Args:
        element: Spell element

    Returns:
        Particle type name string
    """
    from graphics.particles import ParticleType

    particle_map = {
        'FIRE': ParticleType.FIRE_TRAIL,
        'ICE': ParticleType.ICE_TRAIL,
        'LIGHTNING': ParticleType.LIGHTNING_SPARK,
        'ARCANE': ParticleType.MAGIC_TRAIL,
        'NATURE': ParticleType.SPARKLE,  # Use sparkle for nature
        'HOLY': ParticleType.HOLY_LIGHT,
    }

    return particle_map.get(element.name, ParticleType.MAGIC_TRAIL)


def get_spell_color(element: 'SpellElement') -> 'glm.vec3':
    """
    Get the RGB color for a spell element.

    Args:
        element: Spell element

    Returns:
        glm.vec3 RGB color (0.0 to 1.0 range)
    """
    color_map = {
        'FIRE': glm.vec3(1.0, 0.4, 0.0),      # Orange
        'ICE': glm.vec3(0.3, 0.6, 1.0),       # Blue
        'LIGHTNING': glm.vec3(1.0, 1.0, 0.5), # Yellow-white
        'ARCANE': glm.vec3(0.7, 0.3, 1.0),    # Purple
        'NATURE': glm.vec3(0.3, 0.9, 0.3),    # Green
        'HOLY': glm.vec3(1.0, 1.0, 0.8),      # Bright gold-white
    }

    return color_map.get(element.name, glm.vec3(0.8, 0.3, 0.8))  # Default purple


class SpellType(Enum):
    """Types of spells available."""
    FIREBALL = auto()
    LIGHTNING = auto()
    ICE_SHARD = auto()
    HEAL = auto()
    SHIELD = auto()
    TELEPORT = auto()
    MAGIC_MISSILE = auto()
    METEOR = auto()


class SpellElement(Enum):
    """Elemental types for spells."""
    FIRE = auto()
    ICE = auto()
    LIGHTNING = auto()
    ARCANE = auto()
    NATURE = auto()
    HOLY = auto()


class StatusEffect(Enum):
    """Status effects that can be applied."""
    BURNING = auto()
    FROZEN = auto()
    STUNNED = auto()
    SHIELDED = auto()
    REGENERATING = auto()


@dataclass
class SpellStats:
    """Statistics for a spell."""
    damage: float = 0.0
    healing: float = 0.0
    mana_cost: float = 0.0
    cooldown: float = 0.0
    cast_time: float = 0.0
    range: float = 0.0
    projectile_speed: float = 0.0
    area_of_effect: float = 0.0
    duration: float = 0.0
    status_effect: Optional[StatusEffect] = None
    status_duration: float = 0.0


@dataclass
class Spell:
    """Represents a spell that can be cast."""
    spell_type: SpellType
    name: str
    description: str
    element: SpellElement
    stats: SpellStats
    level: int = 1
    is_projectile: bool = False
    is_instant: bool = False
    is_self_target: bool = False
    particle_effect: str = "sparkle"
    sound_effect: str = "spell_cast"

    def get_damage(self) -> float:
        """Get spell damage scaled by level."""
        return self.stats.damage * (1.0 + (self.level - 1) * 0.2)

    def get_healing(self) -> float:
        """Get spell healing scaled by level."""
        return self.stats.healing * (1.0 + (self.level - 1) * 0.2)

    def get_mana_cost(self) -> float:
        """Get mana cost (doesn't scale with level)."""
        return self.stats.mana_cost

    def get_cooldown(self) -> float:
        """Get cooldown time."""
        return self.stats.cooldown


# Spell definitions
SPELL_DEFINITIONS = {
    SpellType.FIREBALL: Spell(
        spell_type=SpellType.FIREBALL,
        name="Fireball",
        description="Launch a blazing ball of fire at your enemy.",
        element=SpellElement.FIRE,
        stats=SpellStats(
            damage=30.0,
            mana_cost=25.0,
            cooldown=2.0,
            cast_time=0.5,
            range=30.0,
            projectile_speed=15.0,
            area_of_effect=3.0,
            status_effect=StatusEffect.BURNING,
            status_duration=5.0,
        ),
        is_projectile=True,
        particle_effect="embers",
        sound_effect="fireball",
    ),
    SpellType.LIGHTNING: Spell(
        spell_type=SpellType.LIGHTNING,
        name="Lightning Bolt",
        description="Strike your foe with a bolt of lightning.",
        element=SpellElement.LIGHTNING,
        stats=SpellStats(
            damage=40.0,
            mana_cost=30.0,
            cooldown=3.0,
            cast_time=0.3,
            range=25.0,
            status_effect=StatusEffect.STUNNED,
            status_duration=2.0,
        ),
        is_instant=True,
        particle_effect="sparkle",
        sound_effect="lightning",
    ),
    SpellType.ICE_SHARD: Spell(
        spell_type=SpellType.ICE_SHARD,
        name="Ice Shard",
        description="Fire a shard of ice that slows enemies.",
        element=SpellElement.ICE,
        stats=SpellStats(
            damage=25.0,
            mana_cost=20.0,
            cooldown=1.5,
            cast_time=0.4,
            range=35.0,
            projectile_speed=20.0,
            status_effect=StatusEffect.FROZEN,
            status_duration=3.0,
        ),
        is_projectile=True,
        particle_effect="snow",
        sound_effect="ice_cast",
    ),
    SpellType.HEAL: Spell(
        spell_type=SpellType.HEAL,
        name="Healing Light",
        description="Restore health with holy magic.",
        element=SpellElement.HOLY,
        stats=SpellStats(
            healing=50.0,
            mana_cost=40.0,
            cooldown=5.0,
            cast_time=1.0,
        ),
        is_self_target=True,
        is_instant=True,
        particle_effect="sparkle",
        sound_effect="heal",
    ),
    SpellType.SHIELD: Spell(
        spell_type=SpellType.SHIELD,
        name="Arcane Shield",
        description="Create a magical barrier that absorbs damage.",
        element=SpellElement.ARCANE,
        stats=SpellStats(
            mana_cost=35.0,
            cooldown=10.0,
            cast_time=0.5,
            duration=10.0,
            status_effect=StatusEffect.SHIELDED,
            status_duration=10.0,
        ),
        is_self_target=True,
        is_instant=True,
        particle_effect="sparkle",
        sound_effect="shield",
    ),
    SpellType.TELEPORT: Spell(
        spell_type=SpellType.TELEPORT,
        name="Blink",
        description="Instantly teleport a short distance forward.",
        element=SpellElement.ARCANE,
        stats=SpellStats(
            mana_cost=30.0,
            cooldown=4.0,
            cast_time=0.2,
            range=10.0,
        ),
        is_self_target=True,
        is_instant=True,
        particle_effect="sparkle",
        sound_effect="teleport",
    ),
    SpellType.MAGIC_MISSILE: Spell(
        spell_type=SpellType.MAGIC_MISSILE,
        name="Magic Missile",
        description="Fire a bolt of pure arcane energy.",
        element=SpellElement.ARCANE,
        stats=SpellStats(
            damage=20.0,
            mana_cost=15.0,
            cooldown=1.0,
            cast_time=0.3,
            range=40.0,
            projectile_speed=25.0,
        ),
        is_projectile=True,
        particle_effect="sparkle",
        sound_effect="magic_missile",
    ),
    SpellType.METEOR: Spell(
        spell_type=SpellType.METEOR,
        name="Meteor Strike",
        description="Call down a meteor from the sky.",
        element=SpellElement.FIRE,
        stats=SpellStats(
            damage=80.0,
            mana_cost=60.0,
            cooldown=15.0,
            cast_time=2.0,
            range=40.0,
            area_of_effect=8.0,
            status_effect=StatusEffect.BURNING,
            status_duration=8.0,
        ),
        is_instant=False,
        particle_effect="embers",
        sound_effect="meteor",
    ),
}


@dataclass
class SpellProjectile:
    """Represents a spell projectile in flight."""
    spell: Spell
    position: glm.vec3
    direction: glm.vec3
    caster_id: int  # ID of the entity that cast the spell
    lifetime: float = 0.0
    max_lifetime: float = 5.0

    def update(self, delta_time: float) -> bool:
        """Update projectile position. Returns True if still active."""
        self.lifetime += delta_time
        if self.lifetime >= self.max_lifetime:
            return False

        # Move projectile
        self.position += self.direction * self.spell.stats.projectile_speed * delta_time
        return True

    def check_collision(self, target_position: glm.vec3, target_radius: float = 1.0) -> bool:
        """Check if projectile hit a target."""
        distance = glm.length(self.position - target_position)
        return distance <= target_radius


@dataclass
class ActiveStatusEffect:
    """Represents an active status effect on an entity."""
    effect_type: StatusEffect
    duration: float
    remaining_time: float
    intensity: float = 1.0

    def update(self, delta_time: float) -> bool:
        """Update effect timer. Returns True if still active."""
        self.remaining_time -= delta_time
        return self.remaining_time > 0


class SpellCaster:
    """Manages spell casting for an entity."""

    def __init__(self, max_mana: float = 100.0):
        self.max_mana = max_mana
        self.current_mana = max_mana
        self.mana_regen_rate = 10.0  # Mana per second

        # Known spells
        self.known_spells: List[Spell] = []
        self.equipped_spells: List[Optional[Spell]] = [None] * 8  # 8 spell slots

        # Casting state
        self.is_casting = False
        self.current_spell: Optional[Spell] = None
        self.cast_time_remaining = 0.0

        # Cooldowns
        self.spell_cooldowns: dict[SpellType, float] = {}

        # Active status effects
        self.active_effects: List[ActiveStatusEffect] = []

    def add_known_spell(self, spell_type: SpellType):
        """Learn a new spell."""
        spell = SPELL_DEFINITIONS.get(spell_type)
        if spell and spell not in self.known_spells:
            self.known_spells.append(spell)
            logger.info(f"Learned spell: {spell.name}")

    def equip_spell(self, spell_type: SpellType, slot: int) -> bool:
        """Equip a spell to a quick slot (0-7)."""
        if slot < 0 or slot >= 8:
            return False

        spell = SPELL_DEFINITIONS.get(spell_type)
        if spell and spell in self.known_spells:
            self.equipped_spells[slot] = spell
            logger.info(f"Equipped {spell.name} to slot {slot + 1}")
            return True
        return False

    def can_cast_spell(self, spell: Spell) -> tuple[bool, str]:
        """Check if a spell can be cast. Returns (can_cast, reason)."""
        if self.is_casting:
            return False, "Already casting"

        if self.current_mana < spell.get_mana_cost():
            return False, "Not enough mana"

        if spell.spell_type in self.spell_cooldowns:
            remaining = self.spell_cooldowns[spell.spell_type]
            if remaining > 0:
                return False, f"On cooldown ({remaining:.1f}s)"

        return True, ""

    def start_cast(self, spell: Spell) -> bool:
        """Begin casting a spell."""
        can_cast, reason = self.can_cast_spell(spell)
        if not can_cast:
            logger.debug(f"Cannot cast {spell.name}: {reason}")
            return False

        # Consume mana
        self.current_mana -= spell.get_mana_cost()

        # Start casting
        self.is_casting = True
        self.current_spell = spell
        self.cast_time_remaining = spell.stats.cast_time

        # If instant cast, complete immediately
        if spell.is_instant or spell.stats.cast_time == 0:
            self.complete_cast()

        return True

    def complete_cast(self) -> Optional[Spell]:
        """Complete spell cast. Returns the spell that was cast."""
        if not self.is_casting or not self.current_spell:
            return None

        spell = self.current_spell

        # Set cooldown
        self.spell_cooldowns[spell.spell_type] = spell.get_cooldown()

        # Reset casting state
        self.is_casting = False
        cast_spell = self.current_spell
        self.current_spell = None
        self.cast_time_remaining = 0.0

        logger.debug(f"Cast {spell.name}")
        return cast_spell

    def cancel_cast(self):
        """Cancel current spell cast."""
        if self.is_casting:
            logger.debug(f"Cancelled {self.current_spell.name}")
            # Return half the mana cost
            if self.current_spell:
                self.current_mana += self.current_spell.get_mana_cost() * 0.5
            self.is_casting = False
            self.current_spell = None
            self.cast_time_remaining = 0.0

    def update(self, delta_time: float):
        """Update spell casting state."""
        # Update casting
        if self.is_casting and self.current_spell:
            self.cast_time_remaining -= delta_time
            if self.cast_time_remaining <= 0:
                self.complete_cast()

        # Update cooldowns
        for spell_type in list(self.spell_cooldowns.keys()):
            self.spell_cooldowns[spell_type] -= delta_time
            if self.spell_cooldowns[spell_type] <= 0:
                del self.spell_cooldowns[spell_type]

        # Regenerate mana
        if self.current_mana < self.max_mana:
            self.current_mana = min(self.max_mana,
                                   self.current_mana + self.mana_regen_rate * delta_time)

        # Update status effects
        self.active_effects = [
            effect for effect in self.active_effects
            if effect.update(delta_time)
        ]

    def add_status_effect(self, effect_type: StatusEffect, duration: float, intensity: float = 1.0):
        """Apply a status effect."""
        # Check if effect already exists
        for effect in self.active_effects:
            if effect.effect_type == effect_type:
                # Refresh duration if new duration is longer
                if duration > effect.remaining_time:
                    effect.remaining_time = duration
                    effect.intensity = max(effect.intensity, intensity)
                return

        # Add new effect
        self.active_effects.append(ActiveStatusEffect(
            effect_type=effect_type,
            duration=duration,
            remaining_time=duration,
            intensity=intensity
        ))
        logger.debug(f"Applied {effect_type.name} for {duration}s")

    def has_status_effect(self, effect_type: StatusEffect) -> bool:
        """Check if entity has a specific status effect."""
        return any(effect.effect_type == effect_type for effect in self.active_effects)

    def get_status_effect_multiplier(self, effect_type: StatusEffect) -> float:
        """Get the intensity of a status effect, or 0 if not active."""
        for effect in self.active_effects:
            if effect.effect_type == effect_type:
                return effect.intensity
        return 0.0


class SpellManager:
    """Manages all active spells and projectiles in the world."""

    def __init__(self):
        self.active_projectiles: List[SpellProjectile] = []

    def cast_projectile_spell(self, spell: Spell, position: glm.vec3,
                             direction: glm.vec3, caster_id: int) -> SpellProjectile:
        """Create a spell projectile."""
        projectile = SpellProjectile(
            spell=spell,
            position=glm.vec3(position),  # Create copy of position
            direction=glm.normalize(direction),
            caster_id=caster_id,
            max_lifetime=spell.stats.range / spell.stats.projectile_speed
        )
        self.active_projectiles.append(projectile)
        return projectile

    def update(self, delta_time: float):
        """Update all active projectiles."""
        # Update projectiles and remove expired ones
        self.active_projectiles = [
            proj for proj in self.active_projectiles
            if proj.update(delta_time)
        ]

    def get_projectiles(self) -> List[SpellProjectile]:
        """Get all active projectiles."""
        return self.active_projectiles

    def clear(self):
        """Clear all active projectiles."""
        self.active_projectiles.clear()
