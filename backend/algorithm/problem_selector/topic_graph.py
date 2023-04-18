from dataclasses import dataclass, field
from functools import lru_cache
from itertools import combinations

from algorithm.models import TopicGraphEdge
from courses.models import Topic, Course


@dataclass
class Edge:
    topic1: Topic
    topic2: Topic
    weight: float


@dataclass
class TopicGraph:
    """Граф связей тем для подсчета оптимального разбиения тем на группы."""
    topics: list[Topic]
    edges: list[Edge]
    weights: dict = field(default_factory=dict)

    def __post_init__(self):
        self.weights = {topic.title: {} for topic in self.topics}
        for edge in self.edges:
            self.weights[edge.topic1.title][edge.topic2.title] = edge.weight

    def split_topics_in_two_groups(self, topics: set[Topic]) -> tuple[set[Topic], set[Topic]]:
        """Разделяет темы на две группы с максимальной связью
        между друг другом.
        """
        if len(topics) == 1:
            return topics, set()
        if len(topics) == 2:
            return {topics.pop()}, {topics.pop()}
        group_combinations1, group_combinations2 = get_group_combinations(topics)
        group_combinations1 = list(group_combinations1)
        group_combinations2 = list(group_combinations2)
        max_weight = 0.0
        final_groups = ()
        for combination1 in group_combinations1:
            for combination2 in group_combinations2:
                if set(combination1 + combination2) != set(topics):
                    continue
                weight = self.calc_topic_group_weight(combination1)
                weight += self.calc_topic_group_weight(combination2)
                if weight > max_weight:
                    max_weight = weight
                    final_groups = set(combination1), set(combination2)
        return final_groups

    def calc_topic_group_weight(self, topics: tuple[Topic]) -> float:
        """Возвращает сумму весов связей тем."""
        weight = 0.0
        group_combinations = combinations(topics, 2)
        for topic1, topic2 in group_combinations:
            weight += self.weights[topic1.title][topic2.title]
        return weight


def get_group_combinations(topics: set[Topic]) -> tuple[combinations, combinations]:
    """Делит темы на две равные группы и возвращает все сочетания тем
    внутри этих групп.
    """
    middle = int(len(topics) / 2)
    group_size1, group_size2 = middle, len(topics) - middle
    group_combinations1 = combinations(topics, group_size1)
    group_combinations2 = combinations(topics, group_size2)
    return group_combinations1, group_combinations2


@lru_cache(maxsize=None)
def load_topic_graph(course: Course) -> TopicGraph:
    """Создает граф связей тем."""
    topic_graph_edges = TopicGraphEdge.objects.filter(course=course)
    if not topic_graph_edges:
        raise ValueError(f'Отсутствует граф связей тем по курсу {course}')
    edges = []
    for edge in topic_graph_edges:
        edges.append(Edge(topic1=edge.topic1,
                          topic2=edge.topic2,
                          weight=edge.weight))
    topics = Topic.objects.filter(module__course=course)
    return TopicGraph(topics, edges)
