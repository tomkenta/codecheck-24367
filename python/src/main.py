from datetime import datetime as dt
from datetime import timedelta
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
        month = sys.stdin.readline()
        time_entry = sys.stdin.readlines()[0]
    else :
        month = '2017/01'
        time_entry = [
            '2017/01/16 08:00-12:00 13:00-18:00',
            '2017/01/17 08:00-12:00 13:00-18:00',
            '2017/01/18 08:00-12:00 13:00-18:00'
        ]

    logger.debug('mainの開始')

    l = time_entry.split(" ")
    date_str , working_time_list = l[0], l[1:]
    date = dt.strptime(date_str, '%Y/%m/%d')

    day_hash = {"date": date_str,
                "day": date.isoweekday(), # 1 - 7
                "week": date.isocalendar()[1], #number of week
                "work_time": 0,
                "work_normal_time": 0,
                "work_legal_time": 0,
                "work_illegal_time": 0,
                "work_midnight_overwork_time": 0,
                "work_prescribed_holiday_time": 0,
                "work_legal_holiday_time": 0
                }

    #入力の切り分け
    a = [time.split("-") for time in working_time_list]
    b = [{"start_time":hogehoge(date,x[0]),
        "end_time":hogehoge(date,x[1])} for x in a]

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



    timeprint(day_hash["work_legal_time"])
    timeprint(day_hash["work_illegal_time"])
    timeprint(day_hash["work_midnight_overwork_time"])
    timeprint(day_hash["work_prescribed_holiday_time"])
    timeprint(day_hash["work_legal_holiday_time"])

def timeprint(time):
    print(int(str(time).split(":")[0]))

def hogehoge(date, time_string='00:00') :
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

#まだ例外は弱い
class MyTime :
    def __init__(self,hour=0, min=0):
        self.hour = hour
        self.min = min
    def __add__(self, other):
        return self.__class__(self.hour + other.hour, self.min + other.min)
    def __sub__(self, other):
        return self.__class__(self.hour - other.hour, self.min - other.min)
    def __str__(self):
        return "%02d:%02d" % (self.hour, self.min)
    def __repr__(self):
        return self.__str__()

if __name__ == '__main__':
    main()



