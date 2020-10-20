from datetime import date

def get_day_from_personal_id(personal_id):
    day = int(personal_id[4:6])
    if day > 50:
        day -= 50
    return day


def get_month_from_personal_id(personal_id):
    year = get_year_from_personal_id(personal_id)
    month = int(personal_id[2:4])
    if month > 70 and year > 2003:
        month -= 70
    elif month > 50:
        month -= 50
    elif month > 20 and year > 2003:
        month -= 20
    return month


def get_year_from_personal_id(personal_id):
    year = int(personal_id[0:2])
    value = personal_id.replace('/', '')
    year += 2000 if year < 54 and len(value) == 10 else 1900
    return year


def personal_id_date(personal_id):
    try:
        return date(get_year_from_personal_id(personal_id), get_month_from_personal_id(personal_id),
                    get_day_from_personal_id(personal_id))
    except ValueError:
        raise ValueError('Invalid personal id')
