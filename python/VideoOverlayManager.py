from moviepy.editor import VideoFileClip, CompositeVideoClip, ColorClip, VideoClip
from moviepy.video.tools.drawing import circle, color_gradient
import numpy as np
from typing import Optional, List, Tuple

class VideoOverlayManager:
    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height

    def create_animated_background(self, duration: float, theme_color: str) -> VideoClip:
        """Create an animated background with floating shapes and gradients"""
        def make_frame(t):
            frame = np.zeros((self.height, self.width, 3))

            # Create gradient background
            for y in range(self.height):
                opacity = 1 - (y / self.height)
                color_value = int(255 * opacity * 0.3)  # 30% max intensity
                frame[y, :] = [color_value] * 3

            # Add floating circles
            num_circles = 5
            for i in range(num_circles):
                # Calculate position based on time
                x = int(self.width * (0.2 + 0.6 * (np.sin(t + i) + 1) / 2))
                y = int(self.height * (0.2 + 0.6 * (np.cos(t * 0.5 + i) + 1) / 2))

                # Draw circle with soft edges
                radius = 50 + 20 * np.sin(t * 2 + i)
                circle(frame, (x, y), radius, (255, 255, 255), blur=30)

            return frame

        return VideoClip(make_frame, duration=duration)

    def create_geometric_overlay(self, duration: float) -> VideoClip:
        """Create geometric patterns that move slowly"""
        def make_frame(t):
            frame = np.zeros((self.height, self.width, 3))

            # Create hexagonal grid
            hex_size = 100
            hex_spacing = hex_size * 1.5
            offset = t * 20  # Slow movement

            for row in range(-1, self.height // int(hex_spacing) + 2):
                for col in range(-1, self.width // int(hex_spacing) + 2):
                    x = col * hex_spacing + (row % 2) * (hex_spacing / 2) + offset
                    y = row * hex_spacing * 0.866

                    # Draw hexagon
                    for i in range(6):
                        angle1 = 2 * np.pi * i / 6
                        angle2 = 2 * np.pi * (i + 1) / 6
                        x1 = int(x + hex_size * np.cos(angle1))
                        y1 = int(y + hex_size * np.sin(angle1))
                        x2 = int(x + hex_size * np.cos(angle2))
                        y2 = int(y + hex_size * np.sin(angle2))

                        if 0 <= x1 < self.width and 0 <= y1 < self.height:
                            opacity = 0.05 * (1 + np.sin(t + x/self.width * np.pi))
                            frame[y1:y2, x1:x2] = np.maximum(frame[y1:y2, x1:x2], 255 * opacity)

            return frame

        return VideoClip(make_frame, duration=duration)

    def create_particle_effect(self, duration: float) -> VideoClip:
        """Create floating particle effect"""
        num_particles = 50
        particles = [(np.random.rand(), np.random.rand(), np.random.rand() * 2 * np.pi)
                    for _ in range(num_particles)]

        def make_frame(t):
            frame = np.zeros((self.height, self.width, 3))

            for base_x, base_y, angle in particles:
                # Calculate position with smooth movement
                x = int(self.width * (base_x + 0.1 * np.sin(t + angle)))
                y = int(self.height * (base_y + 0.1 * np.cos(t + angle)))

                if 0 <= x < self.width and 0 <= y < self.height:
                    # Create glowing particle
                    size = int(5 + 3 * np.sin(t * 2 + angle))
                    opacity = 0.15 * (1 + np.sin(t + angle)) / 2

                    for dy in range(-size, size + 1):
                        for dx in range(-size, size + 1):
                            if x + dx < 0 or x + dx >= self.width or y + dy < 0 or y + dy >= self.height:
                                continue
                            distance = np.sqrt(dx*dx + dy*dy)
                            if distance <= size:
                                pixel_opacity = opacity * (1 - distance/size)
                                frame[y + dy, x + dx] = np.maximum(
                                    frame[y + dy, x + dx],
                                    [255 * pixel_opacity] * 3
                                )

            return frame

        return VideoClip(make_frame, duration=duration)
