from django.views.generic import TemplateView, DetailView
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core import serializers
import logging
from quiz import models
import json

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
            queryset = models.UserQuiz.objects.filter(user=self.request.user, quiz__published=True)  
        return queryset

    def get_user_quiz(self, queryset=None, quiz=None):
        if not queryset:
            queryset = self.get_user_quizzes()
        return get_object_or_404(queryset, quiz=quiz)
    
    def get_all_user_quizzes(self, queryset=None):
        if not queryset:
            queryset = models.UserQuiz.objects.all()  
        return queryset
    
    def get_all_user_scores(self, queryset=None):
        if not queryset:
            queryset = models.UserScore.objects.all()  
        return queryset

    def get_all_rewards(self, queryset=None):
        if not queryset:
            queryset = models.Reward.objects.all()  
        return queryset
    
    def get_all_user_rewards(self, queryset=None):
        if not queryset:
            queryset = models.UserReward.objects.all()  
        return queryset

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

class IndexView(TemplateView):
    template_name = "quiz/index.html"
    extra_context = {'title': "Home"}

class LevelQuizView(TemplateView):
    template_name = "quiz/level_quizzes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        level = get_object_or_404(models.Level, slug=self.kwargs['slug'])
        
        quizzes = models.Quiz.objects.filter(level=level, published=True)  # Add filter for published quizzes

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
        question = self.quiz.question_set.exclude(id__in=self.user_question_ans_ids).order_by('?').first()
        return question

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

            question_options = self.question.questionoptions_set.all()  # Fetch all options for this question

            options_data = [{'option_text': option.option, 'is_answer': option.answer} for option in question_options]
            correct_option = next((opt for opt in options_data if opt['is_answer']), None)

            if correct_option:
                self.extra_context['correct_option_text'] = correct_option['option_text'] 

            self.extra_context['question_options'] = options_data
        
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['object'] = self.question
        kwargs['title'] = self.question.question
        kwargs['question_options'] = self.extra_context.get('question_options', []) 
        kwargs['correct_option_text'] = self.extra_context.get('correct_option_text', '')  

        return kwargs

    def post(self, request, *args, **kwargs):
        data = request.POST
        selected_answer = data.get('answer', 'no_answer')
        user_answer = get_object_or_404(
            models.UserQuestionAnswer,
            user_quiz=self.user_quiz,
            question=self.quiz.question_set.get(id=data['question']),
        )

        if(not selected_answer == 'no_answer' and not selected_answer == ""):
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
        quiz_data = [{
            'user': user_quiz.user.username,
            'user_id': user_quiz.user.id,
            'quiz_title': user_quiz.quiz.title,
            'quiz_slug': user_quiz.quiz.slug,
            'score': user_quiz.score,
            'total': user_quiz.total_questions,
        } for user_quiz in kwargs['quiz_list']]

        # Add the quiz data to the context in JSON format
        kwargs['quiz_list_json'] = json.dumps(quiz_data)

        return kwargs

class LeaderboardView(QuizMixin, TemplateView):
    template_name = "quiz/leaderboard.html"
    extra_context = {'title': "Leaderboard"}

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['quiz_list_total'] = self.get_all_user_quizzes()
        kwargs['quiz_scores'] = self.get_all_user_scores()
        logger.debug(kwargs['quiz_scores'])
        user_scores = []
        for user_quiz in kwargs['quiz_scores']:
            tempDict = {
                "id": user_quiz.user.id,
                "user": user_quiz.user.username,
                "score": user_quiz.total_score
            }
            user_scores.append(tempDict)
        user_scores = sorted(user_scores, key=lambda x: x['score'], reverse=True)
        kwargs["user_scores"] = user_scores
        logger.debug(user_scores)
        return kwargs

class RewardView(QuizMixin, TemplateView):
    template_name = "quiz/reward.html"
    extra_context = {'title': "Reward"}

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['reward_list'] = self.get_all_rewards()
        rewards = []
        for reward_item in kwargs['reward_list']:
            tempDict = {
                "id": reward_item.id,
                "name": "asd",
                "description": reward_item.description,
                "exchanged_points": reward_item.exchanged_points,
                "quantity": reward_item.quantity,
            }
            rewards.append(tempDict)
        kwargs["reward_list"] = rewards
        logger.debug(rewards)
        return kwargs
    
    def get(self, request, *args, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        user_score = models.UserScore.objects.get(user=self.request.user)
        kwargs['user_score'] = user_score.total_score
        kwargs['reward_list'] = models.Reward.objects.filter(quantity__gt=0)
        logger.debug(kwargs['reward_list'])
        logger.debug(user_score.total_score)
        return self.render_to_response(kwargs)

    def post(self, request, *args, **kwargs):
        reward_id = request.POST.get('reward_id', None)
        user_score = models.UserScore.objects.get(user=request.user)

        if reward_id:
            reward = get_object_or_404(models.Reward, id=reward_id)

            # Logging the user and reward for debugging purposes
            logger.debug(f"User {request.user.username} attempting to redeem reward: {reward.name}")

            # Here you would normally check if the user has enough points, etc.
            if user_score.total_score >= reward.exchanged_points:
                logger.debug(f"User {request.user.username} has enough points to redeem {reward.name}.")

                user_score.total_score -= reward.exchanged_points
                user_score.save()
                
                reward.quantity -= 1
                reward.save()

                # Create a new UserReward entry for the user
                models.UserReward.objects.create(user=request.user, reward=reward)
                logger.debug(f"Reward {reward.name} redeemed by user {request.user.username}.")

                logger.debug(f"Reward {reward.name} redeemed by user {request.user.username}.")
            else:
                logger.debug(f"User {request.user.username} does not have enough points for {reward.name}.")
        else:
            logger.debug("No reward_id detected.")

        return self.get(request, *args, **kwargs)
