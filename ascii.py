
from __future__ import division

import pygame
import ctypes
import itertools
import math
import vec
from pygloo import *
from simpleShader import makeProgram

_shader_fullscreen_source = '''

// vertex shader
#ifdef _VERTEX_

flat out int instanceID;

void main() {
	instanceID = gl_InstanceID;
}

#endif

// geometry shader
#ifdef _GEOMETRY_

layout(points) in;
layout(triangle_strip, max_vertices = 3) out;

flat in int instanceID[];

out vec2 fullscreen_tex_coord;
flat out int fullscreen_layer;

void main() {
	// output a single triangle that covers the whole screen
	// if instanced, set layer to instance id
	
	gl_Position = vec4(3.0, 1.0, 0.0, 1.0);
	gl_Layer = instanceID[0];
	fullscreen_layer = instanceID[0];
	fullscreen_tex_coord = vec2(2.0, 1.0);
	EmitVertex();
	
	gl_Position = vec4(-1.0, 1.0, 0.0, 1.0);
	gl_Layer = instanceID[0];
	fullscreen_layer = instanceID[0];
	fullscreen_tex_coord = vec2(0.0, 1.0);
	EmitVertex();
	
	gl_Position = vec4(-1.0, -3.0, 0.0, 1.0);
	gl_Layer = instanceID[0];
	fullscreen_layer = instanceID[0];
	fullscreen_tex_coord = vec2(0.0, -1.0);
	EmitVertex();
	
	EndPrimitive();
	
}

#endif

// fragment shader
#ifdef _FRAGMENT_

in vec2 fullscreen_tex_coord;
flat in int fullscreen_layer;

// main() should be implemented by includer

#endif
'''

_shader_font_source = _shader_fullscreen_source + '''

uniform sampler2D sampler_fontatlas;

#ifdef _FRAGMENT_

out vec4 frag_color;

void main() {
	vec2 uv = mod(vec2(1.0, -1.0) * fullscreen_tex_coord, vec2(1.0));
	int codepoint = fullscreen_layer;
	int ix = codepoint & 0xF;
	int iy = codepoint >> 4;
	frag_color = texture(sampler_fontatlas, (vec2(ix, iy) + uv) / 16.0);
}

#endif
'''

_shader_edge_source = _shader_fullscreen_source + '''

uniform sampler2D sampler_color;
uniform sampler2D sampler_depth;

uniform mat4 proj_inv;

#ifdef _FRAGMENT_

// output is RGB-edge
out vec4 frag_color;

// frei-chen implementation from here
// http://rastergrid.com/blog/2011/01/frei-chen-edge-detector/

// frei-chen convolution kernels
const mat3 freichen_kernel[9] = mat3[](
	1.0/(2.0*sqrt(2.0)) * mat3( 1.0, sqrt(2.0), 1.0, 0.0, 0.0, 0.0, -1.0, -sqrt(2.0), -1.0 ),
	1.0/(2.0*sqrt(2.0)) * mat3( 1.0, 0.0, -1.0, sqrt(2.0), 0.0, -sqrt(2.0), 1.0, 0.0, -1.0 ),
	1.0/(2.0*sqrt(2.0)) * mat3( 0.0, -1.0, sqrt(2.0), 1.0, 0.0, -1.0, -sqrt(2.0), 1.0, 0.0 ),
	1.0/(2.0*sqrt(2.0)) * mat3( sqrt(2.0), -1.0, 0.0, -1.0, 0.0, 1.0, 0.0, 1.0, -sqrt(2.0) ),
	1.0/2.0 * mat3( 0.0, 1.0, 0.0, -1.0, 0.0, -1.0, 0.0, 1.0, 0.0 ),
	1.0/2.0 * mat3( -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0 ),
	1.0/6.0 * mat3( 1.0, -2.0, 1.0, -2.0, 4.0, -2.0, 1.0, -2.0, 1.0 ),
	1.0/6.0 * mat3( -2.0, 1.0, -2.0, 1.0, 4.0, 1.0, -2.0, 1.0, -2.0 ),
	1.0/3.0 * mat3( 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0 )
);

// laplacian kernel
const mat3 laplace_kernel = mat3(0.5, 1.0, 0.5, 1.0, -6.0, 1.0, 0.5, 1.0, 0.5) / 6.0;

const vec2[] deltas = vec2[](vec2(1, 0), vec2(0, 1), vec2(-1, 0), vec2(0, -1));

float convolve(mat3 a, mat3 b) {
	return dot(a[0], b[0]) + dot(a[1], b[1]) + dot(a[2], b[2]);
}

float freichen_edge(mat3 img) {
	float cnv[9];
	// calculate the (squared) convolution values for all the masks
	for (int i=0; i<9; i++) {
		float dp3 = convolve(freichen_kernel[i], img);
		cnv[i] = dp3 * dp3; 
	}
	// compare edge filter sum to total sum
	float m = (cnv[0] + cnv[1]) + (cnv[2] + cnv[3]);
	float s = (cnv[4] + cnv[5]) + (cnv[6] + cnv[7]) + (cnv[8] + m);
	return sqrt(m / s);
}

float texture_depth(vec2 uv) {
	float d0 = texture(sampler_depth, uv).r;
	d0 = d0 * 2.0 - 1.0;
	vec4 p = proj_inv * vec4(0, 0, d0, 1);
	p /= p.w;
	return -p.z;
}

void main() {
	
	// local depth image
	mat3 img_d;
	
	// sample 3x3 neighbourhood
	for(int dx = -1; dx <= 1; ++dx) {
		for(int dy = -1; dy <= 1; ++dy) {		
			vec2 offset = vec2(dx, dy);
			float depth = texture_depth(fullscreen_tex_coord + offset / vec2(textureSize(sampler_color, 0)));
			img_d[dy + 1][dx + 1] = depth; //log(depth * 0.01 + 1.0) / log(1000 * 0.01 + 1.0);
		}
	}
	
	float lap_d = convolve(laplace_kernel, img_d);
	
	// look only at positive curvature ???
	// this gives cleaner lines for common cases
	bool edgy = lap_d / img_d[1][1] > 0.0005;
	
	// passthrough color, add edginess
	frag_color = vec4(texture(sampler_color, fullscreen_tex_coord).rgb, mix(0.0, 1.0, edgy));
}

#endif
'''

_shader_edge_filter_source = _shader_fullscreen_source + '''

// http://graphics.cs.williams.edu/papers/MedianShaderX6/median.pix

/*
3x3 Median
Morgan McGuire and Kyle Whitson
http://graphics.cs.williams.edu


Copyright (c) Morgan McGuire and Williams College, 2006
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

// RGB-edge
uniform sampler2D sampler_color;

#ifdef _FRAGMENT_

#define s2(a, b)				temp = a; a = min(a, b); b = max(temp, b);
#define mn3(a, b, c)			s2(a, b); s2(a, c);
#define mx3(a, b, c)			s2(b, c); s2(a, c);

#define mnmx3(a, b, c)			mx3(a, b, c); s2(a, b);                                   // 3 exchanges
#define mnmx4(a, b, c, d)		s2(a, b); s2(c, d); s2(a, c); s2(b, d);                   // 4 exchanges
#define mnmx5(a, b, c, d, e)	s2(a, b); s2(c, d); mn3(a, c, e); mx3(b, d, e);           // 6 exchanges
#define mnmx6(a, b, c, d, e, f) s2(a, d); s2(b, e); s2(c, f); mn3(a, b, c); mx3(d, e, f); // 7 exchanges

// Starting with a subset of size 6, remove the min and max each time
#define sort9_ \
mnmx6(v[0], v[1], v[2], v[3], v[4], v[5]); \
mnmx5(v[1], v[2], v[3], v[4], v[6]); \
mnmx4(v[2], v[3], v[4], v[7]); \
mnmx3(v[3], v[4], v[8]); \

void sort9(inout float v[9]) {
	float temp;
	sort9_;
}

out vec4 frag_color;

void main() {
	
	float edges[9];
	
	// Add the pixels which make up our window to the pixel array.
	for(int dX = -1; dX <= 1; ++dX) {
		for(int dY = -1; dY <= 1; ++dY) {		
			vec2 offset = vec2(float(dX), float(dY));
			// If a pixel in the window is located at (x+dX, y+dY), put it at index (dX + R)(2R + 1) + (dY + R) of the
			// pixel array. This will fill the pixel array, with the top left pixel of the window at pixel[0] and the
			// bottom right pixel of the window at pixel[N-1].
			edges[(dX + 1) * 3 + (dY + 1)] = texture(sampler_color, fullscreen_tex_coord + offset / vec2(textureSize(sampler_color, 0))).a;
		}
	}
	
	// sort edge flags -> get median
	sort9(edges);
	
	// passthrough color
	frag_color = vec4(texture(sampler_color, fullscreen_tex_coord).rgb, edges[4]);
}

#endif
'''

