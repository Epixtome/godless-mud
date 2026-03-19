class Colors:
    """
    Godless ANSI Color Standards (V5.3).
    Use UPPER_CASE constants only. Aliases are provided for backward compatibility
    but are marked for removal in V6.0.
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
    
    # Standardize on DARK_GRAY
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