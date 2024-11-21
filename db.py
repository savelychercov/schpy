from datetime import time, timedelta
import pickle
import os
from abc import ABC, abstractmethod
import sys
from pathlib import Path

# region Classes


class PairTime:  # pair: start, end, pair_type
    def __init__(self, start: time, end: time, pair_type: str):
        self.start = start
        self.end = end or start + timedelta(hours=1, minutes=30)
        self.pair_type = pair_type

    def __repr__(self):
        return f"({self.start}-{self.end}, {self.pair_type})"
    
    def get_str(self):
        return (f"{str(self.start.hour).rjust(2, '0')}:{str(self.start.minute).rjust(2, '0')} - "
                f"{str(self.end.hour).rjust(2, '0')}:{str(self.end.minute).rjust(2, '0')}")


class Pair:  # pair: date, day, number, pair_time, pair_type, group, teacher, classroom
    def __init__(self, date: str, day: str, number: int, pair_time: PairTime, pair_type: str, group: str,
                 discipline: str, teacher: str, classroom: str):
        self.date = date
        self.day = day
        self.number = number
        self.pair_time = pair_time
        self.pair_type = pair_type
        self.group = group
        self.discipline = discipline
        self.teacher = teacher
        self.classroom = classroom

    def __repr__(self):
        return f"{self.date} | {self.day} | {self.number} | {self.pair_time} | {self.pair_type} | {self.discipline} | {self.teacher} | {self.classroom}"


class Teacher:  # teacher: name, disciplines, groups
    def __init__(self, name: str, disciplines: set, groups: set):
        self.name = name
        self.disciplines = disciplines
        self.groups = groups

    def __repr__(self):
        return f"({self.name}|{self.disciplines}|{self.groups})"


class TeachersSchedule:  # teachers_schedule: day, pairs
    """
    Возвращает объект расписания преподавателя для каждого дня недели

    Один день недели это список пар из 6 слотов, например (True, False, True, True, True, True), None - день не свободен

    True - Пара свободна, False - Пара занята или пару нельзя поставить на это время

    :param mon: Понедельник
    :param tue: Вторник
    :param wed: Среда
    :param thu: Четверг
    :param fri: Пятница
    :param sat: Суббота
    :param sun: Воскресенье
    """

    def __init__(self,
                 mon: list[bool] = None,
                 tue: list[bool] = None,
                 wed: list[bool] = None,
                 thu: list[bool] = None,
                 fri: list[bool] = None,
                 sat: list[bool] = None,
                 sun: list[bool] = None):
        self.schedule_for_days = {
            "Понедельник": None if mon is None else list(mon),
            "Вторник": None if tue is None else list(tue),
            "Среда": None if wed is None else list(wed),
            "Четверг": None if thu is None else list(thu),
            "Пятница": None if fri is None else list(fri),
            "Суббота": None if sat is None else list(sat),
            "Воскресенье": None if sun is None else list(sun)
        }
        for day in self.schedule_for_days:
            if self.schedule_for_days[day] is None:
                self.schedule_for_days[day] = [False] * 6
            while len(self.schedule_for_days[day]) < 6:
                self.schedule_for_days[day].append(False)

    @staticmethod
    def get_pair_number(pair_time: PairTime) -> int | None:
        # Get number from teachers_schedule_time
        for number, (start, end) in teachers_schedule_time.items():
            # print(f"{start} <= {pair_time} <= {end}: {pair_time.start <= end and pair_time.end >= start}")
            # Check if the pair_time overlaps with the scheduled time
            if pair_time.start <= end and pair_time.end >= start:  # M
                return number
        return None

    def take_pair(self, day: str, pair_number: int) -> None:
        self.schedule_for_days[day][pair_number - 1] = False

    def free_pair(self, day: str, pair_number: int) -> None:
        self.schedule_for_days[day][pair_number - 1] = True

    def choose_pair(self, day: str, pair_time: PairTime):
        pair_number = self.get_pair_number(pair_time)
        if pair_number is None:
            raise ValueError(f"Невозможно выбрать время '{pair_time}'")
        if not self.schedule_for_days[day][pair_number - 1]:
            raise ValueError(f"Время '{pair_time}' занято или недоступно")
        self.take_pair(day, pair_number)

    def __repr__(self):
        str_list = []
        for day in self.schedule_for_days:
            s = f"{day[:2]}:"
            for b in self.schedule_for_days[day]:
                s += "X" if b else "O"
            str_list.append(s)
        return "["+", ".join(str_list)+"]"


