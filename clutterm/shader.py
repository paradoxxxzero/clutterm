from gi.repository import Clutter


def clear_effects(actor):
    actor.clear_effects()


def apply_blur_effect(actor):
    actor.clear_effects()
    effect = Clutter.BlurEffect()
    actor.add_effect(effect)


def apply_colorize_effect(actor):
    actor.clear_effects()
    effect = Clutter.ColorizeEffect()
    effect.set_tint(Clutter.Color.new(0, 0, 255, 150))
    actor.add_effect(effect)


def apply_desaturate_effect(actor):
    actor.clear_effects()
    effect = Clutter.DesaturateEffect()
    effect.set_factor(.5)
    actor.add_effect(effect)


def apply_page_turn_effect(actor):
    actor.clear_effects()
    effect = Clutter.PageTurnEffect()
    effect.set_angle(10)
    effect.set_period(.2)
    actor.add_effect(effect)


def apply_glsl_effect(actor):
    actor.clear_effects()
    effect = Clutter.ShaderEffect()
    effect.shader_type = 1
    effect.set_shader_source("""
uniform sampler2D tex;
float height = 1000.;
float width = 2000.;

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
    """)
    actor.add_effect(effect)


shaders = {
    65470: clear_effects,
    65471: apply_blur_effect,
    65472: apply_colorize_effect,
    65473: apply_desaturate_effect,
    65474: apply_page_turn_effect,
    65475: apply_glsl_effect,
}