_shader_ascii_source = _shader_fullscreen_source + '''

uniform sampler2D sampler_color; // RGB-edge
uniform sampler2D sampler_depth;
uniform sampler1D sampler_lum2ascii;

uniform vec3 fgcolor;

uniform samplerBuffer sampler_nnbiases;
uniform samplerBuffer sampler_nnweights;

// dont change this. just dont.
const ivec2 char_size = ivec2(6, 8);

#ifdef _FRAGMENT_

out vec4 frag_ascii;

struct Neuron {
	int first_weight;
	int first_input;
	int last_input;
};

// begin auto-generated-ish

const int neurons_in_layer[] = int[](48, 18, 36);

const Neuron neurons[] = Neuron[](
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 0),
	Neuron(0, 0, 48),
	Neuron(48, 0, 48),
	Neuron(96, 0, 48),
	Neuron(144, 0, 48),
	Neuron(192, 0, 48),
	Neuron(240, 0, 48),
	Neuron(288, 0, 48),
	Neuron(336, 0, 48),
	Neuron(384, 0, 48),
	Neuron(432, 0, 48),
	Neuron(480, 0, 48),
	Neuron(528, 0, 48),
	Neuron(576, 0, 48),
	Neuron(624, 0, 48),
	Neuron(672, 0, 48),
	Neuron(720, 0, 48),
	Neuron(768, 0, 48),
	Neuron(816, 0, 48),
	Neuron(864, 48, 66),
	Neuron(882, 48, 66),
	Neuron(900, 48, 66),
	Neuron(918, 48, 66),
	Neuron(936, 48, 66),
	Neuron(954, 48, 66),
	Neuron(972, 48, 66),
	Neuron(990, 48, 66),
	Neuron(1008, 48, 66),
	Neuron(1026, 48, 66),
	Neuron(1044, 48, 66),
	Neuron(1062, 48, 66),
	Neuron(1080, 48, 66),
	Neuron(1098, 48, 66),
	Neuron(1116, 48, 66),
	Neuron(1134, 48, 66),
	Neuron(1152, 48, 66),
	Neuron(1170, 48, 66),
	Neuron(1188, 48, 66),
	Neuron(1206, 48, 66),
	Neuron(1224, 48, 66),
	Neuron(1242, 48, 66),
	Neuron(1260, 48, 66),
	Neuron(1278, 48, 66),
	Neuron(1296, 48, 66),
	Neuron(1314, 48, 66),
	Neuron(1332, 48, 66),
	Neuron(1350, 48, 66),
	Neuron(1368, 48, 66),
	Neuron(1386, 48, 66),
	Neuron(1404, 48, 66),
	Neuron(1422, 48, 66),
	Neuron(1440, 48, 66),
	Neuron(1458, 48, 66),
	Neuron(1476, 48, 66),
	Neuron(1494, 48, 66)
);

// end auto-generated

float neuron_activations[neurons.length()];

float logistic(float x) {
	return 1.0 / (1.0 + exp(-x));
}

void nn_eval() {
	for (int u = neurons_in_layer[0]; u < neurons.length(); u++) {
		Neuron n = neurons[u];
		float netin = texelFetch(sampler_nnbiases, u).r;
		int k = n.first_weight;
		for (int i = n.first_input; i < n.last_input; i++) {
			netin += neuron_activations[i] * texelFetch(sampler_nnweights, k).r;
			k++;
		}
		neuron_activations[u] = logistic(netin);
	}
}

// LUT from nn output indices to ASCII
const int nn2ascii[] = int[](
	65, 84, 79, 72, 76, 89, 86, 118, 88, 120,
	44, 46, 47, 60, 62, 63, 59, 39, 58, 91, 93,
	92, 123, 125, 124, 96, 126, 33, 94, 42, 40,
	41, 45, 61, 95, 43
);

int edge2ascii() {
	// load input neuron activations from edge flags
	float esum = 0.0;
	for (int j = 0; j < char_size.y; j++) {
		for (int i = 0; i < char_size.x; i++) {
			float e = texelFetch(sampler_color, ivec2(floor(gl_FragCoord.xy)) * char_size + ivec2(i, j), 0).a;
			neuron_activations[j * char_size.x + i] = e;
			esum += e;
		}
	}
	// if no edge flags are set, exit early
	float max_act = 0.0;
	float best = 32; // space
	if (esum > 0.0) {
		// evaluate network
		nn_eval();
		// read back output
		for (int i = 0; i < nn2ascii.length(); i++) {
			float act = neuron_activations[neurons.length() - nn2ascii.length() + i];
			bool r = act > max_act;
			max_act = mix(max_act, act, r);
			best = mix(best, float(nn2ascii[i]), r);
		}
	}
	return int(best);
}

vec3 color_avg() {
	vec3 c;
	for (int i = 0; i < char_size.x; i++) {
		for (int j = 0; j < char_size.y; j++) {
			c += texelFetch(sampler_color, ivec2(floor(gl_FragCoord.xy)) * char_size + ivec2(i, j), 0).rgb;
		}
	}
	return c / float(char_size.x * char_size.y);
}

void main() {
	//float lum = dot(vec3(0.2126, 0.7152, 0.0722), color_avg());
	//int codepoint = int(floor(texture(sampler_lum2ascii, lum).r * 255.0 + 0.5));
	int codepoint = edge2ascii();
	frag_ascii = vec4(fgcolor, (float(codepoint) + 0.5) / 255.0);
}

#endif
'''

_shader_dtext_source = '''

uniform ivec2 viewport_size;

#ifdef _VERTEX_

layout(location = 0) in vec4 pos;

// RGB-ASCII
layout(location = 1) in vec4 color;

out VertexData {
	vec4 color;
} vertex_out;

void main() {
	vec2 origin = pos.zw;
	gl_Position = vec4(((pos.xy + 0.5) / vec2(viewport_size) + origin) * 2.0 - 1.0, 0.0, 1.0);
	vertex_out.color = color;
}

#endif

#ifdef _FRAGMENT_

in VertexData {
	vec4 color;
} vertex_in;

out vec4 frag_color;

void main() {
	// treat null char as transparent
	if (vertex_in.color.a < (0.9 / 255.0)) discard;
	frag_color = vertex_in.color;
}

#endif
'''

_shader_text_source = '''

uniform sampler2D sampler_text;
uniform sampler2DArray sampler_font;

// passthrough for testing
uniform sampler2D sampler_color;

uniform vec3 bgcolor;

const vec2 char_uvlim = vec2(0.75, 1.0);

#ifdef _VERTEX_

layout(location = 0) in vec2 pos;

out vec2 fullscreen_tex_coord;
flat out vec3 textcolor;
flat out ivec2 textpos;
flat out int codepoint;

void main() {
	gl_Position = vec4(pos, 0.0, 1.0);
	fullscreen_tex_coord = vec2(0.5) + 0.5 * pos;
	textpos = ivec2(floor(fullscreen_tex_coord * vec2(textureSize(sampler_text, 0)) + 0.5));
	vec4 rgba = texelFetch(sampler_text, textpos, 0);
	textcolor = rgba.rgb;
	codepoint = int(floor(rgba.a * 255.0));
}

#endif

#ifdef _FRAGMENT_

in vec2 fullscreen_tex_coord;
flat in vec3 textcolor;
flat in ivec2 textpos;
flat in int codepoint;

out vec4 frag_color;

void main() {
	vec2 fsuv = fullscreen_tex_coord * vec2(textureSize(sampler_text, 0));
	// if fragment real position is outside this 'cell', we need to deal with it
	vec2 uv = clamp(fsuv - vec2(textpos), vec2(0.0), vec2(1.0));
	// manual grad to avoid discontinuities
	float f = textureGrad(sampler_font, vec3(uv * char_uvlim, codepoint), dFdx(fsuv * char_uvlim), dFdy(fsuv * char_uvlim)).r;
	// use font texture to interpolate between bg and fg
	frag_color = vec4(mix(bgcolor, textcolor, vec3(f)), 1.0);
	//frag_color = vec4(vec3(texture(sampler_color, fullscreen_tex_coord).a), 1.0);
}

#endif

'''

# magic
_nnbiases = [
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	0.000000,
	-2.719553,
	-0.125992,
	-0.303322,
	-1.147464,
	1.037836,
	-4.104112,
	-1.795221,
	-3.883396,
	-6.399259,
	1.213296,
	-7.185343,
	-2.604998,
	-5.828797,
	-4.562339,
	-2.813242,
	-1.960913,
	0.123920,
	-6.399031,
	-12.037263,
	-9.757934,
	-22.603989,
	-15.365041,
	-11.047910,
	-14.757375,
	-12.613504,
	-14.796516,
	-10.465412,
	-20.177616,
	-14.744551,
	0.886044,
	-15.191303,
	-20.566136,
	-12.073739,
	-14.172974,
	-11.388529,
	-7.230772,
	-12.091497,
	-11.766063,
	-19.205868,
	-4.415214,
	-14.035142,
	-12.742836,
	-9.288658,
	11.190832,
	-2.747679,
	-15.080342,
	4.686029,
	-6.086324,
	-12.804070,
	-20.350203,
	-2.290781,
	1.716275,
	-31.579267,
	-9.774274
]

