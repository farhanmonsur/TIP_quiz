from django import template
from quiz import models


register = template.Library()


@register.filter
def user_quiz(user, quiz):
    return models.UserQuiz.objects.filter(
        user=user, quiz=quiz
    ).exists()


@register.filter
def user_quiz_completed(user, quiz):
    user_quiz = models.UserQuestionAnswer.objects.filter(
        user_quiz__user=user
    )
    return user_quiz.count() == quiz.question_set.all().count()


@register.filter
def quiz_user_score(user, quiz):
    return models.UserQuestionAnswer.objects.filter(
        user_quiz__quiz=quiz, answer__answer=True
    ).count()
