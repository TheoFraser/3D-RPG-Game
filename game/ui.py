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
            except Exception as e:
                pass  # Skip rendering if error occurs

    def draw_hud(self, player, inventory, interaction_target=None, culled_count=0, total_entities=0):
        """
        Draw heads-up display.

        Args:
            player: Player object
            inventory: Inventory object
            interaction_target: Object player is looking at (optional)
            culled_count: Number of culled entities
            total_entities: Total number of entities
        """
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

    def draw_map(self, player_position, chunk_manager=None):
        """Draw simple map view."""
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

        # Close prompt
        self.draw_text("Press M or ESC to close", center_x, map_y + map_size + 30,
                      font='small', center=True, color=(150, 150, 150))

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
