class_name BuffetPlacement
extends RefCounted

const CELL = 0.003
const N = 101
const MID = 50
const RADIUS = 0.143
var grid = PackedFloat32Array()

func _init():
	reset()

func reset():
	grid.resize(N * N)
	for z in range(N):
		for x in range(N):
			var radius = Vector2(x - MID, z - MID).length() * CELL
			grid[z * N + x] = 0.009 if radius < 0.106 else 0.01 + (minf(radius, 0.139) - 0.106) / 0.033 * 0.0135

func occupy(portion: Dictionary):
	var dx = roundi(portion.x / CELL) + MID
	var dz = roundi(portion.z / CELL) + MID
	var shape: Array = portion.shape
	for sample in shape:
		var index = (int(sample[1]) + dz) * N + int(sample[0]) + dx
		if index >= 0 and index < grid.size():
			grid[index] = maxf(grid[index], portion.y + sample[3])

func height_at(shape: Array, x: float, z: float) -> float:
	var dx = roundi(x / CELL) + MID
	var dz = roundi(z / CELL) + MID
	var height = 0.0
	for sample in shape:
		height = maxf(height, grid[(int(sample[1]) + dz) * N + int(sample[0]) + dx] - sample[2])
	return height + 0.0002

func fit(shape: Array, preferred = null) -> Dictionary:
	var best = {}
	var score = INF
	var limit_squared = pow(RADIUS / CELL, 2)
	for z in range(-44, 45, 2):
		for x in range(-44, 45, 2):
			var height = 0.0
			var valid = true
			for sample in shape:
				var ix = x + int(sample[0])
				var iz = z + int(sample[1])
				if ix * ix + iz * iz > limit_squared:
					valid = false
					break
				height = maxf(height, grid[(iz + MID) * N + ix + MID] - sample[2])
			if not valid:
				continue
			var distance = Vector2(x * CELL, z * CELL).length() if preferred == null else Vector2(x * CELL - preferred.x, z * CELL - preferred.z).length()
			var candidate = height * 5.0 + distance * 0.06 if preferred == null else distance + height * 0.35
			if candidate < score:
				score = candidate
				best = {"x": x * CELL, "y": height + 0.0002, "z": z * CELL}
	return best

static func sample_shape(root: Node3D) -> Array:
	var samples = {}
	_sample_node(root, Transform3D.IDENTITY, samples)
	return samples.values()

static func _sample_node(node: Node3D, transform: Transform3D, samples: Dictionary):
	if node is MeshInstance3D and node.mesh:
		var faces = node.mesh.get_faces()
		for i in range(0, faces.size(), 3):
			var a = transform * faces[i]
			var b = transform * faces[i + 1]
			var c = transform * faces[i + 2]
			# Measurements remain in the comparison's left-handed coordinate convention.
			a.z = -a.z
			b.z = -b.z
			c.z = -c.z
			_triangle(samples, a, b, c)
	for child in node.get_children():
		if child is Node3D:
			_sample_node(child, transform * child.transform, samples)

static func _triangle(samples: Dictionary, a: Vector3, b: Vector3, c: Vector3):
	var min_x = floori(minf(a.x, minf(b.x, c.x)) / CELL)
	var max_x = ceili(maxf(a.x, maxf(b.x, c.x)) / CELL)
	var min_z = floori(minf(a.z, minf(b.z, c.z)) / CELL)
	var max_z = ceili(maxf(a.z, maxf(b.z, c.z)) / CELL)
	var determinant = (b.z - c.z) * (a.x - c.x) + (c.x - b.x) * (a.z - c.z)
	if absf(determinant) < 1e-12:
		return
	for iz in range(min_z, max_z + 1):
		for ix in range(min_x, max_x + 1):
			var x = ix * CELL
			var z = iz * CELL
			var u = ((b.z - c.z) * (x - c.x) + (c.x - b.x) * (z - c.z)) / determinant
			var v = ((c.z - a.z) * (x - c.x) + (a.x - c.x) * (z - c.z)) / determinant
			var w = 1.0 - u - v
			if u < -0.025 or v < -0.025 or w < -0.025:
				continue
			var y = u * a.y + v * b.y + w * c.y
			var key = Vector2i(ix, iz)
			if samples.has(key):
				samples[key][2] = minf(samples[key][2], y)
				samples[key][3] = maxf(samples[key][3], y)
			else:
				samples[key] = [ix, iz, y, y]
