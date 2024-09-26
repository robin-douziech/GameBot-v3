from variables import *

def _default_config(variable, default) :
    if isinstance(default, dict) :
        if isinstance(variable, dict) :
            for key in default:
                if not(key in variable) :
                    variable[key] = default[key]
                else :
                    variable[key] = _default_config(variable[key], default[key])
        else :
            variable = default
    else :
        for type in [list, str, int, bool, float] :
            if isinstance(default, type) and not(isinstance(variable, type)) :
                variable = default
    return variable




def set_default_config(variable: dict[any], default: dict[any]) :
    for key in variable :
        variable[key] = _default_config(variable[key], default)
    return variable