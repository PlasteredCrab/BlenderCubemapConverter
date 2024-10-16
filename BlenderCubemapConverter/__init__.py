bl_info = {
    "name": "Cubemap Converter Addon",
    "author": "Plastered_Crab and Ultikynnys (and the py360convert GitHub)",
    "version": (1, 6, 2),
    "blender": (4, 2, 0),
    "location": "View3D > UI",
    "description": "Converts between cubemap images and equirectangular maps",
    "warning": "",
    "wiki_url": "",
    "category": "3D View",
}

import sys
import subprocess
import importlib
import os

def install_package(package):
    print(f"Attempting to import {package}...")
    try:
        importlib.import_module(package)
        print(f"{package} is already installed.")
        return
    except ImportError as e:
        print(f"{package} is not installed: {e}")

    print(f"Installing {package} into a user directory...")
    python_executable = sys.executable

    # Create a directory under the user's home directory
    user_home = os.path.expanduser('~')
    target_dir = os.path.join(user_home, 'blender_python_libs')
    os.makedirs(target_dir, exist_ok=True)

    # Install the package into target_dir without dependencies
    try:
        subprocess.check_call([
            python_executable,
            '-m', 'pip',
            'install',
            package,
            '--no-deps',
            '--target', target_dir
        ])
    except subprocess.CalledProcessError as e:
        print(f"Error installing {package}: {e}")
        return

    # Add target_dir to sys.path if not already present
    if target_dir not in sys.path:
        sys.path.insert(0, target_dir)
        print(f"Added {target_dir} to sys.path")

    print(f"Re-attempting to import {package} after installation...")
    try:
        importlib.import_module(package)
        print(f"{package} installed and imported successfully.")
    except ImportError as e:
        print(f"Failed to import {package} after installation. Error: {e}")
        print(f"sys.path: {sys.path}")

try:#Skip if it exists
    import numpy
except:
    install_package('numpy')

try:#Skip if it exists
    import scipy
except:
    install_package('scipy')


import bpy
import numpy as np
import py360convert

