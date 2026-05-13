from functools import wraps
from flask import render_template

def require_valid_form(form_class, template, **template_ctx):
    """Decorator: instantiate `form_class`, call `validate_on_submit()` and
    - if valid: call wrapped function with `form` as first arg
    - otherwise: render `template` with the form (for GET or invalid POST)
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            form = form_class()
            if form.validate_on_submit():
                return fn(form, *args, **kwargs)
            return render_template(template, form=form, **template_ctx)
        return wrapper
    return decorator