# darker magic
_nnweights = [
	0.558143,
	-2.347904,
	-1.095555,
	-0.752784,
	0.091963,
	-0.675391,
	-3.404731,
	-0.937049,
	-3.953801,
	-1.491495,
	-2.029206,
	-0.360374,
	-3.785545,
	-2.834289,
	0.586586,
	-1.447833,
	-0.359881,
	-2.166878,
	0.011981,
	0.293854,
	0.156080,
	-0.052798,
	0.721680,
	-0.509924,
	-0.121875,
	-0.716778,
	0.195816,
	0.207769,
	0.498244,
	0.254134,
	0.892103,
	0.899083,
	1.168288,
	0.140856,
	-0.163224,
	1.088172,
	8.757582,
	4.467782,
	1.767319,
	1.571878,
	2.802931,
	0.913332,
	6.682884,
	3.052518,
	3.687140,
	1.802332,
	2.321335,
	0.666286,
	4.427469,
	3.391674,
	-3.059420,
	2.155061,
	3.519142,
	7.229814,
	2.590611,
	-1.935217,
	0.966890,
	2.402280,
	4.481490,
	3.186763,
	4.582961,
	6.632328,
	4.540988,
	1.524425,
	1.445454,
	3.298014,
	2.100543,
	2.068386,
	1.243721,
	1.712007,
	0.156796,
	0.431546,
	1.047200,
	0.206028,
	-0.268168,
	1.103235,
	0.237951,
	0.277374,
	0.030157,
	0.038916,
	-0.386779,
	-1.135528,
	-0.798964,
	0.294975,
	-1.317109,
	-0.878641,
	0.155367,
	0.318137,
	-0.747603,
	0.128537,
	-0.600271,
	-0.029850,
	-0.730493,
	-0.063572,
	-0.963280,
	-0.730055,
	-0.506425,
	-0.438473,
	1.655078,
	1.056263,
	0.006381,
	2.729154,
	-0.696591,
	-1.182869,
	0.148874,
	2.314268,
	1.587877,
	2.583327,
	2.006323,
	-0.426266,
	-1.769810,
	1.653709,
	2.215609,
	2.798170,
	-2.293292,
	-0.037820,
	-4.250213,
	-3.732895,
	-2.654404,
	-1.460004,
	-8.190693,
	-4.953176,
	-3.381676,
	-6.171437,
	-0.122824,
	-0.343963,
	-3.449574,
	-1.131113,
	-0.405973,
	-4.596619,
	3.230656,
	3.918560,
	1.768377,
	-0.280515,
	-1.990803,
	0.496156,
	0.299915,
	2.861155,
	0.735309,
	1.647214,
	-2.190983,
	-0.176802,
	4.329470,
	5.999611,
	-0.491004,
	-0.485174,
	-0.297764,
	-0.494057,
	-1.128646,
	-3.574566,
	-0.649639,
	-0.914416,
	-1.318243,
	-1.248007,
	-0.826287,
	0.675997,
	-0.007776,
	-1.249931,
	0.257525,
	-0.919148,
	-0.031603,
	0.245437,
	0.040588,
	-0.115132,
	-0.857829,
	-0.245681,
	0.515522,
	0.018479,
	0.925678,
	-0.335862,
	-0.531556,
	0.669353,
	0.565019,
	1.176500,
	1.136043,
	1.499829,
	-0.209643,
	1.785044,
	1.503964,
	2.336036,
	1.747310,
	0.780131,
	2.626385,
	5.244335,
	4.038598,
	6.016683,
	0.239777,
	2.045481,
	5.895492,
	4.533597,
	5.060112,
	6.271876,
	11.580517,
	2.361052,
	8.765690,
	4.511743,
	5.852249,
	7.741724,
	10.585358,
	4.502946,
	3.132680,
	3.473409,
	3.768028,
	6.743429,
	7.359931,
	1.488435,
	5.265233,
	0.905716,
	4.334088,
	8.298361,
	3.311251,
	0.536946,
	2.205640,
	2.721357,
	4.092874,
	4.745924,
	2.066747,
	0.120551,
	-1.517645,
	-2.986986,
	1.133067,
	-0.548315,
	-1.975678,
	-4.862824,
	-2.162084,
	-3.174954,
	0.949635,
	-4.545692,
	-1.255099,
	-2.302471,
	-3.697427,
	-2.907808,
	-1.038969,
	-3.859282,
	-4.834697,
	-6.358020,
	-4.320376,
	-5.482700,
	-7.393826,
	-2.779085,
	2.726984,
	0.057193,
	6.972089,
	1.103347,
	-0.861393,
	1.098510,
	4.164152,
	1.326460,
	2.166818,
	-2.156188,
	-1.205211,
	-3.349925,
	4.713411,
	3.520725,
	1.277328,
	0.558899,
	-0.461529,
	-1.703768,
	5.528289,
	3.317357,
	-2.919750,
	-1.593499,
	-1.511257,
	1.110530,
	5.225599,
	-0.931876,
	0.469092,
	4.157882,
	0.875393,
	2.361784,
	-0.460250,
	-1.476388,
	2.004489,
	0.778690,
	1.111237,
	1.182912,
	5.397685,
	3.681551,
	0.085251,
	2.563422,
	3.664856,
	2.994113,
	-3.764787,
	-2.034242,
	0.671110,
	2.178144,
	2.791732,
	6.133544,
	2.550613,
	0.618837,
	-0.277682,
	-0.076843,
	0.907568,
	-0.762706,
	0.480702,
	0.655056,
	1.154237,
	0.328131,
	0.507882,
	1.073525,
	0.105185,
	0.218142,
	1.370149,
	1.071849,
	-1.213300,
	2.309470,
	-0.008045,
	0.933019,
	-0.546426,
	0.282093,
	0.963334,
	-0.052764,
	-1.658259,
	0.214451,
	-0.239861,
	-0.498816,
	0.522394,
	2.200677,
	-1.969349,
	-0.603573,
	-0.288700,
	-1.215901,
	-0.345120,
	1.102577,
	-3.882711,
	0.834293,
	-0.091869,
	-0.133108,
	0.576125,
	-0.181640,
	-2.919085,
	-1.207448,
	-0.730241,
	-0.836504,
	-1.563270,
	-0.874164,
	5.680646,
	5.043176,
	-0.878701,
	0.518520,
	-1.280742,
	0.378235,
	0.648088,
	5.914367,
	3.482478,
	4.335291,
	3.756595,
	-0.718557,
	0.152423,
	5.309623,
	-0.361981,
	-2.067807,
	2.665153,
	0.716367,
	-4.989145,
	-1.508400,
	-0.361935,
	2.926702,
	-2.729291,
	0.134454,
	-1.314448,
	1.044303,
	-0.226826,
	-0.934135,
	-1.137196,
	-2.486932,
	-0.686083,
	-3.962674,
	0.102941,
	-0.651470,
	1.781376,
	0.564294,
	2.359298,
	1.704836,
	0.397639,
	0.862818,
	0.341539,
	0.488092,
	2.237320,
	4.480318,
	0.083739,
	0.364501,
	3.089636,
	-0.604775,
	-3.444904,
	-2.712980,
	-3.895807,
	-2.064736,
	1.160850,
	3.355671,
	-3.314421,
	-0.344477,
	2.328648,
	-0.504231,
	1.609812,
	2.105839,
	0.199851,
	0.631873,
	2.147079,
	-0.360014,
	-0.116481,
	3.481368,
	0.306615,
	1.199093,
	2.564170,
	0.825532,
	1.615756,
	1.224432,
	2.345704,
	-0.398219,
	-0.768538,
	-0.630649,
	0.320688,
	-0.101874,
	4.174022,
	-0.959790,
	1.426147,
	0.101192,
	1.956468,
	-0.389739,
	1.897336,
	0.108334,
	1.775877,
	0.118722,
	-1.840027,
	0.709348,
	-1.662636,
	-0.041079,
	0.333607,
	-3.347374,
	1.258509,
	-1.046626,
	1.679093,
	1.336864,
	2.185146,
	0.683374,
	2.702022,
	3.603290,
	0.396999,
	2.384465,
	0.220016,
	0.430900,
	2.080329,
	2.617766,
	-0.487151,
	0.502405,
	-0.346702,
	0.375563,
	0.857973,
	0.867559,
	0.827974,
	-0.431997,
	-1.145209,
	-1.169373,
	0.525414,
	-0.899034,
	-0.705222,
	-1.288905,
	-1.114053,
	-0.560388,
	-0.184880,
	-0.093166,
	-4.279076,
	-2.531700,
	-3.705263,
	-2.790019,
	-0.448691,
	-5.357498,
	-4.400678,
	-1.746098,
	-3.072217,
	-1.159203,
	-2.835401,
	0.417561,
	-8.790999,
	-5.794806,
	-4.159085,
	-1.899800,
	0.038938,
	-0.833780,
	0.935290,
	1.662083,
	0.494225,
	2.985187,
	-1.302146,
	1.244083,
	5.394192,
	1.901292,
	2.407114,
	2.184341,
	2.848892,
	1.395881,
	2.611340,
	1.250494,
	-0.810596,
	1.815164,
	0.903941,
	-3.862602,
	1.076692,
	0.922517,
	1.894598,
	0.905927,
	-0.083905,
	1.416143,
	1.667764,
	2.356935,
	-3.248708,
	1.871740,
	-0.121670,
	0.288314,
	1.839038,
	1.408268,
	0.616031,
	3.143636,
	0.868895,
	-0.362786,
	1.668041,
	0.012170,
	0.243094,
	0.395156,
	-2.040930,
	1.305801,
	0.584632,
	0.165067,
	0.840511,
	-0.017951,
	-0.010370,
	-1.946611,
	0.125998,
	-0.458600,
	-2.110347,
	-0.001814,
	-1.364098,
	0.452682,
	0.654344,
	1.151693,
	-0.189223,
	-1.503557,
	0.089862,
	-0.690637,
	2.085642,
	-0.162548,
	2.137627,
	-0.321021,
	-0.701334,
	1.009813,
	4.462884,
	2.355478,
	-3.486118,
	-1.742459,
	-0.142564,
	-1.989696,
	5.912980,
	1.380532,
	0.188340,
	0.381968,
	-0.708164,
	-1.215407,
	5.500556,
	3.822737,
	1.457598,
	0.742566,
	-1.189523,
	-4.134647,
	5.972286,
	-0.248587,
	0.686407,
	-1.708089,
	-0.773325,
	-1.623823,
	0.339714,
	-0.234483,
	-0.787185,
	1.503704,
	-2.642196,
	-1.549839,
	1.510506,
	-0.207274,
	1.228975,
	2.090014,
	-2.085826,
	-0.969992,
	0.592588,
	0.501196,
	-0.137680,
	0.360394,
	-0.057279,
	-1.481628,
	2.146410,
	2.135234,
	0.840360,
	-1.073178,
	-0.424942,
	-0.956498,
	-1.694013,
	2.505942,
	-0.881290,
	-0.950725,
	0.085084,
	-2.795348,
	2.825984,
	1.803019,
	2.104298,
	1.880835,
	0.147197,
	-1.393917,
	2.633138,
	0.865548,
	1.120435,
	-1.457883,
	0.974557,
	-4.163286,
	2.638240,
	1.081419,
	4.862201,
	0.810635,
	3.987609,
	2.588334,
	4.595308,
	1.732830,
	5.366681,
	2.250345,
	5.175292,
	5.018611,
	-2.091955,
	-0.175003,
	-4.385227,
	-0.423473,
	-5.378965,
	-11.922470,
	-0.688944,
	-0.834399,
	-5.885624,
	4.556136,
	-1.425952,
	-9.221896,
	-3.697233,
	2.418126,
	3.495834,
	0.994863,
	6.041029,
	-0.115855,
	1.097540,
	-1.832313,
	0.980497,
	0.019805,
	1.829275,
	7.074122,
	3.878395,
	2.458339,
	6.975140,
	3.677212,
	4.182204,
	15.794397,
	-2.965667,
	-3.882792,
	-0.173043,
	4.043193,
	9.547550,
	8.449910,
	-4.939475,
	-6.637173,
	-6.538082,
	4.046584,
	0.943245,
	2.324893,
	-2.952556,
	-2.552138,
	-4.999393,
	-2.059135,
	-2.104621,
	-4.114713,
	1.581683,
	1.925363,
	2.611376,
	2.755708,
	3.264968,
	5.168680,
	0.102353,
	3.918635,
	1.300205,
	2.720336,
	2.141305,
	2.203170,
	-0.254756,
	0.197177,
	0.421368,
	1.904322,
	-0.702609,
	-0.638754,
	0.774390,
	1.961083,
	-0.119129,
	-0.955901,
	0.976651,
	0.124001,
	0.744218,
	-0.382881,
	0.911462,
	2.529246,
	2.142524,
	0.918319,
	0.190396,
	2.140105,
	0.960332,
	1.648052,
	0.642284,
	0.233993,
	-2.610425,
	-0.981650,
	-1.314185,
	0.872698,
	-0.133468,
	-0.601028,
	-3.972369,
	-2.581054,
	-1.487188,
	-2.714711,
	-1.417390,
	0.223375,
	-0.970304,
	0.216473,
	0.014177,
	3.305544,
	3.564938,
	9.990643,
	-0.725204,
	1.482751,
	0.466976,
	0.921924,
	5.723780,
	5.159372,
	-1.850492,
	0.140126,
	1.320877,
	1.760723,
	2.407685,
	2.452030,
	-2.742876,
	1.617036,
	-1.398741,
	-1.526265,
	3.277908,
	-0.883363,
	-1.584624,
	-1.339836,
	1.275539,
	0.642146,
	0.846852,
	0.360428,
	-2.230053,
	-0.449603,
	1.887153,
	-2.347500,
	1.249937,
	1.096391,
	-4.697420,
	0.596262,
	0.414672,
	-0.647985,
	0.085233,
	1.951912,
	-5.406472,
	-0.476245,
	-2.069874,
	0.714508,
	2.363003,
	-1.235382,
	5.803204,
	2.418632,
	4.202219,
	3.093188,
	4.265880,
	2.757586,
	1.837637,
	3.215911,
	-1.379121,
	0.582873,
	-0.762917,
	0.770286,
	0.775544,
	0.325388,
	1.778998,
	1.621187,
	-1.510430,
	-0.936261,
	2.998274,
	1.037944,
	0.284768,
	-1.587826,
	-0.831940,
	-4.304006,
	0.233686,
	0.184830,
	-1.803596,
	-2.677299,
	-0.757454,
	-2.730948,
	0.291372,
	0.720657,
	-0.061581,
	1.468554,
	-0.552582,
	-2.577855,
	-0.383144,
	-0.618765,
	-1.592990,
	-1.063818,
	-2.782388,
	-5.733411,
	1.431910,
	0.188736,
	-0.586426,
	-1.316522,
	-1.099716,
	-3.805558,
	-1.504709,
	-4.297005,
	-0.690827,
	-0.773637,
	1.258808,
	2.989391,
	-0.377647,
	-3.013085,
	1.271408,
	3.696475,
	2.415911,
	2.366958,
	-0.464090,
	-2.270999,
	-4.360140,
	-2.551117,
	1.568134,
	5.684635,
	0.061752,
	-1.937524,
	1.077338,
	-0.893384,
	-0.363342,
	8.311901,
	2.478737,
	-4.113476,
	-0.627527,
	-0.993379,
	0.127089,
	9.893126,
	0.536171,
	-3.476303,
	3.617461,
	-0.653340,
	4.380662,
	12.235723,
	-1.182550,
	-2.840024,
	1.113933,
	1.417562,
	2.090157,
	9.902743,
	-0.003063,
	-6.237109,
	-1.086694,
	2.384839,
	5.948768,
	6.482018,
	0.840253,
	0.247759,
	-1.229256,
	0.173643,
	0.838488,
	-0.061688,
	-0.270696,
	0.899828,
	-1.026019,
	-0.781640,
	0.853230,
	1.290666,
	0.514772,
	1.133659,
	0.570103,
	0.601648,
	-1.233057,
	0.780533,
	-0.320553,
	-0.355923,
	-0.325457,
	-0.371345,
	-0.348661,
	-0.349780,
	-0.297195,
	-0.352089,
	-0.313142,
	-0.297109,
	-0.281750,
	-0.309129,
	-0.327404,
	-0.303861,
	-0.320134,
	-0.325987,
	-0.332871,
	-0.332769,
	2.572178,
	6.629026,
	-0.319046,
	0.769214,
	0.186390,
	-1.353191,
	-5.463949,
	2.973504,
	3.231518,
	-1.438469,
	2.944252,
	-0.075246,
	1.682402,
	0.781049,
	-4.248729,
	-0.305701,
	-4.626329,
	6.408326,
	0.439066,
	1.736325,
	1.364579,
	0.113965,
	-2.431835,
	0.213920,
	-0.977204,
	2.851033,
	2.437121,
	-0.713437,
	2.859784,
	2.560600,
	0.321836,
	-0.002951,
	-1.452306,
	-1.306702,
	-0.004213,
	1.561578,
	0.885441,
	0.762986,
	-1.369184,
	-0.134995,
	0.901124,
	0.570590,
	-0.931219,
	-0.217473,
	3.735593,
	-0.785092,
	1.380701,
	0.785356,
	0.133603,
	-1.268236,
	-2.460683,
	-1.531493,
	0.814285,
	-0.657175,
	0.911731,
	1.607211,
	-0.099028,
	0.199750,
	-1.484017,
	0.096626,
	-1.361177,
	4.035253,
	0.249040,
	-0.647249,
	2.748181,
	2.308239,
	0.376055,
	-1.645597,
	2.181535,
	-4.033830,
	-3.391331,
	1.352446,
	0.252183,
	1.170243,
	0.882219,
	0.036481,
	-2.957098,
	0.704032,
	-0.935679,
	0.462213,
	4.936419,
	-0.566328,
	2.260590,
	2.509651,
	0.420352,
	-1.540066,
	-2.631579,
	-1.682166,
	-2.773931,
	0.125002,
	2.365875,
	1.069787,
	-2.733342,
	-2.157421,
	3.518867,
	1.023021,
	-4.268187,
	1.388747,
	2.540336,
	-1.529305,
	-0.120165,
	1.939859,
	-0.704372,
	1.076660,
	1.009817,
	-0.187807,
	-2.686659,
	2.015000,
	0.552161,
	1.707478,
	0.174896,
	0.263497,
	-0.275804,
	0.395258,
	-0.924459,
	1.654909,
	0.526298,
	-0.702295,
	2.492472,
	0.246174,
	0.364125,
	-1.802945,
	-2.286944,
	-0.357162,
	-2.296370,
	0.011393,
	-0.026736,
	0.826171,
	1.111805,
	-1.815596,
	3.349061,
	-0.358338,
	5.648871,
	0.946787,
	3.455210,
	-8.607561,
	0.321046,
	6.784818,
	-1.096612,
	-0.620641,
	-0.131869,
	1.886663,
	-0.840991,
	4.770124,
	-2.196557,
	-2.807419,
	-0.233590,
	-7.897469,
	0.890748,
	1.067583,
	-1.936214,
	0.697299,
	-0.601888,
	4.797598,
	0.496040,
	-8.887223,
	-2.755029,
	9.693612,
	2.563313,
	0.074334,
	5.333230,
	2.711068,
	-7.614563,
	-2.794806,
	-5.078124,
	-14.142453,
	4.717091,
	-7.122381,
	-1.020198,
	-5.884643,
	2.054992,
	19.616215,
	3.786402,
	0.111900,
	8.472652,
	-7.004537,
	-7.149162,
	-5.721958,
	-0.265219,
	4.649257,
	-4.805774,
	-1.288652,
	-2.498306,
	6.453170,
	2.873663,
	1.795660,
	7.736193,
	-1.618475,
	-2.982528,
	-0.867098,
	-0.713829,
	-0.964117,
	4.743181,
	-0.002008,
	-0.236999,
	-5.066689,
	2.318789,
	-6.970205,
	-3.271613,
	3.285983,
	-2.194536,
	3.520325,
	-3.153752,
	4.075365,
	-5.159885,
	-5.968994,
	8.837147,
	-4.428599,
	-0.207161,
	-2.160539,
	1.989222,
	1.849956,
	-2.998408,
	9.904301,
	-3.112629,
	3.507014,
	7.211567,
	0.355894,
	-0.602675,
	0.574438,
	5.021941,
	-0.637458,
	2.788364,
	-1.726992,
	-0.252309,
	-2.420873,
	1.455637,
	-0.917347,
	2.000356,
	3.092426,
	-1.250818,
	-4.277849,
	-4.698151,
	-4.174565,
	0.702253,
	7.120824,
	-1.209220,
	0.698949,
	-4.955284,
	1.536889,
	0.267644,
	1.850705,
	-5.850353,
	-1.266112,
	1.713756,
	1.952188,
	1.771133,
	-5.226276,
	-0.668813,
	-1.914575,
	-5.163876,
	3.406797,
	-5.952032,
	2.276861,
	0.338890,
	6.874163,
	4.082191,
	-0.410031,
	3.408445,
	-1.503565,
	-3.227098,
	-0.790109,
	0.548391,
	-3.622453,
	0.138148,
	-0.396106,
	-0.113585,
	1.172821,
	-2.567800,
	1.828067,
	1.411180,
	-3.623476,
	0.473288,
	0.736611,
	-3.130175,
	4.580018,
	-0.670638,
	-3.163881,
	-0.915385,
	-1.448173,
	-2.530133,
	-6.244490,
	1.127452,
	7.240644,
	-9.977200,
	-0.372538,
	0.992169,
	-1.162305,
	-0.478093,
	4.518600,
	-2.247961,
	4.848718,
	5.194605,
	-1.216083,
	-4.998267,
	1.677818,
	-1.508721,
	-3.413171,
	-2.825577,
	1.542730,
	-1.419924,
	-0.423421,
	-2.178879,
	2.251796,
	4.689616,
	1.256919,
	4.012668,
	-1.983179,
	-4.618967,
	2.773825,
	-0.243543,
	3.705811,
	-2.399074,
	0.325396,
	-5.577906,
	-2.073678,
	-0.447697,
	-4.890732,
	1.264502,
	-3.194768,
	1.897928,
	3.040569,
	0.410732,
	-3.068944,
	5.009451,
	0.361327,
	-1.191297,
	2.423137,
	2.875606,
	3.085661,
	-1.877558,
	3.097088,
	1.692988,
	2.899052,
	-2.915260,
	-6.535857,
	1.317557,
	-1.388528,
	4.774061,
	0.950010,
	-2.268811,
	-0.773424,
	1.437726,
	-1.440601,
	-2.394803,
	-9.445518,
	3.414923,
	-3.052593,
	-5.734111,
	-0.683815,
	-1.069740,
	-8.465976,
	-0.350224,
	-0.816338,
	6.139318,
	-5.119305,
	8.943218,
	-1.739986,
	-1.408702,
	-3.946701,
	1.217209,
	1.433437,
	-1.589835,
	0.948607,
	-2.457228,
	0.569792,
	-1.909788,
	1.412343,
	1.630517,
	-0.845173,
	1.984022,
	1.415035,
	0.727482,
	1.066688,
	1.677621,
	0.508150,
	-0.088892,
	-2.004215,
	2.497259,
	-0.853277,
	1.885367,
	0.320754,
	0.395767,
	0.677323,
	-1.459077,
	1.245736,
	-1.046674,
	-1.722905,
	1.449464,
	-1.196197,
	-0.510084,
	0.063530,
	2.117919,
	-4.273751,
	3.812234,
	1.065532,
	-3.621588,
	4.810171,
	-3.457881,
	0.495138,
	-7.116127,
	-3.667283,
	-2.956245,
	5.831744,
	-2.866203,
	-3.068239,
	2.482457,
	1.095283,
	-1.986780,
	-0.405422,
	1.966898,
	0.199996,
	4.045097,
	-4.912675,
	1.654126,
	-16.981268,
	10.260233,
	4.129570,
	-4.079412,
	-10.005742,
	-3.511023,
	-3.107340,
	0.126283,
	2.052603,
	-0.363361,
	-3.029062,
	-7.300552,
	-8.904532,
	-5.089826,
	-3.253715,
	-7.119002,
	-0.994083,
	1.961424,
	1.051101,
	-4.290612,
	-0.170733,
	-7.495296,
	0.496821,
	-0.125149,
	-3.835783,
	1.044029,
	3.527172,
	-7.108075,
	0.338731,
	-2.878869,
	0.971447,
	7.774766,
	-10.887964,
	-4.556455,
	4.721205,
	3.035758,
	5.059758,
	1.090749,
	3.964496,
	-6.467292,
	2.820755,
	0.538005,
	-3.150710,
	-0.966971,
	-1.703035,
	-1.393863,
	-0.003429,
	-0.292554,
	-0.785092,
	-5.308149,
	-1.639079,
	6.676041,
	0.270535,
	-5.288807,
	-9.795556,
	-9.274520,
	-1.348198,
	-3.705468,
	0.289613,
	-1.164106,
	2.621519,
	1.036187,
	1.328694,
	-4.587717,
	6.537797,
	0.149421,
	-2.991609,
	-6.429351,
	1.971266,
	-2.176317,
	-0.929028,
	1.108812,
	-0.528639,
	-3.217105,
	0.875790,
	-2.013066,
	-1.414788,
	-0.880778,
	-2.146251,
	-1.899722,
	-0.619377,
	-0.928590,
	2.266283,
	1.703559,
	-1.511644,
	-1.936279,
	-1.467959,
	-0.869015,
	-2.337601,
	-1.898528,
	3.270059,
	1.364976,
	4.168171,
	-1.488672,
	2.754710,
	-5.091002,
	-1.385583,
	-1.847938,
	-3.549625,
	3.469870,
	-1.146640,
	1.309315,
	-5.109425,
	4.345720,
	1.953698,
	-4.609067,
	-4.163730,
	8.265890,
	4.796920,
	1.331474,
	2.307904,
	0.167487,
	-0.139965,
	0.739600,
	0.797694,
	-2.270391,
	-1.813980,
	0.081882,
	-4.102630,
	-1.312364,
	3.526483,
	2.290117,
	2.994524,
	-3.131077,
	-2.065180,
	-7.626587,
	0.571751,
	0.217864,
	-6.589658,
	1.092687,
	4.550327,
	-3.002333,
	-3.174402,
	3.350352,
	-1.439289,
	0.659339,
	3.244732,
	-5.666861,
	6.590144,
	-0.138136,
	-1.636311,
	-7.848943,
	-7.952523,
	-3.240642,
	-1.507246,
	-3.661893,
	-0.618296,
	-6.429405,
	-3.553949,
	-1.831556,
	-1.608737,
	0.995912,
	-0.913750,
	3.822312,
	1.788738,
	1.162637,
	1.957547,
	-4.539068,
	-0.300206,
	-3.329137,
	-0.906963,
	-2.655095,
	7.165975,
	8.105485,
	-4.077213,
	0.189458,
	9.649773,
	2.369614,
	7.413894,
	-1.573381,
	1.854873,
	-5.692758,
	-0.891306,
	-12.097332,
	-7.872891,
	0.432060,
	6.951600,
	2.505469,
	-10.412340,
	-0.360152,
	-0.332173,
	-0.328107,
	-0.373275,
	-0.334763,
	-0.389051,
	-0.311611,
	-0.301510,
	-0.305036,
	-0.281320,
	-0.284592,
	-0.325718,
	-0.333670,
	-0.277873,
	-0.319529,
	-0.324899,
	-0.321476,
	-0.298301
]

