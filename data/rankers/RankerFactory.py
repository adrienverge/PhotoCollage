from data.rankers.ImageRanker import SchoolRanker, GradeRanker, ClassroomRanker, ChildRanker
from yearbook.Corpus import Corpus
from yearbook.Yearbook import Yearbook

"""
For now we're going to return new objects
Eventually the rankers will get smarter and will have some caching
"""

rankerFactory = {}


def create_ranker(corpus: Corpus, yearbook: Yearbook):
    if yearbook.grade is None:
        if yearbook.school not in rankerFactory:
            rankerFactory[yearbook.school] = SchoolRanker(corpus, yearbook.school)
        return rankerFactory[yearbook.school]
    elif yearbook.classroom is None:
        return GradeRanker(corpus)
    elif yearbook.child is None:
        return ClassroomRanker(corpus)
    else:
        return ChildRanker(corpus)
