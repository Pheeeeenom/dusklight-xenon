#version 450
layout(push_constant, std140) uniform Push {
    vec4 column0;
    vec4 column1;
    vec4 column2;
    vec4 column3;
    vec4 translation;
} upush;
layout(location = 0) in vec2 in_position;
layout(location = 1) in vec4 in_color;
layout(location = 2) in vec2 in_uv;
layout(location = 0) out vec4 out_color;
layout(location = 1) out vec2 out_uv;
void main() {
    vec4 position = vec4(in_position, 0.0, 0.0) + upush.translation;
    gl_Position = upush.column0 * position.xxxx + upush.column1 * position.yyyy + upush.column3;
    out_color = in_color;
    out_uv = in_uv;
}
