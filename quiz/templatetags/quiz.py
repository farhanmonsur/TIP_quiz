from django import template
from quiz import models
from quiz.models import UserQuestionAnswer
import logging

logger = logging.getLogger(__name__)


register = template.Library()


@register.filter
def user_quiz(user, quiz):
    return models.UserQuiz.objects.filter(
        user=user, quiz=quiz
    ).exists()


@register.filter
# def user_quiz_completed(user, quiz):
#     user_quiz = models.UserQuestionAnswer.objects.filter(
#         user_quiz__user=user
#     )
#     return user_quiz.count() == quiz.question_set.all().count()
def user_quiz_completed(user, quiz):
    # Get the user quiz for the given user and quiz
    user_quiz = quiz.userquiz_set.filter(user=user).first()

    if not user_quiz:
        return False

    # Count how many questions the user has answered
    answered_questions = UserQuestionAnswer.objects.filter(user_quiz=user_quiz).count()

    # Compare it with the total number of questions in the quiz
    total_questions = quiz.question_set.count()
    logger.debug(f"\nUser: {user}, Quiz: {quiz.title}, Answered: {answered_questions}, Total: {total_questions}\n")

    # Return True if all questions are answered
    return answered_questions == total_questions



@register.filter
# def quiz_user_score(user, quiz):
#     return models.UserQuestionAnswer.objects.filter(
#         user_quiz__quiz=quiz, answer__answer=True
#     ).count()

def quiz_user_score(user, quiz):
    # Get the user quiz for the given user and quiz
    user_quiz = quiz.userquiz_set.filter(user=user).first()

    if not user_quiz:
        return 0

    # Count the number of correct answers
    correct_answers = UserQuestionAnswer.objects.filter(
        user_quiz=user_quiz, answer__answer=True
    ).count()

    return correct_answers
