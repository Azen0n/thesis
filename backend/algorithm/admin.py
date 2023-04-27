from django.contrib import admin

import algorithm.models as algorithm_models

algorithm = [algorithm_models.Progress,
             algorithm_models.UserAnswer,
             algorithm_models.WeakestLinkTopic,
             algorithm_models.WeakestLinkProblem,
             algorithm_models.UserWeakestLinkState,
             algorithm_models.TopicGraphEdge,
             algorithm_models.UserTargetPoints]

admin.site.register(algorithm)
