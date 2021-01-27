# Filter Menu classes

import logging
from app.constants import WEEKDAYS
from app.bot.telegram.menu.menu import Menu
from app.bot.telegram.filters import Filter


class FilterDayMenu(Menu):
    def __init__(self, chain_name: str, display_name: str):
        super().__init__(chain_name, display_name, [])

    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}')

        self.init_filters(message)

        self.children.clear()
        # 1. create filter day of week
        for wd in range(7):
            m_filter_day = Menu(self.chain_name, f'{str(WEEKDAYS(wd).name).capitalize()}', [])
            m_filter_day.parent = self
            # append m_day as a child to Show available slots menu
            self.children.append(m_filter_day)
            m_filter_day.register(self.bot)

            # 2. create slots for the day of the week
            for st in range(7, 22):
                wd_filters = getattr(Filter.chat_filters[message.chat_id][self.chain_name], WEEKDAYS(wd).name)
                slot_name = "{:02d}:00-{:02d}:00".format(st, st+1)
                if slot_name in wd_filters:
                    slot_prefix = '[✓]'
                else:
                    slot_prefix = '[  ]'
                m_filter_slot = FilterTimeMenu(self.chain_name, "{} {}".format(slot_prefix, slot_name))
                m_filter_slot.parent = self.children[-1]
                # append m_slot as a child to m_day menu
                self.children[-1].children.append(m_filter_slot)
                m_filter_slot.register(self.bot)

        # 3. adding text
        message.edit_text(self.display_name, reply_markup=self._keyboard(self.children))

    def init_filters(self, message):
        if message.chat_id not in Filter.chat_filters or self.chain_name not in Filter.chat_filters[message.chat_id]:
            Filter.chat_filters[message.chat_id] = {self.chain_name: Filter(message.chat_id, self.chain_name)}


class FilterTimeMenu(Menu):
    def __init__(self, chain_name: str, display_name: str):
        super().__init__(chain_name, display_name, [])

    def display(self, message):
        wd = self.parent.display_name.lower()
        wd_filters = getattr(Filter.chat_filters[message.chat_id][self.chain_name], wd)
        if self.display_name.startswith('[✓]'):
            # remove
            wd_filters.remove(self.display_name[4:])
            self.display_name = self.display_name.replace('[✓]', '[  ]')
        else:
            # add
            wd_filters.append(self.display_name[5:])
            self.display_name = self.display_name.replace('[  ]', '[✓]')
        setattr(Filter.chat_filters[message.chat_id][self.chain_name], wd, wd_filters)
        self.parent.display(message)