class RoomSchedule:
    """
    False - Аудитория свободна
    True - Аудитория занята или пару нельзя поставить на это время
    """
    def __init__(self,
                 mon: list[bool] = None,
                 tue: list[bool] = None,
                 wed: list[bool] = None,
                 thu: list[bool] = None,
                 fri: list[bool] = None,
                 sat: list[bool] = None,
                 sun: list[bool] = None):
        self.schedule_for_days = {
            "Понедельник": None if mon is None else list(mon),
            "Вторник": None if tue is None else list(tue),
            "Среда": None if wed is None else list(wed),
            "Четверг": None if thu is None else list(thu),
            "Пятница": None if fri is None else list(fri),
            "Суббота": None if sat is None else list(sat),
            "Воскресенье": None if sun is None else list(sun)
        }
        for day in self.schedule_for_days:
            if self.schedule_for_days[day] is None:
                self.schedule_for_days[day] = [False] * 6
            while len(self.schedule_for_days[day]) < 6:
                self.schedule_for_days[day].append(False)

    @staticmethod
    def get_pair_number(pair_time: PairTime) -> int | None:
        for number, (start, end) in teachers_schedule_time.items():
            if pair_time.start <= end and pair_time.end >= start:
                return number
        return None

    def __repr__(self):
        return str(self.schedule_for_days)


class Room:
    def __init__(self, is_online: bool = False) -> None:
        self.is_online = is_online

# endregion


# region Constants


offline_str = "Офлайн"
online_str = "Онлайн"


db_file = "db.pickle"
db_path_name = "SchPyPickleData"

days = ("Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье")
workweek_days = ("Понедельник", "Вторник", "Среда", "Четверг", "Пятница")

# CONST
teachers_schedule_time = {
    1: (time(8, 0), time(9, 30)),  # first pair for 1 shift, online for 2 shift
    2: (time(9, 40), time(11, 10)),  # second pair for 1 shift
    3: (time(11, 30), time(13, 0)),  # first pair for 2 shift, online for 3 shift
    4: (time(13, 10), time(14, 40)),  # second pair for 2 shift
    5: (time(15, 0), time(16, 30)),  # first pair for 3 shift
    6: (time(16, 40), time(18, 10))  # second pair for 3 shift, online for 1 shift
}

# endregion


# region Data


class Data(ABC):
    @abstractmethod
    def __init__(self):
        raise NotImplementedError

    counter: int
    days: list = days
    teachers_schedule_time: dict = teachers_schedule_time
    schedule_time_shift_1: dict[int, PairTime]
    schedule_time_shift_2: dict[int, PairTime]
    schedule_time_shift_3: dict[int, PairTime]
    groups_shift: dict[str, dict[int, PairTime]]
    discipline_hours: dict[str, dict[str, int]]
    teachers: dict[str, list[Teacher]]
    teachers_work_hours: dict[str, TeachersSchedule]
    rooms: dict[str, Room]
    rooms_availability_hours: dict[str, RoomSchedule]


class EmptyData(Data):
    def __init__(self):
        self.counter = 1
        self.days = days
        self.teachers_schedule_time = teachers_schedule_time
        self.schedule_time_shift_1 = {}
        self.schedule_time_shift_2 = {}
        self.schedule_time_shift_3 = {}
        self.groups_shift = {}
        self.discipline_hours = {}
        self.teachers = {}
        self.teachers_work_hours = {}
        self.rooms = {}
        self.rooms_availability_hours = {}


