/*
 *
 * Shader program drawing red spheres
 *
 */

uniform mat4 projectionMatrix;
uniform mat4 viewMatrix;

uniform samplerBuffer sampler_ast_pos;
uniform samplerBuffer sampler_ast_ori;
uniform samplerBuffer sampler_ast_rot;

#ifdef _VERTEX_

layout(location = 0) in vec3 m_pos;
layout(location = 1) in vec3 m_norm;
layout(location = 2) in vec3 m_uv;

layout(location = 3) in int asteroid_id; // instanced

out VertexData
{
	vec3 pos;
	vec3 norm;
	vec3 tex;
} v_out;

void main() {
	
	vec4 temp;
	temp = texelFetch(sampler_ast_pos, asteroid_id);
	vec3 apos = temp.xyz;
	float ascale = temp.w;
	vec4 aori = texelFetch(sampler_ast_ori, asteroid_id);
	vec3 arot = texelFetch(sampler_ast_rot, asteroid_id).xyz;
	
	// TODO rotation shit
	
	vec4 pos = viewMatrix * vec4(m_pos * ascale + apos, 1.0);
	vec4 norm = viewMatrix * vec4(m_norm, 0.0);
	gl_Position = projectionMatrix * pos;
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

out vec3 color;

void main(){
	vec3 grey = vec3(0.8, 0.8, 0.8);
	color = grey * abs(normalize(v_in.norm).z);
}

#endif