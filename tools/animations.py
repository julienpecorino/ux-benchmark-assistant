"""
Terminal animations for the BenchmarkUX chat agent.
Provides typing animation for engaging user interactions.
"""

import time
import sys


class TerminalAnimations:
    """Collection of terminal animations for the chat agent."""
    
    @staticmethod
    def typing_indicator(text: str, delay: float = 0.03, end_char: str = "..."):
        """
        Simulate typing effect with animated dots.
        
        Args:
            text (str): Text to display
            delay (float): Delay between characters
            end_char (str): Characters to animate at the end
        """
        # Print the main text
        for char in text:
            print(char, end='', flush=True)
            time.sleep(delay)
        
        # Animate the ending characters
        for _ in range(3):
            for char in end_char:
                print(char, end='', flush=True)
                time.sleep(0.1)
            print('\b' * len(end_char), end='', flush=True)
            time.sleep(0.1)
        
        print(end_char)


# Convenience function for easy use
def typing(text: str, delay: float = 0.03):
    """Quick typing animation."""
    TerminalAnimations.typing_indicator(text, delay)
