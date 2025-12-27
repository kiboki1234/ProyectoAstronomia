
import os
from PIL import Image

def optimize_images():
    figures_dir = r"d:\proyectosPersonales\ProyectoAstronomia\docs\figures"
    target_width = 1000
    
    if not os.path.exists(figures_dir):
        print("Figures directory not found.")
        return

    for filename in os.listdir(figures_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(figures_dir, filename)
            try:
                with Image.open(filepath) as img:
                    # Convert to RGB if needed (handling alpha channel for JPG)
                    if img.mode in ('RGBA', 'P'):
                         img = img.convert('RGB')
                    
                    # Calculate new size
                    ratio = target_width / float(img.size[0])
                    if ratio < 1: # Only shrink, don't upscale
                        new_height = int(float(img.size[1]) * float(ratio))
                        img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
                        
                        # Save back (Optimized)
                        # We save as PNG for drawings/plots, but maybe JPG for photos?
                        # The original files were PNG. Let's keep PNG but optimized, 
                        # OR switch to JPG for the "evidence" files which are photos.
                        
                        if "evidence" in filename or "iod" in filename or "example" in filename:
                             # These are photos/complex images, JPG is better
                             new_name = os.path.splitext(filename)[0] + ".jpg"
                             new_path = os.path.join(figures_dir, new_name)
                             img.save(new_path, "JPEG", quality=85, optimize=True)
                             print(f"Optimized and converted {filename} -> {new_name}")
                             
                             # Remove original massive PNG if different name
                             # os.remove(filepath) 
                             # Actually let's NOT remove, just in case. 
                             # But the latex needs to point to the new extensions?
                             # LaTeX \includegraphics{filename} without extension finds the best one.
                             # But if I have both, it might pick the PNG again.
                             # I should rewrite the content or replace the file in place if I keep extension.
                             # Let's simple OVERWRITE the PNG with a resized PNG to keep file paths valid.
                             
                        # Retrying: Just resize the PNG in place.
                        img.save(filepath, "PNG", optimize=True)
                        print(f"Optimized {filename}")
                    else:
                        print(f"Skipping {filename} (already small enough)")
            
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    optimize_images()
