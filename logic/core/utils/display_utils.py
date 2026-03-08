from utilities.colors import Colors

def render_header(title, width=60, char="="):
    """Renders a centered header within a line of the specified character."""
    # Use ASCII characters for maximum compatibility
    return f"{Colors.BOLD}{f' {title} ':=^{width}}{Colors.RESET}".replace("=", char)

def render_line(width=60, char="-"):
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
