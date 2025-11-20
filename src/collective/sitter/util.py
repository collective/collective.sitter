def mail_contact(name, address):
    name = name.replace('"', r'\"')
    return f'"{name}" <{address}>'
