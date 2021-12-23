from data.rankers.ImageRanker import SchoolRanker, GradeRanker, ClassroomRanker, ChildRanker
from yearbook.Corpus import Corpus

"""
For now we're going to return new objects
Eventually the rankers will get smarter and will have some caching
"""

rankerFactory = {}


def create_ranker(corpus: Corpus, school: str, grade: str, classroom: str, child: str):
    if grade is None:
        if school not in rankerFactory:
            rankerFactory[school] = SchoolRanker(corpus, school)
        return rankerFactory[school]
    elif classroom is None:
        return GradeRanker(corpus)
    elif child is None:
        return ClassroomRanker(corpus)
    else:
        return ChildRanker(corpus)
