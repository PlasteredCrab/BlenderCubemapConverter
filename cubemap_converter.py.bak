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
		
def convert_cubemap_to_equirectangular(cubemap_image_path):
    import py360convert
    
    # Load the cubemap image
    cubemap_image = bpy.data.images.load(cubemap_image_path)
    cubemap_np = np.array(cubemap_image.pixels[:]).reshape((cubemap_image.size[1], cubemap_image.size[0], 4))  # reshape to 2D array with RGBA channels

    # Convert the cubemap to an equirectangular image
    equirectangular_np = py360convert.c2e(cubemap_np, h=800, w=1600, cube_format='dice')

    # Create a new image and assign the pixels
    equirectangular_image = bpy.data.images.new("Equirectangular Image", width=1600, height=800)
    equirectangular_image.pixels = equirectangular_np.flatten().tolist()

    # Save the equirectangular image
    dir_name = os.path.dirname(cubemap_image_path)
    base_name = os.path.basename(cubemap_image_path)
    file_name, ext = os.path.splitext(base_name)
    new_file_name = f"{file_name}_equirectangular{ext}"
    equirectangular_image_path = os.path.join(dir_name, new_file_name)
    equirectangular_image.filepath_raw = equirectangular_image_path
    equirectangular_image.file_format = 'PNG'
    equirectangular_image.save()

    print(f"Saving equirectangular image to: {equirectangular_image_path}")

    #return equirectangular_image_path




def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

class InstallPy360ConvertOperator(bpy.types.Operator):
    bl_idname = "addon.install_py360convert"
    bl_label = "Install Py360convert"

    def execute(self, context):
        import numpy
        import subprocess
    
        # Check numpy version
        
        numpy_version = numpy.__version__
        print("numpy version:", numpy_version)
        if numpy_version >= '1.24.0':
            # Uninstall numpy
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "numpy"])
            # Install specific numpy version
            subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy==1.22.0"])

        preferences = context.preferences.addons[__name__].preferences
        py360convert_path = preferences.library_path

        python_executable_path = sys.executable
        site_packages_path = os.path.join(os.path.dirname(python_executable_path), 'lib', 'site-packages')

        # Check if the path ends with 'bin\lib\site-packages' and modify it
        if site_packages_path.endswith('bin\\lib\\site-packages'):
            site_packages_path = site_packages_path.replace('bin\\lib', 'lib')

        py360convert_dest_path = os.path.join(site_packages_path, 'py360convert')

        if os.path.exists(py360convert_dest_path):
            self.report({'INFO'}, "Py360convert is already installed!")
        else:
            shutil.copytree(py360convert_path, py360convert_dest_path)
            self.report({'INFO'}, "Py360convert installed successfully")

        return {'FINISHED'}




class ConvertCubemapOperator(bpy.types.Operator):
    bl_idname = "addon.convert_cubemap"
    bl_label = "Convert Cubemap"

    def execute(self, context):
        import py360convert
        
        cubemap_image_path = context.scene.cubemap_path  # Get the file path from the scene properties
        convert_cubemap_to_equirectangular(cubemap_image_path)
        self.report({'INFO'}, f"Converted {cubemap_image_path} to equirectangular")
        return {'FINISHED'}



class ConvertAllCubemapsOperator(bpy.types.Operator):
    bl_idname = "addon.convert_all_cubemaps"
    bl_label = "Convert All Cubemaps"

    def execute(self, context):
        import py360convert
        
        directory = context.scene.cubemaps_directory  # Get the directory from the scene properties

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".png"):  # replace with the file extension of your cubemap images
                    cubemap_image_path = os.path.join(root, file)
                    convert_cubemap_to_equirectangular(cubemap_image_path)
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


def unregister():
    bpy.utils.unregister_class(CubemapPreferences)
    bpy.utils.unregister_class(InstallPy360ConvertOperator)
    bpy.utils.unregister_class(ConvertCubemapOperator)
    bpy.utils.unregister_class(ConvertAllCubemapsOperator)
    bpy.utils.unregister_class(ConverterPanel)

    del bpy.types.Scene.cubemap_path
    del bpy.types.Scene.cubemaps_directory


if __name__ == "__main__":
    register()
