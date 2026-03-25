from utilities.colors import Colors
import re

def render_header(title, width=100, char="="):
    """Renders a centered header within a line of the specified character."""
    # Use ASCII characters for maximum compatibility
    return f"{Colors.BOLD}{f' {title} ':=^{width}}{Colors.RESET}".replace("=", char)

def render_line(width=100, char="-"):
    """Renders a horizontal separator line."""
    return f"{Colors.WHITE}{char * width}{Colors.RESET}"

def render_progress_bar(value, max_val=20, width=20, fill_char="#", empty_char="-", color=Colors.CYAN):
    """Renders a visual progress bar using ASCII characters."""
    normalized_val = int((value / max_val) * width) if max_val > 0 else 0
    normalized_val = max(0, min(width, normalized_val))
    
    bar = fill_char * normalized_val + empty_char * (width - normalized_val)
    return f"{color}[{bar}]{Colors.RESET}"

def render_table_header(columns, widths, color=Colors.BOLD):
    """Renders a table header with aligned columns."""
    header_parts = []
    for (col_name, width) in zip(columns, widths):
        header_parts.append(f"{col_name:<{width}}")
    return f"{color}{' '.join(header_parts)}{Colors.RESET}"

def render_table_row(data, widths, colors=None):
    """Renders a table row with aligned columns and optional per-column coloring."""
    row_parts = []
    for i, (val, width) in enumerate(zip(data, widths)):
        col_color = colors[i] if colors and i < len(colors) else ""
        reset = Colors.RESET if col_color else ""
        row_parts.append(f"{col_color}{str(val):<{width}}{reset}")
    return " ".join(row_parts)

def render_labeled_value(label, value, label_width=20, label_color=Colors.CYAN, value_color=Colors.WHITE):
    """Renders a 'Label: Value' line with consistent spacing."""
    return f" {label_color}{label:<{label_width}}{Colors.RESET} {value_color}{value}{Colors.RESET}"

def highlight_status_keywords(text):
    """[V7.2] Unifies status effect highlighting across all UI elements (Deck, Look, Messages)."""
    if not text: return ""
    
    # Priority Mapping (Order matters for overlapping regex)
    # We use explicit groups for semantic clarity in our V7.2 palette.
    ELEMENTAL = [
        (r'\b(?:WET|DRENCHED|CHILLED|FROZEN|SHIVERING|COLD|SHOCK|SHOCKED|STATIS|SOAKED|RESONATING)\b', Colors.CYAN),
        (r'\b(?:BURNING|ON FIRE|IGNITED|BLAZING|SCORCHED|FLAMING|SUNSTROKE)\b', Colors.YELLOW),
        (r'\b(?:SHOCKED|ELECTRIFIED|VOLTAIC|STATIC|OVERHEATED|OVERHEAT|HEAT)\b', Colors.BOLD + Colors.YELLOW),
    ]
    DISRUPTION = [
        (r'\b(?:STUNNED|STUN|PRONE|STAGGERED|OFF[- ]BALANCE|DAZED|BLINDED|CONFUSED|SILENCED|PETRIFIED|SHATTERED|KNOCKDOWN|KNOCKED DOWN|BLIND|PARALYZED)\b', Colors.RED),
    ]
    AFFLICTIONS = [
        (r'\b(?:POISONED|BLIGHTED|VENOMOUS|ENVENOMED|PLAGUED|ATROPHY|WASTING|HEXED|MALEDICTION)\b', Colors.GREEN),
        (r'\b(?:BLEEDING|HEMORRHAGED|EXPOSED|VULNERABLE|CURSED|CORRUPTED|SHATTERED MIND|STRAIN|MENTAL STRAIN)\b', Colors.MAGENTA),
    ]
    BUFFS = [
        (r'\b(?:HASTE|EMPOWERED|PROTECTED|BLESSED|REGENERATE|SHIELDED|UNSTOPPABLE|WARDED|SANCTIFIED|BRACED|REINFORCED|STONE SKIN|MAGIC SHIELD|ECHO SHIELD|BLUR|METAMORPHOSIS|UNDYING)\b', Colors.BOLD + Colors.GREEN),
    ]
    STANCES = [
        (r'\b(?:TIGER STANCE|CRANE STANCE|TURTLE STANCE|CRANE\'S ECHO|TURTLE\'S ECHO|EVASIVE STEP|EVASIVE|BERSERK RAGE|BERSERK)\b', Colors.BOLD + Colors.CYAN),
    ]

    res: str = text
    # Sequence through all groups
    for group in [ELEMENTAL, DISRUPTION, AFFLICTIONS, BUFFS, STANCES]:
        for pattern, color in group:
            def repl(match):
                word = match.group(0)
                # Nest color then restore the expected reset
                return f"{color}{word}{Colors.RESET}"
            res = re.sub(pattern, repl, res, flags=re.IGNORECASE)
            
    return res
