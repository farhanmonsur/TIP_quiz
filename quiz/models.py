from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone


class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


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
    description = models.TextField(null=True, blank=True)
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

    class Meta:
        verbose_name = 'User Quiz'
        verbose_name_plural = 'User Quizzes'
        unique_together = ('user', 'quiz')

    @property
    def score(self):
        return UserQuestionAnswer.objects.filter(
            user_quiz=self, answer__answer=True
        ).count()

    @property
    def total_score(self):
        return self.quiz.question_set.all().count()

    def total_questions(self):
        return self.quiz.question_set.all().count()

    def completed(self, user, quiz):
        user_quiz = UserQuestionAnswer.objects.filter(
            user_quiz__user=user
        )
        return user_quiz.count() == quiz.question_set.all().count()


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
