import business_calendar
import datetime as dt
import collections

today = dt.date.today()

# Source: https://www.gov.hk/en/about/abouthk/holiday/2019.htm
general_holiday = collections.namedtuple(
    'GENERAL_HOLIDAY',
    [
        'New_year',
        'Lunar_new_year_day',
        'The_second_day_of_the_Lunar_New_Year',
        'The_third_day_of_Lunar_New_Year',
        'Ching_Ming_Festival',
        'Good_Friday',
        'The_day_following_Good_Friday',
        'Easter_Monday',
        'Labour_Day',
        'Birthday_of_the_Buddha',
        'Tune_Ng_Festival',
        'HKSAR_Establishment_Day',
        'The_day_following_the_Chinese_Mid_Autumn_Festival',
        'National_Day',
        'Chung_Yeung_Festival',
        'Christmas_Day',
        'The_first_weekday_after_Christmas_Day',
    ],
)
# 2019 General holiday
# https://www.gov.hk/en/about/abouthk/holiday/2019.htm
GENERAL_HOLIDAY_2019 = general_holiday(
    dt.date(2019, 1, 1),
    dt.date(2019, 2, 5),
    dt.date(2019, 2, 6),
    dt.date(2019, 2, 7),
    dt.date(2019, 4, 5),
    dt.date(2019, 4, 19),
    dt.date(2019, 4, 20),
    dt.date(2019, 4, 22),
    dt.date(2019, 5, 1),
    dt.date(2019, 5, 13),
    dt.date(2019, 6, 7),
    dt.date(2019, 7, 1),
    dt.date(2019, 9, 14),
    dt.date(2019, 10, 1),
    dt.date(2019, 10, 7),
    dt.date(2019, 12, 25),
    dt.date(2019, 12, 26),
)
# 2020 General holiday -
# https://www.gov.hk/en/about/abouthk/holiday/2020.htm
GENERAL_HOLIDAY_2020 = general_holiday(
    dt.date(2020, 1, 1),
    dt.date(2020, 1, 25),
    dt.date(2020, 1, 27),
    dt.date(2020, 1, 28),
    dt.date(2020, 4, 4),
    dt.date(2020, 4, 10),
    dt.date(2020, 4, 11),
    dt.date(2020, 4, 13),
    dt.date(2020, 4, 30),
    dt.date(2020, 5, 1),
    dt.date(2020, 6, 25),
    dt.date(2020, 7, 1),
    dt.date(2020, 10, 2),
    dt.date(2020, 10, 1),
    dt.date(2020, 10, 26),
    dt.date(2020, 12, 25),
    dt.date(2020, 12, 26),
)

trading_calendar = business_calendar.Calendar(
    holidays=GENERAL_HOLIDAY_2019 + GENERAL_HOLIDAY_2020
)


def last_td(day):
    return trading_calendar.buseom(day)


def second_last_td(day):
    last_business_day_of_month = last_td(day)
    return trading_calendar.addbusdays(last_business_day_of_month, -1)


def need_rollover(day):
    expiry_day = second_last_td(day)
    return expiry_day <= day
