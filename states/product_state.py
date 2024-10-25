from aiogram.dispatcher.filters.state import StatesGroup, State


class CategoryState(StatesGroup):
    title = State()
    add_category = State()
    rename_category = State()

class RazdelState(StatesGroup):
    title= State()
    rename_razdel = State()


class ProductState(StatesGroup):
    title = State()
    body = State()
    image = State()
    files = State()
    price = State()
    confirm = State()

