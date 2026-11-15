extends Control
func _ready() -> void:
	var data: Dictionary[String, int] = {"answer": 42}
	var f := FileAccess.open("user://smoke.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(data)); f.close()
	var back: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("user://smoke.json"))
	var msg := "EXPORT_SMOKE_OK platform=%s answer=%d debug=%s" % [
		OS.get_name(), int(back["answer"]), OS.is_debug_build()
	]
	print(msg)
	var l := Label.new(); l.text = msg; l.name = "Msg"; add_child(l)
	if OS.get_cmdline_user_args().has("--quit-after-check"):
		get_tree().quit(0)