def convert_equirectangular_to_cubemap(equirectangular_image_path, separate_alpha_channel):
    print(f"Processing equirectangular image: {equirectangular_image_path}")
    try:
        # Skip files that have "cubemap" in the file name (case-insensitive)
        if "cubemap" in equirectangular_image_path.lower():
            print(f"Skipping {equirectangular_image_path}")
            return

        # Load the equirectangular image
        try:
            equirect_image = bpy.data.images.load(equirectangular_image_path)
        except Exception as e:
            print(f"Failed to load image {equirectangular_image_path}: {e}")
            return

        print("Image loaded successfully.")

        equirect_image.use_half_precision = True  # For HDRI support
        equirect_image.colorspace_settings.name = 'Non-Color'  # Set color space to Non-Color

        width, height = equirect_image.size
        channels = len(equirect_image.pixels) // (width * height)

        print(f"Image size: width={width}, height={height}, channels={channels}")

        # Read the pixels and reshape
        equirect_pixels = np.array(equirect_image.pixels[:]).reshape((height, width, channels)).astype(np.float32)
        equirect_pixels = equirect_pixels[:, :, :4]  # Ensure RGBA

        # Separate alpha channel if needed
        if channels == 4:
            alpha_equirect = equirect_pixels[:, :, 3]
            rgb_equirect = equirect_pixels[:, :, :3]
        else:
            alpha_equirect = np.ones((height, width), dtype=np.float32)
            rgb_equirect = equirect_pixels

        # Determine face width based on the width of the equirectangular image
        face_w = width // 4

        # Convert RGB equirectangular to cubemap
        cube_rgb = py360convert.e2c(rgb_equirect, face_w=face_w, cube_format='dice')

        # Convert alpha equirectangular to cubemap
        alpha_equirect_expanded = np.stack([alpha_equirect]*3, axis=-1)
        cube_alpha = py360convert.e2c(alpha_equirect_expanded, face_w=face_w, cube_format='dice')[:, :, 0]

        # Get dimensions from cube_rgb
        height_c, width_c, _ = cube_rgb.shape

        if separate_alpha_channel:
            # Create RGB cubemap image with alpha channel set to 1
            cube_rgb_image = bpy.data.images.new(
                "Cubemap RGB Image",
                width=width_c,
                height=height_c,
                alpha=True,
                float_buffer=True
            )
            cube_rgb_image.use_half_precision = True
            cube_rgb_image.file_format = 'OPEN_EXR'
            cube_rgb_image.colorspace_settings.name = 'Non-Color'

            # Combine RGB channels with alpha channel set to 1
            cube_rgb_alpha = np.dstack((cube_rgb, np.ones_like(cube_alpha)))

            # Flatten and assign pixels
            cube_rgb_image.pixels = cube_rgb_alpha.flatten().tolist()

            # Save the RGB cubemap image
            dir_name = os.path.dirname(equirectangular_image_path)
            base_name = os.path.basename(equirectangular_image_path)
            file_name, ext = os.path.splitext(base_name)
            cube_rgb_file_name = f"{file_name}_cubemap_rgb.exr"
            cube_rgb_image_path = os.path.join(dir_name, cube_rgb_file_name)
            cube_rgb_image.filepath_raw = cube_rgb_image_path
            cube_rgb_image.save()

            print(f"Saved RGB cubemap image to: {cube_rgb_image_path}")

            # Create Alpha cubemap image with alpha channel set to 1
            cube_alpha_image = bpy.data.images.new(
                "Cubemap Alpha Image",
                width=width_c,
                height=height_c,
                alpha=True,
                float_buffer=True
            )
            cube_alpha_image.use_half_precision = True
            cube_alpha_image.file_format = 'OPEN_EXR'
            cube_alpha_image.colorspace_settings.name = 'Non-Color'

            # Replace RGB channels with alpha data, set alpha channel to 1
            cube_alpha_rgb = np.dstack((cube_alpha, cube_alpha, cube_alpha, np.ones_like(cube_alpha)))

            # Flatten and assign pixels
            cube_alpha_image.pixels = cube_alpha_rgb.flatten().tolist()

            # Save the Alpha cubemap image
            cube_alpha_file_name = f"{file_name}_cubemap_alpha.exr"
            cube_alpha_image_path = os.path.join(dir_name, cube_alpha_file_name)
            cube_alpha_image.filepath_raw = cube_alpha_image_path
            cube_alpha_image.save()

            print(f"Saved Alpha cubemap image to: {cube_alpha_image_path}")

        else:
            # Combine RGB and alpha channels
            cube_rgba = np.dstack((cube_rgb, cube_alpha))

            # Create combined cubemap image
            cubemap_image = bpy.data.images.new(
                "Cubemap Image",
                width=width_c,
                height=height_c,
                alpha=True,
                float_buffer=True
            )
            cubemap_image.use_half_precision = True  # For HDRI support
            cubemap_image.file_format = 'OPEN_EXR'
            cubemap_image.colorspace_settings.name = 'Non-Color'

            # Flatten and assign pixels
            cubemap_image.pixels = cube_rgba.flatten().tolist()

            # Save the image
            dir_name = os.path.dirname(equirectangular_image_path)
            base_name = os.path.basename(equirectangular_image_path)
            file_name, ext = os.path.splitext(base_name)
            cubemap_file_name = f"{file_name}_cubemap.exr"
            cubemap_image_path = os.path.join(dir_name, cubemap_file_name)
            cubemap_image.filepath_raw = cubemap_image_path
            cubemap_image.save()

            print(f"Saved cubemap image to: {cubemap_image_path}")

    except Exception as e:
        print(f"An error occurred during conversion: {e}")
        import traceback
        traceback.print_exc()

