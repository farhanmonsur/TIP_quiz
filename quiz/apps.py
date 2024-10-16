from django.apps import AppConfig


class QuizConfig(AppConfig):
    name = 'quiz'
    def ready(self):
        import quiz.signals  # Ensure the signals are loaded
        self.create_missing_user_score()

    def create_missing_user_score(self):
        from django.contrib.auth import get_user_model
        from quiz.models import UserScore

        User = get_user_model()
        # Iterate through all users
        for user in User.objects.all():
            user_score, created = UserScore.objects.get_or_create(user=user)
            if created:
                print(f"Created UserScore for user {user.username}")
