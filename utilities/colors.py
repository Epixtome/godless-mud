class ColorMeta(type):
    """
    [V7.2] Safety Metaclass for Godless Colors.
    Prevents AttributeError crashes when AI agents hallucinate non-standard colors.
    """
    def __getattr__(cls, name):
        # Normalize and filter out magic methods
        if name.startswith("__"):
            return super().__getattribute__(name)
            
        FALLBACKS = {
            "PALE_BLUE": cls.CYAN,
            "LIGHT_BLUE": cls.CYAN,
            "ICE_BLUE": cls.CYAN,
            "DEEP_RED": cls.RED,
            "GOLD": cls.YELLOW,
            "ORANGE": cls.YELLOW,
            "VIOLET": cls.MAGENTA,
            "PINK": cls.MAGENTA,
            "GRAY": cls.DARK_GRAY,
            "GREY": cls.DARK_GRAY,
            "BLACK": "\033[30m"
        }
        
        # Return fallback or DEFAULT (White) to prevent game-breaking exceptions
        return FALLBACKS.get(name.upper(), cls.WHITE)

class Colors(metaclass=ColorMeta):
    """
    Godless ANSI Color Standards (V7.2 - Immortality Refactor).
    Use UPPER_CASE constants and standard 8-color palette.
    """
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    PURPLE = "\033[35m" 
    CYAN = "\033[36m"
    LIGHT_CYAN = "\033[96m"
    WHITE = "\033[37m"
    
    DARK_GRAY = "\033[90m"
    DGREY = "\033[90m" # Legacy Alias
    
    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    @staticmethod
    def strip(text):
        """Removes ANSI codes from a string."""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    @staticmethod
    def translate(text):
        """Translates {Colors.X} tokens in a string."""
        if not text: return ""
        import re
        def repl(match):
            color_name = match.group(1).upper()
            return getattr(Colors, color_name, "")
        return re.sub(r'\{Colors\.([A-Za-z_]+)\}', repl, text)