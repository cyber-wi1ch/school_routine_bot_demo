from vkbottle import BaseStateGroup


class States(BaseStateGroup):
    # name registration state
    ASK_FULL_NAME = 1
    # admin states
    ADMIN_ADD_LATE_CATCHER = 2
    ADMIN_REMOVE_LATE_CATCHER = 3
    # morning duty states
    MORNING_DUTY_CHOOSE_BUILDING = 4
    MORNING_DUTY_WAIT_SURNAME = 5
    MORNING_DUTY_CHOOSE_STUDENT = 6
    MORNING_DUTY_WAIT_REASON = 7