class AsciiRenderer:
	
	def __init__(self, gl, reverse_luminance=True):
		self.gl = gl
		
		self._img_size = (1, 1)
		
		# text screen buffer (w, h)
		self._text_size = (0, 128)
		
		# colors
		self.fgcolor = (1, 1, 1)
		self.bgcolor = (0, 0, 0)
		
		# char size in pixels (w, h)
		self._char_size = (6, 8)
		
		# font texture
		self._init_font()
		
		gl.glActiveTexture(GL_TEXTURE0)
		
		# luminance to ASCII texture (1D)
		lumstr = '#BXEOCxeoc::..  '
		lumstr = lumstr[::-1] if reverse_luminance else lumstr
		self._tex_lum2ascii = GLuint(0)
		gl.glGenTextures(1, self._tex_lum2ascii)
		
		gl.glBindTexture(GL_TEXTURE_1D, self._tex_lum2ascii)
		gl.glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		gl.glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		gl.glTexImage1D(GL_TEXTURE_1D, 0, GL_R8, len(lumstr), 0, GL_RED, GL_UNSIGNED_BYTE, ctypes.create_string_buffer(lumstr))
		
		# main FBO
		self._fbo_main = GLuint(0)
		self._tex_color = GLuint(0)
		self._tex_depth = GLuint(0)
		
		gl.glGenFramebuffers(1, self._fbo_main)
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._fbo_main)
		
		gl.glGenTextures(1, self._tex_color)
		gl.glGenTextures(1, self._tex_depth)
		
		# color texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_color)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, 1, 1, 0, GL_RGB, GL_FLOAT, None)
		gl.glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self._tex_color, 0)
		
		# depth texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_depth)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, 1, 1, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
		gl.glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self._tex_depth, 0)
		
		gl.glDrawBuffer(GL_COLOR_ATTACHMENT0)
		
		# edge detection FBO
		self._fbo_edge = GLuint(0)
		self._tex_edge0 = GLuint(0)
		self._tex_edge1 = GLuint(0)
		
		gl.glGenFramebuffers(1, self._fbo_edge)
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._fbo_edge)
		
		gl.glGenTextures(1, self._tex_edge0)
		gl.glGenTextures(1, self._tex_edge1)
		
		# edge texture - RGB-EDGE
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_edge0)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, 1, 1, 0, GL_RGBA, GL_FLOAT, None)
		gl.glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self._tex_edge0, 0)
		
		# second edge texture - RGB-EDGE
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_edge1)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, 1, 1, 0, GL_RGBA, GL_FLOAT, None)
		gl.glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT1, GL_TEXTURE_2D, self._tex_edge1, 0)
		
		gl.glDrawBuffer(GL_COLOR_ATTACHMENT0)
		
		# text FBO
		self._fbo_text = GLuint(0)
		self._tex_text = GLuint(0) # RGB-ASCII
		
		gl.glGenFramebuffers(1, self._fbo_text)
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._fbo_text)
		
		gl.glGenTextures(1, self._tex_text)
		
		# RGB-ASCII texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_text)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, 1, 1, 0, GL_RGBA, GL_FLOAT, None)
		gl.glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self._tex_text, 0)
		
		gl.glDrawBuffer(GL_COLOR_ATTACHMENT0)
		
		# NN biases and weights
		self._tex_nnbiases = GLuint(0)
		self._tex_nnweights = GLuint(0)
		
		gl.glGenTextures(1, self._tex_nnbiases)
		gl.glGenTextures(1, self._tex_nnweights)
		
		buf = GLuint(0)
		
		# biases
		gl.glGenBuffers(1, buf)
		gl.glBindBuffer(GL_ARRAY_BUFFER, buf)
		gl.glBufferData(GL_ARRAY_BUFFER, len(_nnbiases) * ctypes.sizeof(GLfloat), c_array(GLfloat, _nnbiases), GL_STATIC_DRAW)
		gl.glBindTexture(GL_TEXTURE_BUFFER, self._tex_nnbiases)
		gl.glTexBuffer(GL_TEXTURE_BUFFER, GL_R32F, buf)
		# TODO delete buffer
		
		# weights
		gl.glGenBuffers(1, buf)
		gl.glBindBuffer(GL_ARRAY_BUFFER, buf)
		gl.glBufferData(GL_ARRAY_BUFFER, len(_nnweights) * ctypes.sizeof(GLfloat), c_array(GLfloat, _nnweights), GL_STATIC_DRAW)
		gl.glBindTexture(GL_TEXTURE_BUFFER, self._tex_nnweights)
		gl.glTexBuffer(GL_TEXTURE_BUFFER, GL_R32F, buf)
		# TODO delete buffer
		
		# clean up
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
		gl.glBindTexture(GL_TEXTURE_2D, 0)
		gl.glBindTexture(GL_TEXTURE_BUFFER, 0)
		
		# pending direct text
		self._dtext_pos = [] # x, y, screen origin
		self._dtext_color = [] # r, g, b, ascii
		
		self._vao_dtext = GLuint(0)
		self._vbo_dtext_pos = GLuint(0) # x, y, screen origin
		self._vbo_dtext_color = GLuint(0) # r, g, b, ascii
		
		gl.glGenVertexArrays(1, self._vao_dtext)
		gl.glGenBuffers(1, self._vbo_dtext_pos)
		gl.glGenBuffers(1, self._vbo_dtext_color)
		
		gl.glBindVertexArray(self._vao_dtext)
		
		gl.glBindBuffer(GL_ARRAY_BUFFER, self._vbo_dtext_pos)
		gl.glBufferData(GL_ARRAY_BUFFER, 4 * ctypes.sizeof(GLfloat), c_array(GLfloat, (0, 0, 0, 0)), GL_STREAM_DRAW)
		gl.glVertexAttribPointer(0, 4, GL_FLOAT, GL_FALSE, 0, None)
		gl.glEnableVertexAttribArray(0)
		
		gl.glBindBuffer(GL_ARRAY_BUFFER, self._vbo_dtext_color)
		gl.glBufferData(GL_ARRAY_BUFFER, 4 * ctypes.sizeof(GLfloat), c_array(GLfloat, (0, 0, 0, 0)), GL_STREAM_DRAW)
		gl.glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 0, None)
		gl.glEnableVertexAttribArray(1)
		
		gl.glBindBuffer(GL_ARRAY_BUFFER, 0)
		gl.glBindVertexArray(0)
		
	# }
	
	def _init_font(self):
		gl = self.gl
		
		gl.glActiveTexture(GL_TEXTURE0)
		
		# setup fbo to draw font into array texture
		fbo = GLuint(0)
		tex_font = GLuint(0)
		
		gl.glGenFramebuffers(1, fbo)
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, fbo)
		
		gl.glGenTextures(1, tex_font)
		
		gl.glBindTexture(GL_TEXTURE_2D_ARRAY, tex_font)
		gl.glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		gl.glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
		gl.glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		gl.glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		gl.glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_R8, 64, 64, 256, 0, GL_RED, GL_FLOAT, None)
		gl.glFramebufferTexture(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, tex_font, 0)
		
		gl.glDrawBuffer(GL_COLOR_ATTACHMENT0)
		
		# load font atlas
		fontimg = pygame.image.load('./res/font.bmp')
		tex_font_atlas = GLuint(0)
		gl.glGenTextures(1, tex_font_atlas)
		
		gl.glBindTexture(GL_TEXTURE_2D, tex_font_atlas)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST) # we won't be downscaling
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		# this feels disgusting
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, fontimg.get_width(), fontimg.get_height(), 0, GL_RGB, GL_UNSIGNED_BYTE, ctypes.create_string_buffer(pygame.image.tostring(fontimg, 'RGB')))
		
		# render the atlas into a texture array
		prog = makeProgram(gl, '330 core', (GL_VERTEX_SHADER, GL_GEOMETRY_SHADER, GL_FRAGMENT_SHADER), _shader_font_source)
		
		gl.glViewport(0, 0, 64, 64)
		gl.glDisable(GL_DEPTH_TEST)
		
		gl.glUseProgram(prog)
		gl.glUniform1i(gl.glGetUniformLocation(prog, 'sampler_fontatlas'), 0)
		
		self._draw_dummy(instances=256)
		
		gl.glUseProgram(0)
		gl.glDeleteFramebuffers(1, fbo)
		gl.glDeleteTextures(1, tex_font_atlas)
		
		gl.glGenerateMipmap(GL_TEXTURE_2D_ARRAY)
		self._tex_font = tex_font
		
	# }
	
	def resize(self, w, h, _last = [(1, 1)]):
		'''
		Resize internal textures for a specific screen size.
		'''
		if (w, h) == _last[0]: return
		_last[0] = (w, h)
		#print 'resize motherfucker!'
		
		gl = self.gl
		
		self._text_size = (int(self._text_size[1] * w / h * self._char_size[1] / self._char_size[0]), self._text_size[1])
		self._img_size = tuple(a * b for a, b in zip(self._text_size, self._char_size))
		
		gl.glActiveTexture(GL_TEXTURE0)
		
		# color texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_color)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, self._img_size[0], self._img_size[1], 0, GL_RGB, GL_FLOAT, None)
		
		# depth texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_depth)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, self._img_size[0], self._img_size[1], 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
		
		# edge texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_edge0)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, self._img_size[0], self._img_size[1], 0, GL_RGBA, GL_FLOAT, None)
		
		# second edge texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_edge1)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, self._img_size[0], self._img_size[1], 0, GL_RGBA, GL_FLOAT, None)
		
		# RGB-ASCII texture
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_text)
		gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, self._text_size[0], self._text_size[1], 0, GL_RGBA, GL_FLOAT, None)
		
	# }
	
	def _draw_dummy(self, instances = 1, _vao = GLuint(0)):
		gl = self.gl
		if not _vao.value:
			gl.glGenVertexArrays(1, _vao)
		# }
		gl.glBindVertexArray(_vao);
		gl.glDrawArraysInstanced(GL_POINTS, 0, 1, instances);
		gl.glBindVertexArray(0);
	# }
	
	def _draw_ascii_grid(self, w, h, _cache = {}):
		# w, h are quads
		gl = self.gl
		vao = _cache.get((w, h), None)
		if not vao:
			vao = GLuint(0)
			gl.glGenVertexArrays(1, vao)
			
			ibo = GLuint(0)
			vbo_pos = GLuint(0)
			
			gl.glGenBuffers(1, ibo)
			gl.glGenBuffers(1, vbo_pos)
			
			idx = []
			pos = []
			
			for y in xrange(h + 1):
				for x in xrange(w + 1):
					pos.append(2 * x / w - 1)
					pos.append(2 * y / h - 1)
					# only 2D!
				# }
			# }
			
			def get_index(x, y):
				if x < 0 or x > w: return 0
				if y < 0 or y > h: return 0
				return (w + 1) * y + x
			# }
			
			for y in xrange(h):
				for x in xrange(w):
					# 3---2 //
					# | /   //
					# 1     //
					idx.append(get_index(x, y))
					idx.append(get_index(x + 1, y + 1))
					idx.append(get_index(x, y + 1))
					#     3 //
					#   / | //
					# 1---2 //
					idx.append(get_index(x, y))
					idx.append(get_index(x + 1, y))
					idx.append(get_index(x + 1, y + 1))
				# }
			# }
			
			gl.glBindVertexArray(vao)
			
			# upload indices
			gl.glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo)
			gl.glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(idx) * ctypes.sizeof(GLuint), c_array(GLuint, idx), GL_STATIC_DRAW)
			
			# upload positions
			gl.glBindBuffer(GL_ARRAY_BUFFER, vbo_pos)
			gl.glBufferData(GL_ARRAY_BUFFER, len(pos) * ctypes.sizeof(GLfloat), c_array(GLfloat, pos), GL_STATIC_DRAW)
			gl.glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
			gl.glEnableVertexAttribArray(0)
			
			_cache[(w, h)] = vao
		# }
		
		gl.glBindVertexArray(vao)
		gl.glProvokingVertex(GL_FIRST_VERTEX_CONVENTION)
		gl.glDrawElements(GL_TRIANGLES, 6 * w * h, GL_UNSIGNED_INT, None)
		gl.glBindVertexArray(0)
	# }
	
	def _draw_direct_text(self, _cache = {}):
		gl = self.gl
		
		# if no text, do nothing
		if not len(self._dtext_pos): return
		
		#print self._dtext_pos
		#print self._dtext_color
		
		# upload new text data
		gl.glBindBuffer(GL_ARRAY_BUFFER, self._vbo_dtext_pos)
		gl.glBufferData(GL_ARRAY_BUFFER, len(self._dtext_pos) * ctypes.sizeof(GLfloat), c_array(GLfloat, self._dtext_pos), GL_STREAM_DRAW)
		gl.glBindBuffer(GL_ARRAY_BUFFER, self._vbo_dtext_color)
		gl.glBufferData(GL_ARRAY_BUFFER, len(self._dtext_color) * ctypes.sizeof(GLfloat), c_array(GLfloat, self._dtext_color), GL_STREAM_DRAW)
		
		prog_dtext = _cache.get('prog_dtext', None)
		if not prog_dtext:
			prog_dtext = makeProgram(gl, '330 core', (GL_VERTEX_SHADER, GL_FRAGMENT_SHADER), _shader_dtext_source)
			_cache['prog_dtext'] = prog_dtext
		# }
		
		gl.glUseProgram(prog_dtext)
		
		gl.glUniform2i(gl.glGetUniformLocation(prog_dtext, 'viewport_size'), *self._text_size)
		
		gl.glBindVertexArray(self._vao_dtext)
		gl.glDrawArrays(GL_POINTS, 0, len(self._dtext_pos) // 2)
		gl.glBindVertexArray(0)
		
		# clear text after drawing
		self._dtext_pos = []
		self._dtext_color = []
	# }
	
	def render(self, w, h, game, _cache = {}):
		gl = self.gl
		
		# art1 = wordart('ASCII', 'big')
		# art2 = wordart('ARCADE', 'big')
		
		# # temp
		# self.draw_text(art1, color = (0.333, 1, 1), screenorigin = (0.2, 0.667), textorigin = (0, 0.5), align = 'l')
		# self.draw_text(art2, color = (1, 0.333, 1), screenorigin = (0.8, 0.333), textorigin = (1, 0.5), align = 'l')

		
		if (w, h) == (0, 0): return
		
		self.resize(w, h)
		
		# render game to color + depth framebuffer
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._fbo_main)
		gl.glClearColor(0.0, 0.0, 0.0, 1.0)
		gl.glClearDepth(1.0)
		gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		gl.glEnable(GL_DEPTH_TEST)
		gl.glDepthFunc(GL_LESS)
		gl.glViewport(0, 0, *self._img_size)
		
		proj = game.render(gl, *self._img_size, ascii_r=self)
	 	if not proj: proj = vec.mat4.identity()
		
		gl.glDisable(GL_DEPTH_TEST)
		
		# edge detection
		# output texture is (original) color + edginess
		
		prog_edge = _cache.get('prog_edge', None)
		if not prog_edge:
			prog_edge = makeProgram(gl, '330 core', (GL_VERTEX_SHADER, GL_GEOMETRY_SHADER, GL_FRAGMENT_SHADER), _shader_edge_source)
			_cache['prog_edge'] = prog_edge
		# }
		
		prog_edge_filter = _cache.get('prog_edge_filter', None)
		if not prog_edge_filter:
			prog_edge_filter = makeProgram(gl, '330 core', (GL_VERTEX_SHADER, GL_GEOMETRY_SHADER, GL_FRAGMENT_SHADER), _shader_edge_filter_source)
			_cache['prog_edge_filter'] = prog_edge_filter
		# }
		
		gl.glActiveTexture(GL_TEXTURE0)
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_color)
		gl.glActiveTexture(GL_TEXTURE1)
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_depth)
		gl.glActiveTexture(GL_TEXTURE2)
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_edge0)
		
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._fbo_edge)
		gl.glViewport(0, 0, *self._img_size)
		
		# initial edge detection
		gl.glDrawBuffer(GL_COLOR_ATTACHMENT0)
		gl.glUseProgram(prog_edge)
		gl.glUniform1i(gl.glGetUniformLocation(prog_edge, 'sampler_color'), 0)
		gl.glUniform1i(gl.glGetUniformLocation(prog_edge, 'sampler_depth'), 1)
		gl.glUniformMatrix4fv(gl.glGetUniformLocation(prog_edge, 'proj_inv'), 1, True, c_array(GLfloat, proj.inverse().flatten()))
		
		self._draw_dummy()
		
		# filtering
		gl.glDrawBuffer(GL_COLOR_ATTACHMENT1)
		gl.glUseProgram(prog_edge_filter)
		gl.glUniform1i(gl.glGetUniformLocation(prog_edge_filter, 'sampler_color'), 2)
		
		#self._draw_dummy()
		
		# specify the output texture
		self._tex_edge = self._tex_edge0
		
		# ASCII conversion
		# output texture is (new) color + ascii code
		
		prog_ascii = _cache.get('prog_ascii', None)
		if not prog_ascii: 
			prog_ascii = makeProgram(gl, '330 core', (GL_VERTEX_SHADER, GL_GEOMETRY_SHADER, GL_FRAGMENT_SHADER), _shader_ascii_source)
			_cache['prog_ascii'] = prog_ascii
		# }
		
		gl.glActiveTexture(GL_TEXTURE0)
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_edge)
		gl.glActiveTexture(GL_TEXTURE1)
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_depth)
		gl.glActiveTexture(GL_TEXTURE2)
		gl.glBindTexture(GL_TEXTURE_1D, self._tex_lum2ascii)
		gl.glActiveTexture(GL_TEXTURE3)
		gl.glBindTexture(GL_TEXTURE_BUFFER, self._tex_nnbiases)
		gl.glActiveTexture(GL_TEXTURE4)
		gl.glBindTexture(GL_TEXTURE_BUFFER, self._tex_nnweights)
		
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._fbo_text)
		gl.glViewport(0, 0, *self._text_size)
		
		gl.glUseProgram(prog_ascii)
		#gl.glUniform2i(gl.glGetUniformLocation(prog_ascii, 'char_size'), *self._char_size)
		gl.glUniform1i(gl.glGetUniformLocation(prog_ascii, 'sampler_color'), 0)
		gl.glUniform1i(gl.glGetUniformLocation(prog_ascii, 'sampler_depth'), 1)
		gl.glUniform1i(gl.glGetUniformLocation(prog_ascii, 'sampler_lum2ascii'), 2)
		gl.glUniform3f(gl.glGetUniformLocation(prog_ascii, 'fgcolor'), *self.fgcolor)
		gl.glUniform1i(gl.glGetUniformLocation(prog_ascii, 'sampler_nnbiases'), 3)
		gl.glUniform1i(gl.glGetUniformLocation(prog_ascii, 'sampler_nnweights'), 4)
		
		self._draw_dummy()
		
		# render strings into ascii texture
		self._draw_direct_text()
		
		# real output: convert ASCII codes to text via font atlas
		
		prog_text = _cache.get('prog_text', None)
		if not prog_text:
			prog_text = makeProgram(gl, '330 core', (GL_VERTEX_SHADER, GL_FRAGMENT_SHADER), _shader_text_source)
			_cache['prog_text'] = prog_text
		# }
		
		gl.glActiveTexture(GL_TEXTURE0)
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_text)
		gl.glActiveTexture(GL_TEXTURE1)
		gl.glBindTexture(GL_TEXTURE_2D_ARRAY, self._tex_font)
		gl.glActiveTexture(GL_TEXTURE2)
		gl.glBindTexture(GL_TEXTURE_2D, self._tex_edge)
		
		gl.glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
		gl.glViewport(0, 0, w, h)
		gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		
		gl.glUseProgram(prog_text)
		gl.glUniform1i(gl.glGetUniformLocation(prog_text, 'sampler_text'), 0)
		gl.glUniform1i(gl.glGetUniformLocation(prog_text, 'sampler_font'), 1)
		gl.glUniform1i(gl.glGetUniformLocation(prog_text, 'sampler_color'), 2) # passthrough for testing
		gl.glUniform3f(gl.glGetUniformLocation(prog_text, 'bgcolor'), *self.bgcolor)
		
		self._draw_ascii_grid(*self._text_size)
		
		gl.glUseProgram(0)
	# }
	
	def draw_text(self, text, pos = (0,0), chardelta = (1, 0), linedelta = (0, -1), align = 'l', textorigin = (0, 0), screenorigin = (0, 0), color = None):
		'''
		Draw some (coloured) text. Align text region origin with screen origin, then offset text position by x,y
		
		Parameters:
			pos            Offset from aligned origins (x,y), in characters
			text           Text to draw (str)
			chardelta      Position delta between characters within a line of text (units are characters); default is (1,0)
			linedelta      Position delta between lines of text (units are characters); default is (0,-1)
			align          Alignment within lines; one of 'l' (left / line start), 'c' (centre), 'r' (right / line end); default is 'l'
			textorigin     Origin point within text region; range is [0,1]; default is (0,0)
			screenorigin   Origin point on screen; range is [0,1]; default is (0,0)
			color          Text colour; default is current foreground colour
			
		'''
		color = self.fgcolor if color is None else color
		color = tuple(color)[:3]
		chardelta = tuple(chardelta)[:2]
		linedelta = tuple(linedelta)[:2]
		textorigin = tuple(textorigin)[:2]
		screenorigin = tuple(screenorigin)[:2]
		lines = str(text).split('\n')
		# width and height of text
		tw = max(map(len, lines))
		th = len(lines)
		# prepare alignment
		padfactor = { 'c' : 0.5, 'r' : 1.0 }.get(align, 0.0)
		padsizes = [padfactor * (tw - len(line)) for line in lines]
		# text origin
		# TODO test / check this properly
		x = pos[0]
		y = pos[1]
		x -= tw * textorigin[0] * chardelta[0] + th * textorigin[1] * linedelta[0]
		y -= th * textorigin[1] * linedelta[1] + tw * textorigin[0] * chardelta[1]
		# process lines...
		from itertools import chain, izip, imap, repeat
		for line, psize in izip(lines, padsizes):
			# align
			x0 = x + chardelta[0] * psize
			y0 = y + chardelta[1] * psize
			# write buffers
			self._dtext_pos.extend(chain.from_iterable(izip(*([(x0 + chardelta[0] * f for f in xrange(len(line))), (y0 + chardelta[1] * f for f in xrange(len(line)))] + [repeat(f) for f in screenorigin]))))
			self._dtext_color.extend(chain.from_iterable(izip(*([repeat(f, len(line)) for f in color] + [imap(lambda c: (ord(c) + 0.5) / 255.0, line)]))))
			# newline
			x += linedelta[0]
			y += linedelta[1]
		# }
		
	# }
	
