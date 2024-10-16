from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Level(TimeStampedModel):
    name = models.CharField(max_length=70, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    users = models.ManyToManyField(get_user_model())  # Users who have access to this level

    def __str__(self):
        return self.name

class Quiz(TimeStampedModel):
    title = models.CharField(max_length=70)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    users = models.ManyToManyField(get_user_model(),)
    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(
        blank=True, null=True, editable=False
    )
    end_date = models.DateTimeField(
        blank=True, null=True,
        validators=[MinValueValidator(timezone.now)],
    )
    level = models.ForeignKey(Level, on_delete=models.CASCADE, default = 1)  


    def __str__(self):
        return self.title

    @property
    def is_closed(self):
        return self.end_date < timezone.now()

    def total_questions(self):
        return self.question_set.all().count()

    class Meta:
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'

class Question(TimeStampedModel):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.CharField(max_length=250)
    time = models.PositiveSmallIntegerField(default=60)

    def __str__(self):
        return self.question

class QuestionOptions(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    option = models.CharField(max_length=250)
    answer = models.BooleanField(default=False)

    def __str__(self):
        return self.option

class UserQuiz(TimeStampedModel):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE
    )
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE
    )

    is_completed = models.BooleanField(default=False)
    is_score_added_total = models.BooleanField(default= False)
    # is_time_added_total = models.BooleanField(default= False)
    start_time = models.DateTimeField(null=True, blank=True)  # When the quiz starts
    end_time = models.DateTimeField(null=True, blank=True)    # When the quiz ends
    full_time = models.IntegerField(default=0)  # Total time allowed for the quiz
    calculated_score = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'User Quiz'
        verbose_name_plural = 'User Quizzes'
        unique_together = ('user', 'quiz')

    @property
    def score(self):
        return UserQuestionAnswer.objects.filter(
            user_quiz=self, answer__answer=True
        ).count()

    # @property
    # def total_score(self):
    #     return self.quiz.question_set.all().count()
    
    @property
    def total_questions(self):
        return self.quiz.question_set.all().count()     

    def completed(self, user, quiz):
        user_quiz_answers = UserQuestionAnswer.objects.filter(
            user_quiz__user=user,
            user_quiz__quiz=quiz  
        )
        total_questions = quiz.total_questions()
        if user_quiz_answers.count() == total_questions:
            if(not self.is_completed):
                self.end_time = timezone.now() 
                start_time = self.start_time
                end_time = self.end_time
                full_time = self.full_time
                play_time = (end_time - start_time).total_seconds() - self.total_questions*2
                logger.debug(f"Start time: {start_time}, End time: {end_time}, Full time: {full_time}, Play time: {play_time}, Queues time: {self.total_questions*2}, Ratio: {(full_time - play_time)/full_time}")
                self.calculated_score = 100*self.score*((full_time - play_time)/full_time)
            self.is_completed = True
            self.save()
            return True
        
        else:
            return False  # Quiz is not yet completed

class UserQuestionAnswer(TimeStampedModel):
    user_quiz = models.ForeignKey(
        UserQuiz, on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE
    )
    answer = models.ForeignKey(
        QuestionOptions, on_delete=models.SET_NULL, null=True
    )

    class Meta:
        unique_together = ('user_quiz', 'question', 'answer')

class Reward(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    exchanged_points = models.IntegerField(default = 0)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return self.name
    
class UserReward(TimeStampedModel):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    redeemed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.reward.name}'

class UserScore(TimeStampedModel):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    total_score = models.IntegerField(default=0)

    def calculate_total_quiz_score(self):
        user_quizzes = UserQuiz.objects.filter(user=self.user)
        total_score = sum(quiz.calculated_score for quiz in user_quizzes)
        
        return total_score

    def update_total_score(self):
        self.total_score = self.calculate_total_quiz_score()
        self.save()

    def __str__(self):
        return f'{self.user.username} - {self.total_score} score'
    