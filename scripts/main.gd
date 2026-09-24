extends Node3D

const Placement = preload("res://scripts/placement.gd")
const HALL = preload("res://assets/environment/hall.glb")
const PLATE = preload("res://assets/environment/plate.glb")
const SIGN_FONT = preload("res://assets/fonts/Lora-Regular.ttf")
var camera: Camera3D
var light: DirectionalLight3D
var rig: Node3D
var plate: Node3D
var station_root: Node3D
var models = {}
var triangles = {}
var shapes = {}
var foods = []
var portions: Array = []
var config = {}
var placement = Placement.new()
var station = 0
var started = false
var moving = false
var plate_view = false
var completed = false
var selected = ""
var look = Vector3.ZERO
var bridge = null
var callback = null
var status_clock = 0.0
var viewport_size = Vector2.ZERO
var last_action_ms = 0

func v(x: float, y: float, z: float) -> Vector3:
	return Vector3(x, y, -z)

func station_x(index: int) -> float:
	return (index - 7) * 0.7

func _ready():
	var hall = HALL.instantiate()
	hall.scale.z = -1
	add_child(hall)
	disable_shadows(hall)
	var environment = WorldEnvironment.new()
	environment.environment = Environment.new()
	environment.environment.background_mode = Environment.BG_COLOR
	environment.environment.background_color = Color(0.82, 0.86, 0.87)
	environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_color = Color(0.9, 0.94, 1.0)
	environment.environment.ambient_light_energy = 0.2
	environment.environment.ambient_light_sky_contribution = 0.0
	environment.environment.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	var sky = Sky.new()
	var sky_material = ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color(0.55, 0.65, 0.77)
	sky_material.sky_horizon_color = Color(0.85, 0.87, 0.85)
	sky_material.ground_bottom_color = Color(0.24, 0.23, 0.2)
	sky_material.ground_horizon_color = Color(0.66, 0.67, 0.61)
	sky.sky_material = sky_material
	environment.environment.sky = sky
	environment.environment.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	add_child(environment)
	light = DirectionalLight3D.new()
	light.light_color = Color(1, 0.98, 0.96)
	light.light_energy = 0.27
	light.shadow_enabled = true
	light.directional_shadow_max_distance = 12
	light.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	light.shadow_bias = 0.025
	light.shadow_normal_bias = 0.1
	add_child(light)
	light.look_at(v(-0.45, -1, 0.5), Vector3.UP)
	camera = Camera3D.new()
	camera.near = 0.015
	camera.far = 55
	camera.keep_aspect = Camera3D.KEEP_HEIGHT
	add_child(camera)
	camera.make_current()
	rig = Node3D.new()
	add_child(rig)
	rig.visible = false
	plate = PLATE.instantiate()
	plate.scale.z = -1
	rig.add_child(plate)
	disable_shadows(plate)
	plate.position = v(0, 0.93, -0.59)
	plate.visible = false
	# Portion parents are separate from the reflected plate mesh.
	station_root = Node3D.new()
	add_child(station_root)
	var menu = JSON.parse_string(FileAccess.get_file_as_string("res://assets/menu.json"))
	for food in menu.foods:
		models[food.id] = load("res://assets/food/%s.glb" % food.id)
	fit_camera()
	if OS.has_feature("web"):
		bridge = JavaScriptBridge.get_interface("godotBridge")
		callback = JavaScriptBridge.create_callback(_receive_command)
		bridge.register(callback, JSON.stringify({"version": Engine.get_version_info().string, "renderer": "gl_compatibility", "foodModels": models.size()}))
	else:
		configure({"foods": menu.foods, "config": {"maxPortions": 40, "allowRemoval": true}, "portions": []})
		print("Godot scene ready. Use the web shell for the participant interface.")

func _process(delta):
	if not camera:
		return
	var size = get_viewport().get_visible_rect().size
	if size != viewport_size:
		viewport_size = size
		if not moving:
			fit_camera()
	status_clock += delta
	if bridge and status_clock >= 0.2:
		status_clock = 0.0
		bridge.state(JSON.stringify(snapshot()))

func _receive_command(arguments: Array):
	if arguments.size() == 1:
		call_deferred("_execute_command", JSON.parse_string(str(arguments[0])))