# }

def _nullblock(w, h):
	return '\n'.join(('\0' * w,) * h)
# }

def cookie(text, o = ' ', r = '\0'):
	from itertools import izip, imap, repeat, chain
	# i think this actually works...
	return '\n'.join(imap(str.join, repeat(''), [[lines, list(imap(lambda points, visited, sentinel: [None if p in visited else [visited.add(p), [lines[p[1]].__setitem__(p[0], r), points.extend([(p[0] + dx, p[1] + dy) for dx, dy in [(1,0),(0,1),(-1,0),(0,-1)]]), sentinel.__setitem__(0, len(points))] if lines[p[1]][p[0]] == o else None] for p in [(p0[0] % len(lines[0]), p0[1] % len(lines)) for p0 in [[points.pop(), sentinel.__setitem__(0, len(points))][0]]]], repeat(list(chain(izip(repeat(0), xrange(len(lines))), izip(repeat(len(lines[0])-1), xrange(len(lines))), izip(xrange(len(lines[0])), repeat(0)), izip(xrange(len(lines[0])), repeat(len(lines)-1))))), repeat(set()), iter(lambda x=[1]: x, [0])))][0] for lines in (map(list, text.split('\n')),)][0]))
# }

def _load_aafont(fontname, _cache = {}):
	font = _cache.get(fontname, None)
	if font is not None: return font
	from itertools import izip, imap, chain, repeat, takewhile
	font = {}
	with open('./res/{0}.aafont'.format(fontname)) as file:
		lines = file.readlines()
		(nrows, nspacecols) = map(int, lines[0].split())
		font[' '] = _nullblock(nspacecols, nrows)
		charset = lines[1].strip()
		for fontchar, sprite in izip(charset, izip(*([iter(lines[2:])] * nrows))):
			begcol = min(len(list(takewhile(str.isspace, line))) for line in sprite)
			endcol = max(len(line) - len(list(takewhile(str.isspace, reversed(line)))) for line in sprite)
			sprite = '\n'.join([str.ljust(line, endcol)[begcol:endcol] for line in sprite])
			# replace outside spaces with \0 for transparent bg with solid fg
			sprite = cookie(sprite)
			font[fontchar] = sprite
		# }
	# }
	_cache[fontname] = font
	return font
