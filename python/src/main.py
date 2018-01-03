from datetime import datetime as dt
from datetime import timedelta
from logging import getLogger, DEBUG, StreamHandler, Formatter

#loggerのセッティング あとで外に

logger = getLogger(__name__)
logger.setLevel(DEBUG)
stream_handler = StreamHandler()
formatter = Formatter(
    fmt="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
stream_handler.setFormatter(formatter)
stream_handler.setLevel(DEBUG)
logger.addHandler(stream_handler)

MAX_NORMAL_WORK_HOUR = 7
DEFAULT_GO_HOME_TIME = dt.strptime('16:00','%H:%M')
DEFAULT_MIDNIGHT_OVERWORK_TIME = dt.strptime('22:00','%H:%M')
LEGAL_WORKTIME_AMOUNT = timedelta(hours=8)

def main():
    """ エントリポイント"""
    logger.debug('mainの開始')

    #month = input('month > ')
    #time_entry = input('time > ')

    month = '2017/02'
    time_entry = '2017/02/01 08:00-12:00 13:00-26:00'
    l = time_entry.split(" ")
    date_str , working_time_list = l[0], l[1:]
    date = dt.strptime(date_str, '%Y/%m/%d')

    day_hash = {"date": date_str,
                "day": date.isoweekday(), # 1 - 7
                "week": date.isocalendar()[1]} #number of week

    #入力の切り分け
    a = [time.split("-") for time in working_time_list]
    b = [{"start_time":dt.strptime(x[0],'%H:%M'),
          "end_time":dt.strptime(x[1],'%H:%M')} for x in a]

    i_4, b_4 = add_4pm(b)
    i_10, b_10 = add_10pm(b_4)

    day_hash["work_time"] = sum(b_4)

    work_time_by4pm = sum(b_4[:i_4+1])
    day_hash["work_normal_time"] = work_time_by4pm
    day_hash["work_legal_time"] = LEGAL_WORKTIME_AMOUNT - day_hash["work_normal_time"]

    work_time_by10pm = sum(b_10[:i_10+1])
    day_hash["work_illegal_time"] = work_time_by10pm - LEGAL_WORKTIME_AMOUNT

    day_hash["wrok_midnight_overwork_time"] = day_hash["work_time"] - work_time_by10pm



    #if (day_hash["work_time"] > MAX_NORMAL_WORK_HOUR)


def add_4pm(b):
    list = b
    for index, x in enumerate(list):
        logger.debug("check 4pm start")
    if x["end_time"] > DEFAULT_GO_HOME_TIME :
        list.insert(index+1,
                 {"start_time": DEFAULT_GO_HOME_TIME,
                  "end_time": x["end_time"]})
        x["end_time"] = DEFAULT_GO_HOME_TIME
        return index, list

def add_10pm(b):
    list = b
    for index, x in enumerate(list):
        logger.debug("check 10pm start")
    if x["end_time"] > DEFAULT_MIDNIGHT_OVERWORK_TIME :
        list.insert(index+1,
                    {"start_time": DEFAULT_MIDNIGHT_OVERWORK_TIME,
                     "end_time": x["end_time"]})
        x["end_time"] = DEFAULT_MIDNIGHT_OVERWORK_TIME
        return index, list

def sum(b) :
    """働いた時間の合計"""
    from datetime import timedelta
    sum = timedelta()
    for ele in b:
        sum += ele["end_time"] - ele["start_time"]
    return sum

class Mytime:
    def __init__(self):




if __name__ == '__main__':
    main()