func _execute_command(command: Dictionary):
	var action = str(command.get("action", ""))
	var payload = command.get("payload", {})
	var result = {}
	var time_start = Time.get_ticks_msec()
	match action:
		"configure":
			configure(payload)
		"begin":
			started = true
			rig.visible = true
			plate.visible = true
			await move_view(int(payload.get("station", 0)), false, bool(payload.get("animate", true)))
		"view":
			await move_view(int(payload.station), bool(payload.plate), bool(payload.get("animate", true)))
		"add":
			if not moving and started and not completed and portions.size() < int(config.get("maxPortions", 40)):
				create_portion(payload, true)
		"remove":
			if not moving and not completed and config.get("allowRemoval", true):
				remove_portion(str(payload.portionId))
		"pick":
			result = pick_at(Vector2(payload.x, payload.y))
		"drop":
			result = drop(str(payload.get("portionId", "")), Vector2(payload.x, payload.y))
		"select":
			selected = str(payload.get("portionId", ""))
		"capture":
			result = {"data": await photograph()}
		"complete":
			completed = true
		"resize":
			fit_camera()
	last_action_ms = Time.get_ticks_msec() - time_start
	result["state"] = snapshot()
	if bridge:
		bridge.resolve(command.id, JSON.stringify(result))

func configure(payload: Dictionary):
	config = payload.config
	foods = payload.foods
	completed = bool(payload.get("completed", false))
	for child in station_root.get_children():
		child.free()
	for i in range(foods.size()):
		var food = foods[i]
		add_label(food.name, v(station_x(i), 0.9465, -0.348))
		for k in range(4 if food.id == "pizza" else 6):
			var root = spawn(food.id)
			station_root.add_child(root)
			root.position = v(station_x(i) + (k % 3 - 1) * 0.139, 0.946, (floori(k / 3.0) - 0.5) * 0.17)
			root.rotation.y = -0.2 if k % 2 else 0.15
	for portion in portions:
		portion.root.free()
	portions.clear()
	placement.reset()
	for record in payload.get("portions", []):
		create_portion(record, false)
	rig.position.x = station_x(0)
	fit_camera()

func disable_shadows(node: Node):
	if node is GeometryInstance3D:
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for child in node.get_children():
		disable_shadows(child)

func add_label(text: String, position_: Vector3):
	var paper = MeshInstance3D.new()
	paper.mesh = PlaneMesh.new()
	paper.mesh.size = Vector2(0.221, 0.075)
	var material = StandardMaterial3D.new()
	material.albedo_color = Color("f4f1e6")
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	paper.material_override = material
	paper.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	paper.position = position_
	station_root.add_child(paper)
	var label = Label3D.new()
	label.text = text
	label.font = SIGN_FONT
	label.font_size = 48
	label.pixel_size = minf(0.0004, 0.202 / SIGN_FONT.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, 48).x)
	label.modulate = Color("33493c")
	label.outline_size = 0
	label.position = position_ + Vector3.UP * 0.0002
	label.rotation.x = -PI / 2
	station_root.add_child(label)

func spawn(food_id: String) -> Node3D:
	var root = Node3D.new()
	var mesh = models[food_id].instantiate()
	# Babylon's default GLTF root reflects X; this 180-degree rotation maps
	# the same food orientation into Godot's right-handed scene.
	mesh.rotation.y = PI
	root.add_child(mesh)
	return root

func shape_for(food_id: String, root: Node3D, angle: float) -> Array:
	var key = food_id + ":" + str(snappedf(angle, 0.000001))
	if not shapes.has(key):
		# sample_shape excludes the root transform: include portion rotation explicitly.
		var holder = Node3D.new()
		var duplicate = root.duplicate()
		duplicate.position = Vector3.ZERO
		duplicate.rotation.y = -angle
		holder.add_child(duplicate)
		shapes[key] = Placement.sample_shape(holder)
		holder.free()
	return shapes[key]

func create_portion(record: Dictionary, animate: bool):
	var root = spawn(record.foodId)
	rig.add_child(root)
	var angle = float(record.get("rotation", fmod(portions.size() * 137.5, 360) * PI / 180))
	var shape = shape_for(record.foodId, root, angle)
	root.rotation.y = -angle
	var pose = record.get("position", {})
	if pose.is_empty():
		pose = placement.fit(shape)
	if pose.is_empty():
		root.free()
		push_error("Portion cannot fit on plate: " + str(record.foodId))
		return
	var portion = {"portionId": record.portionId, "foodId": record.foodId, "addedAt": record.addedAt, "angle": angle, "x": float(pose.x), "y": float(pose.y), "z": float(pose.z), "shape": shape, "root": root, "tween": null}
	portions.append(portion)
	placement.occupy(portion)
	var target = v(portion.x, 0.93 + portion.y, -0.59 + portion.z)
	root.position = target
	if animate:
		root.position = v(0, 1.005, -0.19)
		var from = root.position
		var tween = create_tween()
		portion.tween = tween
		tween.tween_method(func(t):
			if is_instance_valid(root):
				root.position = from.lerp(target, t) + Vector3.UP * sin(t * PI) * 0.045,
			0.0, 1.0, 0.43).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)