def convert_cubemap_to_equirectangular(cubemap_image_path, separate_alpha_channel):
    print(f"Processing cubemap image: {cubemap_image_path}")
    try:
        # Skip files that have "equirectangular" in the file name (case-insensitive)
        if "equirectangular" in cubemap_image_path.lower():
            print(f"Skipping {cubemap_image_path}")
            return

        # Load the cubemap image
        try:
            cubemap_image = bpy.data.images.load(cubemap_image_path)
        except Exception as e:
            print(f"Failed to load image {cubemap_image_path}: {e}")
            return

        print("Image loaded successfully.")

        cubemap_image.use_half_precision = True  # For HDRI support
        cubemap_image.colorspace_settings.name = 'Non-Color'  # Set color space to Non-Color

        width, height = cubemap_image.size
        channels = len(cubemap_image.pixels) // (width * height)

        print(f"Image size: width={width}, height={height}, channels={channels}")

        # Read the pixels and reshape
        cubemap_pixels = np.array(cubemap_image.pixels[:]).reshape((height, width, channels)).astype(np.float32)
        cubemap_pixels = cubemap_pixels[:, :, :4]  # Ensure RGBA

        # Separate alpha channel if needed
        if channels == 4:
            alpha_cubemap = cubemap_pixels[:, :, 3]
            rgb_cubemap = cubemap_pixels[:, :, :3]
        else:
            alpha_cubemap = np.ones((height, width), dtype=np.float32)
            rgb_cubemap = cubemap_pixels

        # Determine output dimensions
        equirect_width = width // 4 * 8  # Equirectangular width is typically 2:1 ratio
        equirect_height = height // 3 * 4

        # Convert RGB cubemap to equirectangular
        equirect_rgb = py360convert.c2e(rgb_cubemap, h=equirect_height, w=equirect_width, cube_format='dice')

        # Convert alpha cubemap to equirectangular
        alpha_cubemap_expanded = np.stack([alpha_cubemap]*3, axis=-1)
        equirect_alpha = py360convert.c2e(alpha_cubemap_expanded, h=equirect_height, w=equirect_width, cube_format='dice')[:, :, 0]

        if separate_alpha_channel:
            # Create RGB equirectangular image with alpha channel set to 1
            equirect_rgb_image = bpy.data.images.new(
                "Equirectangular RGB Image",
                width=equirect_width,
                height=equirect_height,
                alpha=True,
                float_buffer=True
            )
            equirect_rgb_image.use_half_precision = True
            equirect_rgb_image.file_format = 'OPEN_EXR'
            equirect_rgb_image.colorspace_settings.name = 'Non-Color'

            # Combine RGB channels with alpha channel set to 1
            equirect_rgb_alpha = np.dstack((equirect_rgb, np.ones_like(equirect_alpha)))

            # Flatten and assign pixels
            equirect_rgb_image.pixels = equirect_rgb_alpha.flatten().tolist()

            # Save the RGB equirectangular image
            dir_name = os.path.dirname(cubemap_image_path)
            base_name = os.path.basename(cubemap_image_path)
            file_name, ext = os.path.splitext(base_name)
            equirect_rgb_file_name = f"{file_name}_equirectangular_rgb.exr"
            equirect_rgb_image_path = os.path.join(dir_name, equirect_rgb_file_name)
            equirect_rgb_image.filepath_raw = equirect_rgb_image_path
            equirect_rgb_image.save()

            print(f"Saved RGB equirectangular image to: {equirect_rgb_image_path}")

            # Create Alpha equirectangular image with alpha channel set to 1
            equirect_alpha_image = bpy.data.images.new(
                "Equirectangular Alpha Image",
                width=equirect_width,
                height=equirect_height,
                alpha=True,
                float_buffer=True
            )
            equirect_alpha_image.use_half_precision = True
            equirect_alpha_image.file_format = 'OPEN_EXR'
            equirect_alpha_image.colorspace_settings.name = 'Non-Color'

            # Replace RGB channels with alpha data, set alpha channel to 1
            equirect_alpha_rgb = np.dstack((equirect_alpha, equirect_alpha, equirect_alpha, np.ones_like(equirect_alpha)))

            # Flatten and assign pixels
            equirect_alpha_image.pixels = equirect_alpha_rgb.flatten().tolist()

            # Save the Alpha equirectangular image
            equirect_alpha_file_name = f"{file_name}_equirectangular_alpha.exr"
            equirect_alpha_image_path = os.path.join(dir_name, equirect_alpha_file_name)
            equirect_alpha_image.filepath_raw = equirect_alpha_image_path
            equirect_alpha_image.save()

            print(f"Saved Alpha equirectangular image to: {equirect_alpha_image_path}")

        else:
            # Combine RGB and alpha channels
            equirect_rgba = np.dstack((equirect_rgb, equirect_alpha))

            # Create combined equirectangular image
            equirect_image = bpy.data.images.new(
                "Equirectangular Image",
                width=equirect_width,
                height=equirect_height,
                alpha=True,
                float_buffer=True
            )
            equirect_image.use_half_precision = True  # For HDRI support
            equirect_image.file_format = 'OPEN_EXR'
            equirect_image.colorspace_settings.name = 'Non-Color'

            # Flatten and assign pixels
            equirect_image.pixels = equirect_rgba.flatten().tolist()

            # Save the image
            dir_name = os.path.dirname(cubemap_image_path)
            base_name = os.path.basename(cubemap_image_path)
            file_name, ext = os.path.splitext(base_name)
            equirect_file_name = f"{file_name}_equirectangular.exr"
            equirect_image_path = os.path.join(dir_name, equirect_file_name)
            equirect_image.filepath_raw = equirect_image_path
            equirect_image.save()

            print(f"Saved equirectangular image to: {equirect_image_path}")

    except Exception as e:
        print(f"An error occurred during conversion: {e}")
        import traceback
        traceback.print_exc()

