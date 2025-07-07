#!/usr/bin/env python3
"""
Simple script to export PNG/JPG from SVG logo files with optional padding.

Usage:
    python export_logo.py PROJECT_NAME [--width WIDTH] [--height HEIGHT] [--white-background] [--jpg] [--padding PERCENT]

Examples:
    python export_logo.py MDAGridDataFormats --width 256
    python export_logo.py PMDA --height 128 --white-background
    python export_logo.py MDAData --jpg
    python export_logo.py MDADistopia --width 512 --jpg --padding 10
    python export_logo.py PyTNG --padding 15 --white-background
    python export_logo.py MDAEncore --jpg --padding 5 --width 400
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Warning: Pillow not found. JPG export with padding requires Pillow.")
    print("Install with: pip install Pillow")
    Image = None


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


def export_image(project_name, width=None, height=None, white_background=False, padding_percent=0, format='png'):
    """Export PNG or JPG from SVG logo with optional padding."""
    # Find source SVG file
    svg_path = Path(f"project_logos/{project_name}/MDAnalysis__{project_name}.svg")
    if not svg_path.exists():
        print(f"Error: SVG file not found: {svg_path}")
        return False
    
    # Output file
    output_path = Path(f"MDAnalysis__{project_name}.{format.lower()}")
    
    # If no padding is needed and format is PNG, use direct conversion
    if padding_percent == 0 and format.lower() == 'png':
        return _export_direct_png(svg_path, output_path, width, height, white_background)
    
    # For JPG or PNG with padding, we need Pillow
    if Image is None:
        print("Error: Pillow library required for JPG export or PNG with padding")
        print("Install with: pip install Pillow")
        return False
    
    # Use Pillow-based export for padding or JPG
    return _export_with_pillow(svg_path, output_path, width, height, white_background, padding_percent, format)


def _export_direct_png(svg_path, output_path, width=None, height=None, white_background=False):
    """Direct PNG export using SVG converters."""
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


def _export_with_pillow(svg_path, output_path, width=None, height=None, white_background=False, padding_percent=0, format='png'):
    """Export using Pillow for padding or JPG format."""
    # First, export to PNG in a temporary file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_png_path = Path(temp_file.name)
    
    try:
        # Find converter
        converter_name, converter_cmd = find_converter()
        if not converter_cmd:
            print("Error: No SVG converter found. Please install:")
            print("  - rsvg-convert (librsvg2-bin package)")
            print("  - or inkscape")
            return False
        
        # Calculate size for PNG export
        base_size = width or height or 512  # Use higher default for better quality
        
        # Build command for PNG export
        if converter_name == "rsvg-convert":
            cmd = [converter_cmd]
            if width:
                cmd.extend(["-w", str(width)])
            elif height:
                cmd.extend(["-h", str(height)])
            else:
                cmd.extend(["-w", str(base_size)])
            cmd.extend(["-o", str(temp_png_path), str(svg_path)])
        
        elif converter_name == "inkscape":
            cmd = [converter_cmd]
            if width:
                cmd.extend(["-w", str(width)])
            elif height:
                cmd.extend(["-h", str(height)])
            else:
                cmd.extend(["-w", str(base_size)])
            cmd.extend(["-o", str(temp_png_path), str(svg_path)])
        
        # Execute PNG conversion
        subprocess.run(cmd, check=True)
        
        # Load the PNG image
        with Image.open(temp_png_path) as img:
            # Ensure we have RGBA for transparency handling
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Calculate original dimensions
            orig_width, orig_height = img.size
            
            # Apply padding if requested
            if padding_percent > 0:
                # Calculate padding
                padding_x = int(orig_width * padding_percent / 100)
                padding_y = int(orig_height * padding_percent / 100)
                
                # Calculate new dimensions with padding
                new_width = orig_width + (2 * padding_x)
                new_height = orig_height + (2 * padding_y)
                
                # Determine background mode
                if format.lower() == 'jpg' or white_background:
                    # Create new image with white background
                    padded_img = Image.new('RGB', (new_width, new_height), 'white')
                    
                    # Handle transparency for white background
                    if img.mode == 'RGBA':
                        # Create a white background for the original image first
                        bg = Image.new('RGB', img.size, 'white')
                        bg.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                        padded_img.paste(bg, (padding_x, padding_y))
                    else:
                        padded_img.paste(img, (padding_x, padding_y))
                else:
                    # Create new image with transparent background (PNG only)
                    padded_img = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
                    padded_img.paste(img, (padding_x, padding_y), img if img.mode == 'RGBA' else None)
                
                final_img = padded_img
            else:
                # No padding needed
                if format.lower() == 'jpg' or white_background:
                    # Convert to RGB with white background
                    if img.mode == 'RGBA':
                        bg = Image.new('RGB', img.size, 'white')
                        bg.paste(img, mask=img.split()[-1])
                        final_img = bg
                    else:
                        final_img = img.convert('RGB')
                else:
                    final_img = img
            
            # Save in the requested format
            if format.lower() == 'jpg':
                if final_img.mode == 'RGBA':
                    # Convert RGBA to RGB with white background for JPG
                    bg = Image.new('RGB', final_img.size, 'white')
                    bg.paste(final_img, mask=final_img.split()[-1])
                    final_img = bg
                final_img.save(output_path, 'JPEG', quality=95, optimize=True)
            else:  # PNG
                final_img.save(output_path, 'PNG', optimize=True)
        
        # Build description
        desc_parts = []
        if format.lower() == 'jpg':
            desc_parts.append("JPG")
        else:
            desc_parts.append("PNG")
            
        if white_background or format.lower() == 'jpg':
            desc_parts.append("white background")
        else:
            desc_parts.append("transparent background")
            
        if padding_percent > 0:
            desc_parts.append(f"{padding_percent}% padding")
        
        description = " with " + " and ".join(desc_parts[1:]) if len(desc_parts) > 1 else desc_parts[0]
        print(f"✓ Exported: {output_path} ({desc_parts[0]}{description})")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error during SVG to PNG conversion: {e}")
        return False
    except Exception as e:
        print(f"Error during image processing: {e}")
        return False
    finally:
        # Clean up temporary file
        if temp_png_path.exists():
            temp_png_path.unlink()


def main():
    parser = argparse.ArgumentParser(
        description="Export PNG/JPG from SVG logo files"
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
    parser.add_argument(
        "--jpg",
        action="store_true",
        help="Export as JPG instead of PNG"
    )
    parser.add_argument(
        "--padding",
        type=float,
        default=0,
        help="Add padding around the image (percentage, e.g., 10 for 10%%)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.width and args.height:
        print("Error: Specify either --width or --height, not both")
        return 1
    
    # Validate padding argument
    if args.padding < 0:
        print("Error: Padding must be a positive number")
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
    
    # Determine format
    format_type = 'jpg' if args.jpg else 'png'
    
    # Export with unified function
    success = export_image(
        args.project_name, 
        args.width, 
        args.height, 
        args.white_background, 
        args.padding,
        format_type
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 