func repack(exclude = null):
	placement.reset()
	var sorted = portions.duplicate()
	sorted.sort_custom(func(a, b): return a.y < b.y)
	for portion in sorted:
		if portion == exclude:
			continue
		stop_animation(portion)
		portion.y = placement.height_at(portion.shape, portion.x, portion.z)
		portion.root.position = v(portion.x, 0.93 + portion.y, -0.59 + portion.z)
		placement.occupy(portion)

func stop_animation(portion: Dictionary):
	if portion.tween and portion.tween.is_valid():
		portion.tween.kill()
	portion.tween = null

func remove_portion(id: String):
	for portion in portions:
		if portion.portionId == id:
			stop_animation(portion)
			portion.root.free()
			portions.erase(portion)
			selected = ""
			repack()
			fit_camera()
			return

func meal_height() -> float:
	var height = 0.03
	for portion in portions:
		for sample in portion.shape:
			height = maxf(height, portion.y + sample[3])
	return height

func plate_pose(fov: float, aspect: float) -> Dictionary:
	var height = meal_height()
	var center = v(rig.position.x, 0.93 + height * 0.5, -0.59)
	var half_fov = atan(tan(fov * 0.5) * minf(1, aspect))
	var radius = Vector2(0.145, height * 0.5).length()
	var distance = maxf(0.54, radius / sin(half_fov) * 1.12)
	return {"target": center + v(0, 1, -0.34).normalized() * distance, "look": center}

func fit_camera():
	var size = get_viewport().get_visible_rect().size
	var aspect = size.x / maxf(size.y, 1)
	var fov = 2 * atan(tan(0.42) * maxf(1, 0.85 / aspect))
	camera.fov = rad_to_deg(fov)
	if not started:
		camera.position = v(0, 1, 0) + v(0, 4.1, -7.5) * maxf(1, 1.5 / maxf(0.85, aspect))
		look = v(0, 1, 0)
	elif plate_view and not moving:
		var pose = plate_pose(fov, aspect)
		camera.position = pose.target
		look = pose.look
	camera.look_at(look)