class ConvertCubemapToEquirectangularOperator(bpy.types.Operator):
    bl_idname = "addon.convert_cubemap"
    bl_label = "Convert Cubemap to Equirectangular"

    def execute(self, context):
        cubemap_image_path = context.scene.cubemap_path  # Get the file path from the scene properties
        separate_alpha_channel = context.scene.separate_alpha_channel  # Get the value of the checkbox
        convert_cubemap_to_equirectangular(cubemap_image_path, separate_alpha_channel)
        self.report({'INFO'}, f"Converted {cubemap_image_path} to equirectangular")
        return {'FINISHED'}

class ConvertAllCubemapsToEquirectangularOperator(bpy.types.Operator):
    bl_idname = "addon.convert_all_cubemaps"
    bl_label = "Convert All Cubemaps to Equirectangular"

    def execute(self, context):
        directory = context.scene.cubemaps_directory  # Get the directory from the scene properties
        separate_alpha_channel = context.scene.separate_alpha_channel  # Get the value of the checkbox

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith((".png", ".jpg", ".hdr", ".exr")):
                    cubemap_image_path = os.path.join(root, file)
                    convert_cubemap_to_equirectangular(cubemap_image_path, separate_alpha_channel)
        self.report({'INFO'}, f"Converted all cubemaps in {directory} to equirectangular")
        return {'FINISHED'}

class ConvertEquirectangularToCubemapOperator(bpy.types.Operator):
    bl_idname = "addon.convert_equirectangular"
    bl_label = "Convert Equirectangular to Cubemap"

    def execute(self, context):
        equirectangular_image_path = context.scene.equirectangular_path  # Get the file path from the scene properties
        separate_alpha_channel = context.scene.separate_alpha_channel  # Get the value of the checkbox
        convert_equirectangular_to_cubemap(equirectangular_image_path, separate_alpha_channel)
        self.report({'INFO'}, f"Converted {equirectangular_image_path} to cubemap")
        return {'FINISHED'}

