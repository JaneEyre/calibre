from datetime import date
import calendar
today = date.today()

# weekend 
weekend = lambda today : today.weekday() >= 5

def weekend(current_date):
    day_index = current_date.weekday()
    return day_index >=5

# 1st day of month
month_d1 = date(today.year, today.month, 1) 

# last day of month
_,num_days = calendar.monthrange(today.year, today.month)
month_lastday = date(today.year, today.month, num_days) 