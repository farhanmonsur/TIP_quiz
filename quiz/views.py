from django.views.generic import TemplateView, DetailView
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils import timezone
import logging
from quiz import models
logger = logging.getLogger(__name__)


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

class LevelQuizView(TemplateView):
    template_name = "quiz/level_quizzes.html"

    def get_context_data(self, **kwargs):
        # Get the context from the base implementation
        context = super().get_context_data(**kwargs)
        
        # Retrieve the level object based on the slug in the URL
        level = get_object_or_404(models.Level, slug=self.kwargs['slug'])
        
        # Get all quizzes that belong to this level
        quizzes = models.Quiz.objects.filter(level=level)
        
        # Pass the level and quizzes to the context
        context['level'] = level
        context['quizzes'] = quizzes
        context['title'] = f"Quizzes for Level: {level.name}"
        
        return context

class QuizView(QuizMixin, TemplateView):
    template_name = "quiz/quiz.html"
    extra_context = {'title': "Quizzes"}

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data()
        kwargs['quiz_list'] = self.get_queryset()
        kwargs['levels'] = models.Level.objects.all()

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
        self.user_question_ans_ids = self.user_quiz.userquestionanswer_set.values_list('question__id', flat=True)
        logger.debug(f"Answered questions: {self.user_question_ans_ids}")
        question = self.quiz.question_set.exclude(id__in=self.user_question_ans_ids).order_by('?').first()
        if question:
            logger.debug(f"Next question: {question.question}")
        else:
            logger.debug("No more questions available!")

        return question

    def dispatch(self, request, *args, **kwargs):
        self.quiz = self.get_quiz()
        self.user_quiz = self.get_user_quiz(quiz=self.quiz)
        logger.debug(f"Dispatch - User: {request.user}, Quiz: {self.quiz.title}, UserQuiz: {self.user_quiz}")

        if not self.user_quiz:
            logger.debug(f"Redirection - User: {request.user} has no existing UserQuiz for quiz: {self.quiz.title}. Redirecting to quiz detail.")
            return redirect('quiz:quiz_detail', self.kwargs['slug'])
        self.question = self.get_question()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        logger.debug(f"\nHandling GET request for user: {request.user}, Quiz: {self.quiz.title}\n")
        if self.user_quiz.completed(request.user, self.quiz):
            logger.debug(f"Completed get - User: {request.user} has completed the quiz: {self.quiz.title}. Redirecting to quiz completion page.")
            return redirect('quiz:quiz_complete', self.kwargs['slug'])
        if not self.question:
            logger.debug(f"No more questions available for user: {request.user} in quiz: {self.quiz.title}")
            self.extra_context["message"] = "Question not available now"
        else:
            logger.debug(f"Creating UserQuestionAnswer for user: {request.user}, Question: {self.question.question}")
            models.UserQuestionAnswer.objects.create(
                user_quiz=self.user_quiz, question=self.question,
            )

            question_options = self.question.questionoptions_set.all()  # Fetch all options for this question
            logger.debug(f"Generating question options: {request.user}, options: {question_options}")

            options_data = [{'option_text': option.option, 'is_answer': option.answer} for option in question_options]
            correct_option = next((opt for opt in options_data if opt['is_answer']), None)

            if correct_option:
                logger.debug(f"Correct answer is: {correct_option['option_text']}")
                self.extra_context['correct_option_text'] = correct_option['option_text'] 

            # Add the formatted options data to the extra context
            self.extra_context['question_options'] = options_data

            logger.debug(f"Options data: {options_data}")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['object'] = self.question
        kwargs['title'] = self.question.question
        kwargs['question_options'] = self.extra_context.get('question_options', [])  # Include the formatted options in the context
        kwargs['correct_option_text'] = self.extra_context.get('correct_option_text', '')  # Pass correct answer to the context

        return kwargs

    def post(self, request, *args, **kwargs):
        data = request.POST
        logger.debug(f"\nPost - User: {request.user} submitting answer for quiz: {self.quiz.title}, Data: {data}\n")

        user_answer = get_object_or_404(
            models.UserQuestionAnswer,
            user_quiz=self.user_quiz,
            question=self.quiz.question_set.get(id=data['question']),
        )
        logger.debug(f"Saving answer for user: {request.user}, Question: {user_answer.question}, Answer: {data['answer']}")
        #asdfdsafasdfasdf
        user_answer.answer_id = data['answer']
        user_answer.save()

        is_correct  = user_answer.answer.answer
        self.extra_context['correct_answer'] = is_correct

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
