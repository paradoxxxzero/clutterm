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
    effect.set_shader_source(open('gloom.glsl').read())
    effect.set_uniform_value('width', actor.get_width())
    effect.set_uniform_value('height', actor.get_height())
    actor.add_effect(effect)
    return effect


shaders = {
    65470: clear_effects,
    65471: apply_blur_effect,
    65472: apply_colorize_effect,
    65473: apply_desaturate_effect,
    65474: apply_page_turn_effect
}
