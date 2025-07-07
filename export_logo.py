#!/usr/bin/env python3
"""
Simple script to export PNG from SVG logo files.

Usage:
    python export_logo.py PROJECT_NAME [--width WIDTH] [--height HEIGHT] [--white-background]

Examples:
    python export_logo.py MDAGridDataFormats --width 256
    python export_logo.py PMDA --height 128 --white-background
    python export_logo.py MDAData
"""

import argparse
import subprocess
import sys
from pathlib import Path


def find_converter():
    """Find available SVG to PNG converter."""
    converters = [
        ("rsvg-convert", "rsvg-convert"),
        ("inkscape", "inkscape")
    ]
    
    for name, cmd in converters:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            return name, cmd
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    return None, None


def export_png(project_name, width=None, height=None, white_background=False):
    """Export PNG from SVG logo."""
    # Find source SVG file
    svg_path = Path(f"project_logos/{project_name}/MDAnalysis__{project_name}.svg")
    if not svg_path.exists():
        print(f"Error: SVG file not found: {svg_path}")
        return False
    
    # Output PNG file
    output_path = Path(f"MDAnalysis__{project_name}.png")
    
    # Find converter
    converter_name, converter_cmd = find_converter()
    if not converter_cmd:
        print("Error: No SVG converter found. Please install:")
        print("  - rsvg-convert (librsvg2-bin package)")
        print("  - or inkscape")
        return False
    
    # Build command
    if converter_name == "rsvg-convert":
        cmd = [converter_cmd]
        if width:
            cmd.extend(["-w", str(width)])
        elif height:
            cmd.extend(["-h", str(height)])
        else:
            cmd.extend(["-w", "256"])  # Default width
        
        # Add white background if requested
        if white_background:
            cmd.extend(["-b", "white"])
        
        cmd.extend(["-o", str(output_path), str(svg_path)])
    
    elif converter_name == "inkscape":
        cmd = [converter_cmd]
        if width:
            cmd.extend(["-w", str(width)])
        elif height:
            cmd.extend(["-h", str(height)])
        else:
            cmd.extend(["-w", "256"])  # Default width
        
        # Add white background if requested
        if white_background:
            cmd.extend(["--export-background", "white", "--export-background-opacity", "1.0"])
        
        cmd.extend(["-o", str(output_path), str(svg_path)])
    
    # Execute conversion
    try:
        subprocess.run(cmd, check=True)
        bg_info = " with white background" if white_background else ""
        print(f"✓ Exported: {output_path}{bg_info}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Export PNG from SVG logo files"
    )
    parser.add_argument(
        "project_name",
        help="Project name (e.g., MDAGridDataFormats, PMDA)"
    )
    parser.add_argument(
        "--width",
        type=int,
        help="Output width in pixels (preserves aspect ratio)"
    )
    parser.add_argument(
        "--height",
        type=int,
        help="Output height in pixels (preserves aspect ratio)"
    )
    parser.add_argument(
        "--white-background",
        action="store_true",
        help="Export with white background instead of transparent"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.width and args.height:
        print("Error: Specify either --width or --height, not both")
        return 1
    
    # Check if project exists
    project_dir = Path(f"project_logos/{args.project_name}")
    if not project_dir.exists():
        print(f"Error: Project '{args.project_name}' not found")
        print("Available projects:")
        logos_dir = Path("project_logos")
        if logos_dir.exists():
            for p in sorted(logos_dir.iterdir()):
                if p.is_dir():
                    print(f"  {p.name}")
        return 1
    
    # Export PNG
    success = export_png(args.project_name, args.width, args.height, args.white_background)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 