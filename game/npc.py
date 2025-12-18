"""NPC (Non-Player Character) system with AI behaviors."""
import glm
import numpy as np
from enum import Enum
from game.entities import Entity
import config


class NPCState(Enum):
    """NPC AI states."""
    IDLE = "idle"
    PATROL = "patrol"
    INTERACT = "interact"
    FLEE = "flee"
    FOLLOW = "follow"


class NPCBehavior(Enum):
    """NPC behavior types."""
    FRIENDLY = "friendly"      # Will talk to player
    NEUTRAL = "neutral"        # Ignores player unless approached
    HOSTILE = "hostile"        # Avoids player
    QUEST_GIVER = "quest_giver"  # Has quests to offer


class NPC(Entity):
    """Non-player character with AI and dialogue."""

    def __init__(self, position, name="NPC", npc_id=None):
        """
        Create an NPC.

        Args:
            position: World position (glm.vec3)
            name: NPC display name
            npc_id: Unique identifier for this NPC (for dialogue/quests)
        """
        super().__init__(position, name)
        self.npc_id = npc_id or name.lower().replace(" ", "_")
        self.interactable = True
        self.description = f"Talk to {name}"

        # AI state
        self.state = NPCState.IDLE
        self.behavior = NPCBehavior.FRIENDLY
        self.velocity = glm.vec3(0.0, 0.0, 0.0)
        self.speed = config.NPC_DEFAULT_SPEED

        # Patrol behavior
        self.patrol_points = []
        self.current_patrol_index = 0
        self.patrol_wait_time = config.NPC_PATROL_WAIT_TIME
        self.patrol_timer = 0.0

        # Interaction
        self.interaction_range = config.NPC_INTERACTION_RANGE
        self.last_interaction_time = -999.0  # Far in the past (allow immediate interaction)
        self.interaction_cooldown = config.NPC_INTERACTION_COOLDOWN

        # Dialogue
        self.dialogue_id = None  # ID to look up in dialogue system
        self.has_talked = False

        # Quest
        self.quest_id = None  # Quest this NPC offers
        self.quest_complete_id = None  # Quest this NPC completes

        # Animation state
        self.animation_time = 0.0
        self.bob_height = 0.0  # Subtle bobbing animation

        # Cached matrices for performance (avoid recalculating every frame)
        self._cached_model_matrix = None
        self._cached_normal_matrix = None
        self._last_position = None
        self._last_rotation_y = None

    def set_patrol_points(self, points):
        """
        Set patrol points for patrol behavior.

        Args:
            points: List of glm.vec3 positions to patrol between
        """
        self.patrol_points = points
        self.current_patrol_index = 0
        if points:
            self.state = NPCState.PATROL

    def update(self, delta_time, player_position=None):
        """
        Update NPC AI and position.

        Args:
            delta_time: Time since last frame
            player_position: Player's current position (glm.vec3)
        """
        self.animation_time += delta_time
        self.patrol_timer -= delta_time

        # Subtle bobbing animation
        self.bob_height = np.sin(self.animation_time * config.NPC_BOB_SPEED) * config.NPC_BOB_HEIGHT

        # Update based on state
        if self.state == NPCState.IDLE:
            self._update_idle(delta_time, player_position)

        elif self.state == NPCState.PATROL:
            self._update_patrol(delta_time)

        elif self.state == NPCState.INTERACT:
            self._update_interact(delta_time, player_position)

        elif self.state == NPCState.FOLLOW:
            self._update_follow(delta_time, player_position)

        elif self.state == NPCState.FLEE:
            self._update_flee(delta_time, player_position)

        # Apply velocity
        self.position += self.velocity * delta_time

        # Gradually slow down
        self.velocity *= 0.9

    def _update_idle(self, delta_time, player_position):
        """Update idle behavior - just stand there."""
        if player_position:
            # Face towards player if nearby
            distance = glm.length(player_position - self.position)
            if distance < self.interaction_range * 2:
                self._face_towards(player_position)

    def _update_patrol(self, delta_time):
        """Update patrol behavior - move between patrol points."""
        if not self.patrol_points:
            self.state = NPCState.IDLE
            return

        # Get current target
        target = self.patrol_points[self.current_patrol_index]
        direction = target - self.position
        distance = glm.length(direction)

        # Reached patrol point
        if distance < 0.5:
            if self.patrol_timer <= 0:
                # Move to next patrol point
                self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)
                self.patrol_timer = self.patrol_wait_time
            # Wait at current point
            self.velocity = glm.vec3(0.0, 0.0, 0.0)
        else:
            # Move towards patrol point
            if distance > 0:
                direction = glm.normalize(direction)
                self.velocity = direction * self.speed
                self._face_towards(target)

    def _update_interact(self, delta_time, player_position):
        """Update interact state - face player during conversation."""
        if player_position:
            self._face_towards(player_position)
        # Stay still during interaction
        self.velocity = glm.vec3(0.0, 0.0, 0.0)

    def _update_follow(self, delta_time, player_position):
        """Update follow behavior - follow the player."""
        if not player_position:
            self.state = NPCState.IDLE
            return

        direction = player_position - self.position
        distance = glm.length(direction)

        # Keep some distance from player
        follow_distance = 3.0
        if distance > follow_distance:
            direction = glm.normalize(direction)
            self.velocity = direction * self.speed
            self._face_towards(player_position)
        else:
            self.velocity = glm.vec3(0.0, 0.0, 0.0)

    def _update_flee(self, delta_time, player_position):
        """Update flee behavior - run away from player."""
        if not player_position:
            self.state = NPCState.IDLE
            return

        direction = self.position - player_position  # Opposite direction
        distance = glm.length(player_position - self.position)

        # Only flee if player is nearby
        if distance < 10.0:
            if glm.length(direction) > 0:
                direction = glm.normalize(direction)
                self.velocity = direction * self.speed * 1.5  # Flee faster
        else:
            self.state = NPCState.IDLE

    def _face_towards(self, target_position):
        """
        Rotate to face towards a position.

        Args:
            target_position: Position to face (glm.vec3)
        """
        direction = target_position - self.position
        if glm.length(glm.vec2(direction.x, direction.z)) > 0.01:
            angle = np.arctan2(direction.x, direction.z)
            self.rotation.y = -np.degrees(angle)

    def can_interact(self, player_position, current_time):
        """
        Check if player can interact with this NPC.

        Args:
            player_position: Player's position
            current_time: Current game time

        Returns:
            bool: True if interaction is possible
        """
        distance = glm.length(player_position - self.position)
        cooldown_ok = (current_time - self.last_interaction_time) > self.interaction_cooldown
        return distance < self.interaction_range and cooldown_ok

    def start_interaction(self, current_time):
        """Start interacting with this NPC."""
        self.state = NPCState.INTERACT
        self.last_interaction_time = current_time
        self.has_talked = True

    def end_interaction(self):
        """End interaction and return to previous behavior."""
        if self.patrol_points:
            self.state = NPCState.PATROL
        else:
            self.state = NPCState.IDLE

    def get_render_position(self):
        """Get position with bobbing animation applied."""
        return self.position + glm.vec3(0.0, self.bob_height, 0.0)

    def get_model_matrix(self):
        """
        Get transformation matrix for rendering (cached for performance).

        Returns:
            glm.mat4: Model matrix with translation, rotation, and scale
        """
        # Check if we need to recalculate (position or rotation changed)
        current_pos = self.get_render_position()
        if (self._cached_model_matrix is None or
            self._last_position != current_pos or
            self._last_rotation_y != self.rotation.y):

            # Recalculate model matrix
            model = glm.mat4(1.0)
            model = glm.translate(model, current_pos)
            model = glm.rotate(model, glm.radians(self.rotation.y), glm.vec3(0, 1, 0))
            model = glm.scale(model, glm.vec3(*config.NPC_SCALE))

            # Cache it
            self._cached_model_matrix = model
            self._last_position = current_pos
            self._last_rotation_y = self.rotation.y

            # Invalidate normal matrix cache
            self._cached_normal_matrix = None

        return self._cached_model_matrix

    def get_normal_matrix(self):
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

    def get_collision_box(self):
        """Get the NPC's collision AABB."""
        from physics.collision import AABB
        # NPCs have a capsule-like collision (tall and thin)
        size = glm.vec3(0.6, 1.8, 0.6)
        return AABB.from_center_size(self.position, size)


