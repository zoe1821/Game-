extends SceneTree
# Loads the .glb produced by make_test_asset.py and reports what survived import.
func _init() -> void:
	var packed: PackedScene = load("res://desk.glb")
	var scene: Node = packed.instantiate()
	var meshes: Array[Node] = scene.find_children("*", "MeshInstance3D", true, false)
	var players: Array[Node] = scene.find_children("*", "AnimationPlayer", true, false)
	var ok := meshes.size() == 1 and players.size() == 1
	var material_name := ""
	var animations: PackedStringArray = []
	if ok:
		var mesh_instance := meshes[0] as MeshInstance3D
		material_name = mesh_instance.mesh.surface_get_material(0).resource_name
		animations = (players[0] as AnimationPlayer).get_animation_list()
		ok = material_name == "Wood" and animations.size() == 1
	var verdict := "OK" if ok else "FAIL"
	print("BLENDER_PIPELINE_%s meshes=%d material=%s animations=%s" % [
		verdict, meshes.size(), material_name, animations
	])
	scene.free()
	quit(0 if ok else 1)
