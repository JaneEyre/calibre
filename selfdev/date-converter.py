from datetime import date

current_date = current_date = date.today()

# date to 'YYYY-MM-DD' string format
formatted_date = current_date.strftime("%Y-%m-%d")
print(formatted_date)

# date to 'MMM DD, YYYY' string format
formatted_date = current_date.strftime("%b %d, %Y")
print(formatted_date)

# 24_01 , 25_11 : %y for two-digit year, %m for two-digit month
formatted_date = current_date.strftime("%y_%m")
print(formatted_date)
