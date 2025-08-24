from djapy_ext.exception import MsgErr


def handle_msg_err(request, exception: MsgErr):
    return 404, {
        'message': exception.message,
        'alias': exception.alias,
        'message_type': exception.message_type,
        'inline': exception.inline,
        'action': exception.action,
        'redirect': exception.redirect
    }
