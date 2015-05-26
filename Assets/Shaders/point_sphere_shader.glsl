/*
 *
 * Default shader program for writing to scene buffer using GL_TRIANGLES
 *
 */

uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;





#ifdef _VERTEX_

layout(location = 0) in vec3 m_pos;
layout(location = 1) in float m_radius;

out VertexData
{
	vec3 pos;
	float radius;
} v_out;

void main() {
	v_out.pos = m_pos;
	v_out.radius = m_radius;
}

#endif






#ifdef _GEOMETRY_

layout(points) in;
layout(triangle_strip, max_vertices = 20) out;

in VertexData
{
	vec3 pos;
	float norm;
} v_in;





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
	color = grey * abs(v_in.norm.z);
}

#endif