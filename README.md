collective.sitter – A (baby)sitter portal implemented on top of Plone
=====================================================================

This Plone add-on implements an application which allows people to offer babysitting services, and others to find them and get in contact. Such a portal may be offered, for example, by a university that wishes to connect staff in need of child care with students who want to earn some additional money.

The functionality of this package is based around a folder, called a sitter folder, that holds all the sitter advertisements and provides some search facility. Each advertisement consists of a freely editable text portion, optionally an image, and some structured data about the sitter including age, local availability, qualification and experience. Possible values for the latter are configurable through the control panel.

A contact form is shown below each advertisement and sending a message to the respective sitter is the only interaction implemented by the portal. Only Plone users may create sitter advertisements and use the contact form and there is a workflow in place to make sure sitters have agreed to terms and conditions before creating their advertisement.

Furthermore, the package implements some housekeeping functionality such as reminding users to log in now and then and removing advertisements by users who don't.

The code was originally written by Philipps-Universität Marburg, Germany, and made public in order to share the effort with other universities.