# }

def _join_multiline(joiner, args):
	# this doesnt do <s>any</s> much safety checking
	if len(args) == 0: return _nullblock(0, len(joiner.split('\n')))
	return '\n'.join(map(str.join, joiner.split('\n'), zip(*[arg.split('\n') for arg in args])))
# }

def size(text):
	lines = [] if text is None else str(text).split('\n')
	tw = max(map(len, lines) + [0])
	th = len(lines)
	return (tw, th)
# }

def wordart(text, fontname, charspace = 0, linespace = 0, align = 'l'):
	font = _load_aafont(fontname)
	text = str(text)
	nrows = len(font[' '].split('\n'))
	joiner = _nullblock(charspace, nrows)
	padfactor = { 'c' : 0.5, 'r' : 1.0 }.get(align, 0.0)
	artsprites = [_join_multiline(joiner, [font.get(c, font.get(' ')) for c in line]) for line in text.split('\n')]
	artwidths = [len(sprite.split('\n')[0]) for sprite in artsprites]
	maxwidth = max(artwidths)
	return '\n'.join(line.ljust(maxwidth, '\0') for line in ('\n' * (linespace + 1)).join(_join_multiline(_nullblock(0, nrows), [_nullblock(int(padfactor * (maxwidth - width)), nrows), sprite]) for sprite, width in itertools.izip(artsprites, artwidths)).split('\n'))
