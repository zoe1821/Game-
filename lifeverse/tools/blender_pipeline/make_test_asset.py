import bpy, sys
out_glb, out_png = sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
room = bpy.context.active_object; room.name = "Desk"
mat = bpy.data.materials.new("Wood"); mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.45, 0.27, 0.12, 1)
room.data.materials.append(mat)
room.keyframe_insert("rotation_euler", frame=1)
room.rotation_euler[2] = 3.14159
room.keyframe_insert("rotation_euler", frame=24)
bpy.ops.object.light_add(type='SUN', location=(4, -4, 6))
bpy.ops.object.camera_add(location=(6, -6, 4), rotation=(1.2, 0, 0.785))
bpy.context.scene.camera = bpy.context.active_object
bpy.ops.export_scene.gltf(filepath=out_glb, export_format='GLB', export_animations=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 8
sc.render.resolution_x = 320; sc.render.resolution_y = 180; sc.render.filepath = out_png
sc.frame_set(12)
bpy.ops.render.render(write_still=True)
print("BLENDER_OK", bpy.app.version_string)
