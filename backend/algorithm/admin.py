from django.contrib import admin

import algorithm.models as algorithm_models

algorithm = [algorithm_models.Progress,
             algorithm_models.TheoryProgress,
             algorithm_models.WeakestLinkProblem,
             algorithm_models.WeakestLinkTopic,
             algorithm_models.PracticeProgress,
             algorithm_models.UserAnswer]

admin.site.register(algorithm)