class ConvertAllEquirectangularsToCubemapOperator(bpy.types.Operator):
    bl_idname = "addon.convert_all_equirectangulars"
    bl_label = "Convert All Equirectangulars to Cubemap"

    def execute(self, context):
        directory = context.scene.equirectangulars_directory  # Get the directory from the scene properties
        separate_alpha_channel = context.scene.separate_alpha_channel  # Get the value of the checkbox

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith((".png", ".jpg", ".hdr", ".exr")):
                    equirectangular_image_path = os.path.join(root, file)
                    convert_equirectangular_to_cubemap(equirectangular_image_path, separate_alpha_channel)
        self.report({'INFO'}, f"Converted all equirectangulars in {directory} to cubemap")
        return {'FINISHED'}

class ConverterPanel(bpy.types.Panel):
    bl_label = "Cubemap Tool"
    bl_idname = "MYADDON_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Cubemap Tool'

    def draw(self, context):
        layout = self.layout

        layout.prop(context.scene, "separate_alpha_channel")
        layout.separator()

        # Cubemap to Equirectangular
        layout.label(text="Cubemap to Equirectangular")
        layout.prop(context.scene, "cubemap_path", text="Cubemap Image")
        layout.operator("addon.convert_cubemap", text="Convert Cubemap")
        layout.prop(context.scene, "cubemaps_directory", text="Cubemaps Directory")
        layout.operator("addon.convert_all_cubemaps", text="Convert All Cubemaps")
        layout.separator()

        # Equirectangular to Cubemap
        layout.label(text="Equirectangular to Cubemap")
        layout.prop(context.scene, "equirectangular_path", text="Equirectangular Image")
        layout.operator("addon.convert_equirectangular", text="Convert Equirectangular")
        layout.prop(context.scene, "equirectangulars_directory", text="Equirectangulars Directory")
        layout.operator("addon.convert_all_equirectangulars", text="Convert All Equirectangulars")

def register():
    bpy.utils.register_class(ConvertCubemapToEquirectangularOperator)
    bpy.utils.register_class(ConvertAllCubemapsToEquirectangularOperator)
    bpy.utils.register_class(ConvertEquirectangularToCubemapOperator)
    bpy.utils.register_class(ConvertAllEquirectangularsToCubemapOperator)
    bpy.utils.register_class(ConverterPanel)

    bpy.types.Scene.cubemap_path = bpy.props.StringProperty(
        name="Cubemap Image",
        description="Path to the cubemap image file",
        subtype="FILE_PATH"
    )
    bpy.types.Scene.cubemaps_directory = bpy.props.StringProperty(
        name="Cubemaps Directory",
        description="Directory containing cubemap images",
        subtype="DIR_PATH"
    )
    bpy.types.Scene.equirectangular_path = bpy.props.StringProperty(
        name="Equirectangular Image",
        description="Path to the equirectangular image file",
        subtype="FILE_PATH"
    )
    bpy.types.Scene.equirectangulars_directory = bpy.props.StringProperty(
        name="Equirectangulars Directory",
        description="Directory containing equirectangular images",
        subtype="DIR_PATH"
    )
    bpy.types.Scene.separate_alpha_channel = bpy.props.BoolProperty(
        name="Separate Alpha Channel",
        description="Handle alpha channel separately",
        default=False
    )

def unregister():
    bpy.utils.unregister_class(ConvertCubemapToEquirectangularOperator)
    bpy.utils.unregister_class(ConvertAllCubemapsToEquirectangularOperator)
    bpy.utils.unregister_class(ConvertEquirectangularToCubemapOperator)
    bpy.utils.unregister_class(ConvertAllEquirectangularsToCubemapOperator)
    bpy.utils.unregister_class(ConverterPanel)

    del bpy.types.Scene.cubemap_path
    del bpy.types.Scene.cubemaps_directory
    del bpy.types.Scene.equirectangular_path
    del bpy.types.Scene.equirectangulars_directory
    del bpy.types.Scene.separate_alpha_channel

if __name__ == "__main__":
    register()