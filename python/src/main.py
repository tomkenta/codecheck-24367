#coding: UTF-8
from datetime import datetime, timedelta
from itertools import groupby
from logging import getLogger, StreamHandler, Formatter, DEBUG, WARN
import sys

#logging
logger = getLogger(__name__)
logger.setLevel(DEBUG)
stream_handler = StreamHandler()
formatter = Formatter(
    fmt="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
stream_handler.setFormatter(formatter)
stream_handler.setLevel(DEBUG)
logger.addHandler(stream_handler)


DEFAULT_GO_HOME_TIME = timedelta(hours=16)
DEFAULT_MIDNIGHT_OVERWORK_TIME = timedelta(hours=22)
DEFAULT_CHANGE_DAY_TIME = timedelta(hours=24)
LEGAL_WORKTIME_AMOUNT = timedelta(hours=8)

PRESCRIBED_HOLIDAY = 6 #土曜日
LEGAL_HOLIDAY = 7 #日曜日

def main():
    """
    entry_point
    """
    # ./test.sh を実行した時用
    if 'test' in sys.argv:

        # logger のレベルをwarningに
        logger.setLevel(WARN)
        stream_handler.setLevel(WARN)
        logger.addHandler(stream_handler)

        # 1行目で計算する月
        month = sys.stdin.readline().rstrip()
        # 2行目で当月の勤務時間エントリをリストで取得
        time_entry = sys.stdin.readlines()

    # ./test.sh を実行した時用
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

    # 勤務時間エントリをパースして計算に必要な情報を持ったレコードにしてdbに保存する
    db = [gen_day_hash(x) for x in time_entry]

    # 計算する月
    this_month = datetime.strptime(month,'%Y/%m').month

    logger.debug('40時間計算')

    # 入力は日付順に並んでいると想定 TODO：並んでいな場合の実装
    # 同じ週のレコードでグループ分け
    for key, group in groupby(db, key= lambda x: x['week']):
        # 日毎に総労働時間加算用hの初期化
        h = {
            "work_time": timedelta(0)
        }
        # group : 同じ週のレコードのグループ
        for record in group:
            h["work_time"] += record["work_time"]
            # 週の総労働時間が40hを超えている時
            if h["work_time"] > timedelta(hours=40):
                over_time = h["work_time"] - timedelta(hours=40)
                # over した時間による分岐
                if record["work_time"] - over_time > timedelta(hours=7):
                    record["work_normal_time"] = timedelta(hours=7)
                    record["work_legal_time"] = timedelta(0)
                    record["work_illegal_time"] = record["work_time"] - timedelta(hours=7)
                else :
                    record["work_normal_time"] = record["work_time"] - over_time
                    record["work_legal_time"] = timedelta(0)
                    record["work_illegal_time"] = over_time

    #結果出力用のhashを初期化
    result = {
            "work_time": timedelta(0),
            "work_normal_time": timedelta(0),
            "work_legal_time": timedelta(0),
            "work_illegal_time": timedelta(0),
            "work_midnight_overwork_time": timedelta(0),
            "work_prescribed_holiday_time": timedelta(0),
            "work_legal_holiday_time": timedelta(0)
        }

    logger.debug('DBに対して演算')
    # 該当する月のレコードの各カラムによる足し上げ
    for record in db :
        # レコードの月が標準入力の月と一致しているか
        if record["date"].month is this_month:
            result["work_time"] += record["work_time"]
            result["work_normal_time"] += record["work_normal_time"]
            result["work_legal_time"] += record["work_legal_time"]
            result["work_illegal_time"] += record["work_illegal_time"]
            result["work_midnight_overwork_time"] += record["work_midnight_overwork_time"]
            result["work_prescribed_holiday_time"] += record["work_prescribed_holiday_time"]
            result["work_legal_holiday_time"] += record["work_legal_holiday_time"]

    logger.debug('結果出力')
    # 四捨五入で出力
    timeprint(result["work_legal_time"],1)
    timeprint(result["work_illegal_time"],1)
    timeprint(result["work_midnight_overwork_time"],1)
    timeprint(result["work_prescribed_holiday_time"],1)
    timeprint(result["work_legal_holiday_time"],1)

def gen_day_hash(time_string):
    """
    :param time_string: 労働時間エントリ ex '2017/01/16 08:00-12:00 13:00-18:00'
    :return: hash ex.
                {"date": datetime,                         # 日付 (%Y/%m/%d')
                "day": datetime.isoweekday(),              # 曜日 1(月) ~ 7（日）
                "week": datetime.isocalendar()[],          # 週番号
                "work_time": timedelta,                    # 実働時間
                "work_normal_time": timedelta,             # 所定内労働時間
                "work_legal_time": timedelta,              # 法定内労働時間
                "work_illegal_time": timedelta,            # 法定外労働時間
                "work_midnight_overwork_time": timedelta,  # 深夜残業時間
                "work_prescribed_holiday_time": timedelta, # 所定休日労働時間
                "work_legal_holiday_time": timedelta       # 法定休日労働時間数
                }
    """

    # time_string をスペースで分割 -> 2017/02/03, [08:00-12:00 13:00-21:00]
    l = time_string.split(" ")
    date_str, working_time_list = l[0], l[1:]
    date = datetime.strptime(date_str, '%Y/%m/%d')

    #返り値用のhashの初期化
    day_hash = {"date": date,                                 # 日付 (%Y/%m/%d')
                "day": date.isoweekday(),                     # 曜日 1(月) ~ 7（日）
                "week": date.isocalendar()[1],                # 週番号
                "work_time": timedelta(0),                    # 実働時間
                "work_normal_time": timedelta(0),             # 所定内労働時間
                "work_legal_time": timedelta(0),              # 法定内労働時間
                "work_illegal_time": timedelta(0),            # 法定外労働時間
                "work_midnight_overwork_time": timedelta(0),  # 深夜残業時間
                "work_prescribed_holiday_time": timedelta(0), # 所定休日労働時間
                "work_legal_holiday_time": timedelta(0)       # 法定休日労働時間数
                }
    # 労働時間エントリを-で分割する
    a = [time.split("-") for time in working_time_list]
    # 分割したものをそれぞれ日付にする
    b = [{"start_time": date_add_by_string(date, x[0]),
        "end_time": date_add_by_string(date, x[1])} for x in a]

    # 基準点となる時間のチェック (16:00, 22:00, 24:00)
    # 基準点を超す場合はそこにチェックポイントをいれる
    i_4, b_4 = add_4pm(date, b)
    i_10, b_10 = add_10pm(date, b_4)
    i_0, b_0 = add_0am(date, b_10)

    # 総労働時間
    day_hash["work_time"] = sum(b)

    # 休日のチェック
    if date.isoweekday() == PRESCRIBED_HOLIDAY :
        # 所定休日労働時間
        day_hash["work_prescribed_holiday_time"] = day_hash["work_time"]
        # 深夜残業時間 チェック
        if i_10 is not -1:
            work_time_by10pm = sum(b_10[:i_10+1])
            day_hash["work_midnight_overwork_time"] = day_hash["work_time"] - work_time_by10pm
        # 日付変更 チェック
        if i_0 is not -1: #0amまで
            if (date + timedelta(days=1)).isoweekday() == LEGAL_HOLIDAY:
                work_time_by0am = sum(b_0[:i_0+1])
                day_hash["work_prescribed_holiday_time"] = work_time_by0am
                # 日付を越えた分は法定休日労働時間数とする
                day_hash["work_legal_holiday_time"] = day_hash["work_time"] - work_time_by0am

    elif date.isoweekday() == LEGAL_HOLIDAY :
        # 法定休日労働時間
        day_hash["work_legal_holiday_time"] = day_hash["work_time"]
        # 深夜残業時間 チェック
        if i_10 is not -1:
            work_time_by10pm = sum(b_10[:i_10+1])
            day_hash["work_midnight_overwork_time"] = day_hash["work_time"] - work_time_by10pm
    else :
        # 平日の計算
        # 所定, 法定内、法定外 労働時間チェック
        if i_4 is not -1:
            work_time_by4pm = sum(b_4[:i_4+1])
            day_hash["work_normal_time"] = work_time_by4pm
            day_hash["work_legal_time"] = LEGAL_WORKTIME_AMOUNT - day_hash["work_normal_time"]
            day_hash["work_illegal_time"] = day_hash["work_time"] - LEGAL_WORKTIME_AMOUNT
        # 深夜残業時間 チェック
        if i_10 is not -1: #10pmまで
            work_time_by10pm = sum(b_10[:i_10+1])
            day_hash["work_midnight_overwork_time"] = day_hash["work_time"] - work_time_by10pm

        # 日付変更 チェック
        if i_0 is not -1: #0amまで
            if (date + timedelta(days=1)).isoweekday() == PRESCRIBED_HOLIDAY:
                work_time_by0am = sum(b_0[:i_0+1])
                day_hash["work_illegal_time"] = work_time_by0am - LEGAL_WORKTIME_AMOUNT
                # 日付を越えた分は所定休日労働時間数とする
                day_hash["work_prescribed_holiday_time"] = day_hash["work_time"] - work_time_by0am

    return day_hash

def timeprint(time,mode=0):
    """
    :param time: timedelta
    :param mode: 0: 秒単位まで表示する, 1:分を四捨五入で時間を表示する
    :return: なし （print される）
    """
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
    """
    :param date: datetime
    :param time_string: formatted_string ex. 16:00 , 25:00...
    :return: datetime (dateにtime_stringの分足したもの）
    """

    hours, mins = map(int, time_string.split(":"))
    if hours >= 24:
        return date + timedelta(days=1, hours=hours-24, minutes=mins)
    else:
        return date + timedelta(hours=hours, minutes=mins)

def add_4pm(date,b):
    """
    :param date: datetime
    :param b: list ex.([{"start_time": datetime,"end_time": datetime}, ... ])
    :return: index, list (listは bに対して チェックポイント16:00が挿入されたもの),
    index は16:00を挿入したときの listのindex, 挿入しない場合は-1を返す
    :description: ex {"start_time":datetime(15:00), "end_time":datatime(18:00)} ->
        [{"start_time":datetime(15:00), "end_time":datatime(16:00)}, {"start_time":datetime(16:00), "end_time":datatime(18:00)}]
    """
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
    """
    add_4pm の 10pm版 (22:00)
    """
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
    """
    add_4pm の 0pm版 (24:00)
    """
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
    """
    :param b: list
    :return: 労働時間の合計
    """
    sum = timedelta()
    for ele in b:
        sum += ele["end_time"] - ele["start_time"]
    return sum

if __name__ == '__main__':
    main()
