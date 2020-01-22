from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField

from webapp.config import depth_limits, intervals, traiding_pairs


class ChartForm(FlaskForm):
    interval = SelectField(
        label="Интервал свечи",
        choices=list(intervals.keys()),
        default=list(intervals.keys())[2],
        description="Интервал свечи")
    pair = SelectField(
        label="Торговый инструмент",
        choices=traiding_pairs,
        default=traiding_pairs[0],
        description="Торговый инструмент")
    depth = SelectField(
        label="Глубина истории",
        choices=depth_limits,
        default=depth_limits[-3],
        description="Глубина истории")
    submit = SubmitField('Get Chart')
