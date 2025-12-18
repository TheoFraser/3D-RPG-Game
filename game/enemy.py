"""Enemy AI with combat."""
import glm
from enum import Enum, auto
from typing import Optional, Callable, List
import config
from game.stats import create_enemy_stats
from game.combat import CombatController, CombatSystem, AttackType
from physics.spatial_grid import SpatialGrid


class EnemyState(Enum):
    """Enemy AI states."""
    IDLE = auto()
    PATROL = auto()
    AGGRO = auto()
    CHASE = auto()
    ATTACK = auto()
    RETREAT = auto()
    DEAD = auto()


class EnemyType(Enum):
    """Types of enemies."""
    WEAK = auto()  # Low health, low damage
    NORMAL = auto()  # Balanced
    TANK = auto()  # High health, slow
    FAST = auto()  # Low health, fast, high damage


class Enemy:
    """Enemy with combat AI."""

    # Enemy type stats (health, stamina, damage, defense)
    ENEMY_STATS = {
        EnemyType.WEAK: (30, 50, 5, 2),
        EnemyType.NORMAL: (60, 80, 10, 5),
        EnemyType.TANK: (120, 100, 8, 10),
        EnemyType.FAST: (40, 60, 15, 3),
    }

    # Enemy type speeds
    ENEMY_SPEEDS = {
        EnemyType.WEAK: 2.0,
        EnemyType.NORMAL: 2.5,
        EnemyType.TANK: 1.5,
        EnemyType.FAST: 4.0,
    }

    def __init__(
        self,
        position: glm.vec3,
        enemy_type: EnemyType = EnemyType.NORMAL,
        name: str = "Enemy"
    ):
        """
        Initialize enemy.

        Args:
            position: Starting position
            enemy_type: Type of enemy
            name: Enemy name
        """
        self.position = position
        self.enemy_type = enemy_type
        self.name = name

        # Create stats based on type
        health, stamina, damage, defense = self.ENEMY_STATS[enemy_type]
        self.stats = create_enemy_stats(health, stamina, damage, defense)
        self.combat = CombatController(self.stats)

        # Movement
        self.velocity = glm.vec3(0.0, 0.0, 0.0)
        self.speed = self.ENEMY_SPEEDS[enemy_type]

        # AI state
        self.state = EnemyState.IDLE
        self.target: Optional[any] = None  # Player or other target

        # AI timers
        self.state_timer = 0.0
        self.aggro_timer = 0.0
        self.death_timer = 0.0  # Timer for removal after death

        # Combat properties
        self.attack_range = config.ENEMY_ATTACK_RANGE
        self.aggro_range = config.ENEMY_AGGRO_RANGE
        self.chase_range = config.ENEMY_CHASE_RANGE

        # Rendering
        self.scale = glm.vec3(0.5, 0.9, 0.5)  # Render scale
        self.color = glm.vec3(0.8, 0.2, 0.2)  # Red-ish for enemies

        # Cached matrices for performance (avoid recalculating every frame)
        self._cached_model_matrix = None
        self._cached_normal_matrix = None
        self._last_position = None

        # Loot and XP flags
        self.loot_dropped = False  # Track if loot/XP has been awarded

    def update(self, delta_time: float, player_pos: glm.vec3, terrain=None) -> None:
        """
        Update enemy AI and combat.

        Args:
            delta_time: Time since last update
            player_pos: Player position for targeting
            terrain: Terrain/chunk manager for height queries
        """
        # Update combat state
        self.combat.update(delta_time)

        # Check if dead
        if not self.stats.is_alive and self.state != EnemyState.DEAD:
            self.state = EnemyState.DEAD
            self.death_timer = 0.0
            return

        if self.state == EnemyState.DEAD:
            self.death_timer += delta_time
            return

        # Update AI state machine
        self._update_ai(delta_time, player_pos)

        # Apply velocity
        self.position += self.velocity * delta_time

        # Snap to terrain height
        if terrain is not None:
            terrain_height = terrain.get_height_at(self.position.x, self.position.z)
            self.position.y = terrain_height

    def _update_ai(self, delta_time: float, player_pos: glm.vec3) -> None:
        """
        Update AI state machine.

        Args:
            delta_time: Time since last update
            player_pos: Player position
        """
        distance_to_player = glm.length(player_pos - self.position)

        # State transitions
        if self.state == EnemyState.IDLE:
            # Check for player in aggro range
            if distance_to_player <= self.aggro_range:
                self.state = EnemyState.AGGRO
                self.target = player_pos
                self.aggro_timer = 0.5  # Brief pause before chasing

        elif self.state == EnemyState.AGGRO:
            self.aggro_timer -= delta_time
            if self.aggro_timer <= 0:
                self.state = EnemyState.CHASE

        elif self.state == EnemyState.CHASE:
            # Check if in attack range
            if distance_to_player <= self.attack_range:
                self.state = EnemyState.ATTACK
                self.velocity = glm.vec3(0.0, 0.0, 0.0)  # Stop moving
            # Check if player escaped
            elif distance_to_player > self.chase_range:
                self.state = EnemyState.IDLE
                self.velocity = glm.vec3(0.0, 0.0, 0.0)
            # Move towards player
            else:
                direction = glm.normalize(player_pos - self.position)
                self.velocity = glm.vec3(direction.x, 0.0, direction.z) * self.speed

        elif self.state == EnemyState.ATTACK:
            # Check if player moved out of range
            if distance_to_player > self.attack_range * 1.5:
                self.state = EnemyState.CHASE
            # Try to attack
            elif self.combat.can_attack():
                self.combat.start_attack()

        elif self.state == EnemyState.RETREAT:
            # Move away from player
            if distance_to_player > self.aggro_range:
                self.state = EnemyState.IDLE
                self.velocity = glm.vec3(0.0, 0.0, 0.0)
            else:
                direction = glm.normalize(self.position - player_pos)
                self.velocity = glm.vec3(direction.x, 0.0, direction.z) * self.speed

        # Check for retreat condition (low health)
        if self.stats.health_percent < config.ENEMY_RETREAT_HEALTH:
            if self.state not in [EnemyState.RETREAT, EnemyState.DEAD]:
                self.state = EnemyState.RETREAT

    def take_damage_from(self, attacker_stats, attack_type: AttackType = AttackType.LIGHT):
        """
        Take damage from an attacker.

        Args:
            attacker_stats: Attacker's CharacterStats
            attack_type: Type of attack

        Returns:
            CombatResult
        """
        result = CombatSystem.execute_attack(
            attacker_stats,
            self.stats,
            attack_type,
            defender_is_blocking=self.combat.is_blocking
        )

        # If hit and not dead, enter aggro/chase state
        if result.hit and self.stats.is_alive:
            if self.state == EnemyState.IDLE:
                self.state = EnemyState.CHASE

        return result

    def get_model_matrix(self) -> glm.mat4:
        """
        Get model matrix for rendering (cached for performance).

        Returns:
            glm.mat4: Model transformation matrix
        """
        # Check if we need to recalculate (position changed)
        if (self._cached_model_matrix is None or
            self._last_position != self.position):

            # Recalculate model matrix
            model = glm.mat4(1.0)
            model = glm.translate(model, self.position)
            model = glm.scale(model, self.scale)

            # Cache it
            self._cached_model_matrix = model
            self._last_position = glm.vec3(self.position)  # Copy position

            # Invalidate normal matrix cache
            self._cached_normal_matrix = None

        return self._cached_model_matrix

    def get_normal_matrix(self) -> glm.mat3:
        """
        Get normal matrix for rendering (cached for performance).

        Returns:
            glm.mat3: Normal matrix for transforming normals
        """
        if self._cached_normal_matrix is None:
            # Ensure model matrix is up to date
            model = self.get_model_matrix()
            # Calculate normal matrix
            self._cached_normal_matrix = glm.mat3(glm.transpose(glm.inverse(model)))

        return self._cached_normal_matrix

    def get_render_position(self) -> glm.vec3:
        """Get position for rendering."""
        return self.position

    def is_alive(self) -> bool:
        """Check if enemy is alive."""
        return self.stats.is_alive