func move_view(index: int, to_plate: bool, animate: bool):
	if moving:
		return
	station = clampi(index, 0, foods.size() - 1)
	moving = true
	plate_view = to_plate
	selected = ""
	var x = station_x(station)
	var from_position = camera.position
	var from_look = look
	var from_x = rig.position.x
	rig.position.x = x
	var size = get_viewport().get_visible_rect().size
	var pose = plate_pose(deg_to_rad(camera.fov), size.x / maxf(size.y, 1))
	rig.position.x = from_x
	var target = pose.target if to_plate else v(x, 1.62, -1.24)
	var target_look = pose.look if to_plate else v(x, 0.95, -0.28)
	if animate:
		var tween = create_tween()
		tween.tween_method(func(t):
			camera.position = from_position.lerp(target, t)
			look = from_look.lerp(target_look, t)
			camera.look_at(look)
			rig.position.x = lerpf(from_x, x, t), 0.0, 1.0, 0.5 if to_plate else 0.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		await tween.finished
	else:
		camera.position = target
		look = target_look
		rig.position.x = x
		camera.look_at(look)
	moving = false
	fit_camera()

func plane_point(point: Vector2):
	var origin = camera.project_ray_origin(point)
	var direction = camera.project_ray_normal(point)
	if absf(direction.y) < 0.000001:
		return null
	var distance = (0.94 - origin.y) / direction.y
	if distance < 0:
		return null
	var hit = origin + direction * distance - v(rig.position.x, 0.93, -0.59)
	return {"x": hit.x, "z": -hit.z}

func pick_at(point: Vector2) -> Dictionary:
	var origin = camera.project_ray_origin(point)
	var direction = camera.project_ray_normal(point)
	if not plate_view:
		var box = AABB(v(station_x(station) - 0.26, 0.946, 0.215), Vector3(0.52, 0.1, 0.43))
		if box.intersects_ray(origin, direction) != null:
			return {"station": station}
	var best = INF
	var found = ""
	for portion in portions:
		var root: Node3D = portion.root
		var inverse = root.global_transform.affine_inverse()
		# Test in centimetres: Godot's fixed parallel-ray epsilon otherwise
		# rejects the sub-millimetre triangles in these life-size food models.
		var local_origin = (inverse * origin) * 100.0
		var local_direction = inverse.basis * direction
		var faces: PackedVector3Array = food_triangles(portion.foodId)
		for i in range(0, faces.size(), 3):
			var hit = Geometry3D.ray_intersects_triangle(local_origin, local_direction, faces[i], faces[i + 1], faces[i + 2])
			if hit != null:
				var distance = origin.distance_to(root.global_transform * (hit / 100.0))
				if distance < best:
					best = distance
					found = portion.portionId
	return {"portion": found} if found else {}

func food_triangles(id: String) -> PackedVector3Array:
	if not triangles.has(id):
		var root = spawn(id)
		var faces = PackedVector3Array()
		collect_faces(root, Transform3D.IDENTITY, faces)
		for i in range(faces.size()):
			faces[i] *= 100.0
		triangles[id] = faces
		root.free()
	return triangles[id]

func collect_faces(node: Node3D, transform: Transform3D, output: PackedVector3Array):
	if node is MeshInstance3D and node.mesh:
		for point in node.mesh.get_faces():
			output.append(transform * point)
	for child in node.get_children():
		if child is Node3D:
			collect_faces(child, transform * child.transform, output)

func drop(id: String, point: Vector2) -> Dictionary:
	var preferred = plane_point(point)
	var on_plate = preferred != null and Vector2(preferred.x, preferred.z).length() < 0.145
	if on_plate and not moving and not completed and plate_view:
		for portion in portions:
			if portion.portionId == id:
				stop_animation(portion)
				repack(portion)
				var pose = placement.fit(portion.shape, preferred)
				portion.merge(pose, true)
				portion.root.position = v(portion.x, 0.93 + portion.y, -0.59 + portion.z)
				placement.occupy(portion)
				fit_camera()
				return {"onPlate": true, "moved": id}
	return {"onPlate": on_plate}

func photograph() -> String:
	for portion in portions:
		stop_animation(portion)
		portion.root.position = v(portion.x, 0.93 + portion.y, -0.59 + portion.z)
	var viewport = SubViewport.new()
	viewport.size = Vector2i(1024, 1024)
	viewport.world_3d = get_viewport().world_3d
	viewport.msaa_3d = Viewport.MSAA_2X
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(viewport)
	var photo_camera = Camera3D.new()
	viewport.add_child(photo_camera)
	photo_camera.near = 0.01
	photo_camera.fov = rad_to_deg(0.68)
	var pose = plate_pose(0.68, 1.0)
	photo_camera.position = pose.target
	photo_camera.look_at(pose.look)
	photo_camera.make_current()
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var image = viewport.get_texture().get_image()
	var png = image.save_png_to_buffer()
	viewport.queue_free()
	return "data:image/png;base64," + Marshalls.raw_to_base64(png)

func project(point: Vector3) -> Dictionary:
	var p = camera.unproject_position(point)
	return {"x": p.x, "y": p.y}

func snapshot() -> Dictionary:
	var records = []
	var points = []
	var height = 0.03
	for portion in portions:
		var extent = 0.0
		var center_sample = portion.shape[0]
		var center_distance = INF
		for sample in portion.shape:
			extent = maxf(extent, Vector2(portion.x + sample[0] * Placement.CELL, portion.z + sample[1] * Placement.CELL).length())
			height = maxf(height, portion.y + sample[3])
			var distance = sample[0] * sample[0] + sample[1] * sample[1]
			if distance < center_distance:
				center_distance = distance
				center_sample = sample
		records.append({"portionId": portion.portionId, "foodId": portion.foodId, "addedAt": portion.addedAt, "x": portion.x, "y": portion.y, "z": portion.z, "angle": portion.angle, "extent": extent})
		points.append(project(portion.root.global_position + v(center_sample[0] * Placement.CELL, center_sample[3], center_sample[1] * Placement.CELL)))
	return {"portions": records, "points": {"dish": project(v(station_x(station), 0.97, 0)), "plate": project(v(rig.position.x, 0.95, -0.59)), "portions": points}, "station": station, "moving": moving, "plateView": plate_view, "selected": selected, "fps": Engine.get_frames_per_second(), "engine": "Godot " + Engine.get_version_info().string, "models": models.size(), "lastActionMs": last_action_ms, "mealHeight": height}
