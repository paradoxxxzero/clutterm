uniform sampler2D tex;
uniform float width;
uniform float height;
uniform float time;

float r = 2.;
float sn = .2;

void main()
{
  vec2 resolution = vec2(width, height);
  vec4 col = vec4(0., 0., 0., 0.);
  float d = 1.;
  for (float i = -r; i <= r; i++) {
    for (float j = -r; j <= r; j++) {
      vec2 sh = vec2(i, j) / resolution.xy;
      if(i == 0. && j == 0.) d = .9;
      else d = sn / (i*i + j*j);
      col += texture2D(tex, cogl_tex_coord_in[0].xy + sh) * d;
    }
  }
  cogl_color_out = vec4(col.xyz, texture2D(tex, cogl_tex_coord_in[0].xy).w);
}