class EnemyManager:
    """Manages all enemies in the game with spatial partitioning."""

    def __init__(self, cell_size: float = 10.0):
        """
        Initialize enemy manager.

        Args:
            cell_size: Size of spatial grid cells for proximity queries
        """
        self.enemies: List[Enemy] = []
        self.spatial_grid: SpatialGrid[Enemy] = SpatialGrid(cell_size)
        self.on_enemy_defeated: Optional[Callable[[Enemy], None]] = None  # Callback for enemy death

    def add_enemy(self, enemy: Enemy) -> None:
        """
        Add an enemy.

        Args:
            enemy: Enemy to add
        """
        self.enemies.append(enemy)
        self.spatial_grid.insert(enemy, enemy.position)

    def remove_enemy(self, enemy: Enemy) -> None:
        """
        Remove an enemy.

        Args:
            enemy: Enemy to remove
        """
        if enemy in self.enemies:
            self.enemies.remove(enemy)
            self.spatial_grid.remove(enemy)

    def update_all(self, delta_time: float, player_pos: glm.vec3, terrain=None) -> None:
        """
        Update all enemies.

        Args:
            delta_time: Time since last update
            player_pos: Player position
            terrain: Terrain/chunk manager for height queries
        """
        # Update all enemies
        for enemy in self.enemies:
            old_pos = glm.vec3(enemy.position)
            enemy.update(delta_time, player_pos, terrain)

            # Update spatial grid if position changed
            if enemy.position != old_pos:
                self.spatial_grid.update(enemy, enemy.position)

            # Check if enemy just died and hasn't dropped loot yet
            if enemy.state == EnemyState.DEAD and not enemy.loot_dropped:
                enemy.loot_dropped = True
                # Trigger defeat callback for loot/XP
                if self.on_enemy_defeated:
                    self.on_enemy_defeated(enemy)

        # Remove dead enemies after a delay (2 seconds)
        dead_enemies = [e for e in self.enemies if e.state == EnemyState.DEAD and e.death_timer >= 2.0]
        for enemy in dead_enemies:
            self.remove_enemy(enemy)

    def get_all_enemies(self):
        """Get all enemies."""
        return self.enemies

    def get_nearest_enemy(self, position: glm.vec3, max_distance: float = None):
        """
        Get the nearest enemy to a position using spatial partitioning (O(log N)).

        Args:
            position: Position to check from
            max_distance: Maximum distance to consider (defaults to infinite)

        Returns:
            Nearest enemy or None
        """
        # Use spatial grid for efficient proximity query
        search_radius = max_distance if max_distance is not None else 100.0

        # Filter function: only alive enemies
        def filter_alive(enemy: Enemy) -> bool:
            return enemy.is_alive()

        # Get position function for spatial grid
        def get_pos(enemy: Enemy) -> glm.vec3:
            return enemy.position

        # Use spatial grid for O(log N) query instead of O(N)
        return self.spatial_grid.get_nearest(
            position,
            search_radius,
            get_pos,
            filter_alive
        )

    def clear(self) -> None:
        """Remove all enemies."""
        self.enemies.clear()
