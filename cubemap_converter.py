bl_info = {
    "name": "Cubemap Converter Addon",
    "author": "Plastered_Crab (and the py360convert GitHub)",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > UI",
    "description": "Converts cubemap images to equirectangular maps",
    "warning": "",
    "wiki_url": "",
    "category": "3D View",
}


#  NOTE  # RUN AS ADMINISTRATOR

import subprocess
import bpy
import os
import sys
import shutil
import numpy as np

class CubemapPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    library_path: bpy.props.StringProperty(
        name="Py360Convert Library Path",
        subtype='DIR_PATH',
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "library_path")
		
def convert_cubemap_to_equirectangular(cubemap_image_path, separate_alpha_channel):
    import py360convert
    import scipy

    # Skip files that have "equirectangular" in the file name
    if "equirectangular" in cubemap_image_path:
        print(f"Skipping {cubemap_image_path}")
        return

    # Load the cubemap image
    cubemap_image = bpy.data.images.load(cubemap_image_path)
    cubemap_np = np.array(cubemap_image.pixels[:]).reshape((cubemap_image.size[1], cubemap_image.size[0], 4))  # reshape to 2D array with RGBA channels

    # Separate the alpha channel into an additional cubemap image
    alpha_cubemap_np = np.zeros_like(cubemap_np)  # Create a new cubemap with the same shape as the original
    alpha_cubemap_np[:, :, :3] = cubemap_np[:, :, 3, np.newaxis]  # Copy the alpha channel to the RGB channels
    alpha_cubemap_np[:, :, 3] = 1  # Set alpha channel to fully opaque
    rgb_cubemap_np = cubemap_np.copy()  # Copy the original cubemap
    rgb_cubemap_np[:, :, 3] = 1  # Set alpha channel to fully opaque

    # Get the resolution of the input image
    height, width, _ = rgb_cubemap_np.shape
    equirectangular_width = int(width * 1.5)
    equirectangular_height = height

    try:
        
        # Convert the RGB cubemap to an equirectangular image
        rgb_equirectangular_np = py360convert.c2e(rgb_cubemap_np, h=equirectangular_height, w=equirectangular_width, cube_format='dice')
        # Convert the Alpha cubemap to an equirectangular image
        alpha_equirectangular_np = py360convert.c2e(alpha_cubemap_np, h=equirectangular_height, w=equirectangular_width, cube_format='dice')

        # Create new images and assign the pixels
        rgb_equirectangular_image = bpy.data.images.new("RGB Equirectangular Image", width=equirectangular_width, height=equirectangular_height)
        alpha_equirectangular_image = bpy.data.images.new("Alpha Equirectangular Image", width=equirectangular_width, height=equirectangular_height)
        rgb_equirectangular_image.pixels = rgb_equirectangular_np.flatten().tolist()
        alpha_equirectangular_image.pixels = alpha_equirectangular_np.flatten().tolist()

        # Save the equirectangular images
        dir_name = os.path.dirname(cubemap_image_path)
        base_name = os.path.basename(cubemap_image_path)
        file_name, ext = os.path.splitext(base_name)
        rgb_file_name = f"{file_name}_rgb_equirectangular{ext}"
        alpha_file_name = f"{file_name}_alpha_equirectangular{ext}"
        rgb_equirectangular_image_path = os.path.join(dir_name, rgb_file_name)
        alpha_equirectangular_image_path = os.path.join(dir_name, alpha_file_name)
        rgb_equirectangular_image.filepath_raw = rgb_equirectangular_image_path
        alpha_equirectangular_image.filepath_raw = alpha_equirectangular_image_path
        rgb_equirectangular_image.file_format = 'PNG'
        alpha_equirectangular_image.file_format = 'PNG'
        
        if separate_alpha_channel:
            rgb_equirectangular_image.save()
            alpha_equirectangular_image.save()

            print(f"Saving RGB equirectangular image to: {rgb_equirectangular_image_path}")
            print(f"Saving Alpha equirectangular image to: {alpha_equirectangular_image_path}")
        else:
            # Create a new image with alpha channel and assign the RGB channels from rgb_equirectangular_image and the alpha channel from alpha_equirectangular_image
            combined_image = bpy.data.images.new("Combined Equirectangular Image", width=equirectangular_width, height=equirectangular_height, alpha=True)
            combined_np = np.zeros((equirectangular_height, equirectangular_width, 4))
            combined_np[:, :, :3] = rgb_equirectangular_np[:, :, :3]  # Copy the RGB channels
            combined_np[:, :, 3] = alpha_equirectangular_np[:, :, 0]  # Use the red channel of alpha_equirectangular_np as the alpha channel
            combined_image.pixels = combined_np.flatten().tolist()

            # Save the combined image
            combined_file_name = f"{file_name}_combined_equirectangular{ext}"
            combined_image_path = os.path.join(dir_name, combined_file_name)
            combined_image.filepath_raw = combined_image_path
            combined_image.file_format = 'PNG'
            combined_image.save()

            print(f"Saving combined equirectangular image to: {combined_image_path}")
    except Exception as e:
        print(f"Error converting {cubemap_image_path}: {e}")








def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

