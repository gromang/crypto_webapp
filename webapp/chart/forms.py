from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField

from webapp.config import depth_limits, intervals, traiding_pairs


def to_tuple(data):
    tuple_list = []
    if type(data) == list:
        for k in data:
            k = str(k)
            tuple_list.append((k, k))
    elif type(data) == dict:
        for k in data.keys():
            tuple_list.append((k, k))
    return tuple_list


interval_choice = to_tuple(intervals)
pair_choice = to_tuple(traiding_pairs)
depth_choice = to_tuple(depth_limits)


class ChartForm(FlaskForm):
    interval = SelectField(
        label="Интервал свечи",
        choices=interval_choice,
        default=interval_choice[2][0],
        description="Интервал свечи")
    pair = SelectField(
        label="Торговый инструмент",
        choices=pair_choice,
        default=pair_choice[0][0],
        description="Торговый инструмент")
    depth = SelectField(
        label="Глубина истории",
        choices=depth_choice,
        default=depth_choice[-3][0],
        description="Глубина истории")
    submit = SubmitField('Get Chart')
