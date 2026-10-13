from aiogram.fsm.state import State, StatesGroup


class SweetReply(StatesGroup):
    waiting_message = State()
    waiting_style = State()
    done = State()


class Videos(StatesGroup):
    waiting_target = State()
    done = State()


class CouplePhotos(StatesGroup):
    waiting_choice = State()
    waiting_description = State()
    done = State()


class DatePlan(StatesGroup):
    waiting_budget = State()
    waiting_custom_budget = State()
    waiting_format = State()
    done = State()


class Travel(StatesGroup):
    waiting_destination_type = State()
    waiting_destination = State()
    waiting_transport = State()
    waiting_car_consumption = State()
    waiting_car_fuel_price = State()
    done = State()


class Compliments(StatesGroup):
    waiting_target = State()
    waiting_style = State()
    done = State()


class Situation(StatesGroup):
    waiting_description = State()
    waiting_goal = State()
    done = State()


class Wish(StatesGroup):
    waiting_description = State()
    done = State()


class Diy(StatesGroup):
    waiting_details = State()
    done = State()


class Flowers(StatesGroup):
    waiting_recipient = State()
    waiting_loved_flowers = State()
    waiting_colors = State()
    waiting_reason = State()
    waiting_budget = State()
    done = State()


class Poems(StatesGroup):
    waiting_description = State()
    done = State()