class NPCManager:
    """Manages all NPCs in the game."""

    def __init__(self):
        """Initialize NPC manager."""
        self.npcs = {}  # npc_id -> NPC
        self.npcs_list = []  # List for iteration

    def add_npc(self, npc):
        """
        Add an NPC to the manager.

        Args:
            npc: NPC instance

        Returns:
            str: NPC ID
        """
        self.npcs[npc.npc_id] = npc
        self.npcs_list.append(npc)
        return npc.npc_id

    def get_npc(self, npc_id):
        """
        Get NPC by ID.

        Args:
            npc_id: NPC identifier

        Returns:
            NPC or None
        """
        return self.npcs.get(npc_id)

    def update_all(self, delta_time, player_position=None):
        """
        Update all NPCs.

        Args:
            delta_time: Time since last frame
            player_position: Player's position
        """
        for npc in self.npcs_list:
            npc.update(delta_time, player_position)

    def get_interactable_npc(self, player_position, current_time):
        """
        Find the closest NPC the player can interact with.

        Args:
            player_position: Player's position
            current_time: Current game time

        Returns:
            NPC or None
        """
        closest_npc = None
        closest_distance = float('inf')

        for npc in self.npcs_list:
            if npc.can_interact(player_position, current_time):
                distance = glm.length(player_position - npc.position)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_npc = npc

        return closest_npc

    def get_all_npcs(self):
        """Get list of all NPCs."""
        return self.npcs_list

    def __len__(self):
        """Return number of NPCs."""
        return len(self.npcs_list)
