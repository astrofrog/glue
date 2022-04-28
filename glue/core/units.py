from astropy import units as u


def find_unit_choices(unit_strings):

    unit_objects = {}
    for unit_string in unit_strings:
        try:
            unit_objects.add(u.Unit(unit_string))
        except ValueError:
            pass

