"""User interface system."""
import pygame
import glm
import config
import moderngl
import numpy as np
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from game.damage_numbers import DamageNumber


class UI:
    """Simple UI overlay system with OpenGL rendering."""

    def __init__(self, window_width, window_height, ctx=None):
        """Initialize UI system."""
        self.width = window_width
        self.height = window_height
        self.ctx = ctx

        # Initialize fonts
        pygame.font.init()
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)

        # Mini-map settings
        self.minimap_enabled = True
        self.minimap_size = 150
        self.minimap_zoom = 1.0  # Zoom level (0.5 = zoomed out, 2.0 = zoomed in)
        self.minimap_position = 'top-right'  # Options: 'top-right', 'top-left', 'bottom-right', 'bottom-left'
        self.minimap_opacity = 180  # Alpha value (0-255)

        # Create overlay surface
        self.surface = pygame.Surface((window_width, window_height), pygame.SRCALPHA)

        # Colors
        self.color_bg = (0, 0, 0, 180)  # Semi-transparent black
        self.color_text = (255, 255, 255)
        self.color_highlight = (255, 255, 0)
        self.color_success = (0, 255, 0)
        self.color_danger = (255, 0, 0)

        # OpenGL setup for UI rendering
        if self.ctx:
            self._setup_gl_ui()

    def _setup_gl_ui(self):
        """Setup OpenGL resources for UI rendering."""
        # Create texture for UI
        self.ui_texture = self.ctx.texture((self.width, self.height), 4)
        self.ui_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

        # Create fullscreen quad
        vertices = np.array([
            # Position (x, y)  UV (u, v)
            -1.0, -1.0,       0.0, 0.0,
             1.0, -1.0,       1.0, 0.0,
            -1.0,  1.0,       0.0, 1.0,
             1.0,  1.0,       1.0, 1.0,
        ], dtype='f4')

        self.ui_vbo = self.ctx.buffer(vertices.tobytes())

        # Shader for UI rendering
        ui_vertex_shader = """
        #version 330
        in vec2 in_position;
        in vec2 in_uv;
        out vec2 uv;

        void main() {
            gl_Position = vec4(in_position, 0.0, 1.0);
            uv = in_uv;
        }
        """

        ui_fragment_shader = """
        #version 330
        uniform sampler2D ui_texture;
        in vec2 uv;
        out vec4 fragColor;

        void main() {
            fragColor = texture(ui_texture, uv);
        }
        """

        self.ui_program = self.ctx.program(
            vertex_shader=ui_vertex_shader,
            fragment_shader=ui_fragment_shader
        )

        self.ui_vao = self.ctx.vertex_array(
            self.ui_program,
            [(self.ui_vbo, '2f 2f', 'in_position', 'in_uv')]
        )

    def clear(self):
        """Clear the UI surface."""
        self.surface.fill((0, 0, 0, 0))

    def draw_text(self, text, x, y, font='medium', color=None, center=False):
        """
        Draw text on UI.

        Args:
            text: Text to draw
            x, y: Position
            font: 'small', 'medium', or 'large'
            color: Text color (default white)
            center: Center the text at position
        """
        if color is None:
            color = self.color_text

        if font == 'small':
            font_obj = self.font_small
        elif font == 'large':
            font_obj = self.font_large
        else:
            font_obj = self.font_medium

        text_surface = font_obj.render(text, True, color)
        if center:
            rect = text_surface.get_rect(center=(x, y))
            self.surface.blit(text_surface, rect)
        else:
            self.surface.blit(text_surface, (x, y))

    def draw_box(self, x, y, width, height, color=None, alpha=180):
        """Draw a semi-transparent box."""
        if color is None:
            color = (0, 0, 0)

        box_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        box_surface.fill((*color, alpha))
        self.surface.blit(box_surface, (x, y))

    def draw_pause_menu(self):
        """Draw pause menu."""
        center_x = self.width // 2
        center_y = self.height // 2

        # Draw background overlay
        self.draw_box(0, 0, self.width, self.height, color=(0, 0, 0), alpha=150)

        # Draw menu box
        menu_width = 400
        menu_height = 300
        menu_x = center_x - menu_width // 2
        menu_y = center_y - menu_height // 2
        self.draw_box(menu_x, menu_y, menu_width, menu_height, color=(20, 20, 40), alpha=220)

        # Draw title
        self.draw_text("PAUSED", center_x, center_y - 80, font='large', center=True)

        # Draw menu options
        self.draw_text("ESC - Resume", center_x, center_y - 30, center=True)
        self.draw_text("I - Inventory", center_x, center_y, center=True)
        self.draw_text("C - Character/Equipment", center_x, center_y + 30, center=True)
        self.draw_text("M - Map", center_x, center_y + 60, center=True)
        self.draw_text("J - Journal", center_x, center_y + 90, center=True)

    def draw_damage_numbers(self, damage_numbers: List['DamageNumber'], view_matrix, projection_matrix):
        """
        Draw floating damage numbers in 3D space.

        Args:
            damage_numbers: List of active damage numbers
            view_matrix: Camera view matrix
            projection_matrix: Camera projection matrix
        """
        for num in damage_numbers:
            # Project 3D position to screen space
            pos_4d = projection_matrix * view_matrix * glm.vec4(num.position, 1.0)

            # Skip if behind camera
            if pos_4d.w <= 0:
                continue

            # Perspective divide
            ndc = glm.vec3(pos_4d) / pos_4d.w

            # Convert to screen coordinates
            screen_x = int((ndc.x + 1.0) * 0.5 * self.width)
            screen_y = int((1.0 - ndc.y) * 0.5 * self.height)  # Flip Y

            # Skip if off-screen
            if not (0 <= screen_x < self.width and 0 <= screen_y < self.height):
                continue

            # Get alpha for fading
            alpha = int(num.get_alpha() * 255)
            if alpha <= 0:
                continue

            # Choose font based on critical hit
            font = self.font_large if num.critical else self.font_medium

            # Create text surface with color and alpha
            color_with_alpha = (*[int(c * 255) for c in num.color], alpha)
            text = num.get_text()

            try:
                text_surface = font.render(text, True, num.color[:3])
                # Apply alpha
                text_surface.set_alpha(alpha)

                # Center the text
                text_rect = text_surface.get_rect(center=(screen_x, screen_y))

                # Draw outline for better visibility (critical hits only)
                if num.critical:
                    outline_color = (0, 0, 0)
                    for offset_x in [-2, 0, 2]:
                        for offset_y in [-2, 0, 2]:
                            if offset_x != 0 or offset_y != 0:
                                outline_surface = font.render(text, True, outline_color)
                                outline_surface.set_alpha(alpha)
                                outline_rect = outline_surface.get_rect(
                                    center=(screen_x + offset_x, screen_y + offset_y)
                                )
                                self.surface.blit(outline_surface, outline_rect)

                self.surface.blit(text_surface, text_rect)
            except pygame.error as e:
                logger.warning(f"Failed to render damage number: {e}")
            except (AttributeError, TypeError, ValueError) as e:
                logger.warning(f"Invalid damage number data: {e}")

    def draw_bar(self, x, y, width, height, current, maximum, color, bg_color=(50, 50, 50), border_color=(255, 255, 255)):
        """Draw a stat bar (health, stamina, mana)."""
        # Draw background
        pygame.draw.rect(self.surface, bg_color, (x, y, width, height))

        # Draw filled portion
        fill_width = int((current / maximum) * width) if maximum > 0 else 0
        if fill_width > 0:
            pygame.draw.rect(self.surface, color, (x, y, fill_width, height))

        # Draw border
        pygame.draw.rect(self.surface, border_color, (x, y, width, height), 2)

    def _draw_boss_health_bar(self, boss):
        """
        Draw a prominent boss health bar at the top of the screen.

        Args:
            boss: Boss enemy object
        """
        # Boss bar dimensions (larger and more prominent)
        bar_width = 600
        bar_height = 40
        bar_x = (self.width - bar_width) // 2
        bar_y = 30

        # Draw background box
        box_padding = 10
        self.draw_box(bar_x - box_padding, bar_y - box_padding - 35,
                     bar_width + 2 * box_padding, bar_height + 2 * box_padding + 35,
                     color=(30, 20, 20), alpha=220)

        # Draw boss name
        self.draw_text(boss.name, bar_x + bar_width // 2, bar_y - 25,
                      font='large', center=True, color=(255, 200, 50))

        # Draw health bar with boss-specific color
        boss_color = (150, 50, 50)  # Dark red for bosses
        if hasattr(boss, 'color'):
            # Use boss's color but darker/more saturated
            boss_color = (
                int(boss.color.x * 200),
                int(boss.color.y * 100),
                int(boss.color.z * 100)
            )

        self.draw_bar(bar_x, bar_y, bar_width, bar_height,
                     boss.stats.current_health, boss.stats.max_health,
                     boss_color, bg_color=(20, 20, 20), border_color=(255, 215, 0))

        # Draw health text
        health_text = f"{int(boss.stats.current_health)} / {int(boss.stats.max_health)}"
        self.draw_text(health_text, bar_x + bar_width // 2, bar_y + 8,
                      font='medium', center=True, color=(255, 255, 255))

    def draw_hud(self, player, inventory, interaction_target=None, culled_count=0, total_entities=0, nearby_boss=None, quest_manager=None):
        """
        Draw heads-up display with waypoint indicators.

        Args:
            player: Player object
            inventory: Inventory object
            interaction_target: Object player is looking at (optional)
            culled_count: Number of culled entities
            total_entities: Total number of entities
            nearby_boss: Boss enemy if one is nearby (optional)
            quest_manager: QuestManager for waypoint display (optional)
        """
        # Draw boss health bar if fighting a boss
        if nearby_boss:
            self._draw_boss_health_bar(nearby_boss)
        # Draw position (debug)
        pos_text = f"Pos: ({player.position.x:.1f}, {player.position.y:.1f}, {player.position.z:.1f})"
        self.draw_text(pos_text, 10, 10, font='small', color=(200, 200, 200))

        # Draw inventory count
        inv_text = f"Items: {inventory.get_total_item_count()}"
        self.draw_text(inv_text, 10, 35, font='small', color=(255, 255, 150))

        # Draw culling stats (debug)
        if total_entities > 0:
            rendered = total_entities - culled_count
            culling_text = f"Rendering: {rendered}/{total_entities} (Culled: {culled_count})"
            self.draw_text(culling_text, 10, 60, font='small', color=(150, 200, 255))

        # Draw stat bars (bottom left)
        bar_x = 20
        bar_y = self.height - 120
        bar_width = 200
        bar_height = 20
        bar_spacing = 30

        # Health bar
        self.draw_text("Health", bar_x, bar_y - 20, font='small', color=(255, 100, 100))
        self.draw_bar(bar_x, bar_y, bar_width, bar_height,
                     player.stats.current_health, player.stats.max_health, (200, 50, 50))
        health_text = f"{int(player.stats.current_health)}/{int(player.stats.max_health)}"
        self.draw_text(health_text, bar_x + bar_width + 10, bar_y + 3, font='small', color=(255, 255, 255))

        # Stamina bar
        bar_y += bar_spacing
        self.draw_text("Stamina", bar_x, bar_y - 20, font='small', color=(100, 255, 100))
        self.draw_bar(bar_x, bar_y, bar_width, bar_height,
                     player.stats.current_stamina, player.stats.max_stamina, (50, 200, 50))
        stamina_text = f"{int(player.stats.current_stamina)}/{int(player.stats.max_stamina)}"
        self.draw_text(stamina_text, bar_x + bar_width + 10, bar_y + 3, font='small', color=(255, 255, 255))

        # Mana bar
        bar_y += bar_spacing
        self.draw_text("Mana", bar_x, bar_y - 20, font='small', color=(100, 100, 255))
        self.draw_bar(bar_x, bar_y, bar_width, bar_height,
                     player.spell_caster.current_mana, player.spell_caster.max_mana, (50, 50, 200))
        mana_text = f"{int(player.spell_caster.current_mana)}/{int(player.spell_caster.max_mana)}"
        self.draw_text(mana_text, bar_x + bar_width + 10, bar_y + 3, font='small', color=(255, 255, 255))

        # XP bar
        bar_y += bar_spacing
        current_xp_in_level = player.progression.xp - (player.progression.xp - int(player.progression.xp_progress * (player.progression.xp_to_next_level / (1 - player.progression.xp_progress)) if player.progression.xp_progress < 1 else 0))
        xp_needed_for_level = player.progression.xp_to_next_level + current_xp_in_level

        # Simpler: just use xp_progress as a percentage
        xp_label = "XP" if player.progression.level < 30 else "XP (MAX)"
        self.draw_text(xp_label, bar_x, bar_y - 20, font='small', color=(255, 215, 0))
        self.draw_bar(bar_x, bar_y, bar_width, bar_height,
                     player.progression.xp_progress, 1.0, (200, 150, 0))
        xp_text = f"Level {player.progression.level}" if player.progression.level >= 30 else f"Level {player.progression.level} ({int(player.progression.xp_progress * 100)}%)"
        self.draw_text(xp_text, bar_x + bar_width + 10, bar_y + 3, font='small', color=(255, 255, 255))

        # Draw spell slots (bottom center)
        self._draw_spell_slots(player)

        # Draw crosshair
        center_x = self.width // 2
        center_y = self.height // 2
        crosshair_size = 10
        pygame.draw.line(self.surface, self.color_text,
                        (center_x - crosshair_size, center_y),
                        (center_x + crosshair_size, center_y), 2)
        pygame.draw.line(self.surface, self.color_text,
                        (center_x, center_y - crosshair_size),
                        (center_x, center_y + crosshair_size), 2)

        # Draw interaction prompt
        if interaction_target:
            prompt = f"[E] {interaction_target.name}"
            if hasattr(interaction_target, 'description'):
                prompt = f"[E] {interaction_target.description}"

            self.draw_text(prompt, center_x, center_y + 40,
                          font='medium', center=True, color=self.color_highlight)

        # Draw quest waypoint indicator (top right)
        if quest_manager:
            waypoints = quest_manager.get_active_waypoints()
            if waypoints:
                # Find nearest waypoint
                player_x, player_z = player.position.x, player.position.z
                nearest = min(waypoints, key=lambda w: w.distance_to(player_x, player_z))

                # Draw waypoint info (top right corner)
                info_x = self.width - 10
                info_y = 80
                distance = nearest.distance_to(player_x, player_z)

                self.draw_text(f"Quest: {nearest.name}", info_x, info_y,
                              font='small', color=nearest.color, center=False)
                self.draw_text(f"Distance: {distance:.0f}m", info_x, info_y + 20,
                              font='small', color=(200, 200, 200), center=False)

    def _draw_spell_slots(self, player):
        """Draw spell quick slots at bottom of screen."""
        slot_size = 50
        slot_spacing = 10
        total_width = (slot_size + slot_spacing) * 8 - slot_spacing
        start_x = (self.width - total_width) // 2
        slot_y = self.height - 80

        for i in range(8):
            slot_x = start_x + i * (slot_size + slot_spacing)

            # Draw slot background
            slot_bg_color = (40, 40, 60) if i < len(player.spell_caster.equipped_spells) else (30, 30, 30)
            pygame.draw.rect(self.surface, slot_bg_color, (slot_x, slot_y, slot_size, slot_size))
            pygame.draw.rect(self.surface, (100, 100, 150), (slot_x, slot_y, slot_size, slot_size), 2)

            # Draw slot number
            self.draw_text(str(i + 1), slot_x + 5, slot_y + 5, font='small', color=(150, 150, 150))

            # Draw spell if equipped
            spell = player.spell_caster.equipped_spells[i]
            if spell:
                # Draw spell icon (first letter of spell name for now)
                spell_initial = spell.name[0]
                self.draw_text(spell_initial, slot_x + slot_size // 2, slot_y + slot_size // 2 - 10,
                             font='large', center=True, color=(200, 200, 255))

                # Check if spell is on cooldown
                if spell.spell_type in player.spell_caster.spell_cooldowns:
                    cooldown_remaining = player.spell_caster.spell_cooldowns[spell.spell_type]
                    if cooldown_remaining > 0:
                        # Draw cooldown overlay
                        cooldown_height = int((cooldown_remaining / spell.get_cooldown()) * slot_size)
                        pygame.draw.rect(self.surface, (0, 0, 0, 180),
                                       (slot_x, slot_y, slot_size, cooldown_height))
                        # Draw cooldown timer
                        self.draw_text(f"{cooldown_remaining:.1f}", slot_x + slot_size // 2,
                                     slot_y + slot_size // 2, font='small', center=True, color=(255, 100, 100))

    def draw_inventory(self, inventory):
        """Draw inventory screen."""
        center_x = self.width // 2
        center_y = self.height // 2

        # Draw background
        self.draw_box(0, 0, self.width, self.height, alpha=180)

        # Draw inventory box
        inv_width = 500
        inv_height = 400
        inv_x = center_x - inv_width // 2
        inv_y = center_y - inv_height // 2
        self.draw_box(inv_x, inv_y, inv_width, inv_height, color=(40, 30, 20), alpha=240)

        # Title
        self.draw_text("INVENTORY", center_x, inv_y + 30, font='large', center=True)

        # Item counts
        y_offset = inv_y + 100
        self.draw_text(f"Total Items: {inventory.get_total_item_count()}", center_x, y_offset, center=True)

        # Equipment items
        if inventory.equipment_items:
            y_offset += 40
            self.draw_text(f"Equipment ({len(inventory.equipment_items)}):", center_x, y_offset, center=True, color=self.color_highlight)
            y_offset += 30
            for item in inventory.equipment_items[:5]:  # Show first 5
                rarity = item.rarity.name
                self.draw_text(f"- [{rarity}] {item.name}", center_x, y_offset, font='small', center=True)
                y_offset += 25
            if len(inventory.equipment_items) > 5:
                self.draw_text(f"... and {len(inventory.equipment_items) - 5} more", center_x, y_offset, font='small', center=True, color=(150, 150, 150))
                y_offset += 25

        # Consumables
        if inventory.consumables:
            y_offset += 20
            self.draw_text(f"Consumables ({len(inventory.consumables)}):", center_x, y_offset, center=True, color=self.color_success)
            y_offset += 30
            for item in inventory.consumables[:5]:  # Show first 5
                self.draw_text(f"- {item}", center_x, y_offset, font='small', center=True)
                y_offset += 25

        # Key items
        if inventory.key_items:
            y_offset += 20
            self.draw_text("Key Items:", center_x, y_offset, center=True, color=(255, 215, 0))
            y_offset += 30
            for item in inventory.key_items:
                self.draw_text(f"- {item}", center_x, y_offset, font='small', center=True)
                y_offset += 25

        # Close prompt
        self.draw_text("Press I or ESC to close | Press C for Character", center_x, inv_y + inv_height - 40,
                      font='small', center=True, color=(150, 150, 150))

    def draw_equipment(self, player, inventory):
        """
        Draw equipment screen showing equipped items and stats.

        Args:
            player: Player object with equipment and stats
            inventory: Inventory object with equipment items
        """
        center_x = self.width // 2
        center_y = self.height // 2

        # Draw background
        self.draw_box(0, 0, self.width, self.height, alpha=180)

        # Draw equipment box
        equip_width = 700
        equip_height = 500
        equip_x = center_x - equip_width // 2
        equip_y = center_y - equip_height // 2
        self.draw_box(equip_x, equip_y, equip_width, equip_height, color=(40, 35, 50), alpha=240)

        # Title
        self.draw_text("EQUIPMENT", center_x, equip_y + 30, font='large', center=True)

        # Player stats (left side)
        left_x = equip_x + 30
        y_offset = equip_y + 80
        self.draw_text("Character Stats:", left_x, y_offset, font='medium', color=self.color_highlight)
        y_offset += 35

        # Display stats
        stats = [
            f"Level: {player.progression.level}",
            f"XP: {player.progression.xp}/{player.progression.xp + player.progression.xp_to_next_level}",
            f"Health: {player.stats.current_health:.0f}/{player.stats.max_health:.0f}",
            f"Stamina: {player.stats.current_stamina:.0f}/{player.stats.max_stamina:.0f}",
            f"Damage: {player.stats.base_damage:.0f}",
            f"Defense: {player.stats.defense:.0f}",
            f"Power Level: {player.get_power_level()}"
        ]

        for stat_text in stats:
            self.draw_text(stat_text, left_x, y_offset, font='small')
            y_offset += 25

        # Equipped items (right side)
        right_x = center_x + 50
        y_offset = equip_y + 80
        self.draw_text("Equipped Items:", right_x, y_offset, font='medium', color=self.color_highlight)
        y_offset += 35

        equipped_items = player.equipment.get_all_equipped()

        if equipped_items:
            for slot, item in equipped_items.items():
                # Slot name
                slot_name = slot.name.title()
                self.draw_text(f"{slot_name}:", right_x, y_offset, font='small', color=(200, 200, 255))
                y_offset += 20

                # Item name and rarity
                rarity_colors = {
                    'COMMON': (180, 180, 180),
                    'UNCOMMON': (0, 255, 0),
                    'RARE': (100, 150, 255),
                    'EPIC': (200, 100, 255),
                    'LEGENDARY': (255, 165, 0)
                }
                rarity = item.rarity.name
                rarity_color = rarity_colors.get(rarity, self.color_text)

                self.draw_text(f"  [{rarity}] {item.name}", right_x, y_offset, font='small', color=rarity_color)
                y_offset += 20

                # Stats
                stats_text = item.get_stat_summary()
                self.draw_text(f"  {stats_text}", right_x, y_offset, font='small', color=(150, 150, 150))
                y_offset += 30
        else:
            self.draw_text("No items equipped", right_x, y_offset, font='small', color=(150, 150, 150))

        # Inventory items count
        y_offset = equip_y + equip_height - 80
        inv_count = inventory.get_equipment_count()
        self.draw_text(f"Equipment in Inventory: {inv_count}", center_x, y_offset, font='small', center=True, color=self.color_success)

        # Controls
        y_offset = equip_y + equip_height - 40
        self.draw_text("Press C or ESC to close", center_x, y_offset, font='small', center=True, color=(150, 150, 150))

    def draw_crafting(self, discovered_recipes, crafting_manager, player, selected_index=0):
        """
        Draw crafting screen showing available recipes.

        Args:
            discovered_recipes: List of discovered recipes (cached for performance)
            crafting_manager: CraftingManager instance
            player: Player object with inventory and level
            selected_index: Index of currently selected recipe
        """
        center_x = self.width // 2
        center_y = self.height // 2

        # Draw background
        self.draw_box(0, 0, self.width, self.height, alpha=180)

        # Draw crafting box
        craft_width = 800
        craft_height = 550
        craft_x = center_x - craft_width // 2
        craft_y = center_y - craft_height // 2
        self.draw_box(craft_x, craft_y, craft_width, craft_height, color=(35, 40, 45), alpha=240)

        # Title
        self.draw_text("CRAFTING", center_x, craft_y + 30, font='large', center=True)

        if not discovered_recipes:
            self.draw_text("No recipes discovered yet", center_x, center_y, font='medium', center=True, color=(150, 150, 150))
        else:
            # Display recipes in two columns
            left_x = craft_x + 30
            right_x = craft_x + craft_width // 2 + 20
            y_offset = craft_y + 80
            column_height = 400
            recipes_per_column = 4

            for i, recipe in enumerate(discovered_recipes[:8]):  # Show first 8 recipes
                # Alternate columns
                x_pos = left_x if i < recipes_per_column else right_x
                y_pos = y_offset + (i % recipes_per_column) * 100

                # Recipe box (highlight if selected)
                box_width = 350
                box_height = 90
                is_selected = (i == selected_index)
                box_color = (80, 90, 100) if is_selected else (50, 55, 60)
                box_alpha = 240 if is_selected else 200
                self.draw_box(x_pos, y_pos, box_width, box_height, color=box_color, alpha=box_alpha)

                # Selection indicator
                if is_selected:
                    self.draw_text(">", x_pos - 15, y_pos + box_height // 2 - 10, font='medium', color=self.color_highlight)

                # Recipe name and rarity
                rarity_colors = {
                    'COMMON': (180, 180, 180),
                    'UNCOMMON': (0, 255, 0),
                    'RARE': (100, 150, 255),
                    'EPIC': (200, 100, 255),
                    'LEGENDARY': (255, 165, 0)
                }
                rarity_color = rarity_colors.get(recipe.rarity.name, self.color_text)
                self.draw_text(f"[{recipe.rarity.name}] {recipe.name}", x_pos + 10, y_pos + 10, font='small', color=rarity_color)

                # Materials required
                y_mat = y_pos + 30
                materials_text = "Materials: "
                for mat_id, qty in recipe.required_materials:
                    available = player.inventory.get_item_count(mat_id)
                    mat_color = self.color_success if available >= qty else self.color_error
                    materials_text += f"{mat_id} ({available}/{qty}), "
                materials_text = materials_text.rstrip(", ")
                self.draw_text(materials_text[:50], x_pos + 10, y_mat, font='tiny', color=(200, 200, 200))

                # Can craft indicator
                can_craft, reason = crafting_manager.can_craft(recipe.recipe_id, player.inventory, player.progression.level)
                if can_craft:
                    self.draw_text("CAN CRAFT", x_pos + box_width - 80, y_pos + 60, font='tiny', color=self.color_success)
                else:
                    self.draw_text(reason[:30], x_pos + 10, y_pos + 60, font='tiny', color=self.color_error)

        # Instructions
        y_offset = craft_y + craft_height - 80
        self.draw_text("UP/DOWN: Select Recipe  |  ENTER/SPACE: Craft Item", center_x, y_offset, font='small', center=True, color=self.color_highlight)
        y_offset += 25
        self.draw_text("Materials consumed on craft - ensure you have enough!", center_x, y_offset, font='small', center=True, color=(150, 150, 150))
        y_offset += 25
        self.draw_text("Press V or ESC to close", center_x, y_offset, font='small', center=True, color=(150, 150, 150))

    def draw_journal(self, journal):
        """Draw journal screen with objectives and lore."""
        center_x = self.width // 2
        center_y = self.height // 2

        # Background
        self.draw_box(0, 0, self.width, self.height, alpha=200)

        # Journal box
        journal_width = 700
        journal_height = 500
        journal_x = center_x - journal_width // 2
        journal_y = center_y - journal_height // 2
        self.draw_box(journal_x, journal_y, journal_width, journal_height,
                     color=(30, 25, 20), alpha=240)

        # Title
        self.draw_text("JOURNAL", center_x, journal_y - 40, font='large', center=True)

        # Active objectives section
        y_offset = journal_y + 30
        self.draw_text("Active Objectives:", journal_x + 20, y_offset,
                      font='medium', color=self.color_highlight)
        y_offset += 35

        active_objectives = journal.get_active_objectives()
        if active_objectives:
            for obj in active_objectives[:3]:  # Show first 3
                # Objective title
                self.draw_text(f"• {obj.title}", journal_x + 30, y_offset, font='small')
                y_offset += 20

                # Progress bar if has sub-tasks
                if obj.sub_tasks:
                    progress_text = f"  Progress: {obj.progress}/{obj.progress_max}"
                    self.draw_text(progress_text, journal_x + 40, y_offset,
                                  font='small', color=(200, 200, 200))
                    y_offset += 25
                else:
                    y_offset += 5
        else:
            self.draw_text("No active objectives", journal_x + 40, y_offset,
                          font='small', color=(150, 150, 150))
            y_offset += 25

        # Discovered lore section
        y_offset += 20
        self.draw_text("Lore Entries:", journal_x + 20, y_offset,
                      font='medium', color=self.color_success)
        y_offset += 35

        discovered_lore = journal.get_discovered_lore()
        if discovered_lore:
            # Group by category
            categories = journal.get_lore_categories()
            for category in categories[:2]:  # Show first 2 categories
                self.draw_text(f"{category}:", journal_x + 30, y_offset,
                              font='small', color=self.color_highlight)
                y_offset += 20

                entries = journal.get_lore_by_category(category)
                for entry in entries[:3]:  # Show first 3 per category
                    self.draw_text(f"  • {entry.title}", journal_x + 40, y_offset,
                                  font='small')
                    y_offset += 20
                y_offset += 10
        else:
            self.draw_text("No lore discovered yet...", journal_x + 40, y_offset,
                          font='small', color=(150, 150, 150))
            y_offset += 25

        # Stats section
        y_offset = journal_y + journal_height - 80
        completed_count = len(journal.get_completed_objectives())
        total_objectives = len(journal.objectives)  # All objectives (including hidden)
        lore_count = len(discovered_lore)

        self.draw_text(f"Objectives Completed: {completed_count}",
                      journal_x + 20, y_offset, font='small', color=(200, 200, 150))
        y_offset += 20
        self.draw_text(f"Lore Discovered: {lore_count}",
                      journal_x + 20, y_offset, font='small', color=(200, 200, 150))

        # Close prompt
        self.draw_text("Press J or ESC to close", center_x, journal_y + journal_height + 20,
                      font='small', center=True, color=(150, 150, 150))

    def draw_map(self, player_position, chunk_manager=None, quest_manager=None):
        """
        Draw simple map view with waypoints.

        Args:
            player_position: Player position
            chunk_manager: ChunkManager for terrain (optional)
            quest_manager: QuestManager for waypoints (optional)
        """
        center_x = self.width // 2
        center_y = self.height // 2

        # Background
        self.draw_box(0, 0, self.width, self.height, alpha=200)

        # Map box
        map_size = 400
        map_x = center_x - map_size // 2
        map_y = center_y - map_size // 2
        self.draw_box(map_x, map_y, map_size, map_size, color=(30, 50, 30), alpha=240)

        # Title
        self.draw_text("MAP", center_x, map_y - 40, font='large', center=True)

        # Draw simple terrain representation if available
        if chunk_manager:
            # Simple heightmap visualization
            grid_size = 20
            cell_size = map_size // grid_size
            map_range = 100  # Show 100x100 units around player

            for y in range(grid_size):
                for x in range(grid_size):
                    # Sample world position relative to player
                    world_x = player_position.x + (x - grid_size // 2) * map_range / grid_size
                    world_z = player_position.z + (y - grid_size // 2) * map_range / grid_size

                    # Get height at this position
                    height = chunk_manager.get_height_at(world_x, world_z)

                    # Color based on height
                    color_val = int(min(max(height / 10.0, 0), 1) * 255)
                    color = (color_val // 3, color_val // 2, color_val // 4)

                    px = map_x + x * cell_size
                    py = map_y + y * cell_size
                    pygame.draw.rect(self.surface, color, (px, py, cell_size, cell_size))

        # Draw player position at center of map
        center_px = map_x + map_size // 2
        center_py = map_y + map_size // 2
        pygame.draw.circle(self.surface, (255, 0, 0), (center_px, center_py), 5)

        # Draw quest waypoints
        if quest_manager:
            waypoints = quest_manager.get_active_waypoints()
            map_range = 100  # Show 100x100 units around player

            for waypoint in waypoints:
                wx, _, wz = waypoint.position

                # Calculate relative position to player
                rel_x = wx - player_position.x
                rel_z = wz - player_position.z

                # Check if waypoint is within map range
                if abs(rel_x) < map_range and abs(rel_z) < map_range:
                    # Convert to screen coordinates
                    screen_x = center_px + int((rel_x / map_range) * (map_size / 2))
                    screen_y = center_py + int((rel_z / map_range) * (map_size / 2))

                    # Draw waypoint marker
                    pygame.draw.circle(self.surface, waypoint.color, (screen_x, screen_y), 6)
                    pygame.draw.circle(self.surface, (255, 255, 255), (screen_x, screen_y), 6, 2)

                    # Draw waypoint name nearby
                    self.draw_text(waypoint.name, screen_x, screen_y - 15,
                                  font='tiny', center=True, color=waypoint.color)

        # Close prompt
        self.draw_text("Press M or ESC to close", center_x, map_y + map_size + 30,
                      font='small', center=True, color=(150, 150, 150))

    def draw_minimap(self, player_position, player_rotation_y, chunk_manager=None, quest_manager=None):
        """
        Draw mini-map in corner of screen.

        Args:
            player_position: Player position (glm.vec3)
            player_rotation_y: Player Y rotation in degrees
            chunk_manager: ChunkManager for terrain (optional)
            quest_manager: QuestManager for waypoints (optional)
        """
        if not self.minimap_enabled:
            return

        # Calculate mini-map position based on setting
        margin = 20
        if self.minimap_position == 'top-right':
            map_x = self.width - self.minimap_size - margin
            map_y = margin
        elif self.minimap_position == 'top-left':
            map_x = margin
            map_y = margin
        elif self.minimap_position == 'bottom-right':
            map_x = self.width - self.minimap_size - margin
            map_y = self.height - self.minimap_size - margin
        else:  # bottom-left
            map_x = margin
            map_y = self.height - self.minimap_size - margin

        # Semi-transparent background
        self.draw_box(map_x, map_y, self.minimap_size, self.minimap_size,
                     color=(20, 30, 20), alpha=self.minimap_opacity)

        # Border
        pygame.draw.rect(self.surface, (100, 120, 100),
                        (map_x, map_y, self.minimap_size, self.minimap_size), 2)

        # Calculate map range based on zoom
        base_range = 50  # Base range in units
        map_range = base_range / self.minimap_zoom

        center_px = map_x + self.minimap_size // 2
        center_py = map_y + self.minimap_size // 2

        # Draw terrain if available
        if chunk_manager:
            grid_size = 15
            cell_size = self.minimap_size // grid_size

            for y in range(grid_size):
                for x in range(grid_size):
                    # Sample world position relative to player
                    world_x = player_position.x + (x - grid_size // 2) * map_range / grid_size
                    world_z = player_position.z + (y - grid_size // 2) * map_range / grid_size

                    # Get height at this position
                    height = chunk_manager.get_height_at(world_x, world_z)

                    # Color based on height
                    color_val = int(min(max(height / 10.0, 0), 1) * 200)
                    color = (color_val // 3, color_val // 2, color_val // 4)

                    px = map_x + x * cell_size
                    py = map_y + y * cell_size
                    pygame.draw.rect(self.surface, color, (px, py, cell_size, cell_size))

        # Draw quest waypoints
        if quest_manager:
            waypoints = quest_manager.get_active_waypoints()

            for waypoint in waypoints:
                wx, _, wz = waypoint.position

                # Calculate relative position to player
                rel_x = wx - player_position.x
                rel_z = wz - player_position.z

                # Check if waypoint is within map range
                if abs(rel_x) < map_range and abs(rel_z) < map_range:
                    # Convert to screen coordinates
                    screen_x = center_px + int((rel_x / map_range) * (self.minimap_size / 2))
                    screen_y = center_py + int((rel_z / map_range) * (self.minimap_size / 2))

                    # Draw waypoint marker (smaller than full map)
                    pygame.draw.circle(self.surface, waypoint.color, (screen_x, screen_y), 4)
                    pygame.draw.circle(self.surface, (255, 255, 255), (screen_x, screen_y), 4, 1)

        # Draw player position and direction at center
        # Player direction indicator (triangle pointing in look direction)
        import math
        rotation_rad = math.radians(-player_rotation_y)
        arrow_length = 8

        # Calculate arrow points
        tip_x = center_px + int(math.sin(rotation_rad) * arrow_length)
        tip_y = center_py + int(math.cos(rotation_rad) * arrow_length)

        # Side points for triangle
        left_angle = rotation_rad - math.radians(140)
        right_angle = rotation_rad + math.radians(140)
        side_length = 6

        left_x = center_px + int(math.sin(left_angle) * side_length)
        left_y = center_py + int(math.cos(left_angle) * side_length)
        right_x = center_px + int(math.sin(right_angle) * side_length)
        right_y = center_py + int(math.cos(right_angle) * side_length)

        # Draw filled triangle for player
        pygame.draw.polygon(self.surface, (255, 50, 50),
                           [(tip_x, tip_y), (left_x, left_y), (right_x, right_y)])
        pygame.draw.polygon(self.surface, (255, 200, 200),
                           [(tip_x, tip_y), (left_x, left_y), (right_x, right_y)], 1)

        # Zoom indicator text (small)
        zoom_text = f"{self.minimap_zoom:.1f}x"
        self.draw_text(zoom_text, map_x + self.minimap_size - 5, map_y + 5,
                      font='tiny', color=(150, 150, 150))

    def toggle_minimap(self):
        """Toggle mini-map visibility."""
        self.minimap_enabled = not self.minimap_enabled
        return self.minimap_enabled

    def zoom_minimap(self, delta):
        """
        Adjust mini-map zoom level.

        Args:
            delta: Zoom delta (positive = zoom in, negative = zoom out)
        """
        self.minimap_zoom = max(0.5, min(3.0, self.minimap_zoom + delta * 0.25))
        return self.minimap_zoom

    def cycle_minimap_position(self):
        """Cycle through mini-map corner positions."""
        positions = ['top-right', 'top-left', 'bottom-left', 'bottom-right']
        current_index = positions.index(self.minimap_position)
        self.minimap_position = positions[(current_index + 1) % len(positions)]
        return self.minimap_position

    def draw_dialogue(self, dialogue_node, npc_name):
        """
        Draw dialogue UI (Phase 5).

        Args:
            dialogue_node: Current DialogueNode
            npc_name: Name of NPC speaking
        """
        from game.dialogue import DialogueNodeType

        center_x = self.width // 2
        center_y = self.height // 2

        # Background box
        box_width = config.UI_DIALOGUE_BOX_WIDTH
        box_height = config.UI_DIALOGUE_BOX_HEIGHT
        box_x = center_x - box_width // 2
        box_y = self.height - box_height - config.UI_DIALOGUE_BOX_MARGIN

        # Draw dialogue box
        pygame.draw.rect(self.surface, self.color_bg, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.surface, self.color_text, (box_x, box_y, box_width, box_height), 3)

        # Draw speaker name
        self.draw_text(dialogue_node.speaker, box_x + 20, box_y + 10, font='medium', color=self.color_highlight)

        # Draw dialogue text (wrap if needed)
        text = dialogue_node.text
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            test_surf = self.font_small.render(test_line, True, self.color_text)
            if test_surf.get_width() < box_width - 40:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        if current_line:
            lines.append(current_line)

        # Draw text lines
        y_offset = box_y + 50
        for line in lines[:config.UI_DIALOGUE_MAX_LINES]:
            self.draw_text(line, box_x + 20, y_offset, font='small')
            y_offset += config.UI_DIALOGUE_LINE_HEIGHT

        # Draw choices if this is a choice node
        if dialogue_node.node_type == DialogueNodeType.CHOICE:
            choice_y = box_y + box_height + 20
            for i, (choice_text, _) in enumerate(dialogue_node.choices):
                choice_color = self.color_highlight if i == 0 else self.color_text
                self.draw_text(f"{i+1}. {choice_text}", box_x + 20, choice_y, font='small', color=choice_color)
                choice_y += 30
            self.draw_text("Press 1-4 to choose", center_x, choice_y + 10, font='small', center=True, color=(150, 150, 150))
        else:
            # Prompt to continue
            self.draw_text("Press SPACE or ENTER to continue", center_x, box_y + box_height + 20,
                          font='small', center=True, color=(150, 150, 150))

        # ESC to exit
        self.draw_text("Press ESC to exit dialogue", 20, 20, font='small', color=(150, 150, 150))

    def draw_quest_log(self, quest_manager):
        """
        Draw quest log UI (Phase 5).

        Args:
            quest_manager: QuestManager instance
        """
        center_x = self.width // 2
        y = 80

        # Title
        self.draw_text("Quest Log", center_x, y, font='large', center=True, color=self.color_highlight)
        y += 60

        # Active quests
        active_quests = quest_manager.get_active_quests()
        if active_quests:
            self.draw_text("Active Quests:", 50, y, font='medium', color=self.color_success)
            y += 40

            for quest in active_quests:
                # Quest title
                self.draw_text(f"• {quest.title}", 70, y, font='small')
                y += 25

                # Current objective
                obj = quest.get_current_objective()
                if obj:
                    progress_text = obj.get_progress_text()
                    self.draw_text(f"  {obj.description} [{progress_text}]", 90, y, font='small', color=(200, 200, 200))
                    y += 25

                y += 10  # Space between quests
        else:
            self.draw_text("No active quests", 70, y, font='small', color=(150, 150, 150))
            y += 40

        # Completed quests
        y += 20
        completed_quests = quest_manager.get_completed_quests()
        if completed_quests:
            self.draw_text("Completed Quests:", 50, y, font='medium', color=(100, 255, 100))
            y += 40

            for quest in completed_quests[:5]:  # Show up to 5
                self.draw_text(f"✓ {quest.title}", 70, y, font='small', color=(100, 255, 100))
                y += 30

        # Controls
        self.draw_text("Press Q or ESC to close", center_x, self.height - 50,
                      font='small', center=True, color=(150, 150, 150))

    def draw_save_menu(self, save_system, selected_slot=1):
        """
        Draw save game menu.

        Args:
            save_system: SaveSystem instance
            selected_slot: Currently selected save slot (1-5)
        """
        center_x = self.width // 2
        center_y = self.height // 2

        # Background
        self.draw_box(0, 0, self.width, self.height, alpha=200)

        # Title
        self.draw_text("SAVE GAME", center_x, 60, font='large', center=True, color=self.color_highlight)

        # Get all save info
        saves = save_system.list_saves()

        # Draw save slots
        y = 150
        for slot in range(1, 6):
            # Slot background
            slot_width = 600
            slot_height = 80
            slot_x = center_x - slot_width // 2

            # Highlight selected slot
            if slot == selected_slot:
                self.draw_box(slot_x, y, slot_width, slot_height, color=(60, 60, 100), alpha=220)
                pygame.draw.rect(self.surface, self.color_highlight, (slot_x, y, slot_width, slot_height), 3)
            else:
                self.draw_box(slot_x, y, slot_width, slot_height, color=(30, 30, 50), alpha=200)

            # Slot number
            self.draw_text(f"Slot {slot}", slot_x + 20, y + 10, font='medium',
                          color=self.color_highlight if slot == selected_slot else self.color_text)

            # Save info or empty
            if slot in saves:
                info = saves[slot]
                timestamp = info.get('timestamp', 'Unknown')
                level = info.get('player_level', 1)
                play_time = info.get('play_time', 0)
                hours = int(play_time // 3600)
                minutes = int((play_time % 3600) // 60)

                self.draw_text(f"Level {level} | {hours}h {minutes}m | {timestamp[:16]}",
                              slot_x + 20, y + 45, font='small', color=(200, 200, 200))
            else:
                self.draw_text("Empty Slot", slot_x + 20, y + 45, font='small',
                              color=(150, 150, 150))

            y += 100

        # Controls
        self.draw_text("↑/↓: Select Slot | ENTER: Save | ESC: Cancel", center_x, self.height - 60,
                      font='small', center=True, color=(150, 150, 150))

    def draw_load_menu(self, save_system, selected_slot=1):
        """
        Draw load game menu.

        Args:
            save_system: SaveSystem instance
            selected_slot: Currently selected save slot (1-5)
        """
        center_x = self.width // 2
        center_y = self.height // 2

        # Background
        self.draw_box(0, 0, self.width, self.height, alpha=200)

        # Title
        self.draw_text("LOAD GAME", center_x, 60, font='large', center=True, color=self.color_highlight)

        # Get all save info
        saves = save_system.list_saves()

        if not saves:
            self.draw_text("No saved games found", center_x, center_y, font='medium',
                          center=True, color=(150, 150, 150))
            self.draw_text("Press ESC to go back", center_x, self.height - 60,
                          font='small', center=True, color=(150, 150, 150))
            return

        # Draw save slots
        y = 150
        for slot in range(1, 6):
            # Slot background
            slot_width = 600
            slot_height = 80
            slot_x = center_x - slot_width // 2

            # Check if slot has save
            has_save = slot in saves

            # Highlight selected slot (only if it has a save)
            if slot == selected_slot and has_save:
                self.draw_box(slot_x, y, slot_width, slot_height, color=(60, 60, 100), alpha=220)
                pygame.draw.rect(self.surface, self.color_highlight, (slot_x, y, slot_width, slot_height), 3)
            else:
                self.draw_box(slot_x, y, slot_width, slot_height, color=(30, 30, 50), alpha=200)

            # Slot number
            self.draw_text(f"Slot {slot}", slot_x + 20, y + 10, font='medium',
                          color=self.color_highlight if (slot == selected_slot and has_save) else self.color_text)

            # Save info or empty
            if has_save:
                info = saves[slot]
                timestamp = info.get('timestamp', 'Unknown')
                level = info.get('player_level', 1)
                play_time = info.get('play_time', 0)
                hours = int(play_time // 3600)
                minutes = int((play_time % 3600) // 60)

                self.draw_text(f"Level {level} | {hours}h {minutes}m | {timestamp[:16]}",
                              slot_x + 20, y + 45, font='small', color=(200, 200, 200))
            else:
                self.draw_text("Empty Slot", slot_x + 20, y + 45, font='small',
                              color=(100, 100, 100))

            y += 100

        # Controls
        self.draw_text("↑/↓: Select Slot | ENTER: Load | DEL: Delete | ESC: Cancel",
                      center_x, self.height - 60, font='small', center=True, color=(150, 150, 150))

    def render(self, screen):
        """Render UI to screen using OpenGL."""
        if self.ctx:
            # Convert pygame surface to OpenGL texture
            # Use True to flip vertically (OpenGL textures are bottom-left origin)
            surf_data = pygame.image.tostring(self.surface, 'RGBA', True)
            self.ui_texture.write(surf_data)

            # Enable blending for transparency
            self.ctx.enable(moderngl.BLEND)
            self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

            # Disable depth testing for UI overlay
            self.ctx.disable(moderngl.DEPTH_TEST)

            # Bind texture and render quad
            self.ui_texture.use(0)
            self.ui_vao.render(moderngl.TRIANGLE_STRIP)

            # Re-enable depth testing
            self.ctx.enable(moderngl.DEPTH_TEST)
        else:
            # Fallback to pygame rendering (shouldn't happen)
            screen.blit(self.surface, (0, 0))
