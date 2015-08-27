/*
 *
 * Default shader program for writing to scene buffer using GL_TRIANGLES
 *
 */

uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;

uniform vec3 explosion_point;
uniform float speed;
uniform float time;

#ifdef _VERTEX_

layout(location = 0) in vec3 m_pos;
layout(location = 1) in vec3 m_norm;
layout(location = 2) in vec2 m_uv;


out VertexData
{
	vec4 pos;
	vec4 norm;
	vec3 tex;
} v_out;

void main() {
	vec4 pos = modelViewMatrix * vec4(m_pos, 1.0);
	vec4 norm = modelViewMatrix * vec4(m_norm, 0.0);
	v_out.pos = pos;
	v_out.norm = norm;
	v_out.tex = m_uv;
}

#endif








#ifdef _GEOMETRY_

layout(triangles) in;
layout(triangle_strip, max_vertices=3) out;

in InVertexData
{
	vec4 pos;
	vec4 norm;
	vec3 tex;
} v_in[];

out OutVertexData
{
	vec3 pos;
	vec3 norm;
	vec3 tex;
} v_out;

void main()
{
	vec4 p0 = v_in[0].pos;
	vec4 p1 = v_in[1].pos;
	vec4 p2 = v_in[2].pos;

	vec4 c = (p0 + p1 + p2)/3;
	vec4 e = modelViewMatrix * vec4(explosion_point, 1.0)
	vec3 d = (c.xyz - e.xyz) * speed * time;

	vec3 pos = (projectionMatrix * vec4(d + p0.xyz, 1.0)).xyz
	gl_Position = pos
	v_out.pos = pos
	v_out.norm = (projectionMatrix * v_in[0].norm).xyz
	v_out.tex = v_in[0].tex
	EmitVertex();

	pos = (projectionMatrix * vec4(d + p1.xyz, 1.0)).xyz
	gl_Position = pos
	v_out.pos = pos
	v_out.norm = (projectionMatrix * v_in[1].norm).xyz
	v_out.tex = v_in[1].tex
	EmitVertex();

	pos = (projectionMatrix * vec4(d + p2.xyz, 1.0)).xyz
	gl_Position = pos
	v_out.pos = pos
	v_out.norm = (projectionMatrix * v_in[2].norm).xyz
	v_out.tex = v_in[2].tex
	EmitVertex();

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

out vec3 color;

void main(){
	vec3 grey = vec3(0.8, 0.8, 0.8);
	color = grey * abs(normalize(v_in.norm).z);
}

#endif