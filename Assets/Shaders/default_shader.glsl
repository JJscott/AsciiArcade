/*
 *
 * Default shader program for writing to scene buffer using GL_TRIANGLES
 *
 */

uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;

uniform vec3 color = vec3(1.0);

uniform float explode_time = 0.0;

#ifdef _VERTEX_

layout(location = 0) in vec3 m_pos;
layout(location = 1) in vec3 m_norm;
layout(location = 2) in vec3 m_uv;

out VertexData
{
	vec3 pos;
	vec3 norm;
	vec3 tex;
} v_out;

void main() {
	v_out.pos = m_pos;
	v_out.norm = m_norm;
	v_out.tex = m_uv;
}

#endif


#ifdef _GEOMETRY_

layout(triangles) in;
layout(triangle_strip, max_vertices=3) out;

in VertexData
{
	vec3 pos;
	vec3 norm;
	vec3 tex;
} v_in[];

out VertexData
{
	vec3 pos;
	vec3 norm;
	vec3 tex;
} v_out;

mat3 rotationMatrix(vec3 axis, float angle) {
	axis = normalize(axis);
	float s = -sin(angle);
	float c = cos(angle);
	float oc = 1.0 - c;
	return mat3(
		oc * axis.x * axis.x + c,           oc * axis.x * axis.y - axis.z * s,  oc * axis.z * axis.x + axis.y * s,
		oc * axis.x * axis.y + axis.z * s,  oc * axis.y * axis.y + c,           oc * axis.y * axis.z - axis.x * s,
		oc * axis.z * axis.x - axis.y * s,  oc * axis.y * axis.z + axis.x * s,  oc * axis.z * axis.z + c
	);
}

vec3 longest(vec3 a, vec3 b, vec3 c) {
	vec3 r = mix(a, b, bvec3(length(b) > length(a)));
	r = mix(r, c, bvec3(length(c) > length(r)));
	return r;
}

void main() {
	
	vec3 p0 = v_in[0].pos;
	vec3 p1 = v_in[1].pos;
	vec3 p2 = v_in[2].pos;
	
	// rotation centre
	vec3 c = longest(p0, p1, p2);
	
	// face normal
	vec3 v0 = p0 - p1;
	vec3 v1 = p2 - p1;
	vec3 fn = normalize(cross(v1, v0));
	vec3 on = normalize(c);
	
	// we may have some backface issues
	// this negates the face normal to align it to the object normal
	fn = mix(fn, -fn, bvec3(dot(fn, on) < 0.0));
	
	// rotation from face norm towards object norm
	// being careful of parallel normals
	bool do_rot = length(fn - on) > 0.05;
	mat3 rot = rotationMatrix(mix(vec3(1, 0, 0), cross(fn, on), bvec3(do_rot)), acos(dot(fn, on)) * (1.0 - exp(-0.2 * explode_time)));
	
	for (int i = 0; i < 3; i++) {
		// exploded vertex position
		vec3 p = v_in[i].pos;
		p -= c;
		p = rot * p;
		p += c + (rot * v_in[i].norm) * explode_time;
		
		// emit
		v_out.pos = (modelViewMatrix * vec4(p, 1.0)).xyz;
		v_out.norm = rot * v_in[i].norm;
		v_out.tex = v_in[i].tex;
		gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
		EmitVertex();
	}
	EndPrimitive();
	
}

#endif


#ifdef _FRAGMENT_

in VertexData
{
	vec3 pos;
	vec3 norm;
	vec3 tex;
} v_in;

out vec3 frag_color;

void main(){
	//vec3 grey = vec3(0.8, 0.8, 0.8);
	//color = grey * abs(normalize(v_in.norm).z);
	frag_color = color;
}

#endif