
def loadOBJ(filename):
	verts = [[0.0, 0.0, 0.0]]
	texts = [[0.0, 0.0]]
	norms = [[0.0, 0.0, 0.0]]

	vertsOut = []
	textsOut = []
	normsOut = []

	for line in open(filename, "r"):
		vals = line.split()
		if len(vals) > 0:
			if vals[0] == "v":
				v = map(float, vals[1:4])
				verts.append(v)
			elif vals[0] == "vn":
				n = map(float, vals[1:4])
				norms.append(n)
			elif vals[0] == "vt":
				t = map(float, vals[1:3])
				texts.append(t)
			elif vals[0] == "f":
				for f in vals[1:4]: # Assume triangluation
					w = f.split("/")
					vertsOut.append(list(verts[int(w[0])]))
					if len(w) == 2 or w[1]: textsOut.append(list(texts[int(w[1])]))
					else: textsOut.append([0.0,0.0])
					if len(w) == 3: normsOut.append(list(norms[int(w[2])]))
					else: normsOut.append([0.0, 0.0, 1.0]) # Fuck you for not providing normals, it'll just point toward some direction then

	return vertsOut, normsOut, textsOut
