import db


def show_schedule(schedule: dict[str, list[db.Pair]]):
    for group in schedule:
        print(group)
        for pair in schedule[group]:
            print(pair)


def make_schedule(existing_pairs: list[db.Pair], discipline: str, group: str, teacher: db.Teacher) -> db.Pair:
    shift = db.groups_shift[group]
    teachers_schedule = db.teachers_work_hours[teacher.name]

    # Ищем первое свободное время для дисциплины
    for day in db.days:
        for number, pair_time in shift.items():
            if number in [pair.number for pair in existing_pairs if pair.day == day]: continue
            try:
                teachers_schedule.choose_pair(day, pair_time)
            except ValueError as e:
                # print(e)
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
    raise ValueError(f"Невозможно найти свободное время")


def make_full_schedule() -> dict:
    full_schedule = {}  # Словарь для хранения расписания по группам

    for group in db.groups_shift.keys():
        full_schedule[group] = []  # Инициализируем список для каждой группы
        # Итерируемся по дисциплинам
        for discipline in db.discipline_hours[group]:  # M получаем недельные часы по дисцип.
            # Ищем подходящего преподавателя для дисциплины
            if db.discipline_hours[group][discipline] == 0:  # M
                continue
            for teacher in db.teachers.values():  # M у каждого препода есть группы за которые он отвечает и дисциплины
                if not (discipline in teacher.disciplines and group in teacher.groups): continue
                try:
                    while db.discipline_hours[group][discipline] > 0:
                        # chosen_schedule_time = [pr.pair_time for pr in full_schedule[group]]
                        pair = make_schedule(full_schedule[group], discipline, group, teacher)
                        full_schedule[group].append(pair)  # Добавляем пару в расписание
                        db.discipline_hours[group][discipline] -= 2
                except ValueError as e:
                    print(f"Ошибка при составлении расписания для группы '{group}' и дисциплины '{discipline}': {e}")
                break  # Прерываем поиск после нахождения первого подходящего преподавателя
    return full_schedule  # Возвращаем полное расписание


def distribute_classrooms(raw_sch: dict):
    available_rooms: dict[str, db.RoomSchedule] = db.rooms_availability_hours
    for group, list_of_pairs in raw_sch.items():
        for pair in list_of_pairs:
            if pair.classroom is not None: continue
            if pair.pair_type == "Онлайн":  # Если онлайн
                _available_rooms_list = [(room, sc) for room, sc in available_rooms.items() if room.startswith("Д")]
            else:
                _available_rooms_list = [(room, sc) for room, sc in available_rooms.items() if room.startswith("К")]
            # random.shuffle(_available_rooms_list)  # TODO: Стереть эту строку
            for room, room_schedule in _available_rooms_list:
                if not room_schedule.schedule_for_days[pair.day][room_schedule.get_pair_number(pair.pair_time)-1]:
                    # Если пара свободна
                    pair.classroom = room
                    room_schedule.schedule_for_days[pair.day][room_schedule.get_pair_number(pair.pair_time)-1] = True
                    break


if __name__ == "__main__":
    raw_schedule = make_full_schedule()
    distribute_classrooms(raw_schedule)
    for g, pairs in raw_schedule.items():
        print(f"Расписание для группы {g}:")
        for p in sorted(pairs, key=lambda pair: db.days.index(pair.day)):
            print(p)
