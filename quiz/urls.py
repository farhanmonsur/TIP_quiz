from django.urls import path
from . import views

app_name = "quiz"

urlpatterns = [
    path('', views.IndexView.as_view(), name="index"),
    path('level/<slug:slug>/', views.LevelQuizView.as_view(), name='level_quizzes'),
    path('quizzes/', views.QuizView.as_view(), name="quizzes"),
    path('quiz/<slug:slug>/', views.QuizDetail.as_view(), name="quiz_detail"),
    path(
        'quiz/<slug:slug>/question/',
        views.QuestionAnswer.as_view(),
        name="quiz_question"
    ),
    path(
        'quiz/<slug:slug>/complete/',
        views.QuizCompleteView.as_view(),
        name="quiz_complete"
    ),
    path(
        'user/quizzes/',
        views.UserQuizList.as_view(),
        name="user_quizzes"
    ),
]