class InstallPy360ConvertOperator(bpy.types.Operator):
    bl_idname = "addon.install_py360convert"
    bl_label = "Install Py360convert"

    def execute(self, context):
        import numpy
        import subprocess
        
        # Check numpy version
        #scipy_version = scipy__version__
        numpy_version = numpy.__version__
        print("numpy version:", numpy_version)
        if numpy_version >= '1.24.0':
            # Uninstall numpy
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "numpy"])
            # Install specific numpy version
            subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy==1.22.0"])

        # if not (scipy_version):
            # # Uninstall numpy
            # subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "scipy"])

        try:
            import scipy
            print("scipy version:", scipy.__version__)
        except ImportError:
            print("scipy is not installed. Installing now...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "scipy"])



        preferences = context.preferences.addons[__name__].preferences
        py360convert_path = preferences.library_path
        scipy_path = py360convert_path.replace("py360convert", "scipy")


        python_executable_path = sys.executable
        site_packages_path = os.path.join(os.path.dirname(python_executable_path), 'lib', 'site-packages')

        # Check if the path ends with 'bin\lib\site-packages' and modify it
        if site_packages_path.endswith('bin\\lib\\site-packages'):
            site_packages_path = site_packages_path.replace('bin\\lib', 'lib')

        py360convert_dest_path = os.path.join(site_packages_path, 'py360convert')
        scipy_dest_path = os.path.join(site_packages_path, 'scipy')

        if os.path.exists(py360convert_dest_path):
            self.report({'INFO'}, "Py360convert is already installed!")
        else:
            #copy py360convert libraries to needed destination
            shutil.copytree(py360convert_path, py360convert_dest_path)
 
            self.report({'INFO'}, "Py360convert installed successfully")
        
        if os.path.exists(scipy_dest_path):
            self.report({'INFO'}, "Scipy is already installed!")
        else:
            #copy scipy libraries to needed destination
            shutil.copytree(scipy_path, scipy_dest_path)

            self.report({'INFO'}, "scipy installed successfully")
        

        return {'FINISHED'}




class ConvertCubemapOperator(bpy.types.Operator):
    bl_idname = "addon.convert_cubemap"
    bl_label = "Convert Cubemap"

    def execute(self, context):
        import py360convert
        
        cubemap_image_path = context.scene.cubemap_path  # Get the file path from the scene properties
        separate_alpha_channel = context.scene.separate_alpha_channel  # Get the value of the checkbox
        convert_cubemap_to_equirectangular(cubemap_image_path, separate_alpha_channel)
        self.report({'INFO'}, f"Converted {cubemap_image_path} to equirectangular")
        return {'FINISHED'}



class ConvertAllCubemapsOperator(bpy.types.Operator):
    bl_idname = "addon.convert_all_cubemaps"
    bl_label = "Convert All Cubemaps"

    def execute(self, context):
        import py360convert
        
        directory = context.scene.cubemaps_directory  # Get the directory from the scene properties
        separate_alpha_channel = context.scene.separate_alpha_channel  # Get the value of the checkbox

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".png"):  # replace with the file extension of your cubemap images
                    cubemap_image_path = os.path.join(root, file)
                    convert_cubemap_to_equirectangular(cubemap_image_path, separate_alpha_channel)
        self.report({'INFO'}, f"Converted all cubemaps in {directory} to equirectangular")
        return {'FINISHED'}


class ConverterPanel(bpy.types.Panel):
    bl_label = "Cubemap Tool"
    bl_idname = "MYADDON_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Cubemap Tool'

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences.addons[__name__].preferences
        layout.label(text="py360convert folder location (first install only)")
        layout.prop(preferences, "library_path")
        layout.operator("addon.install_py360convert")
        layout.row()
        layout.row()
        layout.row()
        layout.prop(context.scene, "separate_alpha_channel")
        layout.row()

        layout.label(text="Choose Singular Cubemap")
        layout.prop(context.scene, "cubemap_path")
        layout.operator("addon.convert_cubemap")
        
        layout.row()
        layout.label(text="Choose Directory of Cubemaps")

        layout.prop(context.scene, "cubemaps_directory")
        layout.operator("addon.convert_all_cubemaps")


def register():
    bpy.utils.register_class(CubemapPreferences)
    bpy.utils.register_class(InstallPy360ConvertOperator)
    bpy.utils.register_class(ConvertCubemapOperator)
    bpy.utils.register_class(ConvertAllCubemapsOperator)
    bpy.utils.register_class(ConverterPanel)

    bpy.types.Scene.cubemap_path = bpy.props.StringProperty(subtype="FILE_PATH")
    bpy.types.Scene.cubemaps_directory = bpy.props.StringProperty(subtype="DIR_PATH")

    bpy.types.Scene.separate_alpha_channel = bpy.props.BoolProperty(name="Separate Alpha Channel")

def unregister():
    bpy.utils.unregister_class(CubemapPreferences)
    bpy.utils.unregister_class(InstallPy360ConvertOperator)
    bpy.utils.unregister_class(ConvertCubemapOperator)
    bpy.utils.unregister_class(ConvertAllCubemapsOperator)
    bpy.utils.unregister_class(ConverterPanel)

    del bpy.types.Scene.cubemap_path
    del bpy.types.Scene.cubemaps_directory
    
    del bpy.types.Scene.separate_alpha_channel

if __name__ == "__main__":
    register()


#### TODO LATER
#  ADD Reverse Support  EQUIRECTANGULAR MAP --> Cubemap  (Combine the alpha channels if there are any)
    # HDRI support -  Find a way to extract light data from HDRIs to get correct gamma values into the alpha channel of the created Cubemap
    