# }

def wordart_size(text, fontname, charspace = 0, linespace = 0, align = 'l'):
	font = _load_aafont(fontname)
	text = str(text)
	nrows = len(font[' '].split('\n'))
	lines = text.split('\n')
	linewidths = [reduce(int.__add__, [len(font.get(c, font.get(' ')).split('\n')[0]) for c in line] + [max(0, (len(line) - 1) * charspace)]) for line in lines]
	return (max(linewidths), len(lines) * nrows + max(0, (len(lines) - 1) * linespace))
# }

def wordwrap(text, width, fontname):
	import re
	lines = []
	line = ''
	for word, space in ((m.group(1), m.group(2)) for m in re.finditer(r'(?!$)(\S*)(\s*)', text)):
		# append word or newline
		line2 = line + word
		if wordart_size(line2, fontname)[0] <= width:
			# fits, append
			line = line2
			#print 'line:', line
		else:
			# doesnt fit, newline
			lines.append(line)
			#print 'newline' 
			if wordart_size(word, fontname)[0] <= width:
				line = word
				#print 'line:', line
			else:
				# word doesnt fit in one line, have to split
				while len(word):
					line = word[0]
					#print 'line:', line
					i = 1
					while wordart_size(word[:i], fontname)[0] <= width and line != word:
						line = word[:i]
						#print 'line:', line
						i += 1
					# }
					i = max(1, i-1)
					if line != word:
						lines.append(line)
						#print 'newline'
						line = ''
					# }
					word = word[i:]
				# }
			# }
		# }
		# process space characters (explicit newlines etc)
		for c in space:
			if c == '\n':
				lines.append(line)
				line = ''
			else:
				line = line + c
			# }
		# }
	# }
	lines.append(line)
	return '\n'.join(lines)
