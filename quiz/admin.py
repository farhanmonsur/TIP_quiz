from django.contrib import admin
from django.utils import timezone
from django.urls import reverse
from django.utils.html import format_html

from quiz.models import (
    Quiz,
    QuestionOptions,
    Question,
    UserQuiz,
    UserQuestionAnswer,
    Level
)



class QuestionTabularInline(admin.TabularInline):
    model = Question
    fields = ('question_display', 'time', 'created')  
    readonly_fields = ('created','time','question_display')  
    extra = 0 
    can_delete = False

    def question_display(self, obj):
        if obj.id:
            url = reverse('admin:quiz_question_change', args=[obj.id])  
            return format_html('<a href="{}">{}</a>', url, obj.question)  
        return ""  

    question_display.short_description = "Question"

    can_delete = False  

    def has_add_permission(self, request, obj=None):
        return False  


    class Media:
        css = {
            'all': ('css/admin_custom.css',),  
        }
   
@admin.register(Quiz)
class QuizModelAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'published_at',
        'published',
        'end_date',
        'created',
        'modified'
    )
    search_fields = ('title', )
    list_filter = ('created', 'modified')
    filter_horizontal = ('users',)
    prepopulated_fields = {'slug': ('title', )}
    inlines = [QuestionTabularInline]
    actions = ('make_published', 'make_unpublished')

    def save_model(self, request, obj, form, change):
        if 'published' in form.changed_data or change:
            obj.published_at = timezone.now() if obj.published else None
        super().save_model(request, obj, form, change)

    def make_published(self, request, queryset):
        queryset.update(published=True, published_at=timezone.now())
    make_published.short_description = "Published selected quizzes"

    def make_unpublished(self, request, queryset):
        queryset.update(published=False, published_at=None)
    make_unpublished.short_description = "Unpublished selected quizzes"

    class Media:
        css = {
            'all': ('css/admin_custom.css',),  # Link to your custom CSS file
        }


class QuestionOptionsTabularInline(admin.TabularInline):
    model = QuestionOptions
    extra = 0
    min_num = 3
    max_num = 6
@admin.register(Question)
class QuestionModelAdmin(admin.ModelAdmin):
    inlines = (QuestionOptionsTabularInline, )
    list_display = ('question', 'quiz', 'modified', 'created')
    list_filter = ('quiz', 'created',)
    search_fields = ('question', 'quiz__title')
    autocomplete_fields = ('quiz', )


class UserQuestionAnsInline(admin.TabularInline):
    model = UserQuestionAnswer
    readonly_fields = ('user_quiz', 'question', 'answer', 'answer_correct')
    extra = 0
    # can_delete = False

    @admin.display(description='Correct?', boolean=True)
    def answer_correct(self, obj):
        return obj.answer.answer
@admin.register(UserQuiz)
class UserQuizAdmin(admin.ModelAdmin):
    inlines = (UserQuestionAnsInline, )
    list_display = (
        'quiz',
        'user',
        'score',
        'total_score',
        'modified',
        'created'
    )
    list_filter = ('quiz', 'created',)
    search_fields = ('user', 'quiz__title')
    autocomplete_fields = ('quiz', )


class QuizInline(admin.TabularInline):
    model = Quiz
    fields = ('title', 'slug', 'published', 'end_date')  
    readonly_fields = ('title', 'slug', 'published', 'end_date') 
    can_delete = False  
    extra = 0  
    class Media:
        css = {
            'all': ('css/admin_custom.css',),  
        }
@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created', 'modified')
    search_fields = ('name', )
    list_filter = ('created', 'modified')
    inlines = [QuizInline]  # This adds the quizzes inline to the level admin


