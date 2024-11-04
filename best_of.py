import schedule_maker
import db
import copy
import random

teachers_gaps_rating_modifier = 5
offline_pairs_gaps_rating_modifier = 20


def shuffled_dict(x: dict) -> dict:
    items = list(x.items())
    random.shuffle(items)
    return dict(items)


def shuffled_tuple(x: tuple) -> tuple:
    random.shuffle(copy.deepcopy(list(x)))
    return tuple(x)


def shuffle_data(data_obj: db.Data, seed: int) -> db.Data:
    random.seed(seed)
    data_obj = copy.deepcopy(data_obj)

    data_obj.days = shuffled_tuple(data_obj.days)
    data_obj.teachers = shuffled_dict(data_obj.teachers)
    data_obj.teachers_work_hours = shuffled_dict(data_obj.teachers_work_hours)
    data_obj.rooms = shuffled_dict(data_obj.rooms)
    data_obj.rooms_availability_hours = shuffled_dict(data_obj.rooms_availability_hours)
    for group in data_obj.discipline_hours:
        data_obj.discipline_hours[group] = shuffled_dict(data_obj.discipline_hours[group])
    data_obj.discipline_hours = shuffled_dict(data_obj.discipline_hours)
    data_obj.groups_shift = shuffled_dict(data_obj.groups_shift)
    return data_obj


def count_teachers_gaps(original_data: db.Data, remaining_data: db.Data) -> int:
    count = 0
    for teacher, teachers_schedule in original_data.teachers_work_hours.items():
        for day in teachers_schedule.schedule_for_days:
            chosen_pairs = []
            first = remaining_data.teachers_work_hours[teacher].schedule_for_days[day]
            second = teachers_schedule.schedule_for_days[day]
            for n, (b1, b2) in enumerate(zip(first, second)):
                if not b1 and b2:
                    chosen_pairs.append(n)
            if not chosen_pairs: continue
            for i in range(min(chosen_pairs), max(chosen_pairs) + 1):
                if i not in chosen_pairs:
                    count += 1
    return count


def count_offline_pairs_gaps(pairs: dict[str, list[db.Pair]], data_obj: db.Data) -> int:
    count = 0
    for group, list_of_pairs in pairs.items():
        offline_pair_numbers = [number for number, pair_time in data_obj.groups_shift[group].items() if
                                pair_time.pair_type == db.offline_str]
        for day in db.workweek_days:
            offline_pair_numbers_for_day = [pair.number for pair in list_of_pairs if pair.day == day and pair.number in offline_pair_numbers]
            if len(offline_pair_numbers_for_day) != len(offline_pair_numbers):
                count += len(offline_pair_numbers) - len(offline_pair_numbers_for_day)
    return count


def sub_percentage(x: float, percentage: float) -> float:
    return x - (x * percentage / 100)


def rate_schedule(schedule: dict[str, list[db.Pair]], original_data: db.Data, remaining_data: db.Data) -> float:
    rate = 100
    teachers_gaps_count = count_teachers_gaps(original_data, remaining_data)
    rate = sub_percentage(rate, teachers_gaps_count * teachers_gaps_rating_modifier)

    offline_pairs_gaps = count_offline_pairs_gaps(schedule, original_data)

    rate = sub_percentage(rate, offline_pairs_gaps * offline_pairs_gaps_rating_modifier)
    return rate


def get_top(seeds_rating_dict: dict, count: int) -> dict:
    seeds_rating_dict = {k: v for k, v in sorted(seeds_rating_dict.items(), key=lambda item: item[1])}
    if len(seeds_rating_dict) < count:
        return seeds_rating_dict
    return dict(list(seeds_rating_dict.items())[-count:])


if __name__ == "__main__":
    data = db.ExampleData()
    data.groups_shift = {
        list(data.groups_shift.keys())[0]: data.groups_shift[list(data.groups_shift.keys())[0]]
    }

    seeds_rating = {}

    for seed in range(100):
        data = shuffle_data(data, seed)
        schedule_obj = schedule_maker.make_full_schedule(data)
        gaps = rate_schedule(schedule_obj.pairs, data, schedule_obj.remaining_data)
        seeds_rating[seed] = gaps

    print(f"Top 10 seeds:\n{"\n".join([f"{k}:\t{v}" for k, v in get_top(seeds_rating, 10).items()])}")
    best_seed = max(seeds_rating, key=seeds_rating.get)
    schedule_obj = schedule_maker.make_full_schedule(shuffle_data(data, best_seed))
    print(f"Best schedule (seed {best_seed}):")
    schedule_maker.print_schedule(schedule_obj.pairs)

