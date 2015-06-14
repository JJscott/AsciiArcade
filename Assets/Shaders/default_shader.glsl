/*
 *
 * Default shader program for writing to scene buffer using GL_TRIANGLES
 *
 */

uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;

uniform vec3 color = vec3(1.0);

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
	vec4 pos = (projectionMatrix * modelViewMatrix * vec4(m_pos, 1.0));
	vec4 norm = (projectionMatrix * modelViewMatrix * vec4(m_norm, 0.0));
	gl_Position = pos;
	v_out.pos = pos.xyz;
	v_out.norm = norm.xyz;
	v_out.tex = m_uv;
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