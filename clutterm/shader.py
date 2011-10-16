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
    #version 110
    uniform sampler2D tex;
    uniform float fraction;
    uniform float height;
    const float c = -0.2;
    const float border_max_height = 60.0;

    mat4 contrast = mat4 (1.0 + c, 0.0, 0.0, 0.0,
                          0.0, 1.0 + c, 0.0, 0.0,
                          0.0, 0.0, 1.0 + c, 0.0,
                          0.0, 0.0, 0.0, 1.0);
    vec4 off = vec4(0.633, 0.633, 0.633, 0);
    void main()
    {
      vec4 color = texture2D(tex, cogl_tex_coord_in[0].xy);
      float y = height * cogl_tex_coord_in[0].y;

      // To reduce contrast, blend with a mid gray
      cogl_color_out = color * contrast - off * c * color.a;

      // We only fully dim at a distance of BORDER_MAX_HEIGHT from the top and
      // when the fraction is 1.0. For other locations and fractions we linearly
      // interpolate back to the original undimmed color, so the top of the window
      // is at full color.
      cogl_color_out = color + (cogl_color_out - color) * max(min(y / border_max_height, 1.0), 0.0);
      cogl_color_out = color + (cogl_color_out - color) * fraction;
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
