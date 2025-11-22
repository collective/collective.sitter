def mail_contact(name, address):
    if not name:
        return address

    name = name.replace('"', r'\"')
    return f'"{name}" <{address}>'
