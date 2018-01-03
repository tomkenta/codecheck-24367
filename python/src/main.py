from datetime import datetime, timedelta
from itertools import groupby
from logging import getLogger, StreamHandler, Formatter, DEBUG, WARN
import sys

logger = getLogger(__name__)
logger.setLevel(DEBUG)
stream_handler = StreamHandler()
formatter = Formatter(
    fmt="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
stream_handler.setFormatter(formatter)
stream_handler.setLevel(DEBUG)
logger.addHandler(stream_handler)

MAX_NORMAL_WORK_HOUR = 7
DEFAULT_GO_HOME_TIME = timedelta(hours=16)
DEFAULT_MIDNIGHT_OVERWORK_TIME = timedelta(hours=22)
DEFAULT_CHANGE_DAY_TIME = timedelta(hours=24)
LEGAL_WORKTIME_AMOUNT = timedelta(hours=8)
PRESCRIBED_HOLIDAY = 6 #土曜日
LEGAL_HOLIDAY = 7 #日曜日

def main():
    """ エントリポイント"""
    if 'test' in sys.argv:
        logger.setLevel(WARN)
        stream_handler.setLevel(WARN)
        logger.addHandler(stream_handler)
        # \nもついてくる readline
        month = sys.stdin.readline().rstrip()
        # \n でsplitしてlistになる
        time_entry = sys.stdin.readlines()
    else :
        month = '2017/01'
        time_entry = [

            '2017/01/02 08:00-12:00 13:00-17:00',
            '2017/01/03 08:00-12:00 13:00-17:00',
            '2017/01/04 08:00-12:00 13:00-17:20',
            '2017/01/05 08:00-12:00 13:00-17:20',
            '2017/01/06 08:00-12:00 13:00-18:40',

            '2017/01/09 08:00-12:00 13:00-18:00',
            '2017/01/10 08:00-12:00 13:00-18:00',
            '2017/01/11 08:00-12:00 13:00-18:00',
            '2017/01/12 08:00-12:00 13:00-17:00',
            '2017/01/13 08:00-12:00 13:00-21:00',

            '2017/01/16 08:00-12:00 13:00-18:00',
            '2017/01/17 08:00-12:00 13:00-18:00',
            '2017/01/18 08:00-12:00 13:00-18:00',
            '2017/01/19 08:00-12:00 13:00-17:00',
            '2017/01/20 08:00-12:00 13:00-21:00',

            '2017/01/23 08:00-12:00 13:00-18:00',
            '2017/01/24 08:00-12:00 13:00-18:00',
            '2017/01/25 08:00-12:00 13:00-18:00',
            '2017/01/26 08:00-12:00 13:00-17:00',
            '2017/01/27 08:00-12:00 13:00-21:00',

            '2017/01/30 08:00-12:00 13:00-18:00',
            '2017/01/31 08:00-12:00 13:00-18:00',
            '2017/02/01 08:00-12:00 13:00-18:00',
            '2017/02/02 08:00-12:00 13:00-17:00',
            '2017/02/03 08:00-12:00 13:00-21:00'
        ]

    logger.debug('mainの開始')
    logger.debug('入力の解析,DBに保存')

    db = [gen_day_hash(x) for x in time_entry]
    this_month = datetime.strptime(month,'%Y/%m').month

    result   = {
                "work_time": timedelta(0),
                "work_normal_time": timedelta(0),
                "work_legal_time": timedelta(0),
                "work_illegal_time": timedelta(0),
                "work_midnight_overwork_time": timedelta(0),
                "work_prescribed_holiday_time": timedelta(0),
                "work_legal_holiday_time": timedelta(0)
                }

    logger.debug('40時間計算')
    for key, group in groupby(db, key= lambda x: x['week']):
        res = {
            "work_time": timedelta(0),
        }
        for record in group:
            res["work_time"] += record["work_time"]
            if res["work_time"] > timedelta(hours=40):
                tmp = res["work_time"] - timedelta(hours=40)
                if record["work_time"] - tmp > timedelta(hours=7) :
                    record["work_normal_time"] = timedelta(hours=7)
                    record["work_legal_time"] = timedelta(0)
                    record["work_illegal_time"] = record["work_time"] - timedelta(hours=7)
                else :
                    record["work_normal_time"] = record["work_time"] - tmp
                    record["work_legal_time"] = timedelta(0)
                    record["work_illegal_time"] = tmp

    logger.debug('DBに対して演算')
    for record in db :
        if record["date"].month is this_month:
            result["work_time"] += record["work_time"]
            result["work_normal_time"] += record["work_normal_time"]
            result["work_legal_time"] += record["work_legal_time"]
            result["work_illegal_time"] += record["work_illegal_time"]
            result["work_midnight_overwork_time"] += record["work_midnight_overwork_time"]
            result["work_prescribed_holiday_time"] += record["work_prescribed_holiday_time"]
            result["work_legal_holiday_time"] += record["work_legal_holiday_time"]

    logger.debug('結果出力')
    timeprint(result["work_legal_time"],1)
    timeprint(result["work_illegal_time"],1)
    timeprint(result["work_midnight_overwork_time"],1)
    timeprint(result["work_prescribed_holiday_time"],1)
    timeprint(result["work_legal_holiday_time"],1)

def gen_day_hash(time_string):

    l = time_string.split(" ")
    date_str, working_time_list = l[0], l[1:]
    date = datetime.strptime(date_str, '%Y/%m/%d')

    day_hash = {"date": date,
                "day": date.isoweekday(), # 1 - 7
                "week": date.isocalendar()[1], #number of week
                "work_time": timedelta(0),
                "work_normal_time": timedelta(0),
                "work_legal_time": timedelta(0),
                "work_illegal_time": timedelta(0),
                "work_midnight_overwork_time": timedelta(0),
                "work_prescribed_holiday_time": timedelta(0),
                "work_legal_holiday_time": timedelta(0)
                }

    a = [time.split("-") for time in working_time_list]
    b = [{"start_time":date_add_by_string(date,x[0]),
        "end_time":date_add_by_string(date,x[1])} for x in a]

    i_4, b_4 = add_4pm(date, b)
    i_10, b_10 = add_10pm(date, b_4)
    i_0, b_0 = add_0am(date, b_10)

    day_hash["work_time"] = sum(b)

    if date.isoweekday() == PRESCRIBED_HOLIDAY :
        day_hash["work_prescribed_holiday_time"] = day_hash["work_time"]
        if i_10 is not -1:
            work_time_by10pm = sum(b_10[:i_10+1])
            day_hash["work_midnight_overwork_time"] = day_hash["work_time"] - work_time_by10pm

        if i_0 is not -1: #0amまで
            if (date + timedelta(days=1)).isoweekday() == LEGAL_HOLIDAY:
                work_time_by0am = sum(b_0[:i_0+1])
                day_hash["work_prescribed_holiday_time"] = work_time_by0am
                day_hash["work_legal_holiday_time"] = day_hash["work_time"] - work_time_by0am

    elif date.isoweekday() == LEGAL_HOLIDAY :
        day_hash["work_legal_holiday_time"] = day_hash["work_time"]
        if i_10 is not -1:
            work_time_by10pm = sum(b_10[:i_10+1])
            day_hash["work_midnight_overwork_time"] = day_hash["work_time"] - work_time_by10pm
    else :

        if i_4 is not -1: #4pmまで
            work_time_by4pm = sum(b_4[:i_4+1])
            day_hash["work_normal_time"] = work_time_by4pm
            day_hash["work_legal_time"] = LEGAL_WORKTIME_AMOUNT - day_hash["work_normal_time"]
            day_hash["work_illegal_time"] = day_hash["work_time"] - LEGAL_WORKTIME_AMOUNT

        if i_10 is not -1: #10pmまで
            work_time_by10pm = sum(b_10[:i_10+1])
            day_hash["work_midnight_overwork_time"] = day_hash["work_time"] - work_time_by10pm

        if i_0 is not -1: #0amまで
            if (date + timedelta(days=1)).isoweekday() == PRESCRIBED_HOLIDAY:
                work_time_by0am = sum(b_0[:i_0+1])
                day_hash["work_illegal_time"] = work_time_by0am - LEGAL_WORKTIME_AMOUNT
                day_hash["work_prescribed_holiday_time"] = day_hash["work_time"] - work_time_by0am

    return day_hash

def timeprint(time,mode=0):
    seconds = time.total_seconds()
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    str = '{}:{}:{}'.format(int(hours), int(minutes), int(seconds))

    assert mode is 0 or 1 , "modeは0/1です"
    if mode is 0:
        print(str)
    elif mode is 1:
        if int(minutes) < 30: print(int(hours))
        else: print(int(hours)+1)


def date_add_by_string(date, time_string='00:00') :
    hours, mins = map(int, time_string.split(":"))
    if hours >= 24:
        return date + timedelta(days=1, hours=hours-24, minutes=mins)
    else:
        return date + timedelta(hours=hours, minutes=mins)

def add_4pm(date,b):
    list = b
    for index, x in enumerate(list):
        logger.debug("check 4pm start")
        if x["end_time"] > date + DEFAULT_GO_HOME_TIME :
            list.insert(index+1,
                     {"start_time": date + DEFAULT_GO_HOME_TIME,
                      "end_time": x["end_time"]})
            x["end_time"] = date + DEFAULT_GO_HOME_TIME
            return index, list
    return -1, list

def add_10pm(date,b):
    list = b
    for index, x in enumerate(list):
        logger.debug("check 10pm start")
        if x["end_time"] > date + DEFAULT_MIDNIGHT_OVERWORK_TIME :
            list.insert(index+1,
                        {"start_time": date + DEFAULT_MIDNIGHT_OVERWORK_TIME,
                         "end_time": x["end_time"]})
            x["end_time"] = date + DEFAULT_MIDNIGHT_OVERWORK_TIME
            return index, list
    return -1, list

def add_0am(date,b):
    list = b
    for index, x in enumerate(list):
        logger.debug("check 0am start")
        if x["end_time"] >= date + DEFAULT_CHANGE_DAY_TIME:
            list.insert(index+1,
                        {"start_time": date + DEFAULT_CHANGE_DAY_TIME,
                         "end_time": x["end_time"]})
            x["end_time"] = date + DEFAULT_CHANGE_DAY_TIME
            return index, list
    return -1, list

def sum(b) :
    """働いた時間の合計"""
    sum = timedelta()
    for ele in b:
        sum += ele["end_time"] - ele["start_time"]
    return sum

if __name__ == '__main__':
    main()
