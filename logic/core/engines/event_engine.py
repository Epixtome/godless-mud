import logging

logger = logging.getLogger("GodlessMUD")

_SUBSCRIBERS = {}

def subscribe(event_name, callback):
    """Registers a function to be called when an event fires."""
    if event_name not in _SUBSCRIBERS:
        _SUBSCRIBERS[event_name] = []
    _SUBSCRIBERS[event_name].append(callback)
    logger.debug(f"Subscribed {callback.__name__} to {event_name}")

def dispatch(event_name, context=None, **kwargs):
    """
    Fires an event. 
    'context' is a mutable dictionary containing event data.
    Accepts kwargs to build context dynamically if a dict isn't passed.
    """
    if context is None:
        context = {}
    
    # Merge kwargs into context
    context.update(kwargs)

    if event_name in _SUBSCRIBERS:
        for callback in _SUBSCRIBERS[event_name]:
            try:
                callback(context)
            except Exception as e:
                logger.error(f"Error in event handler {callback.__name__} for {event_name}: {e}")