class ExampleData(Data):
    def __init__(self):
        self.counter = 1

        self.days = days

        self.teachers_schedule_time = teachers_schedule_time

        self.schedule_time_shift_1 = {  # time schedule for first shift
            1: PairTime(time(8, 0), time(9, 30), offline_str),
            2: PairTime(time(9, 40), time(11, 10), offline_str),
            3: PairTime(time(16, 40), time(17, 40), online_str),
        }

        self.schedule_time_shift_2 = {  # time schedule for second shift
            1: PairTime(time(8, 0), time(9, 0), online_str),
            2: PairTime(time(11, 30), time(13, 0), offline_str),
            3: PairTime(time(13, 10), time(14, 40), offline_str),
        }

        self.schedule_time_shift_3 = {  # time schedule for third shift
            1: PairTime(time(11, 50), time(12, 50), online_str),
            2: PairTime(time(15, 0), time(16, 30), offline_str),
            3: PairTime(time(16, 40), time(18, 10), offline_str),
        }

        self.groups_shift = {
            "П9024": self.schedule_time_shift_1,
            "П9022": self.schedule_time_shift_2,
            "П9021": self.schedule_time_shift_3,
        }

        self.discipline_hours = {  # on current week
            "П9024": {
                "Литература": 2,
                "Физика": 0,
                "Иностранный язык": 2,
                "Математика": 4,
                "Физическая культура": 2,
                "Основы безопасности жизнедеятельности": 0,
                "Информатика": 2,
                "География": 4,
                "Биология": 2,
                "Химия": 0,
                "Русский язык": 2,
                "Обществознание": 4,
                "История": 2,
                "Индивидуальный проект": 0,
                "Право": 2,
            },
            "П9022": {
                "Литература": 2,
                "Физика": 0,
                "Иностранный язык": 2,
                "Математика": 4,
                "Физическая культура": 2,
                "Основы безопасности жизнедеятельности": 0,
                "Информатика": 2,
                "География": 4,
                "Биология": 2,
                "Химия": 0,
                "Русский язык": 2,
                "Обществознание": 4,
                "История": 2,
                "Индивидуальный проект": 0,
                "Право": 2,
            },
            "П9021": {
                "Литература": 2,
                "Физика": 0,
                "Иностранный язык": 2,
                "Математика": 4,
                "Физическая культура": 2,
                "Основы безопасности жизнедеятельности": 0,
                "Информатика": 2,
                "География": 4,
                "Биология": 2,
                "Химия": 0,
                "Русский язык": 2,
                "Обществознание": 4,
                "История": 2,
                "Индивидуальный проект": 0,
                "Право": 2,
            }
        }

        self.teachers = {  # random teachers
            "Дмитриев Д.Д.": [Teacher("Дмитриев Д.Д.", {"Информатика", "Индивидуальный проект"}, {"П9024"})],
            "Александров А.А.": [Teacher("Александров А.А.", {"Математика"}, {"П9024"})],
            "Иванов И.И.": [Teacher("Иванов И.И.", {"Математика", "Физика", "Информатика", "Индивидуальный проект"},
                                   {"П9022", "П9021"})],
            "Петрова П.П.": [Teacher("Петрова П.П.", {"Литература", "Русский язык"}, {"П9022"})],
            "Владимирова В.П.": [Teacher("Владимирова В.П.", {"Литература", "Русский язык"}, {"П9021"})],
            "Данилова Д.Д.": [Teacher("Данилова Д.Д.", {"Литература", "Русский язык"}, {"П9024"})],
            "Сидорова С.С.": [Teacher("Сидорова С.С.", {"География", "Биология", "Химия"}, {"П9022", "П9021", "П9024"})],
            "Кузнецова К.К.": [Teacher("Кузнецова К.К.", {"Обществознание", "История", "Право"}, {"П9021", "П9022", "П9024"})],
            "Васильев В.В.": [Teacher("Васильев В.В.", {"Физическая культура", "Основы безопасности жизнедеятельности"},
                                     {"П9021", "П9022", "П9024"})],
            "Смирнова С.С.": [Teacher("Смирнова С.С.", {"Иностранный язык"}, {"П9024"})],
            "Смирнов В.С.": [Teacher("Смирнов В.С.", {"Иностранный язык"}, {"П9022", "П9021"})],
        }

        self.teachers_work_hours = {  # on current week
            "Дмитриев Д.Д.": TeachersSchedule(
                mon=(True, True, True, True, True, True, True),
                thu=(True, True, True, True, True, True, True),
                fri=(True, True, True, True, True, True, True),
            ),
            "Александров А.А.": TeachersSchedule(
                mon=(True, True, True, True, True, True, True),
                tue=(True, True, True, True, True, True, True),
                wed=(True, True, True, True, True, True, True),
                thu=(True, True, True, True, True, True, True),
                fri=(True, True, True, True, True, True, True),
            ),
            "Иванов И.И.": TeachersSchedule(
                mon=(True, True, True, True, True, True, True),
                wed=(True, True, True, True, True, True, True),
                thu=(True, True, True, True, True, True, True),
                fri=(True, True, True, True, True, True, True),
            ),
            "Петрова П.П.": TeachersSchedule(
                mon=(True, True, True, True, True, True, True),
                tue=(True, True, True, True, True, True, True),
                wed=(True, True, True, True, True, True, True),
            ),
            "Владимирова В.П.": TeachersSchedule(
                mon=(True, True, True, True, True, True, True),
                tue=(True, True, True, True, True, True, True),
            ),
            "Данилова Д.Д.": TeachersSchedule(
                mon=(True, True, True, True, True, True, True),
                tue=(True, True, True, True, True, True, True),
                fri=(True, True, True, True, True, True, True),
            ),
            "Сидорова С.С.": TeachersSchedule(
                mon=(True, True, True, True, True, True, True),
                tue=(True, True, True, True, True, True, True),
                wed=(True, True, True, True, True, True, True),
                thu=(True, True, True, True, True, True, True),
                fri=(True, True, True, True, True, True, True),
            ),
            "Кузнецова К.К.": TeachersSchedule(
                mon=(True, True, True, True, True, True, True),
                wed=(True, True, True, True, True, True, True),
                thu=(True, True, True, True, True, True, True),
                fri=(True, True, True, True, True, True, True),
            ),
            "Васильев В.В.": TeachersSchedule(
                mon=(True, True, True, True, True, True, True),
                thu=(True, True, True, True, True, True, True),
                fri=(True, True, True, True, True, True, True),
            ),
            "Смирнова С.С.": TeachersSchedule(
                wed=(True, True, True, True, True, True, True),
                thu=(True, True, True, True, True, True, True),
                fri=(True, True, True, True, True, True, True),
            ),
            "Смирнов В.С.": TeachersSchedule(
                mon=(True, True, True, True, True, True, True),
                fri=(True, True, True, True, True, True, True),
            )
        }

        self.rooms = {
            "К1": Room(),
            "К2": Room(),
            "К3": Room(),
            "Д1": Room(True),
            "Д2": Room(True),
            "Д3": Room(True),
        }

        self.rooms_availability_hours = {
            "К1": RoomSchedule(),
            "К2": RoomSchedule(),
            "К3": RoomSchedule(),
            "Д1": RoomSchedule(),
            "Д2": RoomSchedule(),
            "Д3": RoomSchedule(),
        }


def save_data(data) -> None:
    db_path = get_data_file_path()
    print(f"Сохранение данных в файл {db_path}")
    data.counter += 1
    with open(db_path, "wb") as f:
        pickle.dump(data, f)


def load_data() -> Data:
    db_path = get_data_file_path()
    print(f"Загрузка данных из файла {db_path}")
    with open(db_path, "rb") as f:
        d: Data = pickle.load(f)
        for k, v in d.teachers.items():
            if isinstance(v, Teacher):
                d.teachers[k] = [v]
        return d


def check_exists_data() -> bool:
    db_path = get_data_file_path()
    return os.path.exists(db_path)


def resource_path(relative_path):
    base_path = getattr(
        sys,
        '_MEIPASS',
        os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def get_data_file_path():
    base_path = Path(os.path.expanduser("~")) / db_path_name
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path / db_file

# endregion
