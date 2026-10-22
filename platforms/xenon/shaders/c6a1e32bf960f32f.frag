#version 450
layout(set = 0, binding = 0) uniform sampler2D source;
layout(location = 0) in vec4 in_color;
layout(location = 1) in vec2 in_uv;
layout(location = 0) out vec4 o_color;
void main() {
    o_color = in_color * texture(source, in_uv);
}