# }

def border(text = None, left = 0, right = 0, top = 0, bottom = 0, fillchar = '\0'):
	lines = [] if text is None else str(text).split('\n')
	tw = max(map(len, lines) + [0])
	lines = [''] * top + lines + [''] * bottom
	lineformat = '{0}{{0}}{1}'.format(fillchar * left, fillchar * right)
	return '\n'.join(lineformat.format(line.ljust(tw, fillchar)) for line in lines)
# }

def fill(size = (0,0), fillchar = '\0'):
	return '\n'.join([fillchar * size[0]] * size[1])
# }

def composite(fgtext, bgtext, pos = (0,0), fgorigin = (0,0), bgorigin = (0,0), modular = False):
	# this function is really useful
	from itertools import imap, izip, chain, repeat
	bgorigin = tuple(bgorigin)[:2]
	fgorigin = tuple(fgorigin)[:2]
	bglines = [] if bgtext is None else str(bgtext).split('\n')
	fglines = [] if fgtext is None else str(fgtext).split('\n')
	bgw = max(map(len, bglines) + [0])
	bgh = len(bglines)
	fgw = max(map(len, fglines) + [0])
	fgh = len(fglines)
	# empty string has size (0,1), so we use None for size (0,0)
	if bgh == 0: return None
	# ensure lines are proper lengths
	bglines = [line.ljust(bgw, '\0') for line in bglines]
	fglines = [line.ljust(fgw, '\0') for line in fglines]
	# fg-bg offset for bottom-left (input coords are positive right-up)
	fgx = int(math.floor(bgw * bgorigin[0] - fgw * fgorigin[0] + pos[0]))
	fgy = int(math.floor(bgh * bgorigin[1] - fgh * fgorigin[1] + pos[1]))
	# change to top-left offset (text coords are positive right-down)
	fgy = bgh - fgy - fgh
	# composite lines
	fgget = lambda x, y: fglines[(y - fgy) % fgh][(x - fgx) % fgw] if modular or (x >= fgx and y >= fgy and x < fgx + fgw and y < fgy + fgh) else '\0'
	return '\n'.join(''.join(lineit) for lineit in imap(lambda bgline, points: imap(lambda bg, p: chr(ord(fgget(*p)) or ord(bg)), bgline, points), bglines, (izip(xrange(bgw), repeat(y)) for y in xrange(bgh))))
# }

def cut(text = None, pos = (0,0), size = (0,0), fgorigin = (0,0), bgorigin = (0,0), modular = False, fillchar = '\0'):
	# convenience? complement of composite, kinda
	return composite(text, fill(size, fillchar), pos=[-x for x in pos], fgorigin=bgorigin, bgorigin=fgorigin, modular=modular)
# }

def crop(text = None, left = 0, right = 0, top = 0, bottom = 0):
	tw, th = size(text)
	return cut(text, pos=(left, bottom), size=(max(tw - right - left, 0), max(th - top - bottom, 0)))
# }

def strip(text = None, chars = ' '):
	# TODO only if really needed
	raise Exception('unimplemented')
# }

def box(text = None, size = (0,0), fillchar = '\0', toppat = '+-+', bottompat = '+-+', leftpat = '|', rightpat = '|'):
	from itertools import islice, chain, repeat
	lines = [] if text is None else str(text).split('\n')
	tw = max(max(map(len, lines) + [0]), size[0])
	th = max(len(lines), size[1])
	lines.extend([fillchar * tw] * (th - len(lines)))
	topline = '{0}{1}{2}'.format(toppat[0], ''.join(islice(chain.from_iterable(repeat(toppat[1:-1])), tw)), toppat[-1])
	bottomline = '{0}{1}{2}'.format(bottompat[0], ''.join(islice(chain.from_iterable(repeat(bottompat[1:-1])), tw)), bottompat[-1])
	return '\n'.join([topline] + ['{0}{1}{2}'.format(leftpat[y % len(leftpat)], line.ljust(tw, fillchar), rightpat[y % len(rightpat)]) for y, line in enumerate(lines)] + [bottomline])
# }

class TextArea(object):
	
	def __init__(self, size, fontname):
		self.fontname = fontname
		self.size = size
		self.align = 'l'
		self.text = ''
		self.fillchar = '\0'
		self.cursor = 0
		self.scroll = 0.0 # in lines
		self.scrollorigin = 0.0 # fraction of size[1], top==0
		self.lineorigin = 0.0 # fraction of line height, top==0
		self.showcursor = False
		self.blink = False
		self.blinkinterval = 0
		self.writeinterval = 0
		self.blinkwait = 0
		self.writewait = 0
		self._pendingtext = ''
		self._cache = {}
	# }
	
	def _line_height(self):
		return wordart_size(' ', self.fontname)[1]
	# }
	
	def _get_lines(self):
		lines = self._cache.get('lines', None)
		if lines is not None: return lines
		# replace 'hard' LF with CRLF so the LF still occupies a character after splitting
		lines = wordwrap(self.text.replace('\n', '\r\n'), self.size[0], self.fontname).split('\n')
		self._cache['lines'] = lines
		return lines
	# }
	
	def _get_line(self, y):
		if y < 0: return ''
		lines = self._get_lines()
		if y < len(lines): return lines[y]
		return ''
	# }
	
	def _i2y(self, i):
		y = 0
		j = 0
		lines = self._get_lines()
		for line in lines:
			j += len(line)
			if i < j: break
			y += 1
		# }
		return min(y, len(lines) - 1)
	# }
	
	def _y2i(self, y):
		lines = self._get_lines()
		y = max(min(int(y), len(lines) - 1), 0)
		j = 0
		for line in lines[:y]: j += len(line)
		return j
	# }
	
	def _safe_cursor(self):
		return min(max(self.cursor, 0), len(self.text))
	# }
	
	def _update(self):
		# autotype pending text
		# do this first as it can affect the blink state
		if len(self._pendingtext):
			if self.writewait <= 0:
				c = self._pendingtext[0]
				# skip nulls, allows them to be used for 'pause'
				if c != '\0':
					self.insert(c)
					self.writewait = self.writeinterval
				else:
					# use cursor blink interval for pause
					self.writewait = self.blinkinterval
				# }
				self.scroll_to_cursor()
				self._pendingtext = self._pendingtext[1:]
				self.invalidate()
			else:
				self.writewait -= 1
			# }
		# }
		# update cursor blink
		if self.blinkwait <= 0:
			self.blinkwait = self.blinkinterval
			self.blink = not self.blink
			self.invalidate()
		else:
			self.blinkwait -= 1
		# }
		# set blink character in font
		_load_aafont(self.fontname)['\xFF'] = fill((1, self._line_height()), '|' if self.blink else '\0')
	# }
	
	def move_cursor(self, dx = 0, dy = 0):
		i = self._safe_cursor()
		y = self._i2y(i)
		x = i - self._y2i(y)
		y += dy
		x += dx
		self.cursor = self._y2i(y) + max(min(x, len(self._get_line(y)) - 1), 0)
	# }
	
	def insert(self, text, advance = True):
		''' Insert text at cursor position. '''
		i = self._safe_cursor()
		self.text = self.text[:i] + text + self.text[i:]
		self.cursor = i + (len(text) if advance else 0)
		self.blink = False
		self.blinkwait = 0
		self.invalidate()
	# }
	
	def erase(self, text, delta = 1):
		''' Erase text at cursor position. delta=1: delete; delta=-1: backspace. '''
		# TODO
		pass
	# }
	
	def write(self, text):
		self._pendingtext = self._pendingtext + text
	# }
	
	def write_cancel(self):
		self._pendingtext = ''
	# }
	
	def scroll_to(self, i):
		self.invalidate()
		i = min(max(i, 0), len(self.text))
		lines = self._get_lines()
		y = self._i2y(i)
		# TODO test this?
		offset = (self.size[1] / self._line_height() * self.scrollorigin) - self.lineorigin
		scrollmax = y + offset
		scrollmin = y - self.size[1] / self._line_height() + 1 + offset
		self.scroll = max(min(self.scroll, scrollmax), scrollmin)
	# }
	
	def scroll_to_cursor(self):
		self.scroll_to(self.cursor)
	# }
	
	def line_count(self):
		return len(self._get_lines())
	# }
	
	def invalidate(self):
		self._cache = {}
	# }
	
	def __str__(self):
		self._update()
		output = self._cache.get('__str__', None)
		if output is not None: return output
		lines = self._get_lines()
		ymin = int(math.floor(self.scroll - (self.size[1] / self._line_height() * self.scrollorigin) + self.lineorigin))
		ymax = ymin + int(math.ceil(self.size[1] / self._line_height())) + 1
		art = fill(self.size, self.fillchar)
		alignfactor = { 'l' : 0.0, 'c' : 0.5, 'r' : 1.0 }.get(self.align, 0.0)
		for y in xrange(ymin, ymax):
			line = self._get_line(y)
			if self.showcursor and y == self._i2y(self.cursor):
				cx = self._safe_cursor() - self._y2i(y)
				# add special character at cursor pos
				line = line[:cx] + '\xFF' + line[cx:]
			# }
			art = composite(wordart(line.strip(' \t\r\n'), self.fontname), art, pos=(0, (self.scroll - y) * self._line_height() + 0.5), fgorigin=(alignfactor, 1 - self.lineorigin), bgorigin=(alignfactor, 1 - self.scrollorigin))
		# }
		self._cache['__str__'] = art
		return art
	# }
	
# }

































