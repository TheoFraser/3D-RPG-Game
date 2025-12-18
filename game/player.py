"""Player controller with physics."""
from typing import Optional, Tuple
import glm
from engine.camera import Camera
from physics.collision import AABB
import config
from game.stats import create_player_stats, CharacterStats
from game.combat import CombatController, CombatSystem
from game.equipment import Equipment, EquipmentItem
from game.progression import CharacterProgression
from game.inventory import Inventory
from game.logger import get_logger

logger = get_logger(__name__)


class Player:
    """Player with physics-based movement."""

    def __init__(self, position: Optional[glm.vec3] = None) -> None:
        """
        Initialize the player.

        Args:
            position: Starting position (glm.vec3)
        """
        self.position = position or glm.vec3(0.0, 2.0, 5.0)
        self.velocity = glm.vec3(0.0, 0.0, 0.0)

        # Physics properties
        self.gravity = -15.0  # m/s^2
        self.jump_force = 6.0  # m/s
        self.is_grounded = False
        self.ground_height = 0.0

        # Player dimensions (for collision)
        self.height = 1.8  # meters
        self.radius = 0.4  # meters (capsule radius)

        # Slope limits
        self.max_slope_angle = 50.0  # degrees - steeper slopes can't be walked up
        self.slide_threshold = 55.0  # degrees - steeper slopes cause sliding

        # Movement
        self.movement_speed = config.MOVEMENT_SPEED
        self.sprint_multiplier = config.SPRINT_MULTIPLIER

        # Combat stats and controller
        self.base_stats = create_player_stats()  # Base stats without bonuses
        self.stats = self.base_stats  # Will be updated with bonuses
        self.combat = CombatController(self.stats)

        # Equipment system (Phase 5)
        self.equipment = Equipment()

        # Inventory system (Phase 6)
        self.inventory = Inventory()

        # Progression system (Phase 5)
        self.progression = CharacterProgression(starting_level=1)
        self.progression.on_level_up = self._on_level_up
        self.progression.on_xp_gain = self._on_xp_gain

        # Currency (Phase 6)
        self.gold = 100  # Starting gold

        # Combat properties
        self.attack_range = 2.5  # meters

        # Apply initial equipment bonuses
        self._update_stats_with_bonuses()

        # Camera
        self.camera = Camera(position=self.position + glm.vec3(0.0, self.height * 0.9, 0.0))

        # Cached movement vectors for performance
        self._forward = glm.vec3(0.0, 0.0, -1.0)
        self._right = glm.vec3(1.0, 0.0, 0.0)
        self._update_movement_vectors()

    def get_collision_box(self) -> AABB:
        """Get the player's collision AABB."""
        size = glm.vec3(self.radius * 2, self.height, self.radius * 2)
        return AABB.from_center_size(self.position + glm.vec3(0.0, self.height * 0.5, 0.0), size)

    def update(self, delta_time: float, terrain: Optional[any] = None) -> None:
        """
        Update player physics and combat.

        Args:
            delta_time: Time since last frame
            terrain: Terrain object for height queries (optional)
        """
        # Update combat state (cooldowns, stamina regen, etc.)
        self.combat.update(delta_time)

        # Apply gravity
        if not self.is_grounded:
            self.velocity.y += self.gravity * delta_time
        else:
            # On ground, reset vertical velocity
            if self.velocity.y < 0:
                self.velocity.y = 0

        # Store old position for slope checking
        old_position = glm.vec3(self.position)

        # Apply velocity to position
        self.position += self.velocity * delta_time

        # Get terrain height if available
        if terrain is not None:
            self.ground_height = terrain.get_height_at(self.position.x, self.position.z)

        # Ground collision with slope checking
        if self.position.y <= self.ground_height:
            # Check if slope is too steep to walk up
            if terrain is not None and old_position.y > 0.1:  # Only check if we have a valid old position
                # Calculate slope by checking height change
                old_ground_height = terrain.get_height_at(old_position.x, old_position.z)
                height_change = self.ground_height - old_ground_height
                horizontal_distance = glm.length(glm.vec2(
                    self.position.x - old_position.x,
                    self.position.z - old_position.z
                ))

                if horizontal_distance > 0.001:  # Avoid division by zero
                    slope_angle = glm.degrees(glm.atan(height_change / horizontal_distance))
                else:
                    slope_angle = 0.0  # Flat ground or no movement

                # If slope is too steep and we're trying to go up, prevent movement
                if slope_angle > self.max_slope_angle and height_change > 0:
                    # Restore old horizontal position (can't walk up)
                    self.position.x = old_position.x
                    self.position.z = old_position.z
                    # Recalculate ground height at old position
                    self.ground_height = old_ground_height

                # If slope is extremely steep, slide down
                elif slope_angle > self.slide_threshold:
                    # Calculate slide direction (down the slope)
                    slide_direction = glm.normalize(glm.vec2(
                        old_position.x - self.position.x,
                        old_position.z - self.position.z
                    ))
                    slide_speed = 2.0 * delta_time
                    self.position.x += slide_direction.x * slide_speed
                    self.position.z += slide_direction.y * slide_speed

            self.position.y = self.ground_height
            self.is_grounded = True
            self.velocity.y = 0
        else:
            self.is_grounded = False

        # Update camera position to follow player (eye level)
        eye_height = self.height * 0.9  # 90% of player height
        self.camera.position = self.position + glm.vec3(0.0, eye_height, 0.0)

    def move(self, direction: str, delta_time: float, sprinting: bool = False) -> None:
        """
        Move the player in a direction.

        Args:
            direction: Movement direction ('forward', 'backward', 'left', 'right')
            delta_time: Time since last frame
            sprinting: Whether sprint is active
        """
        speed = self.movement_speed
        if sprinting:
            speed *= self.sprint_multiplier

        # Use cached movement vectors (updated when camera rotates)
        if direction == "forward":
            self.position += self._forward * speed * delta_time
        elif direction == "backward":
            self.position -= self._forward * speed * delta_time
        elif direction == "left":
            self.position -= self._right * speed * delta_time
        elif direction == "right":
            self.position += self._right * speed * delta_time

    def jump(self) -> None:
        """Make the player jump."""
        if self.is_grounded:
            self.velocity.y = self.jump_force
            self.is_grounded = False

    def _update_movement_vectors(self) -> None:
        """Update cached movement vectors based on camera direction."""
        # Ignore vertical component for movement
        self._forward = glm.normalize(glm.vec3(self.camera.front.x, 0.0, self.camera.front.z))
        self._right = glm.normalize(glm.cross(self._forward, glm.vec3(0.0, 1.0, 0.0)))

    def process_mouse_movement(self, xoffset: float, yoffset: float) -> None:
        """Pass mouse movement to camera and update movement vectors."""
        self.camera.process_mouse_movement(xoffset, yoffset)
        self._update_movement_vectors()  # Update cached vectors when camera rotates

    # ===== Combat Methods =====

    def attack(self, target=None):
        """
        Perform an attack.

        Args:
            target: Target entity with combat stats (optional)

        Returns:
            CombatResult if target provided, bool otherwise
        """
        if not self.combat.start_attack():
            return False if target is None else None

        # If we have a target, calculate damage
        if target is not None and hasattr(target, 'stats'):
            # Check if in range
            if not CombatSystem.is_in_range(self.position, target.position, self.attack_range):
                return None

            # Execute attack
            is_blocking = hasattr(target, 'combat') and target.combat.is_blocking
            result = CombatSystem.execute_attack(
                self.stats,
                target.stats,
                defender_is_blocking=is_blocking
            )
            return result

        return True

    def dodge(self):
        """
        Perform a dodge roll.

        Returns:
            bool: True if dodge started
        """
        if not self.combat.start_dodge():
            return False

        # Apply dodge movement
        forward = glm.normalize(glm.vec3(self.camera.front.x, 0.0, self.camera.front.z))
        self.velocity += forward * config.DODGE_DISTANCE

        return True

    def start_block(self):
        """Start blocking."""
        return self.combat.start_block()

    def stop_block(self):
        """Stop blocking."""
        self.combat.stop_block()

    def get_look_target_position(self, max_distance=None):
        """
        Get the position the player is looking at.

        Args:
            max_distance: Maximum distance to check

        Returns:
            glm.vec3: Position in world space
        """
        if max_distance is None:
            max_distance = self.attack_range

        # Cast ray from camera forward
        return self.camera.position + self.camera.front * max_distance

    # ===== Equipment & Progression Methods (Phase 5) =====

    def _update_stats_with_bonuses(self) -> None:
        """Update stats with bonuses from equipment and levels."""
        # Get bonuses
        equip_damage = self.equipment.get_total_damage_bonus()
        equip_defense = self.equipment.get_total_defense_bonus()
        equip_health = self.equipment.get_total_health_bonus()
        equip_stamina = self.equipment.get_total_stamina_bonus()

        level_bonuses = self.progression.get_all_stat_bonuses()

        # Apply to base stats
        self.stats.base_damage = config.PLAYER_BASE_DAMAGE + equip_damage + level_bonuses.get('base_damage', 0)
        self.stats.defense = config.PLAYER_DEFENSE + equip_defense + level_bonuses.get('defense', 0)

        # Apply health bonus (update max and current proportionally)
        new_max_health = config.PLAYER_MAX_HEALTH + equip_health + level_bonuses.get('max_health', 0)
        health_percent = self.stats.health_percent
        self.stats.max_health = new_max_health
        self.stats.current_health = new_max_health * health_percent

        # Apply stamina bonus (update max and current proportionally)
        new_max_stamina = config.PLAYER_MAX_STAMINA + equip_stamina + level_bonuses.get('max_stamina', 0)
        stamina_percent = self.stats.stamina_percent
        self.stats.max_stamina = new_max_stamina
        self.stats.current_stamina = new_max_stamina * stamina_percent

    def equip_item(self, item: EquipmentItem) -> EquipmentItem:
        """
        Equip an item.

        Args:
            item: Equipment item to equip

        Returns:
            Previously equipped item, or None

        Raises:
            ValueError: If item is None
            TypeError: If item is not an EquipmentItem
        """
        if item is None:
            raise ValueError("Cannot equip None item")

        if not isinstance(item, EquipmentItem):
            raise TypeError(f"Expected EquipmentItem, got {type(item).__name__}")

        # Check level requirement
        if item.level_required > self.progression.level:
            logger.warning(f"Item {item.name} requires level {item.level_required}, player is level {self.progression.level}")
            raise ValueError(f"Item requires level {item.level_required}")

        old_item = self.equipment.equip(item)
        self._update_stats_with_bonuses()
        logger.debug(f"Equipped {item.name}")
        return old_item

    def unequip_item(self, slot) -> EquipmentItem:
        """
        Unequip an item from a slot.

        Args:
            slot: Equipment slot to unequip

        Returns:
            The unequipped item, or None
        """
        item = self.equipment.unequip(slot)
        self._update_stats_with_bonuses()
        return item

    def gain_xp(self, amount: int) -> list:
        """
        Gain XP and check for level ups.

        Args:
            amount: Amount of XP to gain

        Returns:
            List of levels gained
        """
        return self.progression.add_xp(amount)

    def _on_level_up(self, new_level: int) -> None:
        """
        Called when player levels up.

        Args:
            new_level: The new level
        """
        logger.info(f"LEVEL UP! You are now level {new_level}!")
        self._update_stats_with_bonuses()

        # Fully restore health and stamina on level up
        self.stats.current_health = self.stats.max_health
        self.stats.current_stamina = self.stats.max_stamina

    def _on_xp_gain(self, xp_gained: int, new_total: int) -> None:
        """
        Called when player gains XP.

        Args:
            xp_gained: Amount of XP gained
            new_total: New total XP
        """
        logger.debug(f"+{xp_gained} XP ({new_total}/{self.progression.xp_to_next_level + new_total} to next level)")

    def get_power_level(self) -> int:
        """Get player's overall power level."""
        return self.progression.level * 10 + self.equipment.get_equipment_power()

    def add_gold(self, amount: int) -> None:
        """
        Add gold to player's currency.

        Args:
            amount: Amount of gold to add

        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError(f"Cannot add negative gold: {amount}")

        self.gold += amount
        logger.info(f"+{amount} gold ({self.gold} total)")

    def remove_gold(self, amount: int) -> bool:
        """
        Remove gold from player's currency.

        Args:
            amount: Amount of gold to remove

        Returns:
            True if player had enough gold, False otherwise
        """
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False

    def can_afford(self, amount: int) -> bool:
        """Check if player can afford a purchase."""
        return self.gold >= amount
