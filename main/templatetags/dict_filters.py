from django import template

register = template.Library()


@register.filter
def get_item(d, key):
    """
    Usage in template:
      {{ some_dict|get_item:some_key }}
    """
    if d is None:
        return None
    try:
        return d.get(key)
    except Exception:
        return None
