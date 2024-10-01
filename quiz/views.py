from django.views.generic import TemplateView, DetailView
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils import timezone

from quiz import models


class QuizMixin:
    def get_queryset(self):
        return models.Quiz.objects.filter(
            users=self.request.user, published=True,
            end_date__gte=timezone.now()
        ).order_by('end_date')

    def get_quiz(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, slug=self.kwargs['slug'])

    def get_user_quizzes(self, queryset=None):
        if not queryset:
            queryset = models.UserQuiz.objects.filter(user=self.request.user)
        return queryset

    def get_user_quiz(self, queryset=None, quiz=None):
        if not queryset:
            queryset = self.get_user_quizzes()
        return get_object_or_404(queryset, quiz=quiz)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class IndexView(TemplateView):
    template_name = "quiz/index.html"
    extra_context = {'title': "Home"}


class QuizView(QuizMixin, TemplateView):
    template_name = "quiz/quiz.html"
    extra_context = {'title': "Quizzes"}

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data()
        kwargs['quiz_list'] = self.get_queryset()
        return kwargs


class QuizDetail(QuizMixin, DetailView):
    template_name = "quiz/quiz_detail.html"

    def get_object(self, queryset=None):
        return self.quiz

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data()
        kwargs['title'] = self.quiz.title
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.quiz = self.get_quiz()
        self.user_quiz = models.UserQuiz.objects.filter(
            user=request.user, quiz=self.quiz)
        if self.user_quiz.exists():
            return redirect('quiz:quiz_question', self.kwargs['slug'])
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        models.UserQuiz.objects.create(user=request.user, quiz=self.quiz)
        return redirect('quiz:quiz_question', self.kwargs['slug'])


class QuestionAnswer(QuizMixin, TemplateView):
    template_name = "quiz/quiz_question.html"
    extra_context = {}

    def get_question(self):
        self.user_question_ans_ids = self.user_quiz.userquestionanswer_set. \
            values_list('question__id', flat=True)
        return self.quiz.question_set.exclude(
            id__in=self.user_question_ans_ids,
        ).order_by('?').first()

    def dispatch(self, request, *args, **kwargs):
        self.quiz = self.get_quiz()
        self.user_quiz = self.get_user_quiz(quiz=self.quiz)
        if not self.user_quiz:
            return redirect('quiz:quiz_detail', self.kwargs['slug'])
        self.question = self.get_question()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.user_quiz.completed(request.user, self.quiz):
            return redirect('quiz:quiz_complete', self.kwargs['slug'])
        if not self.question:
            self.extra_context["message"] = "Question not available now"
        else:
            models.UserQuestionAnswer.objects.create(
                user_quiz=self.user_quiz, question=self.question,
            )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['object'] = self.question
        kwargs['title'] = self.question.question
        return kwargs

    def post(self, request, *args, **kwargs):
        data = request.POST
        user_answer = get_object_or_404(
            models.UserQuestionAnswer,
            user_quiz=self.user_quiz,
            question=self.quiz.question_set.get(id=data['question']),
        )
        user_answer.answer_id = data['answer']
        user_answer.save()
        if data.get('pause'):
            return redirect('quiz:user_quizzes')
        return self.get(request, *args, **kwargs)


class QuizCompleteView(QuizMixin, TemplateView):
    template_name = "quiz/quiz_complete.html"
    extra_context = {'title': "Quiz Complete"}

    def dispatch(self, request, *args, **kwargs):
        self.quiz = self.get_quiz()
        self.user_quiz = self.get_user_quiz(quiz=self.quiz)
        if not self.user_quiz.completed(request.user, self.quiz):
            return redirect('quiz:quiz_question', self.kwargs['slug'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['object'] = self.get_user_quiz(quiz=self.quiz)
        return kwargs


class UserQuizList(QuizMixin, TemplateView):
    template_name = "quiz/user_quiz.html"
    extra_context = {'title': "User Quizzes"}

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['quiz_list'] = self.get_user_quizzes()
        return kwargs
