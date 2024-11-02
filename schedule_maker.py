import db
import copy
from dataclasses import dataclass


class ScheduleError(ValueError):
    def __init__(self, message: str, discipline=None, group=None, hours=None):
        super().__init__(message)
        self.discipline = discipline
        self.group = group
        self.hours = hours


@dataclass
class Schedule:
    pairs: dict[str, list[db.Pair]]
    errors: list[ScheduleError]
    remaining_data: db.Data


def print_schedule(schedule: dict[str, list[db.Pair]]) -> None:
    for group in schedule:
        print(group)
        for pair in schedule[group]:
            print(pair)


def print_errors(errors_list: list[ScheduleError]) -> None:
    for error in errors_list:
        print(f"Невозможно поставить пару для группы {error.group}, для дисциплины {error.discipline}, оставшиеся часы: {error.hours}")


def choose_a_pair_time(
        existing_pairs: list[db.Pair],
        discipline: str,
        group: str,
        teacher: db.Teacher,
        data: db.Data) -> db.Pair:
    shift = data.groups_shift[group]
    teachers_schedule = data.teachers_work_hours[teacher.name]

    # Ищем первое свободное время для дисциплины
    for day in db.days:
        for number, pair_time in shift.items():
            if number in [pair.number for pair in existing_pairs if pair.day == day]: continue
            try:
                teachers_schedule.choose_pair(day, pair_time)
            except ValueError:
                continue
            # Создаем объект пары
            pair = db.Pair(
                date="2024-XX-XX",  # Пример даты, можно сделать динамическим
                day=day,
                number=number,
                pair_time=pair_time,
                pair_type=pair_time.pair_type,
                group=group,
                discipline=discipline,
                teacher=teacher.name,
                classroom=None
            )
            return pair  # Возвращаем объект пары
    raise ScheduleError(
        f"Невозможно найти свободное время",
        discipline=discipline,
        group=group
    )


def distribute_pairs(data: db.Data) -> tuple[dict[str, list[db.Pair]], list[ScheduleError]]:
    full_schedule = {}  # Словарь для хранения расписания по группам
    errors = []
    remaining_hours = data.discipline_hours

    for group in data.groups_shift.keys():
        full_schedule[group] = []  # Инициализируем список для каждой группы
        # Итерируемся по дисциплинам
        for discipline in remaining_hours[group]:  # M получаем недельные часы по дисциплине.
            # Ищем подходящего преподавателя для дисциплины
            if remaining_hours[group][discipline] == 0:  # M
                continue
            for teacher in data.teachers.values():  # M у каждого преподавателя есть группы за которые он отвечает и дисциплины
                if not (discipline in teacher.disciplines and group in teacher.groups): continue
                try:
                    while remaining_hours[group][discipline] > 0:
                        pair = choose_a_pair_time(full_schedule[group], discipline, group, teacher, data)
                        full_schedule[group].append(pair)  # Добавляем пару в расписание
                        remaining_hours[group][discipline] -= 2
                except ScheduleError as e:
                    e.hours = remaining_hours[group][discipline]
                    errors.append(e)
                break  # Прерываем поиск после нахождения первого подходящего преподавателя
    return full_schedule, errors  # Возвращаем полное расписание


def distribute_classrooms(raw_sch: dict, data: db.Data) -> dict[str, list[db.Pair]]:
    raw_sch = raw_sch.copy()
    available_rooms: dict[str, db.RoomSchedule] = data.rooms_availability_hours
    for group, list_of_pairs in raw_sch.items():
        for pair in list_of_pairs:
            if pair.classroom is not None: continue
            if pair.pair_type == "Онлайн":  # Если онлайн
                _available_rooms_list = [(room, sc) for room, sc in available_rooms.items() if room.startswith("Д")]
            else:
                _available_rooms_list = [(room, sc) for room, sc in available_rooms.items() if room.startswith("К")]
            for room, room_schedule in _available_rooms_list:
                if not room_schedule.schedule_for_days[pair.day][room_schedule.get_pair_number(pair.pair_time)-1]:
                    # Если пара свободна
                    pair.classroom = room
                    room_schedule.schedule_for_days[pair.day][room_schedule.get_pair_number(pair.pair_time)-1] = True
                    break
    return raw_sch


def make_full_schedule(data: db.Data) -> Schedule:
    data = copy.deepcopy(data)
    full_schedule, errors = distribute_pairs(data)
    full_schedule = distribute_classrooms(full_schedule, data)
    for group in full_schedule:
        full_schedule[group] = sorted(full_schedule[group], key=lambda p: db.days.index(p.day))
    return Schedule(pairs=full_schedule, errors=errors, remaining_data=data)


if __name__ == "__main__":
    d = db.get_data()
    full_sch, errs = make_full_schedule(d)
    print_schedule(full_sch)
    print_errors(errs)
