import datetime


def year(request):
    year1 = datetime.date.today()
    year2 = int(year1.year)
    return {'year': year2}
